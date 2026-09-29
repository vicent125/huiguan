import os
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///local_test.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ZIDONG_JIANBIAO = os.getenv("ZIDONG_JIANBIAO", "false").lower() == "true"