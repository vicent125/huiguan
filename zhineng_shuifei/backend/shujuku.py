"""数据库连接、建表和演示数据。

运行环境：Python 3.10+，pymysql（MySQL模式）/ sqlite3（SQLite模式）
默认使用 SQLite 方便本地演示；设置 DATABASE_URL 后使用 MySQL。

数据库表结构（15张业务表 + 1张模型参数表）：
  yonghu(用户), zuowu(作物), zuowu_jieduan(作物生育阶段), turang(土壤),
  feiliao(肥料), jiance(监测数据), tianqi(天气), yuce(预测记录),
  juece(决策记录), zhiling(人工操作单), fankui(执行反馈),
  baogao(分析报告), yujing(预警阈值), rizhi(操作日志),
  shebei(设备信息), moxing_canshu(增量回归模型参数)
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
from urllib.parse import unquote, urlparse

gen_path = os.path.dirname(os.path.abspath(__file__))
shujuku_lujing = os.environ.get("SHUIFEI_DB", os.path.join(gen_path, "nongye.db"))


class JianRongHang(dict):
    """让 MySQL 字典行同时兼容 row[0] 和 row['field'] 的旧写法。"""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class MySqlYoubiao:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = cursor.lastrowid

    def fetchone(self):
        row = self.cursor.fetchone()
        return JianRongHang(row) if row else None

    def fetchall(self):
        return [JianRongHang(row) for row in self.cursor.fetchall()]


class PostgresYoubiao:
    """Small compatibility wrapper for the existing SQLite-style DB API."""
    def __init__(self, cursor, lastrowid=None):
        self.cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self):
        row = self.cursor.fetchone()
        return JianRongHang(dict(row)) if row else None

    def fetchall(self):
        return [JianRongHang(dict(row)) for row in self.cursor.fetchall()]


class MySqlLianjie:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql.replace("?", "%s"), params)
        return MySqlYoubiao(cursor)

    def executemany(self, sql, params):
        cursor = self.conn.cursor()
        cursor.executemany(sql.replace("?", "%s"), params)
        return MySqlYoubiao(cursor)

    def executescript(self, script):
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


class PostgresLianjie:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _sql(sql):
        return sql.replace("?", "%s")

    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        statement = self._sql(sql)
        # Preserve cursor.lastrowid semantics for INSERT statements used by the app.
        if statement.lstrip().upper().startswith("INSERT") and "RETURNING" not in statement.upper():
            statement += " RETURNING id"
        cursor.execute(statement, params)
        lastrowid = None
        if statement.lstrip().upper().startswith("INSERT"):
            row = cursor.fetchone()
            if row:
                lastrowid = row[0]
        return PostgresYoubiao(cursor, lastrowid)

    def executemany(self, sql, params):
        cursor = self.conn.cursor()
        cursor.executemany(self._sql(sql), params)
        return PostgresYoubiao(cursor)

    def executescript(self, script):
        with self.conn.cursor() as cursor:
            cursor.execute(script)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def shifou_mysql():
    return os.environ.get("DATABASE_URL", "").lower().startswith("mysql")


def shifou_postgres():
    return os.environ.get("DATABASE_URL", "").lower().startswith(("postgres://", "postgresql://"))


def lianjie():
    if shifou_postgres():
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:
            raise RuntimeError("PostgreSQL 模式需要安装 psycopg2-binary") from exc
        conn = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)
        return PostgresLianjie(conn)
    if shifou_mysql():
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError("MySQL 模式需要先安装 requirements.txt 中的 PyMySQL") from exc
        parsed = urlparse(os.environ["DATABASE_URL"])
        conn = pymysql.connect(
            host=parsed.hostname or "127.0.0.1",
            port=parsed.port or 3306,
            user=unquote(parsed.username or "root"),
            password=unquote(parsed.password or ""),
            database=(parsed.path or "/shuifei").lstrip("/"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        return MySqlLianjie(conn)
    conn = sqlite3.connect(shujuku_lujing)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SQLITE_BIAO = """
CREATE TABLE IF NOT EXISTS yonghu (id INTEGER PRIMARY KEY, zhanghao TEXT UNIQUE, mima TEXT, mingcheng TEXT, juese TEXT);
CREATE TABLE IF NOT EXISTS zuowu (id INTEGER PRIMARY KEY, mingcheng TEXT, shengyujie TEXT, xushui_xishu REAL, xufei_xishu REAL, shiyi_turang TEXT, mubiao_shidu REAL, tuijian_shuifen TEXT, tuijian_feiliao TEXT, shuoming TEXT);
CREATE TABLE IF NOT EXISTS zuowu_jieduan (id INTEGER PRIMARY KEY, zuowu_id INTEGER, jieduan TEXT, xushui_xishu REAL, xufei_xishu REAL, mubiao_shidu_min REAL, mubiao_shidu_max REAL, nongyi_tishi TEXT);
CREATE TABLE IF NOT EXISTS turang (id INTEGER PRIMARY KEY, zhidi TEXT, rongzhong REAL, chitian_chishuiliang REAL, ph REAL, dian_daolv REAL, qita TEXT);
CREATE TABLE IF NOT EXISTS shebei (id INTEGER PRIMARY KEY, mingcheng TEXT, leixing TEXT, zhuangtai TEXT, shuixiang REAL, feixiang REAL, liuliang REAL);
CREATE TABLE IF NOT EXISTS feiliao (id INTEGER PRIMARY KEY, mingcheng TEXT, dan REAL, lin REAL, jia REAL);
CREATE TABLE IF NOT EXISTS jiance (id INTEGER PRIMARY KEY, zuowu_id INTEGER, shengyujie TEXT, turang_shidu REAL, turang_wendu REAL, kongqi_shidu REAL, guangzhao REAL, dian_daolv REAL, jilu_shijian TEXT);
CREATE TABLE IF NOT EXISTS tianqi (id INTEGER PRIMARY KEY, yubaoriqi TEXT UNIQUE, zuigao_wendu REAL, zuidi_wendu REAL, kongqi_shidu REAL, jiangyu_gailv REAL, jiangyu_liang REAL, tianqi_leixing TEXT, zhengfa_liang REAL, diqu TEXT, shuju_laiyuan TEXT, gengxin_shijian TEXT);
CREATE TABLE IF NOT EXISTS yuce (id INTEGER PRIMARY KEY, zuowu_id INTEGER, yuce_tianshu INTEGER, xushui_json TEXT, xufei_json TEXT, shidu_json TEXT, fenxi TEXT, tianqi_shuoming TEXT, jilu_shijian TEXT);
CREATE TABLE IF NOT EXISTS juece (id INTEGER PRIMARY KEY, jiance_id INTEGER, zuowu_id INTEGER, zhuangtai TEXT, feili_zhuangtai TEXT, guangai_liang REAL, shifei_liang REAL, beng_yunxing REAL, yuanyin TEXT, jilu_shijian TEXT);
CREATE TABLE IF NOT EXISTS baogao (id INTEGER PRIMARY KEY, biaoti TEXT, chuangjian_shijian TEXT, gengxin_shijian TEXT, zuowu TEXT, zhaiyao TEXT, zhuangtai TEXT, daochuren TEXT, daochu_zhuangtai TEXT, neirong_json TEXT);
CREATE TABLE IF NOT EXISTS zhiling (id INTEGER PRIMARY KEY, shebei_id INTEGER, guangai_liang REAL, shifei_liang REAL, beng_yunxing REAL, zhuangtai TEXT, chuangjian_shijian TEXT, xiafa_shijian TEXT, caozuoren TEXT, caozuo_beizhu TEXT);
CREATE TABLE IF NOT EXISTS fankui (id INTEGER PRIMARY KEY, zhiling_id INTEGER, shiji_guangai REAL, shiji_shifei REAL, zhuangtai TEXT, shangbao_shijian TEXT);
CREATE TABLE IF NOT EXISTS yujing (id INTEGER PRIMARY KEY, leixing TEXT, mingcheng TEXT, zuixiao REAL, zuida REAL, dengji TEXT, shuoming TEXT);
CREATE TABLE IF NOT EXISTS rizhi (id INTEGER PRIMARY KEY, caozuo_shijian TEXT, caozuo_leixing TEXT, caozuo_neirong TEXT, caozuoren TEXT);
CREATE TABLE IF NOT EXISTS moxing_canshu (mingcheng TEXT PRIMARY KEY, n INTEGER, mean_x REAL, mean_y REAL, var_x REAL, cov_xy REAL, gengxin_shijian TEXT);
CREATE TABLE IF NOT EXISTS ai_fenxi (id INTEGER PRIMARY KEY, request_id TEXT, zuowu_id INTEGER, moxing_mingcheng TEXT, moxing_banben TEXT, tishici_banben TEXT, jiangji_shiyong INTEGER, haoshi REAL, shuru_json TEXT, shuchu_json TEXT, cuowu_xinxi TEXT, zhixindu REAL, zhuangtai TEXT, jilu_shijian TEXT);
"""


def _sqlite_qianyi(conn):
    columns = {
        "zuowu": [("mubiao_shidu", "REAL"), ("tuijian_shuifen", "TEXT"), ("tuijian_feiliao", "TEXT"), ("shuoming", "TEXT")],
        "tianqi": [("diqu", "TEXT"), ("shuju_laiyuan", "TEXT"), ("gengxin_shijian", "TEXT")],
        "yuce": [("tianqi_shuoming", "TEXT")],
        "juece": [("zuowu_id", "INTEGER"), ("beng_yunxing", "REAL")],
        "baogao": [("gengxin_shijian", "TEXT"), ("daochuren", "TEXT"), ("daochu_zhuangtai", "TEXT")],
        "zhiling": [("caozuoren", "TEXT"), ("caozuo_beizhu", "TEXT")],
    }
    for table, fields in columns.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, kind in fields:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")


def shengcheng_biao():
    conn = lianjie()
    if shifou_postgres():
        with open(os.path.join(gen_path, "postgres_chushihua.sql"), "r", encoding="utf-8") as file:
            conn.executescript(file.read())
    elif shifou_mysql():
        with open(os.path.join(gen_path, "mysql_chushihua.sql"), "r", encoding="utf-8") as file:
            conn.executescript(file.read())
    else:
        conn.executescript(SQLITE_BIAO)
        _sqlite_qianyi(conn)
    _chushi_shuju(conn)
    conn.commit()
    conn.close()


def _chushi_shuju(conn):
    if conn.execute("SELECT COUNT(*) FROM yonghu").fetchone()[0] == 0:
        conn.execute("INSERT INTO yonghu(zhanghao,mima,mingcheng,juese) VALUES (?,?,?,?)", ("admin", "123456", "系统管理员", "管理员"))
    if conn.execute("SELECT COUNT(*) FROM zuowu").fetchone()[0] == 0:
        conn.executemany("INSERT INTO zuowu(id,mingcheng,shengyujie,xushui_xishu,xufei_xishu,shiyi_turang,mubiao_shidu,tuijian_shuifen,tuijian_feiliao,shuoming) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            (1, "柑橘", "果实膨大期", 1.20, 1.10, "砂壤土", 65, "保持根区湿润，避免长期积水", "膨果期注意钾肥配比", "参数需结合当地品种和树龄校准"),
            (2, "蓝莓", "开花期", .90, 1.00, "酸性砂壤土", 68, "少量多次补水", "采用酸性水溶肥", "适宜 pH 约 4.5-5.5"),
            (3, "油橄榄", "油脂积累期", .75, .70, "排水良好的砂壤土", 60, "雨城区雨季重视排水，干热时小水勤灌", "控制氮肥，适当补充钾肥", "演示参数来源于一般栽培规律，应用前需进行本地田间校准"),
            (4, "玉米", "拔节期", 1.35, 1.20, "壤土", 65, "拔节期保持水分稳定", "氮钾配合施用", "避免大水漫灌"),
            (5, "水稻", "分蘖期", 1.50, 1.15, "黏土", 75, "浅水勤灌", "根据叶色和苗情追肥", "不同水稻灌溉模式需单独标定"),
        ])
    olive = conn.execute("SELECT id FROM zuowu WHERE mingcheng='油橄榄'").fetchone()
    if olive:
        conn.execute("UPDATE zuowu SET shengyujie=?,xushui_xishu=?,xufei_xishu=?,shiyi_turang=?,mubiao_shidu=?,tuijian_shuifen=?,tuijian_feiliao=?,shuoming=? WHERE id=?", ("油脂积累期", .75, .70, "排水良好的砂壤土", 60, "雨城区雨季重视排水，干热时小水勤灌", "控制氮肥，适当补充钾肥", "演示参数需根据品种、树龄与田间试验校准", olive["id"]))
        if conn.execute("SELECT COUNT(*) FROM zuowu_jieduan WHERE zuowu_id=?", (olive["id"],)).fetchone()[0] == 0:
            conn.executemany("INSERT INTO zuowu_jieduan(zuowu_id,jieduan,xushui_xishu,xufei_xishu,mubiao_shidu_min,mubiao_shidu_max,nongyi_tishi) VALUES (?,?,?,?,?,?,?)", [
                (olive["id"], "萌芽展叶期", .65, .75, 58, 68, "促进新梢生长，避免根区过湿"),
                (olive["id"], "开花坐果期", .85, .90, 62, 72, "水分波动会影响坐果，保持均匀供水"),
                (olive["id"], "果实膨大期", .95, 1.00, 62, 72, "需水较高，结合降雨控制单次灌溉量"),
                (olive["id"], "油脂积累期", .75, .70, 55, 65, "适度控水，控制氮肥并关注钾素"),
                (olive["id"], "采后恢复期", .55, .85, 55, 65, "采后恢复树势，低温前避免过量施肥"),
            ])
    if conn.execute("SELECT COUNT(*) FROM turang").fetchone()[0] == 0:
        conn.executemany("INSERT INTO turang(id,zhidi,rongzhong,chitian_chishuiliang,ph,dian_daolv,qita) VALUES (?,?,?,?,?,?,?)", [
            (1, "砂壤土", 1.32, 26, 6.5, 1.15, "排水性好，适合油橄榄根系"),
            (2, "壤土", 1.42, 31, 6.8, 1.42, "保水保肥均衡"),
            (3, "黏土", 1.50, 36, 7.1, 1.76, "雨季需重点关注积水"),
        ])
    if conn.execute("SELECT COUNT(*) FROM shebei").fetchone()[0] == 0:
        conn.executemany("INSERT INTO shebei(id,mingcheng,leixing,zhuangtai,shuixiang,feixiang,liuliang) VALUES (?,?,?,?,?,?,?)", [
            (1, "现有一号水肥机", "水肥一体机", "人工登记可用", 82, 68, 2.0),
            (2, "雨城示范地传感器", "土壤传感器", "人工采集", 0, 0, 0),
        ])
    if conn.execute("SELECT COUNT(*) FROM feiliao").fetchone()[0] == 0:
        conn.executemany("INSERT INTO feiliao(id,mingcheng,dan,lin,jia) VALUES (?,?,?,?,?)", [(1, "平衡型复合肥", 15, 15, 15), (2, "油橄榄高钾水溶肥", 10, 5, 25)])
    if olive and conn.execute("SELECT COUNT(*) FROM jiance WHERE zuowu_id=?", (olive["id"],)).fetchone()[0] == 0:
        now = datetime.now()
        values = [36.8, 35.9, 34.7, 33.8, 32.6, 31.9, 31.2]
        for i, moisture in enumerate(values):
            when = (now - timedelta(days=6 - i)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO jiance(zuowu_id,shengyujie,turang_shidu,turang_wendu,kongqi_shidu,guangzhao,dian_daolv,jilu_shijian) VALUES (?,?,?,?,?,?,?,?)", (olive["id"], "油脂积累期", moisture, 24.5 + i * .3, 78 - i, 13800 + i * 650, 1.18 + i * .02, when))
    if conn.execute("SELECT COUNT(*) FROM tianqi").fetchone()[0] == 0:
        today = date.today()
        rows = []
        for i, item in enumerate([(29, 22, 82, 55, 5.2, "阵雨", 3.8), (28, 21, 86, 70, 11.0, "中雨", 3.2), (30, 22, 80, 40, 2.6, "多云", 4.1)]):
            rows.append((str(today + timedelta(days=i)), *item, "四川省雅安市雨城区", "本地演示缓存", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.executemany("INSERT INTO tianqi(yubaoriqi,zuigao_wendu,zuidi_wendu,kongqi_shidu,jiangyu_gailv,jiangyu_liang,tianqi_leixing,zhengfa_liang,diqu,shuju_laiyuan,gengxin_shijian) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.execute("UPDATE tianqi SET diqu=COALESCE(diqu,'四川省雅安市雨城区'), shuju_laiyuan=COALESCE(shuju_laiyuan,'本地演示缓存'), gengxin_shijian=COALESCE(gengxin_shijian,?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    if conn.execute("SELECT COUNT(*) FROM yujing").fetchone()[0] == 0:
        conn.executemany("INSERT INTO yujing(id,leixing,mingcheng,zuixiao,zuida,dengji,shuoming) VALUES (?,?,?,?,?,?,?)", [
            (1, "turang_shidu", "土壤湿度", 18, 48, "二级", "低于下限或高于上限时提醒"),
            (2, "dian_daolv", "土壤电导率", .5, 2.5, "三级", "用于判断肥力与盐分风险"),
        ])
    if conn.execute("SELECT COUNT(*) FROM rizhi").fetchone()[0] == 0:
        conn.execute("INSERT INTO rizhi(caozuo_shijian,caozuo_leixing,caozuo_neirong,caozuoren) VALUES (?,?,?,?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "系统初始化", "完成雨城区油橄榄演示数据初始化", "系统"))


def zidian(row):
    return dict(row) if row else None


shengcheng_biao()
