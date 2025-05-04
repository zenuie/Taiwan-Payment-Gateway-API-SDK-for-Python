# gateways/ecpay/dto.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any # Import List/Dict/Any

from ...schema.dto.payment import BasePaymentInput, BasePaymentInfo, PaymentStatus # Import base classes
from ...core.exceptions import ValidationError

# --- Base Input for ECPay Common Optional Fields ---
@dataclass
class EcpayBasePaymentInput(BasePaymentInput):
    """Base input DTO for ECPay, including common optional AIO fields."""
    client_back_url: Optional[str] = None # ClientBackURL
    item_url: Optional[str] = None        # ItemURL
    remark: Optional[str] = None          # Remark
    need_extra_paid_info: Optional[str] = field(default=None, metadata={'valid_values': ['Y', 'N']}) # NeedExtraPaidInfo (Y/N)
    store_id: Optional[str] = None        # StoreID
    platform_id: Optional[str] = None     # PlatformID
    custom_field1: Optional[str] = None   # CustomField1 (max 50 chars)
    custom_field2: Optional[str] = None   # CustomField2 (max 50 chars)
    custom_field3: Optional[str] = None   # CustomField3 (max 50 chars)
    custom_field4: Optional[str] = None   # CustomField4 (max 50 chars)
    language: Optional[str] = field(default=None, metadata={'valid_values': ['ENG', 'KOR', 'JPN', 'CHI']}) # Language
    device_source: Optional[str] = field(default=None, metadata={'valid_values': ['gwpay']}) # DeviceSource (Ref: indexea8e.txt)
    # ChooseSubPayment is omitted for simplicity, add if needed via gateway_specific_params

    # Basic validation for common fields
    def __post_init__(self):
        if self.need_extra_paid_info and self.need_extra_paid_info not in ['Y', 'N']:
            raise ValidationError("NeedExtraPaidInfo must be 'Y' or 'N'.")
        if self.language and self.language not in ['ENG', 'KOR', 'JPN', 'CHI']:
            raise ValidationError("Invalid Language code.")
        if self.device_source and self.device_source != 'gwpay':
             raise ValidationError("Invalid DeviceSource value.")
        if self.custom_field1 and len(self.custom_field1) > 50: raise ValidationError("CustomField1 exceeds 50 characters.")
        if self.custom_field2 and len(self.custom_field2) > 50: raise ValidationError("CustomField2 exceeds 50 characters.")
        if self.custom_field3 and len(self.custom_field3) > 50: raise ValidationError("CustomField3 exceeds 50 characters.")
        if self.custom_field4 and len(self.custom_field4) > 50: raise ValidationError("CustomField4 exceeds 50 characters.")
        # ReturnURL is technically mandatory for ECPay AIO according to docs
        if self.return_url is None:
             raise ValidationError("ECPay AIO requires 'return_url'.")


# --- Specific Payment Method Inputs ---
@dataclass
class EcpayCreditPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay Credit Card payments (One-time, Installment, Periodic)."""
    credit_installment: Optional[str] = None
    installment_amount: Optional[int] = None
    redeem: Optional[str] = field(default=None, metadata={'valid_values': ['Y']})
    union_pay: Optional[int] = field(default=None, metadata={'valid_values': [0, 1, 2]})
    period_amount: Optional[int] = None
    period_type: Optional[str] = field(default=None, metadata={'valid_values': ['D', 'M', 'Y']})
    frequency: Optional[int] = None
    exec_times: Optional[int] = None
    period_return_url: Optional[str] = None
    binding_card: Optional[int] = field(default=None, metadata={'valid_values': [0, 1]})
    merchant_member_id: Optional[str] = None
    def __post_init__(self):
        # (Validation logic as previously defined)
        super().__post_init__()
        is_installment = self.credit_installment is not None
        is_periodic = any(f is not None for f in [self.period_amount, self.period_type, self.frequency, self.exec_times])
        is_redeem = self.redeem == 'Y'
        if sum([is_installment, is_periodic, is_redeem]) > 1:
             raise ValidationError("CreditInstallment, Periodic parameters, and Redeem are mutually exclusive.")
        if self.binding_card == 1 and not self.merchant_member_id:
             raise ValidationError("MerchantMemberID is required when BindingCard is 1.")
        if is_periodic:
             if not all(f is not None for f in [self.period_amount, self.period_type, self.frequency, self.exec_times]):
                 raise ValidationError("All periodic fields (PeriodAmount, PeriodType, Frequency, ExecTimes) must be provided together.")
             if self.amount != self.period_amount:
                  raise ValidationError("For periodic payments, TotalAmount must be equal to PeriodAmount.")
             if self.exec_times < 2:
                  raise ValidationError("ExecTimes must be at least 2 for periodic payments.")
             if self.period_type == 'D':
                 if not (1 <= self.frequency <= 365): raise ValidationError("Frequency for PeriodType 'D' must be between 1 and 365.")
                 if self.exec_times > 999: raise ValidationError("ExecTimes for PeriodType 'D' cannot exceed 999.")
             elif self.period_type == 'M':
                 if not (1 <= self.frequency <= 12): raise ValidationError("Frequency for PeriodType 'M' must be between 1 and 12.")
                 if self.exec_times > 99: raise ValidationError("ExecTimes for PeriodType 'M' cannot exceed 99.")
             elif self.period_type == 'Y':
                  if self.frequency != 1: raise ValidationError("Frequency for PeriodType 'Y' must be 1.")
                  if self.exec_times > 9: raise ValidationError("ExecTimes for PeriodType 'Y' cannot exceed 9.")


@dataclass
class EcpayAtmPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay ATM payments."""
    expire_date: Optional[int] = 3
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    def __post_init__(self):
        super().__post_init__()
        if self.expire_date is not None and not (1 <= self.expire_date <= 60):
             raise ValidationError("ExpireDate for ATM must be between 1 and 60 days.")

@dataclass
class EcpayCvsPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay CVS code payments."""
    store_expire_date: Optional[int] = 10080
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    desc_1: Optional[str] = None
    desc_2: Optional[str] = None
    desc_3: Optional[str] = None
    desc_4: Optional[str] = None
    def __post_init__(self):
        super().__post_init__()
        if self.store_expire_date is not None and self.store_expire_date > 43200:
             raise ValidationError("StoreExpireDate for CVS cannot exceed 43200 minutes (30 days).")
        if self.desc_1 and len(self.desc_1) > 20: raise ValidationError("Desc_1 exceeds 20 characters.")
        if self.desc_2 and len(self.desc_2) > 20: raise ValidationError("Desc_2 exceeds 20 characters.")
        if self.desc_3 and len(self.desc_3) > 20: raise ValidationError("Desc_3 exceeds 20 characters.")
        if self.desc_4 and len(self.desc_4) > 20: raise ValidationError("Desc_4 exceeds 20 characters.")

@dataclass
class EcpayBarcodePaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay Barcode payments."""
    store_expire_date: Optional[int] = 7
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    def __post_init__(self):
        super().__post_init__()
        if self.store_expire_date is not None and not (1 <= self.store_expire_date <= 30):
             raise ValidationError("StoreExpireDate for BARCODE must be between 1 and 30 days (standard limit).")

@dataclass
class EcpayWebAtmPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay WebATM payments."""
    pass

@dataclass
class EcpayApplePayPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay ApplePay payments."""
    pass

@dataclass
class EcpayTwqrPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay TWQR payments."""
    def __post_init__(self):
        super().__post_init__()
        if not (6 <= self.amount <= 49999):
             raise ValidationError("TotalAmount for TWQR must be between 6 and 49,999 TWD.")

@dataclass
class EcpayBnplPaymentInput(EcpayBasePaymentInput):
    """Input specific to ECPay BNPL (Buy Now Pay Later) payments."""
    payment_info_url: Optional[str] = None
    client_redirect_url_for_info: Optional[str] = None
    def __post_init__(self):
        super().__post_init__()
        if not (1000 <= self.amount <= 500000):
             raise ValidationError("TotalAmount for BNPL must be between 1,000 and 500,000 TWD.")

# --- Specific Output Info DTOs ---
@dataclass
class EcpayBnplApplicationInfo(BasePaymentInfo):
    """Holds info from ECPay BNPL application result notification."""
    bnpl_trade_no: str
    bnpl_installment: str

# --- ECPay Specific Transaction DTOs (Moved from Schema) ---

# --- Query DTOs ---
@dataclass
class EcpayQueryCreditCardDetailsInput:
    """Input for ECPay CreditDetail/QueryTrade/V2 API."""
    credit_refund_id: int
    credit_amount: int
    credit_check_code: int
    merchant_id: Optional[str] = None
    platform_id: Optional[str] = None

@dataclass
class EcpayCreditCloseDataRecord:
    """Represents a single close_data record from QueryTrade/V2."""
    status: str
    amount: int
    sno: str
    datetime: str

@dataclass
class EcpayQueryCreditCardDetailsOutput:
    """Output for ECPay CreditDetail/QueryTrade/V2 API."""
    success: bool
    message: str = ""
    error_code: Optional[str] = None
    gateway_authorization_id: Optional[int] = None
    amount: Optional[int] = None
    closed_amount: Optional[int] = None
    authorization_time: Optional[str] = None
    status: Optional[str] = None
    close_data: List[EcpayCreditCloseDataRecord] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None

@dataclass
class EcpayPeriodicExecLogRecord:
    """Represents a single execution log record from QueryCreditCardPeriodInfo."""
    rtn_code: int
    amount: int
    gwsr: int
    process_date: str
    auth_code: str
    trade_no: str

@dataclass
class EcpayQueryPeriodicDetailsOutput:
    """Output for ECPay QueryCreditCardPeriodInfo API."""
    success: bool
    message: str = ""
    error_code: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_trade_no: Optional[str] = None
    first_trade_no: Optional[str] = None
    period_type: Optional[str] = None
    frequency: Optional[int] = None
    exec_times: Optional[int] = None
    period_amount: Optional[int] = None
    first_amount: Optional[int] = None
    first_gwsr: Optional[int] = None
    first_process_date: Optional[str] = None
    first_auth_code: Optional[str] = None
    card_last_four: Optional[str] = None
    card_first_six: Optional[str] = None
    total_success_times: Optional[int] = None
    total_success_amount: Optional[int] = None
    exec_status: Optional[str] = None
    exec_log: List[EcpayPeriodicExecLogRecord] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None

# --- Action DTOs (Replacing DoAction) ---

# Capture (Action='C')
@dataclass
class EcpayCaptureInput:
    """Input for ECPay Capture (Action='C')."""
    merchant_trade_no: str  # Original MerchantTradeNo
    gateway_trade_no: str   # ECPay's TradeNo from successful auth
    capture_amount: int     # Amount to capture (usually full authorized amount)
    platform_id: Optional[str] = None

@dataclass
class EcpayCaptureOutput:
    """Output from ECPay Capture (Action='C')."""
    success: bool           # True if RtnCode is 1
    status: PaymentStatus   # SUCCESS if successful, FAILED otherwise
    merchant_trade_no: Optional[str] = None # Returned by ECPay
    gateway_trade_no: Optional[str] = None # Returned by ECPay
    message: str = ""       # RtnMsg
    error_code: Optional[str] = None # RtnCode if not success
    raw_response: Optional[Dict[str, Any]] = None

# Refund (Action='R')
@dataclass
class EcpayRefundInput:
    """Input for ECPay Refund (Action='R')."""
    merchant_trade_no: str  # Original MerchantTradeNo
    gateway_trade_no: str   # ECPay's TradeNo from successful auth/capture
    refund_amount: int      # Amount to refund
    platform_id: Optional[str] = None

@dataclass
class EcpayRefundOutput:
    """Output from ECPay Refund (Action='R')."""
    success: bool           # True if RtnCode is 1
    status: PaymentStatus   # REFUNDED if successful, FAILED otherwise
    merchant_trade_no: Optional[str] = None # Returned by ECPay
    gateway_trade_no: Optional[str] = None # Returned by ECPay
    message: str = ""       # RtnMsg
    error_code: Optional[str] = None # RtnCode if not success
    raw_response: Optional[Dict[str, Any]] = None

# Cancel Authorization (Action='E')
@dataclass
class EcpayCancelAuthInput:
    """Input for ECPay Cancel Authorization (Action='E'). Use before capture."""
    merchant_trade_no: str  # Original MerchantTradeNo
    gateway_trade_no: str   # ECPay's TradeNo from successful auth
    # Amount is required by ECPay DoAction API, even for Cancel/Abandon
    # Should typically be the original authorized amount.
    original_amount: int
    platform_id: Optional[str] = None

@dataclass
class EcpayCancelAuthOutput:
    """Output from ECPay Cancel Authorization (Action='E')."""
    success: bool           # True if RtnCode is 1
    status: PaymentStatus   # CANCELED if successful, FAILED otherwise
    merchant_trade_no: Optional[str] = None # Returned by ECPay
    gateway_trade_no: Optional[str] = None # Returned by ECPay
    message: str = ""       # RtnMsg
    error_code: Optional[str] = None # RtnCode if not success
    raw_response: Optional[Dict[str, Any]] = None

# Abandon Transaction (Action='N')
@dataclass
class EcpayAbandonInput:
    """Input for ECPay Abandon Transaction (Action='N'). Use before capture."""
    merchant_trade_no: str  # Original MerchantTradeNo
    gateway_trade_no: str   # ECPay's TradeNo from successful auth
    # Amount is required by ECPay DoAction API, even for Cancel/Abandon
    # Should typically be the original authorized amount.
    original_amount: int
    platform_id: Optional[str] = None

@dataclass
class EcpayAbandonOutput:
    """Output from ECPay Abandon Transaction (Action='N')."""
    success: bool           # True if RtnCode is 1
    status: PaymentStatus   # CANCELED if successful, FAILED otherwise
    merchant_trade_no: Optional[str] = None # Returned by ECPay
    gateway_trade_no: Optional[str] = None # Returned by ECPay
    message: str = ""       # RtnMsg
    error_code: Optional[str] = None # RtnCode if not success
    raw_response: Optional[Dict[str, Any]] = None