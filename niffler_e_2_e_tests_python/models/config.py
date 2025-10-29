from pydantic import BaseModel, StrictStr


class Envs(BaseModel):
    """Конфигурация переменных окружения для запуска тестов.

    :param api_url: Базовый URL для обращения к API.
    :type api_url: StrictStr
    :param base_auth_url: URL для авторизации.
    :type base_auth_url: StrictStr
    :param base_url: URL главной страницы интерфейса приложения.
    :type base_url: StrictStr
    :param base_error_url: URL, на который происходит редирект при ошибке входа.
    :type base_error_url: StrictStr
    :param spend_db_url: URL для подключения к базе данных трат.
    :type spend_db_url: StrictStr
    :param auth_url: URL для авторизации.
    :type auth_url: StrictStr
    :param auth_secret: Секрет для авторизации.
    :type auth_secret: StrictStr
    :param frontend_url: Базовый URL интерфейса приложения.
    :type frontend_url: StrictStr
    :param kafka_address_producer: Адрес Kafka-продьюсера.
    :type kafka_address_producer: StrictStr
    :param kafka_address_consumer: Адрес Kafka-консьюмера.
    :type kafka_address_consumer: StrictStr
    :param user_db_url: URL для подключения к базе данных пользователей.
    :type user_db_url: StrictStr
    :param userdata_group_id: group.id сервиса кафки.
    :type userdata_group_id: StrictStr
    :param grpc_address: адрес grpc сервиса
    :type grpc_address: StrictStr
    :param grpc_mock_address: адрес grpc_mock сервиса
    :type grpc_mock_address: StrictStr
    """

    api_url: StrictStr
    base_auth_url: StrictStr
    base_url: StrictStr
    base_error_url: StrictStr
    spend_db_url: StrictStr
    auth_url: StrictStr
    auth_secret: StrictStr
    frontend_url: StrictStr
    kafka_address_producer: StrictStr
    kafka_address_consumer: StrictStr
    user_db_url: StrictStr
    userdata_group_id: StrictStr
    grpc_address: StrictStr
    grpc_mock_address: StrictStr
