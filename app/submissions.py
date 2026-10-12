"""Submission stages (milestones) belonging to an assessment.

One assessment retains one course weighting and one final grade. Each stage
tracks a distinct deliverable and is intentionally not an extra graded assessment.
"""
from datetime import datetime

STAGE_STATUSES = ('Not Started', 'In Progress', 'Completed')

class SubmissionRepository:
    def __init__(self, connection):
        self.conn = connection
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY,
                assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
                title TEXT NOT NULL, due TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not Started',
                notes TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL DEFAULT 0,
                marks_earned REAL, marks_possible REAL,
                stage_weight REAL
            )''')
        for column in ("marks_earned", "marks_possible", "stage_weight"):
            existing = {r["name"] for r in self.conn.execute("PRAGMA table_info(submissions)")}
            if column not in existing:
                self.conn.execute(f"ALTER TABLE submissions ADD COLUMN {column} REAL")

    def for_assignment(self, assignment_id):
        return self.conn.execute('SELECT * FROM submissions WHERE assignment_id=? ORDER BY position,id',(assignment_id,)).fetchall()

    def add(self, assignment_id, title, due, notes=''):
        if not title.strip(): raise ValueError('Submission title is required')
        datetime.fromisoformat(due)
        with self.conn:
            self.conn.execute('INSERT INTO submissions(assignment_id,title,due,notes,position) VALUES (?,?,?,?,(SELECT COUNT(*) FROM submissions WHERE assignment_id=?))', (assignment_id,title.strip(),due,notes,assignment_id))

    def update(self, submission_id, title, due, status, notes):
        if not title.strip() or status not in STAGE_STATUSES: raise ValueError('Invalid submission')
        datetime.fromisoformat(due)
        with self.conn:
            self.conn.execute('UPDATE submissions SET title=?,due=?,status=?,notes=? WHERE id=?',(title.strip(),due,status,notes,submission_id))

    def save_marks(self, submission_id, earned=None, possible=None, stage_weight=None):
        """Stage weights are percentages of their parent assessment, not of the course."""
        if (earned is None) != (possible is None):
            raise ValueError('Enter both earned and possible marks, or neither')
        if earned is not None and (possible <= 0 or earned < 0 or earned > possible):
            raise ValueError('Earned marks must be between 0 and possible marks')
        if stage_weight is not None and not 0 <= stage_weight <= 100:
            raise ValueError('Stage weight must be between 0 and 100')
        with self.conn:
            self.conn.execute('UPDATE submissions SET marks_earned=?, marks_possible=?, stage_weight=? WHERE id=?',
                              (earned, possible, stage_weight, submission_id))

    def weighted_result(self, assignment_id):
        """Return parent assessment percent only when all stages have grades and weights total 100."""
        stages = self.for_assignment(assignment_id)
        if not stages or any(s['stage_weight'] is None or s['marks_possible'] is None for s in stages):
            return None
        if abs(sum(s['stage_weight'] for s in stages) - 100) > 0.001:
            return None
        return sum(s['stage_weight'] * s['marks_earned'] / s['marks_possible'] for s in stages)

    def delete(self, submission_id):
        with self.conn: self.conn.execute('DELETE FROM submissions WHERE id=?',(submission_id,))

    def progress(self, assignment_id, assignment_status):
        if assignment_status == 'Completed': return 1.0
        stages = self.for_assignment(assignment_id)
        if not stages: return 0.0
        return sum(s['status']=='Completed' for s in stages)/len(stages)
