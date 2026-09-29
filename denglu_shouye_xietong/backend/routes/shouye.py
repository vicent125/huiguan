from flask import Blueprint, request, jsonify

home_bp = Blueprint("home", __name__, url_prefix="/api")


# Token校验函数：和你登录下发token格式匹配
def verify_login_token():
    token = request.headers.get("token")
    if not token or not token.startswith("login_token_"):
        return False
    return True


# GET /api/home 首页数据接口
@home_bp.get("/home")
def get_home_info():
    if not verify_login_token():
        return jsonify({
            "code": 401,
            "message": "登录失效，请重新登录"
        })

    home_data = {
        "username": "admin",
        "welcome_text": "欢迎进入智慧农情监测与决策管理系统",
        "statistics": {
            "farm_count": 28,
            "sensor_count": 146,
            "today_alert": 7,
            "irrigation_task": 12
        },
        "menu_list": [
            {"id": 1, "title": "首页总览", "path": "/home", "icon": "🏠"},
            {"id": 2, "title": "农田管理", "path": "/farm", "icon": "🌾"},
            {"id": 3, "title": "监测数据", "path": "/monitor", "icon": "📊"},
            {"id": 4, "title": "灌溉调度", "path": "/water", "icon": "💧"},
            {"id": 5, "title": "系统设置", "path": "/setting", "icon": "⚙️"}
        ]
    }
    return jsonify({
        "code": 200,
        "message": "首页数据加载成功",
        "data": home_data
    })