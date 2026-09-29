import pandas as pd
import os

DATA_DIR = os.environ.get('WEATHER_DATA_DIR', r'D:\weather\气象数据\气象数据')


def analyze_file(filepath):
    """分析单个文件的数据分布"""
    # 读取表头获取经度值
    df_header = pd.read_csv(filepath, encoding='gbk', nrows=1, header=None)
    lon_values = df_header.iloc[0, 1:].values

    # 读取数据
    df = pd.read_csv(filepath, encoding='gbk', skiprows=2, header=None)

    # 提取纬度
    lat_values = df.iloc[:, 0].dropna().values

    # 统计有效数据
    total_cells = 0
    valid_cells = 0

    for idx, row in df.iterrows():
        lat = row.iloc[0]
        if pd.isna(lat):
            continue

        for j in range(len(lon_values)):
            value = row.iloc[j + 1]
            total_cells += 1
            if not pd.isna(value):
                valid_cells += 1

    return {
        'file': os.path.basename(filepath),
        'lon_min': float(lon_values[0]),
        'lon_max': float(lon_values[-1]),
        'lon_count': len(lon_values),
        'lat_min': float(lat_values.min()),
        'lat_max': float(lat_values.max()),
        'lat_count': len(lat_values),
        'total_cells': total_cells,
        'valid_cells': valid_cells,
        'valid_rate': valid_cells / total_cells if total_cells > 0 else 0
    }


def main():
    print("=" * 60)
    print("气象数据统计分析")
    print("=" * 60)

    # 只分析每个指标的第一个文件（加快速度）
    for folder in os.listdir(DATA_DIR):
        folder_path = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        if not files:
            continue

        # 分析第一个文件
        sample_file = os.path.join(folder_path, sorted(files)[0])
        print(f"\n📂 指标: {folder}")
        print(f"   样本文件: {os.path.basename(sample_file)}")

        result = analyze_file(sample_file)

        print(f"   经度范围: {result['lon_min']:.2f} ~ {result['lon_max']:.2f} ({result['lon_count']} 个)")
        print(f"   纬度范围: {result['lat_min']:.2f} ~ {result['lat_max']:.2f} ({result['lat_count']} 个)")
        print(f"   总单元格: {result['total_cells']:,}")
        print(f"   有效数据: {result['valid_cells']:,}")
        print(f"   有效率: {result['valid_rate'] * 100:.2f}%")

        # 估算该指标总数据量
        total_files = len(files)
        estimated_total = result['valid_cells'] * total_files
        print(f"   该指标{total_files}个文件估算: {estimated_total:,} 条")


if __name__ == '__main__':
    main()
