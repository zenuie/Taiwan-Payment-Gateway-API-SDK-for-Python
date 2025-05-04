# payment_gateway_sdk/__init__.py
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .schema.gateway import GatewayFactory

# Import from schema DTOs (Generic ones)
from .schema.dto.payment import (
    BasePaymentInput,
    PaymentOutput,
    CardholderInfo,
    PaymentStatus,
    RedirectMethod,
    BasePaymentInfo,
    AtmPaymentInfo,
    CvsPaymentInfo,
    BarcodePaymentInfo,
    UrlPaymentInfo,
)
from .schema.dto.transaction import (
    QueryInput,
    QueryOutput,
    TransactionRecord,
    PaymentInfoQueryOutput,
    ActionInput,
    ActionOutput,  # Generic action DTOs from schema
)
from .core.exceptions import (
    ValidationError,
    GatewayError,
    AuthenticationError,
    PaymentGatewayBaseError,
    NotImplementedError,
)

# Import specific adapters and their specific DTOs
from .gateways.ecpay.adapter import EcpayAdapter
from .gateways.ecpay.dto import (  # ECPay specific INPUTS and transaction/info DTOs
    # Payment Inputs
    EcpayBasePaymentInput,
    EcpayCreditPaymentInput,
    EcpayAtmPaymentInput,
    EcpayCvsPaymentInput,
    EcpayBarcodePaymentInput,
    EcpayWebAtmPaymentInput,
    EcpayApplePayPaymentInput,
    EcpayTwqrPaymentInput,
    EcpayBnplPaymentInput,
    # Output Info
    EcpayBnplApplicationInfo,
    # Action Inputs/Outputs
    EcpayCaptureInput,
    EcpayCaptureOutput,
    EcpayRefundInput,
    EcpayRefundOutput,
    EcpayCancelAuthInput,
    EcpayCancelAuthOutput,
    EcpayAbandonInput,
    EcpayAbandonOutput,
    # Query Inputs/Outputs
    EcpayQueryCreditCardDetailsInput,
    EcpayQueryCreditCardDetailsOutput,
    EcpayQueryPeriodicDetailsOutput,
    # Nested Query/Action DTOs
    EcpayCreditCloseDataRecord,
    EcpayPeriodicExecLogRecord,
)
from .gateways.ecpay.constants import EcpayPaymentMethod, EcpayAction  # ECPay constants

from .gateways.tappay.adapter import TappayAdapter
from .gateways.tappay.dto import TappayPrimePaymentInput, TappayTokenPaymentInput

__version__ = "0.6.0"  # Updated version example

__all__ = [
    # Factory
    "GatewayFactory",
    # Base/Generic Input/Output DTOs (from Schema)
    "BasePaymentInput",
    "PaymentOutput",
    "BasePaymentInfo",
    "QueryInput",
    "QueryOutput",
    "TransactionRecord",
    "PaymentInfoQueryOutput",
    "ActionInput",
    "ActionOutput",
    "CardholderInfo",
    # Generic Payment Info DTOs (from Schema)
    "AtmPaymentInfo",
    "CvsPaymentInfo",
    "BarcodePaymentInfo",
    "UrlPaymentInfo",
    # Enums (from Schema)
    "PaymentStatus",
    "RedirectMethod",
    # Exceptions (from Core)
    "ValidationError",
    "GatewayError",
    "AuthenticationError",
    "PaymentGatewayBaseError",
    "NotImplementedError",
    # Specific Gateway Adapters
    "EcpayAdapter",
    "TappayAdapter",
    # --- ECPay Exports ---
    # Specific ECPay Input DTOs (from gateways.ecpay.dto)
    "EcpayBasePaymentInput",
    "EcpayCreditPaymentInput",
    "EcpayAtmPaymentInput",
    "EcpayCvsPaymentInput",
    "EcpayBarcodePaymentInput",
    "EcpayWebAtmPaymentInput",
    "EcpayApplePayPaymentInput",
    "EcpayTwqrPaymentInput",
    "EcpayBnplPaymentInput",
    # Specific ECPay Output Info DTO (from gateways.ecpay.dto)
    "EcpayBnplApplicationInfo",
    # ECPay Constants (from gateways.ecpay.constants)
    "EcpayPaymentMethod",
    "EcpayAction",
    # Specific ECPay Action/Query DTOs (from gateways.ecpay.dto)
    "EcpayCaptureInput",
    "EcpayCaptureOutput",
    "EcpayRefundInput",
    "EcpayRefundOutput",
    "EcpayCancelAuthInput",
    "EcpayCancelAuthOutput",
    "EcpayAbandonInput",
    "EcpayAbandonOutput",
    "EcpayQueryCreditCardDetailsInput",
    "EcpayQueryCreditCardDetailsOutput",
    "EcpayQueryPeriodicDetailsOutput",
    "EcpayCreditCloseDataRecord",
    "EcpayPeriodicExecLogRecord",
    # --- TapPay Exports ---
    "TappayPrimePaymentInput",
    "TappayTokenPaymentInput",
]
