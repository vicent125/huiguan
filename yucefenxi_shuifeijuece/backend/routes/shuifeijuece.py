from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models import JueceJilu, ShebeiZhiling
from services.juecefuwu import shengcheng_juecejieguo

shuifeijuece_bp = Blueprint("shuifeijuece", __name__)


@shuifeijuece_bp.route("/api/shuifeijuece/shengcheng", methods=["POST"])
def shengcheng():
    """
    水肥决策生成接口。

    前端接入位置：
    水肥决策页面点击“生成决策”按钮时调用。

    备注：
    如果前端已经调用过预测分析接口，可以把预测结果中的
    predicted_water_need 和 predicted_fertilizer_need 一起传过来。
    """
    try:
        data = request.get_json(silent=True) or {}

        result = shengcheng_juecejieguo(data)

        record_id = None

        try:
            record = JueceJilu(
                crop_id=result.get("crop_id"),
                growth_stage=result.get("growth_stage"),
                water_status=result.get("water_status"),
                fertility_status=result.get("fertility_status"),
                recommended_irrigation=result.get("recommended_irrigation"),
                recommended_fertilization=result.get("recommended_fertilization"),
                decision_reason=result.get("decision_reason")
            )

            db.session.add(record)
            db.session.commit()

            record_id = record.id

        except Exception:
            db.session.rollback()
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


@shuifeijuece_bp.route("/api/shuifeijuece/xiada", methods=["POST"])
def xiada():
    """
    手动确认下发设备指令接口。

    前端接入位置：
    水肥决策页面或设备协同页面点击“手动确认下发”按钮时调用。

    硬件协同备注：
    当前接口只负责生成并保存设备指令。
    最后与硬件联调时，可以让硬件端：
    1. 轮询 device_command 表；
    2. 或由后端通过 HTTP/MQTT 主动发送给硬件。
    """
    try:
        data = request.get_json(silent=True) or {}

        device_id = data.get("device_id", 1)
        irrigation_amount = float(data.get("irrigation_amount", 0))
        fertilization_amount = float(data.get("fertilization_amount", 0))
        pump_run_time = float(data.get("pump_run_time", 0))

        command_id = None

        try:
            command = ShebeiZhiling(
                device_id=device_id,
                irrigation_amount=irrigation_amount,
                fertilization_amount=fertilization_amount,
                pump_run_time=pump_run_time,
                command_status="已生成",
                sent_at=datetime.now()
            )

            db.session.add(command)
            db.session.commit()

            command_id = command.id

        except Exception:
            db.session.rollback()
            command_id = None

        return jsonify({
            "code": 200,
            "message": "设备指令已生成",
            "data": {
                "command_id": command_id,
                "device_id": device_id,
                "irrigation_amount": irrigation_amount,
                "fertilization_amount": fertilization_amount,
                "pump_run_time": pump_run_time,
                "command_status": "已生成"
            }
        })

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": str(e),
            "data": {}
        }), 500