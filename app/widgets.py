"""Reusable PySide6 interface widgets and progress calculations."""
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QProgressBar

STATUSES = ('To Do', 'In Progress', 'Completed')

def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        elif item.layout(): clear(item.layout())


def card():
    f = QFrame(); f.setObjectName('card'); f.setLayout(QVBoxLayout()); f.layout().setSpacing(8)
    return f


def progress(row):
    """Assessment completion, independent of task progress."""
    p = QProgressBar(); p.setRange(0,100)
    p.setValue(round(100 * row['progress_fraction']) if 'progress_fraction' in row.keys() else (100 if row['status'] == 'Completed' else 0))
    return p


def assessment_progress(rows):
    return round(100 * sum((row['progress_fraction'] if 'progress_fraction' in row.keys() else float(row['status'] == 'Completed')) for row in rows) / len(rows)) if rows else 0


class TaskCard(QFrame):
    def __init__(self, task, owner):
        super().__init__(); self.task=task; self.owner=owner; self.setObjectName('card')
        layout=QVBoxLayout(self)
        name=QLabel(task['title']); name.setWordWrap(True); layout.addWidget(name)
        sub=QLabel(f"{task['course']} · {task['assignment_title']} · {task['priority']} priority" + (f" · due {task['due']}" if task['due'] else '')); sub.setWordWrap(True)
        sub.setStyleSheet('color:#9ca3af'); layout.addWidget(sub)
        buttons=QHBoxLayout()
        combo=QComboBox(); combo.addItems(STATUSES); combo.setCurrentText(task['status'])
        combo.currentTextChanged.connect(lambda status,tid=task['id']: owner.move_task(tid,status))
        buttons.addWidget(combo)
        delete=QPushButton('×'); delete.setFixedWidth(34)
        delete.clicked.connect(lambda _,tid=task['id']:owner.remove_task(tid)); buttons.addWidget(delete)
        layout.addLayout(buttons)

    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag=QDrag(self); mime=QMimeData(); mime.setText(f"assessment-task:{self.task['id']}")
            drag.setMimeData(mime); drag.exec(Qt.DropAction.MoveAction)
        super().mouseMoveEvent(event)


class DropColumn(QFrame):
    def __init__(self,status,owner):
        super().__init__(); self.status=status; self.owner=owner
        self.setAcceptDrops(True); self.setObjectName('card')
        self.setMinimumWidth(235)
        self.layout_=QVBoxLayout(self)
        title=QLabel(status); title.setStyleSheet('font-weight:700;font-size:16px;'); self.layout_.addWidget(title)
        self.cards=QVBoxLayout(); self.layout_.addLayout(self.cards); self.layout_.addStretch()

    def dragEnterEvent(self,event):
        if event.mimeData().text().startswith('assessment-task:'): event.acceptProposedAction()

    def dragMoveEvent(self,event):
        if event.mimeData().text().startswith('assessment-task:'): event.acceptProposedAction()

    def dropEvent(self,event):
        try:
            tid=int(event.mimeData().text().split(':',1)[1]); self.owner.move_task(tid,self.status)
            event.acceptProposedAction()
        except (ValueError,IndexError): event.ignore()


