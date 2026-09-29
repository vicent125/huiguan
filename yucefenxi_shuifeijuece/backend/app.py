import os
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db
from routes.yucefenxi import yucefenxi_bp
from routes.shuifeijuece import shuifeijuece_bp


def chuangjian_yingyong():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)

    app.register_blueprint(yucefenxi_bp)
    app.register_blueprint(shuifeijuece_bp)

    @app.route("/")
    def shouye():
        return jsonify({
            "code": 200,
            "message": "水肥一体化系统后端运行中",
            "data": {
                "modules": ["预测分析", "水肥决策"]
            }
        })

    @app.get("/api/health")
    def health_check():
        return jsonify({"code": 200, "message": "服务运行正常", "data": None})

    if app.config.get("ZIDONG_JIANBIAO"):
        with app.app_context():
            db.create_all()

    return app


app = chuangjian_yingyong()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5041)), debug=False)
