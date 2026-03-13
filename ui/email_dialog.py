"""Email compose dialog linked to a protocol."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QPushButton,
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox, QHBoxLayout, QLabel,
)
from sqlalchemy.orm import Session
from database.models import Protocol, EmailLog
from config.settings import load_config


class EmailDialog(QDialog):
    def __init__(self, session: Session, protocol: Protocol, parent=None):
        super().__init__(parent)
        self._session = session
        self._protocol = protocol
        self.setWindowTitle(f"Αποστολή Email - Πρωτ. {protocol.protocol_full}")
        self.setMinimumSize(580, 500)
        self._build_ui()
        self._prefill()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        self._ed_to = QLineEdit()
        self._ed_to.setPlaceholderText("email1@example.com, email2@example.com")
        form.addRow("Προς *:", self._ed_to)

        self._ed_cc = QLineEdit()
        self._ed_cc.setPlaceholderText("Κοινοποίηση...")
        form.addRow("Κοινοποίηση:", self._ed_cc)

        self._ed_subject = QLineEdit()
        form.addRow("Θέμα *:", self._ed_subject)

        layout.addLayout(form)

        self._ed_body = QTextEdit()
        self._ed_body.setPlaceholderText("Σώμα μηνύματος...")
        layout.addWidget(self._ed_body, 1)

        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("color:#718096;")
        layout.addWidget(self._lbl_status)

        btns = QDialogButtonBox()
        btn_send = QPushButton("Αποστολή")
        btn_send.setStyleSheet("background:#38a169;color:white;padding:8px 20px;border-radius:5px;font-weight:bold;")
        btn_send.clicked.connect(self._send)
        btn_cancel = QPushButton("Ακύρωση")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_send)
        layout.addWidget(btn_cancel)

    def _prefill(self):
        p = self._protocol
        cfg = load_config()
        org = cfg.get("organization_name", "")

        # Collect recipient emails
        emails = []
        for c in p.recipients:
            if c.email:
                emails.append(c.email)
        if p.sender_contact and p.sender_contact.email:
            if not emails:
                emails.append(p.sender_contact.email)

        self._ed_to.setText(", ".join(emails))
        self._ed_subject.setText(f"Αρ. Πρωτ. {p.protocol_full} - {p.subject}")

        body = f"""Αξιότιμε/η κύριε/α,

Σας διαβιβάζουμε το παρόν έγγραφο με αριθμό πρωτοκόλλου {p.protocol_full} ({p.protocol_date.strftime('%d/%m/%Y') if p.protocol_date else ''}).

Θέμα: {p.subject}

{p.summary or ''}

Με εκτίμηση,
{org}
"""
        self._ed_body.setPlainText(body)

    def _send(self):
        to_text = self._ed_to.text().strip()
        subject = self._ed_subject.text().strip()
        if not to_text or not subject:
            QMessageBox.warning(self, "Σφάλμα", "Τα πεδία Προς και Θέμα είναι υποχρεωτικά.")
            return

        to_list = [e.strip() for e in to_text.replace(";", ",").split(",") if e.strip()]
        cc_list = [e.strip() for e in self._ed_cc.text().replace(";", ",").split(",") if e.strip()]
        body = self._ed_body.toPlainText()

        from services.email_service import send_email
        cfg = load_config()
        ok, msg = send_email(cfg, to_list, subject, body, cc=cc_list)

        log = EmailLog(
            protocol_id=self._protocol.id,
            recipients=", ".join(to_list),
            subject=subject,
            body=body,
            success=ok,
            error_message=msg if not ok else None,
        )
        self._session.add(log)
        self._session.commit()

        if ok:
            QMessageBox.information(self, "Επιτυχία", "Το email εστάλη επιτυχώς!")
            self.accept()
        else:
            QMessageBox.critical(self, "Αποτυχία", f"Αποτυχία αποστολής:\n{msg}")
