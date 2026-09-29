from flask import Blueprint, request, jsonify
from services.denglufuwu import denglu_yanzheng

# 创建登录蓝图
denglu_bp = Blueprint("denglu", __name__,url_prefix="/api")

@denglu_bp.route("/denglu", methods=["POST"])
def denglu():
    """
    用户登录接口
    前端登录页面调用
    请求参数：username、password
    返回统一格式：code、message、data
    """
    try:
        json_data = request.get_json() or {}
        username = json_data.get("username")
        password = json_data.get("password")

        # 参数非空校验
        if not username or not password:
            return jsonify({
                "code": 400,
                "message": "账号与密码不能为空",
                "data": {}
            })

        token, msg = denglu_yanzheng(username, password)
        if token:
            return jsonify({
                "code": 200,
                "message": msg,
                "data": {
                    "token": token,
                    "username": username
                }
            })
        else:
            return jsonify({
                "code": 400,
                "message": msg,
                "data": {}
            })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"服务器异常：{str(e)}",
            "data": {}
        }), 500