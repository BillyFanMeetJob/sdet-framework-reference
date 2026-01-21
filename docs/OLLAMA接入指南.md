# Ollama 接入指南

## 📋 前置條件

1. ✅ Ollama 已下載並安裝
2. ✅ Ollama 服務正在運行

---

## 🔧 接入步驟

### 步驟 1：確保 Ollama 服務正在運行

#### Windows
1. 啟動 Ollama 應用程式（通常會自動運行）
2. 或者打開命令提示符（CMD）或 PowerShell，運行：
   ```powershell
   # 查看 Ollama 服務狀態（如果不在 PATH 中，需要找到 Ollama 安裝目錄）
   ollama serve
   ```

#### 驗證服務是否運行
打開瀏覽器訪問：`http://localhost:11434`
- 如果看到 Ollama 的歡迎頁面，表示服務正在運行 ✅
- 如果無法訪問，請啟動 Ollama 服務

---

### 步驟 2：下載 llava 模型

Ollama 服務運行後，下載 `llava` 模型（用於視覺辨識）：

```powershell
ollama pull llava
```

或者使用其他視覺模型：
```powershell
# 更大的模型，更準確但更慢
ollama pull bakllava

# 較小的模型，更快但可能不那麼準確
ollama pull llava:7b
```

**下載時間**：根據網路速度，可能需要 10-30 分鐘（llava 約 4-5 GB）

---

### 步驟 3：驗證配置

檢查 `config.py` 中的配置：

```python
# VLM (視覺語言模型) 設定
VLM_ENABLED = True  # 是否啟用 VLM 辨識
VLM_BACKEND = "ollama"  # 後端: 'ollama' (本地), 'openai', 'anthropic'
VLM_MODEL = "llava"  # 模型名稱: 'llava', 'bakllava', 'gpt-4o', 'claude-3-5-sonnet-20241022'
VLM_PRIORITY = 2  # VLM 在辨識優先級中的位置 (1=最高, 2=OK Script後, 3=OCR後)
```

**配置說明**：
- `VLM_ENABLED = True`：啟用 VLM 辨識 ✅
- `VLM_BACKEND = "ollama"`：使用本地 Ollama ✅
- `VLM_MODEL = "llava"`：使用 llava 模型（確保已下載）✅
- `VLM_PRIORITY = 2`：在 OK Script 之後使用 VLM

---

### 步驟 4：安裝 Python ollama 套件

如果尚未安裝：

```powershell
pip install ollama
```

---

### 步驟 5：測試連接

運行測試腳本驗證 Ollama 是否正常工作：

```powershell
python -c "from base.vlm_recognizer import get_vlm_recognizer; r = get_vlm_recognizer(); print('VLM 狀態:', '正常' if r else '未初始化')"
```

或者在測試執行時查看日誌：
- 如果看到 `>>> Ollama ~: Failed to connect to Ollama`：表示服務未運行或無法連接
- 如果看到 `>>> ✅ VLM 初始化成功: ollama/llava`：表示連接成功 ✅

---

## 📊 使用方式

VLM 會自動在以下情況下使用：

1. **圖片辨識失敗時**：如果 OK Script 和 pyautogui 都無法找到圖片，會使用 VLM
2. **文字查詢時**：使用 `target_text` 參數時，VLM 會嘗試理解自然語言描述

### 範例

```python
# 使用 VLM 查找「站點管理」按鈕
self.smart_click(
    x_ratio=0.15,
    y_ratio=0.16,
    target_text="站點管理",  # VLM 會理解這個文字並找到對應的按鈕
    image_path="desktop_settings/system_admin_menu.png"  # 如果圖片辨識失敗，會使用 VLM
)
```

---

## 🔍 故障排除

### 問題 1：`Ollama ~: Failed to connect to Ollama`

**原因**：
- Ollama 服務未運行
- Ollama 未安裝
- 防火牆阻擋連接

**解決方案**：
1. 確認 Ollama 應用程式正在運行
2. 訪問 `http://localhost:11434` 驗證服務
3. 檢查 Windows 防火牆設定

---

### 問題 2：`Model 'llava' not found`

**原因**：llava 模型尚未下載

**解決方案**：
```powershell
ollama pull llava
```

---

### 問題 3：VLM 辨識速度很慢

**原因**：
- llava 模型較大，首次運行較慢
- 硬體性能不足（建議使用 GPU）

**解決方案**：
1. 使用更小的模型：`ollama pull llava:7b`
2. 或者調整優先級，讓 VLM 只在必要時使用

---

### 問題 4：VLM 命中率為 0%

**原因**：
- 模型未正確載入
- 提示詞解析失敗

**解決方案**：
1. 檢查日誌中的 VLM 錯誤訊息
2. 驗證模型是否已下載：`ollama list`
3. 嘗試手動測試：`ollama run llava "描述這個圖片"`（需要先準備圖片）

---

## 📈 性能優化

1. **優先使用圖片辨識**：VLM 比圖片匹配慢，只在必要時使用
2. **調整優先級**：如果需要更快的速度，設置 `VLM_PRIORITY = 3`（在 OCR 之後）
3. **使用較小模型**：`llava:7b` 比完整 `llava` 更快

---

## 🎯 總結

接入 Ollama 只需要三個步驟：

1. ✅ 確保 Ollama 服務運行
2. ✅ 下載 llava 模型：`ollama pull llava`
3. ✅ 驗證配置：`config.py` 中 `VLM_ENABLED = True`

完成後，VLM 會自動在辨識流程中使用！
