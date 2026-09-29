import json
from models import JianceShuju, TianqiYubao


def zhuan_float(value, default_value):
    try:
        if value is None:
            return default_value
        return float(value)
    except Exception:
        return default_value


def zhuan_bool(value, default_value=True):
    if value is None:
        return default_value

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "是"]

    return bool(value)


def huoqu_zuixin_jiance(data):
    """
    获取最新监测数据。

    优先使用前端传来的数据。
    如果前端没有传，则尝试从数据库 monitor_data 中读取最新数据。

    备注：
    monitor_data 表由“数据录入与监测”模块维护。
    """
    soil_moisture = data.get("soil_moisture")
    ec = data.get("ec")

    if soil_moisture is not None and ec is not None:
        return {
            "crop_id": data.get("crop_id", 1),
            "growth_stage": data.get("growth_stage", "未知生育期"),
            "soil_moisture": zhuan_float(data.get("soil_moisture"), 30),
            "soil_temperature": zhuan_float(data.get("soil_temperature"), 22),
            "air_humidity": zhuan_float(data.get("air_humidity"), 60),
            "light_intensity": zhuan_float(data.get("light_intensity"), 10000),
            "ec": zhuan_float(data.get("ec"), 1.5)
        }

    try:
        latest = JianceShuju.query.order_by(JianceShuju.created_at.desc()).first()

        if latest:
            return {
                "crop_id": latest.crop_id,
                "growth_stage": latest.growth_stage,
                "soil_moisture": latest.soil_moisture,
                "soil_temperature": latest.soil_temperature,
                "air_humidity": latest.air_humidity,
                "light_intensity": latest.light_intensity,
                "ec": latest.ec
            }
    except Exception:
        pass

    # 如果数据库暂时没接好，就用默认值保证页面能跑
    return {
        "crop_id": 1,
        "growth_stage": "默认生育期",
        "soil_moisture": 30,
        "soil_temperature": 22,
        "air_humidity": 60,
        "light_intensity": 10000,
        "ec": 1.5
    }


def huoqu_tianqi(data):
    """
    获取天气数据。

    优先使用前端传来的天气数据。
    如果没有传，则尝试从 weather_forecast 表读取最新天气。

    备注：
    weather_forecast 表由“天气分析”模块维护。
    """
    if data.get("max_temp") is not None:
        return {
            "max_temp": zhuan_float(data.get("max_temp"), 30),
            "min_temp": zhuan_float(data.get("min_temp"), 22),
            "rainfall_prob": zhuan_float(data.get("rainfall_prob"), 20),
            "rainfall": zhuan_float(data.get("rainfall"), 0),
            "weather_type": data.get("weather_type", "未知")
        }

    try:
        latest = TianqiYubao.query.order_by(TianqiYubao.created_at.desc()).first()

        if latest:
            return {
                "max_temp": latest.max_temp,
                "min_temp": latest.min_temp,
                "rainfall_prob": latest.rainfall_prob,
                "rainfall": latest.rainfall,
                "weather_type": latest.weather_type
            }
    except Exception:
        pass

    return {
        "max_temp": 30,
        "min_temp": 22,
        "rainfall_prob": 20,
        "rainfall": 0,
        "weather_type": "默认天气"
    }


def jisuan_xushuixiuliang(jiance, tianqi, days, use_weather):
    """
    计算未来需水量。

    这里是规则模型：
    - 土壤湿度越低，需水越高
    - 温度越高，需水越高
    - 降雨概率越高，需水减少
    - 光照越强，需水略增加
    """
    result = []

    soil_moisture = zhuan_float(jiance.get("soil_moisture"), 30)
    light_intensity = zhuan_float(jiance.get("light_intensity"), 10000)

    max_temp = zhuan_float(tianqi.get("max_temp"), 30)
    rainfall_prob = zhuan_float(tianqi.get("rainfall_prob"), 20)

    for i in range(days):
        value = 18

        if soil_moisture < 20:
            value += 10
        elif soil_moisture < 30:
            value += 6
        elif soil_moisture > 45:
            value -= 3

        if light_intensity > 15000:
            value += 2

        if use_weather:
            if max_temp >= 35:
                value += 5
            elif max_temp >= 30:
                value += 3

            if rainfall_prob >= 70:
                value -= 6
            elif rainfall_prob >= 40:
                value -= 3

        # 简单考虑未来几天灌溉后需求略降低
        value = value - i * 1.2

        if value < 0:
            value = 0

        result.append(round(value, 2))

    return result


def jisuan_xufeiliang(jiance, days):
    """
    计算未来需肥量。

    这里暂时根据 EC 判断：
    - EC 低，认为肥力不足，需要增加施肥
    - EC 高，认为盐分或肥力偏高，需要减少施肥

    备注：
    后续可以结合“作物需肥系数”和“肥料信息表”进一步优化。
    """
    result = []

    ec = zhuan_float(jiance.get("ec"), 1.5)

    for i in range(days):
        value = 5

        if ec < 1.0:
            value += 2.5
        elif ec < 1.5:
            value += 1
        elif ec > 2.5:
            value -= 1.5

        value = value - i * 0.2

        if value < 0:
            value = 0

        result.append(round(value, 2))

    return result


def jisuan_turangshidu(jiance, tianqi, days, use_weather):
    """
    预测未来土壤湿度。
    """
    result = []

    soil_moisture = zhuan_float(jiance.get("soil_moisture"), 30)
    max_temp = zhuan_float(tianqi.get("max_temp"), 30)
    rainfall_prob = zhuan_float(tianqi.get("rainfall_prob"), 20)

    for i in range(days):
        decline = 2 + i * 0.4

        if use_weather:
            if max_temp >= 30:
                decline += 1
            if rainfall_prob >= 60:
                decline -= 1.5

        value = soil_moisture - decline * (i + 1)

        if value < 0:
            value = 0

        result.append(round(value, 2))

    return result


def shengcheng_hanqingfenxi(predicted_soil_moisture):
    """
    生成旱情分析文字。
    """
    if not predicted_soil_moisture:
        return "暂无足够数据进行旱情分析"

    last_value = predicted_soil_moisture[-1]

    if last_value < 15:
        return "未来土壤湿度明显偏低，存在重度干旱风险"
    elif last_value < 25:
        return "未来3天存在轻度干旱风险，建议关注灌溉"
    elif last_value < 35:
        return "未来土壤湿度略有下降，但整体风险可控"
    else:
        return "未来3天土壤湿度整体正常"


def shengcheng_yucejieguo(data):
    """
    生成预测分析结果。
    """
    days = int(zhuan_float(data.get("days"), 3))

    if days < 1:
        days = 1

    if days > 3:
        days = 3

    use_weather = zhuan_bool(data.get("use_weather"), True)

    jiance = huoqu_zuixin_jiance(data)
    tianqi = huoqu_tianqi(data)

    water_need = jisuan_xushuixiuliang(jiance, tianqi, days, use_weather)
    fertilizer_need = jisuan_xufeiliang(jiance, days)
    soil_moisture_list = jisuan_turangshidu(jiance, tianqi, days, use_weather)

    drought_analysis = shengcheng_hanqingfenxi(soil_moisture_list)

    dates = []
    for i in range(days):
        dates.append(f"第{i + 1}天")

    if use_weather:
        basis = "已结合当前监测数据和天气因素进行预测"
    else:
        basis = "仅基于当前监测数据进行预测，未采用天气因素"

    return {
        "crop_id": jiance.get("crop_id"),
        "growth_stage": jiance.get("growth_stage"),
        "dates": dates,
        "predicted_water_need": water_need,
        "predicted_fertilizer_need": fertilizer_need,
        "predicted_soil_moisture": soil_moisture_list,
        "drought_analysis": drought_analysis,
        "basis": basis,
        "weather_desc": json.dumps(tianqi, ensure_ascii=False)
    }