import logging
import os
import time
from datetime import datetime

from flask import Flask, render_template_string

# SDK Imports
from payment_gateway_sdk import GatewayFactory
from payment_gateway_sdk import ValidationError, GatewayError, AuthenticationError
from payment_gateway_sdk.gateways.ecpay import EcpayAdapter, EcpayCreditPaymentInput

# Flask App Setup
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# SDK Configuration - *** REPLACE WITH YOUR SANDBOX CREDENTIALS ***
SDK_CONFIG = {
    "sdk_settings": {"default_timeout": 30},
    "ecpay": {
        "merchant_id": os.environ.get("ECPAY_MERCHANT_ID", "3002607"),
        "hash_key": os.environ.get("ECPAY_HASH_KEY", "pwFHCqoQZGmho4w6"),
        "hash_iv": os.environ.get("ECPAY_HASH_IV", "EkRm7iFT261dpevs"),
        "is_sandbox": True,
    },
}

# Initialize Factory
try:
    factory = GatewayFactory(config=SDK_CONFIG)
    logging.info("GatewayFactory initialized successfully.")
except Exception as e:
    logging.critical(f"Failed to initialize GatewayFactory: {e}", exc_info=True)
    factory = None


# Helper
def generate_order_id(prefix="SDK"):
    return (
        f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{int(time.time()*1000)%1000}"
    )


# HTML Template for Redirect
REDIRECT_FORM_HTML = """<!DOCTYPE html><html><head><title>Redirecting...</title></head><body><p>Redirecting to ECPay...</p><form id="ecpay_form" method="post" action="{{ redirect_url }}">{% for key, value in form_data.items() %}<input type="hidden" name="{{ key }}" value="{{ value }}">{% endfor %}</form><script>document.getElementById('ecpay_form').submit();</script></body></html>"""


# Route to Trigger Payment
@app.route("/")
def trigger_payment():
    if not factory:
        return "SDK Factory not initialized.", 500
    logging.info("\n--- Triggering Example: pay_with_credit_installment ---")
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")
        order_id = generate_order_id("INSTALL")
        credit_input = EcpayCreditPaymentInput(
            order_id=order_id,
            amount=1200,  # Amount eligible for installments
            currency="TWD",
            details="Flask Installment Test (3,6,12)",
            return_url="https://your-publicly-accessible-domain.com/callback/ecpay_return",  # MUST be public
            credit_installment="3,6,12",  # Offer installments
        )
        output = adapter.pay_with_credit(credit_input)
        if output.success and output.redirect_url:
            logging.info(f"SUCCESS! Order ID: {order_id}. Redirecting...")
            return render_template_string(
                REDIRECT_FORM_HTML,
                redirect_url=output.redirect_url,
                form_data=output.redirect_form_data,
            )
        else:
            logging.error(
                f"FAILED! Order ID: {order_id}, Message: {output.message}, Code: {output.error_code}"
            )
            return (
                f"Payment Initiation Failed: {output.message} (Code: {output.error_code})",
                400,
            )
    except (ValidationError, GatewayError, AuthenticationError) as e:
        logging.error(f"SDK Error: {e}", exc_info=True)
        return f"SDK Error: {str(e)}", 500
    except Exception as e:
        logging.error("Unexpected Error", exc_info=True)
        return "An unexpected server error occurred.", 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
