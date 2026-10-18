# Verification before handoff

The package was prepared against upstream commit e6e416f, whose only file was
`.gitignore`. It has not been pushed to the team's GitHub repository.

Checks completed in the preparation environment:

- 31 unit cases passed using Python 3.12.
- 52 cases passed against a PostgreSQL WASM engine through a local protocol
  adapter, with 100% statement coverage for the application source. One direct
  database-constraint case was excluded because the adapter does not handle
  that error/connection sequence correctly. This is an auxiliary check, not
  evidence of a full PostgreSQL 16 or Docker run.
- Python lint and compilation passed; the shell runner passed its syntax check.
- Both Compose files parsed as YAML; PostgreSQL has no published host port.

Docker and PowerShell are not installed in this preparation environment.
The Docker builds, PostgreSQL 16 container execution, Windows runner and named
volume persistence must be verified on the student's machine. Run the full
53-case suite using `scripts/test.ps1` and retain the resulting reports. Do not
mark the database integration work verified solely from the auxiliary results.

The final Level 4 evidence must additionally show the suite running on the
Test/Staging Droplet through the team's workflow, followed by Playwright and
the production deployment gate owned by the relevant team members.

## Local Docker verification on 18 October 2026

The complete suite passed against PostgreSQL 16.15 in Docker:
53 tests passed, comprising 31 unit cases and 22 integration cases.
Application statement coverage was 100% across 129 statements.
The test container exited with code 0.

Reports are stored in reports/ and raw test logs in evidence-local/tests.log.
