from flask import Blueprint, request, jsonify
from models import db, SheBeiXieTong
from datetime import datetime

xietong_bp = Blueprint("xietong", __name__)

# 获取设备协同列表
@xietong_bp.route("/xietong/list", methods=["GET"])
def get_xietong_list():
    data_list = SheBeiXieTong.query.all()
    result = []
    for item in data_list:
        result.append({
            "id": item.id,
            "deviceName": item.device_name,
            "deviceCode": item.device_code,
            "status": item.status,
            "syncMode": item.sync_mode,
            "waterLevel": item.water_level,
            "fertilizerLevel": item.fertilizer_level,
            "irrigation": item.irrigation,
            "fertilize": item.fertilize,
            "pumpStatus": item.pump_status,
            "createTime": item.create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"code": 200, "message": "查询成功", "data": result})

# 新增/下发设备指令
@xietong_bp.route("/xietong/add", methods=["POST"])
def add_xietong():
    json_data = request.get_json()
    new_data = SheBeiXieTong(
        device_name=json_data.get("deviceName"),
        device_code=json_data.get("deviceCode"),
        status=json_data.get("status"),
        sync_mode=json_data.get("syncMode"),
        water_level=json_data.get("waterLevel"),
        fertilizer_level=json_data.get("fertilizerLevel"),
        irrigation=json_data.get("irrigation"),
        fertilize=json_data.get("fertilize"),
        pump_status=json_data.get("pumpStatus"),
        create_time=datetime.now()
    )
    db.session.add(new_data)
    db.session.commit()
    return jsonify({"code": 200, "message": "指令下发成功"})

# 修改设备信息
@xietong_bp.route("/xietong/edit/<int:item_id>", methods=["PUT"])
def edit_xietong(item_id):
    item = SheBeiXieTong.query.get(item_id)
    if not item:
        return jsonify({"code": 400, "message": "记录不存在"})
    json_data = request.get_json()
    item.device_name = json_data.get("deviceName")
    item.device_code = json_data.get("deviceCode")
    item.status = json_data.get("status")
    item.sync_mode = json_data.get("syncMode")
    item.water_level = json_data.get("waterLevel")
    item.fertilizer_level = json_data.get("fertilizerLevel")
    item.irrigation = json_data.get("irrigation")
    item.fertilize = json_data.get("fertilize")
    item.pump_status = json_data.get("pumpStatus")
    db.session.commit()
    return jsonify({"code": 200, "message": "修改成功"})

# 删除记录
@xietong_bp.route("/xietong/del/<int:item_id>", methods=["DELETE"])
def del_xietong(item_id):
    item = SheBeiXieTong.query.get(item_id)
    if not item:
        return jsonify({"code": 400, "message": "记录不存在"})
    db.session.delete(item)
    db.session.commit()
    return jsonify({"code": 200, "message": "删除成功"})