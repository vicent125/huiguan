from datetime import datetime

from flask import Blueprint, jsonify, request
from datetime import timedelta

from database.models import db, WarningThreshold, OperationLog
from utils.rizhi import logger

xitongguanli_bp = Blueprint('xitongguanli', __name__, url_prefix='/api/xitongguanli')


def success_response(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data})


def error_response(message='错误', code=500):
    logger.error(message)
    return jsonify({'code': code, 'message': message, 'data': None}), code


# ==================== 10.1 预警阈值设置 ====================

@xitongguanli_bp.route('/yujingyuzhi', methods=['GET'])
def get_threshold_list():
    """获取预警阈值列表"""
    try:
        threshold_type = request.args.get('threshold_type', '')

        query = WarningThreshold.query

        if threshold_type:
            query = query.filter_by(threshold_type=threshold_type)

        thresholds = query.order_by(WarningThreshold.warning_level.desc()).all()

        logger.info(f'获取阈值列表: {len(thresholds)}条')
        return success_response(data=[t.to_dict() for t in thresholds])
    except Exception as e:
        return error_response(f'获取阈值列表失败: {str(e)}')


@xitongguanli_bp.route('/yujingyuzhi/<int:threshold_id>', methods=['GET'])
def get_threshold_detail(threshold_id):
    """获取单条阈值详情"""
    try:
        threshold = db.session.get(WarningThreshold, threshold_id)
        if not threshold:
            return error_response('阈值记录不存在', 404)

        return success_response(data=threshold.to_dict())
    except Exception as e:
        return error_response(f'获取阈值详情失败: {str(e)}')


@xitongguanli_bp.route('/yujingyuzhi', methods=['POST'])
def create_threshold():
    """创建预警阈值"""
    try:
        data = request.get_json(silent=True) or {}
        if not data.get('threshold_type') or not data.get('threshold_name'):
            return error_response('threshold_type 和 threshold_name 不能为空', 400)

        new_threshold = WarningThreshold(
            threshold_type=data.get('threshold_type'),
            threshold_name=data.get('threshold_name'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            warning_level=data.get('warning_level'),
            description=data.get('description')
        )

        db.session.add(new_threshold)
        db.session.commit()

        _add_operation_log(
            operation_type='创建预警阈值',
            operation_content=f'创建了 {data.get("threshold_name")} 的阈值配置',
            operator=data.get('operator', '系统用户')
        )

        logger.info(f'创建阈值成功: ID={new_threshold.id}')
        return success_response(data=new_threshold.to_dict(), message='创建成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建阈值失败: {str(e)}')


@xitongguanli_bp.route('/yujingyuzhi/<int:threshold_id>', methods=['PUT'])
def update_threshold(threshold_id):
    """更新预警阈值"""
    try:
        threshold = db.session.get(WarningThreshold, threshold_id)
        if not threshold:
            return error_response('阈值记录不存在', 404)

        data = request.get_json(silent=True) or {}

        old_values = {
            'min_value': threshold.min_value,
            'max_value': threshold.max_value,
            'warning_level': threshold.warning_level
        }

        threshold.threshold_type = data.get('threshold_type', threshold.threshold_type)
        threshold.threshold_name = data.get('threshold_name', threshold.threshold_name)
        threshold.min_value = data.get('min_value', threshold.min_value)
        threshold.max_value = data.get('max_value', threshold.max_value)
        threshold.warning_level = data.get('warning_level', threshold.warning_level)
        threshold.description = data.get('description', threshold.description)

        db.session.commit()

        _add_operation_log(
            operation_type='修改预警阈值',
            operation_content=f'修改了 {threshold.threshold_name} 的阈值: 最小值 {old_values["min_value"]}->{threshold.min_value}, '
                              f'最大值 {old_values["max_value"]}->{threshold.max_value}, '
                              f'等级 {old_values["warning_level"]}->{threshold.warning_level}',
            operator=data.get('operator', '系统用户')
        )

        logger.info(f'更新阈值成功: ID={threshold_id}')
        return success_response(data=threshold.to_dict(), message='更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新阈值失败: {str(e)}')


@xitongguanli_bp.route('/yujingyuzhi/<int:threshold_id>', methods=['DELETE'])
def delete_threshold(threshold_id):
    """删除预警阈值"""
    try:
        threshold = db.session.get(WarningThreshold, threshold_id)
        if not threshold:
            return error_response('阈值记录不存在', 404)

        threshold_name = threshold.threshold_name

        db.session.delete(threshold)
        db.session.commit()

        _add_operation_log(
            operation_type='删除预警阈值',
            operation_content=f'删除了 {threshold_name} 的阈值配置',
            operator=(request.get_json(silent=True) or {}).get('operator', '系统用户')
        )

        logger.info(f'删除阈值成功: ID={threshold_id}')
        return success_response(message='删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除阈值失败: {str(e)}')


# ==================== 10.2 操作日志 ====================

@xitongguanli_bp.route('/caozuorizhi', methods=['GET'])
def get_operation_logs():
    """获取操作日志列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        operation_type = request.args.get('operation_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        operator = request.args.get('operator', '')

        query = OperationLog.query

        if operation_type:
            query = query.filter(OperationLog.operation_type.contains(operation_type))

        if operator:
            query = query.filter(OperationLog.operator.contains(operator))

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(OperationLog.operation_time >= start)

        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(OperationLog.operation_time < end)

        pagination = query.order_by(OperationLog.operation_time.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

        logs = [l.to_dict() for l in pagination.items]

        type_stats = db.session.query(
            OperationLog.operation_type,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.operation_type).all()

        logger.info(f'获取操作日志: {len(logs)}条')
        return success_response({
            'list': logs,
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages,
            'type_statistics': [{'type': t[0], 'count': t[1]} for t in type_stats]
        })
    except Exception as e:
        return error_response(f'获取操作日志失败: {str(e)}')


@xitongguanli_bp.route('/caozuorizhi', methods=['POST'])
def add_operation_log():
    """手动添加操作日志"""
    try:
        data = request.get_json(silent=True) or {}
        if not data.get('operation_type'):
            return error_response('operation_type 不能为空', 400)

        log = OperationLog(
            operator=data.get('operator', '系统用户'),
            operation_type=data.get('operation_type'),
            operation_content=data.get('operation_content'),
            operation_ip=data.get('operation_ip', request.remote_addr)
        )

        db.session.add(log)
        db.session.commit()

        logger.info(f'添加操作日志成功: ID={log.id}')
        return success_response(data=log.to_dict(), message='记录成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录日志失败: {str(e)}')


def _add_operation_log(operation_type, operation_content, operator='系统用户'):
    """内部方法：添加操作日志"""
    try:
        log = OperationLog(
            operator=operator,
            operation_type=operation_type,
            operation_content=operation_content,
            operation_ip=request.remote_addr if request else '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()
        logger.debug(f'自动记录操作日志: {operation_type}')
    except Exception as e:
        db.session.rollback()
        logger.error(f'记录操作日志失败: {str(e)}')
