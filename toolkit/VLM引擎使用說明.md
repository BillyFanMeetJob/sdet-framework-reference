# 🤖 UnifiedVLM 引擎使用說明

## 概述

`UnifiedVLM` 是一個統一的視覺語言模型接口，整合了 **Ollama (主)** 與 **Gemini (備援)** 的雙重策略，提供智能元素識別與座標驗證功能。

---

## 核心特性

### 1. 雙重備援策略 (DIP)
- **主策略**: Ollama (Llama 3.2 Vision) - 本地運算，無需網絡
- **備援策略**: Gemini 1.5 Flash - Ollama 失敗時自動切換

### 2. 智能座標庫
- **自適應縮放**: 根據解析度自動縮放歷史座標
- **動態 Prompt**: 包含歷史參考座標和鄰近元素信息
- **增量更新**: 精準識別結果自動寫入座標庫

### 3. 雙重驗證機制
- **歐幾里得距離校驗**: 比較 VLM 結果與歷史座標
- **信心校驗**: 差異過大時觸發二次確認

### 4. 自動化管理
- **座標庫自動創建**: 首次使用自動初始化
- **解析度記錄**: 每次識別記錄當前解析度
- **統計信息**: 提供座標庫使用統計

---

## 快速開始

### 1. 基本使用

```python
from toolkit.vlm_engine import create_vlm_engine

# 創建 VLM 引擎
vlm = create_vlm_engine(threshold=15.0)

# 識別元素
area = vlm.find_element(
    element_name="確認按鈕",
    screenshot_path="screenshot.png",
    current_resolution=(1920, 1080)
)

if area:
    print(f"找到元素位置: {area.center}")
    print(f"區域範圍: {area.to_tuple()}")
```

### 2. 啟用 Gemini 備援

```python
from toolkit.vlm_engine import UnifiedVLM

vlm = UnifiedVLM(
    threshold=15.0,
    gemini_api_key="YOUR_GEMINI_API_KEY"
)

area = vlm.find_element("登錄按鈕", "screenshot.png")
```

### 3. 自定義閾值

```python
# 高精度模式（閾值 10px）
vlm_high = UnifiedVLM(threshold=10.0)

# 寬鬆模式（閾值 30px）
vlm_relaxed = UnifiedVLM(threshold=30.0)
```

---

## API 參考

### UnifiedVLM 類

#### 初始化

```python
UnifiedVLM(
    threshold: float = 15.0,
    logger: Optional[logging.Logger] = None,
    ollama_model: str = "llama3.2-vision",
    gemini_api_key: Optional[str] = None
)
```

**參數：**
- `threshold`: 距離閾值（像素），預設 15
- `logger`: 日誌記錄器（可選）
- `ollama_model`: Ollama 模型名稱
- `gemini_api_key`: Gemini API 金鑰（啟用備援）

#### 主要方法

##### find_element()

```python
find_element(
    element_name: str,
    screenshot_path: str,
    current_resolution: Tuple[int, int] = (1920, 1080)
) -> Optional[Area]
```

**功能**: 尋找元素並返回 Area 物件

**參數:**
- `element_name`: 元素名稱（如 "確認按鈕"）
- `screenshot_path`: 截圖文件路徑
- `current_resolution`: 當前螢幕解析度 (width, height)

**返回:**
- `Area` 物件: 包含識別到的區域座標
- `None`: 識別失敗

**執行流程:**
1. 從座標庫讀取歷史數據
2. 根據解析度縮放歷史座標
3. 生成動態 Prompt（包含歷史參考）
4. 嘗試 Ollama 識別
5. Ollama 失敗則備援至 Gemini
6. 驗證結果並更新座標庫

##### get_statistics()

```python
get_statistics() -> Dict[str, Any]
```

**功能**: 獲取座標庫統計信息

**返回:**
```python
{
    "total_elements": 10,      # 總元素數
    "total_records": 150,      # 總記錄數
    "elements": [...]          # 元素列表
}
```

---

## 座標庫結構

### coordinate_library.json

```json
{
  "metadata": {
    "created_at": "2026-01-27T00:00:00",
    "version": "1.0"
  },
  "elements": {
    "確認按鈕": {
      "avg_coord": [960, 540],
      "resolution": [1920, 1080],
      "count": 15,
      "last_updated": "2026-01-27T12:00:00",
      "neighbors": [
        "取消按鈕在右側 50px",
        "標題在上方 100px"
      ]
    }
  }
}
```

### 欄位說明

- `avg_coord`: 平均座標（加權平均）
- `resolution`: 記錄時的解析度
- `count`: 識別次數
- `last_updated`: 最後更新時間
- `neighbors`: 鄰近元素相對位置

---

## 座標縮放算法

### 自適應縮放原理

當螢幕解析度改變時，座標需要按比例縮放：

```python
# 歷史數據
hist_coord = (960, 540)      # 歷史座標
hist_resolution = (1920, 1080)  # 歷史解析度

# 當前環境
current_resolution = (2560, 1440)  # 當前解析度

# 計算縮放比例
scale_x = 2560 / 1920  # 1.333
scale_y = 1440 / 1080  # 1.333

# 縮放座標
new_x = 960 * 1.333 = 1280
new_y = 540 * 1.333 = 720

# 結果
normalized_coord = (1280, 720)
```

### 實現代碼

```python
def _normalize_coords(
    self,
    historical_data: Dict[str, Any],
    current_resolution: Tuple[int, int]
) -> Optional[Tuple[int, int]]:
    """自適應縮放座標"""
    hist_coord = historical_data.get("avg_coord")
    hist_resolution = historical_data.get("resolution")
    
    hist_x, hist_y = hist_coord
    hist_w, hist_h = hist_resolution
    curr_w, curr_h = current_resolution
    
    # 計算縮放比例
    scale_x = curr_w / hist_w
    scale_y = curr_h / hist_h
    
    # 縮放座標
    new_x = int(hist_x * scale_x)
    new_y = int(hist_y * scale_y)
    
    return (new_x, new_y)
```

---

## 驗證機制

### 1. 歐幾里得距離校驗

```python
# 計算 VLM 結果與歷史座標的距離
distance = Toolkit.calculate_distance(vlm_coord, normalized_coord)

if distance <= threshold:
    # 精準識別，更新座標庫
    update_coordinate_library()
else:
    # 差異過大，觸發信心校驗
    confidence_check()
```

### 2. 信心校驗 (Self-Reflection)

當距離 > 閾值時，觸發二次確認：

```python
prompt = f"""
你給出的座標是 {vlm_coord}，
但歷史記錄顯示此元素通常位於 {expected_coord}。

請重新檢查並回答：
1. 你選擇的座標是否確實是目標元素？
2. 為什麼選擇這個位置？
3. 是否可能誤認了相似元素？

請以 JSON 格式回答：
{{"confidence": true/false, "reason": "解釋原因"}}
"""
```

---

## 動態 Prompt 生成

### Prompt 結構

```
請在截圖中找到「確認按鈕」的中心座標。

參考資訊：歷史記錄顯示此元素通常位於 (960, 540) 附近。

相對位置關係：
  - 取消按鈕在右側 50px
  - 標題在上方 100px

請以 JSON 格式返回結果：
{"x": <整數座標>, "y": <整數座標>}

注意：
1. 座標必須是整數
2. 座標原點 (0,0) 在螢幕左上角
3. 只返回 JSON，不要包含其他文字
```

### 實現代碼

```python
def _generate_prompt(
    self,
    element_name: str,
    normalized_coord: Optional[Tuple[int, int]],
    historical_data: Optional[Dict[str, Any]]
) -> str:
    """生成動態 Prompt"""
    prompt_parts = [
        f"請在截圖中找到「{element_name}」的中心座標。",
        ""
    ]
    
    # 添加歷史參考
    if normalized_coord:
        x, y = normalized_coord
        prompt_parts.append(
            f"參考資訊：歷史記錄顯示此元素通常位於 ({x}, {y}) 附近。"
        )
    
    # 添加鄰近元素
    if historical_data and "neighbors" in historical_data:
        neighbors = historical_data["neighbors"]
        if neighbors:
            prompt_parts.append("相對位置關係：")
            for neighbor in neighbors:
                prompt_parts.append(f"  - {neighbor}")
    
    # 添加輸出格式
    prompt_parts.extend([
        "",
        "請以 JSON 格式返回結果：",
        '{"x": <整數座標>, "y": <整數座標>}'
    ])
    
    return "\n".join(prompt_parts)
```

---

## 使用範例

### 範例 1：基本識別

```python
from toolkit.vlm_engine import create_vlm_engine

vlm = create_vlm_engine()

area = vlm.find_element(
    element_name="確認按鈕",
    screenshot_path="screenshot.png"
)

if area:
    print(f"中心座標: {area.center}")
    print(f"區域: {area.to_tuple()}")
```

### 範例 2：批量識別

```python
elements = ["確認按鈕", "取消按鈕", "登錄輸入框"]

results = {}
for element_name in elements:
    area = vlm.find_element(element_name, "screenshot.png")
    results[element_name] = area

for name, area in results.items():
    if area:
        print(f"✅ {name}: {area.center}")
    else:
        print(f"❌ {name}: 未找到")
```

### 範例 3：查看統計

```python
stats = vlm.get_statistics()

print(f"總元素數: {stats['total_elements']}")
print(f"總記錄數: {stats['total_records']}")
print(f"元素列表: {stats['elements']}")
```

---

## 配置說明

### Ollama 配置

```python
# 預設配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2-vision"

# 自定義配置
vlm = UnifiedVLM(ollama_model="llava:13b")
```

### Gemini 配置

```python
# 啟用 Gemini 備援
vlm = UnifiedVLM(
    gemini_api_key="YOUR_API_KEY"
)

# Gemini 模型
GEMINI_MODEL = "gemini-1.5-flash"  # 免費版
```

---

## 日誌輸出

### 日誌級別

- `INFO`: 識別成功、驗證通過
- `WARNING`: 座標差異、備援切換
- `ERROR`: 識別失敗、請求錯誤
- `DEBUG`: 詳細過程、座標縮放

### 日誌範例

```
[2026-01-27 12:00:00] [UnifiedVLM] [INFO] 初始化完成 - Ollama: llama3.2-vision, 閾值: 15px
[2026-01-27 12:00:01] [UnifiedVLM] [INFO] 開始識別元素: 確認按鈕
[2026-01-27 12:00:01] [UnifiedVLM] [DEBUG] 讀取歷史數據: 確認按鈕 -> {'avg_coord': [960, 540], ...}
[2026-01-27 12:00:01] [UnifiedVLM] [DEBUG] 座標縮放: (960, 540) @ (1920, 1080) -> (1280, 720) @ (2560, 1440)
[2026-01-27 12:00:02] [UnifiedVLM] [INFO] Ollama 識別成功: (1275, 718)
[2026-01-27 12:00:02] [UnifiedVLM] [INFO] 座標驗證: VLM=(1275, 718), 歷史=(1280, 720), 距離=5.83px
[2026-01-27 12:00:02] [UnifiedVLM] [INFO] [VLM_VALIDATION_OK] 元素 '確認按鈕' 座標驗證通過
```

---

## 錯誤處理

### 常見錯誤

#### 1. Ollama 連接失敗

```
[ERROR] Ollama 請求失敗: Connection refused
[WARNING] Ollama 失敗，切換至 Gemini 備援
```

**解決方法:**
- 確認 Ollama 服務已啟動
- 檢查 `OLLAMA_BASE_URL` 配置

#### 2. 座標解析失敗

```
[WARNING] Ollama 響應格式無效
[ERROR] 解析座標失敗: JSON decode error
```

**解決方法:**
- 檢查 Prompt 格式
- 嘗試使用 Gemini 備援

#### 3. 座標差異過大

```
[WARNING] [VLM_DISCREPANCY_WARNING] 元素 '確認按鈕' 座標差異過大: 50.23px > 15px
[INFO] 觸發信心校驗: 確認按鈕
```

**解決方法:**
- 調整閾值參數
- 檢查截圖是否正確
- 查看信心校驗結果

---

## 最佳實踐

### 1. 閾值設置

```python
# UI 穩定的應用（推薦 10-15px）
vlm = UnifiedVLM(threshold=15.0)

# UI 經常變動的應用（推薦 20-30px）
vlm = UnifiedVLM(threshold=25.0)
```

### 2. 解析度管理

```python
import pyautogui

# 獲取當前解析度
current_resolution = pyautogui.size()

area = vlm.find_element(
    "按鈕",
    "screenshot.png",
    current_resolution=current_resolution
)
```

### 3. 批量識別優化

```python
# 創建一個 VLM 實例，重複使用
vlm = create_vlm_engine()

# 批量識別
for element in elements:
    area = vlm.find_element(element, screenshot)
```

### 4. 日誌管理

```python
import logging

# 創建自定義 Logger
logger = logging.getLogger("MyApp")
logger.setLevel(logging.DEBUG)

vlm = UnifiedVLM(logger=logger)
```

---

## 總結

`UnifiedVLM` 提供了一個強大且靈活的視覺元素識別解決方案：

✅ **雙重備援** - Ollama + Gemini 無縫切換  
✅ **智能座標庫** - 自適應縮放 + 增量更新  
✅ **雙重驗證** - 距離校驗 + 信心校驗  
✅ **易於使用** - 簡潔的 API + 詳細的日誌  
✅ **高度可配置** - 靈活的閾值和模型選擇

---

**作者:** SDET Team  
**日期:** 2026-01-27  
**版本:** 1.0
