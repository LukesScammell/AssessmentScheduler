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
        self._column('tasks', 'priority', "TEXT NOT NULL DEFAULT 'Medium'")
        self._column('tasks', 'due', "TEXT NOT NULL DEFAULT ''")
        self._column('assignments', 'weight', 'REAL NOT NULL DEFAULT 0')
        self._column('assignments', 'grade', 'REAL')
        self._column('assignments', 'status', "TEXT NOT NULL DEFAULT 'Not Started'")
        self._column('assignments', 'marks_earned', 'REAL')
        self._column('assignments', 'marks_possible', 'REAL')
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS course_notes (course TEXT PRIMARY KEY, content TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS study_sessions (id INTEGER PRIMARY KEY, course TEXT NOT NULL, started TEXT NOT NULL, minutes INTEGER NOT NULL CHECK(minutes > 0));
        CREATE TABLE IF NOT EXISTS study_plan (id INTEGER PRIMARY KEY, course TEXT NOT NULL, title TEXT NOT NULL, start TEXT NOT NULL, minutes INTEGER NOT NULL CHECK(minutes > 0));
        CREATE TABLE IF NOT EXISTS notification_log (assignment_id INTEGER NOT NULL, threshold TEXT NOT NULL, PRIMARY KEY(assignment_id,threshold));
        CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
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

    def add_assignment(self, course, title, due, notes='', status='Not Started'):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(course,))
            cursor=self.conn.execute('INSERT INTO assignments(course,title,due,notes,status) VALUES (?,?,?,?,?)', (course,title,due,notes,status))
            return cursor.lastrowid

    def update_assignment(self, aid, course, title, due, notes, status='Not Started'):
        with self.conn:
            self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)',(course,))
            self.conn.execute('UPDATE assignments SET course=?,title=?,due=?,notes=?,status=? WHERE id=?', (course,title,due,notes,status,aid))

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

    def _column(self, table, name, definition):
        if name not in [r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')]:
            self.conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')

    def set_task_details(self, tid, priority, due):
        if priority not in ('Low','Medium','High','Urgent'): raise ValueError('Invalid priority')
        with self.conn: self.conn.execute('UPDATE tasks SET priority=?, due=? WHERE id=?',(priority,due,tid))

    def course_note(self, course):
        row=self.conn.execute('SELECT content FROM course_notes WHERE course=?',(course,)).fetchone()
        return row['content'] if row else ''

    def save_course_note(self, course, content):
        with self.conn: self.conn.execute('INSERT INTO course_notes(course,content) VALUES (?,?) ON CONFLICT(course) DO UPDATE SET content=excluded.content',(course,content))

    def save_grade(self, aid, weight, grade):
        """Compatibility for older percentage-only callers."""
        if not 0 <= weight <= 100 or (grade is not None and not 0 <= grade <= 100):
            raise ValueError('Grades and weights must be 0–100')
        with self.conn:
            self.conn.execute('UPDATE assignments SET weight=?,grade=?,marks_earned=NULL,marks_possible=NULL WHERE id=?', (weight,grade,aid))

    def save_marks(self, aid, weight, earned=None, possible=None):
        if not 0 <= weight <= 100:
            raise ValueError('Assessment weight must be between 0 and 100')
        if (earned is None) != (possible is None):
            raise ValueError('Both earned and possible marks are required')
        if earned is not None and (possible <= 0 or earned < 0 or earned > possible):
            raise ValueError('Marks must be between 0 and the maximum possible')
        percentage = (earned / possible * 100) if earned is not None else None
        with self.conn:
            self.conn.execute('UPDATE assignments SET weight=?,grade=?,marks_earned=?,marks_possible=? WHERE id=?', (weight,percentage,earned,possible,aid))

    def set_assignment_status(self, aid, status):
        if status not in ('Not Started','In Progress','Completed'):
            raise ValueError('Invalid assessment status')
        with self.conn:
            self.conn.execute('UPDATE assignments SET status=? WHERE id=?', (status,aid))

    def add_plan(self, course, title, start, minutes):
        with self.conn: self.conn.execute('INSERT INTO study_plan(course,title,start,minutes) VALUES (?,?,?,?)',(course,title,start,minutes))

    def plans(self):
        return self.conn.execute('SELECT * FROM study_plan ORDER BY start').fetchall()

    def delete_plan(self, pid):
        with self.conn: self.conn.execute('DELETE FROM study_plan WHERE id=?',(pid,))

    def record_session(self, course, minutes):
        from datetime import datetime
        with self.conn: self.conn.execute('INSERT INTO study_sessions(course,started,minutes) VALUES (?,?,?)',(course,datetime.now().isoformat(timespec='seconds'),minutes))

    def study_summary(self):
        return self.conn.execute('SELECT course,SUM(minutes) AS minutes FROM study_sessions GROUP BY course').fetchall()

    def preference(self, key, default=''):
        row=self.conn.execute('SELECT value FROM preferences WHERE key=?',(key,)).fetchone()
        return row['value'] if row else default

    def set_preference(self, key, value):
        with self.conn: self.conn.execute('INSERT INTO preferences(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))

    def pending_deadlines(self, now):
        from datetime import datetime
        found=[]
        for a in self.assignments():
            if a['status']=='Completed': continue
            hours=(datetime.fromisoformat(a['due'])-now).total_seconds()/3600
            for threshold,limit in [('7 days',168),('3 days',72),('1 day',24),('3 hours',3)]:
                if 0 <= hours <= limit and not self.conn.execute('SELECT 1 FROM notification_log WHERE assignment_id=? AND threshold=?',(a['id'],threshold)).fetchone():
                    found.append((a,threshold))
        return found

    def mark_notified(self, aid, threshold):
        with self.conn: self.conn.execute('INSERT OR IGNORE INTO notification_log VALUES (?,?)',(aid,threshold))

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

    def import_course_guide_assessments(self):
        """Import 2026 course-guide deadlines without changing existing marks or statuses.

        DAT502 report/test components have unknown individual weightings: use zero
        until the student confirms how the 40%/60% assessment weights are divided.
        """
        examples = [
            ('SDV602', 'Assessment 1 — Python project', '2026-08-28T23:59:00', 40, 'Assessment 1: 40%. Course assessment guide states 28 August 2026, 11:59 PM. Timetable also lists an A1 submission on 4 September; confirm with Moodle.'),
            ('SDV602', 'Assessment 2 — Design, implementation and reflection', '2026-11-13T23:59:00', 60, 'Assessment 2: 60%. Course assessment guide states 13 November 2026, 11:59 PM.'),
            ('WEB701', 'Assignment 1 — DESIGN (Milestone 1)', '2026-08-14T12:00:00', 15, 'Design milestone of Assignment 1; contributes 15% of course grade.'),
            ('WEB701', 'Assignment 1 — EVALUATE (Milestone 2)', '2026-09-25T12:00:00', 25, 'Evaluate milestone of Assignment 1; contributes 25% of course grade. Assignment 1 total is 40%.'),
            ('WEB701', 'Assignment 2 — DEVELOP (Milestone 3)', '2026-11-18T12:00:00', 60, 'Final development submission; contributes 60% of course grade.'),
            ('DAT502', 'Assessment 1 — Database design report', '2026-08-28T17:00:00', 0, 'Assessment 1 overall is worth 40% and includes this report and a test on 1 September, 1–3 PM. Individual component weights are not specified; enter weights after confirmation.'),
            ('DAT502', 'Assessment 1 — Database test', '2026-09-01T13:00:00', 0, 'Test 1–3 PM. Part of Assessment 1 (40% combined with report). Individual component weights not specified.'),
            ('DAT502', 'Assessment 2 — Database build report', '2026-11-06T17:00:00', 0, 'Assessment 2 overall is worth 60% and includes this report and a test on 13 November, 9 AM–noon. Individual component weights are not specified.'),
            ('DAT502', 'Assessment 2 — Database test', '2026-11-13T09:00:00', 0, 'Test 9 AM–noon. Part of Assessment 2 (60% combined with report). Individual component weights not specified.'),
        ]
        added = 0
        with self.conn:
            for course, title, due, weight, notes in examples:
                self.conn.execute('INSERT OR IGNORE INTO courses(code) VALUES (?)', (course,))
                day = due[:10]
                # Existing imported starter entries can have different names but the same deadline.
                existing = self.conn.execute('SELECT id,title,due,weight,notes FROM assignments WHERE course=? AND substr(due,1,10)=? ORDER BY id LIMIT 1', (course, day)).fetchone()
                if existing:
                    # Keep all user-edited titles, notes, grades, statuses and existing weights.
                    # Fix only the known old SDV602 placeholder noon deadline.
                    if course == 'SDV602' and day == '2026-11-13' and existing['due'] == '2026-11-13T12:00:00' and 'placeholder' in existing['notes'].lower():
                        self.conn.execute('UPDATE assignments SET due=? WHERE id=?', (due, existing['id']))
                    if weight and existing['weight'] == 0:
                        self.conn.execute('UPDATE assignments SET weight=? WHERE id=?', (weight, existing['id']))
                    continue
                self.conn.execute('INSERT INTO assignments(course,title,due,notes,status,weight) VALUES (?,?,?,?,?,?)', (course,title,due,notes,'Not Started',weight))
                added += 1
        return added
