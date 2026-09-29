
import os


# 本地开发默认使用项目 instance 目录中的 SQLite。
# 部署到 MySQL 时通过 DATABASE_URL 覆盖，不在源码中保存账号和密码。
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'sqlite:///smart_agriculture.db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# 报告PDF输出目录
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

# 字体配置（Windows）
FONT_PATH = 'C:/Windows/Fonts/simsun.ttc'
FONT_FALLBACK = 'C:/Windows/Fonts/simhei.ttf'
