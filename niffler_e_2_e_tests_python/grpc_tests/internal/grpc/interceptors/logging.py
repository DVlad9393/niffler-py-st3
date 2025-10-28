from collections.abc import Callable

import grpc
from google.protobuf.message import Message


class LoggingInterceptor(grpc.UnaryUnaryClientInterceptor):
    """Интерцептор gRPC-клиента для консольного логирования запросов и ответов.

    Выводит в stdout имя RPC-метода, тело запроса и результат ответа.
    Применяется для быстрой отладки без интеграции в Allure или внешние системы логирования.
    """

    def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request: Message,
    ) -> Callable:
        """Перехватывает unary-вызов клиента и выводит информацию в консоль.

        :param continuation: Функция, выполняющая реальный RPC-вызов.
        :param client_call_details: Метаданные gRPC-вызова (метод, таймаут, метаданные и т.д.).
        :param request: Protobuf-сообщение, передаваемое в запросе.
        :return: Ответ gRPC-вызова после выполнения continuation.
        """
        print(client_call_details.method)
        print(request)

        response = continuation(client_call_details, request)
        print(response.result())
        return response
