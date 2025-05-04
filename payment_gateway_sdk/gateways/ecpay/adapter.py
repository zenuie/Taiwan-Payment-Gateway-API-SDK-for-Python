# payment_gateway_sdk/gateways/ecpay/adapter.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

from .constants import EcpayPaymentMethod, EcpayAction, EcpayRtnCode, EcpayDeviceSource
from .dao import EcpayDAO

# Import DTOs DEFINED LOCALLY in gateways/ecpay/dto.py
from .dto import (
    # Payment Inputs
    EcpayBasePaymentInput,
    EcpayCreditPaymentInput,
    EcpayAtmPaymentInput,
    EcpayCvsPaymentInput,
    EcpayBarcodePaymentInput,
    EcpayWebAtmPaymentInput,
    EcpayApplePayPaymentInput,
    EcpayTwqrPaymentInput,
    EcpayBnplPaymentInput,
    # Specific Action Inputs/Outputs
    EcpayCaptureInput,
    EcpayCaptureOutput,
    EcpayRefundInput,
    EcpayRefundOutput,
    EcpayCancelAuthInput,
    EcpayCancelAuthOutput,
    EcpayAbandonInput,
    EcpayAbandonOutput,
    # Specific Query Inputs/Outputs
    EcpayQueryCreditCardDetailsInput,
    EcpayQueryCreditCardDetailsOutput,
    EcpayQueryPeriodicDetailsOutput,
    EcpayCreditCloseDataRecord,
    EcpayPeriodicExecLogRecord,
)
from ...core.exceptions import (
    ValidationError,
    GatewayError,
    AuthenticationError,
    NotImplementedError,
)
from ...schema.adapter import PaymentAdapter, TransactionAdapter  # Keep ABCs

# Import schema DTOs ONLY for generic outputs/inputs/info-structs
from ...schema.dto.payment import (
    PaymentOutput,
    PaymentStatus,
    RedirectMethod,
    AtmPaymentInfo,
    CvsPaymentInfo,
    BarcodePaymentInfo,
)
from ...schema.dto.transaction import (
    QueryInput,
    QueryOutput,
    TransactionRecord,
    PaymentInfoQueryOutput,
    ActionInput,
    ActionOutput,  # Keep generic action DTOs for potential generic implementation
)

logger = logging.getLogger(__name__)


class EcpayAdapter(PaymentAdapter, TransactionAdapter):
    """ECPay specific implementation with specific methods for all operations."""

    def __init__(self, dao: EcpayDAO):
        self.dao = dao

    # --- Payment Methods ---
    def _prepare_common_params(
        self, input_dto: EcpayBasePaymentInput
    ) -> Dict[str, Any]:
        """Prepares parameters common to all ECPay AIO checkouts."""
        # ItemName processing (max 400 bytes, newline to #)
        item_name_str = input_dto.details.replace("\n", "#").replace("\r", "")
        try:
            item_name_bytes = item_name_str.encode("utf-8")
            if len(item_name_bytes) > 400:
                logger.warning("ItemName exceeds 400 bytes, truncating.")
                item_name_str = item_name_bytes[:400].decode("utf-8", "ignore")
                if not item_name_str:
                    item_name_str = "Truncated Item Name (Decode Error)"
        except Exception as e:
            logger.error(
                f"Error processing ItemName encoding/truncation: {e}", exc_info=True
            )
            item_name_str = "Processed Item Name (Error)"  # Fallback

        params = {
            "MerchantTradeNo": input_dto.order_id,
            "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "PaymentType": "aio",
            "TotalAmount": input_dto.amount,
            "TradeDesc": input_dto.details,
            "ItemName": item_name_str,
            "ReturnURL": input_dto.return_url,  # Already validated as mandatory in DTO
            "EncryptType": 1,
            # Add common optional fields from the base DTO
            "OrderResultURL": input_dto.client_redirect_url,
            "ClientBackURL": input_dto.client_back_url,
            "ItemURL": input_dto.item_url,
            "Remark": input_dto.remark,
            "NeedExtraPaidInfo": input_dto.need_extra_paid_info,
            "StoreID": input_dto.store_id,
            "PlatformID": input_dto.platform_id,
            "CustomField1": input_dto.custom_field1,
            "CustomField2": input_dto.custom_field2,
            "CustomField3": input_dto.custom_field3,
            "CustomField4": input_dto.custom_field4,
            "Language": input_dto.language,
            "DeviceSource": input_dto.device_source,  # Added
        }
        # Remove None values before returning
        return {k: v for k, v in params.items() if v is not None}

    def _build_and_return_output(
        self, ecpay_params: Dict[str, Any], order_id: str
    ) -> PaymentOutput:
        """Helper to build form data using DAO and create PaymentOutput for redirect."""
        try:
            # DAO builds the final form data including CheckMacValue
            form_data = self.dao.build_checkout_form_data(ecpay_params)
            checkout_url = self.dao.base_url + "/Cashier/AioCheckOut/V5"

            logger.info(f"ECPay form data generated for order {order_id}")
            return PaymentOutput(
                success=True,
                status=PaymentStatus.PENDING,  # AIO Checkout always starts as Pending
                message="Redirect user to ECPay checkout page.",
                redirect_url=checkout_url,
                redirect_method=RedirectMethod.POST,
                redirect_form_data=form_data,
                raw_response=form_data,  # Store generated form data as raw response
                order_id=order_id,
                payment_method_name=None,  # Method not known until callback/query
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
            logger.error(f"Failed preparing ECPay payment for order {order_id}: {e}")
            error_code = str(e.code) if hasattr(e, "code") and e.code else None
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                error_code=error_code,
                order_id=order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error preparing ECPay payment for order {order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="An unexpected internal error occurred.",
                order_id=order_id,
            )

    def pay_with_credit(self, input: EcpayCreditPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay Credit payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.CREDIT
            if input.credit_installment:
                ecpay_params["CreditInstallment"] = input.credit_installment
            if input.installment_amount:
                ecpay_params["InstallmentAmount"] = input.installment_amount
            if input.redeem == "Y":
                ecpay_params["Redeem"] = "Y"
            if input.union_pay is not None:
                ecpay_params["UnionPay"] = input.union_pay
            if input.binding_card is not None:
                ecpay_params["BindingCard"] = input.binding_card
            if input.merchant_member_id:
                ecpay_params["MerchantMemberID"] = input.merchant_member_id
            if input.period_amount is not None:
                ecpay_params["PeriodAmount"] = input.period_amount
            if input.period_type:
                ecpay_params["PeriodType"] = input.period_type
            if input.frequency is not None:
                ecpay_params["Frequency"] = input.frequency
            if input.exec_times is not None:
                ecpay_params["ExecTimes"] = input.exec_times
            if input.period_return_url:
                ecpay_params["PeriodReturnURL"] = input.period_return_url
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Credit payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing credit payment.",
                order_id=input.order_id,
            )

    def pay_with_atm(self, input: EcpayAtmPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay ATM payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.ATM
            if input.expire_date is not None:
                ecpay_params["ExpireDate"] = input.expire_date
            if input.payment_info_url:
                ecpay_params["PaymentInfoURL"] = input.payment_info_url
            if input.client_redirect_url_for_info:
                ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
                if "ClientBackURL" in ecpay_params:
                    del ecpay_params["ClientBackURL"]
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay ATM payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing ATM payment.",
                order_id=input.order_id,
            )

    def pay_with_cvs(self, input: EcpayCvsPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay CVS payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.CVS
            if input.store_expire_date is not None:
                ecpay_params["StoreExpireDate"] = input.store_expire_date
            if input.payment_info_url:
                ecpay_params["PaymentInfoURL"] = input.payment_info_url
            if input.client_redirect_url_for_info:
                ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
                if "ClientBackURL" in ecpay_params:
                    del ecpay_params["ClientBackURL"]
            if input.desc_1:
                ecpay_params["Desc_1"] = input.desc_1
            if input.desc_2:
                ecpay_params["Desc_2"] = input.desc_2
            if input.desc_3:
                ecpay_params["Desc_3"] = input.desc_3
            if input.desc_4:
                ecpay_params["Desc_4"] = input.desc_4
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay CVS payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing CVS payment.",
                order_id=input.order_id,
            )

    def pay_with_barcode(self, input: EcpayBarcodePaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay Barcode payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.BARCODE
            if input.store_expire_date is not None:
                ecpay_params["StoreExpireDate"] = input.store_expire_date
            if input.payment_info_url:
                ecpay_params["PaymentInfoURL"] = input.payment_info_url
            if input.client_redirect_url_for_info:
                ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
                if "ClientBackURL" in ecpay_params:
                    del ecpay_params["ClientBackURL"]
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Barcode payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing Barcode payment.",
                order_id=input.order_id,
            )

    def pay_with_webatm(self, input: EcpayWebAtmPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay WebATM payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.WEBATM
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay WebATM payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing WebATM payment.",
                order_id=input.order_id,
            )

    def pay_with_applepay(self, input: EcpayApplePayPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay ApplePay payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.APPLEPAY
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay ApplePay payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing ApplePay payment.",
                order_id=input.order_id,
            )

    def pay_with_twqr(self, input: EcpayTwqrPaymentInput) -> PaymentOutput:
        """Initiates ECPay TWQR payment."""
        logger.info(f"Initiating ECPay TWQR payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.TWQR
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay TWQR payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing TWQR payment.",
                order_id=input.order_id,
            )

    def pay_with_bnpl(self, input: EcpayBnplPaymentInput) -> PaymentOutput:
        """Initiates ECPay BNPL (Buy Now Pay Later) payment."""
        logger.info(f"Initiating ECPay BNPL payment for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.BNPL
            if input.payment_info_url:
                ecpay_params["PaymentInfoURL"] = input.payment_info_url
            if input.client_redirect_url_for_info:
                ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
                if "ClientBackURL" in ecpay_params:
                    del ecpay_params["ClientBackURL"]
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay BNPL payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing BNPL payment.",
                order_id=input.order_id,
            )

    def pay_with_ecpay_pay(
        self, input: EcpayBasePaymentInput, choose_payment: str
    ) -> PaymentOutput:
        """Initiates payment via ECPay Pay App. Requires specifying the underlying payment method."""
        logger.info(
            f"Initiating ECPay Pay App payment for order {input.order_id} using {choose_payment}"
        )
        try:
            supported_for_app = [
                EcpayPaymentMethod.CREDIT,
                EcpayPaymentMethod.ATM,
                EcpayPaymentMethod.CVS,
                EcpayPaymentMethod.BARCODE,
                EcpayPaymentMethod.BNPL,
                EcpayPaymentMethod.ALL,
            ]
            if choose_payment not in supported_for_app:
                raise ValidationError(
                    f"Unsupported ChoosePayment '{choose_payment}' for ECPay Pay App."
                )

            input.device_source = EcpayDeviceSource.ECPAY_PAY_APP
            input.__post_init__()

            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = choose_payment
            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Pay payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing ECPay Pay payment.",
                order_id=input.order_id,
            )

    def pay_all_options(
        self, input: EcpayBasePaymentInput, ignore_methods: Optional[List[str]] = None
    ) -> PaymentOutput:
        """Handles 'ALL' payment type, accepting specific ECPay method strings to ignore."""
        logger.info(f"Initiating ECPay ALL payment methods for order {input.order_id}")
        try:
            input.__post_init__()
            ecpay_params = self._prepare_common_params(input)
            ecpay_params["ChoosePayment"] = EcpayPaymentMethod.ALL

            if ignore_methods:
                valid_ignore_values = [
                    getattr(EcpayPaymentMethod, attr)
                    for attr in dir(EcpayPaymentMethod)
                    if not attr.startswith("_") and attr != "ALL"
                ]
                invalid_methods = [
                    m for m in ignore_methods if m not in valid_ignore_values
                ]
                if invalid_methods:
                    logger.warning(
                        f"Ignoring potentially invalid method strings in ignore_methods: {invalid_methods}"
                    )
                ecpay_params["IgnorePayment"] = "#".join(ignore_methods)

            return self._build_and_return_output(ecpay_params, input.order_id)
        except ValidationError as e:
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                order_id=input.order_id,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay ALL payment prep for order {input.order_id}"
            )
            return PaymentOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message="Internal error preparing ALL payment.",
                order_id=input.order_id,
            )

    # --- Transaction Methods (Specific to ECPay) ---

    def _map_ecpay_status(
        self, status_code: Optional[str], payment_type_str: Optional[str] = None
    ) -> PaymentStatus:
        """Maps ECPay RtnCode/TradeStatus strings to SDK PaymentStatus."""
        if status_code == EcpayRtnCode.SUCCESS:
            return PaymentStatus.SUCCESS
        elif status_code == "0":
            if payment_type_str and payment_type_str.startswith(
                (
                    EcpayPaymentMethod.ATM,
                    EcpayPaymentMethod.CVS,
                    EcpayPaymentMethod.BARCODE,
                )
            ):
                return PaymentStatus.PENDING
            else:
                return PaymentStatus.FAILED
        elif status_code == EcpayRtnCode.TRANSACTION_NOT_COMPLETED:
            return PaymentStatus.FAILED
        elif status_code == EcpayRtnCode.ATM_SUCCESS:
            if payment_type_str and payment_type_str.startswith(
                EcpayPaymentMethod.BNPL
            ):  # Match prefix for BNPL_URICH etc.
                return PaymentStatus.APPLYING
            else:
                return PaymentStatus.PENDING
        elif status_code == EcpayRtnCode.CVS_BARCODE_SUCCESS:
            return PaymentStatus.PENDING
        logger.debug(
            f"Mapping unknown ECPay status code: {status_code} (PaymentType: {payment_type_str})"
        )
        return PaymentStatus.UNKNOWN

    # Generic query_transaction implementation using generic DTOs
    def query_transaction(self, input: QueryInput) -> QueryOutput:
        """Queries basic order info using QueryTradeInfo API. Uses generic Input/Output."""
        logger.info(f"Querying ECPay transaction for order_id: {input.order_id}")
        if not input.order_id:
            return QueryOutput(
                success=False,
                message="ECPay query requires 'order_id' (MerchantTradeNo).",
            )

        ecpay_data = {"MerchantTradeNo": input.order_id}
        if input.gateway_specific_params.get("PlatformID"):
            ecpay_data["PlatformID"] = input.gateway_specific_params["PlatformID"]

        try:
            response_data = self.dao.send_query_order_request(ecpay_data)

            transactions = []
            message = "Query successful."
            success = "TradeStatus" in response_data
            error_code = None

            if success:
                payment_type_str = response_data.get("PaymentType")
                sdk_status = self._map_ecpay_status(
                    response_data.get("TradeStatus"), payment_type_str
                )

                def safe_float(val):
                    try:
                        return float(val) if val else None
                    except:
                        return None

                def safe_int(val):
                    try:
                        return int(val) if str(val).isdigit() else None
                    except:
                        return None

                tx = TransactionRecord(
                    gateway_trade_no=response_data.get("TradeNo", ""),
                    status=sdk_status,
                    amount=safe_int(response_data.get("TradeAmt")) or 0,
                    currency="TWD",
                    raw_data=response_data,
                    order_id=response_data.get("MerchantTradeNo"),
                    payment_type=payment_type_str,  # Use the specific string
                    transaction_time=response_data.get("TradeDate"),
                    payment_time=response_data.get("PaymentDate"),
                    store_id=response_data.get("StoreID"),
                    handling_charge=safe_float(response_data.get("HandlingCharge")),
                    payment_type_charge_fee=safe_float(
                        response_data.get("PaymentTypeChargeFee")
                    ),
                    auth_code=response_data.get("auth_code"),
                    card_last_four=response_data.get("card4no"),
                    card_first_six=response_data.get("card6no"),
                )
                transactions.append(tx)
                message = f"Transaction status: {sdk_status.name}"
            else:
                message = response_data.get(
                    "RtnMsg", "Query failed: TradeStatus missing."
                )
                error_code = response_data.get("RtnCode")

            return QueryOutput(
                success=success,
                transactions=transactions,
                message=message,
                error_code=error_code,
                raw_response=response_data,
            )
        except GatewayError as e:
            logger.error(
                f"ECPay GatewayError during query for order {input.order_id}: {e}"
            )
            return QueryOutput(
                success=False,
                message=str(e),
                error_code=str(e.code) if e.code else None,
                raw_response=e.raw_response,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay query for order {input.order_id}"
            )
            return QueryOutput(success=False, message=f"Unexpected query error: {e}")

    # --- Specific ECPay Actions (Replacing do_action) ---

    def _call_ecpay_action_api(
        self,
        action: str,
        merchant_trade_no: str,
        gateway_trade_no: str,
        amount: int,
        platform_id: Optional[str],
    ) -> Dict[str, Any]:
        """Internal helper to call the DAO's action request."""
        ecpay_data = {
            "MerchantTradeNo": merchant_trade_no,
            "TradeNo": gateway_trade_no,
            "Action": action,
            "TotalAmount": amount,
            "PlatformID": platform_id,
        }
        ecpay_data_cleaned = {k: v for k, v in ecpay_data.items() if v is not None}
        # DAO handles adding MerchantID, TimeStamp, CheckMacValue
        return self.dao.send_action_request(ecpay_data_cleaned)

    def capture(self, input: EcpayCaptureInput) -> EcpayCaptureOutput:
        """Performs ECPay Capture/Close (Action='C')."""
        logger.info(
            f"Performing ECPay Capture for MerchantTradeNo: {input.merchant_trade_no}, TradeNo: {input.gateway_trade_no}"
        )
        try:
            # No specific input validation needed beyond DTO types
            response_data = self._call_ecpay_action_api(
                action=EcpayAction.CAPTURE,
                merchant_trade_no=input.merchant_trade_no,
                gateway_trade_no=input.gateway_trade_no,
                amount=input.capture_amount,
                platform_id=input.platform_id,
            )
            success = response_data.get("RtnCode") == EcpayRtnCode.SUCCESS
            status = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED
            return EcpayCaptureOutput(
                success=success,
                status=status,
                message=response_data.get("RtnMsg", ""),
                error_code=response_data.get("RtnCode") if not success else None,
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                gateway_trade_no=response_data.get("TradeNo"),
                raw_response=response_data,
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
            error_code = str(e.code) if hasattr(e, "code") and e.code else None
            return EcpayCaptureOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                error_code=error_code,
                raw_response=getattr(e, "raw_response", None),
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Capture for order {input.merchant_trade_no}"
            )
            return EcpayCaptureOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=f"Unexpected Capture error: {e}",
            )

    def refund(self, input: EcpayRefundInput) -> EcpayRefundOutput:
        """Performs ECPay Refund (Action='R')."""
        logger.info(
            f"Performing ECPay Refund for MerchantTradeNo: {input.merchant_trade_no}, TradeNo: {input.gateway_trade_no}"
        )
        try:
            # No specific input validation needed beyond DTO types
            response_data = self._call_ecpay_action_api(
                action=EcpayAction.REFUND,
                merchant_trade_no=input.merchant_trade_no,
                gateway_trade_no=input.gateway_trade_no,
                amount=input.refund_amount,
                platform_id=input.platform_id,
            )
            success = response_data.get("RtnCode") == EcpayRtnCode.SUCCESS
            status = (
                PaymentStatus.REFUNDED if success else PaymentStatus.FAILED
            )  # Assuming full refund status if API succeeds
            return EcpayRefundOutput(
                success=success,
                status=status,
                message=response_data.get("RtnMsg", ""),
                error_code=response_data.get("RtnCode") if not success else None,
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                gateway_trade_no=response_data.get("TradeNo"),
                raw_response=response_data,
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
            error_code = str(e.code) if hasattr(e, "code") and e.code else None
            return EcpayRefundOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                error_code=error_code,
                raw_response=getattr(e, "raw_response", None),
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Refund for order {input.merchant_trade_no}"
            )
            return EcpayRefundOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=f"Unexpected Refund error: {e}",
            )

    def cancel_authorization(
        self, input: EcpayCancelAuthInput
    ) -> EcpayCancelAuthOutput:
        """Performs ECPay Cancel Authorization (Action='E')."""
        logger.info(
            f"Performing ECPay Cancel Authorization for MerchantTradeNo: {input.merchant_trade_no}, TradeNo: {input.gateway_trade_no}"
        )
        try:
            # No specific input validation needed beyond DTO types
            response_data = self._call_ecpay_action_api(
                action=EcpayAction.CANCEL_AUTH,
                merchant_trade_no=input.merchant_trade_no,
                gateway_trade_no=input.gateway_trade_no,
                amount=input.original_amount,  # ECPay requires amount even for cancel
                platform_id=input.platform_id,
            )
            success = response_data.get("RtnCode") == EcpayRtnCode.SUCCESS
            status = PaymentStatus.CANCELED if success else PaymentStatus.FAILED
            return EcpayCancelAuthOutput(
                success=success,
                status=status,
                message=response_data.get("RtnMsg", ""),
                error_code=response_data.get("RtnCode") if not success else None,
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                gateway_trade_no=response_data.get("TradeNo"),
                raw_response=response_data,
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
            error_code = str(e.code) if hasattr(e, "code") and e.code else None
            return EcpayCancelAuthOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                error_code=error_code,
                raw_response=getattr(e, "raw_response", None),
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Cancel Authorization for order {input.merchant_trade_no}"
            )
            return EcpayCancelAuthOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=f"Unexpected Cancel Auth error: {e}",
            )

    def abandon_transaction(self, input: EcpayAbandonInput) -> EcpayAbandonOutput:
        """Performs ECPay Abandon Transaction (Action='N')."""
        logger.info(
            f"Performing ECPay Abandon Transaction for MerchantTradeNo: {input.merchant_trade_no}, TradeNo: {input.gateway_trade_no}"
        )
        try:
            # No specific input validation needed beyond DTO types
            response_data = self._call_ecpay_action_api(
                action=EcpayAction.ABANDON,
                merchant_trade_no=input.merchant_trade_no,
                gateway_trade_no=input.gateway_trade_no,
                amount=input.original_amount,  # ECPay requires amount even for abandon
                platform_id=input.platform_id,
            )
            success = response_data.get("RtnCode") == EcpayRtnCode.SUCCESS
            status = PaymentStatus.CANCELED if success else PaymentStatus.FAILED
            return EcpayAbandonOutput(
                success=success,
                status=status,
                message=response_data.get("RtnMsg", ""),
                error_code=response_data.get("RtnCode") if not success else None,
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                gateway_trade_no=response_data.get("TradeNo"),
                raw_response=response_data,
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
            error_code = str(e.code) if hasattr(e, "code") and e.code else None
            return EcpayAbandonOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=str(e),
                error_code=error_code,
                raw_response=getattr(e, "raw_response", None),
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay Abandon Transaction for order {input.merchant_trade_no}"
            )
            return EcpayAbandonOutput(
                success=False,
                status=PaymentStatus.ERROR,
                message=f"Unexpected Abandon error: {e}",
            )

    # --- Other Query Methods ---
    def query_payment_info(self, input: QueryInput) -> PaymentInfoQueryOutput:
        """Queries ATM/CVS/BARCODE payment details, returns generic PaymentInfoQueryOutput."""
        logger.info(f"Querying ECPay payment info for order_id: {input.order_id}")
        if not input.order_id:
            return PaymentInfoQueryOutput(
                success=False,
                message="ECPay query payment info requires 'order_id' (MerchantTradeNo).",
            )

        ecpay_data = {"MerchantTradeNo": input.order_id}
        if input.gateway_specific_params.get("PlatformID"):
            ecpay_data["PlatformID"] = input.gateway_specific_params["PlatformID"]

        try:
            response_data = self.dao.send_query_payment_info_request(ecpay_data)

            rtn_code = response_data.get("RtnCode")
            rtn_msg = response_data.get("RtnMsg", "")
            payment_type_str = response_data.get("PaymentType", "")

            success = (
                rtn_code == EcpayRtnCode.ATM_SUCCESS
                and payment_type_str.startswith(EcpayPaymentMethod.ATM)
            ) or (
                rtn_code == EcpayRtnCode.CVS_BARCODE_SUCCESS
                and payment_type_str.startswith(
                    (EcpayPaymentMethod.CVS, EcpayPaymentMethod.BARCODE)
                )
            )

            payment_info_dto = None
            if success:
                if payment_type_str.startswith(EcpayPaymentMethod.ATM):
                    payment_info_dto = AtmPaymentInfo(
                        bank_code=response_data.get("BankCode"),
                        virtual_account=response_data.get("vAccount", ""),
                        expire_date=response_data.get("ExpireDate", ""),
                    )
                elif payment_type_str.startswith(EcpayPaymentMethod.CVS):
                    payment_info_dto = CvsPaymentInfo(
                        payment_no=response_data.get("PaymentNo", ""),
                        expire_date=response_data.get("ExpireDate", ""),
                        payment_url=response_data.get("PaymentURL"),
                    )
                elif payment_type_str.startswith(EcpayPaymentMethod.BARCODE):
                    payment_info_dto = BarcodePaymentInfo(
                        barcode1=response_data.get("Barcode1"),
                        barcode2=response_data.get("Barcode2"),
                        barcode3=response_data.get("Barcode3"),
                        expire_date=response_data.get("ExpireDate", ""),
                    )

            return PaymentInfoQueryOutput(
                success=success,
                message=rtn_msg,
                error_code=rtn_code if not success else None,
                merchant_id=response_data.get("MerchantID"),
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                store_id=response_data.get("StoreID"),
                gateway_trade_no=response_data.get("TradeNo"),
                amount=(
                    int(response_data["TradeAmt"])
                    if response_data.get("TradeAmt", "").isdigit()
                    else None
                ),
                payment_method_name=payment_type_str,
                order_creation_time=response_data.get("TradeDate"),
                payment_info=payment_info_dto,
                raw_response=response_data,
            )
        except GatewayError as e:
            logger.error(
                f"ECPay GatewayError during query payment info for order {input.order_id}: {e}"
            )
            return PaymentInfoQueryOutput(
                success=False,
                message=str(e),
                error_code=str(e.code) if e.code else None,
                raw_response=e.raw_response,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay query payment info for order {input.order_id}"
            )
            return PaymentInfoQueryOutput(
                success=False, message=f"Unexpected query error: {e}"
            )

    def query_credit_card_details(
        self, input: EcpayQueryCreditCardDetailsInput
    ) -> EcpayQueryCreditCardDetailsOutput:
        """Queries ECPay credit card details using QueryTrade/V2 API."""
        logger.info(
            f"Querying ECPay credit details for CreditRefundId: {input.credit_refund_id}"
        )
        try:
            ecpay_data = {
                "CreditRefundId": input.credit_refund_id,
                "CreditAmount": input.credit_amount,
                "CreditCheckCode": input.credit_check_code,
                "PlatformID": input.platform_id,
                "MerchantID": input.merchant_id,
            }
            ecpay_data_cleaned = {k: v for k, v in ecpay_data.items() if v is not None}
            response_data = self.dao.send_query_credit_details_request(
                ecpay_data_cleaned
            )

            rtn_msg = response_data.get("RtnMsg", "")
            rtn_value = response_data.get("RtnValue")

            success = not rtn_msg and isinstance(rtn_value, dict)
            message = rtn_msg if not success else "Credit details query successful."
            error_code = rtn_msg if not success else None

            close_data_list = []
            if (
                success
                and "close_data" in rtn_value
                and isinstance(rtn_value["close_data"], list)
            ):
                for item in rtn_value["close_data"]:
                    if isinstance(item, dict):
                        close_data_list.append(
                            EcpayCreditCloseDataRecord(
                                status=item.get("status", ""),
                                amount=(
                                    int(item["amount"])
                                    if item.get("amount", "").isdigit()
                                    else 0
                                ),
                                sno=item.get("sno", ""),
                                datetime=item.get("datetime", ""),
                            )
                        )

            def safe_int(val_str):
                try:
                    return (
                        int(val_str)
                        if isinstance(val_str, (str, int)) and str(val_str).isdigit()
                        else None
                    )
                except:
                    return None

            return EcpayQueryCreditCardDetailsOutput(
                success=success,
                message=message,
                error_code=error_code,
                gateway_authorization_id=(
                    safe_int(rtn_value.get("TradeID")) if success else None
                ),
                amount=safe_int(rtn_value.get("amount")) if success else None,
                closed_amount=safe_int(rtn_value.get("clsamt")) if success else None,
                authorization_time=rtn_value.get("authtime") if success else None,
                status=rtn_value.get("status") if success else None,
                close_data=close_data_list,
                raw_response=response_data,
            )

        except GatewayError as e:
            logger.error(
                f"ECPay GatewayError during query credit details for CreditRefundId {input.credit_refund_id}: {e}"
            )
            return EcpayQueryCreditCardDetailsOutput(
                success=False,
                message=str(e),
                error_code=str(e.code) if e.code else None,
                raw_response=e.raw_response,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay query credit details for CreditRefundId {input.credit_refund_id}"
            )
            return EcpayQueryCreditCardDetailsOutput(
                success=False, message=f"Unexpected query error: {e}"
            )

    def query_periodic_details(
        self, input: QueryInput
    ) -> EcpayQueryPeriodicDetailsOutput:
        """Queries ECPay credit card periodic payment details."""
        logger.info(f"Querying ECPay periodic details for order_id: {input.order_id}")
        if not input.order_id:
            return EcpayQueryPeriodicDetailsOutput(
                success=False,
                message="ECPay query periodic details requires 'order_id' (MerchantTradeNo).",
            )

        ecpay_data = {"MerchantTradeNo": input.order_id}
        if input.gateway_specific_params.get("PlatformID"):
            ecpay_data["PlatformID"] = input.gateway_specific_params["PlatformID"]

        try:
            response_data = self.dao.send_query_periodic_details_request(ecpay_data)

            rtn_code_str = str(response_data.get("RtnCode", ""))
            success = rtn_code_str == EcpayRtnCode.SUCCESS
            message = (
                response_data.get(
                    "RtnMsg", "Periodic details query response message missing."
                )
                if not success
                else "Periodic details query successful."
            )

            exec_log_list = []
            raw_exec_log = response_data.get("ExecLog", [])
            if isinstance(raw_exec_log, list):
                for item in raw_exec_log:
                    if isinstance(item, dict):

                        def safe_int_log(val):
                            try:
                                return int(val) if str(val).isdigit() else -1
                            except:
                                return -1

                        exec_log_list.append(
                            EcpayPeriodicExecLogRecord(
                                rtn_code=safe_int_log(item.get("RtnCode")),
                                amount=safe_int_log(item.get("amount")),
                                gwsr=safe_int_log(item.get("gwsr")),
                                process_date=item.get("process_date", ""),
                                auth_code=item.get("auth_code", ""),
                                trade_no=item.get("TradeNo", ""),
                            )
                        )
            elif isinstance(raw_exec_log, str):
                logger.warning(
                    f"ExecLog for periodic query {input.order_id} was returned as a string, not parsed list."
                )

            def safe_int(val):
                try:
                    return int(val) if str(val).isdigit() else None
                except:
                    return None

            return EcpayQueryPeriodicDetailsOutput(
                success=success,
                message=message,
                error_code=rtn_code_str if not success else None,
                merchant_id=response_data.get("MerchantID"),
                merchant_trade_no=response_data.get("MerchantTradeNo"),
                first_trade_no=response_data.get("TradeNo"),
                period_type=response_data.get("PeriodType"),
                frequency=safe_int(response_data.get("Frequency")),
                exec_times=safe_int(response_data.get("ExecTimes")),
                period_amount=safe_int(response_data.get("PeriodAmount")),
                first_amount=safe_int(response_data.get("amount")),
                first_gwsr=safe_int(response_data.get("gwsr")),
                first_process_date=response_data.get("process_date"),
                first_auth_code=response_data.get("auth_code"),
                card_last_four=response_data.get("card4no"),
                card_first_six=response_data.get("card6no"),
                total_success_times=safe_int(response_data.get("TotalSuccessTimes")),
                total_success_amount=safe_int(response_data.get("TotalSuccessAmount")),
                exec_status=str(response_data.get("ExecStatus", "")),
                exec_log=exec_log_list,
                raw_response=response_data,
            )

        except GatewayError as e:
            logger.error(
                f"ECPay GatewayError during query periodic details for order {input.order_id}: {e}"
            )
            return EcpayQueryPeriodicDetailsOutput(
                success=False,
                message=str(e),
                error_code=str(e.code) if e.code else None,
                raw_response=e.raw_response,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during ECPay query periodic details for order {input.order_id}"
            )
            return EcpayQueryPeriodicDetailsOutput(
                success=False, message=f"Unexpected query error: {e}"
            )
