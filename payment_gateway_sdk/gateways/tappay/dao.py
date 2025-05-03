# payment_gateway_sdk/gateways/tappay/dao.py
# (Content unchanged from the previous fully populated version)
import requests
import json
import logging
from ...core.exceptions import GatewayError, AuthenticationError

logger = logging.getLogger(__name__)


class TappayDAO:
    def __init__(self, config: dict):
        self.config = config
        self.partner_key = config.get("partner_key")
        self.merchant_id = config.get("merchant_id")
        self.base_url = config.get("base_url")
        self.timeout = int(config.get("timeout", 30))
        if not self.partner_key:
            raise AuthenticationError("TapPay partner_key missing.")
        if not self.base_url:
            raise ValueError("TapPay base_url missing.")

    def _send_request(self, endpoint: str, data: dict) -> dict:
        url = self.base_url + endpoint
        headers = {"Content-Type": "application/json", "x-api-key": self.partner_key}
        data["partner_key"] = self.partner_key
        if "merchant_id" not in data and self.merchant_id:
            data["merchant_id"] = self.merchant_id
        payload = {k: v for k, v in data.items() if v is not None}
        try:
            logger.debug(f"Sending request to TapPay URL: {url}")
            logger.debug(f"TapPay Headers: {headers}")
            logger.debug(f"TapPay Payload: {json.dumps(payload)}")
            response = requests.post(
                url=url, headers=headers, json=payload, timeout=self.timeout
            )
            logger.debug(f"TapPay Raw Response Status: {response.status_code}")
            logger.debug(f"TapPay Raw Response Body: {response.text}")
            response_json = response.json()  # Try decoding first
            response.raise_for_status()  # Check HTTP status after getting JSON
            if response_json.get("status") != 0 and response_json.get("status") != 2:
                raise GatewayError(
                    f"TapPay API error ({response_json.get('status')}): {response_json.get('msg', 'Unknown')}",
                    code=response_json.get("status"),
                    raw_response=response_json,
                )
            return response_json
        except requests.exceptions.Timeout:
            raise GatewayError(f"TapPay timeout ({self.timeout}s).")
        except (
            requests.exceptions.HTTPError
        ) as e:  # Handle HTTP errors specifically, maybe use response_json if available
            msg = f"TapPay HTTP error: {e}"
            code = e.response.status_code
            raw = response_json if "response_json" in locals() else response.text
            if isinstance(raw, dict) and raw.get("msg"):
                msg = (
                    f"TapPay HTTP error: {raw['msg']}"  # Use TapPay message if possible
                )
            logger.error(msg, exc_info=True)
            raise GatewayError(msg, code=code, raw_response=raw)
        except requests.exceptions.RequestException as e:
            raise GatewayError(f"TapPay communication error: {e}")
        except json.JSONDecodeError:
            raise GatewayError(
                f"TapPay JSON decode error: {response.text[:200]}"
            )  # Show snippet

    def send_pay_by_prime_request(self, data: dict) -> dict:
        return self._send_request("/payment/pay-by-prime", data)

    def send_pay_by_token_request(self, data: dict) -> dict:
        return self._send_request("/payment/pay-by-token", data)

    def send_refund_request(self, data: dict) -> dict:
        return self._send_request("/transaction/refund", data)

    def send_query_request(self, data: dict) -> dict:
        return self._send_request("/transaction/query", data)
