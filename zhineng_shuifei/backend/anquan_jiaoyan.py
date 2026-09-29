"""安全校验服务 —— 对AI分析结果和决策建议进行13项安全校验。

运行环境：Python 3.10+，无第三方依赖
被 ai_jiekou.py 导入，在AI分析后、生成设备参数前执行校验。

校验内容：
  1. 灌溉量是否超过作物允许范围
  2. 施肥量是否超过作物和肥料允许范围
  3. 泵运行时长是否超过设备安全上限
  4. 土壤湿度过高时是否需要减少灌溉
  5. 降雨概率较高时是否需要减少灌溉
  6. 水箱液位是否足够
  7. 肥箱液位是否足够
  8. 设备是否在线
  9. AI置信度是否达到要求
  10. AI返回字段是否完整
  11. 推荐值单位是否正确
  12. 是否存在异常输入
  13. 是否有未处理的风险警告

返回规则：
  approved     通过基础校验（不等于可自动执行）
  manual_review 需人工复核
  rejected     禁止生成设备参数
"""
from datetime import datetime

GUANGAI_SHANGXIAN = 80
GUANGAI_XIAXIAN = 0
SHIFEI_SHANGXIAN = 30
SHIFEI_XIAXIAN = 0
BENG_SHIJIAN_SHANGXIAN = 120
SHIDU_GAO_XIAN = 48
JIANGYU_GAO_GAILV = 70
SHUIXIANG_XIAXIAN = 10
FEIXIANG_XIAXIAN = 10
AI_ZHIXINDU_XIAXIAN = 0.5


def shuzi(value, moren=0):
    """安全转浮点数。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return moren


def jiaoyan(guangai, shifei, beng_shijian, shidu, jiangyu_gailv,
            shuixiang_yewei, feixiang_yewei, shebei_zhuangtai,
            ai_zhixindu, ai_ziduan_wanzheng, tuijian_danwei,
            yichang_shuru, weichuli_yujing, conn=None):
    """执行13项安全校验。

    Args:
        guangai: 推荐灌溉量 L/m2
        shifei: 推荐施肥量 kg/亩
        beng_shijian: 泵运行时间 min
        shidu: 当前土壤湿度 %
        jiangyu_gailv: 降雨概率 %
        shuixiang_yewei: 水箱液位 %
        feixiang_yewei: 肥箱液位 %
        shebei_zhuangtai: 设备状态字符串
        ai_zhixindu: AI置信度 0-1
        ai_ziduan_wanzheng: AI字段是否完整 bool
        tuijian_danwei: 推荐值单位 dict
        yichang_shuru: 是否存在异常输入 bool
        weichuli_yujing: 未处理风险警告 list
        conn: 数据库连接（可选，用于读取阈值配置和写入校验记录）

    Returns:
        dict: passed, status, checked_items, warnings, blocked_reasons
    """
    jiancha = []
    jinggao = []
    zuzhi = []
    if conn:
        jiancha.append(("duqv_yuzhi", True, "从数据库读取阈值配置"))
        try:
            for row in conn.execute("SELECT leixing,mingcheng,zuixiao,zuida FROM yujing").fetchall():
                if row["leixing"] == "turang_shidu":
                    shidu_gao = shuzi(row["zuida"], SHIDU_GAO_XIAN)
                if row["leixing"] == "dian_daolv":
                    pass
        except Exception:
            shidu_gao = SHIDU_GAO_XIAN
    else:
        shidu_gao = SHIDU_GAO_XIAN
    guangai = shuzi(guangai)
    shifei = shuzi(shifei)
    beng_shijian = shuzi(beng_shijian)
    shidu = shuzi(shidu)
    jiangyu_gailv = shuzi(jiangyu_gailv)
    shuixiang_yewei = shuzi(shuixiang_yewei, 100)
    feixiang_yewei = shuzi(feixiang_yewei, 100)
    ai_zhixindu = shuzi(ai_zhixindu, 0)
    if guangai > GUANGAI_SHANGXIAN:
        zuzhi.append("灌溉量{}L/m2超过上限{}L/m2".format(guangai, GUANGAI_SHANGXIAN))
    elif guangai < GUANGAI_XIAXIAN:
        zuzhi.append("灌溉量{}L/m2低于下限{}L/m2".format(guangai, GUANGAI_XIAXIAN))
    jiancha.append(("guangai_fanwei", guangai <= GUANGAI_SHANGXIAN and guangai >= GUANGAI_XIAXIAN,
                    "灌溉量{}L/m2在允许范围[{},{}]内".format(guangai, GUANGAI_XIAXIAN, GUANGAI_SHANGXIAN)))
    if shifei > SHIFEI_SHANGXIAN:
        zuzhi.append("施肥量{}kg/亩超过上限{}kg/亩".format(shifei, SHIFEI_SHANGXIAN))
    elif shifei < SHIFEI_XIAXIAN:
        zuzhi.append("施肥量{}kg/亩低于下限{}kg/亩".format(shifei, SHIFEI_XIAXIAN))
    jiancha.append(("shifei_fanwei", shifei <= SHIFEI_SHANGXIAN and shifei >= SHIFEI_XIAXIAN,
                    "施肥量{}kg/亩在允许范围[{},{}]内".format(shifei, SHIFEI_XIAXIAN, SHIFEI_SHANGXIAN)))
    if beng_shijian > BENG_SHIJIAN_SHANGXIAN:
        zuzhi.append("泵运行时间{}min超过安全上限{}min".format(beng_shijian, BENG_SHIJIAN_SHANGXIAN))
    jiancha.append(("beng_shijian", beng_shijian <= BENG_SHIJIAN_SHANGXIAN,
                    "泵运行时间{}min在安全上限{}min内".format(beng_shijian, BENG_SHIJIAN_SHANGXIAN)))
    if shidu > shidu_gao and guangai > 10:
        jinggao.append("土壤湿度{}%偏高，建议减少灌溉量".format(shidu))
    jiancha.append(("shidu_gao_jiaoyan", not (shidu > shidu_gao and guangai > 10),
                    "土壤湿度{}%，高湿时灌溉量已调整".format(shidu)))
    if jiangyu_gailv >= JIANGYU_GAO_GAILV and guangai > 10:
        jinggao.append("降雨概率{}%较高，建议减少或暂停灌溉".format(jiangyu_gailv))
    jiancha.append(("jiangyu_jiaoyan", not (jiangyu_gailv >= JIANGYU_GAO_GAILV and guangai > 10),
                    "降雨概率{}%，高雨时灌溉量已调整".format(jiangyu_gailv)))
    if shuixiang_yewei < SHUIXIANG_XIAXIAN:
        zuzhi.append("水箱液位{}%低于下限{}%".format(shuixiang_yewei, SHUIXIANG_XIAXIAN))
    jiancha.append(("shuixiang_yewei", shuixiang_yewei >= SHUIXIANG_XIAXIAN,
                    "水箱液位{}%充足".format(shuixiang_yewei)))
    if feixiang_yewei < FEIXIANG_XIAXIAN:
        zuzhi.append("肥箱液位{}%低于下限{}%".format(feixiang_yewei, FEIXIANG_XIAXIAN))
    jiancha.append(("feixiang_yewei", feixiang_yewei >= FEIXIANG_XIAXIAN,
                    "肥箱液位{}%充足".format(feixiang_yewei)))
    shebei_zaixian = shebei_zhuangtai in ("在线", "正常", "人工登记可用", "待人工执行")
    if not shebei_zaixian:
        jinggao.append("设备状态为{}，请确认设备可用".format(shebei_zhuangtai))
    jiancha.append(("shebei_zaixian", shebei_zaixian, "设备状态：{}".format(shebei_zhuangtai)))
    if ai_zhixindu < AI_ZHIXINDU_XIAXIAN:
        jinggao.append("AI置信度{}低于要求{}，建议人工复核".format(ai_zhixindu, AI_ZHIXINDU_XIAXIAN))
    jiancha.append(("ai_zhixindu", ai_zhixindu >= AI_ZHIXINDU_XIAXIAN,
                    "AI置信度{}达到要求{}".format(ai_zhixindu, AI_ZHIXINDU_XIAXIAN)))
    if not ai_ziduan_wanzheng:
        zuzhi.append("AI返回字段不完整")
    jiancha.append(("ai_ziduan", ai_ziduan_wanzheng, "AI返回字段完整"))
    danwei_zhengque = True
    if isinstance(tuijian_danwei, dict):
        if tuijian_danwei.get("irrigation_unit") != "L/m2":
            danwei_zhengque = False
            zuzhi.append("灌溉量单位错误：{}".format(tuijian_danwei.get("irrigation_unit")))
        if tuijian_danwei.get("fertilizer_unit") != "kg/亩":
            danwei_zhengque = False
            zuzhi.append("施肥量单位错误：{}".format(tuijian_danwei.get("fertilizer_unit")))
    jiancha.append(("danwei_jiaoyan", danwei_zhengque, "推荐值单位正确"))
    if yichang_shuru:
        zuzhi.append("存在异常输入")
    jiancha.append(("yichang_shuru", not yichang_shuru, "无异常输入"))
    if weichuli_yujing:
        jinggao.append("存在未处理风险警告：{}".format(weichuli_yujing[:3]))
    jiancha.append(("weichuli_yujing", not weichuli_yujing, "无未处理风险警告"))
    if zuzhi:
        zhuangtai = "rejected"
        tongguo = False
    elif jinggao:
        zhuangtai = "manual_review"
        tongguo = True
    else:
        zhuangtai = "approved"
        tongguo = True
    jieguo = {
        "passed": tongguo,
        "status": zhuangtai,
        "checked_items": [{"name": item[0], "passed": item[1], "desc": item[2]} for item in jiancha],
        "warnings": jinggao,
        "blocked_reasons": zuzhi,
    }
    if conn:
        try:
            conn.execute(
                "INSERT INTO rizhi(caozuo_shijian,caozuo_leixing,caozuo_neirong,caozuoren) VALUES (?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "安全校验",
                 "状态:{}，警告:{}，阻止:{}".format(zhuangtai, len(jinggao), len(zuzhi)), "系统"),
            )
        except Exception:
            pass
    return jieguo