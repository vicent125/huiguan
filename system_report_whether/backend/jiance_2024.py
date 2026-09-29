import os

import pandas as pd

filepath = os.environ.get(
    'WEATHER_SAMPLE_FILE',
    r'D:\weather\气象数据\气象数据\pet（蒸散量）\2024.csv'
)

# 读取原始文件
df = pd.read_csv(filepath, encoding='gbk')
print(f"形状: {df.shape}")
print(f"前3行:\n{df.head(3)}")
print(f"列名: {list(df.columns[:5])}")

# 检查空值比例
print(f"\n空值统计:")
print(df.isna().sum().head(10))
