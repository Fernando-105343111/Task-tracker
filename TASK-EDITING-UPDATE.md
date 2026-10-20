# Task editing update

This update adds full task editing, priority and due dates to the existing Flask
backend. It changes backend files and tests only; it preserves the frontend owner's
HTML, CSS and JavaScript. Apply it to feature/backend-compose-tests, then merge that
branch's new commit into integration/frontend-backend so the frontend can call PUT.

## API

Preferred endpoint: `PUT /api/tasks/<id>`.

```json
{
  "title": "Updated task",
  "description": "Updated description",
  "status": "In Progress",
  "priority": "High",
  "dueDate": "2026-12-01"
}
```

Returns HTTP 200 with the updated fields and original task ID. The collection
endpoint `PUT /api/tasks/` is also supported: include `"id": 1` in the JSON body.
The endpoint must identify a specific task; it never updates all tasks.

Title, description and status are required for PUT. Omitting priority or dueDate
preserves its saved value. Priority accepts exactly Low, Medium and High. A missing
priority during creation defaults to Medium. A due date must be a real YYYY-MM-DD
calendar date. Set dueDate to null or an empty string to remove the date. GET,
POST, PUT and PATCH responses include priority and dueDate. The input alias due_date
is accepted, but responses use dueDate. Sending both aliases returns 400.

Existing POST/GET/PATCH/DELETE routes continue to work. Status-only PATCH preserves
title, description, priority and due date. Unknown IDs return 404. Invalid values
return 400 and leave the saved record unchanged.

## Apply the patch

Save `task-editing-update.zip` in Downloads and run in Windows PowerShell:

```powershell
$bundleDir = Join-Path $env:USERPROFILE 'Downloads\task-editing-update'
Expand-Archive -LiteralPath (Join-Path $env:USERPROFILE 'Downloads\task-editing-update.zip') -DestinationPath $bundleDir -Force
Set-Location 'D:\SWE40006\Task-tracker'
git status --short
```

Continue from a clean working tree. Keep unrelated changes before switching branches.

```powershell
git switch feature/backend-compose-tests
git pull --ff-only origin feature/backend-compose-tests
git apply --check "$bundleDir\task-editing-update.patch"
```

If the check fails, retain the error and adapt the patch to the changed code; do not
force-copy files over teammates' changes. This patch was prepared against b8b4e44.

```powershell
git apply "$bundleDir\task-editing-update.patch"
```

## Back up the existing local database

With the old application/database still running and before rebuilding:

```powershell
New-Item -ItemType Directory -Force .\evidence-local\backups | Out-Null
$backupPath = ".\evidence-local\backups\before-task-editing-$(Get-Date -Format 'yyyyMMdd-HHmmss').dump"
docker compose exec -T db pg_dump -U tasktracker -d tasktracker -Fc -f /tmp/before-task-editing.dump
if ($LASTEXITCODE -ne 0) { throw 'Database backup failed' }
docker compose cp db:/tmp/before-task-editing.dump $backupPath
if ($LASTEXITCODE -ne 0) { throw 'Database backup copy failed' }
```

These commands use the project's existing default local database/user names. If
your .env changes those names, use your configured values. Do not print or share
the database password. The backup remains outside Git under evidence-local/.

## Upgrade and test locally

The new image automatically runs the additive migration through init-db before
Gunicorn starts. Do not delete the volume or run docker compose down -v.

```powershell
$env:COMMIT_SHA = 'local-working-tree'
docker compose up --build -d --wait --wait-timeout 120
if ($LASTEXITCODE -ne 0) { throw 'Application upgrade failed; inspect docker compose logs web' }
Invoke-RestMethod 'http://localhost:8080/ready'
Invoke-RestMethod 'http://localhost:8080/api/tasks' | ConvertTo-Json
```

Old tasks must retain their IDs, titles, descriptions and statuses. They receive
priority Medium and dueDate null. Re-running init-db must preserve subsequent
priority/date changes. Schema creation and the migration run in one transaction.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; keep the logs and do not push as passing' }
Start-Process .\reports\htmlcov\index.html
```

The suite now collects 117 cases: 61 unit and 56 PostgreSQL integration cases.
All must pass; the coverage gate remains 80%. Reports are in reports/ and raw logs
in evidence-local/tests.log. Save the actual test summary and coverage screenshot.

## Verify PUT and persistence

```powershell
$base = 'http://localhost:8080'
$created = Invoke-RestMethod -Method Post -Uri "$base/api/tasks" -ContentType 'application/json' -Body (@{title='Edit verification';description='Before edit';status='To Do';priority='Low';dueDate='2026-12-01'} | ConvertTo-Json)
$taskId = $created.id
$updated = Invoke-RestMethod -Method Put -Uri "$base/api/tasks/$taskId" -ContentType 'application/json' -Body (@{title='Edited task';description='After edit';status='In Progress';priority='High';dueDate='2027-01-01'} | ConvertTo-Json)
$updated | ConvertTo-Json
docker compose restart web
```

After the web service is healthy (check docker compose ps), verify the saved edit:

```powershell
$saved = Invoke-RestMethod "$base/api/tasks/$taskId"
$saved | ConvertTo-Json
if ($saved.title -ne 'Edited task' -or $saved.priority -ne 'High' -or $saved.dueDate -ne '2027-01-01') { throw 'Edited values were not retained' }
Invoke-RestMethod -Method Delete -Uri "$base/api/tasks/$taskId"
```

## Commit and push after tests pass

```powershell
git add app/db.py app/routes.py app/validation.py app/migrations/001_task_details.sql tests/unit/test_validation.py tests/unit/test_task_details.py tests/integration/test_tasks.py tests/integration/test_task_editing.py README.md TASK-EDITING-UPDATE.md
git diff --cached --check
git diff --cached --stat
git commit -m "Add full task editing, priority and due dates"
git push origin feature/backend-compose-tests
```

This updates existing backend PR #2. Then the frontend owner can merge the backend
branch into their integration/frontend-backend branch and connect the Edit action.
The original frontend prototype branch is not the latest integration branch.

## Preparation checks and limitations

The preparation environment passed 61 unit cases and an auxiliary 116-case run
through a PostgreSQL WASM protocol adapter with 100% application statement coverage.
One original direct database-constraint case was excluded due to the adapter's
error/connection handling. The complete 117-case PostgreSQL 16 Docker suite must
be run on the student's laptop or Test/Staging server before reporting it as passing.
Docker is unavailable in the preparation environment. No changes have been pushed
from that environment.

The package was also checked against the latest integration branch: its four
existing backend files match the original backend base, so this patch can be
combined without replacing the integrated frontend template or static assets.
