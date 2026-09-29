
from app import create_app
from database.models import db, ReportRecord
import json

app = create_app()

with app.app_context():
    report = ReportRecord(
        report_title='智能水肥一体化分析报告-第一周',
        crop_id=1,
        growth_period='果实膨大期',
        basic_info=json.dumps({'crop_name': '柑橘', 'growth_period': '果实膨大期'}),
        monitor_summary=json.dumps({'soil_moisture': 65.2}),
        weather_summary=json.dumps({'forecast_days': 3, 'avg_max_temp': 32.5}),
        water_fertilizer_result=json.dumps({'water_status': '适宜'}),
        decision_suggestion=json.dumps({'irrigation_suggestion': '建议灌溉量 15.5 L/亩'}),
        risk_description=json.dumps({'drought_risk': '低风险'}),
        device_suggestion=json.dumps({'pump_runtime': 30})
    )
    db.session.add(report)
    db.session.commit()
    print("报告添加完成")