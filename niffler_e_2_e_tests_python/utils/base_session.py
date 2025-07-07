import json

import allure
import httpx

def _pretty_headers(headers: dict) -> str:
    """
    Форматирует словарь HTTP-заголовков в удобочитаемую строку для отчёта или логов.

    Каждый заголовок выводится с отступом в 4 пробела, один заголовок — одна строка.

    Пример:
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer <token>"
        }
    превратится в:
        "    Content-Type: application/json
             Authorization: Bearer <token>"

    :param headers: Словарь с HTTP-заголовками.
    :return: Многострочная строка с форматированными заголовками.
    """
    return "\n".join(f"    {k}: {v}" for k, v in headers.items())

def _pretty_body(body, content_type="application/json"):
    """
    Форматирует тело HTTP-запроса или ответа для читабельного вывода.

    - Если тело — JSON (по Content-Type или явно), форматирует с отступами.
    - Если тело — bytes, декодирует в строку.
    - Для других типов возвращает строковое представление как есть.
    - В случае ошибки преобразования возвращает исходное значение в виде строки.

    Пример:
        pretty_body(b'{"key": "value"}', "application/json") ->
        '{
          "key": "value"
        }'

    :param body: Тело запроса или ответа (строка или bytes).
    :param content_type: Тип содержимого, влияет на форматирование (по умолчанию "application/json").
    :return: Строка с красиво отформатированным телом.
    """
    try:
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        if "application/json" in content_type:
            parsed = json.loads(body)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        return body
    except Exception:
        return str(body)

def dump_httpx_response(response: httpx.Response) -> str:
    """
    Формирует читаемое текстовое представление HTTP-запроса и ответа для вложения в Allure-отчёт.

    - Форматирует URL, метод, заголовки и тело запроса.
    - Заголовки отображаются по одному на строку.
    - Тело запроса и ответа, если это JSON, будет красиво отформатировано с отступами.
    - Содержимое бинарных/не-JSON тел возвращается как есть.
    - Все секции отделяются заголовками "--- HTTP Request ---" и "--- HTTP Response ---".

    :param response: Объект httpx.Response, содержащий информацию о запросе и ответе.
    :return: Строка с красивым дампом запроса и ответа.
    """
    req = response.request

    req_headers = _pretty_headers(dict(req.headers))
    req_content = req.content
    req_type = req.headers.get("content-type", "")
    req_pretty = _pretty_body(req_content, req_type) if req_content else ""

    resp_headers = _pretty_headers(dict(response.headers))
    resp_type = response.headers.get("content-type", "")
    resp_text = response.text
    resp_pretty = _pretty_body(resp_text, resp_type) if resp_text else ""

    return (
        f"--- HTTP Request ---\n"
        f"URL: {req.url}\n"
        f"Method: {req.method}\n"
        f"Headers:\n{req_headers}\n"
        f"Body:\n{req_pretty}\n"
        f"\n--- HTTP Response ---\n"
        f"Status: {response.status_code}\n"
        f"Headers:\n{resp_headers}\n"
        f"Body:\n{resp_pretty}\n"
    )

class AllureHttpxClient(httpx.Client):
    """httpx.Client с автоматическим логированием всех запросов в Allure."""
    def send(self, request, **kwargs):
        response = super().send(request, **kwargs)
        allure.attach(
            dump_httpx_response(response),
            f"{request.method} {request.url}",
            attachment_type=allure.attachment_type.TEXT
        )
        return response

class BaseSession:
    def __init__(self, base_url: str):
        """
        Инициализация базовой сессии HTTP-клиента с Allure-логированием.

        :param base_url: Базовый URL для всех HTTP-запросов.
        """
        self.base_url = base_url
        self.client = AllureHttpxClient(base_url=self.base_url)

    def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Выполняет HTTP GET-запрос.

        :param url: Относительный URL-адрес для запроса.
        :param kwargs: Дополнительные параметры для httpx.Client.get (например, params, headers).
        :return: Ответ httpx.Response.
        """
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """
        Выполняет HTTP POST-запрос.

        :param url: Относительный URL-адрес для запроса.
        :param kwargs: Дополнительные параметры для httpx.Client.post (например, json, data, headers).
        :return: Ответ httpx.Response.
        """
        return self.client.post(url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """
        Выполняет HTTP PATCH-запрос.

        :param url: Относительный URL-адрес для запроса.
        :param kwargs: Дополнительные параметры для httpx.Client.patch (например, json, data, headers).
        :return: Ответ httpx.Response.
        """
        return self.client.patch(url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """
        Выполняет HTTP DELETE-запрос.

        :param url: Относительный URL-адрес для запроса.
        :param kwargs: Дополнительные параметры для httpx.Client.delete (например, params, headers).
        :return: Ответ httpx.Response.
        """
        return self.client.delete(url, **kwargs)

    def close(self) -> None:
        """
        Закрывает HTTP-клиент и освобождает все сетевые ресурсы.
        """
        self.client.close()