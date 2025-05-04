import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify

# SDK Imports
from payment_gateway_sdk import GatewayFactory, QueryInput, PaymentInfoQueryOutput
from payment_gateway_sdk.gateways.ecpay import EcpayAdapter
from payment_gateway_sdk import (
    AtmPaymentInfo,
    CvsPaymentInfo,
    BarcodePaymentInfo,
)  # Import info DTOs
from payment_gateway_sdk import GatewayError, NotImplementedError

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


# Route to Trigger Query
@app.route("/")
def trigger_query():
    if not factory:
        return "SDK Factory not initialized.", 500

    # *** REPLACE with the MerchantTradeNo of an ATM/CVS/Barcode order created in Sandbox ***
    #     (BEFORE the user would normally pay, to get the code/expiry)
    order_id_to_query = "ATM20231115103500456"  # Example placeholder
    # ***********************************************************************************

    if not order_id_to_query:
        return (
            jsonify(
                {"error": "Please set the 'order_id_to_query' variable in the code."}
            ),
            400,
        )

    logging.info(
        f"\n--- Triggering Example: query_payment_info (Order ID: {order_id_to_query}) ---"
    )
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")
        query_input = QueryInput(order_id=order_id_to_query)
        info_output: PaymentInfoQueryOutput = adapter.query_payment_info(query_input)

        if info_output.success and info_output.payment_info:
            logging.info(f"PAYMENT INFO QUERY SUCCESS for {order_id_to_query}:")
            p_info = info_output.payment_info
            info_dict = {}
            if isinstance(p_info, AtmPaymentInfo):
                info_dict = p_info.__dict__
                info_dict["type"] = "ATM"
            elif isinstance(p_info, CvsPaymentInfo):
                info_dict = p_info.__dict__
                info_dict["type"] = "CVS"
            elif isinstance(p_info, BarcodePaymentInfo):
                info_dict = p_info.__dict__
                info_dict["type"] = "Barcode"

            result = {
                "success": True,
                "message": info_output.message,
                "merchant_trade_no": info_output.merchant_trade_no,
                "payment_method_name": info_output.payment_method_name,
                "payment_info": info_dict,
            }
            return jsonify(result)
        elif info_output.success:
            logging.warning(
                f"Payment info query successful for {order_id_to_query}, but no specific payment info structure found."
            )
            return (
                jsonify(
                    {
                        "message": "Query successful, but no specific payment info found (check order type?)."
                    }
                ),
                404,
            )
        else:
            logging.error(
                f"PAYMENT INFO QUERY FAILED for {order_id_to_query}: {info_output.message} (Code: {info_output.error_code})"
            )
            return (
                jsonify(
                    {
                        "message": f"Query Failed: {info_output.message}",
                        "error_code": info_output.error_code,
                        "raw_response": info_output.raw_response,
                    }
                ),
                400,
            )
    except (GatewayError, NotImplementedError) as e:
        logging.error(
            f"SDK Error querying payment info for {order_id_to_query}: {e}",
            exc_info=True,
        )
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error(
            f"Unexpected Error querying payment info for {order_id_to_query}",
            exc_info=True,
        )
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
