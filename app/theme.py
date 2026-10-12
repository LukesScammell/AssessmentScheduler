"""Centralised colours and application stylesheet."""
STYLE = '''
QWidget { background:#0b1220; color:#e6edf8; font: 13px 'Segoe UI'; }
QLabel#heading { font-size:29px; font-weight:750; padding:8px 0 2px 0; }
QLabel#muted { color:#9cabc1; }
QLabel#metric { font-size:26px; font-weight:750; }
QFrame#card { background:#172236; border:1px solid #2a3b55; border-radius:13px; }
QFrame#card QLabel { background:transparent; }
QFrame#sidebar { background:#101b2d; border:1px solid #263751; border-radius:14px; }
QFrame#sidebar QLabel { background:transparent; }
QPushButton { background:#253650; border:1px solid #30435f; border-radius:9px; padding:10px 13px; font-weight:550; }
QPushButton:hover { background:#334969; }
QPushButton#primary { background:#3575ed; border:1px solid #4c88fa; color:white; font-weight:700; }
QPushButton#primary:hover { background:#2865d5; }
QPushButton#nav { text-align:left; padding:12px 14px; background:transparent; border:0; }
QPushButton#nav:hover { background:#243853; }
QPushButton#nav[active="true"] { background:#27466f; color:#b6d6ff; }
QLabel#section { color:#93a8c4; font-size:11px; font-weight:800; letter-spacing:1px; padding:10px 0 3px 0; }
QLineEdit,QTextEdit,QComboBox,QDateTimeEdit { background:#101a2b; border:1px solid #3b4c67; border-radius:8px; padding:8px; }
QProgressBar { background:#26354b; border:0; border-radius:6px; text-align:center; height:17px; font-weight:650; }
QProgressBar::chunk { background:#38bda6; border-radius:6px; }
QScrollArea { border:0; background:transparent; }
QCalendarWidget QWidget { alternate-background-color:#1a2a40; }
QCalendarWidget QToolButton { background:#253650; }
QDialog { background:#101b2d; }
'''
