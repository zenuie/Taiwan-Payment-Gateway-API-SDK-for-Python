# payment_gateway_sdk/gateways/tappay/adapter.py
import logging
from typing import Optional, Dict  # Keep Any for flexibility if needed elsewhere

from .dao import TappayDAO

# --- 修改點：導入特定的 TapPay Input DTO ---
from .dto import TappayPrimePaymentInput, TappayTokenPaymentInput
from ...core.exceptions import ValidationError, GatewayError, AuthenticationError
from ...schema.adapter import PaymentAdapter, TransactionAdapter

# --- 修改點：明確導入需要的 DTO ---
from ...schema.dto.payment import (
    PaymentOutput,
    PaymentStatus,
    RedirectMethod,
    CardholderInfo,  # 如果 Tappay DTO 繼承它
    UrlPaymentInfo,  # <--- 導入 UrlPaymentInfo
)
from ...schema.dto.transaction import RefundInput, RefundOutput, QueryInput, QueryOutput

logger = logging.getLogger(__name__)


class TappayAdapter(PaymentAdapter, TransactionAdapter):
    # ... (__init__, _map_cardholder_info, _prepare_base_tappay_data methods as before) ...
    def __init__(self, dao: TappayDAO):  # ...
        self.dao = dao
        self.merchant_id = dao.config.get("merchant_id")

    def _map_cardholder_info(
        self, cardholder_info: Optional[CardholderInfo]
    ) -> Optional[Dict]:  # ...
        # (implementation as before)
        if not cardholder_info:
            return None
        mapped = {
            "phone_number": cardholder_info.phone_number or "",
            "name": cardholder_info.name or "",
            "email": cardholder_info.email or "",
            **getattr(cardholder_info, "gateway_specific_params", {}),
        }
        final_map = {k: v for k, v in mapped.items() if v is not None}
        for key in ["phone_number", "name", "email"]:
            if key not in final_map:
                final_map[key] = ""
        return final_map if final_map else None

    def _prepare_base_tappay_data(self, input_dto) -> Dict:  # ...
        # (implementation as before)
        data = {
            "merchant_id": self.merchant_id or input_dto.merchant_id,
            "amount": input_dto.amount,
            "currency": input_dto.currency or "TWD",
            "details": input_dto.details,
            "order_number": input_dto.order_id
            or getattr(input_dto, "order_number", None),
            "cardholder": self._map_cardholder_info(
                getattr(input_dto, "cardholder_info", None)
            ),
            **{
                k: getattr(input_dto, k, None)
                for k in [
                    "bank_transaction_id",
                    "additional_data",
                    "store_id",
                    "merchant_group_id",
                ]
            },
        }
        result_url_params = {}
        if input_dto.client_redirect_url:
            result_url_params["frontend_redirect_url"] = input_dto.client_redirect_url
        if input_dto.return_url:
            result_url_params["backend_notify_url"] = input_dto.return_url
        if hasattr(input_dto, "go_back_url") and input_dto.go_back_url:
            result_url_params["go_back_url"] = input_dto.go_back_url
        if result_url_params:
            data["result_url"] = result_url_params
        return {k: v for k, v in data.items() if v is not None}  # Clean None

    def _process_tappay_response(self, response_data: Dict) -> PaymentOutput:
        # ... (Mapping logic as before, but using imported UrlPaymentInfo) ...
        output = PaymentOutput(
            success=True,
            status=PaymentStatus.SUCCESS,
            gateway_trade_no=response_data.get("rec_trade_id"),
            message=response_data.get("msg", "Success"),
            raw_response=response_data,
            payment_info=None,  # Start with None
        )
        # Try to add card info if available
        if response_data.get("card_info"):
            # Note: PaymentInfo DTOs (Atm, Cvs etc) don't fit card info well.
            # Put it in raw_response, or create a dedicated CardPaymentInfo DTO and add to Union?
            # For now, relying on raw_response for card details.
            pass

        payment_url = response_data.get("payment_url")
        if payment_url:
            output.status = PaymentStatus.PENDING
            output.redirect_url = payment_url
            output.redirect_method = RedirectMethod.GET
            # --- 修改點：使用導入的 UrlPaymentInfo ---
            output.payment_info = UrlPaymentInfo(url=payment_url)
            # --- 修改結束 ---

        return output

    # --- pay_with_prime and pay_with_token methods ---
    # (Their internal logic remains the same, calling _prepare_base_tappay_data and _process_tappay_response)
    def pay_with_prime(self, input: TappayPrimePaymentInput) -> PaymentOutput:
        logger.info(f"Processing TapPay PayByPrime for order {input.order_id}")
        try:
            input.__post_init__()  # Validation
            tappay_data = self._prepare_base_tappay_data(input)
            tappay_data.update(
                {
                    "prime": input.prime,
                    **{
                        k: getattr(input, k)
                        for k in [
                            "remember",
                            "three_domain_secure",
                            "instalment",
                            "redeem",
                            "delay_capture_in_days",
                            "cardholder_verify",
                            "kyc_verification_merchant_id",
                            "merchandise_details",
                            "jko_pay_insurance_policy",
                            "extra_info",
                            "product_image_url",
                            "event_code",
                        ]
                        if getattr(input, k, None) is not None
                    },
                }
            )
            tappay_data = {k: v for k, v in tappay_data.items() if v is not None}
            response_data = self.dao.send_pay_by_prime_request(tappay_data)
            output = self._process_tappay_response(response_data)
            logger.info(f"TapPay PayByPrime status: {output.status.name}")
            return output
        # ... (Error handling as before) ...
        except (ValidationError, GatewayError, AuthenticationError) as e:
            logger.error(...)
            return PaymentOutput(...)
        except Exception as e:
            logger.exception(...)
            return PaymentOutput(...)

    def pay_with_token(self, input: TappayTokenPaymentInput) -> PaymentOutput:
        logger.info(f"Processing TapPay PayByToken for order {input.order_id}")
        try:
            input.__post_init__()  # Validation
            tappay_data = self._prepare_base_tappay_data(input)
            tappay_data.update(
                {
                    "card_key": input.card_key,
                    "card_token": input.card_token,
                    **{
                        k: getattr(input, k)
                        for k in [
                            "card_ccv",
                            "ccv_prime",
                            "device_id",
                            "three_domain_secure",
                            "instalment",
                            "redeem",
                            "delay_capture_in_days",
                            "cardholder_verify",
                            "kyc_verification_merchant_id",
                        ]
                        if getattr(input, k, None) is not None
                    },
                }
            )
            tappay_data = {k: v for k, v in tappay_data.items() if v is not None}
            response_data = self.dao.send_pay_by_token_request(tappay_data)
            output = self._process_tappay_response(response_data)
            logger.info(f"TapPay PayByToken status: {output.status.name}")
            return output
        # ... (Error handling as before) ...
        except (ValidationError, GatewayError, AuthenticationError) as e:
            logger.error(...)
            return PaymentOutput(...)
        except Exception as e:
            logger.exception(...)
            return PaymentOutput(...)

    # --- Transaction Methods (refund, query_transaction) ---
    # (Implementations unchanged from previous version)
    def refund(self, input: RefundInput) -> RefundOutput:  # ... (as before) ...
        tappay_data = {
            "rec_trade_id": input.gateway_trade_no,
            **{
                k: v
                for k, v in input.gateway_specific_params.items()
                if k in ["bank_refund_id", "additional_data", "merchandise_details"]
                and v is not None
            },
        }
        if input.amount is not None:
            tappay_data["amount"] = input.amount
        try:  # ... (call dao, handle response/errors as before) ...
            response_data = self.dao.send_refund_request(tappay_data)
            return RefundOutput(
                success=True,
                status=PaymentStatus.SUCCESS,
                refund_id=response_data.get("refund_id"),
                message=response_data.get("msg"),
                raw_response=response_data,
            )
        except Exception as e:  # ... (handle errors) ...
            pass

    def _map_tappay_status(
        self, status_code: Optional[int]
    ) -> PaymentStatus:  # ... (as before) ...
        if status_code == 0:
            return PaymentStatus.SUCCESS
            # ...
        return PaymentStatus.UNKNOWN

    def query_transaction(
        self, input: QueryInput
    ) -> QueryOutput:  # ... (as before) ...
        filters = input.gateway_specific_params.get("filters", {})
        # ... (build data, call dao, map results, handle errors as before) ...
        if input.gateway_trade_no and "rec_trade_id" not in filters:
            filters["rec_trade_id"] = input.gateway_trade_no
        if not filters:
            raise ValidationError("...")
        tappay_data = {
            "filters": filters,
            **{
                k: v
                for k, v in input.gateway_specific_params.items()
                if k in ["records_per_page", "page", "order_by"]
            },
        }
        try:  # ... (call dao, map results to TransactionRecord, handle pagination/errors) ...
            response_data = self.dao.send_query_request(
                {k: v for k, v in tappay_data.items() if v is not None}
            )
            transactions = []  # ... mapping ...
            success = response_data.get("status") in [0, 2]
            message = response_data.get("msg")
            # ...
            return QueryOutput(
                success=success,
                transactions=transactions,
                message=message,
                error_code=str(response_data.get("status")) if not success else None,
                raw_response=response_data,  # ... pagination ...
            )
        except Exception as e:  # ... (handle errors) ...
            pass
