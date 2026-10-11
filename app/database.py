import os
import sqlite3
from pathlib import Path

APP_DIR = Path(os.getenv('LOCALAPPDATA') or (Path.home() / '.local' / 'share')) / 'AssessmentScheduler'
DB_PATH = APP_DIR / 'assessments.db'

class Database:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY, course TEXT NOT NULL, title TEXT NOT NULL,
            due TEXT NOT NULL, notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
            title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'To Do'
                CHECK(status IN ('To Do','In Progress','Completed'))
        );
        ''')
        self.conn.execute('CREATE TABLE IF NOT EXISTS courses (code TEXT PRIMARY KEY)')
        for code in ('NET502','WEB701','DAT502','SDV602'):
            self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(code,))
        self.conn.execute('INSERT OR IGNORE INTO courses(code) SELECT DISTINCT course FROM assignments')
        self.conn.commit()

    def courses(self):
        return [r['code'] for r in self.conn.execute('SELECT code FROM courses ORDER BY code')]

    def add_course(self,code):
        with self.conn: self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(code,))

    def assignments(self):
        return self.conn.execute('''SELECT a.*, COUNT(t.id) total,
          COALESCE(SUM(CASE WHEN t.status='Completed' THEN 1 ELSE 0 END),0) completed
          FROM assignments a LEFT JOIN tasks t ON t.assignment_id=a.id
          GROUP BY a.id ORDER BY a.due, a.id''').fetchall()

    def assignment(self, aid):
        return self.conn.execute('SELECT * FROM assignments WHERE id=?', (aid,)).fetchone()

    def tasks(self, aid=None):
        if aid is None:
            return self.conn.execute('''SELECT t.*, a.course, a.title assignment_title FROM tasks t
                JOIN assignments a ON a.id=t.assignment_id ORDER BY t.id''').fetchall()
        return self.conn.execute('SELECT * FROM tasks WHERE assignment_id=? ORDER BY id', (aid,)).fetchall()

    def add_assignment(self, course, title, due, notes=''):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(course,))
            self.conn.execute('INSERT INTO assignments(course,title,due,notes) VALUES (?,?,?,?)', (course,title,due,notes))

    def update_assignment(self, aid, course, title, due, notes):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(course,))
            self.conn.execute('UPDATE assignments SET course=?,title=?,due=?,notes=? WHERE id=?', (course,title,due,notes,aid))

    def delete_assignment(self, aid):
        with self.conn:
            self.conn.execute('DELETE FROM assignments WHERE id=?', (aid,))

    def add_task(self, aid, title):
        with self.conn:
            self.conn.execute('INSERT INTO tasks(assignment_id,title) VALUES (?,?)', (aid,title))

    def set_status(self, tid, status):
        if status not in ('To Do','In Progress','Completed'):
            return
        with self.conn:
            self.conn.execute('UPDATE tasks SET status=? WHERE id=?', (status,tid))

    def delete_task(self, tid):
        with self.conn:
            self.conn.execute('DELETE FROM tasks WHERE id=?', (tid,))

    def import_starter_assessments(self):
        """Optional personal sample data; skip matching records so imports are repeatable."""
        examples = [
            ('NET502', 'Scenario-based theory', '2026-10-19T09:00:00', 'Theory assessment.'),
            ('DAT502', 'Database report', '2026-11-06T17:00:00', 'Report submission.'),
            ('NET502', 'Practical project and report', '2026-11-11T11:00:00', 'Practical project and report submission.'),
            ('SDV602', 'Assessment 2 — Design, implementation and reflection', '2026-11-13T12:00:00', 'Due 13 November 2026. Exact submission time was not supplied; 12:00 is a calendar placeholder. Confirm the actual deadline.'),
            ('DAT502', 'Database test', '2026-11-13T09:00:00', 'Test runs 9:00 AM–12:00 PM.'),
            ('WEB701', 'Development assessment', '2026-11-18T12:00:00', 'Development submission, Wednesday at midday.'),
        ]
        added = 0
        with self.conn:
            for course, title, due, notes in examples:
                self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(course,))
                exists = self.conn.execute('SELECT 1 FROM assignments WHERE course=? AND title=? AND due=?', (course,title,due)).fetchone()
                if not exists:
                    self.conn.execute('INSERT INTO assignments(course,title,due,notes) VALUES (?,?,?,?)', (course,title,due,notes))
                    added += 1
        return added
