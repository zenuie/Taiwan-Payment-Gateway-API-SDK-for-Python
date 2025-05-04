import pytest
from unittest.mock import patch, MagicMock
import requests
from urllib.parse import urlencode, parse_qs

from payment_gateway_sdk.gateways.ecpay.dao import EcpayDAO
from payment_gateway_sdk.gateways.ecpay.security import EcpaySecurityHelper # Need real or mock helper
from payment_gateway_sdk.core.exceptions import GatewayError, AuthenticationError, ValidationError

# --- Test Configuration ---
TEST_CONFIG_SANDBOX = {
    'merchant_id': '2000132',
    'hash_key': '5294y06JbISpM5x9',
    'hash_iv': 'v77hoKGq4kWxNNIS',
    'base_url': 'https://payment-stage.ecpay.com.tw', # Set by factory normally
    'timeout': 10
}
MOCK_MAC = "MOCKCHECKSUMVALUEGENERATEDBYHELPER"

@pytest.fixture
def mock_security_helper():
    """Fixture for a mocked EcpaySecurityHelper."""
    helper = MagicMock(spec=EcpaySecurityHelper)
    helper.calculate_check_mac_value.return_value = MOCK_MAC
    helper.verify_check_mac_value.return_value = True # Assume valid by default for DAO tests
    return helper

@pytest.fixture
def ecpay_dao(mock_security_helper):
    """Fixture for EcpayDAO instance with mocked security helper."""
    return EcpayDAO(config=TEST_CONFIG_SANDBOX, security_helper=mock_security_helper)

# --- Tests ---

def test_dao_init_success(mock_security_helper):
    """Test successful DAO initialization."""
    dao = EcpayDAO(config=TEST_CONFIG_SANDBOX, security_helper=mock_security_helper)
    assert dao.merchant_id == TEST_CONFIG_SANDBOX['merchant_id']
    assert dao.base_url == TEST_CONFIG_SANDBOX['base_url']
    assert dao.security_helper is mock_security_helper

def test_dao_init_missing_config():
    """Test DAO initialization with missing config keys."""
    with pytest.raises(AuthenticationError): # MerchantID missing raises Auth error
        EcpayDAO(config={'hash_key': 'k', 'hash_iv': 'i', 'base_url': 'u'}, security_helper=MagicMock())
    with pytest.raises(ValueError): # base_url missing raises ValueError
        EcpayDAO(config={'merchant_id': 'm', 'hash_key': 'k', 'hash_iv': 'i'}, security_helper=MagicMock())

def test_build_checkout_form_data(ecpay_dao, mock_security_helper):
    """Test building the checkout form data dictionary."""
    params = {
        'MerchantTradeNo': 't123', 'MerchantTradeDate': 'd', 'PaymentType': 'aio',
        'TotalAmount': 100, 'TradeDesc': 'desc', 'ItemName': 'item',
        'ReturnURL': 'url', 'ChoosePayment': 'ATM', 'EncryptType': 1
    }
    expected_params_with_mac = params.copy()
    expected_params_with_mac['MerchantID'] = TEST_CONFIG_SANDBOX['merchant_id']
    expected_params_with_mac['CheckMacValue'] = MOCK_MAC

    form_data = ecpay_dao.build_checkout_form_data(params.copy()) # Pass copy

    # Assert security helper was called correctly
    mock_security_helper.calculate_check_mac_value.assert_called_once()
    call_args, _ = mock_security_helper.calculate_check_mac_value.call_args
    # Check if MerchantID was added *before* calculating MAC
    assert call_args[0]['MerchantID'] == TEST_CONFIG_SANDBOX['merchant_id']

    # Assert final form data is correct
    assert form_data == expected_params_with_mac

def test_verify_callback_data(ecpay_dao, mock_security_helper):
    """Test that verify_callback_data delegates to the security helper."""
    callback_data = {'key': 'value', 'CheckMacValue': 'abc'}
    ecpay_dao.verify_callback_data(callback_data)
    mock_security_helper.verify_check_mac_value.assert_called_once_with(callback_data)

# --- Test _send_api_request and specific methods ---

@patch('payment_gateway_sdk.gateways.ecpay.dao.requests.post')
def test_send_query_order_request_success(mock_post, ecpay_dao, mock_security_helper):
    """Test successful query order request."""
    mock_response = MagicMock()
    # Simulate ECPay's urlencoded response
    response_dict = {
        'MerchantID': TEST_CONFIG_SANDBOX['merchant_id'], 'MerchantTradeNo': 'query123',
        'TradeNo': 'ecp456', 'TradeAmt': '200', 'PaymentType': 'Credit_CreditCard',
        'TradeStatus': '1', 'RtnMsg': 'Success', 'CheckMacValue': MOCK_MAC # Assume response also has MAC
    }
    mock_response.text = urlencode(response_dict)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock() # No HTTP error
    mock_post.return_value = mock_response

    # Assume response MAC verification is also needed and mocked to pass
    mock_security_helper.verify_check_mac_value.return_value = True

    query_data = {'MerchantTradeNo': 'query123'}
    result = ecpay_dao.send_query_order_request(query_data.copy())

    # Assert requests.post called correctly
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['url'] == TEST_CONFIG_SANDBOX['base_url'] + '/Cashier/QueryTradeInfo/V5'
    sent_data_parsed = parse_qs(kwargs['data']) # requests sends data urlencoded
    assert sent_data_parsed['MerchantID'][0] == TEST_CONFIG_SANDBOX['merchant_id']
    assert sent_data_parsed['MerchantTradeNo'][0] == 'query123'
    assert 'TimeStamp' in sent_data_parsed
    assert sent_data_parsed['CheckMacValue'][0] == MOCK_MAC # Check if calculated MAC was sent

    # Assert security helper verify was called for the response
    mock_security_helper.verify_check_mac_value.assert_called_once_with(response_dict)

    # Assert parsed result
    assert result['MerchantTradeNo'] == 'query123'
    assert result['TradeStatus'] == '1'
    assert result['TradeAmt'] == '200' # DAO returns strings as parsed

@patch('payment_gateway_sdk.gateways.ecpay.dao.requests.post')
def test_send_action_request_fail_rtncode(mock_post, ecpay_dao, mock_security_helper):
    """Test action request failure due to ECPay RtnCode."""
    mock_response = MagicMock()
    response_dict = {
        'MerchantID': TEST_CONFIG_SANDBOX['merchant_id'], 'MerchantTradeNo': 'action123',
        'TradeNo': 'ecp789', 'RtnCode': '10200047', 'RtnMsg': 'Refund failed',
        'CheckMacValue': MOCK_MAC
    }
    mock_response.text = urlencode(response_dict)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response
    mock_security_helper.verify_check_mac_value.return_value = True # Assume MAC is valid

    action_data = {
        'MerchantTradeNo': 'action123', 'TradeNo': 'ecp789',
        'Action': 'R', 'TotalAmount': 50
    }

    with pytest.raises(GatewayError) as excinfo:
        ecpay_dao.send_action_request(action_data.copy())

    assert excinfo.value.code == '10200047'
    assert 'Refund failed' in excinfo.value.message
    assert excinfo.value.raw_response == response_dict
    # Verify MAC was checked before raising error
    mock_security_helper.verify_check_mac_value.assert_called_once_with(response_dict)


@patch('payment_gateway_sdk.gateways.ecpay.dao.requests.post')
def test_send_api_request_timeout(mock_post, ecpay_dao):
    """Test handling of requests.exceptions.Timeout."""
    mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
    with pytest.raises(GatewayError, match=r'timeout \(10s\)'):
        # Use a method that calls _send_api_request, like query
        ecpay_dao.send_query_order_request({'MerchantTradeNo': 'timeout123'})

@patch('payment_gateway_sdk.gateways.ecpay.dao.requests.post')
def test_send_api_request_http_error(mock_post, ecpay_dao):
    """Test handling of HTTP 4xx/5xx errors."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_post.return_value = mock_response
    with pytest.raises(GatewayError, match=r'API communication error'):
        ecpay_dao.send_query_order_request({'MerchantTradeNo': 'http500'})

@patch('payment_gateway_sdk.gateways.ecpay.dao.requests.post')
def test_send_api_invalid_response_mac(mock_post, ecpay_dao, mock_security_helper):
    """Test failure when received CheckMacValue is invalid."""
    mock_response = MagicMock()
    response_dict = {'RtnCode': '1', 'RtnMsg': 'Success', 'CheckMacValue': 'INVALIDRECEIVEDMAC'}
    mock_response.text = urlencode(response_dict)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Mock verify to return False
    mock_security_helper.verify_check_mac_value.return_value = False

    with pytest.raises(AuthenticationError, match=r'Invalid CheckMacValue received'):
         # Using query as an example API call
        ecpay_dao.send_query_order_request({'MerchantTradeNo': 'badmac123'})

    mock_security_helper.verify_check_mac_value.assert_called_once_with(response_dict)


# Add similar tests for other specific DAO methods like:
# - test_send_query_payment_info_request_success_atm
# - test_send_query_payment_info_request_success_cvs
# - test_send_query_credit_details_request_success (check JSON parsing)
# - test_send_query_periodic_details_request_success (check JSON parsing)
# - Test cases where required parameters for specific methods are missing (should raise ValidationError)