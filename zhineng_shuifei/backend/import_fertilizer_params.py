"""Import the supplied fertilizer parameter workbook into the local database."""
from pathlib import Path
import openpyxl
from shujuku import lianjie

SOURCE = Path(r"C:\Users\D1782\Desktop\肥料参数.xlsx")


def import_fertilizers(path=SOURCE):
    book = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet = book.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows or len(rows[0]) < 4:
        raise ValueError("肥料参数表必须包含肥料名称、N、P、K四列")
    conn = lianjie()
    inserted = updated = 0
    try:
        for raw in rows[1:]:
            if not raw or raw[0] in (None, ""):
                continue
            name = str(raw[0]).strip()
            values = [float(raw[i] or 0) for i in (1, 2, 3)]
            if any(value < 0 or value > 100 for value in values):
                raise ValueError(f"{name}: N/P/K含量必须在0-100%之间")
            existing = conn.execute("SELECT id FROM feiliao WHERE mingcheng=?", (name,)).fetchone()
            if existing:
                conn.execute("UPDATE feiliao SET dan=?,lin=?,jia=? WHERE id=?", (*values, existing["id"]))
                updated += 1
            else:
                conn.execute("INSERT INTO feiliao(mingcheng,dan,lin,jia) VALUES (?,?,?,?)", (name, *values))
                inserted += 1
        conn.execute(
            "INSERT INTO rizhi(caozuo_shijian,caozuo_leixing,caozuo_neirong,caozuoren) VALUES (datetime('now','localtime'),?,?,?)",
            ("肥料参数导入", f"导入肥料参数：新增{inserted}条，更新{updated}条", "系统用户"),
        )
        conn.commit()
        return {"inserted": inserted, "updated": updated}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print(import_fertilizers())
