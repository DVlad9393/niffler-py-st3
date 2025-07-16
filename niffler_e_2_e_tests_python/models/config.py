from pydantic import BaseModel, StrictStr


class Envs(BaseModel):
    """Конфигурация переменных окружения для запуска тестов.

    :param api_url: Базовый URL для обращения к API.
    :type api_url: StrictStr
    :param username: Имя пользователя для аутентификации.
    :type username: StrictStr
    :param password: Пароль пользователя.
    :type password: StrictStr
    :param base_auth_url: URL для авторизации.
    :type base_auth_url: StrictStr
    :param base_url: Главный URL интерфейса приложения.
    :type base_url: StrictStr
    :param base_error_url: URL, на который происходит редирект при ошибке входа.
    :type base_error_url: StrictStr
    :param spend_db_url: URL для подключения к базе данных трат.
    :type spend_db_url: StrictStr
    :param auth_url: URL для авторизации.
    :type auth_url: StrictStr
    """

    api_url: StrictStr
    username: StrictStr
    password: StrictStr
    base_auth_url: StrictStr
    base_url: StrictStr
    base_error_url: StrictStr
    spend_db_url: StrictStr
    auth_url: StrictStr
    auth_secret: StrictStr
