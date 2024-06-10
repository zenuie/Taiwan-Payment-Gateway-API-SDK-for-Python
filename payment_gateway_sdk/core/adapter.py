from payment_gateway_sdk.core.exceptions import ValidationError


class BaseAdapter:
    # error_messages  = {}

    def __init__(self, request):
        self.request = request

    def validation_error(self, code, *args):
        # get error messages
        message = self.error_messages[code]
        if args:
            message = message % args
        exc = ValidationError(message, code=code)
        return exc
