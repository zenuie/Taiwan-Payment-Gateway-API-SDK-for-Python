import pytest
from unittest.mock import patch, MagicMock

from payment_gateway_sdk.gateways.ecpay import EcpayDAO
from payment_gateway_sdk.schema.gateway import GatewayFactory
from payment_gateway_sdk.gateways.ecpay.adapter import EcpayAdapter
from payment_gateway_sdk.gateways.tappay.adapter import TappayAdapter
from payment_gateway_sdk.core.exceptions import PaymentGatewayBaseError

# Mock configurations
MOCK_CONFIG = {
    "sdk_settings": {"default_timeout": 20},
    "ecpay": {
        "merchant_id": "ECMOCK123",
        "hash_key": "eckey",
        "hash_iv": "eciv",
        "is_sandbox": True,
    },
    "tappay": {
        "partner_key": "tapkey",
        "merchant_id": "TAPMOCK456",
        "is_sandbox": False,
    },
}


@pytest.fixture
def factory():
    """Provides a GatewayFactory instance initialized with mock config."""
    # Reset caches for each test if necessary, though Factory creates instances on demand
    return GatewayFactory(config=MOCK_CONFIG)


# Patch the actual loading and instantiation within the factory's methods
@patch("payment_gateway_sdk.schema.gateway.importlib.import_module")
@patch("payment_gateway_sdk.gateways.ecpay.dao.EcpayDAO")  # Patch DAO constructor
@patch(
    "payment_gateway_sdk.gateways.ecpay.security.EcpaySecurityHelper"
)  # Patch Helper constructor
@patch(
    "payment_gateway_sdk.gateways.ecpay.adapter.EcpayAdapter"
)  # Patch Adapter constructor
def test_get_adapter_ecpay_sandbox(
    mock_ecpay_adapter_cls,
    mock_ecpay_helper_cls,
    mock_ecpay_dao_cls,
    mock_import_module,
    factory,
):
    """Test getting ECPay adapter for sandbox."""
    # Configure mocks (instances are created inside the factory)
    mock_dao_instance = MagicMock()
    mock_helper_instance = MagicMock()
    mock_adapter_instance = MagicMock()
    mock_ecpay_dao_cls.return_value = mock_dao_instance
    mock_ecpay_helper_cls.return_value = mock_helper_instance
    mock_ecpay_adapter_cls.return_value = mock_adapter_instance

    # Mock importlib if needed, though patching constructors might be enough
    # mock_import_module.return_value...

    adapter = factory.get_adapter("ecpay")

    # Check correct classes were instantiated with correct args
    mock_ecpay_helper_cls.assert_called_once_with(hash_key="eckey", hash_iv="eciv")
    # Check config passed to DAO (should include calculated base_url)
    mock_ecpay_dao_cls.assert_called_once()
    _, kwargs_dao = mock_ecpay_dao_cls.call_args
    assert kwargs_dao["config"]["merchant_id"] == "ECMOCK123"
    assert (
        kwargs_dao["config"]["base_url"] == "https://payment-stage.ecpay.com.tw"
    )  # Sandbox URL
    assert kwargs_dao["config"]["timeout"] == 20  # From sdk_settings
    assert kwargs_dao["security_helper"] is mock_helper_instance

    # Check DAO instance injected into Adapter
    mock_ecpay_adapter_cls.assert_called_once_with(dao=mock_dao_instance)

    # Check returned instance is the mocked one
    assert adapter is mock_adapter_instance
    # assert isinstance(adapter, EcpayAdapter) # This would fail with MagicMock, check mock instance instead


@patch("payment_gateway_sdk.schema.gateway.importlib.import_module")
@patch("payment_gateway_sdk.gateways.tappay.dao.TappayDAO")
@patch("payment_gateway_sdk.gateways.tappay.adapter.TappayAdapter")
def test_get_adapter_tappay_production(
    mock_tappay_adapter_cls, mock_tappay_dao_cls, mock_import_module, factory
):
    """Test getting TapPay adapter for production."""
    mock_dao_instance = MagicMock()
    mock_adapter_instance = MagicMock()
    mock_tappay_dao_cls.return_value = mock_dao_instance
    mock_tappay_adapter_cls.return_value = mock_adapter_instance

    adapter = factory.get_adapter("tappay")

    mock_tappay_dao_cls.assert_called_once()
    _, kwargs_dao = mock_tappay_dao_cls.call_args
    assert kwargs_dao["config"]["partner_key"] == "tapkey"
    assert kwargs_dao["config"]["merchant_id"] == "TAPMOCK456"
    assert (
        kwargs_dao["config"]["base_url"] == "https://prod.tappaysdk.com/tpc"
    )  # Production URL
    assert kwargs_dao["config"]["timeout"] == 20

    mock_tappay_adapter_cls.assert_called_once_with(dao=mock_dao_instance)
    assert adapter is mock_adapter_instance


def test_get_adapter_missing_config(factory):
    """Test getting adapter for a gateway with missing config."""
    with pytest.raises(ValueError, match="Config for gateway 'missingpay' not found."):
        factory.get_adapter("missingpay")


def test_get_adapter_invalid_name(factory):
    """Test getting adapter with an invalid/non-existent gateway name."""
    # This might raise ImportError or ValueError depending on where loading fails
    with pytest.raises(ImportError):  # Expecting importlib to fail
        factory.get_adapter("invalid gateway name")


def test_get_transaction_adapter(factory):
    """Test that get_transaction_adapter returns the same instance as get_adapter."""
    # Use patch context manager for this specific test
    with patch(
        "payment_gateway_sdk.gateways.ecpay.adapter.EcpayAdapter"
    ) as mock_adapter_cls:
        mock_adapter_instance = MagicMock(
            spec=EcpayAdapter
        )  # Mock instance that passes isinstance check
        # Important: Ensure the mock instance *is* an instance of TransactionAdapter for the check
        # One way is to add TransactionAdapter to the spec, but easier is direct check:
        from payment_gateway_sdk.schema.adapter import TransactionAdapter

        assert isinstance(
            mock_adapter_instance, TransactionAdapter
        )  # Verify mock setup passes check

        mock_adapter_cls.return_value = mock_adapter_instance
        # Patch DAO/Helper as well if their instantiation is complex/problematic
        with patch("payment_gateway_sdk.gateways.ecpay.dao.EcpayDAO"), patch(
            "payment_gateway_sdk.gateways.ecpay.security.EcpaySecurityHelper"
        ):

            adapter1 = factory.get_adapter("ecpay")
            adapter2 = factory.get_transaction_adapter("ecpay")
            assert adapter1 is adapter2  # Should return the cached instance
            assert adapter2 is mock_adapter_instance


def test_get_callback_handler(factory):
    """Test get_callback_handler returns the DAO instance."""
    # Use patch context manager for this specific test
    with patch("payment_gateway_sdk.gateways.ecpay.dao.EcpayDAO") as mock_dao_cls:
        mock_dao_instance = MagicMock(spec=EcpayDAO)
        mock_dao_cls.return_value = mock_dao_instance
        # Patch Helper as well
        with patch("payment_gateway_sdk.gateways.ecpay.security.EcpaySecurityHelper"):
            handler = factory.get_callback_handler("ecpay")
            assert handler is mock_dao_instance
