# payment_gateway_sdk/core/exceptions.py
# (Content unchanged)
class PaymentGatewayBaseError(Exception):
    def __init__(self, message, code=None, raw_response=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.raw_response = raw_response  # Optionally store raw response on error


class ValidationError(PaymentGatewayBaseError):
    pass


class AuthenticationError(PaymentGatewayBaseError):
    pass


class GatewayError(PaymentGatewayBaseError):
    pass


class NotImplementedError(PaymentGatewayBaseError):
    pass  # Standard exception exists, but alias for consistency
