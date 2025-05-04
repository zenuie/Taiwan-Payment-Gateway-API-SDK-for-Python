# Payment Gateway SDK - ECPay Flask Demo Examples

## 簡介

這個目錄包含一系列**獨立**的、最小化的 Flask 應用程式，旨在演示如何使用 `payment-gateway-sdk` 來與 **ECPay (綠界)** 支付閘道進行互動。

**重要提示：** 這些範例是為了**測試和學習** SDK 的用法而設計的，它們**不是**一個功能完整的、生產就緒的應用程式。每個檔案專注於演示**一個特定**的 ECPay API 操作。

## 先決條件

在運行這些範例之前，請確保您已滿足以下條件：

1.  **Python:** 已安裝 Python 3.7 或更高版本。
2.  **pip:** Python 的套件安裝程式。
3.  **Payment Gateway SDK:** 您開發的 `payment-gateway-sdk` 套件已安裝在您的 Python 環境中。
    *   如果您在本地開發 SDK，通常可以在 SDK 專案根目錄下執行 `pip install .` 或 `pip install -e .`。
4.  **Flask:** 已安裝 Flask 框架 (`pip install Flask`)。
5.  **ECPay Sandbox (測試環境) 帳號:** 您**必須**擁有一個 ECPay 的**測試環境**商家帳號，以便獲取測試用的 MerchantID, HashKey, 和 HashIV。您可以向 ECPay 申請。

## 設定

每個範例檔案 (`demo_*.py`) 的頂部都有一個 `SDK_CONFIG` 字典。您**必須**在運行前修改此部分：

1.  **ECPay 憑證:**
    *   將 `merchant_id`, `hash_key`, `hash_iv` 的值替換成您**實際的 ECPay Sandbox** 憑證。**請勿**在生產環境中使用 Sandbox 憑證，反之亦然。
    *   範例程式碼使用 `os.environ.get` 嘗試從環境變數讀取，並提供了 Sandbox 的**範例**值作為預設值，但您仍應明確替換它們。
2.  **`is_sandbox`:** 確保此值為 `True`，因為您使用的是 Sandbox 憑證。當您切換到正式環境時，需要將此設為 `False` 並使用正式環境憑證。
3.  **回呼 URL (Callback URLs):**
    *   在支付範例 (`demo_pay_*.py`) 中，`return_url` (以及可選的 `payment_info_url`, `client_redirect_url_for_info`, `period_return_url` 等) 被設置為 `https://your-publicly-accessible-domain.com/...`。
    *   ECPay 的伺服器需要能夠**公開訪問**這些 URL 來發送非同步通知。如果您在本地運行這些範例 (`localhost`)，ECPay **無法**觸達這些 URL。
    *   **本地測試回呼:** 您可以使用 `ngrok` 這類工具創建一個公開通道指向您本地運行的 Flask 伺服器，然後將 `ngrok` 提供的 URL 更新到範例程式碼中對應的回呼 URL 參數。
    *   **注意:** 這些 Demo **不包含**實際處理 ECPay 回呼請求的 Flask 路由 (`/callback/...`)。

## 範例檔案說明

*   `demo_pay_by_credit_onetime.py`: 信用卡一次付清。
*   `demo_pay_by_credit_installment.py`: 信用卡分期付款。
*   `demo_pay_by_credit_periodic.py`: 信用卡定期定額。
*   `demo_pay_by_atm.py`: ATM 虛擬帳號取號。
*   `demo_pay_by_cvs.py`: 超商代碼取號。
*   `demo_pay_by_barcode.py`: 超商條碼取號。
*   `demo_pay_all_options.py`: 顯示 ECPay 所有可用支付方式頁面。
*   `demo_query_transaction_status.py`: 查詢訂單狀態 (QueryTradeInfo)。
*   `demo_query_payment_info.py`: 查詢 ATM/CVS/Barcode 取號結果 (QueryPaymentInfo)。
*   `demo_action_refund.py`: 執行信用卡退款 (DoAction - Refund)。
*   `demo_action_capture.py`: 執行信用卡請款/關帳 (DoAction - Capture)。
*   `demo_action_cancel_auth.py`: 執行信用卡取消授權 (DoAction - Cancel Auth)。
*   `demo_action_abandon.py`: 執行信用卡放棄交易 (DoAction - Abandon)。

*(您可以依照此模式為其他未包含的 API (如 WebATM, ApplePay, BNPL, TWQR, 特定查詢) 添加更多 demo 檔案)*

## 運行範例

1.  **開啟終端機 (Terminal/Command Prompt)。**
2.  **導航到包含這些範例檔案的目錄。**
3.  **設置 ECPay 憑證:** (擇一)
    *   直接編輯每個 `.py` 檔案中的 `SDK_CONFIG` 字典。
    *   或者，設置環境變數 (Linux/macOS: `export ECPAY_MERCHANT_ID='...'`, Windows: `set ECPAY_MERCHANT_ID=...`)。
4.  **運行指定的範例檔案:**
    *   例如，要運行信用卡一次付清範例：`python demo_pay_credit_onetime.py`
    *   每個範例會監聽不同的端口 (從 5001 開始遞增，請查看檔案末尾的 `app.run` 設定)。
5.  **觸發操作:**
    *   **支付範例 (`demo_pay_*.py`):** 在瀏覽器中訪問 `http://localhost:PORT/` (例如 `http://localhost:5001/`)。您應該會看到終端機輸出 "Redirecting..."，並且瀏覽器（理論上）會被重定向到 ECPay 的沙箱頁面。您需要在 ECPay 頁面完成模擬支付操作。
    *   **查詢範例 (`demo_query_*.py`):** **在運行前，您必須編輯程式碼，將佔位符的訂單 ID (`order_id_to_query`) 替換成您先前在 ECPay 沙箱中成功創建的訂單的 `MerchantTradeNo`。** 然後，在瀏覽器中訪問 `http://localhost:PORT/`。結果會以 JSON 格式顯示在瀏覽器和/或終端機日誌中。
    *   **操作範例 (`demo_action_*.py`):** **在運行前，您必須編輯程式碼，將佔位符的 `merchant_trade_no_to_*`, `gateway_trade_no_to_*`, `amount_to_*` 等變數替換成來自 ECPay 沙箱中**符合操作前提條件**的實際交易數據（例如，退款需要已授權或已請款的交易，請款需要僅授權未請款的交易）。** 然後，在瀏覽器中訪問 `http://localhost:PORT/`。結果會以 JSON 格式顯示。

## 重要注意事項

*   **僅限 Sandbox:** 這些範例預設使用 Sandbox 環境和憑證。請勿在生產環境中直接使用。
*   **回呼處理:** 這些範例**不包含**接收和處理 ECPay 非同步回呼通知 (ReturnURL, PaymentInfoURL 等) 的邏輯。在真實應用中，這是**至關重要**的部分，您需要單獨實現回呼路由，驗證 CheckMacValue，並更新您的訂單狀態。對於非即時付款方式 (ATM, CVS, Barcode)，交易狀態依賴於回呼。
*   **範例依賴性:** 查詢和操作範例通常依賴於先前成功執行的支付範例所產生的數據 (訂單 ID, ECPay 交易編號)。您需要手動獲取這些數據（例如從 ECPay 沙箱後台）並更新到查詢/操作範例的程式碼中。
*   **錯誤處理:** 範例中包含基本的錯誤捕捉，但生產級應用需要更完善的錯誤處理、重試機制和日誌記錄。
*   **安全性:** 範例中啟用了 Flask 的 `debug=True` 模式，這在生產環境中**絕對不安全**。回呼 URL 應使用 HTTPS。
*   **非生產就緒:** 重申，這些是**演示**程式碼，不能直接用於生產環境。

## 後續步驟

1.  將 SDK 的調用整合到您實際的 Web 應用程式框架（Flask, Django, FastAPI 等）的視圖或控制器中。
2.  實現完整的訂單處理邏輯（資料庫互動、狀態更新等）。
3.  創建並部署處理 ECPay 回呼通知的端點，確保它們是公開可訪問的，並包含 CheckMacValue 驗證。
4.  根據您的需求添加更詳細的日誌記錄和錯誤處理。
5.  獲取並配置您的 ECPay **正式環境**憑證，並將 `is_sandbox` 設為 `False` 進行上線部署。