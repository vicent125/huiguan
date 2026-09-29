"""
import_weather.py - 气象数据导入脚本（精简版，精度 0.1°）
使用方式：python import_weather.py
"""

import pandas as pd
import os
import glob
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# ========== 配置区域 ==========

# MySQL 连接配置
MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'smart_agriculture')
}

# 数据文件夹路径
DATA_DIR = os.environ.get('WEATHER_DATA_DIR', r'D:\weather\气象数据\气象数据')

# 精度配置：每隔多少个点取一个（0.01° -> 0.1°，间隔10）
LON_STEP =5  # 经度每隔10个点取一个
LAT_STEP =5  # 纬度每隔10个点取一个

# 每批导入多少条记录
BATCH_SIZE = 20000

# 自动检测数据目录下的文件夹
INDICATORS = {}
if os.path.exists(DATA_DIR):
    for folder in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder)
        if os.path.isdir(folder_path):
            if 'max' in folder.lower() or '最高温' in folder:
                INDICATORS[folder] = 'max_temp'
            elif 'min' in folder.lower() or '最低温' in folder:
                INDICATORS[folder] = 'min_temp'
            elif 'prec' in folder.lower() or '降雨' in folder:
                INDICATORS[folder] = 'rainfall'
            elif 'rhu' in folder.lower() or '湿度' in folder:
                INDICATORS[folder] = 'humidity'
            elif 'pet' in folder.lower() or '蒸散' in folder:
                INDICATORS[folder] = 'evapotranspiration'

print(f"检测到指标: {INDICATORS}")
print(f"精度配置: 每隔 {LON_STEP} 个经度点、{LAT_STEP} 个纬度点取一个（约 0.1°）")


# ========== 数据库操作 ==========

def get_engine():
    """创建数据库连接引擎"""
    url = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True)


def create_table(engine):
    """创建气象网格数据表"""
    sql = """
          CREATE TABLE IF NOT EXISTS weather_grid \
          ( \
              id \
              BIGINT \
              AUTO_INCREMENT \
              PRIMARY \
              KEY, \
              data_date \
              DATE \
              NOT \
              NULL \
              COMMENT \
              '数据日期', \
              latitude \
              DECIMAL \
          ( \
              8, \
              5 \
          ) NOT NULL COMMENT '纬度',
              longitude DECIMAL \
          ( \
              8, \
              5 \
          ) NOT NULL COMMENT '经度',
              max_temp FLOAT COMMENT '最高温度(°C)',
              min_temp FLOAT COMMENT '最低温度(°C)',
              humidity FLOAT COMMENT '相对湿度(%)',
              rainfall FLOAT COMMENT '降雨量(mm)',
              evapotranspiration FLOAT COMMENT '蒸散量(mm)',
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              UNIQUE KEY uk_date_lat_lon \
          ( \
              data_date, \
              latitude, \
              longitude \
          ),
              INDEX idx_date \
          ( \
              data_date \
          ),
              INDEX idx_lat_lon \
          ( \
              latitude, \
              longitude \
          )
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='气象网格数据'; \
          """
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("✅ 数据表 weather_grid 创建/确认完成")


def clear_table(engine):
    """清空表数据"""
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE weather_grid"))
        conn.commit()
    print("✅ 数据表已清空")


# ========== 数据读取 ==========

def find_xls_files(folder_path):
    """查找文件夹下所有文件"""
    files = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            files.append(item_path)
    return sorted(files)


def read_xls_file(filepath):
    """读取气象数据文件，返回 DataFrame"""
    try:
        df = pd.read_csv(filepath, encoding='gbk')
        return df
    except Exception as e1:
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
            return df
        except Exception as e2:
            try:
                df = pd.read_excel(filepath, engine='xlrd')
                return df
            except Exception as e3:
                try:
                    df = pd.read_excel(filepath, engine='openpyxl')
                    return df
                except Exception as e4:
                    print(f"❌ 无法读取文件 {filepath}: {e1}, {e2}, {e3}, {e4}")
                    return None


def parse_year_from_filename(filename):
    """从文件名提取年份"""
    import re
    basename = os.path.basename(filename)
    match = re.search(r'(\d{4})', basename)
    if match:
        return int(match.group(1))
    return None


# ========== 数据导入（精简版） ==========

def import_single_file(engine, filepath, db_field):
    """导入单个 csv 文件（精简版，降低精度）"""
    year = parse_year_from_filename(filepath)
    if not year:
        print(f"⚠️ 无法从文件名解析年份: {filepath}")
        return 0

    print(f"\n📄 正在读取: {os.path.basename(filepath)} ({year}年)")

    # 读取表头获取经度值
    df_header = pd.read_csv(filepath, encoding='gbk', nrows=1, header=None)
    lon_values = df_header.iloc[0, 1:].values

    # 精简经度：每隔 LON_STEP 个取一个
    lon_indices = list(range(0, len(lon_values), LON_STEP))
    lon_values_sparse = [float(lon_values[i]) for i in lon_indices]

    # 读取数据（跳过前两行表头）
    df = pd.read_csv(filepath, encoding='gbk', skiprows=2, header=None)

    if df.empty:
        print(f"⚠️ 文件为空或读取失败")
        return 0

    print(f"   原始数据: {len(df)} 行 × {len(lon_values)} 列")
    print(f"   精简后: ~{len(df) // LAT_STEP} 行 × {len(lon_values_sparse)} 列")

    # 构建插入数据
    records = []
    total_inserted = 0
    date_obj = datetime(year, 1, 1).date()

    with engine.connect() as conn:
        # 精简纬度：每隔 LAT_STEP 行取一个
        for idx in range(0, len(df), LAT_STEP):
            row = df.iloc[idx]
            lat = row.iloc[0]

            # 跳过无效纬度
            if pd.isna(lat):
                continue

            try:
                lat = float(lat)
            except:
                continue

            # 遍历精简后的经度列
            for j, lon_col_idx in enumerate(lon_indices):
                lon = lon_values_sparse[j]

                # 获取气象值
                value = row.iloc[lon_col_idx + 1]

                # 跳过 NaN 值
                if pd.isna(value):
                    continue

                # 构建记录
                record = {
                    'data_date': date_obj,
                    'latitude': round(lat, 5),
                    'longitude': round(lon, 5),
                    db_field: float(value)
                }
                records.append(record)

                # 批量插入
                if len(records) >= BATCH_SIZE:
                    inserted = batch_insert(conn, records, db_field)
                    total_inserted += inserted
                    records = []

                    if total_inserted % 50000 == 0:
                        print(f"   ⏳ 已导入 {total_inserted} 条...")

        # 插入剩余记录
        if records:
            inserted = batch_insert(conn, records, db_field)
            total_inserted += inserted

    print(f"   ✅ 完成，共导入 {total_inserted} 条")
    return total_inserted


def batch_insert(conn, records, db_field):
    """批量插入数据，使用 ON DUPLICATE KEY UPDATE 处理冲突"""
    if not records:
        return 0

    columns = ['data_date', 'latitude', 'longitude', db_field]
    placeholders = ', '.join([':' + c for c in columns])

    sql = f"""
    INSERT INTO weather_grid (data_date, latitude, longitude, {db_field}) 
    VALUES ({placeholders})
    ON DUPLICATE KEY UPDATE {db_field} = VALUES({db_field})
    """

    try:
        conn.execute(text(sql), records)
        conn.commit()
        return len(records)
    except Exception as e:
        print(f"   ❌ 插入失败: {e}")
        conn.rollback()
        return 0


# ========== 主程序 ==========

def main():
    print("=" * 60)
    print("气象数据导入工具（精简版）")
    print("=" * 60)

    # 1. 检查数据目录
    if not os.path.exists(DATA_DIR):
        print(f"❌ 数据目录不存在: {DATA_DIR}")
        return

    print(f"📁 数据目录: {DATA_DIR}")
    print("📂 实际文件夹:", os.listdir(DATA_DIR))

    # 2. 连接数据库
    print("\n🔗 连接 MySQL 数据库...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    # 3. 创建表
    print("\n📋 检查数据表...")
    create_table(engine)

    # 4. 询问是否清空数据
    response = input("\n是否清空已有数据？(yes/no，默认no): ").strip().lower()
    if response == 'yes':
        clear_table(engine)

    # 5. 遍历指标文件夹
    print("\n📊 开始导入数据...")
    total_all = 0

    for folder_name, db_field in INDICATORS.items():
        folder_path = os.path.join(DATA_DIR, folder_name)

        if not os.path.exists(folder_path):
            print(f"\n⚠️ 文件夹不存在，跳过: {folder_name}")
            continue

        print(f"\n{'=' * 50}")
        print(f"📂 正在处理指标: {folder_name} -> {db_field}")
        print(f"{'=' * 50}")

        files = find_xls_files(folder_path)
        print(f"   找到 {len(files)} 个文件")

        for filepath in files:
            count = import_single_file(engine, filepath, db_field)
            total_all += count

    # 6. 完成
    print("\n" + "=" * 60)
    print(f"🎉 全部导入完成！总计导入: {total_all} 条记录")
    print("=" * 60)

    # 7. 统计信息
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM weather_grid"))
        total_rows = result.scalar()
        print(f"📊 数据库当前总记录数: {total_rows}")

        result = conn.execute(text("SELECT MIN(data_date), MAX(data_date) FROM weather_grid"))
        min_date, max_date = result.fetchone()
        print(f"📅 数据日期范围: {min_date} ~ {max_date}")


if __name__ == '__main__':
    main()
