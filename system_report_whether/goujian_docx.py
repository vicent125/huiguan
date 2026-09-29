from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


WORKSPACE = Path.cwd()
SOURCE = WORKSPACE / "report_source.md"
TEMPLATE = Path(r"C:\Users\D1782\Desktop\调研报告.docx")
OUTPUT = WORKSPACE / "调研报告_填充排版完成版.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

ET.register_namespace("w", W)
ET.register_namespace("r", R)


def attr(name: str, value: str) -> str:
    return f' w:{name}="{escape(value)}"'


def fonts(size_half_points: int, bold: bool = False) -> str:
    bold_xml = "<w:b/><w:bCs/>" if bold else ""
    return (
        "<w:rPr>"
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
        'w:eastAsia="宋体" w:cs="Times New Roman"/>'
        f"{bold_xml}<w:sz w:val=\"{size_half_points}\"/>"
        f"<w:szCs w:val=\"{size_half_points}\"/>"
        '<w:lang w:val="en-US" w:eastAsia="zh-CN"/>'
        "</w:rPr>"
    )


def run(text: str, size: int = 24, bold: bool = False) -> str:
    preserve = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f"<w:r>{fonts(size, bold)}<w:t{preserve}>{escape(text)}</w:t></w:r>"


def paragraph(
    text: str,
    *,
    kind: str = "body",
    section: str | None = None,
) -> str:
    ppr: list[str] = []
    size = 24
    bold = False

    if kind in {"title", "subtitle", "cover", "toc_title"}:
        ppr.append('<w:jc w:val="center"/>')
    elif kind in {"body", "keywords", "reference", "appendix"}:
        ppr.append('<w:jc w:val="both"/>')
    else:
        ppr.append('<w:jc w:val="left"/>')

    if kind == "title":
        size, bold = 32, True
        ppr.append('<w:spacing w:after="160" w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:keepNext/>')
    elif kind == "subtitle":
        size, bold = 32, True
        ppr.append('<w:spacing w:after="120" w:line="360" w:lineRule="auto"/>')
    elif kind == "cover":
        size = 28
        ppr.append('<w:spacing w:after="160" w:line="360" w:lineRule="auto"/>')
    elif kind == "toc_title":
        size, bold = 32, True
        ppr.append('<w:spacing w:after="240" w:line="360" w:lineRule="auto"/>')
    elif kind == "heading1":
        size, bold = 28, True
        ppr.append('<w:spacing w:before="240" w:after="120" w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:keepNext/><w:keepLines/><w:outlineLvl w:val="0"/>')
    elif kind == "heading2":
        size, bold = 24, True
        ppr.append('<w:spacing w:before="120" w:after="60" w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:keepNext/><w:keepLines/><w:outlineLvl w:val="1"/>')
    elif kind == "reference":
        size = 21
        ppr.append('<w:spacing w:after="60" w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:ind w:left="480" w:hanging="480"/>')
    elif kind == "appendix":
        ppr.append('<w:spacing w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:ind w:left="480" w:hanging="480"/>')
    elif kind == "keywords":
        ppr.append('<w:spacing w:line="360" w:lineRule="auto"/>')
    else:
        ppr.append('<w:spacing w:line="360" w:lineRule="auto"/>')
        ppr.append('<w:ind w:firstLine="480" w:firstLineChars="200"/>')
        ppr.append('<w:widowControl/>')

    if section:
        ppr.append(section)

    if kind == "keywords" and text.startswith("关键词："):
        body = run("关键词：", size, True) + run(text[4:], size, False)
    else:
        body = run(text, size, bold)

    return f"<w:p><w:pPr>{''.join(ppr)}</w:pPr>{body}</w:p>"


def blank_cover_line() -> str:
    return paragraph("　", kind="cover")


def page_setup(footer_id: str | None = None, number_style: str | None = None) -> str:
    footer = f'<w:footerReference w:type="default" r:id="{footer_id}"/>' if footer_id else ""
    num = ""
    if number_style:
        num = f'<w:pgNumType w:fmt="{number_style}" w:start="1"/>'
    return (
        "<w:sectPr>"
        f"{footer}<w:type w:val=\"nextPage\"/>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1800" '
        'w:header="720" w:footer="720" w:gutter="0"/>'
        f"{num}<w:cols w:space=\"425\"/><w:docGrid w:linePitch=\"312\"/>"
        "</w:sectPr>"
    )


def toc_field() -> str:
    return (
        '<w:p><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr>'
        '<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f'{run("打开文档后更新目录", 24, False)}'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    )


def footer_xml(number_style: str) -> str:
    del number_style
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W}" xmlns:r="{R}">'
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        f'{run("", 21, False)}'
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        '</w:p></w:ftr>'
    )


def build_document_xml() -> str:
    body: list[str] = []
    body.append(paragraph("行走于青衣江与大巴山之间", kind="title"))
    body.append(paragraph("——雅安市雨城区、巴中南龛与通江王坪烈士陵园调研报告", kind="subtitle"))
    body.extend(blank_cover_line() for _ in range(6))
    for text in [
        "学校：四川农业大学",
        "学院：水利水电学院",
        "专业：____________________",
        "班级：____________________",
        "姓名：____________________",
        "学号：____________________",
        "指导教师：________________",
    ]:
        body.append(paragraph(text, kind="cover"))
    body.extend(blank_cover_line() for _ in range(2))
    body.append(paragraph("完成时间：2026年7月", kind="cover"))
    body.append(
        paragraph(
            "正文字数：约1.31万字（不含参考文献与附录）",
            kind="cover",
            section=page_setup(),
        )
    )

    body.append(paragraph("目录", kind="toc_title"))
    body.append(toc_field())
    body.append(paragraph("", kind="body", section=page_setup("rIdFooter1", "lowerRoman")))

    in_references = False
    in_appendix = False
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        if text.startswith("# "):
            continue
        if text.startswith("## "):
            heading = text[3:]
            in_references = heading == "参考文献"
            in_appendix = heading.startswith("附录")
            body.append(paragraph(heading, kind="heading1"))
        elif text.startswith("### "):
            body.append(paragraph(text[4:], kind="heading2"))
        elif in_references and text.startswith("["):
            body.append(paragraph(text, kind="reference"))
        elif in_appendix and re.match(r"^\d+\.", text):
            body.append(paragraph(text, kind="appendix"))
        elif text.startswith("关键词："):
            body.append(paragraph(text, kind="keywords"))
        else:
            body.append(paragraph(text, kind="body"))

    body.append(page_setup("rIdFooter2", "decimal"))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'
        + "".join(body)
        + "</w:body></w:document>"
    )


def update_relationships(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)
    for rel_id, target in [("rIdFooter1", "footer1.xml"), ("rIdFooter2", "footer2.xml")]:
        node = ET.SubElement(root, f"{{{REL}}}Relationship")
        node.set("Id", rel_id)
        node.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer")
        node.set("Target", target)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def update_content_types(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)
    existing = {node.get("PartName") for node in root.findall(f"{{{CT}}}Override")}
    for name in ["/word/footer1.xml", "/word/footer2.xml"]:
        if name not in existing:
            node = ET.SubElement(root, f"{{{CT}}}Override")
            node.set("PartName", name)
            node.set(
                "ContentType",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
            )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def update_settings(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)
    if root.find(f"{{{W}}}updateFields") is None:
        node = ET.SubElement(root, f"{{{W}}}updateFields")
        node.set(f"{{{W}}}val", "true")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_package() -> None:
    temp = OUTPUT.with_suffix(".tmp.docx")
    if temp.exists():
        temp.unlink()

    document_xml = build_document_xml().encode("utf-8")
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    ).encode("utf-8")
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
        '<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
        '<Relationship Id="rIdFooter2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer2.xml"/>'
        '</Relationships>'
    ).encode("utf-8")
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '</Types>'
    ).encode("utf-8")
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>'
        '</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
        '</w:styles>'
    ).encode("utf-8")
    settings = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:settings xmlns:w="{W}"><w:updateFields w:val="true"/></w:settings>'
    ).encode("utf-8")
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        dst.writestr("[Content_Types].xml", content_types)
        dst.writestr("_rels/.rels", root_rels)
        dst.writestr("word/document.xml", document_xml)
        dst.writestr("word/_rels/document.xml.rels", document_rels)
        dst.writestr("word/styles.xml", styles)
        dst.writestr("word/settings.xml", settings)
        dst.writestr("word/footer1.xml", footer_xml("lowerRoman").encode("utf-8"))
        dst.writestr("word/footer2.xml", footer_xml("decimal").encode("utf-8"))

    with zipfile.ZipFile(temp, "r") as check:
        for name in check.namelist():
            if name.endswith(".xml") or name.endswith(".rels"):
                ET.fromstring(check.read(name))

    shutil.move(temp, OUTPUT)


if __name__ == "__main__":
    build_package()
    print(OUTPUT)
    print(f"bytes={OUTPUT.stat().st_size}")
