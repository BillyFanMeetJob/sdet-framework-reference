# VLM (視覺語言模型) 整合說明

## 概述

本框架已整合 VLM (Vision Language Model) 支援，使用 Ollama 本地 VLM 進行 UI 元素識別。VLM 相比傳統 OCR 具有以下優勢：

- **更智能的理解**：能理解 UI 元素的上下文和語義
- **自然語言查詢**：支援如「藍色的確認按鈕」這樣的描述
- **更好的魯棒性**：對字體、顏色、樣式變化有更好的容忍度
- **免費且安全**：本地運行，無 API 費用，資料不出本機

## 安裝與配置

### 1. 安裝 Ollama

**Windows**：
- 訪問 https://ollama.com 下載安裝包
- 執行安裝程序

**Mac**：
```bash
brew install ollama
```

**Linux**：
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. 拉取模型

```bash
# 拉取預設模型 llava
ollama pull llava

# 或使用更新版本
ollama pull llava:13b

# 或使用其他視覺模型
ollama pull bakllava
```

### 3. 安裝 Python 客戶端

```bash
pip install ollama
```

## 配置

在 `config.py` 中設置 VLM 參數：

```python
class DevConfig(BaseConfig):
    # VLM 設定（僅支援 Ollama）
    VLM_ENABLED = True  # 是否啟用 VLM
    VLM_MODEL = "llava"  # Ollama 模型名稱: 'llava' (預設), 'bakllava', 'llava:13b'
    VLM_PRIORITY = 2  # 優先級 (1=最高, 2=OK Script後, 3=OCR後)
```

**環境變數配置**（可選，會覆蓋 config.py 設置）：
```bash
# 設置 VLM 模型
set VLM_MODEL=llava
```

### 優先級說明

| 優先級 | VLM_PRIORITY=1 | VLM_PRIORITY=2 (預設) | VLM_PRIORITY=3 |
|--------|--------------|----------------------|----------------|
| 1 | VLM | OK Script/OpenCV | OK Script/OpenCV |
| 2 | OK Script | VLM | pyautogui |
| 3 | pyautogui | pyautogui | OCR |
| 4 | OCR | OCR | VLM |
| 5 | 座標保底 | 座標保底 | 座標保底 |

## 使用方式

### 在 smart_click 中使用

```python
# 預設會根據配置決定是否使用 VLM
self.smart_click(
    x_ratio=0.5, 
    y_ratio=0.5,
    target_text="確認按鈕"  # VLM 會嘗試找這個元素
)

# 強制使用 VLM
self.smart_click(
    x_ratio=0.5, 
    y_ratio=0.5,
    target_text="藍色的提交按鈕",  # 支援更詳細的描述
    use_vlm=True
)

# 強制禁用 VLM
self.smart_click(
    x_ratio=0.5, 
    y_ratio=0.5,
    target_text="OK",
    use_vlm=False
)
```

### 直接使用 VLM 辨識器

```python
from base.vlm_recognizer import get_vlm_recognizer

# 使用預設模型 llava
vlm = get_vlm_recognizer()

# 或指定模型
vlm = get_vlm_recognizer(model='llava:13b')

# 尋找元素
result = vlm.find_element("設定圖示", region=(0, 0, 800, 600))

if result and result.success:
    print(f"找到元素位置: ({result.x}, {result.y})")
    print(f"信心度: {result.confidence}")
    print(f"耗時: {result.time_ms}ms")
```

## 性能統計

VLM 的辨識統計會記錄在 `logs/recognition_stats.json` 中：

```json
{
  "vlm_hits": 10,
  "vlm_time_total": 15234.5,
  ...
}
```

統計報告會顯示 VLM 的命中率和平均耗時：

```
[Hit Rate]
  OK Script/OpenCV: 45/100 (45.0%)
  VLM (LLM Vision): 25/100 (25.0%)
  OCR:              10/100 (10.0%)
  ...

[Average Recognition Time]
  OK Script/OpenCV: 123.45 ms
  VLM (LLM Vision): 1523.40 ms
  ...
```

## 注意事項

1. **速度**：VLM 通常比傳統 OCR 慢（本地約 1-3 秒，取決於 GPU）
2. **GPU**：本地模型（如 llava）需要 GPU 才能達到較好效能，否則會很慢
3. **Ollama 服務**：確保 Ollama 服務正在運行（通常安裝後會自動啟動）
4. **模型下載**：首次使用時，Ollama 會自動下載模型，可能需要一些時間

## 推薦使用場景

| 場景 | 推薦方法 |
|------|---------|
| 簡單圖片按鈕 | OK Script |
| 固定文字標籤 | OCR |
| 複雜 UI 元素 | VLM |
| 動態內容識別 | VLM |
| 自然語言描述 | VLM |
| 需要高速度 | OK Script > OCR |

## 快速開始

```bash
# 1. 安裝 Ollama
# 訪問 https://ollama.com 下載安裝

# 2. 拉取模型
ollama pull llava

# 3. 安裝 Python 客戶端
pip install ollama

# 4. 在 config.py 中啟用 VLM
# VLM_ENABLED = True
# VLM_MODEL = "llava"

# 5. 執行測試
pytest tests/test_runner.py --test_name "啟用免費一個月的錄製授權" -v -s
```

## 故障排除

### Ollama 連接失敗

如果遇到 "無法連接到 Ollama 服務" 錯誤：

1. 確認 Ollama 服務是否運行：
   ```bash
   ollama list
   ```

2. 如果服務未運行，啟動 Ollama：
   - Windows: 從開始菜單啟動 Ollama
   - Mac/Linux: 運行 `ollama serve`

### 模型未找到

如果遇到 "model not found" 錯誤：

1. 確認模型已下載：
   ```bash
   ollama list
   ```

2. 如果模型不存在，拉取模型：
   ```bash
   ollama pull llava
   ```

### 性能問題

如果 VLM 識別速度很慢：

1. 確認是否有 GPU 支援（推薦使用 GPU）
2. 嘗試使用較小的模型（如 `llava` 而非 `llava:13b`）
3. 考慮降低截圖解析度（已在代碼中自動處理）
