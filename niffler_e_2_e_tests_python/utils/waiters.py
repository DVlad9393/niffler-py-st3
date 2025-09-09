import datetime
import logging
import time
from functools import wraps

import allure


@allure.step
def wait_until_timeout(function):
    """Декоратор ожидания результата с повторными вызовами функции до наступления таймаута.

    Поведение:
      • Многократно вызывает декорируемую функцию с переданными аргументами.
      • Между попытками делает паузу.
      • Управляющие параметры читаются из kwargs и не передаются в целевую функцию:
          - timeout — общее время ожидания в секундах (по умолчанию 12).
          - polling_interval — пауза между попытками в секундах (по умолчанию 0.1).
          - err — если истинно, по истечении таймаута возбуждается TimeoutError; иначе возвращается None.
      • Успешным результатом считается любое значение, которое не равно None, не пустой строке и не пустому списку.
      • Пишет диагностические сообщения в лог: старт ожидания и отсутствие результата.

    Ограничения и заметки:
      • Исключения, выброшенные целевой функцией, не подавляются и пробрасываются наружу.
      • Таймаут отсчитывается от первого вызова и включает задержки между попытками.
      • В конце окна ожидания добавляется небольшая дельта (~0.1 сек.), чтобы избежать погрешности сравнения по времени.

    Пример:
        @wait_until_timeout
        def get_event():
            ...
        result = get_event(timeout=20, polling_interval=0.5, err=True)

    :param function: Функция, которую нужно вызывать до получения «непустого» результата или истечения таймаута.
    :return: Обёрнутая функция, возвращающая первый «непустой» результат либо None/исключение в зависимости от настроек.
    :raises TimeoutError: Если по истечении времени результат не получен и передан параметр err=True.
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        default_timeout = 12
        timeout = kwargs.pop("timeout", default_timeout)
        polling_interval = kwargs.pop("polling_interval", 0.1)
        err = kwargs.pop("err", None)
        start_time = datetime.datetime.now().timestamp()
        result = None
        logging.debug(f"{start_time} start waiting")
        while datetime.datetime.now().timestamp() < start_time + timeout + 0.1:
            result = function(*args, **kwargs)
            if result is not None and result != [] and result != "":
                break
            time.sleep(polling_interval)
        if err and result is None:
            raise TimeoutError(
                f"{datetime.datetime.now().isoformat()} "
                f"Результаты функции {function.__name__} не найдены за {timeout}s"
            )
        if result is None:
            logging.error(f"{datetime.datetime.now().timestamp()} result is None")
        return result

    return wrapper
