
from flask import Blueprint, jsonify, request
from datetime import  datetime,timedelta
from utils.shiqu import get_beijing_time
from sqlalchemy import and_
from database.models import  db, WeatherForecast
from utils.rizhi import logger

tianqifenxi_bp = Blueprint('tianqifenxi', __name__, url_prefix='/api/tianqifenxi')


def success_response(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data})


def error_response(message='错误', code=500):
    logger.error(message)
    return jsonify({'code': code, 'message': message, 'data': None}), code


@tianqifenxi_bp.route('/tianqiyubao', methods=['GET'])
def get_weather_forecast():
    """获取未来三天天气预报"""
    try:
        today = get_beijing_time().date()
        end_date = today + timedelta(days=2)

        rows = WeatherForecast.query.filter(
            and_(
                WeatherForecast.forecast_date >= today,
                WeatherForecast.forecast_date <= end_date
            )
        ).order_by(WeatherForecast.forecast_date, WeatherForecast.id.desc()).all()

        # 兼容旧数据库中同一天被辅助脚本重复插入的记录。
        forecasts_by_date = {}
        for row in rows:
            forecasts_by_date.setdefault(row.forecast_date, row)
        forecasts = [forecasts_by_date[key] for key in sorted(forecasts_by_date)]

        if not forecasts:
            logger.info('数据库无天气数据，生成模拟数据')
            forecasts = _generate_mock_weather(today, end_date)

        data = [f.to_dict() for f in forecasts]

        trend_data = {
            'dates': [d['forecast_date'] for d in data],
            'max_temps': [d['max_temp'] for d in data],
            'min_temps': [d['min_temp'] for d in data],
            'rainfalls': [d['rainfall'] for d in data],
            'humidities': [d['humidity'] for d in data]
        }

        logger.info(f'返回{len(data)}天天气数据')
        return success_response({
            'forecast_list': data,
            'trend_chart': trend_data
        })
    except Exception as e:
        return error_response(f'获取天气数据失败: {str(e)}')


@tianqifenxi_bp.route('/tianqiyubao', methods=['POST'])
def add_weather_forecast():
    """添加/更新天气预报数据"""
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get('forecasts'), list):
            return error_response('forecasts 必须是数组', 400)

        for item in data.get('forecasts', []):
            forecast_date = datetime.strptime(item['forecast_date'], '%Y-%m-%d').date()
            existing = WeatherForecast.query.filter_by(forecast_date=forecast_date).first()

            if existing:
                existing.max_temp = item.get('max_temp')
                existing.min_temp = item.get('min_temp')
                existing.humidity = item.get('humidity')
                existing.rain_probability = item.get('rain_probability')
                existing.rainfall = item.get('rainfall')
                existing.weather_type = item.get('weather_type')
                existing.evapotranspiration = item.get('evapotranspiration')
                logger.info(f'更新天气数据: {forecast_date}')
            else:
                new_forecast = WeatherForecast(
                    forecast_date=forecast_date,
                    max_temp=item.get('max_temp'),
                    min_temp=item.get('min_temp'),
                    humidity=item.get('humidity'),
                    rain_probability=item.get('rain_probability'),
                    rainfall=item.get('rainfall'),
                    weather_type=item.get('weather_type'),
                    evapotranspiration=item.get('evapotranspiration')
                )
                db.session.add(new_forecast)
                logger.info(f'新增天气数据: {forecast_date}')

        db.session.commit()
        return success_response(message='天气预报数据更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新天气数据失败: {str(e)}')


@tianqifenxi_bp.route('/tianqiyubao/<int:forecast_id>', methods=['PUT'])
def update_weather_forecast(forecast_id):
    """更新单条天气预报"""
    try:
        forecast = db.session.get(WeatherForecast, forecast_id)
        if not forecast:
            return error_response('天气记录不存在', 404)

        data = request.get_json()
        forecast.max_temp = data.get('max_temp', forecast.max_temp)
        forecast.min_temp = data.get('min_temp', forecast.min_temp)
        forecast.humidity = data.get('humidity', forecast.humidity)
        forecast.rain_probability = data.get('rain_probability', forecast.rain_probability)
        forecast.rainfall = data.get('rainfall', forecast.rainfall)
        forecast.weather_type = data.get('weather_type', forecast.weather_type)
        forecast.evapotranspiration = data.get('evapotranspiration', forecast.evapotranspiration)

        db.session.commit()
        logger.info(f'更新天气记录: ID={forecast_id}')
        return success_response(data=forecast.to_dict(), message='更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


def _generate_mock_weather(start_date, end_date):
    """生成仅用于展示的模拟天气数据，不在 GET 请求中写数据库。"""
    import random
    mock_data = []
    weather_types = ['晴', '多云', '阴', '小雨', '中雨']

    current = start_date
    while current <= end_date:
        mock = WeatherForecast(
            forecast_date=current,
            max_temp=round(random.uniform(25, 35), 1),
            min_temp=round(random.uniform(18, 24), 1),
            humidity=round(random.uniform(60, 90), 1),
            rain_probability=round(random.uniform(0, 80), 1),
            rainfall=round(random.uniform(0, 20), 1),
            weather_type=random.choice(weather_types),
            evapotranspiration=round(random.uniform(3, 8), 2)
        )
        mock_data.append(mock)
        current += timedelta(days=1)

    logger.info(f'生成{len(mock_data)}天模拟天气数据')
    return mock_data
