#!/bin/sh
# Run on the TEST/STAGING server from the matching source commit.
set -eu
cd "$(dirname "$0")/.."
mkdir -p reports evidence-local
project="${TASK_TEST_PROJECT:-task-tracker-tests}"
cleanup() {
    result=$?
    trap - EXIT
    docker compose -p "$project" -f compose.test.yaml logs --no-color > evidence-local/tests.log 2>&1 || true
    docker compose -p "$project" -f compose.test.yaml down || {
        [ "$result" -ne 0 ] || result=1
    }
    exit "$result"
}
trap cleanup EXIT
docker compose -p "$project" -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
