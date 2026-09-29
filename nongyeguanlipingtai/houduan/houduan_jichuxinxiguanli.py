from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import pandas as pd
import os
app = Flask(__name__)
CORS(app)

@app.get('/api/health')
def health_check():
    return {'code': 200, 'message': '服务运行正常', 'data': None}

# 配置数据库连接（确保与 houduan_shujuluruyujiance.py 指向同一个数据库）
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'BASIC_DATABASE_URL', os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'nongye_guanli.db'))
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'shuju')  # Excel数据文件夹路径

db = SQLAlchemy(app)

# ==================== 数据模型 ====================
class CropInfo(db.Model):
    __tablename__ = 'crop_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    growth_stage = db.Column(db.String(50))
    water_coeff = db.Column(db.Float)
    fertilizer_coeff = db.Column(db.Float)
    suitable_soil = db.Column(db.String(50))


class SoilInfo(db.Model):
    __tablename__ = 'soil_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    texture = db.Column(db.String(50))
    bulk_density = db.Column(db.Float)
    field_capacity = db.Column(db.Float)
    ec = db.Column(db.Float)
    ph = db.Column(db.Float)
    other_params = db.Column(db.String(100))


class DeviceInfo(db.Model):
    __tablename__ = 'device_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50))
    status = db.Column(db.String(20))
    water_tank_level = db.Column(db.String(20))
    fert_tank_level = db.Column(db.String(20))


class FertilizerInfo(db.Model):
    __tablename__ = 'fertilizer_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    n_content = db.Column(db.Float)
    p_content = db.Column(db.Float)
    k_content = db.Column(db.Float)


# ==================== 接口路由 ====================

@app.route('/api/zuowuguanli', methods=['GET'])
def zuowuguanli():
    """获取作物管理列表"""
    records = CropInfo.query.all()
    result = [{
        "id": r.id,
        "name": r.name,
        "growth_stage": r.growth_stage,
        "water_coeff": r.water_coeff,
        "fertilizer_coeff": r.fertilizer_coeff,
        "suitable_soil": r.suitable_soil
    } for r in records]
    return jsonify({"code": 200, "msg": "获取成功", "data": result})


@app.route('/api/turangcanshuguanli', methods=['GET'])
def turangcanshuguanli():
    """获取土壤参数管理列表"""
    records = SoilInfo.query.all()
    result = [{
        "id": r.id,
        "texture": r.texture,
        "bulk_density": r.bulk_density,
        "field_capacity": r.field_capacity,
        "ec": r.ec,
        "ph": r.ph,
        "other_params": r.other_params
    } for r in records]
    return jsonify({"code": 200, "msg": "获取成功", "data": result})


@app.route('/api/shebeixinxiguanli', methods=['GET'])
def shebeixinxiguanli():
    """获取设备信息管理列表"""
    records = DeviceInfo.query.all()
    result = [{
        "id": r.id,
        "name": r.name,
        "type": r.type,
        "status": r.status,
        "water_tank_level": r.water_tank_level,
        "fert_tank_level": r.fert_tank_level
    } for r in records]
    return jsonify({"code": 200, "msg": "获取成功", "data": result})


@app.route('/api/feiliaoxinxiguanli', methods=['GET'])
def feiliaoxinxiguanli():
    """获取肥料信息管理列表"""
    records = FertilizerInfo.query.all()
    result = [{
        "id": r.id,
        "name": r.name,
        "n_content": r.n_content,
        "p_content": r.p_content,
        "k_content": r.k_content
    } for r in records]
    return jsonify({"code": 200, "msg": "获取成功", "data": result})


# ==================== 土壤数据导入接口 ====================

@app.route('/api/daoru_soil', methods=['POST'])
def daoru_soil():
    """
    导入土壤数据

    前端调用方式：
    POST /api/daoru_soil

    返回示例：
    {
        "code": 200,
        "msg": "导入成功",
        "data": {
            "total": 50000,
            "success": 49800,
            "failed": 200
        }
    }
    """
    try:
        excel_folder = app.config['UPLOAD_FOLDER']

        # 检查文件夹是否存在
        if not os.path.exists(excel_folder):
            return jsonify({"code": 400, "msg": f"Excel文件夹不存在: {excel_folder}", "data": None})

        # ==================== 步骤1：读取编码对照表 ====================

        # 质地名称编码表
        code_file_1 = os.path.join(excel_folder, 'turangzhidi_shuju1.xlsx')
        if not os.path.exists(code_file_1):
            return jsonify({"code": 400, "msg": f"文件不存在: {code_file_1}", "data": None})
        df_texture_code = pd.read_excel(code_file_1)
        texture_dict = dict(zip(df_texture_code['CODE'], df_texture_code['VALUE']))

        # 颗粒分级编码表
        code_file_2 = os.path.join(excel_folder, 'turangzhidi_shuju2.xlsx')
        if not os.path.exists(code_file_2):
            return jsonify({"code": 400, "msg": f"文件不存在: {code_file_2}", "data": None})
        df_particle_code = pd.read_excel(code_file_2)
        particle_dict = dict(zip(df_particle_code['CODE'], df_particle_code['VALUE']))

        # 持水量编码表
        code_file_3 = os.path.join(excel_folder, 'tianchichiliang_shuju1.xlsx')
        if not os.path.exists(code_file_3):
            return jsonify({"code": 400, "msg": f"文件不存在: {code_file_3}", "data": None})
        df_water_code = pd.read_excel(code_file_3)
        water_dict = dict(zip(df_water_code['CODE'], df_water_code['VALUE']))

        # ==================== 步骤2：读取数据表 ====================

        # 土壤质地数据
        data_file_1 = os.path.join(excel_folder, 'turangzhidi_shuju3.xlsx')
        df_texture = pd.read_excel(data_file_1)

        # 土壤容重数据
        data_file_2 = os.path.join(excel_folder, 'turangrongliang_shuju.xlsx')
        df_bulk = pd.read_excel(data_file_2)

        # PH值数据
        data_file_3 = os.path.join(excel_folder, 'PHzhi_shuju.xlsx')
        df_ph = pd.read_excel(data_file_3)

        # 电导率数据
        data_file_4 = os.path.join(excel_folder, 'diandaolv_shuju.xlsx')
        df_ec = pd.read_excel(data_file_4)

        # 持水量数据
        data_file_5 = os.path.join(excel_folder, 'tianchichiliang_shuju2.xlsx')
        df_water = pd.read_excel(data_file_5)

        # ==================== 步骤3：合并数据表 ====================

        df_merged = df_texture.merge(df_bulk, on='ID', how='outer')
        df_merged = df_merged.merge(df_ph, on='ID', how='outer')
        df_merged = df_merged.merge(df_ec, on='ID', how='outer')
        df_merged = df_merged.merge(df_water, on='ID', how='outer')

        # ==================== 步骤4：编码转换 ====================

        # 转换编码
        df_merged['texture'] = df_merged['T_USDA_TEX_CLASS'].map(texture_dict)
        df_merged['field_capacity'] = df_merged['AWC_CLASS'].map(water_dict)
        df_merged['bulk_density'] = df_merged['T_BULK_DENSITY']
        df_merged['ph'] = df_merged['T_PH_H2O']
        df_merged['ec'] = df_merged['T_ECE']

        # ==================== 步骤5：导入数据库 ====================

        # 清空原表数据（可选，如需保留原数据请注释掉）
        SoilInfo.query.delete()
        db.session.commit()

        success_count = 0
        failed_count = 0

        final_cols = ['texture', 'bulk_density', 'ph', 'ec', 'field_capacity']

        for idx, row in df_merged.iterrows():
            try:
                # 至少有一个字段不为空才导入
                if not pd.isna(row[final_cols]).all():
                    soil_info = SoilInfo(
                        texture=row['texture'] if pd.notna(row['texture']) else None,
                        bulk_density=float(row['bulk_density']) if pd.notna(row['bulk_density']) else None,
                        field_capacity=float(row['field_capacity']) if pd.notna(row['field_capacity']) else None,
                        ec=float(row['ec']) if pd.notna(row['ec']) else None,
                        ph=float(row['ph']) if pd.notna(row['ph']) else None
                    )
                    db.session.add(soil_info)
                    success_count += 1

                    # 每1000条提交一次
                    if success_count % 1000 == 0:
                        db.session.commit()
            except Exception as e:
                failed_count += 1
                continue

        # 提交剩余数据
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "导入成功",
            "data": {
                "total": len(df_merged),
                "success": success_count,
                "failed": failed_count
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"导入失败: {str(e)}"})


if __name__ == '__main__':
    # 注意：初始化数据库请运行 init_db.py
    app.run(debug=False, port=5002)
