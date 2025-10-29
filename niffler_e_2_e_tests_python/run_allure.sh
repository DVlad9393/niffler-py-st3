#!/usr/bin/env bash
set -u

TEST_FILTER=""
USE_MOCK=0
WORKERS=""
DIST="loadscope"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mock) USE_MOCK=1; shift;;
    --workers)
      WORKERS="$2"; shift 2;;
    --dist)
      DIST="$2"; shift 2;;
    -h|--help)
      cat <<EOF
Usage: ./run_allure.sh [TEST_FILTER] [--mock] [--workers N|auto] [--dist loadscope|loadfile|no]

Examples:
  ./run_allure.sh
  ./run_allure.sh api
  ./run_allure.sh --mock
  ./run_allure.sh api --workers auto
  ./run_allure.sh --workers 4 --dist loadfile
EOF
      exit 0;;
    *) TEST_FILTER="$1"; shift;;
  esac
done

PYTEST_ARGS=(--alluredir=allure-results --clean-alluredir)
[[ -n "$TEST_FILTER" ]] && PYTEST_ARGS+=(-k "$TEST_FILTER")
[[ $USE_MOCK -eq 1 ]] && PYTEST_ARGS+=(--mock)

if [[ -n "$WORKERS" ]]; then
  PYTEST_ARGS+=(-n "$WORKERS" --dist "$DIST")
fi

set +e
poetry run pytest "${PYTEST_ARGS[@]}"
status=$?
set -e

allure generate allure-results --clean -o allure-report

mkdir -p allure-report/data/attachments/static/libs
cp -a schemas/templates/static/libs/. allure-report/data/attachments/static/libs || true

if [[ -z "${CI:-}" ]]; then
  allure open allure-report || true
fi
exit $status