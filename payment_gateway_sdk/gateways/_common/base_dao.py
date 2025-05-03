# payment_gateway_sdk/gateways/_common/base_dao.py (Optional)
from abc import ABC
from typing import Dict, Any


class BaseDAO(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url")
        self.timeout = int(config.get("timeout", 30))
        if not self.base_url:
            raise ValueError(
                f"Base URL not found in config for {self.__class__.__name__}"
            )
