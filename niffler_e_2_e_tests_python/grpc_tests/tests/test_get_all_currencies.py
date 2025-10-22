import allure
import pytest
from google.protobuf import empty_pb2

from niffler_e_2_e_tests_python.grpc_tests.internal.pb.niffler_currency_pb2_pbreflect import (
    NifflerCurrencyServiceClient,
)


@allure.feature("Currencies")
@allure.story("Get all currencies")
@pytest.mark.grpc
def test_get_all_currencies(grpc_client: NifflerCurrencyServiceClient) -> None:
    response = grpc_client.get_all_currencies(empty_pb2.Empty())
    assert len(response.allCurrencies) == 4
