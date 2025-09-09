import json
import logging
from json import JSONDecodeError

import allure
import curlify
from allure_commons.types import AttachmentType
from jinja2 import Environment, PackageLoader, select_autoescape
from requests import Response

# Легаси метод с обычным вложением без подсветки и стилей

# def allure_attach_request(function):
#     """Декоратор логирования запроса, хедеров запроса, хедеров ответа в allure шаг и аллюр аттачмент и в консоль."""
#
#     def wrapper(*args, **kwargs):
#         method, url = args[1], args[2]
#         with allure.step(f"{method} {url}"):
#             response: Response = function(*args, **kwargs)
#
#             curl = curlify.to_curl(response.request)
#             logging.debug(curl)
#             logging.debug(response.text)
#
#             allure.attach(
#                 body=curl.encode("utf8"),
#                 name=f"Request {response.status_code}",
#                 attachment_type=AttachmentType.TEXT,
#                 extension=".txt",
#             )
#             try:
#                 allure.attach(
#                     body=json.dumps(response.json(), indent=4).encode("utf8"),
#                     name=f"Response json {response.status_code}",
#                     attachment_type=AttachmentType.JSON,
#                     extension=".json",
#                 )
#             except JSONDecodeError:
#                 allure.attach(
#                     body=response.text.encode("utf8"),
#                     name=f"Response text {response.status_code}",
#                     attachment_type=AttachmentType.TEXT,
#                     extension=".txt",
#                 )
#             allure.attach(
#                 body=json.dumps(dict(response.headers), indent=4).encode("utf8"),
#                 name=f"Response headers {response.status_code}",
#                 attachment_type=AttachmentType.JSON,
#                 extension=".json",
#             )
#         return response
#
#     return wrapper


def allure_attach_request(function):
    """Декоратор для автоматического логирования HTTP-запроса и ответа в Allure-отчет с поддержкой HTML-подсветки и вложений.

    При каждом вызове функции, обёрнутой этим декоратором:
    - В Allure добавляется шаг с названием вида "METHOD URL" (например, "GET /api/test").
    - Вложение запроса оформляется с помощью HTML-шаблона **http-colored-request.ftl** (см. папку schemas).
    - Вложение ответа оформляется с помощью HTML-шаблона **http-colored-response.ftl** (см. папку schemas).
    - Оба HTML-вложения используют CSS-стили для красивого форматирования HTTP-запроса/ответа, включая подсветку кода, форматирование CURL, заголовков, тела, cookies и т.д.
    - В Allure дополнительно добавляется:
        - JSON-ответ, если он корректно сериализуется (отдельным вложением с типом JSON).
        - Текст ответа, если сериализация не удалась (отдельным вложением с типом TEXT).
    - Для генерации HTML используются шаблоны Freemarker (ftl) через Jinja2 (не забудь скопировать шаблоны в папку **schemas**).

    Применение:
        @allure_attach_request
        def my_api_method(...): ...

    Args:
    ----
        function (callable): Любая функция, возвращающая HTTPX Response (обычно метод API-клиента).

    Returns:
    -------
        callable: Обёрнутая функция с автоматическим созданием красивых вложений в Allure.

    Зависимости:
        - Файлы http-colored-request.ftl и http-colored-response.ftl должны быть доступны в директории 'schemas'.
        - Для корректного отображения HTML-вложений необходимо подключать необходимые CSS/JS-стили в шаблонах.
        - Используются библиотеки allure-pytest, jinja2, curlify.

    """

    def wrapper(*args, **kwargs):
        method, url = args[1], args[2]

        env = Environment(
            loader=PackageLoader("schemas"), autoescape=select_autoescape()
        )

        request_template = env.get_template("http-colored-request.ftl")
        response_template = env.get_template("http-colored-response.ftl")

        with allure.step(f"{method} {url}"):
            response: Response = function(*args, **kwargs)
            curl = curlify.to_curl(response.request)
            logging.debug(curl)
            logging.debug(response.text)

            request_render = request_template.render(
                {
                    "request": response.request,
                    "curl": curl,
                }
            )

            allure.attach(
                body=request_render,
                name="Request",
                attachment_type=AttachmentType.HTML,
                extension=".html",
            )

            response_render = response_template.render(
                {
                    "response": response,
                }
            )

            allure.attach(
                body=response_render,
                name=f"Response HTML {response.status_code}",
                attachment_type=AttachmentType.HTML,
                extension=".html",
            )

            try:
                allure.attach(
                    body=json.dumps(response.json(), indent=4).encode("utf8"),
                    name=f"Response JSON {response.status_code}",
                    attachment_type=AttachmentType.JSON,
                    extension=".json",
                )
            except (JSONDecodeError, TypeError):
                allure.attach(
                    body=response.text.encode("utf8"),
                    name=f"Response text {response.status_code}",
                    attachment_type=AttachmentType.TEXT,
                    extension=".txt",
                )

        return response

    return wrapper


def _pretty_sql(statement: str) -> str:
    """Форматирует SQL-запрос для большей читаемости: переносы строк после ключевых слов.

    :param statement: Текст SQL-запроса.
    :return: SQL-запрос с переносами строк.
    """
    for keyword in [
        "SELECT",
        "FROM",
        "WHERE",
        "ORDER BY",
        "GROUP BY",
        "AND",
        "OR",
        "LEFT JOIN",
        "RIGHT JOIN",
    ]:
        statement = statement.replace(keyword, f"\n{keyword}")
    return statement.strip()


def _safe_format(statement: str, parameters) -> str:
    """Подставляет параметры в SQL для Allure-вложений.
    Не подходит для отправки в базу — только для логов и отчётов!

    :param statement: SQL-запрос с плейсхолдерами.
    :param parameters: Словарь или последовательность с параметрами для подстановки.
    :return: SQL-запрос с подставленными параметрами или исходный запрос при ошибке.
    """
    try:
        if isinstance(parameters, dict):
            params = {
                k: (f"'{v}'" if isinstance(v, str) else v)
                for k, v in parameters.items()
            }
            return statement % params

        if isinstance(parameters, tuple | list):
            params = tuple(f"'{v}'" if isinstance(v, str) else v for v in parameters)
            return statement % params
    except Exception as e:
        logging.warning(
            f"SQL format error: {e!r}. Statement: {statement}, Params: {parameters}"
        )
    return statement


def attach_sql(cursor, statement, parameters, context) -> None:
    """Добавляет SQL-запрос с параметрами в отчет Allure в читабельном виде.

    :param cursor: Курсор базы данных.
    :param statement: Текст SQL-запроса.
    :param parameters: Параметры для подстановки в SQL.
    :param context: Контекст SQLAlchemy.
    """
    sql = _safe_format(statement, parameters)
    pretty_sql = _pretty_sql(sql)
    name = f'{statement.split(" ")[0]} {context.engine.url.database}'
    allure.attach(pretty_sql, name=name, attachment_type=allure.attachment_type.TEXT)
