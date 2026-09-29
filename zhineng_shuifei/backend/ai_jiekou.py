"""AI接口路由 —— 提供AI辅助分析接口。

运行环境：Python 3.10+，Flask 3.x
被 yingyong.py 导入并注册蓝图。

接口路由：
  POST /api/yucefenxi/ai-analyze  AI辅助分析未来三天水肥需求
  GET  /api/yucefenxi/ai-zhuangtai  查询AI服务状态
"""
import json
import os
import time
import uuid
from datetime import date, datetime

from flask import Blueprint, jsonify, request

from ai_fuzhu import TISHICI_BANBEN, diaoyong_moxing, gouzao_shuru, jiangji_jieguo, jiaoyan_shuchu, shifou_qiyong
from anquan_jiaoyan import jiaoyan as anquan_jiaoyan_jiaoyan
from fenxijuece import jisuan_xiuzheng_xishu, shengcheng_juece, shengcheng_yuce, ZengliangHuigui
from shujuku import lianjie, zidian

ai_lantu = Blueprint("ai", __name__)

ZHUANGTAI_FANYI = {
    "low": "偏低", "normal": "正常", "high": "偏高", "unknown": "未知",
    "medium": "中",
    "decrease": "下降", "stable": "稳定", "increase": "上升",
}


def fanyi_zhuangtai(jieguo):
    """将AI返回的英文状态值翻译为中文。"""
    if not isinstance(jieguo, dict):
        return jieguo
    for field in ("soil_moisture_status", "fertility_status", "drought_risk"):
        if field in jieguo and jieguo[field] in ZHUANGTAI_FANYI:
            jieguo[field] = ZHUANGTAI_FANYI[jieguo[field]]
    for item in jieguo.get("three_day_forecast", []):
        for field in ("water_demand_trend", "fertilizer_demand_trend"):
            if field in item and item[field] in ZHUANGTAI_FANYI:
                item[field] = ZHUANGTAI_FANYI[item[field]]
    return jieguo


def fanhui(data=None, xiaoxi="操作成功", zhuangtai=200):
    return jsonify({"code": zhuangtai, "message": xiaoxi, "data": data}), zhuangtai


def shijian():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def shuzi(value, moren=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return moren


def jilu_rizhi(conn, leixing, neirong, caozuoren="系统"):
    conn.execute(
        "INSERT INTO rizhi(caozuo_shijian,caozuo_leixing,caozuo_neirong,caozuoren) VALUES (?,?,?,?)",
        (shijian(), leixing, neirong, caozuoren),
    )


def huoqu_jiance(conn):
    return zidian(conn.execute("SELECT * FROM jiance ORDER BY jilu_shijian DESC,id DESC LIMIT 1").fetchone()) or {}


def huoqu_zuowu(conn, zuowu_id=3):
    row = conn.execute("SELECT * FROM zuowu WHERE id=?", (zuowu_id,)).fetchone()
    return zidian(row) or zidian(conn.execute("SELECT * FROM zuowu ORDER BY id LIMIT 1").fetchone()) or {}


def huoqu_tianqi(conn):
    today = date.today().isoformat()
    rows = conn.execute("SELECT * FROM tianqi WHERE yubaoriqi>=? ORDER BY yubaoriqi LIMIT 3", (today,)).fetchall()
    if not rows:
        rows = conn.execute("SELECT * FROM tianqi ORDER BY yubaoriqi DESC LIMIT 3").fetchall()
        rows = list(reversed(rows))
    return [zidian(row) for row in rows]


def huoqu_lishi_juece(conn, zuowu_id, shuliang=5):
    rows = conn.execute(
        "SELECT guangai_liang,shifei_liang,jilu_shijian FROM juece WHERE zuowu_id=? ORDER BY jilu_shijian DESC LIMIT ?",
        (zuowu_id, shuliang),
    ).fetchall()
    return [zidian(row) for row in rows]


def baocun_fenxi(conn, request_id, zuowu_id, moxing_mingcheng, moxing_banben,
                 tishici_banben, jiangji_shiyong, haoshi, shuru_json, shuchu_json,
                 cuowu_xinxi, zhixindu, zhuangtai):
    """保存AI分析记录到数据库。"""
    try:
        conn.execute(
            "INSERT INTO ai_fenxi(request_id,zuowu_id,moxing_mingcheng,moxing_banben,tishici_banben,jiangji_shiyong,haoshi,shuru_json,shuchu_json,cuowu_xinxi,zhixindu,zhuangtai,jilu_shijian) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (request_id, zuowu_id, moxing_mingcheng, moxing_banben, tishici_banben,
             jiangji_shiyong, haoshi, json.dumps(shuru_json, ensure_ascii=False, default=str),
             json.dumps(shuchu_json, ensure_ascii=False, default=str),
             cuowu_xinxi, zhixindu, zhuangtai, shijian()),
        )
    except Exception:
        pass


@ai_lantu.get("/api/yucefenxi/ai-zhuangtai")
def ai_zhuangtai():
    """查询AI服务配置状态（不返回API密钥）。"""
    qiyong = shifou_qiyong()
    return fanhui({
        "enabled": qiyong,
        "model": os.environ.get("AI_MODEL_NAME", "deepseek-chat"),
        "prompt_version": TISHICI_BANBEN,
        "rate_limit": int(os.environ.get("AI_RATE_LIMIT", "10")),
        "timeout": int(os.environ.get("AI_TIMEOUT", "30")),
    }, "AI服务已启用" if qiyong else "AI服务未启用，将使用规则算法")


@ai_lantu.post("/api/yucefenxi/ai-analyze")
def ai_fenxi():
    """AI辅助分析未来三天水肥需求。

    处理流程（15步）：
      1. 验证用户身份
      2. 验证请求参数
      3. 查询基地信息
      4. 查询作物和生育期信息
      5. 查询土壤和肥料参数
      6. 查询历史监测数据
      7. 查询未来三天天气
      8. 构造AI输入对象
      9. 调用模型适配层
      10. 解析模型JSON
      11. 校验模型输出字段
      12. 使用农业规则校验推荐值
      13. 判断是否需要人工复核
      14. 保存预测记录
      15. 返回前端
    """
    kaishi_shijian = time.time()
    request_id = str(uuid.uuid4()).replace("-", "")[:20]
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    try:
        zuowu_id = int(data.get("crop_id") or data.get("zuowu_id") or 3)
        shengyujie = data.get("growth_stage", "")
        yuce_tianshu = int(data.get("forecast_range") or 3)
        shiyong_tianqi = data.get("weather_enabled", True)
        jiance_shuju = data.get("monitoring_data") or {}
        tianqi_shuju = data.get("weather_data") or []
        jiance = huoqu_jiance(conn)
        for field in ("turang_shidu", "dian_daolv", "turang_wendu", "kongqi_shidu", "guangzhao"):
            if jiance_shuju.get(field) not in (None, ""):
                jiance[field] = jiance_shuju[field]
        if shengyujie:
            jiance["shengyujie"] = shengyujie
        zuowu = huoqu_zuowu(conn, zuowu_id)
        if tianqi_shuju and isinstance(tianqi_shuju, list):
            weather = tianqi_shuju
        else:
            weather = huoqu_tianqi(conn)
        lishi_juece = huoqu_lishi_juece(conn, zuowu_id)
        xiuzheng = jisuan_xiuzheng_xishu(conn)
        huigui = ZengliangHuigui.jiazai(conn, "guangai")
        shidu = shuzi(jiance.get("turang_shidu"), 30)
        huigui_yuce = huigui.yuce(shidu) if huigui.n >= 2 else None
        yuce_jieguo = shengcheng_yuce(jiance, weather, zuowu, yuce_tianshu, shiyong_tianqi)
        juece_jieguo = shengcheng_juece(jiance, weather, zuowu, yuce_jieguo, xiuzheng, huigui_yuce)
        turang = zidian(conn.execute("SELECT * FROM turang ORDER BY id LIMIT 1").fetchone()) or {}
        feiliao = zidian(conn.execute("SELECT * FROM feiliao ORDER BY id LIMIT 1").fetchone()) or {}
        moxing_jieguo = diaoyong_moxing(jiance, weather, zuowu, lishi_juece, turang, feiliao)
        if moxing_jieguo["success"] and moxing_jieguo["result"]:
            fenxi_jieguo = fanyi_zhuangtai(moxing_jieguo["result"])
            jiangji = False
            moxing_mingcheng = moxing_jieguo["model"]
            moxing_banben = moxing_jieguo["model_version"]
            zhixindu = shuzi(fenxi_jieguo.get("confidence"), 0.5)
        else:
            fenxi_jieguo = jiangji_jieguo(yuce_jieguo, juece_jieguo, zuowu)
            jiangji = True
            moxing_mingcheng = "规则算法"
            moxing_banben = "local-rules"
            zhixindu = 0.6
        guangai = shuzi(fenxi_jieguo.get("recommended_irrigation", {}).get("value"), juece_jieguo["recommended_irrigation"])
        shifei = shuzi(fenxi_jieguo.get("recommended_fertilizer", {}).get("value"), juece_jieguo["recommended_fertilization"])
        beng_shijian = round(guangai / 2, 1)
        jiangyu_gailv = shuzi(weather[0].get("jiangyu_gailv"), 0) if weather else 0
        shebei_row = zidian(conn.execute("SELECT * FROM shebei ORDER BY id LIMIT 1").fetchone()) or {}
        shuixiang = shuzi(shebei_row.get("shuixiang"), 100)
        feixiang = shuzi(shebei_row.get("feixiang"), 100)
        shebei_zhuangtai = shebei_row.get("zhuangtai", "未知")
        tuijian_danwei = {
            "irrigation_unit": fenxi_jieguo.get("recommended_irrigation", {}).get("unit", "L/m2"),
            "fertilizer_unit": fenxi_jieguo.get("recommended_fertilizer", {}).get("unit", "kg/亩"),
        }
        tongguo, _ = jiaoyan_shuchu(fenxi_jieguo)
        jiaoyan_jieguo = anquan_jiaoyan_jiaoyan(
            guangai=guangai, shifei=shifei, beng_shijian=beng_shijian,
            shidu=shidu, jiangyu_gailv=jiangyu_gailv,
            shuixiang_yewei=shuixiang, feixiang_yewei=feixiang,
            shebei_zhuangtai=shebei_zhuangtai,
            ai_zhixindu=zhixindu, ai_ziduan_wanzheng=tongguo,
            tuijian_danwei=tuijian_danwei,
            yichang_shuru=False,
            weichuli_yujing=fenxi_jieguo.get("warnings", []),
            conn=conn,
        )
        renfu_fuhe = (
            jiaoyan_jieguo["status"] == "manual_review"
            or zhixindu < 0.7
            or fenxi_jieguo.get("human_confirmation_required", True)
        )
        haoshi = round(time.time() - kaishi_shijian, 3)
        fenxi_id = None
        try:
            cursor = conn.execute(
                "INSERT INTO ai_fenxi(request_id,zuowu_id,moxing_mingcheng,moxing_banben,tishici_banben,jiangji_shiyong,haoshi,shuru_json,shuchu_json,cuowu_xinxi,zhixindu,zhuangtai,jilu_shijian) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (request_id, zuowu_id, moxing_mingcheng, moxing_banben, TISHICI_BANBEN,
                 jiangji, haoshi,
                 json.dumps(gouzao_shuru(jiance, weather, zuowu, lishi_juece, turang, feiliao), ensure_ascii=False, default=str),
                 json.dumps(fenxi_jieguo, ensure_ascii=False, default=str),
                 moxing_jieguo.get("error", ""), zhixindu, jiaoyan_jieguo["status"], shijian()),
            )
            fenxi_id = cursor.lastrowid
        except Exception:
            pass
        conn.execute(
            "INSERT INTO yuce(zuowu_id,yuce_tianshu,xushui_json,xufei_json,shidu_json,fenxi,tianqi_shuoming,jilu_shijian) VALUES (?,?,?,?,?,?,?,?)",
            (zuowu_id, len(yuce_jieguo["dates"]), json.dumps(yuce_jieguo["xushui"]),
             json.dumps(yuce_jieguo["xufei"]), json.dumps(yuce_jieguo["shidu"]),
             fenxi_jieguo.get("analysis_summary", yuce_jieguo["fenxi"]),
             yuce_jieguo["tianqi_shuoming"], shijian()),
        )
        jilu_rizhi(conn, "AI分析", "request_id={}，模型={}，降级={}，耗时={}s".format(
            request_id, moxing_mingcheng, jiangji, haoshi))
        conn.commit()
        jieguo = {
            "success": True,
            "request_id": request_id,
            "analysis_id": fenxi_id,
            "model": moxing_mingcheng,
            "model_version": moxing_banben,
            "prompt_version": TISHICI_BANBEN,
            "fallback_used": jiangji,
            "soil_moisture_status": fenxi_jieguo.get("soil_moisture_status", "unknown"),
            "fertility_status": fenxi_jieguo.get("fertility_status", "unknown"),
            "drought_risk": fenxi_jieguo.get("drought_risk", "unknown"),
            "weather_impact": fenxi_jieguo.get("weather_impact", ""),
            "three_day_forecast": fenxi_jieguo.get("three_day_forecast", []),
            "recommended_irrigation": fenxi_jieguo.get("recommended_irrigation", {}),
            "recommended_fertilizer": fenxi_jieguo.get("recommended_fertilizer", {}),
            "decision_basis": fenxi_jieguo.get("decision_basis", []),
            "warnings": fenxi_jieguo.get("warnings", []),
            "missing_data": fenxi_jieguo.get("missing_data", []),
            "confidence": zhixindu,
            "human_confirmation_required": renfu_fuhe,
            "analysis_summary": fenxi_jieguo.get("analysis_summary", ""),
            "crop_name": fenxi_jieguo.get("crop_name", zuowu.get("mingcheng", "")),
            "growth_stage": fenxi_jieguo.get("growth_stage", zuowu.get("shengyujie", "")),
            "current_soil_moisture": shidu,
            "recommended_irrigation_value": guangai,
            "recommended_fertilizer_value": shifei,
            "pump_runtime": beng_shijian,
            "safety_check": jiaoyan_jieguo,
            "elapsed_time": haoshi,
            "error": moxing_jieguo.get("error", ""),
            "jiance": jiance,
            "zuowu": zuowu,
            "tianqi": weather,
            "yuce": yuce_jieguo,
        }
        conn.close()
        return fanhui(jieguo, "AI分析完成" if not jiangji else "AI降级，使用规则算法完成")
    except Exception as exc:
        conn.rollback()
        conn.close()
        haoshi = round(time.time() - kaishi_shijian, 3)
        return fanhui(None, "AI分析异常：{}（耗时{}s）".format(str(exc)[:200], haoshi), 500)