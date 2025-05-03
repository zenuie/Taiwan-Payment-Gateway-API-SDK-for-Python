# payment_gateway_sdk/schema/adapter.py
# (Content unchanged - Defines the abstract contracts)
from abc import ABC, abstractmethod
from .dto.payment import (
    BasePaymentInput,
    PaymentOutput,
)  # Keep PaymentInput here? Or remove if not used by any adapter method signature? Let's remove it for now.
from .dto.transaction import RefundInput, RefundOutput, QueryInput, QueryOutput


class PaymentAdapter(ABC):
    """
    Base marker class for specific gateway payment adapters.
    Concrete adapters will have specific methods like pay_with_credit, pay_with_atm.
    """

    # No abstract 'payment' method anymore as signatures differ
    pass


class TransactionAdapter(ABC):
    @abstractmethod
    def refund(self, input: RefundInput) -> RefundOutput:
        pass

    @abstractmethod
    def query_transaction(self, input: QueryInput) -> QueryOutput:
        pass
