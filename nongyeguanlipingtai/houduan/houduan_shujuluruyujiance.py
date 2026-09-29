from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import pandas as pd
app = Flask(__name__)
CORS(app)

@app.get('/api/health')
def health_check():
    return {'code': 200, 'message': '服务运行正常', 'data': None}
# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'MONITOR_DATABASE_URL', os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'nongye_jiance.db'))
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 定义监测数据表模型
class MonitorData(db.Model):
    __tablename__ = 'monitor_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crop_id = db.Column(db.Integer, nullable=False)
    growth_stage = db.Column(db.String(50))
    soil_moisture = db.Column(db.Float)
    soil_temp = db.Column(db.Float)
    air_humidity = db.Column(db.Float)
    light_intensity = db.Column(db.Float)
    ec = db.Column(db.Float)
    record_time = db.Column(db.DateTime, default=datetime.now)


# ==================== 接口路由 ====================

@app.route('/api/shoudongluru', methods=['POST'])
def shoudongluru():
    """手动录入数据"""
    data = request.get_json(silent=True) or {}
    crop_id = data.get('crop_id')
    if crop_id is None:
        return jsonify({"code": 400, "msg": "作物ID不能为空"})
    try:
        new_data = MonitorData(
            crop_id=crop_id,
            growth_stage=data.get('growth_stage'),
            soil_moisture=data.get('soil_moisture'),
            soil_temp=data.get('soil_temp'),
            air_humidity=data.get('air_humidity'),
            light_intensity=data.get('light_intensity'),
            ec=data.get('ec')
        )
        db.session.add(new_data)
        db.session.commit()
        return jsonify({"code": 200, "msg": "手动录入成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"录入失败: {str(e)}"})


@app.route('/api/piliangdaoru', methods=['POST'])
def piliangdaoru():
    """批量导入Excel数据"""
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "未检测到文件"})
    file = request.files['file']
    try:
        df = pd.read_excel(file)
        required_cols = ['crop_id', 'growth_stage', 'soil_moisture', 'soil_temp', 'air_humidity', 'light_intensity', 'ec']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({"code": 400, "msg": f"Excel缺少必要列: {', '.join(missing)}"})
        success_count = 0
        failed_count = 0
        for _, row in df.iterrows():
            try:
                new_data = MonitorData(
                    crop_id=row['crop_id'],
                    growth_stage=row['growth_stage'],
                    soil_moisture=row['soil_moisture'],
                    soil_temp=row['soil_temp'],
                    air_humidity=row['air_humidity'],
                    light_intensity=row['light_intensity'],
                    ec=row['ec']
                )
                db.session.add(new_data)
                success_count += 1
            except Exception:
                failed_count += 1
                continue
        db.session.commit()
        return jsonify({"code": 200, "msg": f"批量导入成功，成功{success_count}条，失败{failed_count}条"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"导入失败: {str(e)}"})


@app.route('/api/lishijiance', methods=['GET'])
def lishijiance():
    """查询历史监测数据"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = MonitorData.query
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = datetime(end.year, end.month, end.day, 23, 59, 59)
            query = query.filter(MonitorData.record_time >= start, MonitorData.record_time <= end)
        except ValueError:
            return jsonify({"code": 400, "msg": "日期格式错误，请使用 YYYY-MM-DD"})

    records = query.order_by(MonitorData.record_time.desc()).all()
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "crop_id": r.crop_id,
            "growth_stage": r.growth_stage,
            "soil_moisture": r.soil_moisture,
            "soil_temp": r.soil_temp,
            "air_humidity": r.air_humidity,
            "light_intensity": r.light_intensity,
            "ec": r.ec,
            "record_time": r.record_time.strftime('%Y-%m-%d %H:%M:%S') if r.record_time else "—"
        })
    return jsonify({"code": 200, "data": result, "msg": "查询成功"})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
    # 注意：初始化数据库请运行 init_db.py，此处不再包含初始化逻辑以保持服务纯净
