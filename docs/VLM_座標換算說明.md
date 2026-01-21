# VLM 座標換算說明

## 概述

VLM (Vision Language Model) 返回的座標需要經過換算才能得到屏幕絕對座標。此文件說明換算邏輯，確保修改時不會破壞已有功能。

## 座標換算流程

### 1. VLM 返回的座標

VLM 返回的座標可能是：
- **比例座標**：0-1 之間的小數（相對於截圖尺寸）
- **像素座標**：整數（相對於截圖的像素位置）

判斷標準：如果座標值 < 1.0，認為是比例座標；否則是像素座標。

### 2. 截圖處理

截圖可能經過以下處理：
- **縮小**：為了減少 API 成本和延遲，截圖可能被縮小到最大 1280x720
- **區域截圖**：如果提供了 `region`，只截取指定區域

### 3. 座標換算步驟

```
VLM 返回座標（相對於縮小後的截圖）
    ↓
判斷是比例座標還是像素座標
    ↓
轉換為縮小後圖片的像素座標（如果是比例座標）
    ↓
轉換回原始截圖尺寸（如果截圖被縮小）
    ↓
加上 region 偏移（如果提供了 region）
    ↓
得到屏幕絕對座標
```

## 換算公式

### 比例座標換算

```python
# 1. 轉換為縮小後圖片的像素座標
pixel_x = vlm_x * resized_size[0]
pixel_y = vlm_y * resized_size[1]

# 2. 轉換回原始截圖尺寸
scale_x = original_size[0] / resized_size[0]
scale_y = original_size[1] / resized_size[1]
result_x = pixel_x * scale_x
result_y = pixel_y * scale_y

# 3. 加上 region 偏移（如果有）
if region:
    result_x += region[0]  # region[0] 是 left
    result_y += region[1]  # region[1] 是 top
```

### 像素座標換算

```python
# 1. 直接使用（假設是相對於縮小後的圖片）
pixel_x = vlm_x
pixel_y = vlm_y

# 2. 轉換回原始截圖尺寸
scale_x = original_size[0] / resized_size[0]
scale_y = original_size[1] / resized_size[1]
result_x = pixel_x * scale_x
result_y = pixel_y * scale_y

# 3. 加上 region 偏移（如果有）
if region:
    result_x += region[0]
    result_y += region[1]
```

## 測試驗證

修改座標換算邏輯前，請運行：

```bash
python test_vlm_coordinate_conversion.py
```

此測試涵蓋以下場景：
1. 全屏截圖，無縮小，比例座標
2. 全屏截圖，縮小後，比例座標
3. 區域截圖，無縮小，比例座標
4. 區域截圖，縮小後，比例座標
5. 區域截圖，無縮小，像素座標
6. 區域截圖，縮小後，像素座標

## 使用 VLM 的地方

以下地方使用 VLM，修改座標換算邏輯時需要檢查：

### base/desktop_app.py
- `_try_vlm_recognition()`: 核心 VLM 辨識方法
- `verify_element_exists()`: 驗證元素是否存在
- `smart_click()`: 智能點擊（VLM 優先級）
- `smart_click_priority_text()`: 文字優先點擊
- `smart_click_priority_image()`: 圖片優先點擊

### pages/desktop/camera_page.py
- `click_camera_settings_menu()`: 點擊攝影機設定選單
- `switch_to_recording_tab()`: 切換到錄影分頁
- `check_and_set_recording_radio_y()`: 檢查並設置錄影 radio
- `select_recording_schedule_range()`: 選擇錄影時段
- `apply_camera_settings()`: 套用攝影機設定

## 注意事項

1. **座標換算邏輯是核心邏輯**，影響所有使用 VLM 的地方
2. **修改前必須運行測試**，確保不會破壞已有功能
3. **添加詳細的調試日誌**，方便排查問題
4. **保持向後兼容性**，避免突然改變座標換算行為

## 常見問題

### Q: 為什麼需要座標換算？

A: VLM 返回的座標是相對於截圖的，而截圖可能被縮小或只截取部分區域。需要換算才能得到屏幕絕對座標。

### Q: 如何判斷 VLM 返回的是比例座標還是像素座標？

A: 如果座標值 < 1.0，認為是比例座標；否則是像素座標。

### Q: 修改座標換算邏輯後，如何確保不會破壞已有功能？

A: 
1. 運行 `test_vlm_coordinate_conversion.py` 驗證
2. 檢查所有使用 VLM 的地方是否仍然正常工作
3. 添加詳細的調試日誌，方便排查問題
