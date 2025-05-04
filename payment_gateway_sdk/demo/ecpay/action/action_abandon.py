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
    EcpayAbandonInput,
    EcpayAbandonOutput,
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


# Route to Trigger Abandon Action
@app.route("/")
def trigger_abandon():
    if not factory:
        return "SDK Factory not initialized.", 500

    # *** REPLACE with actual data from a successful CREDIT CARD transaction ***
    #     (Ensure it's AUTHORIZED but not captured/closed yet in Sandbox)
    merchant_trade_no_to_abandon = "CREDIT120231115112000111"  # Your original Order ID
    gateway_trade_no_to_abandon = "2311151120000000111"  # ECPay's TradeNo
    original_amount_for_abandon = 300  # Original authorized amount
    # *************************************************************************

    if not merchant_trade_no_to_abandon or not gateway_trade_no_to_abandon:
        return jsonify({"error": "Please set abandon variables in the code."}), 400

    logging.info(f"\n--- Triggering Example: abandon_transaction ---")
    logging.info(f"  MerchantTradeNo: {merchant_trade_no_to_abandon}")
    logging.info(f"  TradeNo: {gateway_trade_no_to_abandon}")
    logging.info(f"  Original Amount: {original_amount_for_abandon}")
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")

        # *** Use specific EcpayAbandonInput DTO ***
        abandon_input = EcpayAbandonInput(
            merchant_trade_no=merchant_trade_no_to_abandon,
            gateway_trade_no=gateway_trade_no_to_abandon,
            original_amount=original_amount_for_abandon,  # ECPay requires amount here
        )

        # *** Call specific abandon_transaction method ***
        abandon_output: EcpayAbandonOutput = adapter.abandon_transaction(abandon_input)

        result_data = {
            "success": abandon_output.success,
            "status": abandon_output.status.name,
            "message": abandon_output.message,
            "error_code": abandon_output.error_code,
            "merchant_trade_no": abandon_output.merchant_trade_no,
            "gateway_trade_no": abandon_output.gateway_trade_no,
            "raw_response": abandon_output.raw_response,
        }

        if abandon_output.success:
            logging.info(
                f"ABANDON ACTION SUCCESS for {merchant_trade_no_to_abandon}: Status: {abandon_output.status.name}"
            )
            return jsonify(result_data), 200
        else:
            logging.error(
                f"ABANDON ACTION FAILED for {merchant_trade_no_to_abandon}: {abandon_output.message} (Code: {abandon_output.error_code})"
            )
            return jsonify(result_data), 400

    except (
        ValidationError,
        GatewayError,
        NotImplementedError,
        AuthenticationError,
    ) as e:
        logging.error(f"SDK Error during abandon action: {e}", exc_info=True)
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error("Unexpected Error during abandon action", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
