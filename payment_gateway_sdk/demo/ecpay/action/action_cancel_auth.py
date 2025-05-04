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
    EcpayCancelAuthInput,
    EcpayCancelAuthOutput,
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


# Route to Trigger Cancel Authorization Action
@app.route("/")
def trigger_cancel_auth():
    if not factory:
        return "SDK Factory not initialized.", 500

    # *** REPLACE with actual data from a successful CREDIT CARD transaction ***
    #     (Ensure it's AUTHORIZED but not captured/closed yet in Sandbox)
    merchant_trade_no_to_cancel = "CREDIT120231115111500999"  # Your original Order ID
    gateway_trade_no_to_cancel = "2311151115000000999"  # ECPay's TradeNo
    original_amount_for_cancel = 200  # Original authorized amount
    # *************************************************************************

    if not merchant_trade_no_to_cancel or not gateway_trade_no_to_cancel:
        return jsonify({"error": "Please set cancel auth variables in the code."}), 400

    logging.info(f"\n--- Triggering Example: cancel_authorization ---")
    logging.info(f"  MerchantTradeNo: {merchant_trade_no_to_cancel}")
    logging.info(f"  TradeNo: {gateway_trade_no_to_cancel}")
    logging.info(f"  Original Amount: {original_amount_for_cancel}")
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")

        # *** Use specific EcpayCancelAuthInput DTO ***
        cancel_input = EcpayCancelAuthInput(
            merchant_trade_no=merchant_trade_no_to_cancel,
            gateway_trade_no=gateway_trade_no_to_cancel,
            original_amount=original_amount_for_cancel,  # ECPay requires amount here
        )

        # *** Call specific cancel_authorization method ***
        cancel_output: EcpayCancelAuthOutput = adapter.cancel_authorization(
            cancel_input
        )

        result_data = {
            "success": cancel_output.success,
            "status": cancel_output.status.name,
            "message": cancel_output.message,
            "error_code": cancel_output.error_code,
            "merchant_trade_no": cancel_output.merchant_trade_no,
            "gateway_trade_no": cancel_output.gateway_trade_no,
            "raw_response": cancel_output.raw_response,
        }

        if cancel_output.success:
            logging.info(
                f"CANCEL AUTH ACTION SUCCESS for {merchant_trade_no_to_cancel}: Status: {cancel_output.status.name}"
            )
            return jsonify(result_data), 200
        else:
            logging.error(
                f"CANCEL AUTH ACTION FAILED for {merchant_trade_no_to_cancel}: {cancel_output.message} (Code: {cancel_output.error_code})"
            )
            return jsonify(result_data), 400

    except (
        ValidationError,
        GatewayError,
        NotImplementedError,
        AuthenticationError,
    ) as e:
        logging.error(f"SDK Error during cancel auth action: {e}", exc_info=True)
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error("Unexpected Error during cancel auth action", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
