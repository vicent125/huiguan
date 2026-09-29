import os

filepath = os.environ.get(
    'WEATHER_SAMPLE_FILE',
    r'D:\weather\气象数据\气象数据\temp min\2020最低温.csv'
)

print(f"文件大小: {os.path.getsize(filepath)} bytes")

with open(filepath, 'rb') as f:
    header = f.read(50)
    print(f"文件头(十六进制): {header.hex()}")
    print(f"文件头(原始): {header}")

    # 尝试判断格式
    if header[:4] == b'PK\x03\x04':
        print("→ 这是 ZIP 格式（可能是 .xlsx）")
    elif header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        print("→ 这是 OLE 格式（老版 .xls）")
    elif header[:4] == b'CDF\x01' or header[:4] == b'CDF\x02':
        print("→ 这是 NetCDF 格式")
    elif header[:4] == b'GRIB':
        print("→ 这是 GRIB 气象数据格式")
    elif header[:2] == b'BM':
        print("→ 这是 BMP 图片")
    else:
        print("→ 未知格式，需要进一步分析")
