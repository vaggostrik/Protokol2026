"""Generate and print receipt of protocol acknowledgement."""
from __future__ import annotations
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database.models import Protocol
from utils.helpers import format_date_greek, format_date_short
from utils.pdf_fonts import register_greek_fonts, FONT_NORMAL, FONT_BOLD
from config.settings import EXPORTS_DIR


def _get_styles():
    register_greek_fonts()
    fn  = FONT_NORMAL
    fb  = FONT_BOLD

    title_style = ParagraphStyle(
        "OrgTitle",
        fontName=fb, fontSize=15,
        spaceAfter=4, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a365d"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=fn, fontSize=10,
        spaceAfter=2, alignment=TA_CENTER,
        textColor=colors.HexColor("#4a5568"),
    )
    rec_title_style = ParagraphStyle(
        "RecTitle",
        fontName=fb, fontSize=13,
        spaceAfter=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#2d3748"),
    )
    label_style = ParagraphStyle(
        "Label",
        fontName=fn, fontSize=9,
        textColor=colors.HexColor("#718096"),
    )
    value_style = ParagraphStyle(
        "Value",
        fontName=fb, fontSize=10,
        textColor=colors.HexColor("#1a202c"),
    )
    att_lbl_style = ParagraphStyle(
        "AttLbl",
        fontName=fn, fontSize=9,
        textColor=colors.HexColor("#718096"),
        spaceAfter=4,
    )
    att_item_style = ParagraphStyle(
        "AttItem",
        fontName=fn, fontSize=9,
        leftIndent=12,
        textColor=colors.HexColor("#2d3748"),
    )
    footer_style = ParagraphStyle(
        "Footer",
        fontName=fn, fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )
    proto_num_style = ParagraphStyle(
        "ProtoNum",
        fontName=fb, fontSize=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1a365d"),
    )
    proto_date_style = ParagraphStyle(
        "ProtoDate",
        fontName=fb, fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2d3748"),
    )
    col_hdr_style = ParagraphStyle(
        "ColHdr",
        fontName=fn, fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#718096"),
    )
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "rec_title": rec_title_style,
        "label": label_style,
        "value": value_style,
        "att_lbl": att_lbl_style,
        "att_item": att_item_style,
        "footer": footer_style,
        "proto_num": proto_num_style,
        "proto_date": proto_date_style,
        "col_hdr": col_hdr_style,
    }


def build_receipt_pdf(protocol: Protocol, config: dict, output_path: str):
    """Build a receipt PDF for the given protocol."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )
    st = _get_styles()
    org_name    = config.get("organization_name", "Οργανισμός")
    org_address = config.get("organization_address", "")
    org_phone   = config.get("organization_phone", "")

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph(org_name, st["title"]))
    if org_address:
        story.append(Paragraph(org_address, st["subtitle"]))
    if org_phone:
        story.append(Paragraph(f"Τηλ.: {org_phone}", st["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#1a365d")))
    story.append(Spacer(1, 0.4 * cm))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("ΒΕΒΑΙΩΣΗ ΠΑΡΑΛΑΒΗΣ ΕΓΓΡΑΦΟΥ", st["rec_title"]))

    # ── Protocol number / date box ────────────────────────────────────────────
    proto_table_data = [
        [
            Paragraph("ΑΡΙΘΜΟΣ ΠΡΩΤΟΚΟΛΛΟΥ", st["col_hdr"]),
            Paragraph("ΗΜΕΡΟΜΗΝΙΑ", st["col_hdr"]),
        ],
        [
            Paragraph(protocol.protocol_full or "", st["proto_num"]),
            Paragraph(format_date_greek(protocol.protocol_date), st["proto_date"]),
        ],
    ]
    proto_table = Table(proto_table_data, colWidths=[8 * cm, 7 * cm])
    proto_table.setStyle(TableStyle([
        ("BOX",         (0, 0), (-1, -1), 1.5, colors.HexColor("#2b6cb0")),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND",  (0, 0), (-1,  0), colors.HexColor("#ebf4ff")),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(proto_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Details ───────────────────────────────────────────────────────────────
    p = protocol
    direction_label = p.direction.value if p.direction else ""
    priority_label  = p.priority.value  if p.priority  else ""
    status_label    = p.status.value    if p.status    else ""
    sender = ""
    if p.sender_contact:
        sender = p.sender_contact.display_name
    elif p.sender_employee:
        sender = p.sender_employee.full_name

    details = [
        ("Κατεύθυνση:",   direction_label),
        ("Αποστολέας:",   sender),
        ("Θέμα:",         p.subject or ""),
        ("Προτεραιότητα:", priority_label),
        ("Κατάσταση:",    status_label),
        ("Τμήμα:",        p.department.name if p.department else ""),
        ("Χειριστής:",    p.handler.full_name if p.handler else ""),
    ]
    if p.ext_protocol_number:
        details.append(("Αρ. Πρωτ. Αποστολέα:", p.ext_protocol_number))
    if p.deadline_date:
        details.append(("Προθεσμία:", format_date_short(p.deadline_date)))
    if p.summary:
        details.append(("Περίληψη:", p.summary))

    table_data = [
        [Paragraph(lbl, st["label"]), Paragraph(str(val), st["value"])]
        for lbl, val in details
    ]
    det_table = Table(table_data, colWidths=[4.5 * cm, 10.5 * cm])
    det_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.8 * cm))

    # ── Attachments ───────────────────────────────────────────────────────────
    if p.attachments:
        story.append(Paragraph("Συνημμένα αρχεία:", st["att_lbl"]))
        for att in p.attachments:
            name = att.original_filename if hasattr(att, "original_filename") else None
            name = name or (att.filename if hasattr(att, "filename") else str(att.file_path or ""))
            story.append(Paragraph(f"•  {name}", st["att_item"]))
        story.append(Spacer(1, 0.3 * cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Εκτυπώθηκε: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  {org_name}",
        st["footer"]
    ))

    doc.build(story)


def print_receipt(protocol: Protocol, config: dict):
    """Build PDF and open it for printing."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_num = (protocol.protocol_full or str(protocol.protocol_number or "x")
                ).replace("/", "_").replace("\\", "_")
    filename = f"receipt_{safe_num}_{ts}.pdf"
    out_path = str(EXPORTS_DIR / filename)
    try:
        build_receipt_pdf(protocol, config, out_path)
        if sys.platform == "win32":
            os.startfile(out_path)
        elif sys.platform == "darwin":
            os.system(f"open '{out_path}'")
        else:
            os.system(f"xdg-open '{out_path}'")
    except Exception as ex:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Σφάλμα εκτύπωσης", str(ex))
