# payment_gateway_sdk/schema/dto/payment.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union
from enum import Enum

# Removed PaymentMethod Enum - Now handled via strings by adapters


class PaymentStatus(Enum):
    PENDING = "Pending"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELED = "Canceled"
    REFUNDED = "Refunded"
    PARTIALLY_REFUNDED = "PartiallyRefunded"
    APPLYING = "Applying"  # Specific state, e.g., for BNPL application
    ERROR = "Error"
    UNKNOWN = "Unknown"


class RedirectMethod(Enum):
    GET = "GET"
    POST = "POST"


@dataclass
class CardholderInfo:
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BasePaymentInput:
    amount: int
    currency: str
    order_id: str
    details: str
    return_url: Optional[str] = None  # Often mandatory depending on gateway/method
    client_redirect_url: Optional[str] = None


# --- Generic PaymentInfo DTOs (kept in schema for standardization) ---
@dataclass
class BasePaymentInfo:
    pass


@dataclass
class AtmPaymentInfo(BasePaymentInfo):
    virtual_account: str
    expire_date: str
    bank_code: Optional[str] = None  # Made optional as not all gateways provide it


@dataclass
class CvsPaymentInfo(BasePaymentInfo):
    payment_no: str
    expire_date: str
    payment_url: Optional[str] = None


@dataclass
class BarcodePaymentInfo(BasePaymentInfo):
    expire_date: str
    barcode1: Optional[str] = None  # Made optional as structure varies
    barcode2: Optional[str] = None
    barcode3: Optional[str] = None
    full_barcode: Optional[str] = None  # Add if some return a single string


@dataclass
class UrlPaymentInfo(BasePaymentInfo):
    url: str


# --- Main PaymentOutput DTO ---
@dataclass
class PaymentOutput:
    success: bool
    status: PaymentStatus
    # transaction_id remains ECPay's TradeNo, TapPay's rec_trade_id etc.
    gateway_trade_no: Optional[str] = None
    order_id: Optional[str] = None  # The merchant's order ID
    message: str = ""
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None
    redirect_method: Optional[RedirectMethod] = None
    redirect_form_data: Optional[Dict[str, str]] = None
    # Specific method name returned by gateway (e.g., "Credit_CreditCard", "ATM_BOT")
    # Usually populated after query/callback, not initial redirect.
    payment_method_name: Optional[str] = None
    # Generic payment info structures
    payment_info: Optional[
        Union[
            AtmPaymentInfo,
            CvsPaymentInfo,
            BarcodePaymentInfo,
            UrlPaymentInfo,
            Dict[
                str, Any
            ],  # Keep Dict as fallback for gateway-specific structured info
        ]
    ] = None  # Removed BnplApplicationInfo
