# Assessment Scheduler

An open-source, offline-first Windows desktop app for managing assessment deadlines and tasks.

## Version 1.0.0 features

- Dashboard with upcoming deadlines and overall progress
- Kanban board with drag-and-drop task status changes
- Interactive monthly calendar highlighting due dates; select a day to open its assessments
- Create, edit and delete assignments and tasks
- Automatic task-based progress bars across the app
- Local SQLite database stored outside the installation directory
- Dark interface

## Run from source (Windows)

Requires Python 3.13.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Publish an installer using GitHub Actions

1. Create a **public** GitHub repository, for example `AssessmentScheduler`.
2. Upload/push all files including `.github/workflows/release.yml`.
3. In repository Settings > Actions > General, ensure workflows are enabled and have permission to create releases (workflow declares `contents: write`; repository policy must allow it).
4. Create and push a release tag:

```powershell
git init
git add .
git commit -m "Release version 1.0.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AssessmentScheduler.git
git push -u origin main
git tag v1.0.0
git push origin v1.0.0
```

5. Wait for **Actions > Windows release** to finish. The workflow creates a downloadable installer on **Releases**. The Actions run also provides an installer artifact.

For later updates, change code, commit, and push a new tag like `v1.1.0`. The installer uses the same app ID and installation directory, so it updates application files. The user database is preserved in `%LOCALAPPDATA%\AssessmentScheduler\assessments.db`.

**Important:** Back up user data before any future database schema migrations. The current version does not include automatic in-app update checks, notifications, or automatic backups. GitHub Releases provides manual downloadable updates.

## Privacy and sample data

No personal assessments are committed to the repository. Every user starts with an empty database and can add their own courses and tasks. No login or internet connection is needed for daily use.

## Windows installer security

The executable is unsigned. Windows SmartScreen may warn users when downloading a new, unsigned app. Code signing can be added in a later release.

## License

MIT.

## v1.1.0 — Dashboard refresh and optional assessment import

The dashboard has refreshed styling, three summary cards, course-coloured assignment cards, and an overall progress bar. The Dashboard includes **Import my 2026 assessment dates (6)**, an optional, confirmation-based import of NET502, DAT502, SDV602, and WEB701 deadlines. The import does not erase existing data and skips exact matching course/title/date records.

**Important:** The SDV602 deadline supplied was 13 November 2026 without a time. The import uses 12:00 as an editable calendar placeholder, clearly labelled in the assignment notes. Confirm and correct it before relying on reminders.

### Updating from v1.0.0

Keep the same installation directory and installer AppId. Application data remains in the per-user `AssessmentScheduler/assessments.db` folder under LOCALAPPDATA, separate from installed program files. Back up this file before updating. The import is optional; existing users can select it from the Dashboard.

### Publish v1.1.0

Commit and push the updated project to `main`. After testing a manually triggered Windows workflow build, tag the updated commit `v1.1.0` and push the tag to trigger the GitHub Release workflow.
