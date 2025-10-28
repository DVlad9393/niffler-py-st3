import allure
import grpc
import pytest

from niffler_e_2_e_tests_python.grpc_tests.internal.pb.niffler_currency_pb2 import (
    CalculateRequest,
    CurrencyValues,
)
from niffler_e_2_e_tests_python.grpc_tests.internal.pb.niffler_currency_pb2_pbreflect import (
    NifflerCurrencyServiceClient,
)


@allure.feature("Currencies")
@allure.story("Calculate rate")
@pytest.mark.grpc
class TestCurrencyRate:
    """Тесты gRPC-методов NifflerCurrencyService для расчёта валютных курсов."""

    def test_calculate_rate(self, grpc_client: NifflerCurrencyServiceClient) -> None:
        """Проверка корректного расчёта курса при заданных валютах EUR→RUB."""
        request = CalculateRequest(
            spendCurrency=CurrencyValues.EUR,
            desiredCurrency=CurrencyValues.RUB,
            amount=100.0,
        )

        response = grpc_client.calculate_rate(request)

        assert (
            response.calculatedAmount == 7200
        ), "Expected calculated amount to be 7200"

    def test_calculate_rate_without_desired_currency(
        self, grpc_client: NifflerCurrencyServiceClient
    ) -> None:
        """Проверка поведения при отсутствии целевой валюты (должен быть gRPC-ошибкой)."""
        request = CalculateRequest(
            spendCurrency=CurrencyValues.EUR,
            amount=100.0,
        )

        with pytest.raises(grpc.RpcError) as e:
            grpc_client.calculate_rate(request)

        assert e.value.code() == grpc.StatusCode.UNKNOWN, "Expected grpc error"
        assert e.value.details() == "Application error processing RPC"

    @pytest.mark.parametrize(
        "spend, spend_currency, desired_currency, expected_result",
        [
            (100.0, CurrencyValues.USD, CurrencyValues.RUB, 6666.67),
            (100.0, CurrencyValues.RUB, CurrencyValues.USD, 1.5),
            (100.0, CurrencyValues.USD, CurrencyValues.USD, 100.0),
        ],
    )
    def test_currency_conversion(
        self,
        grpc_client: NifflerCurrencyServiceClient,
        spend: float,
        spend_currency: CurrencyValues,
        desired_currency: CurrencyValues,
        expected_result: float,
    ) -> None:
        """Проверка пересчёта валют для разных направлений конверсии."""
        request = CalculateRequest(
            spendCurrency=spend_currency,
            desiredCurrency=desired_currency,
            amount=spend,
        )

        response = grpc_client.calculate_rate(request)

        assert (
            response.calculatedAmount == expected_result
        ), f"Expected calculated amount to be {expected_result}"
