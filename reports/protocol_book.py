"""Protocol Book report – Βιβλίο Πρωτοκόλλου."""
from __future__ import annotations
import os
import sys
from datetime import datetime, date
from typing import List, Optional

from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database.models import Protocol
from utils.helpers import format_date_short
from utils.pdf_fonts import register_greek_fonts, FONT_NORMAL, FONT_BOLD
from config.settings import EXPORTS_DIR


def _page_header(canvas, doc, config):
    register_greek_fonts()
    canvas.saveState()
    org = config.get("organization_name", "")
    canvas.setFont(FONT_BOLD, 10)
    canvas.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 1.5 * cm, org)
    canvas.setFont(FONT_NORMAL, 8)
    canvas.drawCentredString(doc.pagesize[0] / 2, doc.pagesize[1] - 2 * cm, "ΒΙΒΛΙΟ ΠΡΩΤΟΚΟΛΛΟΥ")
    canvas.setFont(FONT_NORMAL, 7)
    canvas.drawString(doc.leftMargin, 1.2 * cm,
                      f"Εκτύπωση: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 1.2 * cm, f"Σελίδα {doc.page}")
    canvas.restoreState()


def build_protocol_book(
    protocols: List[Protocol],
    config: dict,
    output_path: str,
    paper_size: str = "A4",
    orientation: str = "landscape",
    year: Optional[int] = None,
    direction: Optional[str] = None,
):
    register_greek_fonts()
    fn = FONT_NORMAL
    fb = FONT_BOLD

    size_map = {"A4": A4, "A3": A3}
    base_size = size_map.get(paper_size.upper(), A4)
    if orientation.lower() == "landscape":
        page_size = landscape(base_size)
    else:
        page_size = base_size

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    org = config.get("organization_name", "")
    story = []

    # Cover
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(org, ParagraphStyle(
        "H", fontSize=16, fontName=fb, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a365d"))))
    story.append(Spacer(1, 0.4 * cm))
    title_parts = ["ΒΙΒΛΙΟ ΠΡΩΤΟΚΟΛΛΟΥ"]
    if year:
        title_parts.append(str(year))
    if direction:
        title_parts.append(direction)
    story.append(Paragraph(" – ".join(title_parts), ParagraphStyle(
        "Title2", fontSize=14, fontName=fb, alignment=TA_CENTER, spaceAfter=10)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a365d")))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        f"Σύνολο εγγράφων: {len(protocols)}",
        ParagraphStyle("Info", fontSize=10, fontName=fn, alignment=TA_CENTER,
                       textColor=colors.grey)
    ))
    story.append(Spacer(1, 0.5 * cm))

    # Table headers
    col_headers = [
        "Α/Α", "Αρ. Πρωτ.", "Ημερομηνία", "Κατεύθυνση",
        "Αποστολέας / Αποδέκτης", "Θέμα", "Κατάσταση", "Χειριστής",
    ]

    is_landscape = orientation.lower() == "landscape"
    if paper_size.upper() == "A3" and is_landscape:
        col_widths = [1.2*cm, 2.5*cm, 2.5*cm, 2.8*cm, 5*cm, 9*cm, 3*cm, 3.5*cm]
    elif is_landscape:
        col_widths = [1*cm, 2.3*cm, 2.3*cm, 2.5*cm, 4.5*cm, 7*cm, 2.8*cm, 3*cm]
    else:
        col_widths = [0.8*cm, 2*cm, 2*cm, 2.2*cm, 4*cm, 5*cm, 2.5*cm, 2.5*cm]

    header_row = [Paragraph(h, ParagraphStyle(
        "TH", fontSize=8, fontName=fb, textColor=colors.white,
        alignment=TA_CENTER)) for h in col_headers]
    table_data = [header_row]

    cell_style = ParagraphStyle("TC",  fontSize=8, leading=10, fontName=fn)
    bold_style = ParagraphStyle("TCB", fontSize=8, leading=10, fontName=fb)

    direction_colors = {
        "ΕΙΣΕΡΧΟΜΕΝΟ": colors.HexColor("#e6fffa"),
        "ΕΞΕΡΧΟΜΕΝΟ":  colors.HexColor("#ebf8ff"),
        "ΕΣΩΤΕΡΙΚΟ":   colors.HexColor("#fffff0"),
    }

    for idx, p in enumerate(protocols, 1):
        sender = ""
        if p.sender_contact:
            sender = p.sender_contact.name
        elif p.sender_employee:
            sender = p.sender_employee.full_name
        if p.recipients:
            names = [r.name for r in p.recipients[:2]]
            if sender:
                sender += " → " + ", ".join(names)
            else:
                sender = "→ " + ", ".join(names)

        row = [
            Paragraph(str(idx), cell_style),
            Paragraph(p.protocol_full or "", bold_style),
            Paragraph(format_date_short(p.protocol_date), cell_style),
            Paragraph(p.direction.value if p.direction else "", cell_style),
            Paragraph(sender, cell_style),
            Paragraph(p.subject or "", cell_style),
            Paragraph(p.status.value if p.status else "", cell_style),
            Paragraph(p.handler.full_name if p.handler else "", cell_style),
        ]
        table_data.append(row)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_bg_cmds = []
    for i in range(1, len(table_data)):
        p_row = protocols[i - 1]
        dir_val = p_row.direction.value if p_row.direction else ""
        bg = direction_colors.get(dir_val, colors.white)
        row_bg_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), colors.HexColor("#1a365d")),
        ("TEXTCOLOR",     (0, 0), (-1,  0), colors.white),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("ALIGN",         (1, 0), (3, -1), "CENTER"),
    ] + row_bg_cmds))

    story.append(t)
    doc.build(story, onFirstPage=lambda c, d: _page_header(c, d, config),
              onLaterPages=lambda c, d: _page_header(c, d, config))


def print_protocol_book(
    protocols: List[Protocol],
    config: dict,
    paper_size: str = "A4",
    orientation: str = "landscape",
    year: Optional[int] = None,
    direction: Optional[str] = None,
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"protocol_book_{ts}.pdf"
    out_path = str(EXPORTS_DIR / filename)
    try:
        build_protocol_book(protocols, config, out_path, paper_size, orientation,
                            year, direction)
        if sys.platform == "win32":
            os.startfile(out_path)
        elif sys.platform == "darwin":
            os.system(f"open '{out_path}'")
        else:
            os.system(f"xdg-open '{out_path}'")
        return out_path
    except Exception as ex:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Σφάλμα εκτύπωσης", str(ex))
        return None
