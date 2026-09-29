from models import YongHu

def zhuan_kong_zifuchuan(value):
    """空值处理，去除两端空格"""
    if value is None:
        return ""
    return str(value).strip()

def shengcheng_token(user_id, username):
    """生成简易登录令牌，后续可替换标准JWT"""
    token = f"login_token_{user_id}_{username}"
    return token

def denglu_yanzheng(username, password):
    """
    登录业务校验
    :param username: 用户名
    :param password: 明文密码
    :return: (token, xinxi)
    成功返回(token, "登录成功")
    失败返回(None, "账号或密码错误")
    """
    username = zhuan_kong_zifuchuan(username)
    password = zhuan_kong_zifuchuan(password)

    user = YongHu.query.filter_by(username=username).first()
    if user and user.jianyan_mima(password):
        token = shengcheng_token(user.id, username)
        return token, "登录成功"
    return None, "账号或密码错误"