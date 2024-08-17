from abc import abstractmethod

from payment_gateway_sdk.core.adapter import BaseAdapter


class PaymentAdapter(BaseAdapter):
    def __init__(self, **kwargs):
        super(PaymentAdapter, self).__init__(**kwargs)

    @abstractmethod
    def authorize(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def payment(self, *args, **kwargs) -> str:
        pass


class TransactionAdapter(BaseAdapter):
    def __init__(self, **kwargs):
        super(TransactionAdapter, self).__init__(**kwargs)

    @abstractmethod
    def refund(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def record(self, *args, **kwargs) -> str:
        pass
