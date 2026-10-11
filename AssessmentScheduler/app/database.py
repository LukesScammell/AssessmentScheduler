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
        self.conn.commit()

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
            self.conn.execute('INSERT INTO assignments(course,title,due,notes) VALUES (?,?,?,?)', (course,title,due,notes))

    def update_assignment(self, aid, course, title, due, notes):
        with self.conn:
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
