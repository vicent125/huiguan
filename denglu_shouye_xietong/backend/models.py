from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class YongHu(db.Model):
    """
    系统用户表
    备注：
    用于登录页面账号密码校验
    """
    __tablename__ = "sys_yonghu"
    id = db.Column(db.Integer, primary_key=True, comment="主键id")
    username = db.Column(db.String(50), unique=True, nullable=False, comment="用户名")
    password_hash = db.Column(db.String(200), nullable=False, comment="加密密码")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")

    def she_mima(self, raw_pwd):
        """设置密码，自动加密"""
        self.password_hash = generate_password_hash(raw_pwd)

    def jianyan_mima(self, raw_pwd):
        """校验明文密码"""
        return check_password_hash(self.password_hash, raw_pwd)


class SheBeiXieTong(db.Model):
    __tablename__ = "shebei_xietong"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_name = db.Column(db.String(100), comment="设备名称")
    device_code = db.Column(db.String(50), unique=True, comment="设备编号")
    status = db.Column(db.String(30), comment="设备状态")
    sync_mode = db.Column(db.String(100), comment="协同模式")
    water_level = db.Column(db.Float, comment="水箱液位")
    fertilizer_level = db.Column(db.Float, comment="肥箱液位")
    irrigation = db.Column(db.Float, comment="灌溉水量")
    fertilize = db.Column(db.Float, comment="施肥用量")
    pump_status = db.Column(db.String(20), comment="水泵状态")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")