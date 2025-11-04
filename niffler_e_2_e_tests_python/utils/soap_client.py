from __future__ import annotations

import textwrap
import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING

import allure
import requests
from defusedxml import ElementTree

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element as XMLElement


class SoapClient:
    """🔹 Универсальный SOAP-клиент для взаимодействия с сервисами в документ-ориентированном стиле (без WSDL).

    Этот класс реализует безопасный SOAP-запрос через HTTP POST с помощью `requests`.
    XML формируется вручную, оборачивается в `<Envelope>` и логируется в Allure как вложение.
    Для парсинга ответов используется `defusedxml.ElementTree`, что защищает от XML-атак
    (таких как XXE и Billion Laughs).

    Основные возможности:
      • Формирование SOAP Envelope с корректными namespace;
      • Логирование запроса и ответа в Allure;
      • Возврат готового XML-элемента `<Body>` из ответа;
      • Безопасная обработка XML без зависимости от WSDL.

    :param endpoint: URL SOAP-сервиса (например, `http://userdata.niffler.dc:8089/ws`)
    :param ns: XML namespace для тегов (например, `niffler-userdata`)
    :param timeout: Максимальное время ожидания ответа (по умолчанию 10 секунд)
    """

    def __init__(self, endpoint: str, ns: str, timeout: float = 10.0):
        """Инициализация SOAP-клиента и сохранение настроек подключения.

        :param endpoint: Конечная точка SOAP API;
        :param ns: Пространство имён (`xmlns:ud="..."`);
        :param timeout: Таймаут запроса в секундах.
        """
        self.endpoint = endpoint.rstrip("/")
        self.ns = ns
        self.timeout = timeout

    def _envelope(self, body_xml: str) -> str:
        """Оборачивает XML-запрос в SOAP Envelope.

        Возвращает корректно сформированный SOAP XML-документ, готовый к отправке.

        :param body_xml: Тело запроса, заключённое в `<ud:...Request>`;
        :return: Полный SOAP Envelope как строка.
        """
        return textwrap.dedent(
            f"""\
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ud="{self.ns}">
          <soapenv:Header/>
          <soapenv:Body>
            {body_xml}
          </soapenv:Body>
        </soapenv:Envelope>
        """
        ).strip()

    def call(
        self, inner_xml: str, extra_headers: Mapping[str, str] | None = None
    ) -> XMLElement:
        """Отправляет SOAP-запрос и возвращает первый XML-элемент из `<Body>`.

        Метод автоматически формирует полный SOAP Envelope, добавляет стандартные заголовки
        (`Content-Type`, `X-Request-Id`), выполняет HTTP-запрос через `requests.post`
        и парсит XML-ответ безопасным способом.

        Весь SOAP-запрос и ответ прикладываются в Allure-отчёт для удобства отладки.

        :param inner_xml: XML-тело без обёртки Envelope;
        :param extra_headers: Дополнительные HTTP-заголовки (опционально);
        :return: XML-элемент первого дочернего узла из SOAP `<Body>`;
        :raises AssertionError: если `<Body>` пуст или отсутствует.
        :raises requests.HTTPError: при неуспешном HTTP-ответе.
        """
        envelope = self._envelope(inner_xml)
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "X-Request-Id": str(uuid.uuid4()),
        }
        if extra_headers:
            headers.update(extra_headers)

        with allure.step("[SOAP] Request"):
            allure.attach(
                envelope,
                name="soap_request.xml",
                attachment_type=allure.attachment_type.XML,
            )

        resp = requests.post(
            self.endpoint,
            data=envelope.encode("utf-8"),
            headers=headers,
            timeout=self.timeout,
        )

        with allure.step(f"[SOAP] Response HTTP {resp.status_code}"):
            allure.attach(
                resp.text,
                name="soap_response.xml",
                attachment_type=allure.attachment_type.XML,
            )

        resp.raise_for_status()

        root = ElementTree.fromstring(resp.content)
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        if body is None or len(body) == 0:
            raise AssertionError("SOAP Body пуст или не содержит ответа")

        return body[0]
