from datetime import datetime
from extensions import db


class JianceShuju(db.Model):
    """
    监测数据表

    备注：
    这个表主要由“数据录入与监测”模块维护。
    预测分析和水肥决策模块只读取它。
    """
    __tablename__ = "monitor_data"

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer)
    growth_stage = db.Column(db.String(50))

    soil_moisture = db.Column(db.Float)
    soil_temperature = db.Column(db.Float)
    air_humidity = db.Column(db.Float)
    light_intensity = db.Column(db.Float)
    ec = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.now)


class TianqiYubao(db.Model):
    """
    天气预报表

    备注：
    这个表主要由“天气分析”模块维护。
    预测分析和水肥决策模块需要读取未来天气。
    """
    __tablename__ = "weather_forecast"

    id = db.Column(db.Integer, primary_key=True)

    max_temp = db.Column(db.Float)
    min_temp = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall_prob = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    weather_type = db.Column(db.String(50))
    evapotranspiration = db.Column(db.Float)

    forecast_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.now)


class YuceJilu(db.Model):
    """
    预测记录表
    """
    __tablename__ = "predict_record"

    id = db.Column(db.Integer, primary_key=True)

    crop_id = db.Column(db.Integer)
    growth_stage = db.Column(db.String(50))

    predicted_water_need = db.Column(db.Text)
    predicted_fertilizer_need = db.Column(db.Text)
    predicted_soil_moisture = db.Column(db.Text)

    weather_desc = db.Column(db.Text)
    drought_analysis = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)


class JueceJilu(db.Model):
    """
    水肥决策记录表

    备注：
    如果报告中心需要展示历史决策结果，可以读取这个表。
    """
    __tablename__ = "decision_record"

    id = db.Column(db.Integer, primary_key=True)

    crop_id = db.Column(db.Integer)
    growth_stage = db.Column(db.String(50))

    water_status = db.Column(db.String(50))
    fertility_status = db.Column(db.String(50))

    recommended_irrigation = db.Column(db.Float)
    recommended_fertilization = db.Column(db.Float)

    decision_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)


class ShebeiZhiling(db.Model):
    """
    设备指令表

    备注：
    设备协同模块和硬件模块需要读取这个表。
    """
    __tablename__ = "device_command"

    id = db.Column(db.Integer, primary_key=True)

    device_id = db.Column(db.Integer)

    irrigation_amount = db.Column(db.Float)
    fertilization_amount = db.Column(db.Float)
    pump_run_time = db.Column(db.Float)

    command_status = db.Column(db.String(50), default="未下发")

    created_at = db.Column(db.DateTime, default=datetime.now)
    sent_at = db.Column(db.DateTime)