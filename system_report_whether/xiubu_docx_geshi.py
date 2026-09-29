from __future__ import annotations

import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
WORKSPACE = Path.cwd()
DOCX = WORKSPACE / "调研报告_填充排版完成版.docx"
TEMP = WORKSPACE / "调研报告_格式修正.tmp.docx"

ET.register_namespace("w", W)


def q(local: str) -> str:
    return f"{{{W}}}{local}"


def ensure_run_fonts(run: ET.Element) -> None:
    rpr = run.find(q("rPr"))
    if rpr is None:
        rpr = ET.Element(q("rPr"))
        run.insert(0, rpr)
    rfonts = rpr.find(q("rFonts"))
    if rfonts is None:
        rfonts = ET.Element(q("rFonts"))
        rpr.insert(0, rfonts)
    rfonts.set(q("ascii"), "Times New Roman")
    rfonts.set(q("hAnsi"), "Times New Roman")
    rfonts.set(q("eastAsia"), "宋体")
    rfonts.set(q("cs"), "Times New Roman")


def ensure_paragraph_spacing(paragraph: ET.Element) -> None:
    ppr = paragraph.find(q("pPr"))
    if ppr is None:
        ppr = ET.Element(q("pPr"))
        paragraph.insert(0, ppr)
    spacing = ppr.find(q("spacing"))
    if spacing is None:
        spacing = ET.Element(q("spacing"))
        ppr.append(spacing)
    spacing.set(q("line"), "360")
    spacing.set(q("lineRule"), "auto")


def patch() -> None:
    if TEMP.exists():
        TEMP.unlink()
    with zipfile.ZipFile(DOCX, "r") as src, zipfile.ZipFile(
        TEMP, "w", compression=zipfile.ZIP_DEFLATED
    ) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                # ElementTree may rename namespace prefixes. The original
                # mc:Ignorable value lists literal prefixes, so remove that
                # stale declaration after reserialization.
                root.attrib.pop(f"{{{MC}}}Ignorable", None)
                for p in root.iter(q("p")):
                    ensure_paragraph_spacing(p)
                for r in root.iter(q("r")):
                    ensure_run_fonts(r)
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            dst.writestr(item, data)
    shutil.move(TEMP, DOCX)


if __name__ == "__main__":
    patch()
    print(DOCX)
    print(f"bytes={DOCX.stat().st_size}")
