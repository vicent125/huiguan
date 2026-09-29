from app import create_app
from database.models import db
from database.tianqi_moxing import WeatherGrid
from database.models import WeatherForecast

app = create_app()


with app.app_context():
    db.create_all()
    print("✅ 表创建完成")