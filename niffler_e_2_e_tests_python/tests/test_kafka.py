import json
import logging
import time

from allure import epic, id, step, suite, tag, title
from faker import Faker

from niffler_e_2_e_tests_python.models.config import Envs
from niffler_e_2_e_tests_python.models.user import UserName


@epic("[KAFKA][niffler-auth]: Паблишинг сообщений в кафку")
@suite("[KAFKA][niffler-auth]: Паблишинг сообщений в кафку")
class TestAuthRegistrationKafkaTest:
    @id("600001")
    @title(
        "KAFKA: Сообщение с пользователем публикуется в Kafka после успешной регистрации"
    )
    @tag("KAFKA")
    def test_message_should_be_produced_to_kafka_after_successful_registration(
        self, auth_client, kafka, envs: Envs
    ):
        username = Faker().user_name()
        password = Faker().password(special_chars=False)

        topic_partitions = kafka.subscribe_listen_new_offsets("users")

        result = auth_client.registration(username, password, envs=envs)
        assert result.status_code == 201

        event = kafka.log_msg_and_json(topic_partitions)

        with step("Check that message from kafka exist"):
            assert event != "" and event != b""

        with step("Check message content"):
            UserName.model_validate(json.loads(event.decode("utf8")))
            assert json.loads(event.decode("utf8"))["username"] == username

    @id("600002")
    @title(
        "KAFKA/USERDATA: сервис забирает сообщение из топика users и пишет пользователя в БД"
    )
    @tag("KAFKA")
    def test_niffler_userdata_should_consume_message_from_kafka(self, kafka, db_client):
        with step("Отправляем сообщение в топик users"):
            username = Faker().user_name()
            logging.info(f"Отправляем сообщение по пользователю: {username}")
            kafka.sending_message("users", username)
        try:
            with step("Ждём появление записи о пользователе в БД"):
                user = db_client.wait_for_user_appears(username, timeout=25)
                assert user.username == username

            with step("Проверяем, что запись единственная"):
                assert db_client.count_users_by_username(username) == 1
        finally:
            db_client.delete_user_by_username(username)

    @id("600003")
    @title(
        "KAFKA/USERDATA: повторная публикация того же пользователя не создаёт дубль (идемпотентность)"
    )
    @tag("KAFKA")
    def test_userdata_is_idempotent_on_duplicate_events(self, kafka, db_client):
        username = Faker().user_name()

        try:
            with step("Публикуем пользователя первый раз"):
                kafka.sending_message("users", username)
                user1 = db_client.wait_for_user_appears(username, timeout=25)
                first_count = db_client.count_users_by_username(username)
                assert first_count == 1

            with step("Публикуем пользователя второй раз"):
                kafka.sending_message("users", username)
                time.sleep(1.0)
                second_count = db_client.count_users_by_username(username)
                assert (
                    second_count == 1
                ), "Повторное сообщение не должно создавать дубликат записи"

            with step("ID записи не изменился (если БД хранит то же id/primary key)"):
                user2 = db_client.wait_for_user_appears(username, timeout=5)
                assert user2.id == user1.id

        finally:
            db_client.delete_user_by_username(username)

    ##TODO Тест проходит успешно но из-за него докер контейнер начинает заполняться логами, поэтому тест либо надо убирать
    ##либо править нифлер чтобы не сыпал логами при отправке невалидного сообщения
    # @id("600004")
    # @title("KAFKA/USERDATA: невалидные сообщения игнорируются и не приводят к записи в БД")
    # @tag("KAFKA")
    # def test_userdata_ignores_invalid_messages(self, kafka, db_client,envs):
    #         bogus_username = Faker().user_name()
    #
    #         try:
    #                 with step("Шлём невалидный JSON (сырой текст) в users"):
    #                         kafka.producer.produce(
    #                                 "users",
    #                                 value=b"not a json",
    #                                 on_delivery=kafka.delivery_report,
    #                                 headers={"__TypeId__": "guru.qa.niffler.model.UserJson"},
    #                         )
    #                         kafka.producer.flush(5)
    #
    #                 with step("Убеждаемся, что запись НЕ появилась"):
    #                         time.sleep(2.0)
    #                         assert db_client.get_user_by_username(bogus_username) is None
    #                         assert db_client.count_users_by_username(bogus_username) == 0
    #
    #                 with step("Шлём валидный JSON, но без поля username"):
    #                         kafka.producer.produce(
    #                                 "users",
    #                                 value=json.dumps({"foo": "bar"}).encode("utf-8"),
    #                                 on_delivery=kafka.delivery_report,
    #                                 headers={"__TypeId__": "guru.qa.niffler.model.UserJson"},
    #                         )
    #                         kafka.producer.flush(5)
    #
    #                 with step("Снова убеждаемся, что записи нет"):
    #                         time.sleep(2.0)
    #                         assert db_client.get_user_by_username(bogus_username) is None
    #
    #         finally:
    #                 kafka.advance_group_to_end_admin(topic="users", group_id=envs.userdata_group_id)
    #                 kafka.list_group_offsets(envs.userdata_group_id, "users")
    #                 db_client.delete_user_by_username(bogus_username)

    @id("600005")
    @title(
        "KAFKA/USERDATA: обрабатывает несколько сообщений подряд и создаёт все записи"
    )
    @tag("KAFKA")
    def test_userdata_handles_multiple_messages(self, kafka, db_client):
        users = [Faker().user_name() for _ in range(3)]
        try:
            with step("Чистим возможные хвосты в БД по этим именинам"):
                for u in users:
                    db_client.delete_user_by_username(u)

            with step("Публикуем пачку сообщений"):
                for u in users:
                    kafka.sending_message("users", u)

            with step("Проверяем, что все пользователи появились в БД"):
                for u in users:
                    user = db_client.wait_for_user_appears(u, timeout=25)
                    assert user.username == u
                    assert db_client.count_users_by_username(u) == 1
        finally:
            for u in users:
                db_client.delete_user_by_username(u)
