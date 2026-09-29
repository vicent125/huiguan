"""天气服务：支持任意经纬度查询 + 雅安雨城区/西昌专用分析。

运行环境：Python 3.10+，requests
数据源：Open-Meteo API（免费、无需Key）https://api.open-meteo.com
网络不可用时使用数据库缓存（tianqi表）。

预设地区：
  - 雅安市雨城区（学校所在地，纬度29.98 经度103.00）
  - 西昌市（油橄榄主产区，纬度27.90 经度102.27）
"""
from datetime import datetime

import requests


# 预设地区：雅安市雨城区（学校所在地）和西昌市（尝试性扩展）
DIQU_YUCHENG = {"name": "四川省雅安市雨城区", "latitude": 29.98, "longitude": 103.00}
DIQU_XICHANG = {"name": "四川省凉山州西昌市", "latitude": 27.90, "longitude": 102.27}

# 所有预设地区列表，前端可调用获取选项
YUSHE_DIQU = [DIQU_YUCHENG, DIQU_XICHANG]


def tianqi_mingcheng(code):
    if code == 0:
        return "晴"
    if code in (1, 2):
        return "多云"
    if code == 3:
        return "阴"
    if code in (45, 48):
        return "雾"
    if code in (51, 53, 55, 56, 57, 61, 80):
        return "小雨"
    if code in (63, 66, 81):
        return "中雨"
    if code in (65, 67, 82):
        return "大雨"
    if code in (71, 73, 75, 77, 85, 86):
        return "降雪"
    if code in (95, 96, 99):
        return "雷雨"
    return "天气变化"


def huoqu_yucheng_tianqi():
    """获取雅安市雨城区三天天气（保留原有接口，向后兼容）。"""
    return huoqu_jingwei_tianqi(DIQU_YUCHENG["latitude"], DIQU_YUCHENG["longitude"], DIQU_YUCHENG["name"])


def huoqu_jingwei_tianqi(latitude, longitude, diming=None):
    """根据任意经纬度获取三天天气预报。

    Args:
        latitude: 纬度（float）
        longitude: 经度（float）
        diming: 地区名称（str），未提供时用"经纬度(lat,lon)"格式

    Returns:
        list[dict]: 三天天气数据列表
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join([
            "temperature_2m_max", "temperature_2m_min", "relative_humidity_2m_mean",
            "precipitation_probability_max", "precipitation_sum", "weather_code",
            "et0_fao_evapotranspiration",
        ]),
        "timezone": "Asia/Shanghai",
        "forecast_days": 3,
    }
    response = requests.get(url, params=params, timeout=8)
    response.raise_for_status()
    daily = response.json()["daily"]
    diqu_mingcheng = diming or f"经纬度({latitude},{longitude})"
    rows = []
    for i, day in enumerate(daily["time"]):
        rows.append({
            "yubaoriqi": day,
            "zuigao_wendu": daily["temperature_2m_max"][i],
            "zuidi_wendu": daily["temperature_2m_min"][i],
            "kongqi_shidu": daily["relative_humidity_2m_mean"][i],
            "jiangyu_gailv": daily["precipitation_probability_max"][i],
            "jiangyu_liang": daily["precipitation_sum"][i],
            "tianqi_leixing": tianqi_mingcheng(daily["weather_code"][i]),
            "zhengfa_liang": daily["et0_fao_evapotranspiration"][i],
            "diqu": diqu_mingcheng,
            "shuju_laiyuan": "Open-Meteo",
            "gengxin_shijian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "jingdu": longitude,
            "weidu": latitude,
        })
    return rows


def baocun_tianqi(conn, rows):
    for item in rows:
        exists = conn.execute("SELECT id FROM tianqi WHERE yubaoriqi=?", (item["yubaoriqi"],)).fetchone()
        values = (
            item["zuigao_wendu"], item["zuidi_wendu"], item["kongqi_shidu"],
            item["jiangyu_gailv"], item["jiangyu_liang"], item["tianqi_leixing"],
            item["zhengfa_liang"], item["diqu"], item["shuju_laiyuan"], item["gengxin_shijian"],
        )
        if exists:
            conn.execute("UPDATE tianqi SET zuigao_wendu=?,zuidi_wendu=?,kongqi_shidu=?,jiangyu_gailv=?,jiangyu_liang=?,tianqi_leixing=?,zhengfa_liang=?,diqu=?,shuju_laiyuan=?,gengxin_shijian=? WHERE id=?", values + (exists["id"],))
        else:
            conn.execute("INSERT INTO tianqi(zuigao_wendu,zuidi_wendu,kongqi_shidu,jiangyu_gailv,jiangyu_liang,tianqi_leixing,zhengfa_liang,diqu,shuju_laiyuan,gengxin_shijian,yubaoriqi) VALUES (?,?,?,?,?,?,?,?,?,?,?)", values + (item["yubaoriqi"],))
    conn.commit()
