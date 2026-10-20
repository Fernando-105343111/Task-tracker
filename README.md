# Task tracker backend and PostgreSQL tests

This branch supplies the backend, PostgreSQL schema, Docker Compose setup,
unit tests and integration tests for SWE4-10, SWE4-12 and SWE4-13. It does not
configure GitHub Actions, public server access, monitoring or Playwright.
The home page is an integration placeholder; Isuri will build the task interface
in `app/templates/index.html` and can put browser assets in `app/static/`.

## Run locally on Windows

Install Git and Docker Desktop. Start Docker Desktop with Linux containers.
You do not need to install Python or PostgreSQL on Windows for these commands.
Run all commands in PowerShell from the repository root.

```powershell
git --version
docker version
docker compose version
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-local.ps1
$env:COMMIT_SHA = 'local-working-tree'
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
docker compose ps
Start-Process 'http://localhost:8080'
Invoke-RestMethod 'http://localhost:8080/health'
Invoke-RestMethod 'http://localhost:8080/ready'
```

`setup-local.ps1` generates a random local database password in `.env`.
It preserves an existing `.env`. The file is excluded from Git and the image.
Do not print or commit it. PostgreSQL has no published host port.
The application binds to localhost:8080 by default. The application image runs
Gunicorn as a non-root user. Compose waits for the database health check before
starting the application. Startup creates the initial schema and applies the
rerunnable additive SQL migration in `app/migrations/` without removing existing
records. Existing tasks receive priority `Medium` and no due date. Re-running
startup retains saved values. This is a specific upgrade, not a general-purpose
migration framework.

## Verify task operations and persistence

```powershell
New-Item -ItemType Directory -Force evidence-local | Out-Null
Start-Transcript -Path .\evidence-local\manual-checks.txt
$base = 'http://localhost:8080'
$created = Invoke-RestMethod -Method Post -Uri "$base/api/tasks" -ContentType 'application/json' -Body (@{title='Backend verification';description='Verify PostgreSQL persistence';status='To Do'} | ConvertTo-Json)
$taskId = $created.id
$created | ConvertTo-Json
Invoke-RestMethod "$base/api/tasks/$taskId"
Invoke-RestMethod -Method Patch -Uri "$base/api/tasks/$taskId" -ContentType 'application/json' -Body (@{status='In Progress'} | ConvertTo-Json)
docker compose exec -T db psql -U tasktracker -d tasktracker -c 'SELECT id, title, status FROM tasks;'
docker compose down
docker compose up -d --wait --wait-timeout 120
$saved = Invoke-RestMethod "$base/api/tasks/$taskId"
if ($saved.title -ne 'Backend verification' -or $saved.status -ne 'In Progress') { throw 'Persistence verification failed' }
$saved | ConvertTo-Json
Invoke-RestMethod -Method Patch -Uri "$base/api/tasks/$taskId" -ContentType 'application/json' -Body (@{status='Done'} | ConvertTo-Json)
Invoke-WebRequest -UseBasicParsing -Method Delete -Uri "$base/api/tasks/$taskId" | Select-Object StatusCode
Invoke-RestMethod "$base/api/tasks"
Stop-Transcript
```

Expected: POST returns a generated ID and `To Do`; GET returns the saved values;
PATCH stores the new status; the task survives `down` followed by `up`; DELETE
returns HTTP 204. Do not add `-v` to `docker compose down` when checking persistence:
that option deletes the database volume. Screenshots and logs from your own run
are the project evidence.

## Run the complete unit and integration suite

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
if ($LASTEXITCODE -ne 0) { throw 'Tests failed: do not hand this version to the deployment pipeline' }
Start-Process .\reports\htmlcov\index.html
```

The current suite collects 117 cases: 61 unit cases and 56 PostgreSQL integration
cases. Parameterised cases count individually. All must pass; application statement
coverage must be at least 80%. The script preserves the test exit status even after
cleaning up the test containers. Keep these outputs:

- `reports/junit.xml`: machine-readable test results.
- `reports/coverage.xml`: coverage for pipeline tools.
- `reports/htmlcov/index.html`: readable coverage report.
- `evidence-local/tests.log`: raw test service logs.

The test Compose file is independent of the application Compose file. Its
PostgreSQL database is named `tasktracker_test` and uses temporary container
storage. It does not mount the application's persistent volume or publish a port.
Each pytest run also gets a random schema that is removed after testing. The
fixture refuses database names that do not end with `_test`. Never supply production
credentials to the test command. Missing PostgreSQL configuration fails the
integration tests rather than silently skipping them or substituting SQLite.

Integration coverage includes create/list/retrieve/update/delete, persistence
across Flask instances, invalid input, invalid updates, missing IDs, malformed
JSON, parameterised SQL inputs, database constraints and idempotent schema setup.
The manual container restart check above verifies persistence across containers.

## Frontend contract for Isuri

Use same-origin requests; no separate frontend server or CORS configuration is
required. Keep the visible commit element `id="commit-id"` in the HTML template.
Jinja receives the variable `commit_sha`.

| Method | Path | Input | Success result |
| --- | --- | --- | --- |
| GET | `/api/tasks` | None | 200; JSON array of task objects |
| POST | `/api/tasks` | JSON title, optional description, status, priority and dueDate | 201; created task; Location header |
| GET | `/api/tasks/<id>` | None | 200; one task |
| PATCH | `/api/tasks/<id>` | JSON containing only status | 200; updated task |
| PUT | `/api/tasks/<id>` | JSON title, description, status; optional priority and dueDate | 200; updated task |
| PUT | `/api/tasks/` | Same fields plus a positive integer id | 200; updated task |
| DELETE | `/api/tasks/<id>` | None | 204; empty response |
| GET | `/health` | None | 200; application status and commit |
| GET | `/ready` | None | 200 when PostgreSQL responds; 503 otherwise |
| GET | `/version` | None | 200; commit identifier |

Example task: `{"id":1,"title":"Review brief","description":"Check diagram","status":"To Do","priority":"Medium","dueDate":null}`.
Valid statuses are exactly `To Do`, `In Progress` and `Done`. Titles must contain
1-200 characters after trimming. Descriptions must be strings of at most 2000
characters. Invalid values return 400 with `{"error":"..."}`; missing IDs return
404; a non-JSON request body returns 415. Task creation defaults to an empty
description, status `To Do`, priority `Medium` and no due date. Priority must be
exactly `Low`, `Medium` or `High`. `dueDate` must be a real calendar date in
`YYYY-MM-DD` form, null or an empty string. API responses always use `dueDate`
and return null when no date is set. Input also accepts `due_date` as an alias;
do not send both date field names in one request. Past dates are allowed.

PATCH still changes status only and preserves the other fields. PUT requires
title, description and status. Optional priority/date values are preserved if
omitted; explicit null or an empty string clears the date. A body `id` on the
resource URL must match the URL. Unknown IDs return 404 rather than creating
a task. The collection endpoint accepts both `/api/tasks` and `/api/tasks/`
and requires a positive integer `id` in the JSON body.

```javascript
await fetch(`/api/tasks/${editingTaskId}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title, description, status, priority, dueDate: dueDate || null
  })
});
```

See `TASK-EDITING-UPDATE.md` for the database backup, update and verification
commands. Do not delete the database volume to introduce the new columns.

## Pipeline handoff for Siddharth

Build and publish the runtime target from the source commit being released:

```sh
docker build --target runtime --build-arg COMMIT_SHA="$GITHUB_SHA" -t "$APP_IMAGE" .
```

`APP_IMAGE` is the GHCR reference selected by the pipeline owner. Do not rebuild
the image on a deployment server. Supply its tested digest through `APP_IMAGE`
and use `docker compose up -d --no-build --wait --wait-timeout 120` after pulling.
The database password belongs in each server's own `.env`, not in the image.

On the TEST/STAGING Droplet, check out the same source commit and execute:

```sh
sh scripts/test.sh
```

The script runs unit/integration tests in a test target built from that commit.
Playwright must separately test the deployed runtime image before promoting its
digest to production. Run one release at a time, or set unique `TASK_TEST_PROJECT`
values and use separate checkout directories so report paths cannot overlap.
The workflow must propagate the test command's exit code and collect the report
paths above. These files do not themselves implement the workflow gate.

## Deployment handoff for Fernando

Use the same tested runtime image digest, a separate production database volume
and separate credentials. `APP_BIND=127.0.0.1` is intentional for local use; the
server owner must choose the application binding/reverse proxy and firewall rules
for public access. Do not run the local verification commands against a public
production endpoint unless the team has arranged the verification task data.

The provided proof shows DigitalOcean host monitoring. It does not show HTTP
request instrumentation or Prometheus/Grafana. Monitoring remains Fernando's task;
the application does not yet expose a `/metrics` endpoint.

## Completion evidence

Capture the actual branch/commit, both healthy application services, manual task
operations, PostgreSQL SELECT output, preserved task after restart, a full passing
test run and its coverage percentage. For final project evidence, also retain the
test results when Siddharth runs this suite on the Test/Staging Droplet.
Do not use another environment's results as proof that your laptop or server passed.

## Official references

- Flask testing: https://flask.palletsprojects.com/en/stable/testing/
- Psycopg parameter binding: https://www.psycopg.org/psycopg3/docs/basic/params.html
- Compose readiness: https://docs.docker.com/compose/how-tos/startup-order/
- pytest-cov configuration: https://pytest-cov.readthedocs.io/en/stable/config.html
