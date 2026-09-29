from datetime import datetime
from houduan_shujuluruyujiance import app as monitor_app, db as monitor_db, MonitorData
from houduan_jichuxinxiguanli import app as basic_app, db as basic_db, CropInfo, SoilInfo, DeviceInfo, FertilizerInfo


def init_all():
    print("开始初始化数据库...")

    # --- 初始化监测数据相关表 ---
    with monitor_app.app_context():
        monitor_db.create_all()
        print("✅ 监测数据表 结构创建完成")

        if MonitorData.query.count() == 0:
            mock_monitor_data = [
                MonitorData(crop_id=1, growth_stage="开花期", soil_moisture=45.5, soil_temp=22.1,
                            air_humidity=60.0, light_intensity=30000, ec=1.2,
                            record_time=datetime(2023, 10, 1)),
                MonitorData(crop_id=2, growth_stage="结果期", soil_moisture=30.2, soil_temp=25.5,
                            air_humidity=55.0, light_intensity=45000, ec=1.5,
                            record_time=datetime(2023, 10, 2)),
                MonitorData(crop_id=1, growth_stage="开花期", soil_moisture=42.0, soil_temp=23.0,
                            air_humidity=62.0, light_intensity=32000, ec=1.1,
                            record_time=datetime(2023, 10, 3))
            ]
            monitor_db.session.add_all(mock_monitor_data)
            monitor_db.session.commit()
            print("✅ 监测数据 初始数据插入完成")
        else:
            print("⚠️  监测数据 表中已存在数据，跳过插入")

    # --- 初始化基础信息相关表 ---
    with basic_app.app_context():
        basic_db.create_all()
        print("✅ 基础信息表 结构创建完成")

        # 1. 作物信息
        if CropInfo.query.count() == 0:
            crop_list = [
                CropInfo(name="柑橘", growth_stage="膨大期", water_coeff=1.2, fertilizer_coeff=1.5,
                         suitable_soil="砂壤土"),
                CropInfo(name="蓝莓", growth_stage="开花期", water_coeff=0.8, fertilizer_coeff=1.0,
                         suitable_soil="酸性土"),
                CropInfo(name="油橄榄", growth_stage="结果期", water_coeff=1.0, fertilizer_coeff=1.2,
                         suitable_soil="钙质土"),
                CropInfo(name="玉米", growth_stage="拔节期", water_coeff=1.5, fertilizer_coeff=2.0,
                         suitable_soil="壤土"),
                CropInfo(name="水稻", growth_stage="分蘖期", water_coeff=2.0, fertilizer_coeff=1.8,
                         suitable_soil="黏土")
            ]
            basic_db.session.add_all(crop_list)
            print("✅ 作物信息 初始数据插入完成")

        # 2. 土壤信息
        if SoilInfo.query.count() == 0:
            soil_list = [
                SoilInfo(texture="砂壤土", bulk_density=1.3, field_capacity=25, ec=0.5, ph=6.5,
                         other_params="透气性好"),
                SoilInfo(texture="黏土", bulk_density=1.5, field_capacity=35, ec=0.8, ph=7.0, other_params="保水保肥强")
            ]
            basic_db.session.add_all(soil_list)
            print("✅ 土壤信息 初始数据插入完成")

        # 3. 设备信息
        if DeviceInfo.query.count() == 0:
            device_list = [
                DeviceInfo(name="1号土壤传感器", type="传感器", status="在线", water_tank_level="无",
                           fert_tank_level="无"),
                DeviceInfo(name="主灌溉水泵", type="水泵", status="在线", water_tank_level="85%", fert_tank_level="无")
            ]
            basic_db.session.add_all(device_list)
            print("✅ 设备信息 初始数据插入完成")

        # 4. 肥料信息
        if FertilizerInfo.query.count() == 0:
            fertilizer_list = [
                FertilizerInfo(name="复合肥A", n_content=15, p_content=15, k_content=15),
                FertilizerInfo(name="高钾肥B", n_content=10, p_content=5, k_content=25)
            ]
            basic_db.session.add_all(fertilizer_list)
            print("✅ 肥料信息 初始数据插入完成")

        basic_db.session.commit()

    print("\n" + "=" * 30)
    print("🎉 数据库初始化全部完成！")
    print("=" * 30)


if __name__ == '__main__':
    init_all()
