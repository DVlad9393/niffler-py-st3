from collections.abc import Callable

import allure
import grpc
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message


class AllureInterceptor(grpc.UnaryUnaryClientInterceptor):
    """Интерцептор gRPC-клиента для интеграции с Allure-отчётами.

    Автоматически добавляет шаги в Allure-отчёт при каждом gRPC-вызове,
    фиксируя метод, тело запроса и ответ сервера в формате JSON.
    Используется для визуализации и отладки gRPC-взаимодействий в отчётах о тестах.

    Пример в Allure:
        • шаг = имя RPC-метода (например, ``/guru.qa.grpc.niffler.NifflerCurrencyService/Calculate``)
        • вложенные вложения = Request.json, Response.json
    """

    def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request: Message,
    ) -> Callable:
        """Перехватывает unary-вызов клиента, записывая запрос и ответ в Allure.
        :param continuation: Функция, выполняющая реальный RPC-вызов.
        :param client_call_details: Метаданные вызова (метод, таймаут, метаданные и т.д.).
        :param request: Protobuf-сообщение, передаваемое в запросе.
        :return: Ответ gRPC-вызова, возвращённый исходным continuation.
        """
        with allure.step(client_call_details.method):
            allure.attach(
                MessageToJson(request),
                name="Request",
                attachment_type=allure.attachment_type.JSON,
            )
            response = continuation(client_call_details, request)
            allure.attach(
                MessageToJson(response.result()),
                name="Response",
                attachment_type=allure.attachment_type.JSON,
            )
        return response
