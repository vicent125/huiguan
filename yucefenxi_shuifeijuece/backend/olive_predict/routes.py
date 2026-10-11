from flask import Blueprint,request,jsonify
from .engine import predict,InputError

olive_predict_bp=Blueprint('olive_predict_v2',__name__)

@olive_predict_bp.route('/api/olive/predict',methods=['POST'])
def forecast():
    data=request.get_json(silent=True)
    try:
        result=predict(data)
        return jsonify(code=200,message='success',data=result)
    except (InputError,KeyError,TypeError,ValueError) as exc:
        return jsonify(code=422,message=str(exc),data=None),422

@olive_predict_bp.route('/api/olive/health',methods=['GET'])
def health():return jsonify(status='ok',schema_version='2.1',automatic_execution=False)
