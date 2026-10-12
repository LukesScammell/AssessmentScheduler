## v1.6.0
- Assessment cards show 100% when status is Completed, regardless of subtasks.
- Class and dashboard progress bars now count completed assessments.
- Subtask completion remains a separate metric.
- Keeps the same installer AppId and existing SQLite data.

# Changelog

## v1.3.0
- Task priorities (Low, Medium, High, Urgent) and optional task due dates.
- Deadline notifications while the app is running (system tray notifications).
- Pomodoro focus timer with study time recorded by class.
- SQLite backup and restore with integrity checking and app restart after restore.
- Light/dark appearance and accent colour settings.
- Persistent class notes on each course page.
- Study planner with weekly grouping and session duration.
- Assessment weights and marks, with weighted averages by class.
- Additive database migration preserves v1.2.0 data; unchanged installer AppId.
- GitHub Actions manual build reads version from main.py.

## v1.2.0
- Individual course pages, class navigation, course filters.

## v1.4.0 — Completed assessments and raw marks
- Enter assessment results as marks earned / marks possible (e.g. 58/70) and calculate the percentage automatically.
- Preserve older percentage-only grades when upgrading from v1.3.0.
- Add previously completed assessments with historical due dates, optional grades and assessment weights.
- Mark assessments Not Started, In Progress or Completed, independently of whether the grade is available.
- Separate completed assessments on class pages and exclude them from upcoming deadlines and reminders.
- Show weighted course averages and percentage points earned toward the course total.
- Keep the same installer AppId and migrate the existing SQLite database without deleting records.

## v1.7.0 — Submission stages and modular architecture
- Multiple submission stages per assessment with independent due dates, statuses, and notes.
- Assessment progress reflects completed stages, or 100% when the overall assessment is completed.
- Reusable dialogs, widgets, theme and submission manager extracted from main.py.
- Existing database and course grades are preserved through additive SQLite migrations.
