# gateways/ecpay/dto.py (NEW FILE)
from dataclasses import dataclass
from typing import Optional

from ...schema.dto.payment import BasePaymentInput  # Inherit common fields


@dataclass
class EcpayCreditPaymentInput(BasePaymentInput):
    """Input specific to ECPay Credit Card payments (One-time, Installment, Periodic)."""

    # Common optional fields already in BasePaymentInput (return_url, client_redirect_url)

    # Credit specific options
    credit_installment: Optional[str] = (
        None  # e.g., "3,6,12" or "30N" (Mutually exclusive with periodic)
    )
    installment_amount: Optional[int] = None  # Only used with CreditInstallment
    redeem: Optional[bool] = (
        None  # Y/N - Default is N (Mutually exclusive with installment)
    )
    union_pay: Optional[int] = None  # 0, 1, 2

    # Periodic specific options (Mutually exclusive with installment/redeem)
    period_amount: Optional[int] = None
    period_type: Optional[str] = None  # D, M, Y
    frequency: Optional[int] = None
    exec_times: Optional[int] = None
    period_return_url: Optional[str] = None

    # Optional common ECPay fields
    client_back_url: Optional[str] = None  # ECPay specific "back" button
    item_url: Optional[str] = None
    remark: Optional[str] = None
    need_extra_paid_info: Optional[str] = None  # Y/N
    language: Optional[str] = None  # ENG, KOR, JPN, CHI
    store_id: Optional[str] = None
    platform_id: Optional[str] = None
    custom_field1: Optional[str] = None
    custom_field2: Optional[str] = None
    custom_field3: Optional[str] = None
    custom_field4: Optional[str] = None

    # Memory Card options
    binding_card: Optional[int] = None  # 0 or 1
    merchant_member_id: Optional[str] = None  # Required if binding_card is 1


@dataclass
class EcpayAtmPaymentInput(BasePaymentInput):
    """Input specific to ECPay ATM payments."""

    expire_date: int = None  # Required for ATM (days)
    payment_info_url: Optional[str] = None  # Optional server URL to get code
    client_redirect_url_for_info: Optional[str] = (
        None  # Optional client URL to get code (Use this or PaymentInfoURL)
    )
    # Optional common ECPay fields
    client_back_url: Optional[str] = None
    item_url: Optional[str] = None
    remark: Optional[str] = None
    need_extra_paid_info: Optional[str] = None  # Y/N
    language: Optional[str] = None
    store_id: Optional[str] = None
    platform_id: Optional[str] = None
    custom_field1: Optional[str] = None  # etc.


@dataclass
class EcpayCvsPaymentInput(BasePaymentInput):
    """Input specific to ECPay CVS code payments."""

    store_expire_date: Optional[int] = None  # Optional (minutes, default 7 days)
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    desc_1: Optional[str] = None  # Optional descriptions shown at kiosk
    desc_2: Optional[str] = None
    desc_3: Optional[str] = None
    desc_4: Optional[str] = None
    # Optional common ECPay fields
    client_back_url: Optional[str] = None  # etc.


@dataclass
class EcpayBarcodePaymentInput(BasePaymentInput):
    """Input specific to ECPay Barcode payments."""

    store_expire_date: Optional[int] = None  # Optional (days, default 7)
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    # Optional common ECPay fields
    client_back_url: Optional[str] = None  # etc.


@dataclass
class EcpayWebAtmPaymentInput(BasePaymentInput):
    """Input specific to ECPay WebATM payments."""

    # Optional common ECPay fields
    client_back_url: Optional[str] = None  # etc.


# TODO: Add DTOs for TWQR, BNPL etc. as needed
