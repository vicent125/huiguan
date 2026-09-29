import os

from sqlalchemy import create_engine, text

url = os.environ.get('DATABASE_URL')
if not url:
    raise RuntimeError('请先设置 DATABASE_URL，再执行清理脚本')
engine = create_engine(url)

with engine.connect() as conn:
    conn.execute(text("DELETE FROM weather_grid"))
    conn.commit()
    print("✅ 表已清空")
