# payment_gateway_sdk/schema/__init__.py
from .adapter import PaymentAdapter, TransactionAdapter  # Keep ABCs
from .gateway import GatewayFactory

# Expose base DTOs and common Enums
from .dto.payment import (
    BasePaymentInput,
    PaymentOutput,
    PaymentMethod,
    PaymentStatus,
    RedirectMethod,
    CardholderInfo,
    BasePaymentInfo,
    AtmPaymentInfo,
    CvsPaymentInfo,
    BarcodePaymentInfo,
    UrlPaymentInfo,
)
from .dto.transaction import (
    RefundInput,
    RefundOutput,
    QueryInput,
    QueryOutput,
    TransactionRecord,
)
