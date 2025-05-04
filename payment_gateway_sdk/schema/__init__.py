# payment_gateway_sdk/schema/__init__.py
from .adapter import PaymentAdapter, TransactionAdapter
from .gateway import GatewayFactory

# Expose base DTOs and common Enums/Structs
from .dto.payment import (
    BasePaymentInput,
    PaymentOutput,
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
    QueryInput,
    QueryOutput,
    TransactionRecord,
    PaymentInfoQueryOutput,
    ActionInput,
    ActionOutput,  # Export generic action DTOs
    # ECPay specific DTOs are removed from here
)

__all__ = [
    # Adapters ABCs
    "PaymentAdapter",
    "TransactionAdapter",
    # Factory
    "GatewayFactory",
    # Base/Generic DTOs
    "BasePaymentInput",
    "PaymentOutput",
    "CardholderInfo",
    "QueryInput",
    "QueryOutput",
    "TransactionRecord",
    "PaymentInfoQueryOutput",
    "ActionInput",  # Generic Action Input
    "ActionOutput",  # Generic Action Output
    # Base/Generic Payment Info DTOs
    "BasePaymentInfo",
    "AtmPaymentInfo",
    "CvsPaymentInfo",
    "BarcodePaymentInfo",
    "UrlPaymentInfo",
    # Enums
    "PaymentStatus",
    "RedirectMethod",
]
