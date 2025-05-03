# payment_gateway_sdk/schema/gateway.py
# (Content mostly unchanged, factory returns specific Adapters now)
from typing import Dict, Any, Optional, Type
import importlib

# Import Adapter interfaces (TransactionAdapter is still relevant)
from .adapter import (
    TransactionAdapter,
    PaymentAdapter,
)  # Import PaymentAdapter marker too
from ..core.exceptions import PaymentGatewayBaseError, NotImplementedError

# Assume SecurityHelper ABC is defined in core.security
from ..core.security import SecurityHelper

DaoType = Any
SecurityHelperType = Any
AdapterType = Any  # Generic type for adapters


class GatewayFactory:
    def __init__(self, config: Dict[str, Dict[str, Any]]):
        if not isinstance(config, dict):
            raise TypeError("Config must be a dictionary.")
        self.config = config
        self._dao_cache: Dict[str, DaoType] = {}
        self._security_helper_cache: Dict[str, Optional[SecurityHelperType]] = {}
        # Cache adapters by gateway name AND type (e.g., 'tappay_adapter', 'ecpay_adapter')
        self._adapter_cache: Dict[str, AdapterType] = {}

    def _get_gateway_specific_config(self, gateway_name: str) -> dict:
        # ... (Implementation to get config and set base_url as before) ...
        gw_config = self.config.get(gateway_name)
        if not gw_config:
            raise ValueError(f"Config for gateway '{gateway_name}' not found.")
        config_copy = gw_config.copy()
        is_sandbox = config_copy.get("is_sandbox", True)
        env = "sandbox" if is_sandbox else "production"
        url_map = {
            "tappay": {
                "sandbox_url": "https://sandbox.tappaysdk.com/tpc",
                "production_url": "https://prod.tappaysdk.com/tpc",
            },
            "ecpay": {
                "sandbox_url": "https://payment-stage.ecpay.com.tw",
                "production_url": "https://payment.ecpay.com.tw",
            },
        }
        url_key = f"{env}_url"
        if gateway_name not in url_map or url_key not in url_map[gateway_name]:
            raise ValueError(f"'{url_key}' not defined for '{gateway_name}'.")
        config_copy["base_url"] = url_map[gateway_name][url_key]
        if "timeout" not in config_copy:
            config_copy["timeout"] = self.config.get("sdk_settings", {}).get(
                "default_timeout", 30
            )
        return config_copy

    def _load_class(self, module_path: str, class_name: str) -> Type:
        # ... (Implementation as before) ...
        try:
            fmp = f"{__package__.split('.')[0]}.{module_path.replace('/', '.')}"
            mod = importlib.import_module(fmp)
            return getattr(mod, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(
                f"Could not load class '{class_name}' from module '{fmp}': {e}"
            )

    def _get_security_helper(self, gateway_name: str) -> Optional[SecurityHelperType]:
        # ... (Implementation as before, loading from gateways.<gw>.security) ...
        if gateway_name not in self._security_helper_cache:
            helper = None
            if gateway_name == "ecpay":
                cfg = self._get_gateway_specific_config(gateway_name)
                hc = self._load_class(
                    f"gateways.{gateway_name}.security", "EcpaySecurityHelper"
                )
                helper = hc(
                    hash_key=cfg.get("hash_key", ""), hash_iv=cfg.get("hash_iv", "")
                )
            # Add other gateways needing security helpers here
            self._security_helper_cache[gateway_name] = helper
        return self._security_helper_cache[gateway_name]

    def _get_dao(self, gateway_name: str) -> DaoType:
        # ... (Implementation as before, loading from gateways.<gw>.dao) ...
        if gateway_name not in self._dao_cache:
            cfg = self._get_gateway_specific_config(gateway_name)
            dcn = f"{gateway_name.capitalize()}DAO"
            dmp = f"gateways.{gateway_name}.dao"
            dc = self._load_class(dmp, dcn)
            dao: DaoType
            if gateway_name == "ecpay":
                sh = self._get_security_helper("ecpay")
                dao = dc(config=cfg, security_helper=sh)
            else:
                dao = dc(config=cfg)
            self._dao_cache[gateway_name] = dao
        return self._dao_cache[gateway_name]

    def get_adapter(self, gateway_name: str) -> AdapterType:
        """
        Gets the specific adapter instance for the gateway.
        The returned adapter will have gateway-specific payment methods.
        """
        if gateway_name not in self._adapter_cache:
            dao = self._get_dao(gateway_name)
            # Load the concrete adapter class (e.g., TappayAdapter, EcpayAdapter)
            adapter_class_name = f"{gateway_name.capitalize()}Adapter"
            adapter_module_path = f"gateways.{gateway_name}.adapter"
            adapter_class = self._load_class(adapter_module_path, adapter_class_name)

            adapter_instance = adapter_class(dao=dao)  # Inject DAO
            self._adapter_cache[gateway_name] = (
                adapter_instance  # Cache by gateway name
            )

        return self._adapter_cache[gateway_name]

    def get_transaction_adapter(self, gateway_name: str) -> TransactionAdapter:
        """
        Gets the adapter instance, specifically type-hinted for transaction operations.
        Relies on the concrete adapter implementing TransactionAdapter methods.
        """
        adapter_instance = self.get_adapter(gateway_name)
        if not isinstance(adapter_instance, TransactionAdapter):
            raise TypeError(
                f"Adapter for '{gateway_name}' does not implement TransactionAdapter."
            )
        return adapter_instance

    def get_callback_handler(self, gateway_name: str) -> Any:
        # ... (Implementation as before, returning DAO) ...
        try:
            return self._get_dao(gateway_name)
        except (ImportError, ValueError, TypeError) as e:
            raise NotImplementedError(
                f"Could not get Callback Handler for '{gateway_name}': {e}"
            )
