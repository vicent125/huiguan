import os
import unittest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from database.models import db


class ApiIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def test_health_and_weather_forecast(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        response = self.client.get('/api/tianqifenxi/tianqiyubao')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()['data']['forecast_list']), 3)

    def test_report_create_list_and_detail(self):
        created = self.client.post('/api/baogaozhongxin/baogaojilu', json={
            'crop_id': 1,
            'report_title': '接口联调测试报告'
        })
        self.assertEqual(created.status_code, 200)
        report_id = created.get_json()['data']['id']
        self.assertEqual(self.client.get('/api/baogaozhongxin/baogaojilu').status_code, 200)
        self.assertEqual(
            self.client.get(f'/api/baogaozhongxin/baogaojilu/{report_id}').status_code,
            200
        )

    def test_threshold_update_and_operation_log(self):
        created = self.client.post('/api/xitongguanli/yujingyuzhi', json={
            'threshold_type': 'soil_moisture',
            'threshold_name': '土壤湿度预警',
            'min_value': 40,
            'max_value': 80,
            'warning_level': 2
        })
        self.assertEqual(created.status_code, 200)
        threshold_id = created.get_json()['data']['id']
        updated = self.client.put(
            f'/api/xitongguanli/yujingyuzhi/{threshold_id}',
            json={'min_value': 35, 'max_value': 85, 'warning_level': 3}
        )
        self.assertEqual(updated.status_code, 200)
        logs = self.client.get('/api/xitongguanli/caozuorizhi').get_json()['data']['list']
        self.assertEqual(len(logs), 2)

    def test_weather_grid_validation_and_years(self):
        invalid = self.client.get(
            '/api/weather/grid?lat_min=0&lat_max=1&lon_min=0&lon_max=1'
            '&year=2026&indicator=id%20FROM%20weather_grid'
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.client.get('/api/weather/years').status_code, 200)


if __name__ == '__main__':
    unittest.main()
