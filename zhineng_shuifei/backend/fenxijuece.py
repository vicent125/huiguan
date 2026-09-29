"""水肥决策核心算法模块 —— 规则引擎 + 增量学习 + 反馈修正。

运行环境：Python 3.10+，无第三方依赖（仅用标准库）。
被 yingyong.py 导入，提供预测和决策两个核心能力。

设计思路：
  1. AI分析土壤墒情/气候/电导率 → 决策施水施肥量
  2. 预测未来3天墒情变化趋势 → 干旱/积水预警
  3. 人工反馈实际执行量 → 增量更新模型（方案2线性回归 + 方案1 EWMA修正系数）

算法选择说明：
  项目数据仅13条，不足以训练传统ML模型。
  采用可解释规则算法（透明、可复现）+ 在线增量学习（逐条更新、无需批量训练）。
"""
from datetime import datetime


def shuzi(value, moren=0):
    """安全转浮点数，失败时返回默认值。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return moren


class ZengliangHuigui:
    """方案2：增量式一元线性回归（在线学习）。

    逐条更新参数，无需批量训练。递推公式基于Welford算法，
    数值稳定且 O(1) 时间复杂度。持久化到 moxing_canshu 表。
    """

    def __init__(self):
        self.n = 0
        self.mean_x = 0.0
        self.mean_y = 0.0
        self.var_x = 0.0
        self.cov_xy = 0.0

    def gengxin(self, x, y):
        """来一条新数据(x,y)就更新回归参数。"""
        self.n += 1
        dx = x - self.mean_x
        dy = y - self.mean_y
        self.mean_x += dx / self.n
        self.mean_y += dy / self.n
        self.var_x += dx * (x - self.mean_x)
        self.cov_xy += dx * (y - self.mean_y)

    def yuce(self, x):
        """根据当前参数预测 y。数据不足时返回均值。"""
        if self.n < 2 or self.var_x == 0:
            return self.mean_y
        a = self.cov_xy / self.var_x
        b = self.mean_y - a * self.mean_x
        return a * x + b

    def baocun(self, conn, mingcheng="guangai"):
        """持久化参数到数据库，重启后不丢失。"""
        conn.execute(
            "INSERT INTO moxing_canshu(mingcheng,n,mean_x,mean_y,var_x,cov_xy,gengxin_shijian) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(mingcheng) DO UPDATE SET n=excluded.n, mean_x=excluded.mean_x, mean_y=excluded.mean_y, "
            "var_x=excluded.var_x, cov_xy=excluded.cov_xy, gengxin_shijian=excluded.gengxin_shijian",
            (mingcheng, self.n, self.mean_x, self.mean_y, self.var_x, self.cov_xy, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    @classmethod
    def jiazai(cls, conn, mingcheng="guangai"):
        """从数据库加载已有参数，无记录时返回空模型。"""
        row = conn.execute("SELECT n,mean_x,mean_y,var_x,cov_xy FROM moxing_canshu WHERE mingcheng=?", (mingcheng,)).fetchone()
        if not row:
            return cls()
        m = cls()
        m.n, m.mean_x, m.mean_y, m.var_x, m.cov_xy = row["n"], row["mean_x"], row["mean_y"], row["var_x"], row["cov_xy"]
        return m


def jisuan_xiuzheng_xishu(conn):
    """方案1：从历史反馈计算灌溉量修正系数。

    基于人工登记的实际执行量与预测量的偏差，
    用指数加权移动平均(EWMA)平滑，限制在 0.5~1.5 之间。
    """
    rows = conn.execute(
        "SELECT z.guangai_liang AS yuce,f.shiji_guangai AS shiji FROM zhiling z JOIN fankui f ON f.zhiling_id=z.id WHERE f.shiji_guangai>0 AND z.guangai_liang>0 ORDER BY f.shangbao_shijian DESC LIMIT 20"
    ).fetchall()
    if not rows:
        return 1.0
    ratios = [r["shiji"] / r["yuce"] for r in rows if r["yuce"] > 0]
    alpha = 0.3
    xishu = 1.0
    for ratio in reversed(ratios):
        xishu = alpha * ratio + (1 - alpha) * xishu
    return max(0.5, min(1.5, xishu))


def gengxin_moxing(conn, jiance, shiji_guangai):
    """收到人工反馈后更新增量回归模型。

    x=土壤湿度, y=实际灌溉量，逐条更新。
    """
    shidu = shuzi(jiance.get("turang_shidu"), 30)
    if shiji_guangai <= 0:
        return
    moxing = ZengliangHuigui.jiazai(conn, "guangai")
    moxing.gengxin(shidu, shiji_guangai)
    moxing.baocun(conn, "guangai")


def zhuangtai_shidu(shidu):
    """土壤湿度状态判定（可解释规则）。

    阈值依据：油橄榄适宜土壤湿度 28%-48%（参考作物系数和田间持水量）。
    """
    if shidu < 18:
        return "严重缺水"
    if shidu < 28:
        return "轻度缺水"
    if shidu <= 48:
        return "水分适宜"
    return "水分偏高"


def zhuangtai_feili(ec):
    """电导率(EC)肥力状态判定（可解释规则）。

    阈值依据：土壤EC 0.8-2.5 mS/cm 为肥力适宜区间。
    """
    if ec < .8:
        return "肥力不足"
    if ec <= 2.5:
        return "肥力适宜"
    return "盐分偏高"


def shengcheng_yuce(jiance, tianqi, zuowu, tianshu=3, shiyong_tianqi=True):
    """生成未来1-3天墒情预测（决策未来墒情）。

    计算步骤：
      1. 读取当前土壤湿度、光照、作物需水/需肥系数
      2. 逐日计算需水量：基础值 + 湿度 deficit + 温度增量 + 蒸散量
      3. 降雨扣减：概率≥70%扣6mm，≥40%扣3mm
      4. 递推土壤湿度：当日湿度 - 灌溉增量 + 降雨补充
      5. 末日湿度<18%→干旱预警，>48%→积水预警

    Args:
        jiance: 最新监测数据dict（含turang_shidu, guangzhao, dian_daolv等）
        tianqi: 天气预报list（每日含zuigao_wendu, jiangyu_gailv, zhengfa_liang）
        zuowu: 作物信息dict（含xushui_xishu, xufei_xishu）
        tianshu: 预测天数（1-3）
        shiyong_tianqi: 是否采用天气数据（False时用默认值）

    Returns:
        dict: dates(日期列表), xushui(需水量), xufei(需肥量),
              shidu(预测湿度), fenxi(分析结论), tianqi_shuoming(天气说明)
    """
    tianshu = max(1, min(3, int(tianshu or 3)))
    shidu = shuzi(jiance.get("turang_shidu"), 30)
    guangzhao = shuzi(jiance.get("guangzhao"), 15000)
    xushui_xishu = shuzi(zuowu.get("xushui_xishu"), 1)
    xufei_xishu = shuzi(zuowu.get("xufei_xishu"), 1)
    xu_shui, xu_fei, yu_shidu = [], [], []
    for i, tian in enumerate(tianqi[:tianshu]):
        wendu = shuzi(tian.get("zuigao_wendu"), 25) if shiyong_tianqi else 25
        jiangyu = shuzi(tian.get("jiangyu_gailv"), 0) if shiyong_tianqi else 0
        zhengfa = shuzi(tian.get("zhengfa_liang"), 3) if shiyong_tianqi else 3
        # 需水量 = 基础12mm + 湿度deficit×0.42 + 温度增量×0.55 + 蒸散×0.5
        base = 12 + max(0, (35 - shidu) * .42) + max(0, (wendu - 25) * .55) + zhengfa * .5
        base *= xushui_xishu
        # 强光照（>16000lux）额外需水
        if guangzhao > 16000:
            base += 1.5
        # 降雨扣减：大雨扣6mm，中雨扣3mm
        if jiangyu >= 70:
            base -= 6
        elif jiangyu >= 40:
            base -= 3
        xu_shui.append(round(max(0, base), 1))
        # 需肥量 = 基础4.2 + EC deficit×2，大雨减施30%
        fei = (4.2 + max(0, 1.4 - shuzi(jiance.get("dian_daolv"), 1.2)) * 2) * xufei_xishu
        if jiangyu >= 70:
            fei *= .7
        xu_fei.append(round(max(0, fei), 1))
        # 递推土壤湿度：当前 - 灌溉消耗 + 降雨补充
        shidu -= (base * .16) - (jiangyu * .035)
        yu_shidu.append(round(max(0, min(60, shidu)), 1))
    fenxi = "未来三天预计土壤湿度将逐步下降，建议重点关注早晨灌溉窗口。"
    if yu_shidu[-1] < 18:
        fenxi = "预测末日湿度低于预警线，存在干旱风险，应提前安排灌溉。"
    elif yu_shidu[-1] > 48:
        fenxi = "降雨影响下湿度偏高，建议延后灌溉，避免根区积水。"
    tianqi_shuoming = "已采用雅安市雨城区三日天气数据" if shiyong_tianqi else "未采用天气数据，仅依据监测数据和作物系数计算"
    return {"dates": [str(x["yubaoriqi"]) for x in tianqi[:tianshu]], "xushui": xu_shui, "xufei": xu_fei, "shidu": yu_shidu, "fenxi": fenxi, "tianqi_shuoming": tianqi_shuoming, "jisuan_shijian": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def shengcheng_juece(jiance, tianqi, zuowu, yuce=None, xiuzheng=1.0, huigui_yuce=None):
    """生成水肥决策建议（决策施水施肥）。

    计算步骤：
      1. 读取土壤湿度、EC、明日天气（降雨概率、温度）
      2. 灌溉量 = 16 + 湿度deficit×0.8 + 温度增量×0.5，乘作物需水系数
      3. 降雨扣减：概率≥70%乘0.45，≥40%乘0.72
      4. 若有预测结果，融合预测需水量（权重6:4）
      5. 施肥量 = 4.5 + EC deficit×2.2，EC>2.5减施65%，大雨减施35%
      6. 若有增量回归预测值，融合（权重6:4）
      7. 乘以反馈修正系数（方案1 EWMA）
      8. 生成可解释的决策依据文字

    Args:
        jiance: 最新监测数据
        tianqi: 天气预报列表
        zuowu: 作物信息
        yuce: 预测结果（可选，融合预测需水量）
        xiuzheng: 反馈修正系数（方案1 EWMA，0.5~1.5）
        huigui_yuce: 增量回归预测值（方案2，可选）

    Returns:
        dict: water_status, fertility_status, recommended_irrigation,
              recommended_fertilization, pump_runtime, reason
    """
    shidu = shuzi(jiance.get("turang_shidu"), 30)
    ec = shuzi(jiance.get("dian_daolv"), 1.2)
    weather = tianqi[0] if tianqi else {}
    rain = shuzi(weather.get("jiangyu_gailv"), 20)
    temp = shuzi(weather.get("zuigao_wendu"), 30)
    # 步骤2：基础灌溉量 = 16 + 湿度deficit×0.8 + 温度增量×0.5
    water = 16 + max(0, (32 - shidu) * .8) + max(0, (temp - 28) * .5)
    water *= shuzi(zuowu.get("xushui_xishu"), 1)
    # 步骤3：降雨扣减
    if rain >= 70: water *= .45
    elif rain >= 40: water *= .72
    # 步骤4：融合预测需水量（权重6:4）
    if yuce and yuce.get("xushui"): water = water * .6 + shuzi(yuce["xushui"][0]) * .4
    # 步骤5：施肥量 = 4.5 + EC deficit×2.2
    fert = 4.5 + max(0, 1.3 - ec) * 2.2
    fert *= shuzi(zuowu.get("xufei_xishu"), 1)
    if ec > 2.5: fert *= .35
    if rain >= 70: fert *= .65
    # 步骤6：融合增量回归预测值（权重6:4）
    if huigui_yuce is not None and huigui_yuce > 0:
        water = water * .6 + huigui_yuce * .4
    # 步骤7：乘以反馈修正系数
    water *= xiuzheng
    fert *= xiuzheng
    water, fert = round(max(0, water), 1), round(max(0, fert), 1)
    water_status, fert_status = zhuangtai_shidu(shidu), zhuangtai_feili(ec)
    reason = f"当前土壤湿度 {shidu:.1f}%，判定为{water_status}；EC {ec:.2f} mS/cm，判定为{fert_status}。"
    reason += f"结合明日最高温 {temp:.1f}℃、降雨概率 {rain:.0f}%，给出本次建议。"
    if xiuzheng != 1.0:
        reason += f"系统已根据近期{('修正系数' + format(xiuzheng, '.2f'))}自适配建议量。"
    return {"water_status": water_status, "fertility_status": fert_status, "recommended_irrigation": water, "recommended_fertilization": fert, "pump_runtime": round(water / 2, 1), "reason": reason}
