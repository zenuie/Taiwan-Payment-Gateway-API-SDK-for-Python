import pytest
from unittest.mock import MagicMock, patch

from payment_gateway_sdk.gateways.ecpay.adapter import EcpayAdapter
from payment_gateway_sdk.gateways.ecpay.dao import EcpayDAO
from payment_gateway_sdk.gateways.ecpay.dto import *  # Import all local DTOs
from payment_gateway_sdk.gateways.ecpay.constants import *  # Import constants
from payment_gateway_sdk.schema.dto.payment import (
    PaymentStatus,
    RedirectMethod,
    AtmPaymentInfo,
)  # Generic schema DTOs
from payment_gateway_sdk.schema.dto.transaction import (
    QueryInput,
    QueryOutput,
    TransactionRecord,
    PaymentInfoQueryOutput,
)  # Generic schema DTOs
from payment_gateway_sdk.core.exceptions import ValidationError, GatewayError

MOCK_FORM_DATA = {"Field1": "Value1", "CheckMacValue": "GENERATED_MAC"}
MOCK_BASE_URL = "https://payment-stage.ecpay.com.tw"
MOCK_CHECKOUT_ENDPOINT = "/Cashier/AioCheckOut/V5"


@pytest.fixture
def mock_dao():
    """Fixture for a mocked EcpayDAO."""
    dao = MagicMock(spec=EcpayDAO)
    dao.base_url = MOCK_BASE_URL
    # Configure mock return values for specific methods as needed in tests
    dao.build_checkout_form_data.return_value = MOCK_FORM_DATA
    # Mock successful action response by default
    dao.send_action_request.return_value = {
        "RtnCode": "1",
        "RtnMsg": "Success",
        "MerchantTradeNo": "mtn1",
        "TradeNo": "tn1",
    }
    # Mock successful query response by default
    dao.send_query_order_request.return_value = {
        "MerchantID": "mid",
        "MerchantTradeNo": "mtn1",
        "TradeNo": "tn1",
        "TradeAmt": "100",
        "PaymentType": "Credit_CreditCard",
        "TradeStatus": "1",
        "PaymentDate": "2023/11/15 12:00:00",
        "TradeDate": "2023/11/15 11:59:00",
        "RtnMsg": "Success",
        "CheckMacValue": "VALIDMAC",  # Assuming DAO verifies response MAC internally
    }
    # Mock successful payment info query response by default
    dao.send_query_payment_info_request.return_value = {
        "RtnCode": EcpayRtnCode.ATM_SUCCESS,
        "RtnMsg": "Success",
        "MerchantTradeNo": "atm123",
        "TradeNo": "tn2",
        "PaymentType": "ATM_BOT",
        "BankCode": "007",
        "vAccount": "9991234567890",
        "ExpireDate": "2023/11/20",
        "CheckMacValue": "VALIDMAC",
    }
    return dao


@pytest.fixture
def adapter(mock_dao):
    """Fixture for EcpayAdapter with mocked DAO."""
    return EcpayAdapter(dao=mock_dao)


# --- Payment Method Tests ---


def test_pay_with_atm_success(adapter, mock_dao):
    """Test successful ATM payment initiation."""
    order_id = "ATMSuccess1"
    input_dto = EcpayAtmPaymentInput(
        order_id=order_id,
        amount=300,
        currency="TWD",
        details="Test ATM",
        return_url="https://test.com/ret",
    )
    output = adapter.pay_with_atm(input_dto)

    assert output.success is True
    assert output.status == PaymentStatus.PENDING
    assert output.redirect_url == MOCK_BASE_URL + MOCK_CHECKOUT_ENDPOINT
    assert output.redirect_method == RedirectMethod.POST
    assert output.redirect_form_data == MOCK_FORM_DATA
    assert output.order_id == order_id

    # Check parameters passed to DAO's build_checkout_form_data
    mock_dao.build_checkout_form_data.assert_called_once()
    call_args, _ = mock_dao.build_checkout_form_data.call_args
    passed_params = call_args[0]
    assert passed_params["ChoosePayment"] == EcpayPaymentMethod.ATM
    assert passed_params["MerchantTradeNo"] == order_id
    assert passed_params["TotalAmount"] == 300
    assert passed_params["ExpireDate"] == 3  # Default value


def test_pay_with_credit_periodic_validation_fail(adapter):
    """Test validation failure for periodic credit payment (amount mismatch)."""
    order_id = "PeriodFail1"
    # TotalAmount != PeriodAmount should fail validation in DTO/Adapter
    with pytest.raises(ValidationError):
        EcpayCreditPaymentInput(
            order_id=order_id,
            amount=100,
            currency="TWD",
            details="Fail",
            return_url="url",
            period_amount=99,
            period_type="M",
            frequency=1,
            exec_times=2,
        )
    # Alternatively, if adapter catches it and returns PaymentOutput:
    # input_dto = ... (create invalid DTO instance carefully, maybe skip validation if possible for test)
    # output = adapter.pay_with_credit(input_dto)
    # assert output.success is False
    # assert output.status == PaymentStatus.ERROR
    # assert "TotalAmount must be equal to PeriodAmount" in output.message


def test_pay_all_options_with_ignore(adapter, mock_dao):
    """Test pay_all_options with ignored methods."""
    order_id = "AllIgnore1"
    input_dto = EcpayBasePaymentInput(
        order_id=order_id,
        amount=500,
        currency="TWD",
        details="All with Ignore",
        return_url="https://test.com/ret",
    )
    ignore_list = [EcpayPaymentMethod.BNPL, EcpayPaymentMethod.WEBATM]
    output = adapter.pay_all_options(input_dto, ignore_methods=ignore_list)

    assert output.success is True
    mock_dao.build_checkout_form_data.assert_called_once()
    call_args, _ = mock_dao.build_checkout_form_data.call_args
    passed_params = call_args[0]
    assert passed_params["ChoosePayment"] == EcpayPaymentMethod.ALL
    assert (
        passed_params["IgnorePayment"]
        == f"{EcpayPaymentMethod.BNPL}#{EcpayPaymentMethod.WEBATM}"
    )


def test_payment_initiation_dao_error(adapter, mock_dao):
    """Test handling of DAO errors during payment initiation."""
    order_id = "DaoError1"
    mock_dao.build_checkout_form_data.side_effect = GatewayError(
        "DAO failed", code="D101"
    )
    input_dto = EcpayAtmPaymentInput(
        order_id=order_id,
        amount=100,
        currency="TWD",
        details="DAO Error Test",
        return_url="url",
    )
    output = adapter.pay_with_atm(input_dto)

    assert output.success is False
    assert output.status == PaymentStatus.ERROR
    assert "DAO failed" in output.message
    assert output.error_code == "D101"


# Add similar tests for other pay_with_* methods, testing different parameters and validation rules

# --- Transaction Query Tests ---


def test_query_transaction_success(adapter, mock_dao):
    """Test successful generic transaction query."""
    order_id = "QuerySuccess1"
    input_dto = QueryInput(order_id=order_id)
    # Mock DAO response (already mocked in fixture, can override if needed)
    mock_dao.send_query_order_request.return_value = {
        "MerchantID": "mid",
        "MerchantTradeNo": order_id,
        "TradeNo": "TN_QSUCCESS",
        "TradeAmt": "150",
        "PaymentType": "ATM_BOT",
        "TradeStatus": "0",  # 0 means PENDING for ATM
        "PaymentDate": "",
        "TradeDate": "2023/11/15 14:00:00",
        "RtnMsg": "Query Success",
        "CheckMacValue": "VALIDMAC",
    }
    output = adapter.query_transaction(input_dto)

    assert output.success is True
    assert len(output.transactions) == 1
    tx = output.transactions[0]
    assert tx.order_id == order_id
    assert tx.gateway_trade_no == "TN_QSUCCESS"
    assert tx.status == PaymentStatus.PENDING  # Correctly mapped from 0 for ATM
    assert tx.amount == 150
    assert tx.payment_type == "ATM_BOT"
    mock_dao.send_query_order_request.assert_called_once_with(
        {"MerchantTradeNo": order_id}
    )


def test_query_transaction_paid(adapter, mock_dao):
    """Test generic query result for a paid transaction."""
    order_id = "QueryPaid1"
    input_dto = QueryInput(order_id=order_id)
    mock_dao.send_query_order_request.return_value = {
        "MerchantTradeNo": order_id,
        "TradeNo": "TN_PAID",
        "TradeAmt": "200",
        "PaymentType": "Credit_CreditCard",
        "TradeStatus": "1",  # 1 is SUCCESS
        "PaymentDate": "2023/11/15 14:05:00",
        "TradeDate": "2023/11/15 14:04:00",
        "auth_code": "777777",
        "card4no": "1111",  # Example extra info
        "RtnMsg": "Success",
        "CheckMacValue": "VALIDMAC",
    }
    output = adapter.query_transaction(input_dto)
    assert output.success is True
    assert len(output.transactions) == 1
    tx = output.transactions[0]
    assert tx.status == PaymentStatus.SUCCESS
    assert tx.amount == 200
    assert tx.auth_code == "777777"
    assert tx.card_last_four == "1111"


def test_query_transaction_dao_error(adapter, mock_dao):
    """Test generic query when DAO raises an error."""
    order_id = "QueryFailDao1"
    input_dto = QueryInput(order_id=order_id)
    mock_dao.send_query_order_request.side_effect = GatewayError(
        "Query failed", code="ECP101"
    )
    output = adapter.query_transaction(input_dto)

    assert output.success is False
    assert len(output.transactions) == 0
    assert "Query failed" in output.message
    assert output.error_code == "ECP101"


def test_query_payment_info_success_atm(adapter, mock_dao):
    """Test successful query for ATM payment info."""
    order_id = "QueryInfoATM1"
    input_dto = QueryInput(order_id=order_id)
    # Mock response already set in fixture, reuse it
    output: PaymentInfoQueryOutput = adapter.query_payment_info(input_dto)

    assert output.success is True
    assert output.merchant_trade_no == "atm123"  # From mock
    assert output.payment_method_name == "ATM_BOT"
    assert isinstance(output.payment_info, AtmPaymentInfo)
    assert output.payment_info.bank_code == "007"
    assert output.payment_info.virtual_account == "9991234567890"
    assert output.payment_info.expire_date == "2023/11/20"
    mock_dao.send_query_payment_info_request.assert_called_once_with(
        {"MerchantTradeNo": order_id}
    )


# Add tests for query_payment_info failure, CVS/Barcode types, other query methods...

# --- Transaction Action Tests ---


def test_refund_success(adapter, mock_dao):
    """Test successful refund action."""
    input_dto = EcpayRefundInput(
        merchant_trade_no="RefundMTN1", gateway_trade_no="RefundTN1", refund_amount=100
    )
    # Mock DAO response (already mocked to succeed in fixture, can override if needed)
    output = adapter.refund(input_dto)

    assert output.success is True
    assert output.status == PaymentStatus.REFUNDED
    assert output.message == "Success"
    assert output.merchant_trade_no == "mtn1"  # From mock response
    assert output.gateway_trade_no == "tn1"

    # Check parameters passed to DAO
    expected_dao_call = {
        "MerchantTradeNo": "RefundMTN1",
        "TradeNo": "RefundTN1",
        "Action": EcpayAction.REFUND,
        "TotalAmount": 100,
    }
    mock_dao.send_action_request.assert_called_once_with(expected_dao_call)


def test_capture_failure_dao(adapter, mock_dao):
    """Test capture action when DAO returns failure."""
    input_dto = EcpayCaptureInput(
        merchant_trade_no="CaptureFail1",
        gateway_trade_no="CaptureFailTN1",
        capture_amount=200,
    )
    # Mock DAO failure response
    mock_dao.send_action_request.return_value = {
        "RtnCode": "10200005",
        "RtnMsg": "Capture amount error",
    }
    output = adapter.capture(input_dto)

    assert output.success is False
    assert output.status == PaymentStatus.FAILED
    assert "Capture amount error" in output.message
    assert output.error_code == "10200005"


# Add tests for other actions (cancel, abandon) and DAO errors during actions...

# --- Test Generic Action (Optional, depending on strategy) ---
# def test_adapter_generic_refund_raises_not_implemented(adapter):
#    """Test that the generic refund method raises NotImplementedError."""
#    generic_input = ActionInput(gateway_trade_no="tn", action_type="REFUND", amount=10)
#    with pytest.raises(NotImplementedError):
#        adapter.refund(generic_input) # Assuming TransactionAdapter.refund is abstract or raises
