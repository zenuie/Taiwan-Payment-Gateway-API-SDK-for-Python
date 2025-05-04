# Taiwan Payment Gateway API SDK for Python

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- Add other relevant badges here: CI/CD status, code coverage, PyPI version -->

SDK of the Taiwan Payment Gateway API for Python.

## 簡介 (Introduction)

本 SDK 提供了一個統一、模組化、可擴展的 Python 介面，用於整合台灣常見的第三方支付閘道 (Payment Gateway)，例如 ECPay (綠界) 和 TapPay。

主要目標是：

*   **簡化整合:** 將不同支付閘道的 API 差異封裝起來，提供相對一致的操作方式 (特別是交易查詢)。
*   **模組化設計:** 每個支付閘道的實作細節被隔離在獨立的模組中，易於維護和擴展。
*   **類型安全:** 大量使用 `dataclasses` 定義輸入和輸出 DTO (Data Transfer Objects)，減少錯誤。
*   **處理通用流程:** 封裝常見的任務，如 ECPay 的 CheckMacValue 計算。

開發者可以使用此 SDK 來處理支付發起、交易查詢、退款 (ECPay)、請款 (ECPay) 等操作，而無需深入了解每個支付閘道 API 的所有底層細節。

## 主要功能 (Key Features)

*   **統一入口:** `GatewayFactory` 負責創建和配置特定支付閘道的 Adapter 實例。
*   **Adapter 模式:** 每個支付閘道 (`ECPayAdapter`, `TappayAdapter`) 負責適配其獨特的 API。
*   **模組化結構:** 在 `gateways/` 目錄下輕鬆添加新的支付閘道支援。
*   **標準化查詢:** 提供通用的 `query_transaction` 方法及 `QueryOutput`, `TransactionRecord` DTO。
*   **特定操作:** 透過 Adapter 的特定方法 (如 `pay_with_atm`, `refund`) 和特定 DTO 處理各閘道的獨特功能。
*   **內建安全輔助:** 包含如 ECPay CheckMacValue 的計算與驗證。
*   **清晰的 DTO:** 使用 `dataclasses` 定義通用 (`schema/dto`) 和特定 (`gateways/<gateway>/dto`) 的資料結構。

## 需求 (Requirements)

*   **Python:** 3.8 或更高版本
*   **pip:** Python 套件安裝程式
*   **外部函式庫:**
    *   `requests`: 用於進行 HTTP API 請求。 (SDK 會自動安裝)
*   **支付閘道帳號:** 您需要擁有您打算整合的支付閘道 (例如 ECPay, TapPay) 的有效商家帳號 (包括測試環境帳號和憑證)。

## 安裝 (Installation)

**選項 1: 使用 pip (推薦 - 當套件發布到 PyPI 後)**

```bash
pip install payment-gateway-sdk
```

*(注意: 目前您可能需要使用選項 2 或 3，直到套件正式發布)*

**選項 2: 從本地原始碼安裝 (用於開發)**

在 SDK 專案的根目錄下執行：

```bash
pip install .
```

或者，如果您希望在編輯原始碼時立即生效（可編輯模式）：

```bash
pip install -e .
```

**選項 3: 直接從 Git Repository 安裝 (如果託管在 GitHub 等平台)**

```bash
pip install git+https://github.com/your-username/your-repo-name.git # 將 URL 替換成您的 repo
```

## 快速開始 (Quick Start)

以下是一個使用 ECPay ATM 付款的簡單範例：

```python
import os
import logging
from datetime import datetime

# 1. 從 SDK 導入必要元件
from payment_gateway_sdk import GatewayFactory
from payment_gateway_sdk.gateways.ecpay import EcpayAdapter, EcpayAtmPaymentInput
from payment_gateway_sdk import PaymentStatus, ValidationError, GatewayError

logging.basicConfig(level=logging.INFO)

# 2. SDK 配置 (務必替換成您的測試憑證)
SDK_CONFIG = {
    'sdk_settings': {'default_timeout': 30},
    'ecpay': {
        'merchant_id': os.environ.get('ECPAY_MERCHANT_ID', '3002607'), # 測試 ID
        'hash_key': os.environ.get('ECPAY_HASH_KEY', 'pwFHCqoQZGmho4w6'),    # 測試 Key
        'hash_iv': os.environ.get('ECPAY_HASH_IV', 'EkRm7iFT261dpevs'),      # 測試 IV
        'is_sandbox': True, # 使用測試環境
    },
    # 可以加入其他支付閘道的配置...
    # 'tappay': { ... }
}

# 3. 初始化 GatewayFactory
try:
    factory = GatewayFactory(config=SDK_CONFIG)
    logging.info("Factory initialized.")
except Exception as e:
    logging.error(f"Factory init failed: {e}")
    exit()

# 4. 獲取 ECPay Adapter
try:
    adapter: EcpayAdapter = factory.get_adapter("ecpay")

    # 5. 準備支付輸入 DTO
    order_id = f"SDKATM{datetime.now().strftime('%Y%m%d%H%M%S')}"
    atm_input = EcpayAtmPaymentInput(
        order_id=order_id,
        amount=555,
        currency="TWD",
        details="SDK Quick Start ATM Test",
        return_url="https://your-domain.com/ecpay_callback", # *** 您的回呼 URL ***
        expire_date=3 # 3天後過期
    )

    # 6. 調用支付方法
    payment_output = adapter.pay_with_atm(atm_input)

    # 7. 處理結果 (通常是重定向)
    if payment_output.success and payment_output.redirect_url:
        logging.info(f"Payment initiation successful for order {order_id}!")
        logging.info("Redirect user to ECPay using the following details:")
        logging.info(f"  URL: {payment_output.redirect_url}")
        logging.info(f"  Method: {payment_output.redirect_method.name}")
        logging.info(f"  Form Data: {payment_output.redirect_form_data}")
        # 在 Web 應用中，您會生成一個自動提交的 HTML 表單來完成重定向
    else:
        logging.error(f"Payment initiation failed for order {order_id}: {payment_output.message} (Code: {payment_output.error_code})")

except (ValidationError, GatewayError) as e:
    logging.error(f"SDK Error: {e}")
except Exception as e:
    logging.exception("An unexpected error occurred.")

```

## 支援的支付閘道 (Supported Gateways)

目前內建支援：

*   **ECPay (綠界科技)**
    *   信用卡 (一次付清, 分期, 定期定額)
    *   ATM 虛擬帳號
    *   超商代碼 (CVS)
    *   超商條碼 (Barcode)
    *   網路 ATM (WebATM)
    *   Apple Pay
    *   TWQR (需申請)
    *   無卡分期 (BNPL - 裕富) (需申請)
    *   綠界 PAY (透過 `DeviceSource`)
    *   交易查詢 (通用)
    *   取號結果查詢 (ATM/CVS/Barcode)
    *   信用卡請款 (Capture) / 退款 (Refund) / 取消授權 / 放棄交易
    *   信用卡定期定額查詢
*   **TapPay**
    *   信用卡 (Pay by Prime)
    *   信用卡 (Pay by Token)
    *   交易查詢
    *   退款

## 架構概觀 (Architecture Overview)

SDK 遵循模組化設計，主要包含三個核心部分：

1.  **`core/`**: 包含與特定閘道無關的基礎元件，例如自定義例外 (`core.exceptions`) 和安全性抽象 (`core.security`)。
2.  **`schema/`**: 定義 SDK 的**通用**公開介面和資料結構。
    *   `GatewayFactory`: 創建 Adapter 的工廠。
    *   `adapter.py`: 定義抽象基底類別 (`PaymentAdapter`, `TransactionAdapter`)，目前主要規範 `query_transaction`。
    *   `dto/`: 包含**通用**的輸入 (`BasePaymentInput`, `QueryInput`, `ActionInput`)、輸出 (`PaymentOutput`, `QueryOutput`, `ActionOutput`) 和資訊結構 (`TransactionRecord`, `AtmPaymentInfo` 等)。
3.  **`gateways/`**: 每個子目錄代表一個支付閘道的完整實現。
    *   `constants.py`: (例如 ECPay) 定義特定常數。
    *   `dao.py`: 處理與該閘道 API 的直接 HTTP 通訊。
    *   `adapter.py`: 實現 `schema` 中的通用介面，並提供該閘道**所有特定**的支付和交易操作方法。
    *   `dto.py`: 定義該閘道**所有特定**操作的輸入和輸出 DTO。
    *   `security.py`, `utils.py`: (例如 ECPay) 包含特定的安全邏輯或工具函式。

使用者主要透過 `GatewayFactory` 獲取特定閘道的 `Adapter` 實例，然後調用 Adapter 上的方法（通用 `query_transaction` 或特定閘道的方法如 `pay_with_atm`, `refund`）來執行操作，並使用對應的 DTO 傳遞參數和接收結果。

## 配置 (Configuration)

SDK 的配置是透過一個字典傳遞給 `GatewayFactory` 的。基本結構如下：

```python
SDK_CONFIG = {
    # --- SDK 全域設定 (可選) ---
    'sdk_settings': {
        'default_timeout': 30, # API 請求預設超時時間 (秒)
    },

    # --- ECPay 配置 ---
    'ecpay': {
        'merchant_id': 'YOUR_ECPAY_MERCHANT_ID',
        'hash_key': 'YOUR_ECPAY_HASH_KEY',
        'hash_iv': 'YOUR_ECPAY_HASH_IV',
        'is_sandbox': True, # True 使用測試環境, False 使用正式環境
        # 'base_url' 會由 Factory 根據 is_sandbox 自動設定
    },

    # --- TapPay 配置 ---
    'tappay': {
        'partner_key': 'YOUR_TAPPAY_PARTNER_KEY',
        'merchant_id': 'YOUR_TAPPAY_MERCHANT_ID', # TapPay 的 Merchant ID (可選，如果 API 需要)
        'is_sandbox': True,
        # 'base_url' 會由 Factory 根據 is_sandbox 自動設定
    },

    # --- 其他支付閘道配置 ---
    # 'other_gateway': { ... }
}
```

*   **強烈建議**使用環境變數、`.env` 檔案或安全的配置管理系統來儲存敏感的憑證 (MerchantID, Key, IV, Partner Key)，而不是直接寫在程式碼中。
*   `is_sandbox` 參數決定了 SDK 是否使用支付閘道的測試環境 URL。Factory 會根據此設定自動填入 `base_url`。

## 錯誤處理 (Error Handling)

SDK 定義了自定義的例外類別，位於 `payment_gateway_sdk.core.exceptions`:

*   `ValidationError`: 輸入參數驗證失敗。
*   `AuthenticationError`: 憑證錯誤或身份驗證失敗。
*   `GatewayError`: 與支付閘道 API 通訊時發生錯誤（網路問題、超時、閘道返回錯誤碼等）。通常包含 `code` (閘道錯誤碼) 和 `raw_response` 屬性。
*   `NotImplementedError`: 嘗試調用尚未實現的功能。
*   `PaymentGatewayBaseError`: 所有 SDK 自定義例外的基底類別。

建議在調用 SDK 方法時使用 `try...except` 捕捉這些例外，以便進行適當的處理和日誌記錄。

## 範例 (Examples / Demos)

專案中包含一系列獨立的 Flask Demo 範例檔案 (例如 `demo_pay_by_credit_onetime.py`, `demo_query_transaction_status.py` 等)。請參閱這些檔案以了解如何調用各種 API 操作。

**運行 Demo 前請務必閱讀 Demo 目錄下的 `README.md` 文件**，了解如何設定憑證、前提條件以及如何運行每個範例。

## 貢獻 (Contributing)

歡迎對本專案做出貢獻！如果您發現任何問題或有改進建議，請隨時提出 Issue 或提交 Pull Request。
(您可以加入更詳細的貢獻指南連結)

## 授權 (License)

本專案採用 MIT 授權。詳情請參閱 [LICENSE](LICENSE) 文件 (如果有的話)。

```

現在您可以將上面這個程式碼區塊內的**所有內容**（從 `# Taiwan Payment Gateway API SDK for Python` 開始，一直到結尾的 `(如果有的話)。`）直接複製，並貼到您的 `README.md` 檔案中了。