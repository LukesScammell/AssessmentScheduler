# Assessment Scheduler

Offline-first Windows desktop app for managing university courses, assessments and study time.

## Features (v1.3.0)

- Separate course pages, notes, assignments and completion progress
- Task checklist with Kanban statuses, priority and optional due dates
- Calendar, upcoming deadlines, and deadline notifications while the app is open
- Pomodoro focus timer with completed sessions recorded per course
- Weekly study planner
- Assessment grade and weight tracker, with current weighted average
- Appearance settings: dark/light mode and four accent colours
- Backup and restore of the full SQLite database
- Existing data preserved when upgrading from previous versions

**Important:** Deadline alerts require the app to be running. They are not scheduled Windows notifications when the app is closed. Focus sessions are saved after the countdown completes; pauses and resets are not logged. Grades are entered as percentages, and ungraded assessments are excluded from the weighted average. Backup restore replaces all current data and closes the application so you can reopen it. Create a backup before restoring.

## Run locally

Requires Python 3.13 and Windows for the packaged installer.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Build a Windows installer

The GitHub Actions workflow is in `.github/workflows/release.yml`. Run it manually on `main` to test before tagging. It reads the application version from `main.py` for manual builds. After testing, publish with `git tag v1.3.0` and `git push origin v1.3.0`.

The Inno Setup `AppId` is intentionally unchanged so installing a new version updates the existing app rather than creating a second application. Data is stored in `%LOCALAPPDATA%\AssessmentScheduler\assessments.db`, outside the installation directory.
