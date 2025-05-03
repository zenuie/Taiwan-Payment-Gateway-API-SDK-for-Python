# --- payment_gateway_sdk/gateways/ecpay/dao.py ---
import logging
from datetime import datetime
from urllib.parse import unquote_plus

import requests

from .security import EcpaySecurityHelper
from ...core.exceptions import GatewayError, AuthenticationError, ValidationError

logger = logging.getLogger(__name__)


class EcpayDAO:
    def __init__(self, config: dict, security_helper: EcpaySecurityHelper):
        # super().__init__(config) # If used
        self.config = config
        self.merchant_id = config.get("merchant_id")
        self.base_url = config.get("base_url")
        self.timeout = int(config.get("timeout", 30))
        if not self.merchant_id:
            raise AuthenticationError("ECPay MerchantID missing.")
        if not self.base_url:
            raise ValueError("ECPay base_url missing.")
        if not isinstance(security_helper, EcpaySecurityHelper):
            raise TypeError("EcpayDAO requires EcpaySecurityHelper.")
        self.security_helper = security_helper

    def build_checkout_form_data(self, params: dict) -> dict:
        # ... (implementation as before) ...
        required = [
            "MerchantTradeNo",
            "MerchantTradeDate",
            "PaymentType",
            "TotalAmount",
            "TradeDesc",
            "ItemName",
            "ReturnURL",
            "ChoosePayment",
            "EncryptType",
        ]
        if not all(k in params for k in required):
            raise ValidationError(f"Missing required ECPay params: {required}")
        if "MerchantID" not in params:
            params["MerchantID"] = self.merchant_id
        check_mac_value = self.security_helper.calculate_check_mac_value(params.copy())
        params["CheckMacValue"] = check_mac_value
        logger.debug(f"ECPay Form Data Prepared: {params}")
        return params

    def verify_callback_data(self, callback_data: dict) -> bool:
        logger.debug(f"Verifying ECPay callback data: {callback_data}")
        is_valid = self.security_helper.verify_check_mac_value(callback_data)
        logger.info(f"ECPay callback verification result: {is_valid}")
        return is_valid

    def _send_api_request(self, endpoint: str, data: dict) -> dict:
        url = self.base_url + endpoint
        if "MerchantID" not in data:
            data["MerchantID"] = self.merchant_id
        if "TimeStamp" not in data:
            data["TimeStamp"] = str(int(datetime.now().timestamp()))
        # Calculate CheckMacValue *before* sending
        data_to_send = data.copy()
        data_to_send["CheckMacValue"] = self.security_helper.calculate_check_mac_value(
            data_to_send.copy()
        )

        try:
            logger.debug(f"Sending API request to ECPay: {url}")
            logger.debug(f"Request Data: {data_to_send}")
            response = requests.post(url=url, data=data_to_send, timeout=self.timeout)
            logger.debug(f"ECPay API Raw Response Status: {response.status_code}")
            logger.debug(f"ECPay API Raw Response Body: {response.text}")
            response.raise_for_status()
            response_text = response.text
            response_dict = {}
            if response_text:
                try:
                    decoded_text = unquote_plus(response_text)
                    response_dict = dict(
                        item.split("=", 1)
                        for item in decoded_text.split("&")
                        if "=" in item
                    )
                except ValueError as e:
                    logger.error(
                        f"Could not parse ECPay API response: {response_text}. Error: {e}"
                    )
                    raise GatewayError(
                        f"Could not parse ECPay API response: {response_text[:100]}"
                    )

            # TODO: Add CheckMacValue verification for API responses if ECPay includes one
            rtn_code = response_dict.get("RtnCode")
            if rtn_code != "1":  # Assuming '1' is success for API calls
                msg = response_dict.get("RtnMsg", "Unknown ECPay API error")
                logger.error(
                    f"ECPay API Error: Code={rtn_code}, Message={msg}, Response={response_dict}"
                )
                raise GatewayError(f"ECPay API error: {msg}", code=rtn_code)

            return response_dict

        except requests.exceptions.Timeout:
            raise GatewayError(f"ECPay API timeout ({self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise GatewayError(f"ECPay API communication error: {e}")

    def send_query_order_request(self, data: dict) -> dict:
        """Sends QueryTradeInfo request."""
        endpoint = "/Cashier/QueryTradeInfo/V5"
        if "MerchantTradeNo" not in data:
            raise ValidationError("MerchantTradeNo is required for ECPay query.")
        logger.info(
            f"Sending ECPay QueryTradeInfo for MerchantTradeNo: {data['MerchantTradeNo']}"
        )
        return self._send_api_request(endpoint, data)

    def send_action_request(self, data: dict) -> dict:
        """Sends Credit Card DoAction request (Capture/Refund/Cancel)."""
        endpoint = "/CreditDetail/DoAction/V5"
        required = ["MerchantTradeNo", "TradeNo", "Action", "TotalAmount"]
        if not all(k in data for k in required):
            raise ValidationError(f"Missing params for ECPay DoAction: {required}")
        logger.info(
            f"Sending ECPay DoAction '{data['Action']}' for TradeNo: {data['TradeNo']}"
        )
        return self._send_api_request(endpoint, data)
