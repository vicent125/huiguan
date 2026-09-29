from flask_sqlalchemy import SQLAlchemy
from utils.shiqu import get_beijing_time

db = SQLAlchemy()


# ==================== 天气分析相关表 ====================

class WeatherForecast(db.Model):
    """
    天气预报表 - tianqiyubao
    前后端对接：前端天气分析页面通过 /api/tianqifenxi/tianqiyubao 接口获取数据
    """
    __tablename__ = 'weather_forecast'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    forecast_date = db.Column(db.Date, nullable=False, comment='预报日期')
    max_temp = db.Column(db.Float, comment='最高温(°C)')
    min_temp = db.Column(db.Float, comment='最低温(°C)')
    humidity = db.Column(db.Float, comment='湿度(%)')
    rain_probability = db.Column(db.Float, comment='降雨概率(%)')
    rainfall = db.Column(db.Float, comment='降雨量(mm)')
    weather_type = db.Column(db.String(50), comment='天气类型(晴/阴/雨等)')
    evapotranspiration = db.Column(db.Float, comment='蒸散量(mm)')
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    def to_dict(self):
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.strftime('%Y-%m-%d') if self.forecast_date else None,
            'max_temp': self.max_temp,
            'min_temp': self.min_temp,
            'humidity': self.humidity,
            'rain_probability': self.rain_probability,
            'rainfall': self.rainfall,
            'weather_type': self.weather_type,
            'evapotranspiration': self.evapotranspiration,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 报告中心相关表 ====================

class ReportRecord(db.Model):
    """
    报告记录表 - baogaojilu
    前后端对接：前端报告中心页面通过 /api/baogaozhongxin/baogaojilu 接口获取报告列表
    """
    __tablename__ = 'report_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_title = db.Column(db.String(200), nullable=False, comment='报告标题')
    crop_id = db.Column(db.Integer, comment='作物ID')
    growth_period = db.Column(db.String(100), comment='生育期')
    create_time = db.Column(db.DateTime, default=get_beijing_time, comment='创建时间')
    update_time = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time, comment='更新时间')
    exporter = db.Column(db.String(100), comment='导出人')
    export_status = db.Column(db.Integer, default=0, comment='导出状态 0-未导出 1-已导出')
    export_time = db.Column(db.DateTime, comment='导出时间')
    file_path = db.Column(db.String(500), comment='PDF文件路径')

    # 报告内容摘要
    basic_info = db.Column(db.Text, comment='基础信息JSON')
    monitor_summary = db.Column(db.Text, comment='监测数据摘要JSON')
    weather_summary = db.Column(db.Text, comment='天气摘要JSON')
    water_fertilizer_result = db.Column(db.Text, comment='水肥分析结果JSON')
    decision_suggestion = db.Column(db.Text, comment='决策建议JSON')
    risk_description = db.Column(db.Text, comment='风险说明JSON')
    device_suggestion = db.Column(db.Text, comment='设备执行建议JSON')

    def to_list_dict(self):
        """列表页使用"""
        return {
            'id': self.id,
            'report_title': self.report_title,
            'growth_period': self.growth_period,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'exporter': self.exporter,
            'export_status': self.export_status,
            'export_time': self.export_time.strftime('%Y-%m-%d %H:%M:%S') if self.export_time else None
        }

    def to_detail_dict(self):
        """详情页使用"""
        import json
        return {
            'id': self.id,
            'report_title': self.report_title,
            'crop_id': self.crop_id,
            'growth_period': self.growth_period,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'basic_info': json.loads(self.basic_info) if self.basic_info else {},
            'monitor_summary': json.loads(self.monitor_summary) if self.monitor_summary else {},
            'weather_summary': json.loads(self.weather_summary) if self.weather_summary else {},
            'water_fertilizer_result': json.loads(self.water_fertilizer_result) if self.water_fertilizer_result else {},
            'decision_suggestion': json.loads(self.decision_suggestion) if self.decision_suggestion else {},
            'risk_description': json.loads(self.risk_description) if self.risk_description else {},
            'device_suggestion': json.loads(self.device_suggestion) if self.device_suggestion else {}
        }


# ==================== 系统管理相关表 ====================

class WarningThreshold(db.Model):
    """
    预警阈值表 - yujingyuzhi
    前后端对接：前端系统管理-预警阈值设置页面通过 /api/xitongguanli/yujingyuzhi 接口操作
    """
    __tablename__ = 'warning_threshold'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    threshold_type = db.Column(db.String(100), nullable=False,
                               comment='阈值类型(soil_moisture/soil_temp/air_humidity等)')
    threshold_name = db.Column(db.String(100), comment='阈值名称')
    min_value = db.Column(db.Float, comment='最小值')
    max_value = db.Column(db.Float, comment='最大值')
    warning_level = db.Column(db.Integer, comment='预警等级 1-提示 2-次要 3-重要 4-紧急')
    description = db.Column(db.Text, comment='说明')
    created_at = db.Column(db.DateTime, default=get_beijing_time)
    updated_at = db.Column(db.DateTime, default=get_beijing_time, onupdate=get_beijing_time)

    def to_dict(self):
        return {
            'id': self.id,
            'threshold_type': self.threshold_type,
            'threshold_name': self.threshold_name,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'warning_level': self.warning_level,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class OperationLog(db.Model):
    """
    操作日志表 - caozuorizhi
    前后端对接：前端系统管理-操作日志页面通过 /api/xitongguanli/caozuorizhi 接口获取日志
    """
    __tablename__ = 'operation_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator = db.Column(db.String(100), comment='操作人')
    operation_type = db.Column(db.String(100), nullable=False, comment='操作类型')
    operation_content = db.Column(db.Text, comment='操作内容')
    operation_ip = db.Column(db.String(50), comment='操作IP')
    operation_time = db.Column(db.DateTime, default=get_beijing_time, comment='操作时间')

    def to_dict(self):
        return {
            'id': self.id,
            'operator': self.operator,
            'operation_type': self.operation_type,
            'operation_content': self.operation_content,
            'operation_ip': self.operation_ip,
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M:%S') if self.operation_time else None
        }
