# payment_gateway_sdk/schema/dto/transaction.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union

# Import generic info DTOs from payment
from .payment import PaymentStatus, AtmPaymentInfo, CvsPaymentInfo, BarcodePaymentInfo


# --- Generic Query Input/Output ---
@dataclass
class QueryInput:
    """Generic input for querying transaction status."""

    order_id: Optional[str] = None  # Merchant's order ID
    gateway_trade_no: Optional[str] = None  # Gateway's transaction ID
    # Use for any other parameters needed by specific gateways (e.g., Tappay filters, ECPay PlatformID)
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionRecord:
    """Represents a single generic transaction record from a query."""

    gateway_trade_no: str  # Gateway's unique ID for the transaction
    status: PaymentStatus  # SDK's standardized status
    amount: int
    currency: str
    raw_data: Dict[str, Any]  # Always include raw data from the gateway

    order_id: Optional[str] = None  # Merchant's order ID
    payment_type: Optional[str] = None  # Gateway's specific payment method name string
    transaction_time: Optional[str] = None  # Usually order creation time
    payment_time: Optional[str] = None  # Actual payment completion time
    store_id: Optional[str] = None

    # Optional common details (populate if available from query)
    handling_charge: Optional[float] = None
    payment_type_charge_fee: Optional[float] = None
    auth_code: Optional[str] = None
    card_last_four: Optional[str] = None
    card_first_six: Optional[str] = None
    # Add other common optional fields as needed across gateways


@dataclass
class QueryOutput:
    """Generic output for transaction queries."""

    success: bool
    transactions: List[TransactionRecord] = field(default_factory=list)
    message: str = ""
    error_code: Optional[str] = None  # Gateway's error code, if any
    raw_response: Optional[Dict[str, Any]] = None
    # Optional pagination details if supported by gateway query
    total_records: Optional[int] = None
    current_page: Optional[int] = None
    total_pages: Optional[int] = None


# --- Generic Payment Info Query Output ---
@dataclass
class PaymentInfoQueryOutput:
    """Generic output for queries retrieving specific payment info (like ATM/CVS codes)."""

    success: bool
    message: str
    error_code: Optional[str] = None

    # Common fields likely returned by such queries
    merchant_id: Optional[str] = None
    merchant_trade_no: Optional[str] = None
    store_id: Optional[str] = None
    gateway_trade_no: Optional[str] = None  # Gateway's ID
    amount: Optional[int] = None
    payment_method_name: Optional[str] = None  # Specific payment method name string
    order_creation_time: Optional[str] = None

    # The actual payment info details - using generic structures from schema
    payment_info: Optional[
        Union[AtmPaymentInfo, CvsPaymentInfo, BarcodePaymentInfo]
    ] = None

    raw_response: Optional[Dict[str, Any]] = None


# --- Generic Refund/Action DTOs (Abstracted) ---
# These become very generic, relying on gateway_specific_params heavily.
# Specific adapters will need to interpret these params.


@dataclass
class ActionInput:
    """Generic input for performing actions like refund, capture, cancel."""

    gateway_trade_no: str  # Usually required to identify the transaction at the gateway
    action_type: (
        str  # A string indicating the action (e.g., "REFUND", "CAPTURE", "CANCEL")
    )
    order_id: Optional[str] = None  # Merchant Order ID might be needed
    amount: Optional[int] = None  # Amount for the action (e.g., partial refund)
    currency: Optional[str] = None
    # All other parameters required by the specific gateway's action API
    gateway_specific_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionOutput:
    """Generic output for actions like refund, capture, cancel."""

    success: bool
    status: PaymentStatus  # Resulting status (e.g., REFUNDED, SUCCESS, CANCELED)
    action_type: str  # The action that was performed
    message: str = ""
    error_code: Optional[str] = None
    gateway_reference_id: Optional[str] = None  # e.g., Refund ID from gateway
    raw_response: Optional[Dict[str, Any]] = None
