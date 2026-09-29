import json
from flask import Blueprint, request, jsonify
from extensions import db
from models import YuceJilu
from services.yucefuwu import shengcheng_yucejieguo

yucefenxi_bp = Blueprint("yucefenxi", __name__)


@yucefenxi_bp.route("/api/yucefenxi/shengcheng", methods=["POST"])
def shengcheng():
    """
    预测分析接口。

    前端接入位置：
    预测分析页面点击“生成预测”按钮时调用。

    后端依赖：
    1. monitor_data 监测数据表
    2. weather_forecast 天气预报表

    如果这些表暂时未完成，也可以直接使用前端传入的数据。
    """
    try:
        data = request.get_json(silent=True) or {}

        result = shengcheng_yucejieguo(data)

        record_id = None

        try:
            record = YuceJilu(
                crop_id=result.get("crop_id"),
                growth_stage=result.get("growth_stage"),
                predicted_water_need=json.dumps(result.get("predicted_water_need"), ensure_ascii=False),
                predicted_fertilizer_need=json.dumps(result.get("predicted_fertilizer_need"), ensure_ascii=False),
                predicted_soil_moisture=json.dumps(result.get("predicted_soil_moisture"), ensure_ascii=False),
                weather_desc=result.get("weather_desc"),
                drought_analysis=result.get("drought_analysis")
            )

            db.session.add(record)
            db.session.commit()

            record_id = record.id

        except Exception:
            db.session.rollback()
            # 数据库没接好时，不影响前端展示预测结果
            record_id = None

        result["record_id"] = record_id

        return jsonify({
            "code": 200,
            "message": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e),
            "data": {}
        }), 500