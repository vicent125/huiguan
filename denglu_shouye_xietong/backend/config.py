import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 拼接相对路径，标准Flask写法
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "instance", "denglu.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 自动建表开关

    ZIDONG_JIANBIAO = True
