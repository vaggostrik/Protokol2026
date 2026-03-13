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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database.models import Protocol
from utils.helpers import format_date_greek, format_date_short
from config.settings import EXPORTS_DIR


def _get_styles(config: dict):
    styles = getSampleStyleSheet()
    org = config.get("organization_name", "Οργανισμός")

    title_style = ParagraphStyle(
        "OrgTitle", parent=styles["Title"],
        fontSize=14, spaceAfter=4, alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, spaceAfter=2, alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey,
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
    )
    subject_style = ParagraphStyle(
        "Subject", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold", spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, alignment=TA_CENTER, textColor=colors.grey,
    )
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "label": label_style,
        "value": value_style,
        "subject": subject_style,
        "footer": footer_style,
        "normal": styles["Normal"],
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
    styles = _get_styles(config)
    org_name = config.get("organization_name", "Οργανισμός")
    org_address = config.get("organization_address", "")
    org_phone = config.get("organization_phone", "")

    story = []

    # Header
    story.append(Paragraph(org_name, styles["title"]))
    if org_address:
        story.append(Paragraph(org_address, styles["subtitle"]))
    if org_phone:
        story.append(Paragraph(f"Τηλ.: {org_phone}", styles["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a365d")))
    story.append(Spacer(1, 0.3 * cm))

    # Title
    story.append(Paragraph(
        "ΒΕΒΑΙΩΣΗ ΠΑΡΑΛΑΒΗΣ ΕΓΓΡΑΦΟΥ",
        ParagraphStyle("RecTitle", fontSize=13, fontName="Helvetica-Bold",
                       alignment=TA_CENTER, spaceAfter=10),
    ))

    # Protocol number box
    proto_table_data = [
        [
            Paragraph("ΑΡΙΘΜΟΣ ΠΡΩΤΟΚΟΛΛΟΥ", ParagraphStyle(
                "PN_lbl", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)),
            Paragraph("ΗΜΕΡΟΜΗΝΙΑ", ParagraphStyle(
                "D_lbl", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)),
        ],
        [
            Paragraph(protocol.protocol_full or "", ParagraphStyle(
                "PN_val", fontSize=22, fontName="Helvetica-Bold", alignment=TA_CENTER,
                textColor=colors.HexColor("#1a365d"))),
            Paragraph(format_date_greek(protocol.protocol_date), ParagraphStyle(
                "D_val", fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER)),
        ],
    ]
    proto_table = Table(proto_table_data, colWidths=[8 * cm, 7 * cm])
    proto_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#2b6cb0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ebf4ff")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(proto_table)
    story.append(Spacer(1, 0.5 * cm))

    # Details table
    p = protocol
    direction_label = p.direction.value if p.direction else ""
    priority_label = p.priority.value if p.priority else ""
    status_label = p.status.value if p.status else ""
    sender = ""
    if p.sender_contact:
        sender = p.sender_contact.display_name
    elif p.sender_employee:
        sender = p.sender_employee.full_name

    details = [
        ["Κατεύθυνση:", direction_label],
        ["Αποστολέας:", sender],
        ["Θέμα:", p.subject or ""],
        ["Προτεραιότητα:", priority_label],
        ["Κατάσταση:", status_label],
        ["Τμήμα:", p.department.name if p.department else ""],
        ["Χειριστής:", p.handler.full_name if p.handler else ""],
    ]
    if p.ext_protocol_number:
        details.append(["Αρ. Πρωτ. Αποστολέα:", p.ext_protocol_number])
    if p.deadline_date:
        details.append(["Προθεσμία:", format_date_short(p.deadline_date)])
    if p.summary:
        details.append(["Περίληψη:", p.summary])

    table_data = [[
        Paragraph(row[0], styles["label"]),
        Paragraph(str(row[1]), styles["value"])
    ] for row in details]

    det_table = Table(table_data, colWidths=[5 * cm, 10 * cm])
    det_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.lightgrey),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.8 * cm))

    # Attachments
    if p.attachments:
        story.append(Paragraph("Συνημμένα αρχεία:", ParagraphStyle(
            "AttLbl", fontSize=9, textColor=colors.grey, spaceAfter=4)))
        for att in p.attachments:
            story.append(Paragraph(
                f"• {att.original_filename or att.filename}",
                ParagraphStyle("AttItem", fontSize=9, leftIndent=10)
            ))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2 * cm))

    # Footer
    story.append(Paragraph(
        f"Εκτυπώθηκε: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {org_name}",
        styles["footer"]
    ))

    doc.build(story)


def print_receipt(protocol: Protocol, config: dict):
    """Build PDF and open it for printing."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"receipt_{protocol.protocol_full.replace('/', '_')}_{ts}.pdf"
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
