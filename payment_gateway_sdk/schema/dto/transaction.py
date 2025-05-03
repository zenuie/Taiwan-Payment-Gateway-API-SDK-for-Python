# payment_gateway_sdk/schema/dto/transaction.py
# (Content mostly unchanged, TransactionRecord order fixed)
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .payment import PaymentStatus


@dataclass
class RefundInput:
    gateway_trade_no: str
    amount: Optional[int] = None
    currency: Optional[str] = None
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefundOutput:
    success: bool
    status: PaymentStatus
    refund_id: Optional[str] = None
    message: str = ""
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class QueryInput:
    order_id: Optional[str] = None
    gateway_trade_no: Optional[str] = None
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionRecord:
    # Fields without default first
    gateway_trade_no: str
    status: PaymentStatus
    amount: int
    currency: str
    raw_data: Dict[str, Any]
    # Optional fields with defaults
    order_id: Optional[str] = None
    payment_type: Optional[str] = None
    transaction_time: Optional[str] = None
    card_last_four: Optional[str] = None
    auth_code: Optional[str] = None


@dataclass
class QueryOutput:
    success: bool
    transactions: List[TransactionRecord] = field(default_factory=list)
    message: str = ""
    error_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    total_records: Optional[int] = None
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
