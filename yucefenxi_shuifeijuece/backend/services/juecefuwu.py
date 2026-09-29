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


def pinggu_shuifen(soil_moisture):
    """
    水分状态评估。
    """
    soil_moisture = zhuan_float(soil_moisture, 30)

    if soil_moisture < 15:
        return "严重缺水"
    elif soil_moisture < 30:
        return "轻度缺水"
    elif soil_moisture <= 45:
        return "水分正常"
    else:
        return "水分偏高"


def pinggu_feili(ec):
    """
    肥力状态评估。
    """
    ec = zhuan_float(ec, 1.5)

    if ec < 1.0:
        return "肥力不足"
    elif ec <= 2.5:
        return "肥力正常"
    else:
        return "肥力偏高"


def jisuan_guangailiang(soil_moisture, max_temp, rainfall_prob, use_weather, predicted_water_need):
    """
    计算推荐灌溉量。
    """
    soil_moisture = zhuan_float(soil_moisture, 30)
    max_temp = zhuan_float(max_temp, 30)
    rainfall_prob = zhuan_float(rainfall_prob, 20)

    base = 18

    if soil_moisture < 15:
        base += 12
    elif soil_moisture < 25:
        base += 8
    elif soil_moisture < 35:
        base += 4
    elif soil_moisture > 45:
        base -= 5

    if use_weather:
        if max_temp >= 35:
            base += 4
        elif max_temp >= 30:
            base += 2

        if rainfall_prob >= 70:
            base -= 6
        elif rainfall_prob >= 40:
            base -= 3

    if isinstance(predicted_water_need, list) and len(predicted_water_need) > 0:
        avg_value = sum([zhuan_float(x, 0) for x in predicted_water_need]) / len(predicted_water_need)
        base = base * 0.6 + avg_value * 0.4

    if base < 0:
        base = 0

    return round(base, 2)


def jisuan_shifeiliang(ec, predicted_fertilizer_need):
    """
    计算推荐施肥量。
    """
    ec = zhuan_float(ec, 1.5)

    base = 5

    if ec < 1.0:
        base += 2.5
    elif ec < 1.5:
        base += 1
    elif ec > 2.5:
        base -= 1.5

    if isinstance(predicted_fertilizer_need, list) and len(predicted_fertilizer_need) > 0:
        avg_value = sum([zhuan_float(x, 0) for x in predicted_fertilizer_need]) / len(predicted_fertilizer_need)
        base = base * 0.6 + avg_value * 0.4

    if base < 0:
        base = 0

    return round(base, 2)


def shengcheng_yuanyin(soil_moisture, ec, max_temp, rainfall_prob, use_weather, water_status, fertility_status):
    """
    生成决策依据说明。
    """
    reason = ""

    reason += f"当前土壤湿度为 {soil_moisture}%，水分状态为：{water_status}。"
    reason += f" 当前电导率 EC 为 {ec}，肥力状态为：{fertility_status}。"

    if use_weather:
        reason += f" 已结合天气因素，最高温为 {max_temp}℃，降雨概率为 {rainfall_prob}%。"
    else:
        reason += " 本次决策未采用天气因素。"

    if water_status in ["严重缺水", "轻度缺水"]:
        reason += " 由于当前水分不足，建议进行灌溉。"
    elif water_status == "水分偏高":
        reason += " 当前水分偏高，应减少或暂停灌溉。"
    else:
        reason += " 当前水分较为正常，建议保持常规灌溉。"

    if fertility_status == "肥力不足":
        reason += " 当前肥力不足，建议适量增加施肥。"
    elif fertility_status == "肥力偏高":
        reason += " 当前肥力偏高，建议减少施肥，避免盐分累积。"
    else:
        reason += " 当前肥力正常，建议维持常规施肥。"

    return reason


def shengcheng_shebeicanshu(irrigation, fertilization):
    """
    生成设备参数。

    备注：
    pump_run_time 暂时按 2 L/min 的流量估算。
    后续需要设备协同模块提供真实流量参数。
    """
    pump_flow = 2.0

    if pump_flow <= 0:
        pump_flow = 2.0

    pump_run_time = irrigation / pump_flow

    return {
        "irrigation_amount": round(irrigation, 2),
        "fertilization_amount": round(fertilization, 2),
        "pump_run_time": round(pump_run_time, 2)
    }


def shengcheng_juecejieguo(data):
    """
    生成水肥决策结果。
    """
    soil_moisture = zhuan_float(data.get("soil_moisture"), 30)
    ec = zhuan_float(data.get("ec"), 1.5)
    max_temp = zhuan_float(data.get("max_temp"), 30)
    rainfall_prob = zhuan_float(data.get("rainfall_prob"), 20)
    use_weather = zhuan_bool(data.get("use_weather"), True)

    predicted_water_need = data.get("predicted_water_need", [])
    predicted_fertilizer_need = data.get("predicted_fertilizer_need", [])

    water_status = pinggu_shuifen(soil_moisture)
    fertility_status = pinggu_feili(ec)

    irrigation = jisuan_guangailiang(
        soil_moisture,
        max_temp,
        rainfall_prob,
        use_weather,
        predicted_water_need
    )

    fertilization = jisuan_shifeiliang(
        ec,
        predicted_fertilizer_need
    )

    decision_reason = shengcheng_yuanyin(
        soil_moisture,
        ec,
        max_temp,
        rainfall_prob,
        use_weather,
        water_status,
        fertility_status
    )

    device_params = shengcheng_shebeicanshu(irrigation, fertilization)

    return {
        "crop_id": data.get("crop_id", 1),
        "growth_stage": data.get("growth_stage", "未知生育期"),
        "water_status": water_status,
        "fertility_status": fertility_status,
        "recommended_irrigation": irrigation,
        "recommended_fertilization": fertilization,
        "decision_reason": decision_reason,
        "device_params": device_params
    }