#!/usr/bin/env bash
set -u  # (без -e)

TEST_FILTER=""
USE_MOCK=0

for arg in "$@"; do
  if [[ "$arg" == "--mock" ]]; then
    USE_MOCK=1
  else
    TEST_FILTER="$arg"
  fi
done

PYTEST_ARGS=(--alluredir=allure-results --clean-alluredir)
[[ -n "$TEST_FILTER" ]] && PYTEST_ARGS+=(-k "$TEST_FILTER")
[[ $USE_MOCK -eq 1 ]] && PYTEST_ARGS+=(--mock)

set +e
poetry run pytest "${PYTEST_ARGS[@]}"
status=$?
set -e

allure generate allure-results --clean -o allure-report

mkdir -p allure-report/data/attachments/static/libs
cp -a schemas/templates/static/libs/. allure-report/data/attachments/static/libs || true

allure open allure-report || true

exit $status