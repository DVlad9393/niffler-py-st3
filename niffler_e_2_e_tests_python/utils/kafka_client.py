import json
import logging
from typing import Any

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
        group_id: str = "tester",
    ):
        """Инициализирует Kafka-клиенты (AdminClient, Producer, Consumer) на основании окружения.

        :param envs: Объект с настройками окружения (содержит адреса для продюсера и консюмера).
        :param client_id: Идентификатор клиента для метрик и отладки.
        :param group_id: Группа консюмера для управления оффсетами и ребалансом.
        :raises: Исключения `confluent_kafka` при невозможности получить метаданные кластера.
        """
        self.server_producer = envs.kafka_address_producer
        self.server_consumer = envs.kafka_address_consumer

        self.admin = AdminClient({"bootstrap.servers": self.server_producer})
        self.producer = Producer({"bootstrap.servers": self.server_producer})
        self.consumer = Consumer(
            {
                "bootstrap.servers": self.server_consumer,
                "group.id": group_id,
                "client.id": client_id,
                "auto.offset.reset": "latest",
                "enable.auto.commit": False,
                "enable.ssl.certificate.verification": False,
            }
        )
        md = self.admin.list_topics(timeout=5)
        advertised = {b.id: f"{b.host}:{b.port}" for b in md.brokers.values()}
        logging.info(
            "Bootstrap(producer)=%s, Bootstrap(consumer)=%s, Advertised brokers=%s",
            self.server_producer,
            self.server_consumer,
            advertised,
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
        self.consumer.assign(partitions)
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

    def log_msg_and_json(self, topic_partitions):
        """Ожидает сообщение с указанных оффсетов, логирует его и возвращает полезную нагрузку.

        Внутри использует `consume_message(..., timeout=25)`.

        :param topic_partitions: Список объектов `TopicPartition` с актуальными оффсетами чтения.
        :return: Сырые байты сообщения или `None`, если за отведённое время ничего не пришло.
        """
        msg = self.consume_message(topic_partitions, timeout=25)
        logging.info(msg)
        return msg

    def subscribe_listen_new_offsets(self, topic):
        """Подписывается на топик и возвращает список партиций со следующими оффсетами чтения.

        Логика:
          1) подписаться на топик;
          2) получить перечень партиций топика;
          3) определить high watermark (текущий «конец» партиции) для каждой;
          4) вернуть `TopicPartition(topic, partition_id, next_offset)` — чтобы читать только новые сообщения.

        :param topic: Имя топика.
        :return: Список `TopicPartition` с оффсетами для чтения «с конца».
        """
        self.consumer.subscribe([topic])
        p_ids = self.consumer.list_topics(topic).topics[topic].partitions.keys()
        partitions_offsets_event = {k: self.get_last_offset(topic, k) for k in p_ids}
        logging.info("%s offsets: %s", topic, partitions_offsets_event)
        topic_partitions = [
            TopicPartition(topic, k, v) for k, v in partitions_offsets_event.items()
        ]
        return topic_partitions

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

    ##TODO к тесту @id("600004")
    # def advance_group_to_end_admin(self, topic: str, group_id: str, timeout: float = 10.0) -> Dict[int, int]:
    #     """
    #     Сдвигает оффсеты consumer-группы на конец топика (high watermark) через Admin API,
    #     не вступая в группу (без ребалансов).
    #     """
    #     # 1) Партиции топика
    #     md = self.admin.list_topics(topic, timeout=timeout)
    #     partitions: List[int] = list(md.topics[topic].partitions.keys())
    #
    #     # 2) Снять high watermark по всем партициям на «зондирующем» консюмере
    #     probe = Consumer({
    #         "bootstrap.servers": self.server_consumer,
    #         "group.id": f"offset-probe-{uuid4().hex}",
    #         "enable.auto.commit": False,
    #         "auto.offset.reset": "latest",
    #     })
    #     try:
    #         desired_tps: List[TopicPartition] = []
    #         result_map: Dict[int, int] = {}
    #         for p in partitions:
    #             _, high = probe.get_watermark_offsets(TopicPartition(topic, p), timeout=timeout)
    #             desired_tps.append(TopicPartition(topic, p, high))  # хотим зафиксировать offset=high
    #             result_map[p] = high
    #     finally:
    #         probe.close()
    #
    #     # 3) Сформировать запрос и применить
    #     req = [ConsumerGroupTopicPartitions(group_id=group_id, topic_partitions=desired_tps)]
    #     futures = self.admin.alter_consumer_group_offsets(req, request_timeout=timeout)
    #
    #     # 4) Дождаться завершения операции (если были ошибки — здесь выпадет исключение)
    #     for _grp, fut in futures.items():
    #         fut.result(timeout=timeout)
    #
    #     return result_map
    #
    # def list_group_offsets(self, group_id: str, topic: str, timeout: float = 10.0) -> Dict[int, int]:
    #     """
    #     ВернутьCommitted offsets группы group_id по указанному topic.
    #     Работает на confluent-kafka>=2.11: result() -> ConsumerGroupTopicPartitions.
    #     """
    #     # Запрашиваем offsets по всем партициям группы:
    #     req = [ConsumerGroupTopicPartitions(group_id=group_id)]
    #     futures = self.admin.list_consumer_group_offsets(req, request_timeout=timeout)
    #     out: Dict[int, int] = {}
    #
    #     # У нас один запрос -> один future
    #     for _req, fut in futures.items():
    #         cgtp = fut.result(timeout=timeout)  # <-- это ConsumerGroupTopicPartitions
    #         # Берем только нужный топик, извлекаем оффсеты из TopicPartition.offset
    #         for tp in cgtp.topic_partitions:
    #             if tp.topic == topic:
    #                 out[tp.partition] = tp.offset
    #     return out
