import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify

# SDK Imports
from payment_gateway_sdk import GatewayFactory, QueryInput, QueryOutput
from payment_gateway_sdk.gateways.ecpay import EcpayAdapter
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

    # *** REPLACE with the MerchantTradeNo of an order you created in Sandbox ***
    order_id_to_query = "CREDIT120231115103000123"  # Example placeholder
    # **************************************************************************

    if not order_id_to_query:
        return (
            jsonify(
                {"error": "Please set the 'order_id_to_query' variable in the code."}
            ),
            400,
        )

    logging.info(
        f"\n--- Triggering Example: query_transaction (Order ID: {order_id_to_query}) ---"
    )
    try:
        adapter: EcpayAdapter = factory.get_adapter("ecpay")
        query_input = QueryInput(order_id=order_id_to_query)
        query_output: QueryOutput = adapter.query_transaction(query_input)

        if query_output.success and query_output.transactions:
            tx = query_output.transactions[0]
            logging.info(f"QUERY SUCCESS for {order_id_to_query}")
            result = {
                "order_id": tx.order_id,
                "gateway_trade_no": tx.gateway_trade_no,
                "status": tx.status.name,
                "amount": tx.amount,
                "payment_type": tx.payment_type,
                "payment_time": tx.payment_time,
                "raw_data_summary": {
                    k: v for k, v in tx.raw_data.items() if k != "CheckMacValue"
                },
            }
            return jsonify(result)
        elif query_output.success:
            logging.warning(
                f"Query successful for {order_id_to_query}, but no transaction data found."
            )
            return (
                jsonify(
                    {"message": "Query successful, but no transaction data found."}
                ),
                404,
            )
        else:
            logging.error(
                f"QUERY FAILED for {order_id_to_query}: {query_output.message} (Code: {query_output.error_code})"
            )
            return (
                jsonify(
                    {
                        "message": f"Query Failed: {query_output.message}",
                        "error_code": query_output.error_code,
                        "raw_response": query_output.raw_response,
                    }
                ),
                400,
            )
    except (GatewayError, NotImplementedError) as e:
        logging.error(f"SDK Error querying {order_id_to_query}: {e}", exc_info=True)
        return jsonify({"message": f"SDK Error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Unexpected Error querying {order_id_to_query}", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500


# Flask App Runner
if __name__ == "__main__":
    if factory:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        logging.critical("Cannot start Flask app: SDK Factory failed.")
