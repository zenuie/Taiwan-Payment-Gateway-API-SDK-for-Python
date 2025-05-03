# gateways/ecpay/security.py
import hashlib
import hmac

from .utils import ecpay_url_encode  # Import from sibling utils.py


class EcpaySecurityHelper:
    """Handles ECPay specific security logic like CheckMacValue."""

    def __init__(self, hash_key: str, hash_iv: str):
        if not hash_key or not hash_iv:
            raise ValueError("ECPay HashKey and HashIV must be provided.")
        self.hash_key = hash_key
        self.hash_iv = hash_iv

    def calculate_check_mac_value(self, params: dict) -> str:
        """Calculates the ECPay CheckMacValue."""
        # Create a copy to avoid modifying the original dict
        params_copy = params.copy()
        if "CheckMacValue" in params_copy:
            del params_copy["CheckMacValue"]

        # 1. Sort parameters by key alphabetically (case-insensitive for keys)
        sorted_params = sorted(params_copy.items(), key=lambda x: x[0].lower())

        # 2. Format into string: "Key1=Value1&Key2=Value2..."
        param_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        # 3. Prepend HashKey, append HashIV
        full_string = f"HashKey={self.hash_key}&{param_string}&HashIV={self.hash_iv}"

        # 4. URL Encode using DotNet compatible encoding and lowercase
        encoded_string = ecpay_url_encode(full_string).lower()

        # 5. Calculate SHA256 hash (HMAC is not used by ECPay for SHA256 CheckMacValue)
        hashed = hashlib.sha256(encoded_string.encode("utf-8"))

        # 6. Convert to uppercase hex string
        check_mac_value = hashed.hexdigest().upper()

        return check_mac_value

    def verify_check_mac_value(self, received_params: dict) -> bool:
        """Verifies the received CheckMacValue from ECPay callback."""
        if "CheckMacValue" not in received_params:
            print("Warning: CheckMacValue not found in received parameters.")
            return False

        received_mac = received_params["CheckMacValue"]
        # Important: Calculate based on a copy, excluding the received CheckMacValue
        calculated_mac = self.calculate_check_mac_value(received_params.copy())

        # Use compare_digest for timing attack resistance
        return hmac.compare_digest(received_mac, calculated_mac)
