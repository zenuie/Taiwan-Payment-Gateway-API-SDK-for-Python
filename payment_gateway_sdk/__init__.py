# payment_gateway_sdk/__init__.py
import logging

# Configure basic logging for the SDK
# Users can override this in their application
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Expose key components for easier import by the user
from .schema.gateway import GatewayFactory
from .schema.dto.payment import (
    BasePaymentInput,
    PaymentOutput,
    CardholderInfo,
    PaymentMethod,
    PaymentStatus,
    RedirectMethod,
    BasePaymentInfo,
    AtmPaymentInfo,
    CvsPaymentInfo,
    BarcodePaymentInfo,
    UrlPaymentInfo,
)
from .schema.dto.transaction import (
    RefundInput,
    RefundOutput,
    QueryInput,
    QueryOutput,
    TransactionRecord,
)
from .core.exceptions import (
    ValidationError,
    GatewayError,
    AuthenticationError,
    PaymentGatewayBaseError,
    NotImplementedError,  # Re-export if needed
)

# Import specific adapters if users might need to type hint or check instance
from .gateways.ecpay.adapter import EcpayAdapter
from .gateways.tappay.adapter import TappayAdapter

__version__ = "0.2.0"  # Updated version example

__all__ = [
    # Factory
    "GatewayFactory",
    # Base Input/Output DTOs
    "BasePaymentInput",
    "PaymentOutput",
    "BasePaymentInfo",
    "RefundInput",
    "RefundOutput",
    "QueryInput",
    "QueryOutput",
    "TransactionRecord",
    "CardholderInfo",
    # Specific Payment Info DTOs (for interpreting PaymentOutput.payment_info)
    "AtmPaymentInfo",
    "CvsPaymentInfo",
    "BarcodePaymentInfo",
    "UrlPaymentInfo",
    # Enums
    "PaymentMethod",
    "PaymentStatus",
    "RedirectMethod",
    # Exceptions
    "ValidationError",
    "GatewayError",
    "AuthenticationError",
    "PaymentGatewayBaseError",
    "NotImplementedError",
    # Specific Adapters (Optional - if needed for type checking)
    "EcpayAdapter",
    "TappayAdapter",
]
