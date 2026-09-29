"""AI辅助分析测试 —— 接口测试、模型超时测试、非法JSON测试。

运行方式：python test_ai_fuzhu.py
测试内容：
  1. AI未启用时自动降级
  2. AI输入构造正确性
  3. JSON提取和校验
  4. 频率限制
  5. 模型超时降级
  6. 非法JSON降级
  7. AI分析接口端到端测试
  8. 安全校验测试
"""
import json
import os
import sys
import atexit
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tests use a private writable SQLite file instead of the bundled demo database.
# This keeps the repository database unchanged and also works in read-only CI workspaces.
_test_db_handle, _test_db_path = tempfile.mkstemp(prefix="huiguan-ai-test-", suffix=".db")
os.close(_test_db_handle)
os.environ["SHUIFEI_DB"] = _test_db_path
os.environ.pop("DATABASE_URL", None)
atexit.register(lambda: os.path.exists(_test_db_path) and os.remove(_test_db_path))


class TestAiFuzhuJiangji(unittest.TestCase):
    """测试AI未配置时自动降级。"""

    def test_weizhi_peizhi_jiangji(self):
        from ai_fuzhu import diaoyong_moxing
        with patch.dict(os.environ, {}, clear=True):
            jiance = {"turang_shidu": 30, "dian_daolv": 1.2}
            tianqi = [{"yubaoriqi": "2026-08-22", "zuigao_wendu": 28, "jiangyu_gailv": 30}]
            zuowu = {"mingcheng": "油橄榄", "shengyujie": "油脂积累期"}
            jieguo = diaoyong_moxing(jiance, tianqi, zuowu)
            self.assertFalse(jieguo["success"])
            self.assertTrue(jieguo["fallback_used"])
            self.assertIn("AI_API_KEY", jieguo["error"])

    def test_shuru_gouzao(self):
        from ai_fuzhu import gouzao_shuru
        jiance = {"turang_shidu": 30, "turang_wendu": 25, "dian_daolv": 1.2, "guangzhao": 15000}
        tianqi = [{"yubaoriqi": "2026-08-22", "zuigao_wendu": 28, "jiangyu_gailv": 30, "jiangyu_liang": 5}]
        zuowu = {"mingcheng": "油橄榄", "shengyujie": "油脂积累期", "xushui_xishu": 0.75}
        shuru = gouzao_shuru(jiance, tianqi, zuowu)
        self.assertEqual(shuru["crop_name"], "油橄榄")
        self.assertEqual(shuru["soil_moisture"], 30)
        self.assertEqual(len(shuru["weather_forecast"]), 1)
        self.assertEqual(shuru["weather_forecast"][0]["max_temp"], 28)

    def test_tiqu_json(self):
        from ai_fuzhu import tiqu_json
        result = tiqu_json('{"confidence": 0.8}')
        self.assertEqual(result["confidence"], 0.8)
        result = tiqu_json('```json\n{"confidence": 0.8}\n```')
        self.assertEqual(result["confidence"], 0.8)
        result = tiqu_json('分析结果如下：{"confidence": 0.8} 以上。')
        self.assertEqual(result["confidence"], 0.8)
        result = tiqu_json('不是JSON')
        self.assertIsNone(result)
        result = tiqu_json('')
        self.assertIsNone(result)

    def test_jiaoyan_shuchu(self):
        from ai_fuzhu import jiaoyan_shuchu
        hege = {
            "crop_name": "油橄榄", "growth_stage": "油脂积累期", "analysis_summary": "测试",
            "soil_moisture_status": "normal", "fertility_status": "normal",
            "drought_risk": "low", "weather_impact": "无",
            "three_day_forecast": [], "recommended_irrigation": {}, "recommended_fertilizer": {},
            "decision_basis": [], "missing_data": [], "warnings": [],
            "confidence": 0.8, "human_confirmation_required": True,
        }
        tongguo, queshi = jiaoyan_shuchu(hege)
        self.assertTrue(tongguo)
        self.assertEqual(queshi, [])
        que_ziduan = dict(hege)
        del que_ziduan["confidence"]
        tongguo, queshi = jiaoyan_shuchu(que_ziduan)
        self.assertFalse(tongguo)
        self.assertIn("confidence", queshi)
        fanwei_cuowu = dict(hege)
        fanwei_cuowu["confidence"] = 1.5
        tongguo, queshi = jiaoyan_shuchu(fanwei_cuowu)
        self.assertFalse(tongguo)

    def test_jiangji_jieguo(self):
        from ai_fuzhu import jiangji_jieguo
        yuce = {"dates": ["2026-08-22", "2026-08-23", "2026-08-24"], "xushui": [15, 16, 14], "xufei": [4, 4.5, 3.8], "shidu": [28, 27, 26], "fenxi": "测试", "tianqi_shuoming": "测试"}
        juece = {"water_status": "水分适宜", "fertility_status": "肥力适宜", "recommended_irrigation": 16, "recommended_fertilization": 4.5, "pump_runtime": 8, "reason": "测试"}
        zuowu = {"mingcheng": "油橄榄", "shengyujie": "油脂积累期"}
        jieguo = jiangji_jieguo(yuce, juece, zuowu)
        self.assertEqual(jieguo["crop_name"], "油橄榄")
        self.assertEqual(jieguo["soil_moisture_status"], "正常")
        self.assertEqual(jieguo["confidence"], 0.6)
        self.assertTrue(jieguo["human_confirmation_required"])
        self.assertEqual(len(jieguo["three_day_forecast"]), 3)


class TestPinlvXianzhi(unittest.TestCase):
    """测试频率限制。"""

    def test_pinlv_xianzhi(self):
        from ai_fuzhu import PinlvXianzhi
        xianzhi = PinlvXianzhi(3)
        self.assertTrue(xianzhi.jiancha())
        self.assertTrue(xianzhi.jiancha())
        self.assertTrue(xianzhi.jiancha())
        self.assertFalse(xianzhi.jiancha())


class TestAnquanJiaoyan(unittest.TestCase):
    """测试安全校验。"""

    def test_tongguo_jiaoyan(self):
        from anquan_jiaoyan import jiaoyan
        jieguo = jiaoyan(
            guangai=20, shifei=5, beng_shijian=10, shidu=30, jiangyu_gailv=20,
            shuixiang_yewei=80, feixiang_yewei=70, shebei_zhuangtai="在线",
            ai_zhixindu=0.8, ai_ziduan_wanzheng=True,
            tuijian_danwei={"irrigation_unit": "L/m2", "fertilizer_unit": "kg/亩"},
            yichang_shuru=False, weichuli_yujing=[],
        )
        self.assertTrue(jieguo["passed"])
        self.assertEqual(jieguo["status"], "approved")

    def test_juece_jiaoyan(self):
        from anquan_jiaoyan import jiaoyan
        jieguo = jiaoyan(
            guangai=100, shifei=5, beng_shijian=10, shidu=30, jiangyu_gailv=20,
            shuixiang_yewei=80, feixiang_yewei=70, shebei_zhuangtai="在线",
            ai_zhixindu=0.8, ai_ziduan_wanzheng=True,
            tuijian_danwei={"irrigation_unit": "L/m2", "fertilizer_unit": "kg/亩"},
            yichang_shuru=False, weichuli_yujing=[],
        )
        self.assertFalse(jieguo["passed"])
        self.assertEqual(jieguo["status"], "rejected")
        self.assertTrue(len(jieguo["blocked_reasons"]) > 0)

    def test_fuke_jiaoyan(self):
        from anquan_jiaoyan import jiaoyan
        jieguo = jiaoyan(
            guangai=20, shifei=5, beng_shijian=10, shidu=50, jiangyu_gailv=20,
            shuixiang_yewei=80, feixiang_yewei=70, shebei_zhuangtai="在线",
            ai_zhixindu=0.3, ai_ziduan_wanzheng=True,
            tuijian_danwei={"irrigation_unit": "L/m2", "fertilizer_unit": "kg/亩"},
            yichang_shuru=False, weichuli_yujing=[],
        )
        self.assertTrue(jieguo["passed"])
        self.assertEqual(jieguo["status"], "manual_review")
        self.assertTrue(len(jieguo["warnings"]) > 0)


class TestAiJiekou(unittest.TestCase):
    """测试AI接口路由（使用Flask test_client）。"""

    def setUp(self):
        from yingyong import app
        self.app = app
        self.client = app.test_client()

    def test_ai_zhuangtai_jiekou(self):
        response = self.client.get("/api/yucefenxi/ai-zhuangtai")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["code"], 200)
        self.assertIn("enabled", data["data"])

    def test_ai_fenxi_jiangji_jiekou(self):
        """测试AI未配置时接口自动降级。"""
        with patch.dict(os.environ, {"AI_API_KEY": ""}, clear=False):
            response = self.client.post(
                "/api/yucefenxi/ai-analyze",
                json={"crop_id": 3, "forecast_range": 3, "weather_enabled": True},
            )
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["code"], 200)
            self.assertTrue(data["data"]["fallback_used"])
            self.assertTrue(data["data"]["success"])

    def test_ai_fenxi_cuowu_canshu(self):
        """测试错误参数处理。"""
        response = self.client.post(
            "/api/yucefenxi/ai-analyze",
            json={},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["code"], 200)


class TestMoxingChaoshi(unittest.TestCase):
    """测试模型超时降级。"""

    @patch("ai_fuzhu.requests.post")
    def test_chaoshi_jiangji(self, mock_post):
        import requests as req
        from ai_fuzhu import diaoyong_moxing
        mock_post.side_effect = req.Timeout("模拟超时")
        with patch.dict(os.environ, {"AI_API_KEY": "test-key", "AI_TIMEOUT": "1"}, clear=True):
            jiance = {"turang_shidu": 30}
            tianqi = [{"yubaoriqi": "2026-08-22"}]
            zuowu = {"mingcheng": "油橄榄"}
            jieguo = diaoyong_moxing(jiance, tianqi, zuowu)
            self.assertFalse(jieguo["success"])
            self.assertTrue(jieguo["fallback_used"])
            self.assertIn("超时", jieguo["error"])


class TestFeifaJson(unittest.TestCase):
    """测试非法JSON降级。"""

    @patch("ai_fuzhu.requests.post")
    def test_feifa_json_jiangji(self, mock_post):
        from ai_fuzhu import diaoyong_moxing
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "这不是一个有效的JSON"}}]
        }
        mock_post.return_value = mock_response
        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}, clear=True):
            jiance = {"turang_shidu": 30}
            tianqi = [{"yubaoriqi": "2026-08-22"}]
            zuowu = {"mingcheng": "油橄榄"}
            jieguo = diaoyong_moxing(jiance, tianqi, zuowu)
            self.assertFalse(jieguo["success"])
            self.assertTrue(jieguo["fallback_used"])
            self.assertIn("非法JSON", jieguo["error"])

    @patch("ai_fuzhu.requests.post")
    def test_ziduan_buwanzheng_jiangji(self, mock_post):
        from ai_fuzhu import diaoyong_moxing
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"crop_name": "油橄榄"})}}]
        }
        mock_post.return_value = mock_response
        with patch.dict(os.environ, {"AI_API_KEY": "test-key"}, clear=True):
            jiance = {"turang_shidu": 30}
            tianqi = [{"yubaoriqi": "2026-08-22"}]
            zuowu = {"mingcheng": "油橄榄"}
            jieguo = diaoyong_moxing(jiance, tianqi, zuowu)
            self.assertFalse(jieguo["success"])
            self.assertTrue(jieguo["fallback_used"])
            self.assertIn("校验失败", jieguo["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
