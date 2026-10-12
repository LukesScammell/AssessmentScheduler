"""Dialogs for creating and editing assessments."""
from datetime import datetime
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QDateTimeEdit, QComboBox, QDoubleSpinBox, QCheckBox, QDialogButtonBox, QMessageBox

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

