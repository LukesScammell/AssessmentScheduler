"""Submission management UI: independent milestones within an assessment."""
from datetime import datetime
from PySide6.QtWidgets import (QDialog,QFormLayout,QLineEdit,QTextEdit,QDateTimeEdit,QComboBox,
    QDialogButtonBox,QMessageBox,QHBoxLayout,QLabel,QPushButton,QProgressBar,QDoubleSpinBox,QCheckBox)
from app.widgets import card

class SubmissionDialog(QDialog):
    def __init__(self, parent, record=None):
        super().__init__(parent)
        self.setWindowTitle('Edit submission' if record else 'Add submission')
        self.form=QFormLayout(self)
        self.title=QLineEdit(record['title'] if record else '')
        self.due=QDateTimeEdit(); self.due.setCalendarPopup(True)
        self.due.setDisplayFormat('dd MMM yyyy HH:mm')
        self.due.setDateTime(datetime.fromisoformat(record['due']) if record else datetime.now().replace(second=0,microsecond=0))
        self.status=QComboBox(); self.status.addItems(['Not Started','In Progress','Completed'])
        if record: self.status.setCurrentText(record['status'])
        self.notes=QTextEdit(record['notes'] if record else '')
        for name,control in [('Submission',self.title),('Deadline',self.due),('Status',self.status),('Notes',self.notes)]: self.form.addRow(name,control)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate); buttons.rejected.connect(self.reject); self.form.addRow(buttons)

    def validate(self):
        if not self.title.text().strip(): QMessageBox.warning(self,'Missing title','Enter a submission name.')
        else: self.accept()

    def values(self):
        return (self.title.text().strip(),self.due.dateTime().toString('yyyy-MM-ddTHH:mm:ss'),self.status.currentText(),self.notes.toPlainText())

class SubmissionManager:
    def __init__(self, window):
        self.window=window

    def display(self, assignment_id, layout):
        stages=self.window.db.submissions.for_assignment(assignment_id)
        heading=QHBoxLayout(); heading.addWidget(QLabel('SUBMISSIONS / MILESTONES')); heading.addStretch()
        add=QPushButton('+ Add submission'); add.clicked.connect(lambda:self.add(assignment_id)); heading.addWidget(add); layout.addLayout(heading)
        assessment=self.window.db.assignment(assignment_id)
        if assessment and assessment['course']=='SDV602' and 'Assessment 1' in assessment['title'] and not stages:
            preset=QPushButton('Add SDV602 Assessment 1 stages (confirm dates in Moodle)')
            preset.clicked.connect(lambda:self.add_sdv_template(assignment_id))
            layout.addWidget(preset)
        if not stages: layout.addWidget(QLabel('No submissions yet. Add separate stages such as Design, Review and Final Submission.'))
        if stages:
            calculate=QPushButton('Calculate overall grade from weighted stages')
            calculate.clicked.connect(lambda:self.apply_stage_grade(assignment_id)); layout.addWidget(calculate)
            layout.addWidget(QLabel('Stage grades are recorded separately. They affect the overall grade only when you explicitly apply a complete weighted result.'))
        for stage in stages:
            tile=card()
            tile.layout().addWidget(QLabel(f"{stage['title']} — {stage['status']}"))
            tile.layout().addWidget(QLabel('Due '+stage['due'].replace('T',' ')))
            if stage['notes']: tile.layout().addWidget(QLabel(stage['notes']))
            if stage['marks_possible'] is not None:
                pct=100*stage['marks_earned']/stage['marks_possible']
                tile.layout().addWidget(QLabel(f"Stage grade: {stage['marks_earned']:g}/{stage['marks_possible']:g} ({pct:.2f}%)"))
            else:
                tile.layout().addWidget(QLabel('Stage grade: Not graded'))
            if stage['stage_weight'] is not None:
                tile.layout().addWidget(QLabel(f"Share of parent assessment: {stage['stage_weight']:g}%"))
            actions=QHBoxLayout()
            edit=QPushButton('Edit submission'); edit.clicked.connect(lambda _,s=stage:self.edit(s)); actions.addWidget(edit)
            marks=QPushButton('Set stage marks'); marks.clicked.connect(lambda _,s=stage:self.edit_marks(s)); actions.addWidget(marks)
            delete=QPushButton('Delete'); delete.clicked.connect(lambda _,sid=stage['id']:self.delete(sid)); actions.addWidget(delete)
            tile.layout().addLayout(actions); layout.addWidget(tile)

    def edit_marks(self, stage):
        dialog=QDialog(self.window); dialog.setWindowTitle('Stage marks — '+stage['title'])
        form=QFormLayout(dialog)
        graded=QCheckBox('Grade received'); graded.setChecked(stage['marks_possible'] is not None)
        earned=QDoubleSpinBox(); earned.setRange(0,100000); earned.setDecimals(2)
        earned.setValue(stage['marks_earned'] or 0)
        possible=QDoubleSpinBox(); possible.setRange(0.01,100000); possible.setDecimals(2)
        possible.setValue(stage['marks_possible'] or 100)
        weighted=QCheckBox('Stage has a confirmed weighting within its assessment')
        weighted.setChecked(stage['stage_weight'] is not None)
        weight=QDoubleSpinBox(); weight.setRange(0,100); weight.setDecimals(2); weight.setSuffix('%')
        weight.setValue(stage['stage_weight'] or 0)
        for label,field in [('Marks available',graded),('Marks earned',earned),('Marks possible',possible),('Weighting confirmed',weighted),('Share of parent assessment',weight)]:
            form.addRow(label,field)
        form.addRow(QLabel('Leave the stage weighting unchecked if your guide does not specify it.'))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec():
            try:
                self.window.db.submissions.save_marks(stage['id'], earned.value() if graded.isChecked() else None,
                    possible.value() if graded.isChecked() else None, weight.value() if weighted.isChecked() else None)
                self.window.refresh()
            except ValueError as exc:
                QMessageBox.warning(self.window,'Invalid marks',str(exc))

    def apply_stage_grade(self, assignment_id):
        result=self.window.db.submissions.weighted_result(assignment_id)
        if result is None:
            QMessageBox.information(self.window,'Stage weights incomplete',
                'Enter a grade and confirmed stage weighting for every stage, with weights adding to 100%. No assessment grade was changed.')
            return
        if QMessageBox.question(self.window,'Apply stage result',
            f'Calculated assessment grade: {result:.2f}%. Replace the current overall assessment grade with this result?')!=QMessageBox.StandardButton.Yes: return
        parent=self.window.db.assignment(assignment_id)
        self.window.db.save_grade(assignment_id,parent['weight'],result)
        self.window.refresh()

    def add(self, assignment_id):
        dialog=SubmissionDialog(self.window)
        if dialog.exec():
            title,due,status,notes=dialog.values()
            self.window.db.submissions.add(assignment_id,title,due,notes)
            if status!='Not Started':
                stage=self.window.db.submissions.for_assignment(assignment_id)[-1]
                self.window.db.submissions.update(stage['id'],title,due,status,notes)
            self.window.refresh()

    def edit(self, stage):
        dialog=SubmissionDialog(self.window,stage)
        if dialog.exec(): self.window.db.submissions.update(stage['id'],*dialog.values()); self.window.refresh()

    def delete(self, stage_id):
        if QMessageBox.question(self.window,'Delete submission','Delete this submission stage?')==QMessageBox.StandardButton.Yes:
            self.window.db.submissions.delete(stage_id); self.window.refresh()

    def add_sdv_template(self, assignment_id):
        """Optional stages based on the course timetable, with unconfirmed times."""
        if self.window.db.submissions.for_assignment(assignment_id): return
        message=('The SDV602 timetable lists 7 August (Design Specification), '
                 '20 August (Review), and 4 September (Final Submission). '
                 'It conflicts with the 28 August overall assessment-table deadline. '
                 'The timetable gives no times; 12:00 PM is a placeholder. '
                 'Please confirm each deadline in Moodle. Add these stages?')
        if QMessageBox.question(self.window,'Confirm SDV602 stages',message)!=QMessageBox.StandardButton.Yes: return
        for title,due in [('Phase 1 — Design Specification','2026-08-07T12:00:00'),
                          ('Phase 2 — Review','2026-08-20T12:00:00'),
                          ('Phase 3 — Final Submission','2026-09-04T12:00:00')]:
            self.window.db.submissions.add(assignment_id,title,due,'12:00 PM is a placeholder; confirm the actual deadline in Moodle.')
        self.window.refresh()
