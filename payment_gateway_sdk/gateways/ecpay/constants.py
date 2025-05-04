# payment_gateway_sdk/gateways/ecpay/constants.py


class EcpayPaymentMethod:
    ALL = "ALL"
    CREDIT = "Credit"
    WEBATM = "WebATM"
    ATM = "ATM"
    CVS = "CVS"
    BARCODE = "BARCODE"
    APPLEPAY = "ApplePay"
    TWQR = "TWQR"
    BNPL = "BNPL"
    # Add sub-methods like 'Credit_CreditCard', 'ATM_BOT' if needed for mapping outputs


class EcpayAction:
    CAPTURE = "C"
    REFUND = "R"
    CANCEL_AUTH = "E"
    ABANDON = "N"


class EcpayDeviceSource:
    ECPAY_PAY_APP = "gwpay"


# Add other constants like RtnCodes if useful
class EcpayRtnCode:
    # General
    SUCCESS = "1"
    # QueryPaymentInfo specific success
    ATM_SUCCESS = "2"
    CVS_BARCODE_SUCCESS = "10100073"
    # QueryTradeInfo specific failure
    TRANSACTION_NOT_COMPLETED = "10200095"
    # BNPL Application Result
    BNPL_APPLYING = (
        "2"  # From index8556.txt (Same as ATM success code, context matters)
    )
    # DoAction success is '1'


# Add more constants as needed
