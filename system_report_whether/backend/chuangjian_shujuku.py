import os

import pymysql

# 连接 MySQL（不指定数据库）
conn = pymysql.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    port=int(os.environ.get('DB_PORT', '3306')),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', '')
)

cursor = conn.cursor()

# 创建数据库
cursor.execute("CREATE DATABASE IF NOT EXISTS smart_agriculture CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
print("✅ 数据库 smart_agriculture 创建成功（或已存在）")

cursor.close()
conn.close()
