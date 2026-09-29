import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db
from routes.denglu import denglu_bp
from routes.shouye import home_bp
from models import YongHu
from routes.xietong import xietong_bp


def chuangjian_yingyong():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # 开启跨域，允许前端访问
    CORS(app)

    # 初始化数据库
    db.init_app(app)

    # 注册接口蓝图
    app.register_blueprint(denglu_bp, url_prefix='/api')
    app.register_blueprint(home_bp)
    app.register_blueprint(xietong_bp, url_prefix='/api')

    # 首页测试接口
    @app.route("/")
    def shouye():
        return jsonify({
            "code": 200,
            "message": "登录后端服务正常运行",
            "data": {}
        })

    @app.get("/api/health")
    def health_check():
        return jsonify({"code": 200, "message": "服务运行正常", "data": None})

    # 判断是否自动建表并初始化管理员账号
    if app.config["ZIDONG_JIANBIAO"]:
        with app.app_context():
            db.create_all()
            admin_name = os.environ.get("INITIAL_ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD")
            if not admin_password and os.environ.get("FLASK_ENV", "development") == "production":
                raise RuntimeError("生产环境必须设置 INITIAL_ADMIN_PASSWORD")
            admin_password = admin_password or "123456"
            admin_user = YongHu.query.filter_by(username=admin_name).first()
            if not admin_user:
                new_admin = YongHu(username=admin_name)
                new_admin.she_mima(admin_password)
                db.session.add(new_admin)
                db.session.commit()

    return app

# 启动入口
if __name__ == '__main__':
    app = chuangjian_yingyong()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5010)), debug=False)
