$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force reports, evidence-local | Out-Null

$result = 1
try {
    docker compose -p task-tracker-tests -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
    $result = $LASTEXITCODE
    docker compose -p task-tracker-tests -f compose.test.yaml logs --no-color |
        Out-File -Encoding utf8 evidence-local/tests.log
} finally {
    docker compose -p task-tracker-tests -f compose.test.yaml down
    if ($LASTEXITCODE -ne 0 -and $result -eq 0) { $result = $LASTEXITCODE }
}
exit $result
