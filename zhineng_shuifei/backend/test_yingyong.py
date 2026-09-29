import io
import os
import tempfile
import unittest
import atexit

# Keep module-level imports from initializing the bundled demo database in place.
_test_db_handle, _test_db_path = tempfile.mkstemp(prefix="huiguan-app-test-", suffix=".db")
os.close(_test_db_handle)
os.environ["SHUIFEI_DB"] = _test_db_path
os.environ.pop("DATABASE_URL", None)
atexit.register(lambda: os.path.exists(_test_db_path) and os.remove(_test_db_path))

import shujuku
from openpyxl import Workbook
from yingyong import app


class YingyongCeshi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.yuan_lujing = shujuku.shujuku_lujing
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        cls.shujuku_lujing = handle.name
        shujuku.shujuku_lujing = cls.shujuku_lujing
        shujuku.shengcheng_biao()

    @classmethod
    def tearDownClass(cls):
        shujuku.shujuku_lujing = cls.yuan_lujing
        if os.path.exists(cls.shujuku_lujing):
            os.remove(cls.shujuku_lujing)

    def setUp(self):
        self.kehu = app.test_client()

    def test_zonglan_baohan_liulei_tubiao(self):
        data = self.kehu.get("/api/zonglan").get_json()["data"]
        self.assertEqual(set(data["trends"]), {"jiance", "guangai", "shifei", "tianqi", "juece_count", "yujing"})
        self.assertEqual(data["zuowu"]["mingcheng"], "油橄榄")

    def test_youganlan_fen_jieduan_shuju(self):
        rows = self.kehu.get("/api/jichu/zuowu").get_json()["data"]
        olive = next(item for item in rows if item["mingcheng"] == "油橄榄")
        self.assertEqual(len(olive["jieduan"]), 5)
        self.assertEqual(olive["shengyujie"], "油脂积累期")

    def test_yucheng_tianqi_he_yuce(self):
        weather = self.kehu.get("/api/tianqi").get_json()["data"]
        self.assertEqual(weather["diqu"], "四川省雅安市雨城区")
        self.assertEqual(len(weather["forecast_list"]), 3)
        prediction = self.kehu.post("/api/yuce", json={"tianshu": 3, "zuowu_id": 3, "shiyong_tianqi": True}).get_json()["data"]
        self.assertEqual(len(prediction["xushui"]), 3)
        self.assertIn("雨城区", prediction["tianqi_shuoming"])

    def test_csv_piliang_daoru_he_riqi_shaixuan(self):
        content = "作物ID,生育期,土壤湿度,土壤温度,空气湿度,光照强度,电导率,记录时间\n3,油脂积累期,30.5,25.6,76,16000,1.25,2026-08-01 08:00:00\n"
        response = self.kehu.post("/api/shuju/piliang", data={"file": (io.BytesIO(content.encode("utf-8")), "jiance.csv")}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["success"], 1)
        history = self.kehu.get("/api/shuju/lishi?kaishi=2026-08-01&jieshu=2026-08-01").get_json()["data"]
        self.assertTrue(any(float(row["turang_shidu"]) == 30.5 for row in history))

    def test_excel_piliang_daoru(self):
        book = Workbook()
        sheet = book.active
        sheet.append(["作物ID", "生育期", "土壤湿度", "土壤温度", "空气湿度", "光照强度", "电导率", "记录时间"])
        sheet.append([3, "油脂积累期", 29.8, 25.2, 79, 15800, 1.28, "2026-08-01 10:00:00"])
        content = io.BytesIO()
        book.save(content)
        content.seek(0)
        response = self.kehu.post("/api/shuju/piliang", data={"file": (content, "jiance.xlsx")}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["success"], 1)

    def test_rengong_caozuodan_buhui_zidong_fankui(self):
        decision = self.kehu.post("/api/juece", json={"zuowu_id": 3}).get_json()["data"]
        order = self.kehu.post("/api/zhiling", json={
            "guangai_liang": decision["recommended_irrigation"],
            "shifei_liang": decision["recommended_fertilization"],
            "beng_yunxing": decision["pump_runtime"],
        }).get_json()["data"]
        self.assertEqual(order["zhuangtai"], "待人工执行")
        device_data = self.kehu.get("/api/shebei").get_json()["data"]
        self.assertNotIn("devices", device_data)
        self.assertEqual(device_data["feedback"], [])
        self.kehu.post(f"/api/zhiling/{order['zhiling_id']}/queren", json={"caozuoren": "测试员"})
        self.kehu.post("/api/fankui", json={"zhiling_id": order["zhiling_id"], "shiji_guangai": 10, "shiji_shifei": 2})
        device_data = self.kehu.get("/api/shebei").get_json()["data"]
        self.assertEqual(device_data["orders"][0]["zhuangtai"], "已人工执行")
        self.assertEqual(len(device_data["feedback"]), 1)

    def test_baogao_xiangqing_he_dayinban(self):
        decision = self.kehu.post("/api/juece", json={"zuowu_id": 3}).get_json()["data"]
        self.kehu.post("/api/zhiling", json={
            "guangai_liang": decision["recommended_irrigation"],
            "shifei_liang": decision["recommended_fertilization"],
            "beng_yunxing": decision["pump_runtime"],
        })
        report = self.kehu.post("/api/baogao", json={}).get_json()["data"]
        detail = self.kehu.get(f"/api/baogao/{report['id']}")
        printable = self.kehu.get(f"/baogao/dayin/{report['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("监测数据摘要", detail.get_json()["data"]["neirong"])
        self.assertEqual(printable.status_code, 200)
        self.assertIn("打印或另存为 PDF", printable.get_data(as_text=True))
        self.assertIn("泵运行时间", printable.get_data(as_text=True))
        self.assertNotIn("beng_yunxing", printable.get_data(as_text=True))
        self.assertNotIn("device_suggestion", printable.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
