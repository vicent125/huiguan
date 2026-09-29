import os

from flask import Flask, jsonify
from flask_cors import CORS
from database.models import db

from routes.tianqifenxi import tianqifenxi_bp
from routes.baogaozhongxin import baogaozhongxin_bp
from routes.xitongguanli import xitongguanli_bp
from routes.tianqi import weather_bp


def create_app():
    app = Flask(__name__)

    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    app.config.from_object('config')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False

    db.init_app(app)

    app.register_blueprint(tianqifenxi_bp)
    app.register_blueprint(baogaozhongxin_bp)
    app.register_blueprint(xitongguanli_bp)
    app.register_blueprint(weather_bp)

    # 首次启动自动创建缺失的数据表，降低本地联调门槛。
    with app.app_context():
        db.create_all()

    @app.get('/api/health')
    def health_check():
        return jsonify({'code': 200, 'message': '服务运行正常', 'data': None})

    @app.route('/weather')
    def weather_page():
        return app.send_static_file('tianqifenxi.html')

    @app.route('/system')
    def system_page():
        return app.send_static_file('xitongguanli.html')

    @app.route('/report')
    def report_page():
        return app.send_static_file('baogaozhongxin.html')

    return app


if __name__ == '__main__':
    app = create_app()
    debug_enabled = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5030)), debug=debug_enabled, use_reloader=False)
