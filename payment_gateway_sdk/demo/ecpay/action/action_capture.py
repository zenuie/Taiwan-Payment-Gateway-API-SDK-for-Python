import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify

# SDK Imports
from payment_gateway_sdk import GatewayFactory

# *** Import specific action DTOs and Adapter ***
from payment_gateway_sdk.gateways.ecpay import (
    EcpayAdapter,
    EcpayCaptureInput,
    EcpayCaptureOutput,
)
from payment_gateway_sdk import (
    PaymentStatus,
    ValidationError,
    GatewayError,
    AuthenticationError,
    NotImplementedError,
)

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


# Route to Trigger Capture Action
@app.route("/")
def trigger_capture():
    if not factory:
        return "SDK Factory not initialized.", 500

    # *** REPLACE with actual data from a successful CREDIT CARD transaction ***
    #     (Ensure it's AUTHORIZED but not captured/closed yet in Sandbox)
    merchant_trade_no_to_capture = "CREDIT120231115110000789"  # Your original Order ID
    gateway_trade_no_to_capture = "2311151100000000789"  # ECPay's TradeNo
    amount_to_capture = 150  # Usually the original authorized amount
    # *************************************************************************

    if not merchant_trade_no_to_capture or not gateway_trade_no_to_capture:
        return jsonify({"error": "Please set capture variables in the code."}), 400

    logging.info(f"\n--- Triggering Example: capture ---")  # Changed log message
    logging.info(f"  MerchantTradeNo: {merchant_trade_no_to_capture}")
    logging.info(f"  TradeNo: {gateway_trade_no_to_capture}")
    logging.info(f"  Amount: {amount_to_capture}")
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")

        # *** Use specific EcpayCaptureInput DTO ***
        capture_input = EcpayCaptureInput(
            merchant_trade_no=merchant_trade_no_to_capture,
            gateway_trade_no=gateway_trade_no_to_capture,
            capture_amount=amount_to_capture,  # Use correct field name
        )

        # *** Call specific capture method ***
        capture_output: EcpayCaptureOutput = adapter.capture(
            capture_input
        )  # Explicitly type hint output

        result_data = {
            "success": capture_output.success,
            "status": capture_output.status.name,
            "message": capture_output.message,
            "error_code": capture_output.error_code,
            "merchant_trade_no": capture_output.merchant_trade_no,
            "gateway_trade_no": capture_output.gateway_trade_no,
            "raw_response": capture_output.raw_response,
        }

        if capture_output.success:
            logging.info(
                f"CAPTURE ACTION SUCCESS for {merchant_trade_no_to_capture}: Status: {capture_output.status.name}"
            )
            return jsonify(result_data), 200
        else:
            logging.error(
                f"CAPTURE ACTION FAILED for {merchant_trade_no_to_capture}: {capture_output.message} (Code: {capture_output.error_code})"
            )
            return jsonify(result_data), 400

    except (
        ValidationError,
        GatewayError,
        NotImplementedError,
        AuthenticationError,
    ) as e:
        logging.error(f"SDK Error during capture action: {e}", exc_info=True)
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error("Unexpected Error during capture action", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
