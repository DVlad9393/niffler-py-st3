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
def test_calculate_rate(grpc_client: NifflerCurrencyServiceClient) -> None:
    response = grpc_client.calculate_rate(
        request=CalculateRequest(
            spendCurrency=CurrencyValues.EUR,
            desiredCurrency=CurrencyValues.RUB,
            amount=100.0,
        )
    )
    assert response.calculatedAmount == 7200, "Expected calculated amount to be 7200"


@allure.feature("Currencies")
@allure.story("Calculate rate")
@pytest.mark.grpc
def test_calculate_rate_without_desired_currency(
    grpc_client: NifflerCurrencyServiceClient,
) -> None:
    try:
        grpc_client.calculate_rate(
            request=CalculateRequest(
                spendCurrency=CurrencyValues.EUR,
                amount=100.0,
            )
        )
    except grpc.RpcError as e:
        assert e.code() == grpc.StatusCode.UNKNOWN, "Expected grpc error"
        assert e.details() == "Application error processing RPC"


@allure.feature("Currencies")
@allure.story("Calculate rate")
@pytest.mark.grpc
@pytest.mark.parametrize(
    "spend, spend_currency, desired_currency, expected_result",
    (
        (100.0, CurrencyValues.USD, CurrencyValues.RUB, 6666.67),
        (100.0, CurrencyValues.RUB, CurrencyValues.USD, 1.5),
        (100.0, CurrencyValues.USD, CurrencyValues.USD, 100.0),
    ),
)
def test_currency_conversion(
    grpc_client: NifflerCurrencyServiceClient,
    spend: float,
    spend_currency: CurrencyValues,
    desired_currency: CurrencyValues,
    expected_result: float,
) -> None:
    response = grpc_client.calculate_rate(
        request=CalculateRequest(
            spendCurrency=spend_currency,
            desiredCurrency=desired_currency,
            amount=spend,
        )
    )
    assert (
        response.calculatedAmount == expected_result
    ), f"Expected calculated amount to be {expected_result}]"
