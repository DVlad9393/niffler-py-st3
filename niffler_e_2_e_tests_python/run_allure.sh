#!/bin/bash

TEST_FILTER=${1:-""}

poetry run pytest ${TEST_FILTER:+-k "$TEST_FILTER"} --alluredir=allure-results --clean-alluredir
allure generate allure-results --clean -o allure-report

mkdir -p allure-report/data/attachments/static/libs

cp -a schemas/templates/static/libs/. allure-report/data/attachments/static/libs

allure open allure-report