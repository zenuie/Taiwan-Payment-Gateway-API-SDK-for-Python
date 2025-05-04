import pytest
from payment_gateway_sdk.gateways.ecpay.security import EcpaySecurityHelper
from payment_gateway_sdk.gateways.ecpay.utils import (
    ecpay_url_encode,
)  # Import the specific util

# Use known test values (replace if you have official test vectors)
# These should match the ECPay documentation example if possible
TEST_HASH_KEY = "5294y06JbISpM5x9"
TEST_HASH_IV = "v77hoKGq4kWxNNIS"
TEST_PARAMS = {
    "MerchantID": "2000132",
    "MerchantTradeNo": "test12345",
    "MerchantTradeDate": "2023/01/01 12:00:00",
    "PaymentType": "aio",
    "TotalAmount": 150,
    "TradeDesc": "Test Order",
    "ItemName": "Product A#Product B",
    "ReturnURL": "https://test.com/return",
    "ChoosePayment": "Credit",
    "EncryptType": 1,
}
# Pre-calculated expected CheckMacValue for TEST_PARAMS with TEST_HASH_KEY/IV
# You MUST calculate this correctly based on ECPay's exact algorithm (sort, add key/iv, encode, lowercase, sha256, uppercase)
# Example (CALCULATE THIS VALUE ACCURATELY FOR YOUR TEST PARAMS):
EXPECTED_MAC = "15A754F8059654F49230A75A83BC8A168EC4979161204B2B3D405C5ACDB4573E"  # <<< REPLACE WITH CORRECT VALUE


@pytest.fixture
def security_helper():
    """Provides an instance of EcpaySecurityHelper."""
    return EcpaySecurityHelper(hash_key=TEST_HASH_KEY, hash_iv=TEST_HASH_IV)


def test_calculate_check_mac_value(security_helper):
    """Test the calculation of the CheckMacValue."""
    calculated_mac = security_helper.calculate_check_mac_value(TEST_PARAMS.copy())
    assert calculated_mac == EXPECTED_MAC


def test_verify_check_mac_value_valid(security_helper):
    """Test verification with a valid CheckMacValue."""
    received_params = TEST_PARAMS.copy()
    received_params["CheckMacValue"] = EXPECTED_MAC
    assert security_helper.verify_check_mac_value(received_params) is True


def test_verify_check_mac_value_invalid(security_helper):
    """Test verification with an invalid CheckMacValue."""
    received_params = TEST_PARAMS.copy()
    received_params["CheckMacValue"] = "INVALIDMAC123"
    assert security_helper.verify_check_mac_value(received_params) is False


def test_verify_check_mac_value_case_insensitive(security_helper):
    """Test that verification is case-insensitive for the MAC itself (should fail if calculation output is different case)."""
    received_params = TEST_PARAMS.copy()
    # Note: compare_digest handles the comparison securely, case matters unless pre-normalized
    received_params["CheckMacValue"] = EXPECTED_MAC.lower()
    # Verification should fail because calculated MAC is uppercase
    assert security_helper.verify_check_mac_value(received_params) is False


def test_verify_check_mac_value_missing(security_helper):
    """Test verification when CheckMacValue is missing."""
    received_params = TEST_PARAMS.copy()
    # CheckMacValue key is absent
    assert security_helper.verify_check_mac_value(received_params) is False


def test_init_missing_credentials():
    """Test initialization fails with missing key or iv."""
    with pytest.raises(ValueError):
        EcpaySecurityHelper(hash_key="", hash_iv=TEST_HASH_IV)
    with pytest.raises(ValueError):
        EcpaySecurityHelper(hash_key=TEST_HASH_KEY, hash_iv="")


# Add more tests for ecpay_url_encode if it had complex logic (it's simple now)
# def test_ecpay_url_encode_specific_chars(): ...
