# gateways/ecpay/utils.py
from urllib.parse import quote_plus


def ecpay_url_encode(text: str) -> str:
    """
    Performs URL encoding compatible with ECPay's CheckMacValue calculation.
    Based on ECPay docs: uses standard percent-encoding, but converts result to lowercase
    and does *not* encode reserved characters like -, _, ., !, *, (, ).
    """
    # Encode everything except A-Z, a-z, 0-9, and the specified reserved characters
    # quote_plus handles space to '+' which is standard for application/x-www-form-urlencoded
    encoded = quote_plus(text, safe="-_.~!*()")

    # ECPay documentation often implies the *entire encoded string* should be lowercased
    # for the CheckMacValue calculation step.
    # Let's return the encoded string as is, and the SecurityHelper will lowercase it.
    # However, if specific %XX codes needed transformation, it would happen here.
    # Example (if needed, based on testing): encoded = encoded.replace('%2f', '/')

    # Based on provided docs and common practice for CheckMacValue:
    # No specific %XX replacements seem required *before* hashing, unlike MD5.
    # The crucial part is the specific character set for quote_plus's `safe` parameter
    # and the final lowercasing performed in the SecurityHelper.

    return encoded
