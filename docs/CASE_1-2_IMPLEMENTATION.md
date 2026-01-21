# Case 1-2 實作說明文件

## 📋 測試案例概述

**測試案例**: 新增 Webcam 攝影機  
**測試步驟**: 17~19 操作  
**目標**: 啟用自動偵測內建 USB 攝影機功能

---

## 🎯 具體流程

1. **步驟 17**: 進入 Nx 主畫面，會看到剛剛建立好的 Server，右鍵點選「伺服器設定」
2. **步驟 18**: 顯示伺服器設定視窗，在「一般」頁籤中，勾選「自動偵測內建成 USB 攝影機」選項
3. **步驟 19**: 點選「確認」後，左側伺服器列表下，會自動新增該筆電的 Web Cam，點選之後會顯示在中央佈局上

---

## 🏗️ 架構設計

### 1. 新增頁面物件

**檔案**: `pages/desktop/server_settings_page.py`

繼承自 `DesktopApp`，封裝了伺服器設定相關的所有操作：

```python
class ServerSettingsPage(DesktopApp):
    def right_click_server_icon()      # 右鍵點擊 Server 圖示
    def click_server_settings_menu()   # 點擊「伺服器設定」選單
    def enable_usb_detection()         # 勾選 USB 攝影機選項
    def apply_settings()               # 點擊套用/確定按鈕
```

### 2. 動作流程整合

**檔案**: `actions/nx_poc_actions.py`

新增方法 `run_enable_usb_webcam_step()`，串接完整流程：

```python
def run_enable_usb_webcam_step(self, **kwargs):
    1. right_click_server_icon()       # 在 Server 圖示上點右鍵
    2. click_server_settings_menu()    # 點擊選單中的「伺服器設定」
    3. enable_usb_detection()          # 勾選 USB 選項
    4. apply_settings()                # 套用設定
```

---

## 🛡️ 主動防禦機制

### 問題 1: 右鍵選單容易消失

**解決方案**:
- 在點擊右鍵後，立即加入 `time.sleep(0.8)` 等待選單穩定
- 點擊選單項目時，使用 `smart_click` 的相對座標模式
- 記錄上次點擊位置，選單項目使用相對偏移計算

```python
# 右鍵點擊後立即等待
pyautogui.rightClick(click_x, click_y)
time.sleep(0.8)  # 🎯 關鍵：確保選單穩定

# 使用相對座標點擊選單項目
self.smart_click(
    x_ratio=0, 
    y_ratio=30,  # 向下偏移 30px
    is_relative=True,  # 相對於上次點擊位置
    ...
)
```

### 問題 2: 圖像辨識可能失敗

**解決方案**: 多層保底策略

#### 層級 1: 圖像辨識（優先）
使用 `pyautogui.locateOnScreen()` 嘗試找到目標元素

#### 層級 2: 比例座標保底
根據視窗大小和位置，使用預設的比例座標：

| 元素 | 保底座標 | 說明 |
|------|----------|------|
| Server Icon | (8%, 8%) | 視窗左上角 |
| Server Settings Menu | (+0px, +30px) | 相對座標，向下 30px |
| USB Checkbox | (30%, 42%) | 視窗內比例座標 |
| OK Button | (84%, 6% from bottom) | 視窗右下角 |

```python
# 保底策略範例
if click_x is None:
    self.logger.warning("⚠️ 圖像辨識失敗，使用座標保底策略")
    click_x = win.left + int(win.width * 0.08)
    click_y = win.top + int(win.height * 0.08)
```

#### 層級 3: 視窗底部對齊
針對按鈕類元素，使用 `from_bottom=True` 參數：

```python
self.smart_click(
    x_ratio=0.84,
    y_ratio=0.06,
    from_bottom=True,  # 從視窗底部向上計算
    ...
)
```

---

## 📸 所需圖像資源

請依照 `res/desktop_settings/SETUP_GUIDE_CASE_1-2.md` 指南截取以下圖像：

1. **server_icon.png** - Server 圖示
2. **server_settings_menu.png** - 「伺服器設定」選單項目
3. **usb_checkbox.png** - USB 攝影機勾選框區域
4. **ok_btn.png** - 確定按鈕

---

## 🔧 使用方式

### 在測試腳本中調用

```python
from actions.nx_poc_actions import NxPocActions

# 初始化
actions = NxPocActions(browser_context=None)

# 執行 Case 1-2
actions.run_enable_usb_webcam_step()
```

### 配合 Case 1-1 串接使用

```python
# Case 1-1: 登錄伺服器
actions.run_server_login_step()

# Case 1-2: 啟用 USB 攝影機
actions.run_enable_usb_webcam_step()
```

---

## 🎨 設計特點

### 1. 高容錯性
- 圖像辨識失敗時自動切換到座標保底
- 每個步驟都有錯誤處理和日誌記錄
- 支援多種點擊模式（絕對、相對、底部對齊）

### 2. 可維護性
- 清晰的方法命名和職責劃分
- 完整的中文註釋和日誌輸出
- 模組化設計，易於擴展

### 3. 可靠性
- 針對右鍵選單易消失問題的專門處理
- 視窗激活和等待機制
- 座標計算基於視窗動態位置

---

## 🐛 疑難排解

### 問題 1: 右鍵選單沒有出現
**檢查**:
- Server 圖示是否正確定位
- 是否有足夠的等待時間 (0.8s)

**調整**:
- 增加 `right_click_server_icon()` 中的等待時間
- 調整保底座標 (0.08, 0.08)

### 問題 2: 找不到伺服器設定選單
**檢查**:
- 右鍵選單是否成功顯示
- 相對座標偏移是否正確 (+30px)

**調整**:
- 修改 `click_server_settings_menu()` 中的 `y_ratio` 值
- 截取正確的 `server_settings_menu.png` 圖像

### 問題 3: USB 選項勾選失敗
**檢查**:
- 設定視窗是否已開啟
- 保底座標 (0.3, 0.42) 是否對應到勾選框

**調整**:
- 在設定視窗開啟後增加等待時間
- 根據實際視窗截圖調整比例座標
- 確保截取清晰的 `usb_checkbox.png`

### 問題 4: 無法點擊確定/套用按鈕
**檢查**:
- 按鈕是否在視窗可見範圍內
- `from_bottom=True` 座標計算是否正確

**調整**:
- 調整 `apply_settings()` 中的 x_ratio 和 y_ratio
- 確保 `ok_btn.png` 圖像清晰可辨識

---

## 📊 執行日誌範例

```
[INFO] 🎬 執行 Case 1-2: 啟用 USB 攝影機自動偵測
[INFO] 🖱️ 在 Server 圖示上點擊右鍵...
[INFO] 📸 Server 圖示辨識成功: (120, 150)
[INFO] ✅ 右鍵選單已觸發，等待選單穩定...
[INFO] 🖱️ 點擊「伺服器設定」選單項目...
[INFO] ✅ 成功點擊「伺服器設定」
[INFO] 🖱️ 勾選「自動偵測內建 USB 攝影機」...
[INFO] 📍 執行視窗比例點擊: (350, 280)
[INFO] ✅ 成功勾選 USB 攝影機選項
[INFO] 🖱️ 點擊「套用」或「確定」按鈕...
[INFO] 📍 執行視窗底部對齊點擊: (820, 690)
[INFO] ✅ 成功點擊「確定」按鈕
[INFO] ✅ Case 1-2 完成：USB 攝影機自動偵測已啟用
```

---

## 🔄 後續擴展

可以基於此架構擴展更多伺服器設定相關功能：

- 修改伺服器名稱
- 設定儲存管理
- 配置備援伺服器
- 調整儲存分析設定

只需在 `ServerSettingsPage` 中新增對應的方法即可。
