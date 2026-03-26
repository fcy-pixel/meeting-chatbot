# 會議紀錄 Chatbot

實時查閱 Google Drive 資料夾內的會議紀錄 PDF，使用 Qwen AI 回答老師問題。

## 設定步驟

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. Google Drive API 設定

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 **Google Drive API**
4. 建立服務帳號 (Service Account)：
   - 前往「IAM 與管理」→「服務帳號」
   - 建立服務帳號，下載 JSON 金鑰檔案
   - 將金鑰檔案儲存為 `service_account.json` 放在本專案目錄
5. 將 Google Drive 資料夾**共享**給服務帳號的 email（在 JSON 中的 `client_email`）

### 3. 設定 .env 或 Streamlit secrets

在專案目錄建立 `.streamlit/secrets.toml`：
```toml
QWEN_API_KEY = "sk-your-qwen-api-key"
GOOGLE_DRIVE_FOLDER_ID = "your-google-drive-folder-id"
```

Google Drive Folder ID 就是資料夾 URL 中的ID：
`https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXX` 中的 `XXXXXXXXXXXXXXXX`

### 4. 啟動應用
```bash
streamlit run app.py
```

## 功能
- 自動從 Google Drive 讀取所有 PDF 會議紀錄
- 使用 Qwen AI 分析內容並回答問題
- 支援中文對話
- 可隨時重新整理文件列表
