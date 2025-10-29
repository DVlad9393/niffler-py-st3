import json
import logging
import time
from typing import Any
from uuid import uuid4

from confluent_kafka import TopicPartition
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import Consumer, Message, Producer

from niffler_e_2_e_tests_python.models.user import UserName
from niffler_e_2_e_tests_python.utils.waiters import wait_until_timeout


class KafkaClient:
    """Класс для взаимодействия с Apache Kafka на базе библиотеки `confluent-kafka`.

    Создаёт админ-клиент, продюсер и консюмер, позволяет:
      • публиковать сообщения в произвольный топик;
      • публиковать доменную модель пользователя в топик `userdata`;
      • подписываться на партиции и читать сообщения, начиная с нужных оффсетов;
      • получать «верхние» оффсеты партиций и логировать принятые сообщения.

    Во время инициализации логирует «рекламируемые» брокерами адреса, что помогает диагностировать
    проблемы с `advertised.listeners` (частая причина ошибок подключения в Docker/Compose).
    """

    def __init__(
        self,
        envs,
        client_id: str = "tester",
        group_id: str | None = None,
    ):
        """Инициализирует Kafka-клиенты (AdminClient, Producer, Consumer) на основании окружения.
        Если group_id не передан — генерируется уникальный для каждого клиента.
        Это нужно для изоляции параллельных тестов (xdist).

        :param envs: Объект с настройками окружения (содержит адреса для продюсера и консюмера).
        :param client_id: Идентификатор клиента для метрик и отладки.
        :param group_id: Группа консюмера для управления оффсетами и ребалансом.
        :raises: Исключения `confluent_kafka` при невозможности получить метаданные кластера.
        """
        self.server_producer = envs.kafka_address_producer
        self.server_consumer = envs.kafka_address_consumer
        self.group_id = group_id or f"tester-{uuid4().hex[:8]}"

        self.admin = AdminClient({"bootstrap.servers": self.server_producer})
        self.producer = Producer({"bootstrap.servers": self.server_producer})
        self.consumer = Consumer(
            {
                "bootstrap.servers": self.server_consumer,
                "group.id": self.group_id,
                "client.id": client_id,
                "auto.offset.reset": "latest",
                "enable.auto.commit": False,
                "enable.ssl.certificate.verification": False,
            }
        )
        md = self.admin.list_topics(timeout=5)
        advertised = {b.id: f"{b.host}:{b.port}" for b in md.brokers.values()}
        logging.info(
            "Bootstrap(producer)=%s, Bootstrap(consumer)=%s, Advertised brokers=%s, group_id=%s",
            self.server_producer,
            self.server_consumer,
            advertised,
            self.group_id,
        )

    def __enter__(self):
        """Возвращает сам клиент для использования в контекстном менеджере `with`.

        :return: Экземпляр KafkaClient для `with KafkaClient(...) as kafka: ...`.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрывает ресурсы при выходе из контекстного менеджера.

        Гарантированно закрывает консюмера и дожидается отправки буфера продюсера.

        :param exc_type: Тип исключения, возникшего в блоке `with` (если было).
        :param exc_val: Экземпляр исключения (если было).
        :param exc_tb: Трейсбек исключения (если был).
        :return: Ничего не возвращает.
        """
        self.consumer.close()
        self.producer.flush()

    @staticmethod
    def delivery_report(err: Exception | None, msg: Message) -> None:
        """Колбэк результата доставки сообщения для продюсера.

        Вызывается библиотекой после попытки доставки. В случае ошибки пишет в лог,
        в случае успеха логирует топик, партицию и оффсет.

        :param err: Ошибка доставки, если она произошла.
        :param msg: Сообщение с метаданными доставки.
        :return: Ничего не возвращает.
        """
        if err is not None:
            logging.error("Delivery failed: %s", err)
        else:
            logging.debug(
                "Delivered to %s [%s] @ %s", msg.topic(), msg.partition(), msg.offset()
            )

    def produce_message(self, topic: str, key: str, value: dict[str, Any]):
        """Публикует произвольное сообщение в указанный топик (payload сериализуется в JSON).

        Колбэк доставки логирует успех/ошибку, а `poll(0)` выкачивает внутреннюю очередь событий.

        :param topic: Имя топика, в который нужно отправить сообщение.
        :param key: Ключ сообщения (влияет на партиционирование и идемпотентность downstream-обработки).
        :param value: Словарь с данными, который будет сериализован в JSON.
        :return: Ничего не возвращает.
        :raises: Исключения сериализации или отправки; при ошибке пишется лог и исключение пробрасывается.
        """

        def delivery_callback(err: Exception | None, msg: Message):
            if err:
                logging.error("Message delivery failed: %s", err)
            else:
                logging.debug(
                    "Message delivered to %s [%s]", msg.topic(), msg.partition()
                )

        try:
            json_value = json.dumps(value)
            self.producer.produce(
                topic=topic, key=key, value=json_value, callback=delivery_callback
            )
            self.producer.poll(0)
        except Exception as e:
            logging.error("Failed to produce message: %s", e)
            raise

    def produce_user_data(self, user_data: dict[str, Any]):
        """Публикует пользовательские данные в топик `userdata`.

        В качестве ключа используется `id` из `user_data`, а при его отсутствии — `username`.

        :param user_data: Словарь с данными пользователя для публикации.
        :return: Ничего не возвращает.
        """
        user_id = user_data.get("id", user_data.get("username", "unknown"))
        self.produce_message("userdata", str(user_id), user_data)

    def list_topics_names(self, attempts: int = 5):
        """Возвращает список доступных в кластере топиков.

        :param attempts: Таймаут ожидания метаданных в секундах.
        :return: Список имён топиков или `None`, если получить список не удалось.
        """
        try:
            topics = self.admin.list_topics(timeout=attempts).topics
            return [topics.get(item).topic for item in topics]
        except RuntimeError:
            logging.error("no topics in kafka")

    @wait_until_timeout
    def consume_message(self, partitions, **kwargs):
        """Возвращает значение следующего сообщения после указанных оффсетов.

        Метод назначает консюмеру заданные партиции с оффсетами и выполняет `poll(1.0)`.
        Обёрнут декоратором `@wait_until_timeout`, поэтому поддерживает параметры:
          • `timeout` — общий таймаут ожидания результата;
          • `polling_interval` — интервал между попытками;
          • `err` — при значении `True` декоратор поднимет TimeoutError после истечения времени.

        :param partitions: Набор объектов `TopicPartition` с топиком, партицией и оффсетом начала чтения.
        :param kwargs: Параметры ожидания, прокидываемые в декоратор (`timeout`, `polling_interval`, `err`).
        :return: Сырые байты значения сообщения или `None`, если оно не было получено в пределах таймаута.
        """
        try:
            message = self.consumer.poll(1.0)
            logging.debug("%s", message.value())
            return message.value()
        except AttributeError:
            pass

    def get_last_offset(self, topic: str = "", partition_id=0):
        """Возвращает верхнюю границу оффсета (high watermark) для заданной партиции.

        Полезно, чтобы начать чтение «с конца» (только новые сообщения).

        :param topic: Имя топика.
        :param partition_id: Номер партиции.
        :return: Числовое значение high watermark или `None` при ошибке получения.
        """
        partition = TopicPartition(topic, partition_id)
        try:
            low, high = self.consumer.get_watermark_offsets(partition, timeout=10)
            return high
        except Exception as err:
            logging.error("probably no such topic: %s: %s", topic, err)

    def log_msg_and_json(
        self,
        topic_partitions,
        *,
        match_username: str | None = None,
        timeout: float = 25.0,
    ):
        """Блокирующе ожидает публикации нового JSON-сообщения в Kafka,
        начиная с заданных оффсетов, и возвращает «сырое» содержимое первого
        подходящего сообщения (в виде bytes).

        Метод используется для end-to-end тестов, где необходимо убедиться,
        что после некоторого действия в системе (например, регистрации пользователя)
        соответствующее событие действительно попало в Kafka-топик.


        Поведение предназначено для изоляции при параллельных запусках тестов (pytest-xdist):
        фильтрация по `match_username` гарантирует, что каждый тест дождётся именно своего
        пользовательского события, даже если Kafka-топик общий для всех воркеров.

        :param topic_partitions: Список объектов `confluent_kafka.TopicPartition`,
                                 задающих топик, партицию и оффсет начала чтения.
                                 Обычно возвращается методом `subscribe_listen_new_offsets()`.
        :param match_username: (опционально) строка с ожидаемым username;
                               если указана, метод возвращает только сообщение,
                               где `payload["username"] == match_username`.
        :param timeout: Общее время ожидания (в секундах). По умолчанию 25.0.
                        После его истечения будет выброшено исключение AssertionError.
        :return: Сырые байты (`bytes`) полезной нагрузки Kafka-сообщения (value).
        :raises AssertionError: если в течение `timeout` не найдено ни одного
                                подходящего JSON-сообщения (или подходящего по username).
        :raises ValueError: если формат сообщения невалиден (например, не JSON),
                            но эти ошибки обычно перехватываются и просто логируются.
        """
        self.consumer.assign(topic_partitions)

        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            raw = self.consume_message(
                topic_partitions,
                timeout=max(0.2, remaining),
                polling_interval=0.5,
                err=False,
            )

            if not raw:
                continue

            try:
                payload = json.loads(
                    raw.decode("utf-8") if isinstance(raw, bytes | bytearray) else raw
                )
            except Exception as e:
                logging.debug("Skip non-JSON message: %s", e)
                continue

            logging.info("Kafka payload: %s", payload)
            if match_username is None or payload.get("username") == match_username:
                return raw

        raise AssertionError(
            "Timed out waiting Kafka event"
            + (f" for {match_username}" if match_username else "")
        )

    def subscribe_listen_new_offsets(self, topic):
        """Подписывается на топик и возвращает список партиций со следующими оффсетами чтения.

        Логика:
          1) получить перечень партиций топика;
          2) определить high watermark (текущий «конец» партиции) для каждой;
          3) вернуть `TopicPartition(topic, partition_id, next_offset)` — чтобы читать только новые сообщения.

        :param topic: Имя топика.
        :return: Список `TopicPartition` с оффсетами для чтения «с конца».
        """
        md = self.admin.list_topics(topic, timeout=5)
        p_ids = md.topics[topic].partitions.keys()

        partitions_offsets_event = {p: self.get_last_offset(topic, p) for p in p_ids}
        logging.info("%s offsets: %s", topic, partitions_offsets_event)

        return [
            TopicPartition(topic, p, off) for p, off in partitions_offsets_event.items()
        ]

    def sending_message(self, topic: str, username: str):
        """Формирует и публикует доменное сообщение о пользователе в указанный топик.

        Тело сообщения строится на основе модели `UserName`, сериализуется в JSON и отправляется.
        Для диагностики доставки используется `delivery_report`. По окончании публикации
        вызывается `flush(5)` для гарантии отправки.

        :param topic: Имя целевого топика (например, `users`).
        :param username: Имя пользователя, которое будет включено в payload.
        :return: Ничего не возвращает.
        """
        value = json.dumps(UserName(username=username).model_dump()).encode("utf-8")
        self.producer.produce(
            topic,
            value=value,
            on_delivery=KafkaClient.delivery_report,
            headers={"__TypeId__": "guru.qa.niffler.model.UserJson"},
        )
        self.producer.flush(5)
