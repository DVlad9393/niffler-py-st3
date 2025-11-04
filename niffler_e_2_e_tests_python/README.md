# 🧩 Проект автоматизированного тестирования приложения **Niffler**
<img src="assets/niffler-with-a-coin.png" width="300">

<details>
<summary>Схема проекта Niffler 2.0</summary>
<br>
<img src="assets/niffler-diagram.png" width="600">
</details>

<details>
<summary>Главная страница UI интерфейса</summary>
<br>
<p align="center">
  <code><img width="75%" title="main_page" src="assets/main_page.PNG"></code>
</p>
</details>

---

## 🚀 Быстрый старт
Для запуска проекта необходимо установить docker и Java 21
### 💻 Для macOS / Linux

```bash
# Клонировать репозиторий
git clone https://github.com/DVlad9393/niffler-py-st3.git
cd niffler-py-st3

# Установить Poetry и зависимости
pip install poetry
poetry install --no-root

# Установить браузеры Playwright
poetry run playwright install --with-deps

# Установить Allure CLI
brew install allure        # macOS
# или через npm
npm install -g allure-commandline --save-dev

# Собрать и запустить систему Niffler
bash docker-compose-dev.sh
```

---

### 🪟 Для Windows

```bash
# Клонировать репозиторий
git clone https://github.com/<your-username>/niffler-py-st3.git
cd niffler-py-st3

# Установить Poetry
pip install poetry
poetry install --no-root

# Установить Playwright и браузеры
poetry run playwright install

# Установить Allure CLI (через Scoop или npm)
scoop install allure       # если установлен Scoop
# или
npm install -g allure-commandline --save-dev

# Запуск приложения Niffler (через Git Bash или PowerShell)
bash docker-compose-dev.sh
```

💡 *На Windows обязательно использовать терминал Git Bash или PowerShell с поддержкой bash-команд.*

---

## ⚙️ Технологии проекта

<p align="left">
  <code><img width="5%" title="python" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg"></code>
  <code><img width="5%" title="pytest" src="https://github.com/MDN78/MDN78/blob/main/assets/pytest.png"></code>
  <code><img width="5%" title="playwright" src="https://playwright.dev/img/playwright-logo.svg"></code>
  <code><img width="5%" title="allure" src="https://github.com/MDN78/MDN78/blob/main/assets/allure_report.png"></code>
  <code><img width="5%" title="kafka" src="assets/kafka.svg"></code>
  <code><img width="5%" title="postgres" src="assets/PostgresSQL.svg"></code>
  <code><img width="5%" title="poetry" src="https://python-poetry.org/images/logo-origami.svg"></code>
  <code><img width="5%" title="github" src="https://github.com/MDN78/MDN78/blob/main/assets/github.png"></code>
  <code><img width="5%" title="pycharm" src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pycharm/pycharm-original.svg"></code>
  <code><img width="5%" title="Requests" src="assets/Requests_Python_Logo.png"></code>
  <code><img width="5%" title="SQLAlchemy" src="assets/SQLAlchemy.svg"></code>
  <code><img width="5%" title="Pydantic" src="assets/Pydantic--Streamline-Simple-Icons.svg"></code>
  <code><img width="5%" title="Jinja2" src="assets/jinja-svgrepo-com.svg"></code>
  <code><img width="5%" title="Git" src="assets/Git.svg"></code>
  <code><img width="5%" title="Pre-commit" src="assets/pre-commit-svgrepo-com.svg"></code>
</p>

---

## 🧭 Структура проекта

```
niffler-py-st3/
│
├── docker-compose-dev.sh           # Сборка и запуск контейнеров Niffler
├── niffler_e_2_e_tests_python/
│   ├── fixtures/                   # Pytest-фикстуры (UI, API, DB, Kafka, gRPC)
│   ├── pages/                      # PageObject модели для Playwright UI тестов
│   ├── grpc_tests/                 # gRPC тесты и мок-сервер
│   ├── databases/                  # Подключения к PostgreSQL (SQLModel)
│   ├── utils/                      # Клиенты Kafka, AuthClient, Allure-хелперы
│   ├── models/                     # Pydantic-конфиги и DTO
│   ├── tests/                      # Тестовые сценарии (UI, API, E2E)
│   ├── run_allure.sh               # Bash-скрипт для тестов и отчётов
│   ├── pyproject.toml              # Конфигурация Poetry / Pytest
│   ├── .env                        # Переменные окружения
│   └── allure-results/, allure-report/ # Allure результаты и отчёты
│
└── .github/workflows/ci.yml        # GitHub Actions CI/CD с Allure Report
```

---

## 🔍 Основные особенности

- ✅ **UI-тесты** на фреймворке `Playwright` с использованием Page Object Model и Page Factory. Также добавлены UI тесты + DB с использованием передачи данных REST API
- ✅ **API-тесты** проверяющие интеграцию REST API и SOAP с авторизацией, токенами и JSON-валидацией  (библиотеки Request, HTTPX)
- ✅ **E2E-тесты** проверяющие очередь и обработку событий Kafka → DB → API
- ✅ **Фикстуры** для управления запуском тестов и подготовкой тестовых данных
- ✅ **Pydantic** для валидации и трансформации данных 
- ✅ **SQLModel + PostgreSQL+ SQLAlchemy** для управления и взаимодействия с БД и валидации данных 
- ✅ Поддержка **headless-режима** и CI-запусков. Поддержка параллельного запуска тестов
- ✅ **gRPC-тесты** с мок-сервером через Docker 
- ✅ **Allure-отчёты** с кастомными CSS-вложениями 
- ✅ **Jinja2** шаблонизатор для повышения читаемости отчетов тестирования

---

## ⚙️ Настройка Docker и Java

```bash
# Собрать контейнеры с Niffler (если на предыдущем шаге не выполнено)
cd niffler-py-st3
bash docker-compose-dev.sh
```

Если есть проблемы со сборкой Gradle:
```bash
./gradlew clean build --refresh-dependencies
```

Очистить кэши Gradle:
```bash
rm -rf ~/.gradle/caches ~/.gradle/daemon ~/.m2/repository
```

Настроить Java (если требуется):
```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH="$JAVA_HOME/bin:$PATH"
java -version
rm -rf ~/.gradle/caches
java -version
echo $JAVA_HOME
bash docker-compose-dev.sh
```

---

## 🧪 Подготовка окружения тестов

Тестовые настройки `.env` в папке `niffler_e_2_e_tests_python/`:

```
BASE_AUTH_URL=http://auth.niffler.dc:9000/login
BASE_URL=http://frontend.niffler.dc/main
BASE_ERROR_URL=http://auth.niffler.dc:9000/login?error
API_URL=http://gateway.niffler.dc:8090
SPEND_DB_URL=postgresql+psycopg2://postgres:secret@localhost:5432/niffler-spend
AUTH_URL=http://auth.niffler.dc:9000
AUTH_SECRET=secret
FRONTEND_URL=http://frontend.niffler.dc
KAFKA_ADDRESS_PRODUCER=localhost:9093
KAFKA_ADDRESS_CONSUMER=localhost:9093
USER_DB_URL=postgresql+psycopg2://postgres:secret@localhost:5432/niffler-userdata
USERDATA_GROUP_ID=userdata
GRPC_ADDRESS=localhost:8092
GRPC_MOCK_ADDRESS=localhost:8094
USERDATA_SOAP_URL=http://userdata.niffler.dc:8089/ws
USERDATA_SOAP_NS=niffler-userdata
```

---

## 🧰 Bash-скрипт `run_allure.sh`
В проекте добавлен bash-скрипт run_allure.sh, который позволяет сформировать отчет allure c вложениями запросов и ответов API в шагах, оформленных с CSS стилями.

Скрипт автоматизирует:
- запуск тестов;
- очистку отчётов;
- генерацию Allure-отчёта.

```bash
# Выполнить один раз (Linux/macOS)
chmod +x run_allure.sh
```

### Примеры команд:

| Назначение | Команда |
|-------------|----------|
| Все тесты | `./run_allure.sh` |
| Один тест | `./run_allure.sh test_add_duplicate_category_api` |
| По группе | `./run_allure.sh api` |
| Параллельно (auto) | `./run_allure.sh api --workers auto` |
| Параллельно (4 потока) | `./run_allure.sh --workers 4 --dist loadfile` |
| Headless режим | `PW_HEADLESS=1 ./run_allure.sh --workers 8 --dist loadfile` |
| gRPC с моками | `./run_allure.sh grpc --mock` |

Перед `--mock` запусти мок-сервис:
```bash
docker-compose -f grpc_tests/docker-compose.mock.yml up -d
```

---

## 📊 Allure-отчёт

Локальный запуск:
```bash
allure serve
```

<details>
<summary>Пример отчёта</summary>
<br>
<code><img src="assets/allure_report_1.png"></code>
<code><img src="assets/allure_report_2.png"></code>
<code><img src="assets/allure_report_3.png"></code>
</details>

<details>
<summary>Пример прогона UI теста</summary>
<br>
<code><img src="assets/data_attachments_809db929d1b2f0cb.gif"></code>
</details>

---

## 🧹 Линтеры и форматирование кода
В проекте настроен pre-commit.

Для ручнного запуска линтеров можно пользоваться командами
```bash
# Проверка стиля
poetry run ruff check .

# Автоисправление
poetry run ruff check . --fix

# Форматирование
poetry run ruff format .
```

```bash
## Запустить тесты с allure и удалением предыдущих результатов без bash-скрипт:
cd niffler_e_2_e_tests_python
poetry run pytest -k "test_archive_category_db" --alluredir allure-results --clean-alluredir
```

---

## 🤖 CI/CD и GitHub Pages

- Запускается при Pull Request и коммитах в `main`/`master`
- Автоматически поднимает Docker, Playwright и Allure
- После прогона формирует Allure Report
- **Публикует отчёт на GitHub Pages**

---

## 📘 Автор и контакты

👤 **Владислав Дурицкий**  
🧠 QA Automation Engineer  
🗓️ 2025  
🔗 Проект: *Учебно-практическая стендовая система автотестов Niffler (UI + API + Kafka + DB + gRPC + Allure)*  
📧 [Email](vladdd9312@gmail.com)  
💼 [LinkedIn](https://www.linkedin.com/in/vladislav-duritski-053827376/)  
💻 [HeadHunter (HH.ru)](https://hh.ru/resume/bead2577ff0d39e32f0039ed1f744f7568616b)
