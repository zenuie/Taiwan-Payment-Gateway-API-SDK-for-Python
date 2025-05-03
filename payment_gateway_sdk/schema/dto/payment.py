# payment_gateway_sdk/schema/dto/payment.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union  # Ensure Union is imported
from enum import Enum


# --- Enums (PaymentMethod, PaymentStatus, RedirectMethod) ---
# ... (as before) ...
class PaymentMethod(Enum):  # ...
    CREDIT = "Credit"
    ATM = "ATM"
    CVS = "CVS"
    BARCODE = "BARCODE"
    WEBATM = "WebATM"
    APPLEPAY = "ApplePay"
    GOOGLEPAY = "GooglePay"
    LINEPAY = "LinePay"
    ALL = "ALL"
    BNPL = "BNPL"
    TWQR = "TWQR"
    UNKNOWN = "Unknown"


class PaymentStatus(Enum):  # ...
    PENDING = "Pending"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELED = "Canceled"
    REFUNDED = "Refunded"
    PARTIALLY_REFUNDED = "PartiallyRefunded"
    ERROR = "Error"
    UNKNOWN = "Unknown"


class RedirectMethod(Enum):
    GET = "GET"
    POST = "POST"


# --- Input DTOs ---
@dataclass
class CardholderInfo:  # ... (as before) ...
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BasePaymentInput:  # ... (as before) ...
    amount: int
    currency: str
    order_id: str
    details: str
    return_url: Optional[str] = None
    client_redirect_url: Optional[str] = None


# --- Output DTOs ---
# --- PaymentInfo specific DTOs (Needs to be defined here) ---
@dataclass
class BasePaymentInfo:  # Marker base class
    pass


@dataclass
class AtmPaymentInfo(BasePaymentInfo):
    bank_code: str
    virtual_account: str
    expire_date: str


@dataclass
class CvsPaymentInfo(BasePaymentInfo):
    payment_no: str
    expire_date: str


@dataclass
class BarcodePaymentInfo(BasePaymentInfo):
    barcode1: str
    barcode2: str
    barcode3: str
    expire_date: str


@dataclass
class UrlPaymentInfo(BasePaymentInfo):  # <-- 確保這個定義存在
    """Holds a URL for payment initiation or completion (non-redirect POST)."""

    url: str


# --- Main PaymentOutput DTO ---
@dataclass
class PaymentOutput:
    success: bool
    status: PaymentStatus
    transaction_id: Optional[str] = None
    gateway_trade_no: Optional[str] = None
    message: str = ""
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None
    redirect_method: Optional[RedirectMethod] = None
    redirect_form_data: Optional[Dict[str, str]] = None
    # Use Union to allow different specific info types
    payment_info: Optional[
        Union[
            AtmPaymentInfo,
            CvsPaymentInfo,
            BarcodePaymentInfo,
            UrlPaymentInfo,
            Dict[str, Any],
        ]
    ] = None  # <-- 包含 UrlPaymentInfo
