import sys
from pathlib import Path
from datetime import date, datetime
from PySide6.QtCore import Qt, QDate, QMimeData, QTimer
from PySide6.QtGui import QDrag, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QLineEdit, QTextEdit, QDialog,
    QDialogButtonBox, QFormLayout, QDateTimeEdit, QMessageBox, QCalendarWidget,
    QComboBox, QProgressBar, QTabWidget, QInputDialog, QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog, QSystemTrayIcon)
from app.database import Database

APP_VERSION = '1.5.0'
STATUSES = ('To Do', 'In Progress', 'Completed')
COURSE_COLORS = {'NET502':'#38bdf8','DAT502':'#a78bfa','SDV602':'#34d399','WEB701':'#fb923c'}
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
        self.status=QComboBox(); self.status.addItems(['Not Started','In Progress','Completed'])
        if record: self.status.setCurrentText(record['status'])
        layout.addRow('Course',self.course); layout.addRow('Assessment',self.title)
        layout.addRow('Deadline',self.due); layout.addRow('Status',self.status); layout.addRow('Notes',self.notes)
        if not record:
            self.weight=QDoubleSpinBox(); self.weight.setRange(0,100); self.weight.setDecimals(2); self.weight.setSuffix('%')
            self.has_grade=QCheckBox('Grade received (optional)')
            self.earned=QDoubleSpinBox(); self.earned.setRange(0,100000); self.earned.setDecimals(2)
            self.possible=QDoubleSpinBox(); self.possible.setRange(0.01,100000); self.possible.setValue(100); self.possible.setDecimals(2)
            layout.addRow('Assessment weight',self.weight); layout.addRow(self.has_grade)
            layout.addRow('Marks earned',self.earned); layout.addRow('Marks possible',self.possible)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate); buttons.rejected.connect(self.reject); layout.addRow(buttons)

    def validate(self):
        if not self.course.text().strip() or not self.title.text().strip():
            QMessageBox.warning(self,'Missing details','Enter both a course and an assessment title.')
        else: self.accept()

    def values(self):
        return (self.course.text().strip(),self.title.text().strip(),self.due.dateTime().toString('yyyy-MM-ddTHH:mm:ss'),self.notes.toPlainText(),self.status.currentText())

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
            drag=QDrag, QIcon(self); mime=QMimeData(); mime.setText(f"assessment-task:{self.task['id']}")
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
        super().__init__(); self.db=Database(); self.setWindowTitle(f'Assessment Scheduler v{APP_VERSION}')
        self.resize(1180,760); self.selected=None; self.page='Dashboard'; self.course_filter='All courses'; self.remaining=0; self.timer_paused=False; self.timer_course=''; self.timer_minutes=25
        self.timer=QTimer(self); self.timer.timeout.connect(self.timer_tick)
        self.tray=QSystemTrayIcon(self); self.tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)); self.tray.show()
        self.notification_timer=QTimer(self); self.notification_timer.timeout.connect(self.check_deadlines); self.notification_timer.start(60000)
        base=QWidget(); self.setCentralWidget(base); root=QHBoxLayout(base); root.setContentsMargins(16,16,16,16); root.setSpacing(18)
        sidebar=QFrame(); sidebar.setFixedWidth(220); sidebar.setObjectName('sidebar')
        nav=QVBoxLayout(sidebar); nav.setContentsMargins(14,20,14,14); nav.setSpacing(7); logo=QLabel('✦  ASSESSMENT\n     SCHEDULER'); logo.setStyleSheet('font-size:17px;font-weight:800;color:#9dccff;padding:10px 0 24px 0;'); nav.addWidget(logo); self.nav_buttons={}
        for name in ('Dashboard','Kanban Board','Calendar','Assignments','Study Planner','Study Timer','Grades','Settings'):
            btn=QPushButton(name); btn.setObjectName('nav'); btn.clicked.connect(lambda _,n=name:self.show_page(n)); nav.addWidget(btn); self.nav_buttons[name]=btn
        course_heading=QLabel('MY CLASSES'); course_heading.setObjectName('section'); nav.addWidget(course_heading)
        self.course_nav=QVBoxLayout(); self.course_nav.setSpacing(3); nav.addLayout(self.course_nav)
        nav.addStretch(); version=QLabel(f'VERSION {APP_VERSION}  •  LOCAL & PRIVATE'); version.setObjectName('muted'); version.setStyleSheet('font-size:10px;color:#8ca1bc;'); nav.addWidget(version); root.addWidget(sidebar)
        self.content=QScrollArea(); self.content.setWidgetResizable(True)
        self.host=QWidget(); self.body=QVBoxLayout(self.host); self.body.setContentsMargins(10,4,10,16); self.body.setSpacing(14); self.body.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content.setWidget(self.host); root.addWidget(self.content,1)
        self.update_course_navigation(); self.apply_appearance(); self.show_page('Dashboard'); QTimer.singleShot(2000,self.check_deadlines)

    def courses(self):
        return self.db.courses()

    def update_course_navigation(self):
        clear(self.course_nav)
        for course in self.courses():
            button=QPushButton('●  '+course); button.setObjectName('nav')
            button.setStyleSheet('text-align:left;color:'+COURSE_COLORS.get(course,'#9dccff')+';')
            button.clicked.connect(lambda _,c=course:self.show_page('Course',course=c))
            self.course_nav.addWidget(button)
        add=QPushButton('+ Add class'); add.setObjectName('nav')
        add.clicked.connect(self.add_class); self.course_nav.addWidget(add)

    def add_class(self):
        course,ok=QInputDialog.getText(self,'Add class','Course code (for example, WEB701):')
        if ok and course.strip():
            self.db.add_course(course.strip().upper()); self.update_course_navigation(); self.show_page('Course',course=course.strip().upper())

    def show_page(self,page,aid=None,course=None):
        self.page=page
        if course is not None: self.active_course=course
        self.selected=aid if aid is not None else (self.selected if page=='Assignments' else None)
        for name,button in self.nav_buttons.items():
            button.setProperty('active', 'true' if name==page else 'false'); button.style().unpolish(button); button.style().polish(button)
        clear(self.body); self.detail=None
        heading=QLabel(self.active_course if page=='Course' else page); heading.setObjectName('heading'); self.body.addWidget(heading)
        getattr(self,'page_'+{'Dashboard':'dashboard','Kanban Board':'kanban','Calendar':'calendar','Assignments':'assignments','Course':'course','Study Planner':'study_planner','Study Timer':'study_timer','Grades':'grades','Settings':'settings'}[page])()

    def refresh(self):
        self.update_course_navigation(); self.show_page(self.page)

    def assignment_card(self,row,open_button=True):
        f=card(); course=QLabel(row['course']); course.setStyleSheet(f"color:{COURSE_COLORS.get(row['course'],'#9dccff')};font-size:12px;font-weight:800;letter-spacing:1px;"); f.layout().addWidget(course); title=QLabel(row['title']); title.setWordWrap(True); title.setStyleSheet('font-size:16px;font-weight:700;'); f.layout().addWidget(title)
        due=datetime.fromisoformat(row['due'])
        f.layout().addWidget(QLabel('Status: '+row['status']))
        if row['grade'] is not None:
            grade_text=(f"{row['marks_earned']:g}/{row['marks_possible']:g} marks" if row['marks_possible'] else 'Percentage grade')
            f.layout().addWidget(QLabel(f"Grade: {grade_text} ({row['grade']:.2f}%)"))
        f.layout().addWidget(QLabel(f"Due {due:%d %b %Y, %I:%M %p}  ·  {row['completed']}/{row['total']} tasks completed"))
        f.layout().addWidget(progress(row))
        if open_button:
            btn=QPushButton('Open assignment →'); btn.clicked.connect(lambda _,aid=row['id']:self.show_page('Assignments',aid)); f.layout().addWidget(btn)
        return f

    def page_dashboard(self):
        rows=self.db.assignments(); now=datetime.now()
        upcoming=[r for r in rows if r['status']!='Completed' and datetime.fromisoformat(r['due'])>=now]
        total=sum(r['total'] for r in rows); done=sum(r['completed'] for r in rows)
        intro=QLabel('Your assessments, at a glance. Stay focused on what matters next.')
        intro.setObjectName('muted'); self.body.addWidget(intro)
        metrics=QHBoxLayout(); metrics.setSpacing(12)
        for label,value,accent in [('ASSIGNMENTS',str(len(rows)),'#93c5fd'),('UPCOMING',str(len(upcoming)),'#fbbf24'),('TASKS DONE',f'{done}/{total}','#6ee7b7')]:
            tile=card(); small=QLabel(label); small.setStyleSheet('color:#9cabc1;font-size:11px;font-weight:700;letter-spacing:1px;'); tile.layout().addWidget(small)
            big=QLabel(value); big.setObjectName('metric'); big.setStyleSheet(f'color:{accent};font-size:27px;font-weight:750;'); tile.layout().addWidget(big); metrics.addWidget(tile,1)
        self.body.addLayout(metrics)
        section=card(); section.layout().addWidget(QLabel('OVERALL TASK PROGRESS'))
        bar=QProgressBar(); bar.setValue(round(done/total*100) if total else 0); section.layout().addWidget(bar); self.body.addWidget(section)
        toolbar=QHBoxLayout(); heading=QLabel('Upcoming deadlines'); heading.setStyleSheet('font-size:18px;font-weight:700;'); toolbar.addWidget(heading); toolbar.addStretch()
        add=QPushButton('+ New assignment'); add.setObjectName('primary'); add.clicked.connect(self.new_assignment); toolbar.addWidget(add)
        self.body.addLayout(toolbar)
        for row in upcoming[:8]: self.body.addWidget(self.assignment_card(row))
        if not upcoming:
            empty=QLabel('No upcoming deadlines yet. Add an assignment or import your assessment dates.')
            empty.setObjectName('muted'); self.body.addWidget(empty)
        sample=QPushButton('Import my 2026 assessment dates (6)')
        sample.clicked.connect(self.import_assessments); self.body.addWidget(sample)
        guides=QPushButton('Import 2026 course-guide assessments (SDV602, WEB701, DAT502)')
        guides.clicked.connect(self.import_course_guides); self.body.addWidget(guides)

    def import_assessments(self):
        answer=QMessageBox.question(self,'Import assessment dates',
            'Add the six NET502, DAT502, SDV602 and WEB701 assessment deadlines?\n\n'
            'Existing assignments will be kept. Matching imported assignments will not be duplicated.\n\n'
            'SDV602 has no confirmed submission time; a 12:00 placeholder will be used and clearly marked in its notes.')
        if answer==QMessageBox.StandardButton.Yes:
            count=self.db.import_starter_assessments()
            QMessageBox.information(self,'Import complete',f'{count} assessment(s) added. Existing data was preserved.')
            self.refresh()

    def import_course_guides(self):
        answer=QMessageBox.question(self,'Import course-guide assessments',
            'Add SDV602, WEB701 and DAT502 assessment deadlines from the 2026 course guides?\n\n'
            'Existing assignments, marks, statuses and notes will be kept. Matching dates will not be duplicated.\n\n'
            'DAT502 report/test component weights are unspecified and will start at 0 until you confirm them.\n'
            'SDV602 Assessment 1 has conflicting guide dates; the formal assessment table date is used.')
        if answer==QMessageBox.StandardButton.Yes:
            count=self.db.import_course_guide_assessments()
            QMessageBox.information(self,'Import complete',f'{count} new assessment(s) added. Existing marks were not changed.')
            self.refresh()

    def course_selector(self, callback):
        line=QHBoxLayout(); line.addWidget(QLabel('Filter by class:'))
        combo=QComboBox(); combo.addItems(['All courses']+self.courses())
        combo.setCurrentText(self.course_filter if self.course_filter in ['All courses']+self.courses() else 'All courses')
        combo.currentTextChanged.connect(callback); line.addWidget(combo); line.addStretch(); self.body.addLayout(line)

    def set_course_filter(self,course):
        self.course_filter=course; self.refresh()

    def page_kanban(self):
        self.course_selector(self.set_course_filter)
        hint=QLabel('Drag task cards between columns, or use the status dropdown.'); self.body.addWidget(hint)
        cols=QHBoxLayout(); columns={s:DropColumn(s,self) for s in STATUSES}
        for c in columns.values(): cols.addWidget(c,1)
        for task in self.db.tasks():
            if self.course_filter=='All courses' or task['course']==self.course_filter:
                columns[task['status']].cards.addWidget(TaskCard(task,self))
        self.body.addLayout(cols)
        if not any(self.course_filter=='All courses' or t['course']==self.course_filter for t in self.db.tasks()): self.body.addWidget(QLabel('No tasks in this view. Open a class page to create tasks.'))

    def page_calendar(self):
        self.course_selector(self.set_course_filter)
        cal=QCalendarWidget(); cal.setGridVisible(True); self.body.addWidget(cal)
        events=QLabel('Select a date to see assignments due that day.'); self.body.addWidget(events)
        results=QVBoxLayout(); self.body.addLayout(results)
        rows=[r for r in self.db.assignments() if self.course_filter=='All courses' or r['course']==self.course_filter]
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
        self.course_selector(self.set_course_filter)
        add=QPushButton('+ New assignment'); add.setObjectName('primary'); add.clicked.connect(self.new_assignment); self.body.addWidget(add)
        rows=[r for r in self.db.assignments() if self.course_filter=='All courses' or r['course']==self.course_filter]
        for row in sorted(rows,key=lambda r:(r['status']=='Completed',r['due'])):
            f=self.assignment_card(row,False)
            buttons=QHBoxLayout()
            for label,callback in [('Open tasks',lambda aid=row['id']:self.show_details(aid)),
                ('Edit',lambda aid=row['id']:self.edit_assignment(aid)),
                ('Delete',lambda aid=row['id']:self.remove_assignment(aid))]:
                btn=QPushButton(label); btn.clicked.connect(lambda _,cb=callback:cb()); buttons.addWidget(btn)
            f.layout().addLayout(buttons); self.body.addWidget(f)
        if self.selected: self.show_details(self.selected)

    def page_course(self):
        course=self.active_course
        rows=[r for r in self.db.assignments() if r['course']==course]
        done=sum(r['completed'] for r in rows); total=sum(r['total'] for r in rows)
        sub=QLabel('Your dedicated workspace for '+course+' assignments and tasks.')
        sub.setObjectName('muted'); self.body.addWidget(sub)
        stats=QHBoxLayout()
        for label,value in [('ASSESSMENTS',str(len(rows))),('TASKS COMPLETED',f'{done}/{total}'),('CLASS PROGRESS',f'{round(100*done/total) if total else 0}%')]:
            tile=card(); caption=QLabel(label); caption.setObjectName('muted'); tile.layout().addWidget(caption)
            number=QLabel(value); number.setObjectName('metric'); tile.layout().addWidget(number); stats.addWidget(tile,1)
        self.body.addLayout(stats)
        overall=card(); overall.layout().addWidget(QLabel('Overall class progress'))
        overall.layout().addWidget(progress({'completed':done,'total':total})); self.body.addWidget(overall)
        line=QHBoxLayout(); line.addWidget(QLabel('Assessments')); line.addStretch()
        add=QPushButton('+ New assignment'); add.setObjectName('primary')
        add.clicked.connect(lambda:self.new_assignment(course)); line.addWidget(add); self.body.addLayout(line)
        if not rows:
            empty=QLabel('No assignments for this class yet. Add one to get started.')
            empty.setObjectName('muted'); self.body.addWidget(empty)
        note_box=card(); note_box.layout().addWidget(QLabel('CLASS NOTES'))
        notes=QTextEdit(); notes.setPlaceholderText('Class notes, links, revision topics…'); notes.setPlainText(self.db.course_note(course)); note_box.layout().addWidget(notes)
        save=QPushButton('Save class notes'); save.clicked.connect(lambda:self.save_notes(course,notes.toPlainText())); note_box.layout().addWidget(save); self.body.addWidget(note_box)
        for label,subset in [('UPCOMING / IN PROGRESS',[r for r in rows if r['status']!='Completed']),('COMPLETED ASSESSMENTS',[r for r in rows if r['status']=='Completed'])]:
            if not subset: continue
            group_heading=QLabel(label); group_heading.setObjectName('section'); self.body.addWidget(group_heading)
            for row in subset:
                self.body.addWidget(self.course_assignment_card(row))
        if self.selected and any(r['id']==self.selected for r in rows): self.show_details(self.selected)

    def course_assignment_card(self,row):
        tile=self.assignment_card(row,False)
        actions=QHBoxLayout()
        for label,action in [('Manage tasks',lambda aid=row['id']:self.show_details(aid)),
                             ('Edit',lambda aid=row['id']:self.edit_assignment(aid)),
                             ('Set grade',lambda aid=row['id']:self.edit_grade(aid)),
                             ('Delete',lambda aid=row['id']:self.remove_assignment(aid))]:
            button=QPushButton(label); button.clicked.connect(lambda _,cb=action:cb()); actions.addWidget(button)
        tile.layout().addLayout(actions)
        return tile

    def save_notes(self,course,text):
        self.db.save_course_note(course,text); QMessageBox.information(self,'Notes saved','Class notes saved successfully.')

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
            priority=QComboBox(); priority.addItems(['Low','Medium','High','Urgent']); priority.setCurrentText(task['priority'])
            priority.currentTextChanged.connect(lambda value,tid=task['id'],due=task['due']:self.db.set_task_details(tid,value,due)); row.addWidget(priority)
            due=QLineEdit(task['due']); due.setPlaceholderText('Optional due YYYY-MM-DD'); due.setMaximumWidth(145)
            due.editingFinished.connect(lambda tid=task['id'],combo=priority,field=due:self.save_task_due(tid,combo.currentText(),field.text())); row.addWidget(due)
            delete=QPushButton('Delete'); delete.clicked.connect(lambda _,tid=task['id']:self.remove_task(tid)); row.addWidget(delete)
            lay.addLayout(row)
        new=QHBoxLayout(); entry=QLineEdit(); entry.setPlaceholderText('Add a task…'); new.addWidget(entry,1)
        btn=QPushButton('+ Add task'); new.addWidget(btn)
        def add_task():
            if entry.text().strip(): self.db.add_task(aid,entry.text().strip()); self.refresh()
        btn.clicked.connect(add_task); entry.returnPressed.connect(add_task); lay.addLayout(new)

    def save_task_due(self,tid,priority,due):
        if due:
            try: date.fromisoformat(due)
            except ValueError:
                QMessageBox.warning(self,'Invalid date','Use YYYY-MM-DD or leave the due date blank.'); return
        self.db.set_task_details(tid,priority,due)

    def new_assignment(self,course=None):
        dlg=AssignmentDialog(self)
        if course: dlg.course.setText(course)
        if dlg.exec():
            if hasattr(dlg,'has_grade') and dlg.has_grade.isChecked() and dlg.earned.value()>dlg.possible.value():
                QMessageBox.warning(self,'Invalid marks','Marks earned cannot exceed marks possible.'); return
            aid=self.db.add_assignment(*dlg.values())
            self.db.save_marks(aid,dlg.weight.value(),dlg.earned.value() if dlg.has_grade.isChecked() else None,dlg.possible.value() if dlg.has_grade.isChecked() else None)
            self.refresh()

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

    def page_study_timer(self):
        self.body.addWidget(QLabel('Pomodoro focus timer — sessions are saved when the countdown finishes.'))
        line=QHBoxLayout(); self.focus_course=QComboBox(); self.focus_course.addItems(self.courses()); line.addWidget(self.focus_course)
        self.focus_length=QSpinBox(); self.focus_length.setRange(1,120); self.focus_length.setValue(25); self.focus_length.setSuffix(' min'); line.addWidget(self.focus_length); self.body.addLayout(line)
        self.timer_label=QLabel(); self.timer_label.setStyleSheet('font-size:52px;font-weight:800;'); self.body.addWidget(self.timer_label)
        controls=QHBoxLayout()
        for name,handler in [('Start',self.timer_start),('Pause / Resume',self.timer_pause),('Reset',self.timer_reset)]:
            b=QPushButton(name); b.clicked.connect(handler); controls.addWidget(b)
        self.body.addLayout(controls)
        self.update_timer_label()
        self.body.addWidget(QLabel('Recorded focus time by class'))
        for r in self.db.study_summary(): self.body.addWidget(QLabel(f"{r['course']}: {r['minutes']} minutes"))

    def update_timer_label(self):
        if getattr(self,'timer_label',None) and self.page=='Study Timer':
            remaining=self.remaining if self.remaining else self.focus_length.value()*60
            self.timer_label.setText(f'{remaining//60:02d}:{remaining%60:02d}')

    def timer_start(self):
        if self.remaining==0:
            self.remaining=self.focus_length.value()*60
            self.timer_course=self.focus_course.currentText(); self.timer_minutes=self.focus_length.value()
        self.timer_paused=False; self.timer.start(1000); self.update_timer_label()

    def timer_pause(self):
        if not self.remaining: return
        self.timer_paused=not self.timer_paused
        if self.timer_paused: self.timer.stop()
        else: self.timer.start(1000)

    def timer_reset(self):
        self.timer.stop(); self.remaining=0; self.timer_paused=False; self.update_timer_label()

    def timer_tick(self):
        if self.remaining>0: self.remaining-=1
        self.update_timer_label()
        if self.remaining==0:
            self.timer.stop(); self.db.record_session(self.timer_course,self.timer_minutes)
            self.tray.showMessage('Focus session complete',f'{self.timer_minutes} minutes logged for {self.timer_course}. Take a break.',QSystemTrayIcon.MessageIcon.Information,6000)
            if self.page=='Study Timer': self.refresh()

    def page_study_planner(self):
        self.body.addWidget(QLabel('Schedule study sessions by class, date and duration.'))
        add=QPushButton('+ Schedule study session'); add.clicked.connect(self.add_study_plan); self.body.addWidget(add)
        last_week=None
        for plan in self.db.plans():
            week=datetime.fromisoformat(plan['start']).strftime('%G-W%V')
            if week!=last_week:
                self.body.addWidget(QLabel(f'Week {week}')); last_week=week
            row=card(); row.layout().addWidget(QLabel(f"{plan['course']} · {plan['title']}"))
            row.layout().addWidget(QLabel(f"{plan['start'].replace('T',' ')} · {plan['minutes']} minutes"))
            delete=QPushButton('Remove session'); delete.clicked.connect(lambda _,pid=plan['id']:self.delete_study_plan(pid)); row.layout().addWidget(delete); self.body.addWidget(row)

    def add_study_plan(self):
        dlg=QDialog(self); dlg.setWindowTitle('Schedule study session'); form=QFormLayout(dlg)
        course=QComboBox(); course.addItems(self.courses()); title=QLineEdit(); title.setPlaceholderText('Study topic')
        start=QDateTimeEdit(); start.setCalendarPopup(True); start.setDateTime(datetime.now()); start.setDisplayFormat('dd MMM yyyy HH:mm')
        duration=QSpinBox(); duration.setRange(5,480); duration.setValue(60); duration.setSuffix(' minutes')
        for label,widget in [('Class',course),('Topic',title),('Start',start),('Duration',duration)]: form.addRow(label,widget)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addRow(buttons)
        if dlg.exec() and title.text().strip():
            self.db.add_plan(course.currentText(),title.text().strip(),start.dateTime().toString('yyyy-MM-ddTHH:mm:ss'),duration.value()); self.refresh()

    def delete_study_plan(self,pid): self.db.delete_plan(pid); self.refresh()

    def page_grades(self):
        self.body.addWidget(QLabel('Enter marks earned / marks possible and the assessment weight. Previously saved percentage-only grades are preserved.'))
        for course in self.courses():
            rows=[a for a in self.db.assignments() if a['course']==course]
            if not rows: continue
            heading=QLabel(course); heading.setStyleSheet('font-size:20px;font-weight:700;'); self.body.addWidget(heading)
            graded=[a for a in rows if a['grade'] is not None and a['weight']>0]
            weights=sum(a['weight'] for a in graded)
            weighted=sum(a['weight']*a['grade']/100 for a in graded)
            total_weights=sum(a['weight'] for a in rows)
            self.body.addWidget(QLabel(f'Average across graded assessment weights: {weighted/weights*100:.2f}%' if weights else 'No weighted grades recorded yet'))
            self.body.addWidget(QLabel(f'Points earned toward course total: {weighted:.2f} / 100 (assuming weights total 100%)'))
            self.body.addWidget(QLabel(f'Total assigned assessment weight: {total_weights:g}% (target: 100%)'))
            for a in rows:
                row=QHBoxLayout(); row.addWidget(QLabel(a['title']),1)
                if a['grade'] is None: mark='Not graded'
                elif a['marks_possible'] is not None: mark=f"{a['marks_earned']:g}/{a['marks_possible']:g} ({a['grade']:.2f}%)"
                else: mark=f"{a['grade']:.2f}% (legacy grade)"
                row.addWidget(QLabel(f"Weight {a['weight']:g}% · {mark} · {a['status']}"))
                edit=QPushButton('Set marks'); edit.clicked.connect(lambda _,aid=a['id']:self.edit_grade(aid)); row.addWidget(edit); self.body.addLayout(row)

    def edit_grade(self,aid):
        a=self.db.assignment(aid); dlg=QDialog(self); dlg.setWindowTitle('Assessment marks'); form=QFormLayout(dlg)
        weight=QDoubleSpinBox(); weight.setRange(0,100); weight.setDecimals(2); weight.setValue(a['weight']); weight.setSuffix('%')
        graded=QCheckBox('Grade has been received'); graded.setChecked(a['grade'] is not None)
        earned=QDoubleSpinBox(); earned.setRange(0,100000); earned.setDecimals(2)
        possible=QDoubleSpinBox(); possible.setRange(0.01,100000); possible.setDecimals(2); possible.setValue(a['marks_possible'] if a['marks_possible'] is not None else 100)
        earned.setValue(a['marks_earned'] if a['marks_earned'] is not None else (a['grade'] or 0))
        status=QComboBox(); status.addItems(['Not Started','In Progress','Completed']); status.setCurrentText(a['status'])
        form.addRow('Assessment weight',weight); form.addRow('Assessment status',status); form.addRow(graded)
        form.addRow('Marks earned',earned); form.addRow('Marks possible',possible)
        if a['grade'] is not None and a['marks_possible'] is None:
            form.addRow(QLabel('Existing percentage-only grade: edit marks to replace it.'))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addRow(buttons)
        if dlg.exec():
            try:
                self.db.save_marks(aid,weight.value(),earned.value() if graded.isChecked() else None,possible.value() if graded.isChecked() else None)
                self.db.set_assignment_status(aid,status.currentText())
                self.refresh()
            except ValueError as exc: QMessageBox.warning(self,'Invalid marks',str(exc))

    def page_settings(self):
        self.body.addWidget(QLabel('Appearance'))
        theme=QComboBox(); theme.addItems(['Blue','Purple','Green','Orange']); theme.setCurrentText(self.db.preference('accent','Blue'))
        theme.currentTextChanged.connect(self.change_accent); self.body.addWidget(theme)
        mode=QComboBox(); mode.addItems(['Dark','Light']); mode.setCurrentText(self.db.preference('mode','Dark')); mode.currentTextChanged.connect(self.change_mode); self.body.addWidget(mode)
        alerts=QCheckBox('Show deadline notifications while app is open'); alerts.setChecked(self.db.preference('notifications','on')=='on')
        alerts.toggled.connect(lambda enabled:self.db.set_preference('notifications','on' if enabled else 'off')); self.body.addWidget(alerts)
        self.body.addWidget(QLabel('Data backup and restore'))
        backup=QPushButton('Back up all app data (.sqlite3)'); backup.clicked.connect(self.backup_data); self.body.addWidget(backup)
        restore=QPushButton('Restore from backup (.sqlite3)'); restore.clicked.connect(self.restore_data); self.body.addWidget(restore)
        self.body.addWidget(QLabel('Restoring replaces the current database. The app closes afterward; reopen it to load the restored data.'))
        self.body.addWidget(QLabel('Deadline notifications are checked while Assessment Scheduler is running.'))

    def change_accent(self,name):
        self.db.set_preference('accent',name); self.apply_appearance()

    def change_mode(self,name):
        self.db.set_preference('mode',name); self.apply_appearance()

    def apply_appearance(self):
        accents={'Blue':'#3575ed','Purple':'#8257d9','Green':'#16866f','Orange':'#c56b24'}
        color=accents.get(self.db.preference('accent','Blue'),'#3575ed')
        style=STYLE
        if self.db.preference('mode','Dark')=='Light':
            import re
            palette=dict([('#0b1220','#f3f6fb'),('#e6edf8','#172236'),('#172236','#ffffff'),('#2a3b55','#c5d0e0'),('#101b2d','#e8eef7'),('#263751','#c5d0e0'),('#9cabc1','#4e6077'),('#93a8c4','#4e6077'),('#253650','#dce5f1'),('#30435f','#b4c5d9'),('#334969','#cad9ed'),('#101a2b','#ffffff'),('#3b4c67','#b4c5d9')])
            style=re.sub('|'.join(re.escape(k) for k in palette),lambda m:palette[m.group(0)],style)
        QApplication.instance().setStyleSheet(style+f'\nQPushButton#primary {{background:{color};border-color:{color};color:white;}} QProgressBar::chunk {{background:{color};}}')

    def backup_data(self):
        from app.database import DB_PATH
        import sqlite3
        filename,_=QFileDialog.getSaveFileName(self,'Save backup','AssessmentScheduler-backup.sqlite3','SQLite backup (*.sqlite3)')
        if not filename: return
        if Path(filename).resolve()==DB_PATH.resolve():
            QMessageBox.warning(self,'Invalid backup path','Choose a location other than the live database.'); return
        try:
            target=sqlite3.connect(filename)
            try: self.db.conn.backup(target)
            finally: target.close()
            QMessageBox.information(self,'Backup complete','Backup saved successfully.')
        except Exception as exc: QMessageBox.critical(self,'Backup failed',str(exc))

    def restore_data(self):
        from app.database import DB_PATH
        import sqlite3,os,tempfile
        filename,_=QFileDialog.getOpenFileName(self,'Select backup','','SQLite backup (*.sqlite3)')
        if not filename: return
        if Path(filename).resolve()==DB_PATH.resolve():
            QMessageBox.warning(self,'Invalid backup','Choose a backup file, not the live database.'); return
        if QMessageBox.question(self,'Restore backup','Replace all current classes, assignments and tasks with this backup? This cannot be undone unless you create a backup first.')!=QMessageBox.StandardButton.Yes: return
        temp=None
        try:
            source=sqlite3.connect(f'file:{Path(filename).as_posix()}?mode=ro',uri=True)
            try:
                if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('Backup integrity check failed')
                tables={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'assignments','tasks','courses'}.issubset(tables): raise ValueError('This is not an Assessment Scheduler backup')
                fd,temp=tempfile.mkstemp(suffix='.sqlite3',dir=DB_PATH.parent); os.close(fd)
                target=sqlite3.connect(temp)
                try: source.backup(target)
                finally: target.close()
            finally: source.close()
            self.timer.stop(); self.notification_timer.stop(); self.db.conn.close()
            os.replace(temp,DB_PATH); temp=None
            QMessageBox.information(self,'Restore complete','Backup restored. The application will close. Please reopen Assessment Scheduler.')
            QApplication.instance().quit()
        except Exception as exc:
            QMessageBox.critical(self,'Restore failed',str(exc))
        finally:
            if temp and os.path.exists(temp): os.unlink(temp)

    def check_deadlines(self):
        if self.db.preference('notifications','on')!='on': return
        pending=self.db.pending_deadlines(datetime.now())
        if not pending: return
        # Show the nearest notification and record only notifications actually attempted.
        sent=set()
        for a,threshold in sorted(pending,key=lambda item:item[0]['due']):
            if a['id'] in sent: continue
            sent.add(a['id'])
            self.tray.showMessage('Upcoming assessment deadline',f"{a['course']}: {a['title']} — due {a['due'].replace('T',' ')} (within {threshold}).",QSystemTrayIcon.MessageIcon.Information,8000)
            for row,level in pending:
                if row['id']==a['id']: self.db.mark_notified(a['id'],level)

if __name__=='__main__':
    app=QApplication(sys.argv); app.setStyleSheet(STYLE)
    window=MainWindow(); window.show(); sys.exit(app.exec())
