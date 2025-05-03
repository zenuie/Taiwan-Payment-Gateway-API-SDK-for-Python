# payment_gateway_sdk/gateways/tappay/dto.py
# (Content as generated in the previous step with Optional + __post_init__)
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ...schema.dto.payment import BasePaymentInput, CardholderInfo
from ...core.exceptions import ValidationError


@dataclass
class TappayPaymentInputBase(BasePaymentInput):
    cardholder_info: Optional[CardholderInfo] = None
    order_number: Optional[str] = None
    bank_transaction_id: Optional[str] = None
    additional_data: Optional[str] = None
    store_id: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_group_id: Optional[str] = None


@dataclass
class TappayPrimePaymentInput(TappayPaymentInputBase):
    prime: Optional[str] = None  # Changed to Optional
    remember: Optional[bool] = False
    three_domain_secure: Optional[bool] = False
    instalment: Optional[int] = None
    redeem: Optional[bool] = False
    delay_capture_in_days: Optional[int] = None
    cardholder_verify: Optional[Dict[str, bool]] = None
    kyc_verification_merchant_id: Optional[str] = None
    merchandise_details: Optional[Dict[str, int]] = None
    jko_pay_insurance_policy: Optional[List[Dict[str, Any]]] = None
    extra_info: Optional[Dict[str, Any]] = None
    product_image_url: Optional[str] = None
    event_code: Optional[str] = None
    go_back_url: Optional[str] = None

    def __post_init__(self):
        if self.prime is None or not str(self.prime).strip():
            raise ValidationError("'prime' is required for TappayPrimePaymentInput")
        if self.three_domain_secure and (
            not self.return_url or not self.client_redirect_url
        ):
            raise ValidationError(
                "Both return_url and client_redirect_url required for 3DS."
            )


@dataclass
class TappayTokenPaymentInput(TappayPaymentInputBase):
    card_key: Optional[str] = None  # Changed to Optional
    card_token: Optional[str] = None  # Changed to Optional
    card_ccv: Optional[str] = None
    ccv_prime: Optional[str] = None
    device_id: Optional[str] = None
    three_domain_secure: Optional[bool] = False
    instalment: Optional[int] = None
    redeem: Optional[bool] = False
    delay_capture_in_days: Optional[int] = None
    cardholder_verify: Optional[Dict[str, bool]] = None
    kyc_verification_merchant_id: Optional[str] = None
    go_back_url: Optional[str] = None

    def __post_init__(self):
        if not (self.card_key and self.card_token):
            raise ValidationError(
                "'card_key' and 'card_token' are required for TappayTokenPaymentInput"
            )
        if self.card_ccv and self.ccv_prime:
            raise ValidationError("'card_ccv' and 'ccv_prime' cannot be used together.")
        if self.three_domain_secure and (
            not self.return_url or not self.client_redirect_url
        ):
            raise ValidationError(
                "Both return_url and client_redirect_url required for 3DS."
            )


# TODO: Add other specific DTOs if needed (e.g., TappayLinePayInput if mandatory fields differ)
