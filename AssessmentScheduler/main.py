import sys
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate, QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QLineEdit, QTextEdit, QDialog,
    QDialogButtonBox, QFormLayout, QDateTimeEdit, QMessageBox, QCalendarWidget,
    QComboBox, QProgressBar, QTabWidget)
from app.database import Database

STATUSES = ('To Do', 'In Progress', 'Completed')
STYLE = '''
QWidget { background:#111827; color:#e5e7eb; font: 13px 'Segoe UI'; }
QLabel#heading { font-size:24px; font-weight:700; padding:5px 0; }
QFrame#card { background:#1f2937; border:1px solid #374151; border-radius:10px; }
QFrame#card QLabel { background:transparent; }
QPushButton { background:#374151; border:0; border-radius:7px; padding:9px 12px; }
QPushButton:hover { background:#4b5563; }
QPushButton#primary { background:#2563eb; font-weight:600; }
QPushButton#primary:hover { background:#1d4ed8; }
QLineEdit,QTextEdit,QComboBox,QDateTimeEdit { background:#1f2937; border:1px solid #4b5563; border-radius:6px; padding:7px; }
QProgressBar { background:#374151; border:0; border-radius:5px; text-align:center; height:15px; }
QProgressBar::chunk { background:#22c55e; border-radius:5px; }
QScrollArea { border:0; }
QCalendarWidget QWidget { alternate-background-color:#1f2937; }
'''

def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget(): item.widget().deleteLater()
        elif item.layout(): clear(item.layout())

def card():
    f = QFrame(); f.setObjectName('card'); f.setLayout(QVBoxLayout()); f.layout().setSpacing(8)
    return f

def progress(row):
    p = QProgressBar(); p.setRange(0,100)
    p.setValue(round(100*row['completed']/row['total']) if row['total'] else 0)
    return p

class AssignmentDialog(QDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent)
        self.setWindowTitle('Edit assignment' if record else 'New assignment')
        self.resize(440, 310)
        layout=QFormLayout(self)
        self.course=QLineEdit(record['course'] if record else '')
        self.title=QLineEdit(record['title'] if record else '')
        self.due=QDateTimeEdit(); self.due.setCalendarPopup(True)
        self.due.setDisplayFormat('dd MMM yyyy HH:mm')
        self.due.setDateTime(datetime.fromisoformat(record['due']) if record else datetime.now().replace(second=0,microsecond=0))
        self.notes=QTextEdit(record['notes'] if record else '')
        layout.addRow('Course',self.course); layout.addRow('Assessment',self.title)
        layout.addRow('Deadline',self.due); layout.addRow('Notes',self.notes)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate); buttons.rejected.connect(self.reject); layout.addRow(buttons)

    def validate(self):
        if not self.course.text().strip() or not self.title.text().strip():
            QMessageBox.warning(self,'Missing details','Enter both a course and an assessment title.')
        else: self.accept()

    def values(self):
        return (self.course.text().strip(),self.title.text().strip(),self.due.dateTime().toString('yyyy-MM-ddTHH:mm:ss'),self.notes.toPlainText())

class TaskCard(QFrame):
    def __init__(self, task, owner):
        super().__init__(); self.task=task; self.owner=owner; self.setObjectName('card')
        layout=QVBoxLayout(self)
        name=QLabel(task['title']); name.setWordWrap(True); layout.addWidget(name)
        sub=QLabel(f"{task['course']} · {task['assignment_title']}"); sub.setWordWrap(True)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.db=Database(); self.setWindowTitle('Assessment Scheduler v1.0.0')
        self.resize(1180,760); self.selected=None; self.page='Dashboard'
        base=QWidget(); self.setCentralWidget(base); root=QHBoxLayout(base)
        sidebar=QFrame(); sidebar.setFixedWidth(205); sidebar.setObjectName('card')
        nav=QVBoxLayout(sidebar); logo=QLabel('ASSESSMENT\nSCHEDULER'); logo.setStyleSheet('font-size:18px;font-weight:700;color:#93c5fd;'); nav.addWidget(logo)
        for name in ('Dashboard','Kanban Board','Calendar','Assignments'):
            btn=QPushButton(name); btn.clicked.connect(lambda _,n=name:self.show_page(n)); nav.addWidget(btn)
        nav.addStretch(); root.addWidget(sidebar)
        self.content=QScrollArea(); self.content.setWidgetResizable(True)
        self.host=QWidget(); self.body=QVBoxLayout(self.host); self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content.setWidget(self.host); root.addWidget(self.content,1)
        self.show_page('Dashboard')

    def show_page(self,page,aid=None):
        self.page=page; self.selected=aid if aid is not None else self.selected
        clear(self.body); self.detail=None
        heading=QLabel(page); heading.setObjectName('heading'); self.body.addWidget(heading)
        getattr(self,'page_'+{'Dashboard':'dashboard','Kanban Board':'kanban','Calendar':'calendar','Assignments':'assignments'}[page])()

    def refresh(self): self.show_page(self.page)

    def assignment_card(self,row,open_button=True):
        f=card(); f.layout().addWidget(QLabel(f"{row['course']}  ·  {row['title']}"))
        due=datetime.fromisoformat(row['due'])
        f.layout().addWidget(QLabel(f"Due: {due:%d %b %Y, %I:%M %p}   |   {row['completed']}/{row['total']} tasks"))
        f.layout().addWidget(progress(row))
        if open_button:
            btn=QPushButton('Open assignment →'); btn.clicked.connect(lambda _,aid=row['id']:self.show_page('Assignments',aid)); f.layout().addWidget(btn)
        return f

    def page_dashboard(self):
        rows=self.db.assignments(); now=datetime.now()
        upcoming=[r for r in rows if datetime.fromisoformat(r['due'])>=now]
        total=sum(r['total'] for r in rows); done=sum(r['completed'] for r in rows)
        stats=QLabel(f"{len(rows)} assignments   •   {len(upcoming)} upcoming   •   {done}/{total} tasks completed")
        self.body.addWidget(stats)
        p=QProgressBar(); p.setValue(round(done/total*100) if total else 0); self.body.addWidget(p)
        self.body.addWidget(QLabel('Upcoming deadlines'))
        for row in upcoming[:8]: self.body.addWidget(self.assignment_card(row))
        if not upcoming: self.body.addWidget(QLabel('No upcoming deadlines. Add an assignment to get started.'))
        add=QPushButton('+ New assignment'); add.setObjectName('primary'); add.clicked.connect(self.new_assignment); self.body.addWidget(add)

    def page_kanban(self):
        hint=QLabel('Drag task cards between columns, or use the status dropdown.'); self.body.addWidget(hint)
        cols=QHBoxLayout(); columns={s:DropColumn(s,self) for s in STATUSES}
        for c in columns.values(): cols.addWidget(c,1)
        for task in self.db.tasks(): columns[task['status']].cards.addWidget(TaskCard(task,self))
        self.body.addLayout(cols)
        if not self.db.tasks(): self.body.addWidget(QLabel('No tasks yet. Open Assignments to create your first task.'))

    def page_calendar(self):
        cal=QCalendarWidget(); cal.setGridVisible(True); self.body.addWidget(cal)
        events=QLabel('Select a date to see assignments due that day.'); self.body.addWidget(events)
        results=QVBoxLayout(); self.body.addLayout(results)
        rows=self.db.assignments()
        from PySide6.QtGui import QTextCharFormat, QColor
        fmt=QTextCharFormat(); fmt.setBackground(QColor('#2563eb')); fmt.setForeground(QColor('white'))
        for row in rows:
            d=date.fromisoformat(row['due'][:10]); cal.setDateTextFormat(QDate(d.year,d.month,d.day),fmt)
        def selected():
            clear(results); selected_date=cal.selectedDate().toString('yyyy-MM-dd')
            matches=[r for r in rows if r['due'].startswith(selected_date)]
            events.setText(f'{len(matches)} assignment(s) due on {cal.selectedDate().toString("dd MMM yyyy")}')
            for row in matches: results.addWidget(self.assignment_card(row))
        cal.selectionChanged.connect(selected); selected()

    def page_assignments(self):
        add=QPushButton('+ New assignment'); add.setObjectName('primary'); add.clicked.connect(self.new_assignment); self.body.addWidget(add)
        rows=self.db.assignments()
        for row in rows:
            f=self.assignment_card(row,False)
            buttons=QHBoxLayout()
            for label,callback in [('Open tasks',lambda aid=row['id']:self.show_details(aid)),
                ('Edit',lambda aid=row['id']:self.edit_assignment(aid)),
                ('Delete',lambda aid=row['id']:self.remove_assignment(aid))]:
                btn=QPushButton(label); btn.clicked.connect(lambda _,cb=callback:cb()); buttons.addWidget(btn)
            f.layout().addLayout(buttons); self.body.addWidget(f)
        if self.selected: self.show_details(self.selected)

    def show_details(self,aid):
        record=self.db.assignment(aid)
        if not record: self.selected=None; return
        self.selected=aid
        if hasattr(self,'detail') and self.detail:
            self.body.removeWidget(self.detail); self.detail.deleteLater()
        self.detail=card(); self.body.addWidget(self.detail)
        lay=self.detail.layout(); lay.addWidget(QLabel(f"Tasks for {record['course']} — {record['title']}"))
        for task in self.db.tasks(aid):
            row=QHBoxLayout(); row.addWidget(QLabel(task['title']),1)
            combo=QComboBox(); combo.addItems(STATUSES); combo.setCurrentText(task['status'])
            combo.currentTextChanged.connect(lambda status,tid=task['id']:self.move_task(tid,status))
            row.addWidget(combo)
            delete=QPushButton('Delete'); delete.clicked.connect(lambda _,tid=task['id']:self.remove_task(tid)); row.addWidget(delete)
            lay.addLayout(row)
        new=QHBoxLayout(); entry=QLineEdit(); entry.setPlaceholderText('Add a task…'); new.addWidget(entry,1)
        btn=QPushButton('+ Add task'); new.addWidget(btn)
        def add_task():
            if entry.text().strip(): self.db.add_task(aid,entry.text().strip()); self.refresh()
        btn.clicked.connect(add_task); entry.returnPressed.connect(add_task); lay.addLayout(new)

    def new_assignment(self):
        dlg=AssignmentDialog(self)
        if dlg.exec(): self.db.add_assignment(*dlg.values()); self.refresh()

    def edit_assignment(self,aid):
        record=self.db.assignment(aid)
        if not record: return
        dlg=AssignmentDialog(self,record)
        if dlg.exec(): self.db.update_assignment(aid,*dlg.values()); self.refresh()

    def remove_assignment(self,aid):
        if QMessageBox.question(self,'Delete assignment','Delete this assignment and all its tasks?')==QMessageBox.StandardButton.Yes:
            self.db.delete_assignment(aid); self.selected=None; self.refresh()

    def move_task(self,tid,status): self.db.set_status(tid,status); self.refresh()

    def remove_task(self,tid):
        if QMessageBox.question(self,'Delete task','Delete this task?')==QMessageBox.StandardButton.Yes:
            self.db.delete_task(tid); self.refresh()

if __name__=='__main__':
    app=QApplication(sys.argv); app.setStyleSheet(STYLE)
    window=MainWindow(); window.show(); sys.exit(app.exec())
