# VLM (視覺語言模型) 整合說明

## 概述

本框架已整合 VLM (Vision Language Model) 支援，可用於取代或輔助傳統 OCR 進行 UI 元素識別。VLM 相比傳統 OCR 具有以下優勢：

- **更智能的理解**：能理解 UI 元素的上下文和語義
- **自然語言查詢**：支援如「藍色的確認按鈕」這樣的描述
- **更好的魯棒性**：對字體、顏色、樣式變化有更好的容忍度

## 支援的後端

### 1. Ollama (本地，推薦)

**優點**：免費、無 API 費用、資料不出本機

```bash
# 安裝 Ollama (https://ollama.com)
# Windows: 下載安裝包
# Mac: brew install ollama

# 拉取模型
ollama pull llava
# 或使用更新版本
ollama pull llava:13b
ollama pull bakllava

# 安裝 Python 客戶端
pip install ollama
```

### 2. OpenAI GPT-4V/GPT-4o (雲端)

**優點**：辨識精度高、多語言支援好

```bash
pip install openai

# 設置 API Key
set OPENAI_API_KEY=your_api_key
```

### 3. Anthropic Claude Vision (雲端)

**優點**：安全性高、多輪對話能力強

```bash
pip install anthropic

# 設置 API Key
set ANTHROPIC_API_KEY=your_api_key
```

## 配置

在 `config.py` 中設置 VLM 參數：

```python
class DevConfig(BaseConfig):
    # VLM 設定
    VLM_ENABLED = True  # 是否啟用 VLM
    VLM_BACKEND = "ollama"  # 'ollama', 'openai', 'anthropic'
    VLM_MODEL = "llava"  # 模型名稱
    VLM_PRIORITY = 2  # 優先級 (1=最高, 2=OK Script後, 3=OCR後)
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

vlm = get_vlm_recognizer(backend='ollama', model='llava')
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

1. **速度**：VLM 通常比傳統 OCR 慢（本地約 1-3 秒，雲端約 2-5 秒）
2. **成本**：雲端 API 有使用費用，建議用於重要場景
3. **網路**：雲端 API 需要穩定網路連接
4. **GPU**：本地模型（如 llava）需要 GPU 才能達到較好效能

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
# VLM_BACKEND = "ollama"

# 5. 執行測試
pytest tests/test_runner.py --test_name "啟用免費一個月的錄製授權" -v -s
```
