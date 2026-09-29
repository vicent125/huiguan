from app import create_app
from database.models import db, WeatherForecast
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    today = datetime.now().date()

    for i in range(3):
        date = today + timedelta(days=i)
        forecast = WeatherForecast.query.filter_by(forecast_date=date).first()
        if forecast is None:
            forecast = WeatherForecast(forecast_date=date)
            db.session.add(forecast)
        forecast.max_temp = 30 + i
        forecast.min_temp = 22 + i
        forecast.humidity = 65 + i * 5
        forecast.rain_probability = 10 + i * 20
        forecast.rainfall = i * 5
        forecast.weather_type = ['晴', '多云', '小雨'][i]
        forecast.evapotranspiration = 5.5 + i

    db.session.commit()
    print("天气预报数据添加完成")
