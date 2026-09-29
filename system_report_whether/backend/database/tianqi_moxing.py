
from database.models import db
from utils.shiqu import get_beijing_time


class WeatherGrid(db.Model):
    """
    气象网格数据表 - weathermesh
    存储经纬度网格气象数据，用于地图热力图展示
    """
    __tablename__ = 'weather_grid'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    data_date = db.Column(db.Date, nullable=False, comment='数据日期')
    latitude = db.Column(db.Numeric(8, 5), nullable=False, comment='纬度')
    longitude = db.Column(db.Numeric(8, 5), nullable=False, comment='经度')
    max_temp = db.Column(db.Float, comment='最高温度(°C)')
    min_temp = db.Column(db.Float, comment='最低温度(°C)')
    humidity = db.Column(db.Float, comment='相对湿度(%)')
    rainfall = db.Column(db.Float, comment='降雨量(mm)')
    evapotranspiration = db.Column(db.Float, comment='蒸散量(mm)')
    created_at = db.Column(db.DateTime, default=get_beijing_time)

    __table_args__ = (
        db.UniqueConstraint('data_date', 'latitude', 'longitude', name='uk_date_lat_lon'),
        db.Index('idx_date', 'data_date'),
        db.Index('idx_lat_lon', 'latitude', 'longitude'),
        {'comment': '气象网格数据'}
    )