"""AI模型适配层 —— 调用DeepSeek兼容OpenAI API格式的模型。

运行环境：Python 3.10+，requests
配置方式：环境变量（API密钥不出现在前端/源代码/日志中）
  AI_API_KEY     模型API密钥（必填，未设置时自动降级）
  AI_API_URL     模型接口地址（默认DeepSeek官方地址）
  AI_MODEL_NAME  模型名称（默认deepseek-chat）
  AI_TIMEOUT     请求超时秒数（默认30）
  AI_RATE_LIMIT  每分钟调用上限（默认10）

设计原则：
  1. AI只增强分析文字，不参与数值计算，不控制设备
  2. AI调用失败时降级为规则算法（返回None）
  3. 所有调用可追溯（记录模型版本、提示词版本、耗时、异常）
  4. API密钥不出现在日志中
"""
import json
import os
import time
from datetime import datetime

import requests

TISHICI_BANBEN = "1.0.0"

TISHICI = """你是农业水肥分析辅助模型，不是自动控制系统。

请根据输入的作物、生育期、土壤监测数据、天气预报数据和历史决策数据，分析未来三天的水肥需求。

分析规则：

1. 优先使用输入中的真实数据；
2. 不得编造缺失数据；
3. 数据不足时必须列出缺失字段；
4. 结合土壤湿度和田间持水量分析水分状态；
5. 结合生育期和天气变化分析需水趋势；
6. 结合肥料参数和土壤电导率分析肥力状态；
7. 结合未来降雨量和降雨概率调整灌溉建议；
8. 结合高温、低温、干旱和强降雨给出风险提示；
9. 所有推荐值必须经过本地农业规则再次校验；
10. 不得直接输出设备控制指令；
11. 不得直接控制水泵、施肥泵和电磁阀；
12. confidence 必须是 0 到 1 之间的数字；
13. 数据不足时降低 confidence；
14. 结果必须经过人工确认；
15. 只返回 JSON，不返回 Markdown；
16. 不要输出任何额外解释。

返回格式：

{
  "crop_name": "",
  "growth_stage": "",
  "analysis_summary": "",
  "soil_moisture_status": "low|normal|high|unknown",
  "fertility_status": "low|normal|high|unknown",
  "drought_risk": "low|medium|high|unknown",
  "weather_impact": "",
  "three_day_forecast": [
    {
      "date": "",
      "water_demand_trend": "decrease|stable|increase|unknown",
      "fertilizer_demand_trend": "decrease|stable|increase|unknown",
      "irrigation_suggestion": "",
      "fertilizer_suggestion": "",
      "risk_note": ""
    }
  ],
  "recommended_irrigation": {
    "value": 0,
    "unit": "L/m2",
    "range_min": 0,
    "range_max": 0
  },
  "recommended_fertilizer": {
    "value": 0,
    "unit": "kg/亩",
    "range_min": 0,
    "range_max": 0
  },
  "decision_basis": [],
  "missing_data": [],
  "warnings": [],
  "confidence": 0,
  "human_confirmation_required": true
}"""


def huoqu_peizhi():
    """读取环境变量配置，API密钥未设置时返回空密钥标记。"""
    return {
        "api_key": os.environ.get("AI_API_KEY", ""),
        "api_url": os.environ.get("AI_API_URL", "https://api.deepseek.com/v1/chat/completions"),
        "model_name": os.environ.get("AI_MODEL_NAME", "deepseek-chat"),
        "timeout": int(os.environ.get("AI_TIMEOUT", "30")),
        "rate_limit": int(os.environ.get("AI_RATE_LIMIT", "10")),
    }


class PinlvXianzhi:
    """滑动窗口频率限制器，默认每分钟10次。"""

    def __init__(self, shangxian=10):
        self.shangxian = shangxian
        self.jilu = []

    def jiancha(self):
        """检查是否允许调用，允许时记录时间戳并返回True。"""
        now = time.time()
        self.jilu = [t for t in self.jilu if now - t < 60]
        if len(self.jilu) >= self.shangxian:
            return False
        self.jilu.append(now)
        return True


_pinlv = PinlvXianzhi(huoqu_peizhi()["rate_limit"])


def shifou_qiyong():
    """判断AI是否已启用（API密钥已配置）。"""
    return bool(huoqu_peizhi()["api_key"])


def gouzao_shuru(jiance, tianqi, zuowu, lishi_juece=None, turang=None, feiliao=None):
    """构造AI输入对象，仅传递真实数据，不编造缺失字段。

    Args:
        jiance: 最新监测数据dict
        tianqi: 天气预报list
        zuowu: 作物信息dict
        lishi_juece: 历史决策记录list（可选）
        turang: 土壤信息dict（可选，含田间持水量、pH等）
        feiliao: 肥料信息dict（可选，含氮磷钾含量）

    Returns:
        dict: AI输入对象
    """
    shuru = {
        "crop_name": zuowu.get("mingcheng", ""),
        "growth_stage": zuowu.get("shengyujie", ""),
        "soil_moisture": jiance.get("turang_shidu"),
        "soil_temperature": jiance.get("turang_wendu"),
        "air_humidity": jiance.get("kongqi_shidu"),
        "light_intensity": jiance.get("guangzhao"),
        "soil_ec": jiance.get("dian_daolv"),
        "field_capacity": None,
        "soil_ph": None,
        "soil_texture": None,
        "nitrogen_content": None,
        "phosphorus_content": None,
        "potassium_content": None,
        "weather_forecast": [],
        "fertilizer_params": {},
        "historical_decisions": [],
    }
    if turang:
        shuru["field_capacity"] = turang.get("chitian_chishuiliang")
        shuru["soil_ph"] = turang.get("ph")
        shuru["soil_texture"] = turang.get("zhidi")
    if feiliao:
        shuru["nitrogen_content"] = feiliao.get("dan")
        shuru["phosphorus_content"] = feiliao.get("lin")
        shuru["potassium_content"] = feiliao.get("jia")
    for tian in (tianqi or [])[:3]:
        shuru["weather_forecast"].append({
            "date": tian.get("yubaoriqi", ""),
            "max_temp": tian.get("zuigao_wendu"),
            "min_temp": tian.get("zuidi_wendu"),
            "rain_probability": tian.get("jiangyu_gailv"),
            "rain_amount": tian.get("jiangyu_liang"),
            "weather_type": tian.get("tianqi_leixing", ""),
            "evapotranspiration": tian.get("zhengfa_liang"),
        })
    if zuowu.get("xushui_xishu") is not None:
        shuru["fertilizer_params"]["water_coefficient"] = zuowu.get("xushui_xishu")
    if zuowu.get("xufei_xishu") is not None:
        shuru["fertilizer_params"]["fertilizer_coefficient"] = zuowu.get("xufei_xishu")
    if zuowu.get("mubiao_shidu") is not None:
        shuru["fertilizer_params"]["target_moisture"] = zuowu.get("mubiao_shidu")
    for juece in (lishi_juece or [])[:5]:
        shuru["historical_decisions"].append({
            "date": str(juece.get("jilu_shijian", ""))[:10],
            "irrigation": juece.get("guangai_liang"),
            "fertilization": juece.get("shifei_liang"),
        })
    return shuru


def tiqu_json(text):
    """从模型响应文本中提取JSON，处理Markdown代码块包裹。

    Args:
        text: 模型返回的原始文本

    Returns:
        dict or None: 解析成功返回dict，失败返回None
    """
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    kaishi = text.find("{")
    jieshu = text.rfind("}")
    if kaishi != -1 and jieshu != -1 and jieshu > kaishi:
        try:
            return json.loads(text[kaishi:jieshu + 1])
        except json.JSONDecodeError:
            pass
    return None


def jiaoyan_shuchu(result):
    """校验AI输出字段完整性，返回(是否通过, 缺失字段列表)。

    Args:
        result: AI返回的JSON dict

    Returns:
        tuple: (bool, list) 是否通过校验, 缺失字段列表
    """
    if not isinstance(result, dict):
        return False, ["root"]
    bixu_ziduan = [
        "crop_name", "growth_stage", "analysis_summary",
        "soil_moisture_status", "fertility_status", "drought_risk",
        "three_day_forecast", "recommended_irrigation", "recommended_fertilizer",
        "decision_basis", "missing_data", "warnings", "confidence",
        "human_confirmation_required",
    ]
    queshi = [z for z in bixu_ziduan if z not in result]
    if queshi:
        return False, queshi
    if not isinstance(result["three_day_forecast"], list):
        return False, ["three_day_forecast"]
    if not isinstance(result["recommended_irrigation"], dict):
        return False, ["recommended_irrigation"]
    if not isinstance(result["recommended_fertilizer"], dict):
        return False, ["recommended_fertilizer"]
    confidence = result.get("confidence", 0)
    try:
        confidence = float(confidence)
        if not 0 <= confidence <= 1:
            return False, ["confidence_range"]
    except (TypeError, ValueError):
        return False, ["confidence_type"]
    return True, []


def diaoyong_moxing(jiance, tianqi, zuowu, lishi_juece=None, turang=None, feiliao=None):
    """调用AI模型进行分析，失败时返回None触发降级。

    Args:
        jiance: 最新监测数据dict
        tianqi: 天气预报list
        zuowu: 作物信息dict
        lishi_juece: 历史决策记录list（可选）
        turang: 土壤信息dict（可选）
        feiliao: 肥料信息dict（可选）

    Returns:
        dict: 包含success, result, model, model_version, prompt_version,
              fallback_used, error, haoshi, request_id
    """
    kaishi_shijian = time.time()
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    peizhi = huoqu_peizhi()
    jieguo = {
        "success": False, "result": None, "model": peizhi["model_name"],
        "model_version": peizhi["model_name"], "prompt_version": TISHICI_BANBEN,
        "fallback_used": True, "error": "", "haoshi": 0, "request_id": request_id,
    }
    if not peizhi["api_key"]:
        jieguo["error"] = "AI_API_KEY未配置，使用规则算法降级"
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo
    if not _pinlv.jiancha():
        jieguo["error"] = "调用频率超限（每分钟{}次），使用规则算法降级".format(peizhi["rate_limit"])
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo
    shuru = gouzao_shuru(jiance, tianqi, zuowu, lishi_juece, turang, feiliao)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(peizhi["api_key"]),
    }
    payload = {
        "model": peizhi["model_name"],
        "messages": [
            {"role": "system", "content": TISHICI},
            {"role": "user", "content": json.dumps(shuru, ensure_ascii=False, default=str)},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            peizhi["api_url"], headers=headers, json=payload,
            timeout=peizhi["timeout"],
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = tiqu_json(content)
        if parsed is None:
            jieguo["error"] = "模型返回非法JSON，使用规则算法降级"
            jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
            return jieguo
        tongguo, queshi = jiaoyan_shuchu(parsed)
        if not tongguo:
            jieguo["error"] = "模型输出字段校验失败，缺失：{}".format(queshi)
            jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
            return jieguo
        jieguo["success"] = True
        jieguo["result"] = parsed
        jieguo["fallback_used"] = False
        jieguo["error"] = ""
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo
    except requests.Timeout:
        jieguo["error"] = "模型请求超时（{}秒），使用规则算法降级".format(peizhi["timeout"])
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo
    except requests.RequestException as exc:
        jieguo["error"] = "模型请求异常：{}，使用规则算法降级".format(str(exc)[:200])
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo
    except Exception as exc:
        jieguo["error"] = "模型调用未知异常：{}，使用规则算法降级".format(str(exc)[:200])
        jieguo["haoshi"] = round(time.time() - kaishi_shijian, 3)
        return jieguo


def jiangji_jieguo(yuce_jieguo, juece_jieguo, zuowu):
    """AI降级时，从规则算法结果构造兼容格式的分析结果。

    Args:
        yuce_jieguo: shengcheng_yuce返回的预测结果
        juece_jieguo: shengcheng_juece返回的决策结果
        zuowu: 作物信息dict

    Returns:
        dict: 兼容AI输出格式的结果
    """
    dates = yuce_jieguo.get("dates", [])
    xushui = yuce_jieguo.get("xushui", [])
    xufei = yuce_jieguo.get("xufei", [])
    shidu = yuce_jieguo.get("shidu", [])
    forecast = []
    for i, day in enumerate(dates):
        qushui = "未知"
        qufei = "未知"
        if i > 0 and len(xushui) > i:
            if xushui[i] > xushui[i - 1]:
                qushui = "上升"
            elif xushui[i] < xushui[i - 1]:
                qushui = "下降"
            else:
                qushui = "稳定"
        if i > 0 and len(xufei) > i:
            if xufei[i] > xufei[i - 1]:
                qufei = "上升"
            elif xufei[i] < xufei[i - 1]:
                qufei = "下降"
            else:
                qufei = "稳定"
        forecast.append({
            "date": day,
            "water_demand_trend": qushui,
            "fertilizer_demand_trend": qufei,
            "irrigation_suggestion": "建议灌溉{}L/亩".format(xushui[i] if i < len(xushui) else 0),
            "fertilizer_suggestion": "建议施肥{}kg/亩".format(xufei[i] if i < len(xufei) else 0),
            "risk_note": "预测土壤湿度{}%".format(shidu[i] if i < len(shidu) else 0),
        })
    shidu_zhuangtai = juece_jieguo.get("water_status", "未知")
    if "缺水" in shidu_zhuangtai:
        soil_status = "偏低"
    elif "偏高" in shidu_zhuangtai:
        soil_status = "偏高"
    elif "适宜" in shidu_zhuangtai:
        soil_status = "正常"
    else:
        soil_status = "未知"
    feili_zhuangtai = juece_jieguo.get("fertility_status", "未知")
    if "不足" in feili_zhuangtai:
        fert_status = "偏低"
    elif "偏高" in feili_zhuangtai:
        fert_status = "偏高"
    elif "适宜" in feili_zhuangtai:
        fert_status = "正常"
    else:
        fert_status = "未知"
    fenxi = yuce_jieguo.get("fenxi", "")
    if "干旱" in fenxi:
        drought = "高"
    elif "积水" in fenxi:
        drought = "低"
    else:
        drought = "中"
    irrigation = juece_jieguo.get("recommended_irrigation", 0)
    fertilizer = juece_jieguo.get("recommended_fertilization", 0)
    return {
        "crop_name": zuowu.get("mingcheng", ""),
        "growth_stage": zuowu.get("shengyujie", ""),
        "analysis_summary": fenxi,
        "soil_moisture_status": soil_status,
        "fertility_status": fert_status,
        "drought_risk": drought,
        "weather_impact": yuce_jieguo.get("tianqi_shuoming", ""),
        "three_day_forecast": forecast,
        "recommended_irrigation": {
            "value": irrigation, "unit": "L/m2",
            "range_min": round(irrigation * 0.8, 1), "range_max": round(irrigation * 1.2, 1),
        },
        "recommended_fertilizer": {
            "value": fertilizer, "unit": "kg/亩",
            "range_min": round(fertilizer * 0.8, 1), "range_max": round(fertilizer * 1.2, 1),
        },
        "decision_basis": [juece_jieguo.get("reason", "规则算法生成")],
        "missing_data": [],
        "warnings": [],
        "confidence": 0.6,
        "human_confirmation_required": True,
    }