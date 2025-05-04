# payment_gateway_sdk/gateways/ecpay/__init__.py
from .adapter import EcpayAdapter
from .dao import EcpayDAO

from .dto import (
    # Base and specific payment inputs
    EcpayBasePaymentInput,
    EcpayCreditPaymentInput,
    EcpayAtmPaymentInput,
    EcpayCvsPaymentInput,
    EcpayBarcodePaymentInput,
    EcpayWebAtmPaymentInput,
    EcpayApplePayPaymentInput,
    EcpayTwqrPaymentInput,
    EcpayBnplPaymentInput,
    # Specific Output Info DTO
    EcpayBnplApplicationInfo,
    # --- Specific Action Inputs/Outputs (Replaced DoAction) ---
    EcpayCaptureInput,
    EcpayCaptureOutput,
    EcpayRefundInput,
    EcpayRefundOutput,
    EcpayCancelAuthInput,
    EcpayCancelAuthOutput,
    EcpayAbandonInput,
    EcpayAbandonOutput,
    # --- Specific Query Inputs/Outputs ---
    EcpayQueryCreditCardDetailsInput,
    EcpayQueryCreditCardDetailsOutput,
    EcpayQueryPeriodicDetailsOutput,
    # Nested DTOs used by above outputs
    EcpayCreditCloseDataRecord,
    EcpayPeriodicExecLogRecord,
)

# Import generic PaymentInfoQueryOutput from schema
from ...schema.dto.transaction import PaymentInfoQueryOutput

from .security import EcpaySecurityHelper
from .utils import ecpay_url_encode
from .constants import (
    EcpayPaymentMethod,
    EcpayAction,
    EcpayDeviceSource,
)  # Export constants

__all__ = [
    "EcpayAdapter",
    "EcpayDAO",
    "EcpaySecurityHelper",
    "ecpay_url_encode",
    # Constants
    "EcpayPaymentMethod",
    "EcpayAction",
    "EcpayDeviceSource",
    # Input DTOs
    "EcpayBasePaymentInput",
    "EcpayCreditPaymentInput",
    "EcpayAtmPaymentInput",
    "EcpayCvsPaymentInput",
    "EcpayBarcodePaymentInput",
    "EcpayWebAtmPaymentInput",
    "EcpayApplePayPaymentInput",
    "EcpayTwqrPaymentInput",
    "EcpayBnplPaymentInput",
    # Specific Output Info DTO
    "EcpayBnplApplicationInfo",
    # Transaction Operation DTOs (Defined locally) - Use new names
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
    "EcpayCreditCloseDataRecord",  # Export nested DTO
    "EcpayPeriodicExecLogRecord",  # Export nested DTO
    # Generic Output DTO (Imported from schema)
    "PaymentInfoQueryOutput",
]
