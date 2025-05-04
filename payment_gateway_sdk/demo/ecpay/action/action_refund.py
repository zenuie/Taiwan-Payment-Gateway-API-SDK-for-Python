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
    EcpayRefundInput,
    EcpayRefundOutput,
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


# Route to Trigger Refund Action
@app.route("/")
def trigger_refund():
    if not factory:
        return "SDK Factory not initialized.", 500

    # *** REPLACE with actual data from a successful/captured CREDIT CARD transaction in Sandbox ***
    merchant_trade_no_to_refund = "CREDIT120231115103000123"  # Your original Order ID
    gateway_trade_no_to_refund = (
        "2311151030000000123"  # ECPay's TradeNo for the transaction
    )
    amount_to_refund = 50  # Amount to refund
    # *****************************************************************************************

    if not merchant_trade_no_to_refund or not gateway_trade_no_to_refund:
        return jsonify({"error": "Please set refund variables in the code."}), 400

    logging.info(f"\n--- Triggering Example: refund ---")  # Changed log message
    logging.info(f"  MerchantTradeNo: {merchant_trade_no_to_refund}")
    logging.info(f"  TradeNo: {gateway_trade_no_to_refund}")
    logging.info(f"  Amount: {amount_to_refund}")
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")

        # *** Use specific EcpayRefundInput DTO ***
        refund_input = EcpayRefundInput(
            merchant_trade_no=merchant_trade_no_to_refund,
            gateway_trade_no=gateway_trade_no_to_refund,
            refund_amount=amount_to_refund,  # Use correct field name
        )

        # *** Call specific refund method ***
        refund_output: EcpayRefundOutput = adapter.refund(
            refund_input
        )  # Explicitly type hint output

        result_data = {
            "success": refund_output.success,
            "status": refund_output.status.name,
            "message": refund_output.message,
            "error_code": refund_output.error_code,
            "merchant_trade_no": refund_output.merchant_trade_no,
            "gateway_trade_no": refund_output.gateway_trade_no,
            "raw_response": refund_output.raw_response,
        }

        if refund_output.success:
            logging.info(
                f"REFUND ACTION SUCCESS for {merchant_trade_no_to_refund}: Status: {refund_output.status.name}"
            )
            return jsonify(result_data), 200
        else:
            logging.error(
                f"REFUND ACTION FAILED for {merchant_trade_no_to_refund}: {refund_output.message} (Code: {refund_output.error_code})"
            )
            return jsonify(result_data), 400

    except (
        ValidationError,
        GatewayError,
        NotImplementedError,
        AuthenticationError,
    ) as e:
        logging.error(f"SDK Error during refund action: {e}", exc_info=True)
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error("Unexpected Error during refund action", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
