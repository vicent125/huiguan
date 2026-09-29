"""慧灌云控统一后端入口，所有业务接口采用小写拼音。

运行环境：Python 3.10+，Flask 3.x，flask-cors
依赖：fenxijuece.py(决策算法), shujuku.py(数据库), tianqifuwu.py(天气服务)
端口：5050（可通过环境变量PORT覆盖）
数据库：默认SQLite(nongye.db)，设置DATABASE_URL后使用MySQL

接口路由总览：
  /api/denglu          POST   用户登录
  /api/zonglan         GET    首页总览（指标+图表+预警）
  /api/jichu/<类型>    GET/POST/PUT/DELETE  基础信息CRUD（作物/土壤/肥料）
  /api/shuju/lishi     GET    历史监测查询
  /api/shuju/luru      POST   单条监测录入
  /api/shuju/piliang   POST   批量导入(xlsx/csv)
  /api/tianqi          GET    天气缓存查询
  /api/tianqi/shuaxin  POST   刷新雅安雨城区天气
  /api/tianqi/jingwei  GET    任意经纬度天气查询
  /api/yuce            POST   生成未来1-3天墒情预测
  /api/juece           POST   生成水肥决策建议
  /api/zhiling         POST   生成人工操作单（不直连硬件）
  /api/fankui          POST   登记实际执行量+触发模型更新
  /api/baogao          GET/POST  报告列表/生成
  /api/baogao/<id>/daochu  POST  导出PDF打印版
  /api/xitong/yujing   GET/PUT/DELETE  预警阈值管理
  /api/xitong/rizhi    GET    操作日志查询
"""
import csv
import io
import json
import os
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, render_template_string, request, send_from_directory
from flask_cors import CORS

from fenxijuece import ZengliangHuigui, gengxin_moxing, jisuan_xiuzheng_xishu, shengcheng_juece, shengcheng_yuce
from shujuku import lianjie, shengcheng_biao, zidian
from tianqifuwu import YUSHE_DIQU, baocun_tianqi, huoqu_jingwei_tianqi, huoqu_yucheng_tianqi
from ai_jiekou import ai_lantu

gen_lujing = os.path.dirname(os.path.abspath(__file__))
wangye_lujing = os.path.join(os.path.dirname(gen_lujing), "web")
app = Flask(__name__, static_folder=wangye_lujing, static_url_path="")
CORS(app)
app.register_blueprint(ai_lantu)


def fanhui(data=None, xiaoxi="操作成功", zhuangtai=200):
    return jsonify({"code": zhuangtai, "message": xiaoxi, "data": data}), zhuangtai


def shijian():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def jilu_rizhi(conn, leixing, neirong, caozuoren="系统用户"):
    conn.execute("INSERT INTO rizhi(caozuo_shijian,caozuo_leixing,caozuo_neirong,caozuoren) VALUES (?,?,?,?)", (shijian(), leixing, neirong, caozuoren))


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


def shuzi(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def shifou_zhen(value):
    return value is True or str(value).lower() in ("true", "1", "yes", "on")


ZIDUAN_MINGCHENG = {
    "basic_info": "基础信息", "monitor_summary": "监测数据摘要", "weather_summary": "天气摘要",
    "prediction": "水肥预测", "decision": "决策建议", "risk": "风险说明",
    "device_suggestion": "人工操作建议", "manual_operation": "人工操作建议",
    "crop": "作物信息", "area": "所在区域", "report_time": "报告时间",
    "drought": "旱情分析", "notice": "注意事项", "status": "状态",
    "id": "编号", "zuowu_id": "作物编号", "jiance_id": "监测记录编号", "shebei_id": "原设备编号",
    "mingcheng": "名称", "shengyujie": "生育期", "xushui_xishu": "需水系数",
    "xufei_xishu": "需肥系数", "shiyi_turang": "适宜土壤", "mubiao_shidu": "目标土壤湿度",
    "tuijian_shuifen": "水分管理建议", "tuijian_feiliao": "肥料管理建议", "shuoming": "说明",
    "turang_shidu": "土壤湿度", "turang_wendu": "土壤温度", "kongqi_shidu": "空气湿度",
    "guangzhao": "光照强度", "dian_daolv": "电导率", "jilu_shijian": "记录时间",
    "yubaoriqi": "预报日期", "zuigao_wendu": "最高温度", "zuidi_wendu": "最低温度",
    "jiangyu_gailv": "降雨概率", "jiangyu_liang": "降雨量", "tianqi_leixing": "天气类型",
    "zhengfa_liang": "蒸散量", "diqu": "地区", "shuju_laiyuan": "数据来源", "gengxin_shijian": "更新时间",
    "yuce_tianshu": "预测天数", "xushui_json": "预测需水量", "xufei_json": "预测需肥量",
    "shidu_json": "预测土壤湿度", "fenxi": "预测分析", "tianqi_shuoming": "天气预测说明",
    "zhuangtai": "状态", "feili_zhuangtai": "肥力状态", "guangai_liang": "灌溉量",
    "shifei_liang": "施肥量", "beng_yunxing": "泵运行时间", "yuanyin": "决策依据",
    "chuangjian_shijian": "创建时间", "xiafa_shijian": "人工传达时间", "caozuoren": "操作人",
    "caozuo_beizhu": "人工操作备注", "zhiling_id": "人工操作单编号",
    "shiji_guangai": "实际灌溉量", "shiji_shifei": "实际施肥量", "shangbao_shijian": "登记时间",
}


def zhuanhuan_zhongwen_ziduan(value):
    if isinstance(value, dict):
        return {ZIDUAN_MINGCHENG.get(key, key): zhuanhuan_zhongwen_ziduan(item) for key, item in value.items()}
    if isinstance(value, list):
        return [zhuanhuan_zhongwen_ziduan(item) for item in value]
    return value


@app.get("/")
def shouye():
    return send_from_directory(wangye_lujing, "index.html")


@app.get("/api/health")
def health_check():
    return jsonify({"code": 200, "message": "服务运行正常", "data": None})


# 前端登录页调用：校验本地系统用户，硬件侧不参与认证。
@app.post("/api/denglu")
def denglu():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    user = conn.execute("SELECT id,zhanghao,mingcheng,juese FROM yonghu WHERE zhanghao=? AND mima=?", (data.get("zhanghao"), data.get("mima"))).fetchone()
    if user:
        jilu_rizhi(conn, "用户登录", f"账号 {data.get('zhanghao')} 登录系统", zidian(user)["mingcheng"])
        conn.commit()
    conn.close()
    if not user:
        return fanhui(None, "账号或密码错误", 401)
    return fanhui({"yonghu": zidian(user), "token": "local-session"}, "登录成功")


# 前端首页调用：一次返回顶部指标、中部状态及六类图表数据。
@app.get("/api/zonglan")
def zonglan():
    conn = lianjie()
    jiance = huoqu_jiance(conn)
    zuowu = huoqu_zuowu(conn, int(jiance.get("zuowu_id", 3)))
    weather = huoqu_tianqi(conn)
    monitor_rows = [zidian(x) for x in conn.execute("SELECT * FROM jiance ORDER BY jilu_shijian DESC,id DESC LIMIT 30").fetchall()]
    decisions = [zidian(x) for x in conn.execute("SELECT * FROM juece ORDER BY jilu_shijian DESC,id DESC LIMIT 30").fetchall()]
    today = date.today().isoformat()
    alerts, distribution = [], {"缺水": 0, "湿度偏高": 0, "EC异常": 0}
    for row in monitor_rows:
        moisture, ec = shuzi(row.get("turang_shidu")), shuzi(row.get("dian_daolv"))
        if moisture < 18:
            distribution["缺水"] += 1
        if moisture > 48:
            distribution["湿度偏高"] += 1
        if ec < .5 or ec > 2.5:
            distribution["EC异常"] += 1
    moisture = shuzi(jiance.get("turang_shidu"))
    ec = shuzi(jiance.get("dian_daolv"))
    if moisture < 18 or moisture > 48:
        alerts.append({"dengji": "二级", "leixing": "土壤湿度", "neirong": f"当前土壤湿度 {moisture:.1f}% 超出适宜范围"})
    if ec < .5 or ec > 2.5:
        alerts.append({"dengji": "三级", "leixing": "土壤电导率", "neirong": f"当前 EC {ec:.2f} mS/cm 超出阈值"})
    seven_days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    count_by_day = {day: 0 for day in seven_days}
    for item in decisions:
        day = str(item.get("jilu_shijian", ""))[:10]
        if day in count_by_day:
            count_by_day[day] += 1
    latest_decision = decisions[0] if decisions else None
    result = {
        "counts": {
            "jiance": sum(1 for x in monitor_rows if str(x.get("jilu_shijian", ""))[:10] == today),
            "yujing": len(alerts),
            "juece": sum(1 for x in decisions if str(x.get("jilu_shijian", ""))[:10] == today),
        },
        "jiance": jiance, "zuowu": zuowu, "tianqi": weather, "alerts": alerts,
        "latest_decision": latest_decision,
        "trends": {
            "jiance": list(reversed(monitor_rows[:7])),
            "guangai": list(reversed(decisions[:7])),
            "shifei": list(reversed(decisions[:7])),
            "tianqi": weather,
            "juece_count": [{"riqi": day, "shuliang": count_by_day[day]} for day in seven_days],
            "yujing": [{"leixing": key, "shuliang": value} for key, value in distribution.items()],
        },
    }
    conn.close()
    return fanhui(result)


# 前端基础信息四个子页面调用。
@app.get("/api/jichu/<leixing>")
def jichu_liebiao(leixing):
    biao = {"zuowu": "zuowu", "turang": "turang", "feiliao": "feiliao"}.get(leixing)
    if not biao:
        return fanhui(None, "基础信息类型无效", 400)
    conn = lianjie()
    rows = [zidian(x) for x in conn.execute(f"SELECT * FROM {biao} ORDER BY id").fetchall()]
    if leixing == "zuowu":
        for row in rows:
            row["jieduan"] = [zidian(x) for x in conn.execute("SELECT * FROM zuowu_jieduan WHERE zuowu_id=? ORDER BY id", (row["id"],)).fetchall()]
    conn.close()
    return fanhui(rows)


@app.post("/api/jichu/<leixing>")
def jichu_xinzeng(leixing):
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    try:
        if leixing == "zuowu":
            conn.execute("INSERT INTO zuowu(mingcheng,shengyujie,xushui_xishu,xufei_xishu,shiyi_turang,mubiao_shidu,tuijian_shuifen,tuijian_feiliao,shuoming) VALUES (?,?,?,?,?,?,?,?,?)", tuple(data.get(x) for x in ["mingcheng", "shengyujie", "xushui_xishu", "xufei_xishu", "shiyi_turang", "mubiao_shidu", "tuijian_shuifen", "tuijian_feiliao", "shuoming"]))
        elif leixing == "turang":
            conn.execute("INSERT INTO turang(zhidi,rongzhong,chitian_chishuiliang,ph,dian_daolv,qita) VALUES (?,?,?,?,?,?)", tuple(data.get(x) for x in ["zhidi", "rongzhong", "chitian_chishuiliang", "ph", "dian_daolv", "qita"]))

        elif leixing == "feiliao":
            conn.execute("INSERT INTO feiliao(mingcheng,dan,lin,jia) VALUES (?,?,?,?)", (data.get("mingcheng"), data.get("dan", 0), data.get("lin", 0), data.get("jia", 0)))
        else:
            conn.close()
            return fanhui(None, "基础信息类型无效", 400)
        jilu_rizhi(conn, "新增基础信息", f"新增 {leixing} 记录")
        conn.commit()
        return fanhui({}, "保存成功")
    except Exception as exc:
        conn.rollback()
        return fanhui(None, str(exc), 400)
    finally:
        conn.close()


@app.put("/api/jichu/<leixing>/<int:record_id>")
def jichu_gengxin(leixing, record_id):
    data = request.get_json(silent=True) or {}
    fields = {
        "zuowu": ["mingcheng", "shengyujie", "xushui_xishu", "xufei_xishu", "shiyi_turang", "mubiao_shidu", "tuijian_shuifen", "tuijian_feiliao", "shuoming"],
        "turang": ["zhidi", "rongzhong", "chitian_chishuiliang", "ph", "dian_daolv", "qita"],

        "feiliao": ["mingcheng", "dan", "lin", "jia"],
    }.get(leixing)
    if not fields:
        return fanhui(None, "基础信息类型无效", 400)
    changed = [field for field in fields if field in data]
    if not changed:
        return fanhui(None, "没有可更新字段", 400)
    conn = lianjie()
    conn.execute(f"UPDATE {leixing} SET " + ",".join(f"{field}=?" for field in changed) + " WHERE id=?", tuple(data[field] for field in changed) + (record_id,))
    jilu_rizhi(conn, "修改基础信息", f"修改 {leixing} #{record_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "更新成功")


# 前端基础信息管理页调用：删除指定记录，支持作物/土壤/设备/肥料。
@app.delete("/api/jichu/<leixing>/<int:record_id>")
def jichu_shanchu(leixing, record_id):
    biao = {"zuowu": "zuowu", "turang": "turang", "feiliao": "feiliao"}.get(leixing)
    if not biao:
        return fanhui(None, "基础信息类型无效", 400)
    conn = lianjie()
    if leixing == "zuowu":
        conn.execute("DELETE FROM zuowu_jieduan WHERE zuowu_id=?", (record_id,))
    conn.execute(f"DELETE FROM {biao} WHERE id=?", (record_id,))
    jilu_rizhi(conn, "删除基础信息", f"删除 {leixing} #{record_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


# 前端历史监测子页面调用，支持开始和结束日期筛选。
@app.get("/api/shuju/lishi")
def shuju_lishi():
    start, end = request.args.get("kaishi"), request.args.get("jieshu")
    sql, params = "SELECT j.*,z.mingcheng AS zuowu_mingcheng FROM jiance j LEFT JOIN zuowu z ON z.id=j.zuowu_id WHERE 1=1", []
    if start:
        sql += " AND j.jilu_shijian>=?"
        params.append(start + " 00:00:00")
    if end:
        sql += " AND j.jilu_shijian<=?"
        params.append(end + " 23:59:59")
    sql += " ORDER BY j.jilu_shijian DESC,j.id DESC LIMIT 500"
    conn = lianjie()
    rows = [zidian(x) for x in conn.execute(sql, tuple(params)).fetchall()]
    conn.close()
    return fanhui(rows)


def _baocun_jiance(conn, data):
    moisture = shuzi(data.get("turang_shidu"), -1)
    ec = shuzi(data.get("dian_daolv"), -1)
    if not 0 <= moisture <= 100 or not 0 <= ec <= 20:
        raise ValueError("土壤湿度应在 0-100%，EC 应在 0-20 mS/cm")
    conn.execute("INSERT INTO jiance(zuowu_id,shengyujie,turang_shidu,turang_wendu,kongqi_shidu,guangzhao,dian_daolv,jilu_shijian) VALUES (?,?,?,?,?,?,?,?)", (int(data.get("zuowu_id", 3)), data.get("shengyujie", "油脂积累期"), moisture, shuzi(data.get("turang_wendu"), 25), shuzi(data.get("kongqi_shidu"), 70), shuzi(data.get("guangzhao"), 15000), ec, data.get("jilu_shijian") or shijian()))


@app.post("/api/shuju/luru")
def shuju_luru():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    try:
        _baocun_jiance(conn, data)
        jilu_rizhi(conn, "监测录入", "手动新增一条监测数据")
        conn.commit()
        return fanhui({}, "监测数据已保存")
    except ValueError as exc:
        conn.rollback()
        return fanhui(None, str(exc), 400)
    finally:
        conn.close()


# 前端批量导入子页面调用，支持 xlsx 和 csv。
@app.post("/api/shuju/piliang")
def shuju_piliang():
    uploaded = request.files.get("file")
    if not uploaded:
        return fanhui(None, "请选择 Excel 或 CSV 文件", 400)
    columns = {"作物ID": "zuowu_id", "生育期": "shengyujie", "土壤湿度": "turang_shidu", "土壤温度": "turang_wendu", "空气湿度": "kongqi_shidu", "光照强度": "guangzhao", "电导率": "dian_daolv", "记录时间": "jilu_shijian"}
    try:
        if uploaded.filename.lower().endswith(".csv"):
            text = uploaded.stream.read().decode("utf-8-sig")
            source_rows = list(csv.DictReader(io.StringIO(text)))
        else:
            from openpyxl import load_workbook
            book = load_workbook(uploaded.stream, data_only=True, read_only=True)
            sheet = book.active
            values = list(sheet.iter_rows(values_only=True))
            headers = [str(x).strip() if x is not None else "" for x in values[0]]
            source_rows = [dict(zip(headers, row)) for row in values[1:]]
        if len(source_rows) > 5000:
            return fanhui(None, "单次最多导入 5000 条数据", 400)
        conn, success, failed = lianjie(), 0, []
        for index, row in enumerate(source_rows, 2):
            normalized = {columns.get(key, key): value for key, value in row.items()}
            try:
                _baocun_jiance(conn, normalized)
                success += 1
            except Exception as exc:
                failed.append({"hang": index, "yuanyin": str(exc)})
        jilu_rizhi(conn, "批量导入", f"导入成功 {success} 条，失败 {len(failed)} 条")
        conn.commit()
        conn.close()
        return fanhui({"success": success, "failed": len(failed), "errors": failed[:20]}, "批量导入完成")
    except ImportError:
        return fanhui(None, "读取 Excel 需要先安装 openpyxl", 500)
    except Exception as exc:
        return fanhui(None, f"文件解析失败：{exc}", 400)


# 前端历史监测子页面调用：删除指定监测记录。
@app.delete("/api/shuju/<int:record_id>")
def shuju_shanchu(record_id):
    conn = lianjie()
    conn.execute("DELETE FROM jiance WHERE id=?", (record_id,))
    jilu_rizhi(conn, "删除监测", f"删除监测记录 #{record_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


# 前端天气分析页调用：返回雅安市雨城区缓存；刷新接口主动获取公开天气。
@app.get("/api/tianqi")
def tianqi():
    conn = lianjie()
    rows = huoqu_tianqi(conn)
    conn.close()
    return fanhui({"diqu": "四川省雅安市雨城区", "forecast_list": rows})


@app.post("/api/tianqi/shuaxin")
def tianqi_shuaxin():
    try:
        rows = huoqu_yucheng_tianqi()
        conn = lianjie()
        baocun_tianqi(conn, rows)
        jilu_rizhi(conn, "天气更新", "更新雅安市雨城区未来三天天气")
        conn.commit()
        conn.close()
        return fanhui({"diqu": "四川省雅安市雨城区", "forecast_list": rows}, "天气更新成功")
    except Exception as exc:
        conn = lianjie()
        rows = huoqu_tianqi(conn)
        conn.close()
        return fanhui({"diqu": "四川省雅安市雨城区", "forecast_list": rows, "warning": f"在线更新失败，继续使用缓存：{exc}"}, "已使用本地缓存")


# 前端天气分析页调用：返回预设地区列表（雅安雨城区、西昌等）。
@app.get("/api/tianqi/diqu")
def tianqi_diqu():
    return fanhui(YUSHE_DIQU)


# 前端天气分析页调用：根据任意经纬度获取三天天气预报。
@app.get("/api/tianqi/jingwei")
def tianqi_jingwei():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    diming = request.args.get("diming")
    if lat is None or lon is None:
        return fanhui(None, "请提供lat(纬度)和lon(经度)参数", 400)
    try:
        rows = huoqu_jingwei_tianqi(lat, lon, diming)
        return fanhui({"diqu": diming or f"经纬度({lat},{lon})", "weidu": lat, "jingdu": lon, "forecast_list": rows}, "天气查询成功")
    except Exception as exc:
        return fanhui(None, f"天气查询失败：{exc}", 500)


# 前端天气分析页调用：刷新指定预设地区的天气并缓存。
@app.post("/api/tianqi/shuaxin_diqu")
def tianqi_shuaxin_diqu():
    data = request.get_json(silent=True) or {}
    lat = data.get("weidu")
    lon = data.get("jingdu")
    diming = data.get("diming", "未知地区")
    if lat is None or lon is None:
        return fanhui(None, "请提供weidu(纬度)和jingdu(经度)", 400)
    try:
        rows = huoqu_jingwei_tianqi(float(lat), float(lon), diming)
        conn = lianjie()
        baocun_tianqi(conn, rows)
        jilu_rizhi(conn, "天气更新", f"更新{diming}未来三天天气")
        conn.commit()
        conn.close()
        return fanhui({"diqu": diming, "weidu": lat, "jingdu": lon, "forecast_list": rows}, "天气更新成功")
    except Exception as exc:
        return fanhui(None, f"在线更新失败：{exc}", 500)


# 前端预测分析页调用：可选 1-3 天及是否采用天气数据。
# 支持三种天气来源：雅安雨城区(默认)、西昌市、自定义经纬度(前端传入tianqi_data)
@app.post("/api/yuce")
def yuce():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    jiance = huoqu_jiance(conn)
    zuowu = huoqu_zuowu(conn, int(data.get("zuowu_id", jiance.get("zuowu_id", 3))))
    use_weather = shifou_zhen(data.get("shiyong_tianqi", True))
    # 优先使用前端传入的天气数据（西昌/自定义经纬度），否则从数据库读取（雨城区缓存）
    if data.get("tianqi_data"):
        weather = data["tianqi_data"]
    else:
        weather = huoqu_tianqi(conn)
    result = shengcheng_yuce(jiance, weather, zuowu, data.get("tianshu", 3), use_weather)
    conn.execute("INSERT INTO yuce(zuowu_id,yuce_tianshu,xushui_json,xufei_json,shidu_json,fenxi,tianqi_shuoming,jilu_shijian) VALUES (?,?,?,?,?,?,?,?)", (zuowu["id"], len(result["dates"]), json.dumps(result["xushui"]), json.dumps(result["xufei"]), json.dumps(result["shidu"]), result["fenxi"], result["tianqi_shuoming"], shijian()))
    history = [zidian(x) for x in conn.execute("SELECT turang_shidu,jilu_shijian FROM jiance WHERE zuowu_id=? ORDER BY jilu_shijian DESC LIMIT 7", (zuowu["id"],)).fetchall()]
    jilu_rizhi(conn, "预测分析", f"生成 {len(result['dates'])} 日预测，天气数据：{'采用' if use_weather else '未采用'}")
    conn.commit()
    conn.close()
    return fanhui({"jiance": jiance, "zuowu": zuowu, "tianqi": weather, "lishi": list(reversed(history)), **result})


# 前端预测分析页调用：删除指定预测记录。
@app.delete("/api/yuce/<int:record_id>")
def yuce_shanchu(record_id):
    conn = lianjie()
    conn.execute("DELETE FROM yuce WHERE id=?", (record_id,))
    jilu_rizhi(conn, "删除预测", f"删除预测记录 #{record_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


# 前端水肥决策页调用：生成决策建议（决策施水施肥）。
# 流程：读取监测→计算修正系数→加载增量回归→生成决策→存库→返回人工操作参数
@app.post("/api/juece")
def juece():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    jiance = huoqu_jiance(conn)
    for field in ("turang_shidu", "dian_daolv", "turang_wendu", "kongqi_shidu", "guangzhao"):
        if data.get(field) not in (None, ""):
            jiance[field] = data[field]
    zuowu = huoqu_zuowu(conn, int(data.get("zuowu_id", jiance.get("zuowu_id", 3))))
    weather = huoqu_tianqi(conn)
    xiuzheng = jisuan_xiuzheng_xishu(conn)
    huigui = ZengliangHuigui.jiazai(conn, "guangai")
    shidu = shuzi(jiance.get("turang_shidu"), 30)
    huigui_yuce = huigui.yuce(shidu) if huigui.n >= 2 else None
    result = shengcheng_juece(jiance, weather, zuowu, data.get("yuce"), xiuzheng, huigui_yuce)
    conn.execute("INSERT INTO juece(jiance_id,zuowu_id,zhuangtai,feili_zhuangtai,guangai_liang,shifei_liang,beng_yunxing,yuanyin,jilu_shijian) VALUES (?,?,?,?,?,?,?,?,?)", (jiance.get("id"), zuowu["id"], result["water_status"], result["fertility_status"], result["recommended_irrigation"], result["recommended_fertilization"], result["pump_runtime"], result["reason"], shijian()))
    history = [zidian(x) for x in conn.execute("SELECT guangai_liang,shifei_liang,jilu_shijian FROM juece ORDER BY jilu_shijian DESC LIMIT 7").fetchall()]
    jilu_rizhi(conn, "水肥决策", "生成软件分析建议，等待人员确认")
    conn.commit()
    conn.close()
    result.update({"zuowu": zuowu, "jiance": jiance, "trend": list(reversed(history)), "xiafa_fangshi": "人工向硬件操作人员传达，不进行接口下发"})
    return fanhui(result, "决策已生成")


# 前端水肥决策页调用：删除指定决策记录。
@app.delete("/api/juece/<int:record_id>")
def juece_shanchu(record_id):
    conn = lianjie()
    conn.execute("DELETE FROM juece WHERE id=?", (record_id,))
    jilu_rizhi(conn, "删除决策", f"删除决策记录 #{record_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


# 前端设备协同页调用：设备信息由人员维护，操作单不发送到硬件。
@app.get("/api/shebei")
def shebei():
    conn = lianjie()
    result = {
        "orders": [zidian(x) for x in conn.execute("SELECT * FROM zhiling ORDER BY id DESC LIMIT 30").fetchall()],
        "feedback": [zidian(x) for x in conn.execute("SELECT * FROM fankui ORDER BY id DESC LIMIT 30").fetchall()],
    }
    conn.close()
    return fanhui(result)


@app.post("/api/zhiling")
def zhiling():
    data = request.get_json(silent=True) or {}
    water, fert = shuzi(data.get("guangai_liang")), shuzi(data.get("shifei_liang"))
    runtime = shuzi(data.get("beng_yunxing"), water / max(shuzi(data.get("liuliang"), 2), .1))
    conn = lianjie()
    cursor = conn.execute("INSERT INTO zhiling(shebei_id,guangai_liang,shifei_liang,beng_yunxing,zhuangtai,chuangjian_shijian,caozuoren,caozuo_beizhu) VALUES (?,?,?,?,?,?,?,?)", (data.get("shebei_id", 1), water, fert, runtime, "待人工执行", shijian(), data.get("caozuoren", "系统用户"), data.get("caozuo_beizhu", "软件生成参数，未连接硬件")))
    jilu_rizhi(conn, "生成设备参数", f"生成灌溉 {water} L/亩、施肥 {fert} kg/亩、泵运行 {runtime} min 的人工操作单")
    conn.commit()
    result = {"zhiling_id": cursor.lastrowid, "zhuangtai": "待人工执行", "shuoming": "系统未连接水肥机，请人工核对后在实体设备上操作"}
    conn.close()
    return fanhui(result, "人工操作单已生成")


@app.post("/api/zhiling/<int:zhiling_id>/queren")
def zhiling_queren(zhiling_id):
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    conn.execute("UPDATE zhiling SET zhuangtai=?,xiafa_shijian=?,caozuoren=?,caozuo_beizhu=? WHERE id=?", ("已人工传达", shijian(), data.get("caozuoren", "现场操作员"), data.get("caozuo_beizhu", "已将参数人工传达给硬件操作人员"), zhiling_id))
    jilu_rizhi(conn, "人工确认", f"操作单 #{zhiling_id} 已由人员确认传达", data.get("caozuoren", "现场操作员"))
    conn.commit()
    conn.close()
    return fanhui({"zhuangtai": "已人工传达"}, "已登记人工传达")


# 前端设备协同页调用：登记实际执行量并触发模型自更新。
# 流程：保存反馈→更新指令状态→调用gengxin_moxing增量更新回归模型
@app.post("/api/fankui")
def fankui_xinzeng():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    conn.execute("INSERT INTO fankui(zhiling_id,shiji_guangai,shiji_shifei,zhuangtai,shangbao_shijian) VALUES (?,?,?,?,?)", (data.get("zhiling_id"), shuzi(data.get("shiji_guangai")), shuzi(data.get("shiji_shifei")), data.get("zhuangtai", "人工登记已完成"), shijian()))
    conn.execute("UPDATE zhiling SET zhuangtai='已人工执行' WHERE id=?", (data.get("zhiling_id"),))
    shiji_guangai = shuzi(data.get("shiji_guangai"))
    if shiji_guangai > 0:
        jiance = huoqu_jiance(conn)
        gengxin_moxing(conn, jiance, shiji_guangai)
    jilu_rizhi(conn, "执行反馈", f"人工登记操作单 #{data.get('zhiling_id')} 的实际执行量")
    conn.commit()
    conn.close()
    return fanhui({}, "实际执行量已登记")


# 前端设备协同页调用：删除指定指令及其反馈。
@app.delete("/api/zhiling/<int:zhiling_id>")
def zhiling_shanchu(zhiling_id):
    conn = lianjie()
    conn.execute("DELETE FROM fankui WHERE zhiling_id=?", (zhiling_id,))
    conn.execute("DELETE FROM zhiling WHERE id=?", (zhiling_id,))
    jilu_rizhi(conn, "删除指令", f"删除操作单 #{zhiling_id} 及其反馈")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


# 前端报告中心调用：列表、详情、生成和浏览器 PDF 打印。
@app.get("/api/baogao")
def baogao_liebiao():
    conn = lianjie()
    rows = [zidian(x) for x in conn.execute("SELECT id,biaoti,chuangjian_shijian,gengxin_shijian,zuowu,zhaiyao,zhuangtai,daochuren,daochu_zhuangtai FROM baogao ORDER BY id DESC").fetchall()]
    conn.close()
    return fanhui(rows)


@app.post("/api/baogao")
def baogao_xinzeng():
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    monitor, weather = huoqu_jiance(conn), huoqu_tianqi(conn)
    crop = huoqu_zuowu(conn, int(monitor.get("zuowu_id", 3)))
    decision = zidian(conn.execute("SELECT * FROM juece ORDER BY id DESC LIMIT 1").fetchone()) or {}
    prediction = zidian(conn.execute("SELECT * FROM yuce ORDER BY id DESC LIMIT 1").fetchone()) or {}
    order = zidian(conn.execute("SELECT * FROM zhiling ORDER BY id DESC LIMIT 1").fetchone()) or {}
    # 动态地区：前端传入diqu参数，默认雅安市雨城区
    diqu = data.get("diqu", "四川省雅安市雨城区")
    diqu_jiancheng = diqu.replace("四川省", "").replace("市", "").replace("州", "")
    content = data.get("neirong") or {
        "basic_info": {"crop": crop, "area": diqu, "report_time": shijian()},
        "monitor_summary": monitor, "weather_summary": weather,
        "prediction": prediction, "decision": decision,
        "risk": {"drought": prediction.get("fenxi", "尚未生成预测"), "notice": "建议量需由现场人员复核，不直接控制设备"},
        "manual_operation": order or {"status": "尚未生成人工操作单"},
    }
    title = data.get("biaoti", f"{diqu_jiancheng}油橄榄水肥分析报告-{datetime.now():%Y%m%d%H%M}")
    summary = data.get("zhaiyao", f"汇总监测、{diqu}天气、预测、决策和人工执行建议")
    now = shijian()
    cursor = conn.execute("INSERT INTO baogao(biaoti,chuangjian_shijian,gengxin_shijian,zuowu,zhaiyao,zhuangtai,daochuren,daochu_zhuangtai,neirong_json) VALUES (?,?,?,?,?,?,?,?,?)", (title, now, now, crop.get("mingcheng", "油橄榄"), summary, "已生成", "", "未导出", json.dumps(content, ensure_ascii=False, default=str)))
    jilu_rizhi(conn, "报告生成", title)
    conn.commit()
    result = zidian(conn.execute("SELECT * FROM baogao WHERE id=?", (cursor.lastrowid,)).fetchone())
    conn.close()
    result.pop("neirong_json", None)
    return fanhui(result, "报告已生成")


@app.get("/api/baogao/<int:baogao_id>")
def baogao_xiangqing(baogao_id):
    conn = lianjie()
    row = zidian(conn.execute("SELECT * FROM baogao WHERE id=?", (baogao_id,)).fetchone())
    conn.close()
    if not row:
        return fanhui(None, "报告不存在", 404)
    row["neirong"] = zhuanhuan_zhongwen_ziduan(json.loads(row.pop("neirong_json") or "{}"))
    return fanhui(row)


@app.post("/api/baogao/<int:baogao_id>/daochu")
def baogao_daochu(baogao_id):
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    conn.execute("UPDATE baogao SET daochuren=?,daochu_zhuangtai=?,gengxin_shijian=? WHERE id=?", (data.get("daochuren", "系统管理员"), "已生成打印版", shijian(), baogao_id))
    jilu_rizhi(conn, "报告导出", f"生成报告 #{baogao_id} 的 PDF 打印版", data.get("daochuren", "系统管理员"))
    conn.commit()
    conn.close()
    return fanhui({"url": f"/baogao/dayin/{baogao_id}"}, "打印版已生成")


# 前端报告中心调用：删除指定报告。
@app.delete("/api/baogao/<int:baogao_id>")
def baogao_shanchu(baogao_id):
    conn = lianjie()
    conn.execute("DELETE FROM baogao WHERE id=?", (baogao_id,))
    jilu_rizhi(conn, "删除报告", f"删除报告 #{baogao_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


@app.get("/baogao/dayin/<int:baogao_id>")
def baogao_dayin(baogao_id):
    conn = lianjie()
    row = zidian(conn.execute("SELECT * FROM baogao WHERE id=?", (baogao_id,)).fetchone())
    conn.close()
    if not row:
        return "报告不存在", 404
    content = zhuanhuan_zhongwen_ziduan(json.loads(row.get("neirong_json") or "{}"))
    template = """<!doctype html><html lang='zh-CN'><head><meta charset='UTF-8'><title>{{ row.biaoti }}</title><style>body{font-family:'Microsoft YaHei',sans-serif;color:#24342c;max-width:900px;margin:30px auto;line-height:1.7}h1{border-bottom:3px solid #3d7b59;padding-bottom:12px}h2{font-size:18px;margin-top:28px;color:#24553d}table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #d8e2db;padding:8px;text-align:left}pre{white-space:pre-wrap;background:#f4f7f4;padding:14px}.no-print{margin-bottom:20px}@media print{.no-print{display:none}body{margin:0}}</style></head><body><button class='no-print' onclick='window.print()'>打印或另存为 PDF</button><h1>{{ row.biaoti }}</h1><p>作物：{{ row.zuowu }}　创建时间：{{ row.chuangjian_shijian }}　导出人：{{ row.daochuren }}</p><p>{{ row.zhaiyao }}</p>{% for title,value in sections %}<h2>{{ title }}</h2><pre>{{ value }}</pre>{% endfor %}</body></html>"""
    sections = [(key, json.dumps(value, ensure_ascii=False, indent=2, default=str)) for key, value in content.items()]
    return render_template_string(template, row=row, sections=sections)


# 前端系统管理页调用。
@app.get("/api/xitong/yujing")
def yujing():
    conn = lianjie()
    rows = [zidian(x) for x in conn.execute("SELECT * FROM yujing ORDER BY id").fetchall()]
    conn.close()
    return fanhui(rows)


@app.put("/api/xitong/yujing/<int:yujing_id>")
def yujing_gengxin(yujing_id):
    data = request.get_json(silent=True) or {}
    conn = lianjie()
    conn.execute("UPDATE yujing SET zuixiao=?,zuida=?,dengji=?,shuoming=? WHERE id=?", (data.get("zuixiao"), data.get("zuida"), data.get("dengji"), data.get("shuoming"), yujing_id))
    jilu_rizhi(conn, "阈值设置", f"更新预警阈值 #{yujing_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "阈值已更新")


# 前端系统管理页调用：删除指定预警阈值。
@app.delete("/api/xitong/yujing/<int:yujing_id>")
def yujing_shanchu(yujing_id):
    conn = lianjie()
    conn.execute("DELETE FROM yujing WHERE id=?", (yujing_id,))
    jilu_rizhi(conn, "删除阈值", f"删除预警阈值 #{yujing_id}")
    conn.commit()
    conn.close()
    return fanhui({}, "删除成功")


@app.get("/api/xitong/rizhi")
def rizhi():
    conn = lianjie()
    rows = [zidian(x) for x in conn.execute("SELECT * FROM rizhi ORDER BY id DESC LIMIT 100").fetchall()]
    conn.close()
    return fanhui(rows)


if __name__ == "__main__":
    shengcheng_biao()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=os.environ.get("FLASK_DEBUG") == "1")
