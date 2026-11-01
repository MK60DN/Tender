from __future__ import annotations

import html
import io
import re
import shutil
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, ListFlowable, ListItem,
    LongTable, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Preformatted,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
TMP = ROOT / "tmp" / "manuals_v22"
OUTPUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

FONT_REG = "TenderSimSun"
FONT_BOLD = "TenderSimHei"
pdfmetrics.registerFont(TTFont(FONT_REG, r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont(FONT_BOLD, r"C:\Windows\Fonts\simhei.ttf"))

BLUE = colors.HexColor("#245779")
GREEN = colors.HexColor("#327764")
GOLD = colors.HexColor("#A77B2E")
LIGHT_BLUE = colors.HexColor("#EEF4F8")
LIGHT_GREEN = colors.HexColor("#EDF6F1")
LIGHT_GRAY = colors.HexColor("#F5F7F8")
TEXT = colors.HexColor("#202629")
MUTED = colors.HexColor("#667177")
RULE = colors.HexColor("#D5DDE1")

BODY_STYLE = ParagraphStyle(
    "BodyCN", fontName=FONT_REG, fontSize=10.2, leading=17.2, textColor=TEXT,
    firstLineIndent=18, spaceAfter=7, wordWrap="CJK", alignment=TA_LEFT,
)
BODY_NO_INDENT = ParagraphStyle("BodyNoIndent", parent=BODY_STYLE, firstLineIndent=0)
H1_STYLE = ParagraphStyle("H1", fontName=FONT_BOLD, fontSize=20, leading=27, textColor=BLUE, spaceAfter=14, wordWrap="CJK")
H2_STYLE = ParagraphStyle("H2", fontName=FONT_BOLD, fontSize=14.5, leading=21, textColor=BLUE, spaceBefore=16, spaceAfter=8, wordWrap="CJK", keepWithNext=True)
H3_STYLE = ParagraphStyle("H3", fontName=FONT_BOLD, fontSize=11.8, leading=18, textColor=GREEN, spaceBefore=10, spaceAfter=5, wordWrap="CJK", keepWithNext=True)
QUOTE_STYLE = ParagraphStyle("Quote", parent=BODY_NO_INDENT, leftIndent=15, rightIndent=8, borderColor=GOLD, borderWidth=0.8, borderPadding=8, backColor=colors.HexColor("#FCF8EE"), spaceBefore=4, spaceAfter=9)
CODE_STYLE = ParagraphStyle("Code", fontName=FONT_REG, fontSize=8.2, leading=12, textColor=colors.HexColor("#263238"), backColor=LIGHT_GRAY, borderColor=RULE, borderWidth=0.5, borderPadding=7, leftIndent=6, rightIndent=6, spaceBefore=5, spaceAfter=8, wordWrap="CJK")
TABLE_STYLE = ParagraphStyle("Table", fontName=FONT_REG, fontSize=8.3, leading=12.2, textColor=TEXT, wordWrap="CJK")
TABLE_HEAD_STYLE = ParagraphStyle("TableHead", parent=TABLE_STYLE, fontName=FONT_BOLD, textColor=BLUE)
CAPTION_STYLE = ParagraphStyle("Caption", fontName=FONT_REG, fontSize=8.5, leading=13, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10)


def inline_markup(text: str) -> str:
    value = html.escape(str(text or ""), quote=False)
    value = re.sub(r"`([^`]+)`", lambda m: f'<font color="#245779">{html.escape(m.group(1))}</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#245779">\1</link>', value)
    return value


def strip_markdown(text: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text or ""))
    value = value.replace("**", "").replace("`", "")
    return value.strip()


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return lines[index].strip().startswith("|") and bool(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[index + 1]))


def _table_cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def parse_blocks(markdown: str) -> list[tuple]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[tuple] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            blocks.append(("code", language, "\n".join(code_lines)))
            continue
        if _is_table_start(lines, index):
            rows = [_table_cells(line)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(_table_cells(lines[index]))
                index += 1
            blocks.append(("table", rows))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            blocks.append(("heading", len(heading.group(1)), heading.group(2).strip()))
            index += 1
            continue
        if stripped.startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            blocks.append(("quote", " ".join(quote_lines)))
            continue
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^[-*]\s+", lines[index].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[index].strip()))
                index += 1
            blocks.append(("bullet", items))
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s+", lines[index].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[index].strip()))
                index += 1
            blocks.append(("numbered", items))
            continue
        if stripped in {"---", "***", "___"}:
            blocks.append(("rule",))
            index += 1
            continue
        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("#", "```", ">", "|", "- ", "* ")) or re.match(r"^\d+\.\s+", candidate) or candidate in {"---", "***", "___"}:
                break
            paragraph.append(candidate)
            index += 1
        blocks.append(("paragraph", " ".join(paragraph)))
    return blocks


def _table_flowable(rows: list[list[str]]) -> LongTable:
    if not rows:
        return LongTable([[""]])
    columns = max(len(row) for row in rows)
    normalized = [row + [""] * (columns - len(row)) for row in rows]
    available = A4[0] - 40 * mm
    first_width = min(available * 0.26, 58 * mm) if columns > 1 else available
    rest = (available - first_width) / max(1, columns - 1) if columns > 1 else available
    widths = [first_width] + [rest] * (columns - 1)
    data = [[Paragraph(inline_markup(cell), TABLE_HEAD_STYLE if row_index == 0 else TABLE_STYLE) for cell in row] for row_index, row in enumerate(normalized)]
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLUE),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _list_flowable(items: list[str], numbered: bool = False) -> ListFlowable:
    bullet_type = "1" if numbered else "bullet"
    return ListFlowable(
        [ListItem(Paragraph(inline_markup(item), BODY_NO_INDENT), leftIndent=14) for item in items],
        bulletType=bullet_type,
        start=1 if numbered else None,
        leftIndent=14,
        bulletFontName=FONT_REG,
        bulletFontSize=8.5,
        spaceAfter=6,
    )


def blocks_to_story(blocks: list[tuple]) -> list:
    story: list = []
    for block in blocks:
        kind = block[0]
        if kind == "heading":
            level, text = block[1], block[2]
            style = H1_STYLE if level == 1 else H2_STYLE if level == 2 else H3_STYLE
            story.append(KeepTogether([Paragraph(inline_markup(text), style), HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=5)]))
        elif kind == "paragraph":
            story.append(Paragraph(inline_markup(block[1]), BODY_STYLE))
        elif kind == "quote":
            story.append(Paragraph(inline_markup(block[1]), QUOTE_STYLE))
        elif kind in {"bullet", "numbered"}:
            story.append(_list_flowable(block[1], numbered=kind == "numbered"))
        elif kind == "code":
            code = block[2]
            wrapped = []
            for line in code.splitlines() or [""]:
                while len(line) > 100:
                    wrapped.append(line[:100])
                    line = line[100:]
                wrapped.append(line)
            story.append(Preformatted("\n".join(wrapped), CODE_STYLE, maxLineLength=100))
        elif kind == "table":
            story.append(Spacer(1, 3))
            story.append(_table_flowable(block[1]))
            story.append(Spacer(1, 8))
        elif kind == "rule":
            story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=6, spaceAfter=8))
    return story


class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, *, title: str, version: str, **kwargs):
        self.book_title = title
        self.book_version = version
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=21 * mm,
            bottomMargin=19 * mm,
            title=title,
            author="Tender Research Group",
            subject=version,
            **kwargs,
        )
        cover_frame = Frame(20 * mm, 20 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="cover-frame")
        main_frame = Frame(20 * mm, 19 * mm, A4[0] - 40 * mm, A4[1] - 40 * mm, id="main-frame")
        self.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=self._cover_page),
            PageTemplate(id="Main", frames=[main_frame], onPage=self._main_page),
        ])

    def _cover_page(self, canv: canvas.Canvas, doc) -> None:
        width, height = A4
        canv.saveState()
        canv.setFillColor(colors.HexColor("#F4F8FA"))
        canv.rect(0, 0, width, height, stroke=0, fill=1)
        canv.setFillColor(BLUE)
        canv.rect(0, height - 18 * mm, width, 18 * mm, stroke=0, fill=1)
        canv.setFillColor(GOLD)
        canv.rect(20 * mm, 46 * mm, 46 * mm, 2.2 * mm, stroke=0, fill=1)
        canv.restoreState()

    def _main_page(self, canv: canvas.Canvas, doc) -> None:
        width, height = A4
        canv.saveState()
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(20 * mm, height - 15 * mm, width - 20 * mm, height - 15 * mm)
        canv.setFont(FONT_REG, 7.6)
        canv.setFillColor(MUTED)
        canv.drawString(20 * mm, height - 12.5 * mm, self.book_title)
        canv.drawRightString(width - 20 * mm, height - 12.5 * mm, self.book_version)
        canv.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
        canv.drawString(20 * mm, 9.5 * mm, "Tender Research Group · 2026-11-01")
        canv.drawRightString(width - 20 * mm, 9.5 * mm, f"{doc.page}")
        canv.restoreState()


def cover_story(title: str, subtitle: str, version: str, date_text: str, summary: str) -> list:
    return [
        Spacer(1, 62 * mm),
        Paragraph(inline_markup(title), ParagraphStyle("CoverTitle", fontName=FONT_BOLD, fontSize=27, leading=38, textColor=BLUE, wordWrap="CJK")),
        Spacer(1, 6 * mm),
        Paragraph(inline_markup(subtitle), ParagraphStyle("CoverSub", fontName=FONT_REG, fontSize=15, leading=24, textColor=GREEN, wordWrap="CJK")),
        Spacer(1, 16 * mm),
        Paragraph(inline_markup(summary), ParagraphStyle("CoverSummary", fontName=FONT_REG, fontSize=10.5, leading=18, textColor=TEXT, wordWrap="CJK")),
        Spacer(1, 24 * mm),
        Paragraph(f"版本 {inline_markup(version)}　|　{inline_markup(date_text)}　|　Tender Research Group", ParagraphStyle("CoverMeta", fontName=FONT_REG, fontSize=10, leading=16, textColor=MUTED)),
        NextPageTemplate("Main"),
        PageBreak(),
    ]


def build_markdown_pdf(source: Path, target: Path, *, title: str, subtitle: str, version: str, date_text: str, summary: str, include_toc: bool = True) -> int:
    blocks = parse_blocks(source.read_text(encoding="utf-8"))
    # The source contains its own top title; keep it in body only for complete manuals.
    story = cover_story(title, subtitle, version, date_text, summary)
    if include_toc:
        headings = [text for kind, level, text in [b for b in blocks if b[0] == "heading"] if level == 2]
        toc_items = [Paragraph("目录", H1_STYLE)]
        toc_items.extend(Paragraph(f"{idx:02d}　{inline_markup(text)}", BODY_NO_INDENT) for idx, text in enumerate(headings, 1))
        story.extend(toc_items)
        story.append(PageBreak())
    story.extend(blocks_to_story(blocks))
    doc = BookDocTemplate(str(target), title=title, version=version)
    doc.build(story)
    return len(PdfReader(str(target)).pages)

def _set_docx_style_font(style, name: str, size: float | None = None, bold: bool | None = None) -> None:
    style.font.name = name
    if size is not None:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", "Microsoft YaHei")


def append_markdown_to_docx(doc: Document, markdown: str, *, skip_first_h1: bool = False) -> None:
    blocks = parse_blocks(markdown)
    skipped_h1 = False
    for block in blocks:
        kind = block[0]
        if kind == "heading":
            level, text = block[1], strip_markdown(block[2])
            if skip_first_h1 and level == 1 and not skipped_h1:
                skipped_h1 = True
                continue
            doc.add_heading(text, level=min(level, 3))
        elif kind == "paragraph":
            paragraph = doc.add_paragraph(strip_markdown(block[1]))
            paragraph.paragraph_format.first_line_indent = Cm(0.74)
            paragraph.paragraph_format.space_after = Pt(5)
        elif kind == "quote":
            paragraph = doc.add_paragraph(strip_markdown(block[1]))
            paragraph.style = doc.styles["Intense Quote"]
        elif kind == "bullet":
            for item in block[1]:
                doc.add_paragraph(strip_markdown(item), style="List Bullet")
        elif kind == "numbered":
            for item in block[1]:
                doc.add_paragraph(strip_markdown(item), style="List Number")
        elif kind == "code":
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(block[2])
            run.font.name = "Consolas"
            run.font.size = Pt(8)
            paragraph.paragraph_format.left_indent = Cm(0.4)
            paragraph.paragraph_format.space_after = Pt(7)
        elif kind == "table":
            rows = block[1]
            if not rows:
                continue
            columns = max(len(row) for row in rows)
            table = doc.add_table(rows=0, cols=columns)
            table.style = "Table Grid"
            for row_index, row in enumerate(rows):
                cells = table.add_row().cells
                for index in range(columns):
                    value = row[index] if index < len(row) else ""
                    cells[index].text = strip_markdown(value)
                    for paragraph in cells[index].paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(8.5)
                            if row_index == 0:
                                run.bold = True
            doc.add_paragraph()
        elif kind == "rule":
            doc.add_paragraph("")


def write_markdown_docx(source: Path, target: Path, *, title: str, subtitle: str, version: str, date_text: str, summary: str) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.1)
    section.bottom_margin = Cm(1.9)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    _set_docx_style_font(normal, "Microsoft YaHei", 10.5)
    for style_name, size, color in [("Title", 26, BLUE), ("Heading 1", 18, BLUE), ("Heading 2", 14, BLUE), ("Heading 3", 12, GREEN)]:
        style = doc.styles[style_name]
        _set_docx_style_font(style, "Microsoft YaHei", size, True)
        try:
            style.font.color.rgb = RGBColor(color.red * 255, color.green * 255, color.blue * 255)
        except Exception:
            pass
    paragraph = doc.add_paragraph(style="Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(title)
    subtitle_p = doc.add_paragraph(subtitle)
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_p.runs[0].font.size = Pt(14)
    meta = doc.add_paragraph(f"版本 {version}　|　{date_text}　|　Tender Research Group")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    append_markdown_to_docx(doc, source.read_text(encoding="utf-8"), skip_first_h1=True)
    doc.core_properties.title = title
    doc.core_properties.subject = version
    doc.core_properties.author = "Tender Research Group"
    doc.save(target)


def _stamp_page(page, version: str):
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    buffer = io.BytesIO()
    canv = canvas.Canvas(buffer, pagesize=(width, height))
    canv.setFont(FONT_REG, 7.2)
    canv.setFillColor(colors.HexColor("#6A7479"))
    canv.drawRightString(width - 28, 11, f"Tender · {version} · 2026-11-01")
    canv.save()
    buffer.seek(0)
    stamp = PdfReader(buffer).pages[0]
    page.merge_page(stamp)
    return page


def merge_source_with_addendum(source_pdf: Path, addendum_pdf: Path, target: Path, *, title: str, version: str) -> int:
    source = PdfReader(str(source_pdf))
    addendum = PdfReader(str(addendum_pdf))
    writer = PdfWriter()
    writer.add_page(addendum.pages[0])
    writer.add_outline_item("版本封面", 0)
    body_start = len(writer.pages)
    for page in source.pages:
        writer.add_page(_stamp_page(page, version))
    writer.add_outline_item("继承的基础正文", body_start)
    appendix_start = len(writer.pages)
    for page in addendum.pages[1:]:
        writer.add_page(page)
    writer.add_outline_item("新版增补章", appendix_start)
    writer.add_metadata({"/Title": title, "/Author": "Tender Research Group", "/Subject": version})
    with target.open("wb") as handle:
        writer.write(handle)
    return len(PdfReader(str(target)).pages)


def update_whitepaper_docx(source: Path, addendum_md: Path, target: Path) -> int:
    doc = Document(source)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.text = run.text.replace("V2.1", "V2.2").replace("Version 1.8", "Version 2.2")
    doc.add_page_break()
    append_markdown_to_docx(doc, addendum_md.read_text(encoding="utf-8"), skip_first_h1=False)
    doc.core_properties.title = "Tender 项目白皮书 V2.2"
    doc.core_properties.subject = "预测加工、心智化、世界树与多模态有限观测"
    doc.core_properties.author = "Tender Research Group"
    doc.save(target)
    return len(Document(target).paragraphs)


def main() -> None:
    product_src = ROOT / "docs/product/Tender-Product-Manual-v7.2.md"
    user_src = ROOT / "docs/product/Tender-User-Guide-v7.2.md"
    white_src = ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.tex"
    teach_src = ROOT / "docs/teaching/Tender-Teaching-Manual-v6.2.tex"
    white_add = ROOT / "docs/manual_sources/whitepaper_addendum.md"
    teach_add = ROOT / "docs/manual_sources/teaching_addendum.md"

    product_pdf = ROOT / "docs/product/Tender-Product-Manual-v7.2.pdf"
    user_pdf = ROOT / "docs/product/Tender-User-Guide-v7.2.pdf"
    white_pdf = ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.pdf"
    teach_pdf = ROOT / "docs/teaching/Tender-Teaching-Manual-v6.2.pdf"
    product_docx = ROOT / "docs/product/Tender-Product-Manual-v7.2.docx"
    user_docx = ROOT / "docs/product/Tender-User-Guide-v7.2.docx"
    white_docx = ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.docx"

    p_pages = build_markdown_pdf(
        product_src, product_pdf,
        title="Tender 产品手册 V7.2",
        subtitle="连接自我、世界与他人心智的环境型多 Agent 学习系统",
        version="V7.2", date_text="2026-11-01",
        summary="本版在既有产品架构上加入界面上下文 MCP、多媒体插件、本地隐私边界与新的验收规格，继续保持日常入口只有弹幕和底部对话条。",
    )
    u_pages = build_markdown_pdf(
        user_src, user_pdf,
        title="Tender 用户手册 V7.2",
        subtitle="首次启用、桌面弹幕、多媒体与隐私控制",
        version="V7.2", date_text="2026-11-01",
        summary="本版说明如何逐次授权界面读取、如何处理图片音频视频，以及哪些内容不会进入长期事件库。",
    )
    white_add_pdf = TMP / "whitepaper_addendum.pdf"
    teach_add_pdf = TMP / "teaching_addendum.pdf"
    w_add_pages = build_markdown_pdf(
        white_add, white_add_pdf,
        title="Tender 项目白皮书 V2.2 增补章",
        subtitle="多模态有限观测、MCP 工具层与证据边界",
        version="V2.2", date_text="2026-11-01",
        summary="本增补章在 V2.1 理论基础上加入界面上下文与本地媒体插件，并明确原始内容、派生信号与主观解释之间的分账。",
        include_toc=False,
    )
    t_add_pages = build_markdown_pdf(
        teach_add, teach_add_pdf,
        title="Tender 零基础教学手册 V6.2 增补章",
        subtitle="界面上下文、多媒体插件与本地 MCP 工程实现",
        version="V6.2", date_text="2026-11-01",
        summary="本增补章给出组件图、权限链路、依赖安装、MCP 配置、安全不变量与验收步骤。",
        include_toc=False,
    )
    w_pages = merge_source_with_addendum(
        ROOT / "docs/archive/Tender-Whitepaper-v2.1-base.pdf", white_add_pdf, white_pdf,
        title="Tender 项目白皮书 V2.2", version="V2.2",
    )
    t_pages = merge_source_with_addendum(
        ROOT / "docs/archive/Tender-Teaching-Manual-v6.1-base.pdf", teach_add_pdf, teach_pdf,
        title="Tender 零基础教学手册 V6.2", version="V6.2",
    )
    write_markdown_docx(product_src, product_docx, title="Tender 产品手册 V7.2", subtitle="连接自我、世界与他人心智的环境型多 Agent 学习系统", version="V7.2", date_text="2026-11-01", summary="")
    write_markdown_docx(user_src, user_docx, title="Tender 用户手册 V7.2", subtitle="首次启用、桌面弹幕、多媒体与隐私控制", version="V7.2", date_text="2026-11-01", summary="")
    update_whitepaper_docx(ROOT / "docs/archive/Tender-Whitepaper-v2.1-base.docx", white_add, white_docx)
    print(f"product_pages={p_pages}")
    print(f"user_pages={u_pages}")
    print(f"whitepaper_pages={w_pages} addendum_pages={w_add_pages}")
    print(f"teaching_pages={t_pages} addendum_pages={t_add_pages}")


if __name__ == "__main__":
    main()


