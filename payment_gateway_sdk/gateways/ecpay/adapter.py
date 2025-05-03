# payment_gateway_sdk/gateways/ecpay/adapter.py
# (Content updated to use specific methods and DTOs)
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from .dao import EcpayDAO
# Import ECPay specific DTOs and DAO
from .dto import (
    EcpayCreditPaymentInput, EcpayAtmPaymentInput, EcpayCvsPaymentInput,
    EcpayBarcodePaymentInput, EcpayWebAtmPaymentInput, BasePaymentInput  # Import BaseInput too
)
from ...core.exceptions import ValidationError, GatewayError, AuthenticationError
from ...schema.adapter import PaymentAdapter, TransactionAdapter  # Base classes
from ...schema.dto.payment import (
    PaymentOutput, PaymentStatus, RedirectMethod, PaymentMethod  # Specific output info DTOs
)
from ...schema.dto.transaction import RefundInput, RefundOutput, QueryInput, QueryOutput, TransactionRecord

logger = logging.getLogger(__name__)

class EcpayAdapter(PaymentAdapter, TransactionAdapter): # Implements both marker and ABC
    """ECPay specific implementation with distinct methods per payment type."""

    def __init__(self, dao: EcpayDAO):
        self.dao = dao

    def _prepare_common_params(self, input_dto: BasePaymentInput) -> Dict[str, Any]:
        """Prepares parameters common to all ECPay AIO checkouts."""
        # Ensure ItemName is handled correctly (replace newline, check length)
        item_name_str = input_dto.details.replace('\n', '#').replace('\r', '')
        item_name_bytes = item_name_str.encode('utf-8')
        if len(item_name_bytes) > 400:
            logger.warning("ItemName exceeds 400 bytes, truncating.")
            try: item_name_str = item_name_bytes[:400].decode('utf-8', 'ignore')
            except Exception: item_name_str = "Truncated Item Name"

        params = {
            "MerchantTradeNo": input_dto.order_id,
            "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "PaymentType": "aio",
            "TotalAmount": input_dto.amount,
            "TradeDesc": input_dto.details,
            "ItemName": item_name_str,
            "ReturnURL": input_dto.return_url, # Mandatory
            "EncryptType": 1,
        }
        if input_dto.client_redirect_url: params['OrderResultURL'] = input_dto.client_redirect_url
        if not params["ReturnURL"]: raise ValidationError("ECPay requires ReturnURL.")
        return {k: v for k, v in params.items() if v is not None}

    def _build_and_return_output(self, ecpay_params: Dict[str, Any], order_id: str) -> PaymentOutput:
        """Helper to build form data and create PaymentOutput."""
        try:
            # Add common optional fields ONLY if they exist in the specific input DTO passed implicitly
            common_opts = ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info',
                           'language', 'store_id', 'platform_id', 'custom_field1',
                           'custom_field2', 'custom_field3', 'custom_field4', 'IgnorePayment']
            for key in common_opts:
                 # The actual value comes from the *specific* input DTO (e.g., EcpayCreditPaymentInput)
                 # which was used to build the initial ecpay_params dict before calling this helper.
                 # We just ensure it's included if present.
                 if key in ecpay_params and ecpay_params[key] is not None:
                     pass # Already included
                 elif key in ecpay_params: # Remove if None explicitly
                     del ecpay_params[key]


            # Remove None values before calculating MAC
            final_params = {k: v for k, v in ecpay_params.items() if v is not None}

            form_data = self.dao.build_checkout_form_data(final_params)
            checkout_url = self.dao.base_url + "/Cashier/AioCheckOut/V5"
            logger.info(f"ECPay form data generated for order {order_id}")
            return PaymentOutput(
                success=True, status=PaymentStatus.PENDING,
                message="Redirect user to ECPay checkout page.",
                redirect_url=checkout_url, redirect_method=RedirectMethod.POST,
                redirect_form_data=form_data, raw_response=form_data
            )
        except (ValidationError, GatewayError, AuthenticationError) as e:
             logger.error(f"Failed preparing ECPay payment for order {order_id}: {e}")
             return PaymentOutput(success=False, status=PaymentStatus.ERROR, message=str(e), error_code=str(e.code) if hasattr(e, 'code') else None)
        except Exception as e:
            logger.exception(f"Unexpected error preparing ECPay payment for order {order_id}")
            return PaymentOutput(success=False, status=PaymentStatus.ERROR, message="An unexpected internal error occurred.")

    # --- Specific Payment Methods ---
    def pay_with_credit(self, input: EcpayCreditPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay Credit payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "Credit"
        # Add specific Credit fields
        if input.credit_installment: ecpay_params["CreditInstallment"] = input.credit_installment
        if input.installment_amount: ecpay_params["InstallmentAmount"] = input.installment_amount
        if input.redeem is not None: ecpay_params["Redeem"] = "Y" if input.redeem else "N"
        if input.union_pay is not None: ecpay_params["UnionPay"] = input.union_pay
        if input.binding_card is not None: ecpay_params["BindingCard"] = input.binding_card
        if input.merchant_member_id: ecpay_params["MerchantMemberID"] = input.merchant_member_id
        if input.period_amount: ecpay_params["PeriodAmount"] = input.period_amount
        if input.period_type: ecpay_params["PeriodType"] = input.period_type
        if input.frequency: ecpay_params["Frequency"] = input.frequency
        if input.exec_times: ecpay_params["ExecTimes"] = input.exec_times
        if input.period_return_url: ecpay_params["PeriodReturnURL"] = input.period_return_url
        # Add common optional fields from input object
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
             if getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        # Validation
        if input.credit_installment and input.period_amount: raise ValidationError("...")
        if input.credit_installment and input.redeem: raise ValidationError("...")
        if input.binding_card == 1 and not input.merchant_member_id: raise ValidationError("...")
        periodic_fields = [input.period_amount, input.period_type, input.frequency, input.exec_times]
        if any(f is not None for f in periodic_fields) and not all(f is not None for f in periodic_fields): raise ValidationError("...")

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_with_atm(self, input: EcpayAtmPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay ATM payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "ATM"
        ecpay_params["ExpireDate"] = input.expire_date
        if input.payment_info_url: ecpay_params["PaymentInfoURL"] = input.payment_info_url
        if input.client_redirect_url_for_info: ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
        # Add common optional fields from input object
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
             if getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_with_cvs(self, input: EcpayCvsPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay CVS payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "CVS"
        if input.store_expire_date is not None: ecpay_params["StoreExpireDate"] = input.store_expire_date
        if input.payment_info_url: ecpay_params["PaymentInfoURL"] = input.payment_info_url
        if input.client_redirect_url_for_info: ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
        if input.desc_1: ecpay_params["Desc_1"] = input.desc_1; # ... add Desc 2, 3, 4
        if input.desc_2: ecpay_params["Desc_2"] = input.desc_2
        if input.desc_3: ecpay_params["Desc_3"] = input.desc_3
        if input.desc_4: ecpay_params["Desc_4"] = input.desc_4
        # Add common optional fields
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
             if getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_with_barcode(self, input: EcpayBarcodePaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay Barcode payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "BARCODE"
        if input.store_expire_date is not None: ecpay_params["StoreExpireDate"] = input.store_expire_date
        if input.payment_info_url: ecpay_params["PaymentInfoURL"] = input.payment_info_url
        if input.client_redirect_url_for_info: ecpay_params["ClientRedirectURL"] = input.client_redirect_url_for_info
        # Add common optional fields
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
             if getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_with_webatm(self, input: EcpayWebAtmPaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay WebATM payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "WebATM"
        # Add common optional fields
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
             if getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_with_applepay(self, input: BasePaymentInput) -> PaymentOutput:
        logger.info(f"Initiating ECPay ApplePay payment for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "ApplePay"
        # Add common optional fields
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
            if hasattr(input, key) and getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    def pay_all_options(self, input: BasePaymentInput, ignore_methods: Optional[List[PaymentMethod]] = None) -> PaymentOutput:
        """Handles the 'ALL' payment type, showing ECPay's selection page."""
        logger.info(f"Initiating ECPay ALL payment methods for order {input.order_id}")
        ecpay_params = self._prepare_common_params(input)
        ecpay_params["ChoosePayment"] = "ALL"
        if ignore_methods:
            ignore_strings = []
            for method in ignore_methods:
                try:
                    # Map back to ECPay strings, skipping UNKNOWN/ALL
                    mapping = { PaymentMethod.CREDIT: "Credit", PaymentMethod.ATM: "ATM", PaymentMethod.CVS: "CVS", PaymentMethod.BARCODE: "BARCODE", PaymentMethod.WEBATM: "WebATM", PaymentMethod.APPLEPAY: "ApplePay"} # etc.
                    if method in mapping:
                        ignore_strings.append(mapping[method])
                except KeyError:
                    logger.warning(f"Cannot map SDK method {method.name} to ECPay ignore string.")
            if ignore_strings:
                ecpay_params['IgnorePayment'] = "#".join(ignore_strings)

        # Add common optional fields
        for key in ['client_back_url', 'item_url', 'remark', 'need_extra_paid_info', 'language', 'store_id', 'platform_id', 'custom_field1', 'custom_field2', 'custom_field3', 'custom_field4']:
            if hasattr(input, key) and getattr(input, key, None) is not None: ecpay_params[key] = getattr(input, key)

        return self._build_and_return_output(ecpay_params, input.order_id)

    # --- Transaction Methods ---
    def refund(self, input: RefundInput) -> RefundOutput:
        # (Implementation unchanged from previous version, using DAO's send_action_request)
        # Placeholder - requires ECPay DoAction API documentation
        logger.warning("ECPay Refund (DoAction) requires API docs not fully provided.")
        if input.amount is None: raise ValidationError("'amount' required for ECPay refund.")
        if not input.gateway_trade_no: raise ValidationError("'gateway_trade_no' (ECPay TradeNo) required.")
        if 'MerchantTradeNo' not in input.gateway_specific_params: raise ValidationError("'MerchantTradeNo' required in gateway_specific_params.")
        ecpay_data = {"MerchantTradeNo": input.gateway_specific_params['MerchantTradeNo'], "TradeNo": input.gateway_trade_no, "Action": "R", "TotalAmount": input.amount, "PlatformID": input.gateway_specific_params.get('PlatformID')}
        try:
            response_data = self.dao.send_action_request({k:v for k,v in ecpay_data.items() if v is not None})
            success = response_data.get('RtnCode') == '1'; status = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED
            return RefundOutput(success=success, status=status, message=response_data.get('RtnMsg'), error_code=response_data.get('RtnCode') if not success else None, raw_response=response_data)
        except (ValidationError, GatewayError, AuthenticationError) as e: return RefundOutput(success=False, status=PaymentStatus.FAILED, message=str(e), error_code=str(e.code) if hasattr(e, 'code') else None)
        except Exception as e: logger.exception(...); return RefundOutput(success=False, status=PaymentStatus.ERROR, message="Unexpected refund error.")

    def _map_ecpay_status(self, status: Optional[str], p_type: Optional[str]) -> PaymentStatus: # Unchanged
         if status == '1': return PaymentStatus.SUCCESS
         if status == '0' and p_type and p_type.startswith(('ATM', 'CVS', 'BARCODE')): return PaymentStatus.PENDING
         if status == '0': return PaymentStatus.FAILED
         return PaymentStatus.UNKNOWN

    def query_transaction(self, input: QueryInput) -> QueryOutput:
        # (Implementation unchanged from previous version, using DAO's send_query_order_request)
        # Placeholder - requires ECPay QueryTradeInfo API documentation
        logger.warning("ECPay Query (QueryTradeInfo) uses API docs not fully provided.")
        if not input.order_id: raise ValidationError("ECPay query requires 'order_id' (MerchantTradeNo).")
        ecpay_data = {"MerchantTradeNo": input.order_id, "PlatformID": input.gateway_specific_params.get('PlatformID')}
        try:
            response_data = self.dao.send_query_order_request({k:v for k,v in ecpay_data.items() if v is not None})
            success = response_data.get('RtnCode') == '1'; message = response_data.get('RtnMsg'); transactions = []
            if success:
                sdk_status = self._map_ecpay_status(response_data.get('TradeStatus'), response_data.get('PaymentType'))
                tx = TransactionRecord( gateway_trade_no=response_data.get('TradeNo',''), order_id=response_data.get('MerchantTradeNo'), status=sdk_status, amount=int(response_data.get('TradeAmt',0)), currency='TWD', payment_type=response_data.get('PaymentType'), transaction_time=response_data.get('TradeDate'), card_last_four=response_data.get('card4no'), auth_code=response_data.get('auth_code'), raw_data=response_data); transactions.append(tx)
            return QueryOutput(success=success, transactions=transactions, message=message, error_code=response_data.get('RtnCode') if not success else None, raw_response=response_data)
        except (ValidationError, GatewayError, AuthenticationError) as e: return QueryOutput(success=False, message=str(e), error_code=str(e.code) if hasattr(e, 'code') else None)
        except Exception as e: logger.exception(...); return QueryOutput(success=False, message=f"Unexpected query error: {e}")