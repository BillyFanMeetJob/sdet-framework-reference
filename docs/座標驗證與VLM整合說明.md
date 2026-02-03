# 座標驗證與 VLM 整合說明

## 概述

本文檔說明如何使用新增的座標驗證功能，以及如何整合 VLM（視覺語言模型）進行雙重識別驗證。

## 功能特性

### 1. Area 類型與工具方法

在 `toolkit/types.py` 中定義了 `Area` 類別和 `Toolkit` 工具類：

```python
from toolkit.types import Area, Toolkit

# 創建 Area 物件
area = Area(x1=100, y1=100, x2=200, y2=200)

# 獲取中心點
center = Toolkit.calculate_center(area)
# 或使用屬性
center = area.center

# 計算兩點距離
distance = Toolkit.calculate_distance((100, 100), (105, 103))

# 從中心點計算左上角座標
top_left = Toolkit.calculate_top_left_from_center(
    center=(150, 150),
    width=100,
    height=100
)
# 結果: (100, 100)

# 從中心點創建 Area
area = Toolkit.create_area_from_center(
    center=(150, 150),
    width=100,
    height=100
)
# 結果: Area(x1=100, y1=100, x2=200, y2=200)
```

### 2. 座標驗證器

`CoordinateValidator` 類用於驗證圖像辨識與 VLM 的座標差異：

```python
from toolkit.coordinate_validator import CoordinateValidator

# 初始化驗證器（預設閾值 15 像素）
validator = CoordinateValidator(threshold=15.0, logger=logger)

# 驗證座標
comparison = validator.validate_coordinates(
    element_name="確認按鈕",
    cv_coord=(100, 100),  # 圖像辨識座標
    vlm_coord=(105, 103)  # VLM 識別座標
)

# 檢查結果
if comparison.is_discrepancy:
    print(f"座標差異過大: {comparison.distance:.2f}px")
else:
    print(f"座標驗證通過: {comparison.distance:.2f}px")

# 保存至座標庫
validator.save_to_library(comparison)

# 或一次完成驗證與保存
comparison = validator.validate_and_save(
    element_name="確認按鈕",
    cv_coord=(100, 100),
    vlm_coord=(105, 103)
)
```

### 3. 座標庫數據格式

座標比對結果保存在 `coordinate_library.json`：

```json
[
  {
    "element_name": "確認按鈕",
    "cv_coord": [100, 100],
    "vlm_coord": [105, 103],
    "distance": 5.83,
    "timestamp": "2026-01-23T18:30:45.123456",
    "threshold": 15.0,
    "is_discrepancy": false
  },
  {
    "element_name": "取消按鈕",
    "cv_coord": [200, 200],
    "vlm_coord": [220, 210],
    "distance": 22.36,
    "timestamp": "2026-01-23T18:31:12.654321",
    "threshold": 15.0,
    "is_discrepancy": true
  }
]
```

### 4. 測試報告整合

`TestReporter` 已整合座標驗證功能：

```python
from engine.test_reporter import TestReporter

reporter = TestReporter(test_name="測試案例")

# 添加辨識截圖時自動進行 VLM 驗證
reporter.add_recognition_screenshot(
    item_name="確認按鈕",
    x=100,  # 圖像辨識的中心點 X 座標
    y=100,  # 圖像辨識的中心點 Y 座標
    width=80,
    height=30,
    method="OK Script",
    vlm_coord=(105, 103)  # VLM 識別的座標（可選）
)
```

## 修復的問題

### 物件框選繪圖偏移

**問題描述：**
- 之前的繪圖邏輯誤將物件中心點 `(x, y)` 當作左上角座標
- 導致繪製的紅色矩形框位置不正確

**修復方案：**
- 使用 `Toolkit.calculate_top_left_from_center()` 計算正確的左上角座標
- 確保框線精準包圍物件

**修復前：**
```python
# 錯誤：將中心點當作左上角
rect = [x, y, x + width, y + height]
draw.rectangle(rect, outline='red', width=3)
```

**修復後：**
```python
# 正確：先計算左上角座標
top_left_x, top_left_y = Toolkit.calculate_top_left_from_center(
    center=(x, y),
    width=width,
    height=height
)
rect = [top_left_x, top_left_y, top_left_x + width, top_left_y + height]
draw.rectangle(rect, outline='red', width=3)
```

## 使用流程

### 完整的圖像辨識 + VLM 驗證流程

```python
# 1. 使用圖像辨識找到物件
cv_result = image_recognition.find_element("確認按鈕")
cv_x, cv_y = cv_result.center
cv_width, cv_height = cv_result.width, cv_result.height

# 2. 使用 VLM 進行二次驗證
from base.vlm_recognizer import get_vlm_recognizer

vlm = get_vlm_recognizer(model='llava')
vlm_result = vlm.find_element(
    query="確認按鈕",
    region=(cv_x - 50, cv_y - 50, 100, 100)  # 在圖像辨識結果附近搜索
)

# 3. 驗證兩個座標的一致性
if vlm_result and vlm_result.success:
    vlm_x, vlm_y = vlm_result.x, vlm_result.y
    
    # 計算距離
    distance = Toolkit.calculate_distance((cv_x, cv_y), (vlm_x, vlm_y))
    
    # 如果距離過大，記錄警告
    if distance > 15:
        logger.warning(
            f"[VLM_DISCREPANCY_WARNING] 座標差異: "
            f"CV=({cv_x}, {cv_y}), VLM=({vlm_x}, {vlm_y}), "
            f"距離={distance:.2f}px"
        )
    
    # 4. 保存比對結果到座標庫
    validator.validate_and_save(
        element_name="確認按鈕",
        cv_coord=(cv_x, cv_y),
        vlm_coord=(vlm_x, vlm_y)
    )
    
    # 5. 添加到測試報告（自動進行驗證）
    reporter.add_recognition_screenshot(
        item_name="確認按鈕",
        x=cv_x,
        y=cv_y,
        width=cv_width,
        height=cv_height,
        method="OK Script",
        vlm_coord=(vlm_x, vlm_y),
        vlm_box=vlm_result.box  # VLM 邊界框
    )
```

## 日誌輸出範例

### 驗證通過

```log
[INFO] [VLM_VALIDATION_OK] 元素 '確認按鈕' 座標驗證通過: CV=(100, 100), VLM=(105, 103), 距離=5.83px
```

### 驗證失敗（差異過大）

```log
[WARNING] [VLM_DISCREPANCY_WARNING] 元素 '取消按鈕' 座標差異過大: CV=(200, 200), VLM=(220, 210), 距離=22.36px (閾值=15px)
```

## 座標庫統計

獲取座標庫的統計信息：

```python
stats = validator.get_statistics()
print(f"總記錄數: {stats['total_records']}")
print(f"差異記錄數: {stats['discrepancy_count']}")
print(f"差異比例: {stats['discrepancy_rate']}%")
print(f"平均距離: {stats['avg_distance']}px")
print(f"最大距離: {stats['max_distance']}px")
```

輸出範例：

```
總記錄數: 150
差異記錄數: 12
差異比例: 8.0%
平均距離: 7.35px
最大距離: 28.50px
```

## 最佳實踐

### 1. 閾值設定

- **預設閾值：** 15 像素
- **高精度場景：** 可降低至 10 像素
- **低精度場景：** 可提高至 20 像素

```python
# 高精度驗證
validator = CoordinateValidator(threshold=10.0)

# 一般驗證
validator = CoordinateValidator(threshold=15.0)

# 寬鬆驗證
validator = CoordinateValidator(threshold=20.0)
```

### 2. VLM 搜索區域

建議在圖像辨識結果附近設置搜索區域，提高 VLM 識別速度：

```python
# 在圖像辨識結果周圍 ±50 像素範圍內搜索
region = (
    cv_x - 50,  # left
    cv_y - 50,  # top
    100,        # width
    100         # height
)
vlm_result = vlm.find_element(query="按鈕", region=region)
```

### 3. 座標轉換注意事項

- **中心點 → 左上角：** 使用 `Toolkit.calculate_top_left_from_center()`
- **左上角 → 中心點：** 使用 `Area.center` 屬性或 `Toolkit.calculate_center()`
- **距離計算：** 使用 `Toolkit.calculate_distance()`，基於歐幾里得距離公式

## 故障排除

### 問題：座標驗證總是失敗

**可能原因：**
1. 閾值設置過小
2. VLM 模型識別精度不足
3. 圖像辨識與 VLM 使用的座標系不一致

**解決方案：**
1. 適當提高閾值
2. 檢查 VLM 模型是否正確加載
3. 確認座標轉換邏輯正確

### 問題：座標庫文件過大

**解決方案：**
定期清理舊記錄或實施數據歸檔策略：

```python
import json
from datetime import datetime, timedelta

# 讀取座標庫
with open('coordinate_library.json', 'r') as f:
    library = json.load(f)

# 保留最近 30 天的記錄
cutoff_date = datetime.now() - timedelta(days=30)
filtered_library = [
    record for record in library
    if datetime.fromisoformat(record['timestamp']) > cutoff_date
]

# 寫回文件
with open('coordinate_library.json', 'w') as f:
    json.dump(filtered_library, f, ensure_ascii=False, indent=2)
```

## 未來優化方向

1. **機器學習模型：** 使用座標庫數據訓練模型，預測最佳點擊位置
2. **自適應閾值：** 根據元素類型自動調整閾值
3. **可視化分析：** 生成座標差異的熱力圖
4. **自動修正：** 當差異超過閾值時，自動使用 VLM 座標
