"""Qt stylesheets and theme definitions."""

MAIN_STYLE = """
QMainWindow, QDialog {
    background-color: #f0f4f8;
}

QMenuBar {
    background-color: #1a365d;
    color: white;
    padding: 4px;
    font-size: 13px;
}
QMenuBar::item:selected {
    background-color: #2a4a7f;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    padding: 4px 0;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    font-size: 13px;
}
QMenu::item:selected {
    background-color: #ebf4ff;
    color: #1a365d;
}

QToolBar {
    background-color: #2b6cb0;
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}
QToolButton:hover {
    background-color: #3182ce;
}
QToolButton:pressed {
    background-color: #2c5282;
}

QTabWidget::pane {
    border: 1px solid #cbd5e0;
    background: #ffffff;
}
QTabBar::tab {
    background: #e2e8f0;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    color: #4a5568;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #1a365d;
    border-bottom: 3px solid #2b6cb0;
}
QTabBar::tab:hover {
    background: #f7fafc;
}

QPushButton {
    background-color: #2b6cb0;
    color: white;
    border: none;
    padding: 8px 18px;
    border-radius: 5px;
    font-size: 13px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #3182ce;
}
QPushButton:pressed {
    background-color: #2c5282;
}
QPushButton:disabled {
    background-color: #a0aec0;
}
QPushButton[flat="true"] {
    background: transparent;
    color: #2b6cb0;
    border: 1px solid #2b6cb0;
}
QPushButton[flat="true"]:hover {
    background: #ebf4ff;
}
QPushButton[danger="true"] {
    background-color: #e53e3e;
}
QPushButton[danger="true"]:hover {
    background-color: #fc8181;
}
QPushButton[success="true"] {
    background-color: #38a169;
}
QPushButton[success="true"]:hover {
    background-color: #48bb78;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 13px;
    color: #2d3748;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border: 2px solid #3182ce;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    border: 1px solid #cbd5e0;
    selection-background-color: #ebf4ff;
    selection-color: #1a365d;
}

QLabel {
    color: #2d3748;
    font-size: 13px;
}
QLabel[heading="true"] {
    font-size: 16px;
    font-weight: bold;
    color: #1a365d;
}

QGroupBox {
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    font-size: 13px;
    color: #2d3748;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #2b6cb0;
}

QTableWidget, QTableView {
    background: #ffffff;
    alternate-background-color: #f7fafc;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    font-size: 13px;
    selection-background-color: #bee3f8;
    selection-color: #1a365d;
}
QHeaderView::section {
    background-color: #2b6cb0;
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
    font-size: 12px;
}
QHeaderView::section:hover {
    background-color: #3182ce;
}

QScrollBar:vertical {
    width: 10px;
    background: #f7fafc;
}
QScrollBar::handle:vertical {
    background: #a0aec0;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #718096;
}

QStatusBar {
    background: #1a365d;
    color: white;
    font-size: 12px;
    padding: 3px 8px;
}

QSplitter::handle {
    background: #e2e8f0;
}

/* Priority badges */
QLabel[priority="ΕΠΕΙΓΟΝ"] {
    color: #c05621;
    font-weight: bold;
}
QLabel[priority="ΑΜΕΣΩΣ ΕΠΕΙΓΟΝ"] {
    color: #c53030;
    font-weight: bold;
}
QLabel[priority="ΑΠΟΡΡΗΤΟ"] {
    color: #702459;
    font-weight: bold;
}

/* Sidebar */
QListWidget#sidebar {
    background-color: #1a365d;
    color: #bee3f8;
    border: none;
    font-size: 14px;
    padding: 4px;
    outline: none;
}
QListWidget#sidebar::item {
    padding: 10px 14px;
    border-radius: 5px;
    margin: 2px 4px;
}
QListWidget#sidebar::item:selected {
    background-color: #2b6cb0;
    color: white;
}
QListWidget#sidebar::item:hover {
    background-color: #2a4a7f;
}
"""

INCOMING_COLOR = "#276749"   # green
OUTGOING_COLOR = "#2b6cb0"   # blue
INTERNAL_COLOR = "#744210"   # amber

PRIORITY_COLORS = {
    "ΚΑΝΟΝΙΚΟ": "#4a5568",
    "ΕΠΕΙΓΟΝ": "#c05621",
    "ΑΜΕΣΩΣ ΕΠΕΙΓΟΝ": "#c53030",
    "ΑΠΟΡΡΗΤΟ": "#702459",
    "ΑΥΣΤΗΡΩΣ ΑΠΟΡΡΗΤΟ": "#1a202c",
}

STATUS_COLORS = {
    "ΕΛΛΗΦΘΗ": "#2b6cb0",
    "ΣΕ ΕΚΚΡΕΜΟΤΗΤΑ": "#c05621",
    "ΣΕ ΕΞΕΛΙΞΗ": "#276749",
    "ΔΙΑΒΙΒΑΣΤΗΚΕ": "#6b46c1",
    "ΔΙΕΚΠΕΡΑΙΩΘΗΚΕ": "#38a169",
    "ΑΡΧΕΙΟΘΕΤΗΘΗΚΕ": "#718096",
    "ΑΚΥΡΩΘΗΚΕ": "#e53e3e",
}
