from flask import Blueprint, request, jsonify
from sqlalchemy import extract, text
from database.models import db
from database.tianqi_moxing import WeatherGrid

weather_bp = Blueprint('weather', __name__, url_prefix='/api/weather')

ALLOWED_INDICATORS = {
    'max_temp', 'min_temp', 'humidity', 'rainfall', 'evapotranspiration'
}


def _get_indicator(name):
    """只允许查询模型中实际存在的列，避免把请求参数拼进 SQL。"""
    return name if name in ALLOWED_INDICATORS else None


@weather_bp.route('/grid', methods=['GET'])
def get_grid_data():
    """
    查询指定区域+年份的气象网格数据
    参数: lat_min, lat_max, lon_min, lon_max, year, indicator(可选)
    """
    try:
        lat_min = request.args.get('lat_min', type=float)
        lat_max = request.args.get('lat_max', type=float)
        lon_min = request.args.get('lon_min', type=float)
        lon_max = request.args.get('lon_max', type=float)
        year = request.args.get('year', type=int)
        indicator = _get_indicator(request.args.get('indicator', 'max_temp'))

        if any(value is None for value in (lat_min, lat_max, lon_min, lon_max, year)):
            return jsonify({'code': 400, 'message': '缺少必要参数', 'data': None}), 400
        if indicator is None or lat_min > lat_max or lon_min > lon_max:
            return jsonify({'code': 400, 'message': '查询参数无效', 'data': None}), 400

        date_str = f"{year}-01-01"

        # 构建查询
        sql = text(f"""
            SELECT latitude, longitude, {indicator} as value
            FROM weather_grid
            WHERE data_date = :date
              AND latitude BETWEEN :lat_min AND :lat_max
              AND longitude BETWEEN :lon_min AND :lon_max
              AND {indicator} IS NOT NULL
            LIMIT 10000
        """)

        result = db.session.execute(sql, {
            'date': date_str,
            'lat_min': lat_min,
            'lat_max': lat_max,
            'lon_min': lon_min,
            'lon_max': lon_max
        })

        data = [{
            'lat': float(row.latitude),
            'lon': float(row.longitude),
            'value': float(row.value)
        } for row in result]

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data,
            'total': len(data),
            'year': year,
            'indicator': indicator
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@weather_bp.route('/point', methods=['GET'])
def get_point_timeseries():
    """
    查询某个经纬度点的时间序列数据
    参数: lat, lon, indicator(可选)
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        indicator = _get_indicator(request.args.get('indicator', 'max_temp'))

        if lat is None or lon is None:
            return jsonify({'code': 400, 'message': '缺少经纬度参数', 'data': None}), 400
        if indicator is None:
            return jsonify({'code': 400, 'message': '指标无效', 'data': None}), 400

        # 找最近的点
        sql = text(f"""
            SELECT data_date, {indicator} as value
            FROM weather_grid
            WHERE {indicator} IS NOT NULL
              AND ABS(latitude - :lat) < 0.1
              AND ABS(longitude - :lon) < 0.1
            ORDER BY data_date
            LIMIT 100
        """)

        result = db.session.execute(sql, {'lat': lat, 'lon': lon})

        data = [{
            'date': row.data_date.strftime('%Y-%m-%d'),
            'value': float(row.value)
        } for row in result]

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data,
            'lat': lat,
            'lon': lon,
            'indicator': indicator
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@weather_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    统计某区域某指标的均值、最大最小值
    参数: lat_min, lat_max, lon_min, lon_max, year, indicator(可选)
    """
    try:
        lat_min = request.args.get('lat_min', type=float)
        lat_max = request.args.get('lat_max', type=float)
        lon_min = request.args.get('lon_min', type=float)
        lon_max = request.args.get('lon_max', type=float)
        year = request.args.get('year', type=int)
        indicator = _get_indicator(request.args.get('indicator', 'max_temp'))

        if any(value is None for value in (lat_min, lat_max, lon_min, lon_max, year)):
            return jsonify({'code': 400, 'message': '缺少必要参数', 'data': None}), 400
        if indicator is None or lat_min > lat_max or lon_min > lon_max:
            return jsonify({'code': 400, 'message': '查询参数无效', 'data': None}), 400

        date_str = f"{year}-01-01"

        sql = text(f"""
            SELECT 
                AVG({indicator}) as avg_val,
                MIN({indicator}) as min_val,
                MAX({indicator}) as max_val,
                COUNT(*) as count
            FROM weather_grid
            WHERE data_date = :date
              AND latitude BETWEEN :lat_min AND :lat_max
              AND longitude BETWEEN :lon_min AND :lon_max
              AND {indicator} IS NOT NULL
        """)

        result = db.session.execute(sql, {
            'date': date_str,
            'lat_min': lat_min,
            'lat_max': lat_max,
            'lon_min': lon_min,
            'lon_max': lon_max
        }).fetchone()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'avg': float(result.avg_val) if result.avg_val is not None else None,
                'min': float(result.min_val) if result.min_val is not None else None,
                'max': float(result.max_val) if result.max_val is not None else None,
                'count': result.count
            },
            'year': year,
            'indicator': indicator
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@weather_bp.route('/years', methods=['GET'])
def get_years():
    """
    获取有数据的年份列表
    """
    try:
        year_column = extract('year', WeatherGrid.data_date).label('year')
        years = [row[0] for row in db.session.query(
            year_column
        ).distinct().order_by(year_column).all()]
        years = [int(year) for year in years if year]

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': years
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
