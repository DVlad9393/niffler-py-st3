# Собрать докер контейнеры:
cd niffler-py-st3
bash docker-compose-dev.sh

# иногда необходимо почистить кэш gradle если есть проблемы со сборкой
./gradlew clean build --refresh-dependencies

Полное очищение кэшей
rm -rf ~/.gradle/caches ~/.gradle/daemon ~/.m2/repository

# если необходимо настроить JAVA то выполнить команду:
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH="$JAVA_HOME/bin:$PATH"
java -version
rm -rf ~/.gradle/caches
java -version
echo $JAVA_HOME
bash docker-compose-dev.sh

# Запустить тесты с allure и удалением предыдущих результатов:
cd niffler_e_2_e_tests_python
poetry run pytest -k "test_archive_category_db" --alluredir allure-results --clean-alluredir

# В проекте добавлен bash-скрипт run_allure.sh
# Баш скрипт позволяет сформировать отчет allure c вложениями запросов и ответов API в шагах, оформленных с CSS стилями.

# Выполнить один раз
chmod +x run_allure.sh # сделать скрипт исполняемым

# Доступные команды bash скрипта: 
 - Все тесты: ./run_allure.sh
 - Один тест: ./run_allure.sh test_add_duplicate_category_api
 - Тесты по группе: ./run_allure.sh api
 - Запуск тестов с параллелизацией автоматическое определение воркеров: ./run_allure.sh api --workers auto
 - Запуск тестов с параллелизацией ручное определение воркеров и настройка loadfile: ./run_allure.sh --workers 4 --dist loadfile
 - Запуск тестов с параллелизацией + headless режим в браузере PW_HEADLESS=1 ./run_allure.sh --workers 8 --dist loadfile
 Перед выполнением скрипта собрать докер контейнер с мок-объектом в пути (grpc niffler_e_2_e_tests_python/grpc_tests/docker-compose.mock.yml)
 - Тесты по группе c конфигом --mock (запуск для grpc тестов с данными мок объекта): ./run_allure.sh grpc --mock

# Открыть отчёт:
allure serve

Запуск линтеров:
# without fix
poetry run ruff check .  
# with fix
poetry run ruff check . --fix 
# format
poetry run ruff format . 
