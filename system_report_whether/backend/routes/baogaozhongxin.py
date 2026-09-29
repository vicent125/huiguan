
from flask import Blueprint, jsonify, request, send_file
from database.models import  db, ReportRecord
import json, os
from utils.shiqu import get_beijing_time

baogaozhongxin_bp = Blueprint('baogaozhongxin', __name__, url_prefix='/api/baogaozhongxin')


# ==================== 8.1 报告列表页 ====================

@baogaozhongxin_bp.route('/baogaojilu', methods=['GET'])
def get_report_list():
    """
    获取历史报告列表
    前后端对接：前端报告列表页调用，支持分页和关键词搜索
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 10, type=int), 100)
        if page < 1 or page_size < 1:
            return jsonify({'code': 400, 'message': '分页参数无效', 'data': None}), 400
        keyword = request.args.get('keyword', '')

        query = ReportRecord.query

        if keyword:
            query = query.filter(ReportRecord.report_title.contains(keyword))

        # 按创建时间倒序
        pagination = query.order_by(ReportRecord.create_time.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

        reports = [r.to_list_dict() for r in pagination.items]

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': reports,
                'total': pagination.total,
                'page': page,
                'page_size': page_size,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@baogaozhongxin_bp.route('/baogaojilu/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    """
    获取报告详情
    前后端对接：前端报告详细页调用，展示基础信息、监测数据摘要、天气摘要等
    """
    try:
        report = db.session.get(ReportRecord, report_id)
        if not report:
            return jsonify({'code': 404, 'message': '报告不存在', 'data': None}), 404

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': report.to_detail_dict()
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


# ==================== 8.2 报告生成与详情 ====================

@baogaozhongxin_bp.route('/baogaojilu', methods=['POST'])
def create_report():
    """
    生成报告
    前后端对接：前端点击"生成报告"按钮调用，后端自动汇总数据生成报告
    """
    try:
        data = request.get_json(silent=True) or {}
        crop_id = data.get('crop_id')
        report_title = data.get('report_title', f'水肥决策报告-{get_beijing_time().strftime("%Y%m%d")}')


        # 组装基础信息
        basic_info = {
            'crop_name': '柑橘',  # 合并后替换为真实数据
            'growth_period': '果实膨大期',  # 合并后替换为真实数据
            'suitable_soil': '砂壤土',  # 合并后替换为真实数据
            'report_date': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 组装监测数据摘要（合并时从监测数据表获取）
        monitor_summary = {
            'latest_soil_moisture': 65.2,  # 合并后替换为真实数据
            'latest_soil_temp': 28.5,
            'latest_air_humidity': 78.3,
            'latest_light_intensity': 12500,
            'latest_conductivity': 1.2
        }

        # 组装天气摘要（合并时从天气表获取）
        weather_summary = {
            'forecast_days': 3,
            'weather_list': [],  # 合并后填充真实数据
            'avg_max_temp': 32.5,
            'total_rainfall': 15.2
        }

        # 水肥分析结果（前后端对接：从水肥决策模块获取，此处模拟）
        water_fertilizer_result = {
            'water_status': '适宜',
            'fertilizer_status': '轻度缺肥',
            'recommended_irrigation': 15.5,
            'recommended_fertilizer': 8.2,
            'unit': 'L/亩'
        }

        # 决策建议
        decision_suggestion = {
            'irrigation_suggestion': '建议灌溉量 15.5 L/亩',
            'fertilizer_suggestion': '建议施肥量 8.2 kg/亩',
            'timing_suggestion': '建议在早晨6-8点进行灌溉'
        }

        # 风险说明
        risk_description = {
            'drought_risk': '低风险',
            'flood_risk': '无风险',
            'disease_risk': '中等风险（高温高湿）'
        }

        # 设备执行建议
        device_suggestion = {
            'pump_runtime': 30,
            'irrigation_volume': 15.5,
            'fertilizer_volume': 8.2,
            'execution_time': '06:00-08:00'
        }

        # 创建报告记录
        new_report = ReportRecord(
            report_title=report_title,
            crop_id=crop_id,
            growth_period=basic_info['growth_period'],
            basic_info=json.dumps(basic_info, ensure_ascii=False),
            monitor_summary=json.dumps(monitor_summary, ensure_ascii=False),
            weather_summary=json.dumps(weather_summary, ensure_ascii=False),
            water_fertilizer_result=json.dumps(water_fertilizer_result, ensure_ascii=False),
            decision_suggestion=json.dumps(decision_suggestion, ensure_ascii=False),
            risk_description=json.dumps(risk_description, ensure_ascii=False),
            device_suggestion=json.dumps(device_suggestion, ensure_ascii=False)
        )

        db.session.add(new_report)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '报告生成成功',
            'data': new_report.to_list_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


# ==================== 8.3 报告删除 ====================

@baogaozhongxin_bp.route('/baogaojilu/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """删除报告记录"""
    try:
        report = db.session.get(ReportRecord, report_id)
        if not report:
            return jsonify({'code': 404, 'message': '报告不存在', 'data': None}), 404

        file_path = report.file_path
        db.session.delete(report)
        db.session.commit()

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        return jsonify({'code': 200, 'message': '删除成功', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


# ==================== 8.4 报告导出PDF ====================

@baogaozhongxin_bp.route('/baogaojilu/<int:report_id>/daochu', methods=['GET'])
def export_report_pdf(report_id):
    """导出报告为PDF文件"""
    try:
        report = db.session.get(ReportRecord, report_id)
        if not report:
            return jsonify({'code': 404, 'message': '报告不存在', 'data': None}), 404

        if report.file_path and os.path.exists(report.file_path):
            return send_file(report.file_path, as_attachment=True,
                             download_name=f'{report.report_title}.pdf')

        return jsonify({'code': 400, 'message': 'PDF文件尚未生成，请先生成报告', 'data': None}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

