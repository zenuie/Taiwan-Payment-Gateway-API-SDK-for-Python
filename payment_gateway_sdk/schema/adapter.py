# payment_gateway_sdk/schema/adapter.py
from abc import ABC, abstractmethod

# Import Generic DTOs used in abstract methods
from .dto.transaction import QueryInput, QueryOutput


class PaymentAdapter(ABC):
    """Base marker class for specific gateway payment adapters."""

    # No abstract 'payment' method due to differing signatures.
    # Concrete adapters define methods like pay_with_credit, pay_with_prime, etc.
    pass


class TransactionAdapter(ABC):
    """Abstract Base Class for standardized transaction operations."""

    # Refund/Action is often too gateway-specific for a useful generic signature.
    # Adapters should implement specific methods (e.g., ecpay_adapter.do_action)
    # or raise NotImplementedError for generic methods like refund().
    # @abstractmethod
    # def refund(self, input: ActionInput) -> ActionOutput:
    #    """ Performs a refund action. """
    #    pass

    @abstractmethod
    def query_transaction(self, input: QueryInput) -> QueryOutput:
        """Queries the status and details of one or more transactions."""
        pass

    # Add other potentially standardizable actions here if identified later
