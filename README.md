# Assessment Scheduler

Offline-first Windows desktop app for managing university courses, assessments and study time.

## Features (v1.7.0)

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

### v1.4.0: Completed assessments and marks
When adding an assessment, choose its status (including **Completed** for past work), enter its historical deadline, and optionally enter its assessment weighting and marks earned / marks possible. You can also leave the grade blank while waiting for results. Existing assessments can be edited to change their status, and their marks can be entered from **Grades** or **Set grade** on the class page.

For example, **58/70** is **82.86%**. At a **40%** course weight, that earns **33.14 percentage points** toward the final course total. Previously stored percentage-only grades are retained until you explicitly replace them with marks.

**Upgrade safety:** Use **Settings → Back up all app data** before installing a test build. The SQLite database is stored outside the application installation folder and the Inno Setup AppId is unchanged.

### Submission stages (v1.7.0)
Open a class, select **Submissions & tasks** for an assessment, then add stages such as Design, Review and Final Submission. Each stage has its own date, status and notes. Each stage can store its own earned/possible marks and an optional confirmed weighting within the parent assessment. The parent retains its course weighting. A stage result does not automatically change the parent grade. If all stage weights total 100% and all stages are graded, you can explicitly apply the calculated parent grade. WEB701 Design (15%), Evaluate (25%), and Develop (60%) are separately course-weighted graded milestones, not three equally weighted stages. DAT502 reports/tests belong to their respective 40%/60% assessments, but the course guide does not specify their internal mark splits.

The SDV602 course timetable lists A1 Design Specification (7 August), A1 Review (20 August), and A1 Submission (4 September), while its assessment table lists the overall Assessment 1 deadline as 28 August. Verify individual stage deadlines in Moodle before entering them.
