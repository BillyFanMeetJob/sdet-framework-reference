# 📋 Case 1-2: 新增 Webcam 攝影機 - 完整流程

## 🎯 測試目標

驗證 USB 攝影機自動偵測功能，並成功開啟攝影機畫面。

---

## 📊 完整流程

```
1. 登入檢查
   ↓
2. 右鍵點擊 Server 圖示
   ↓
3. 點擊「伺服器設定」選單
   ↓
4. 勾選「自動偵測內建 USB 攝影機」
   ↓
5. 點擊「確定」按鈕
   ↓
6. 處理密碼確認彈窗（如果出現）
   ↓
7. 等待設定生效
   ↓
8. 左鍵點擊 Server 圖示（展開攝影機列表）
   ↓
9. 雙擊 USB 攝影機項目
   ↓
10. 顯示攝影機畫面 ✅
```

---

## 🔧 步驟詳解

### 步驟 1-6：啟用 USB 攝影機偵測

這部分已經完成，包括：
- ✅ 右鍵點擊 Server 圖示
- ✅ 點擊「伺服器設定」選單
- ✅ 智能勾選 checkbox（已勾選時跳過）
- ✅ 點擊確定按鈕
- ✅ 處理密碼確認彈窗

---

### 步驟 7：等待設定生效

```python
time.sleep(1)  # 等待設定生效
```

**原因：** USB 攝影機需要時間被系統偵測並註冊

---

### 步驟 8：雙擊 Server 項目

**目的：** 展開 Server 下的攝影機列表

**方法：** `double_click_server_icon()`

**實現：**
```python
def double_click_server_icon(self):
    """
    🎯 雙擊左側面板的 Server 項目（展開攝影機列表）
    優先級：OCR 文字 > 座標保底
    """
    # 1. OCR 文字辨識（在左側面板搜尋）
    left_panel_region = (win.left, win.top, int(win.width * 0.2), win.height)
    result = self._find_text_by_ocr("Server", left_panel_region)
    
    # 2. 座標保底
    click_x = win.left + int(win.width * 0.10)
    click_y = win.top + int(win.height * 0.14)
    
    # 執行雙擊
    pyautogui.doubleClick(click_x, click_y)
```

**兩級優先級：**
1. 📝 OCR 文字：在左側面板（視窗左側 20%）尋找 "Server" 文字
2. 📍 座標保底：(0.10, 0.14) 左側面板 Server 項目位置

---

### 步驟 9：雙擊 USB 攝影機

**目的：** 開啟攝影機畫面

**方法：** `double_click_usb_camera(camera_name="usb_cam")`

**實現：**
```python
def double_click_usb_camera(self, camera_name="usb_cam"):
    """
    🎯 雙擊 USB 攝影機項目
    優先級：圖片辨識 > OCR 文字 > 座標保底
    """
    # 1. 圖片辨識
    camera_img_path = "desktop_main/usb_cam_item.png"
    loc = pyautogui.locateOnScreen(camera_img_path, confidence=0.7, region=region)
    
    # 2. OCR 文字辨識
    result = self._find_text_by_ocr(camera_name, region)
    
    # 3. 座標保底
    click_x = win.left + int(win.width * 0.15)
    click_y = win.top + int(win.height * 0.20)
    
    # 執行雙擊
    pyautogui.doubleClick(click_x, click_y)
```

**三級優先級：**
1. 📸 圖片辨識：`desktop_main/usb_cam_item.png`
2. 📝 OCR 文字：尋找攝影機名稱（如 "usb_cam"）
3. 📍 座標保底：(0.15, 0.20) 左側面板中間位置

---

## 📝 TestPlan 配置

### DemoData/TestPlan.xlsx

**Case1 分頁：**

| TestName | StepNo | FlowName | Params |
|----------|--------|----------|--------|
| 新增Webcam攝影機 | 1 | ensure_login | server_name=LAPTOP-QRJN5735 |
| 新增Webcam攝影機 | 2 | 啟用USB攝影機 | camera_name=usb_cam |

**Translate 分頁：**

| FlowName | ActionKey | ActionMethod |
|----------|-----------|--------------|
| ensure_login | nx_poc | run_ensure_login_step |
| 啟用USB攝影機 | nx_poc | run_enable_usb_webcam_step |

---

## 🎯 參數說明

### camera_name

**用途：** 指定要雙擊的攝影機名稱

**預設值：** `"usb_cam"`

**使用範例：**
```excel
Params: camera_name=usb_cam-ACER HD User Facing
```

**對應到代碼：**
```python
def run_enable_usb_webcam_step(self, **kwargs):
    camera_name = kwargs.get("camera_name", "usb_cam")
    self.server_settings_page.double_click_usb_camera(camera_name)
```

---

## 🧪 測試指令

```powershell
pytest tests/test_runner.py -s --test_name "新增Webcam攝影機"
```

---

## 📊 預期日誌輸出

```
>>> 🔍 檢查登錄狀態（目標伺服器: LAPTOP-QRJN5735）
>>> ✅ 已在主畫面，無需重新登錄
>>> 🎬 執行 Case 1-2: 啟用 USB 攝影機自動偵測
>>> 🖱️ 在 Server 圖示上點擊右鍵...
>>> 📸 Server 圖示辨識成功: (63, 201)
>>> ✅ 右鍵選單已出現
>>> 🖱️ 點擊「伺服器設定」選單項目...
>>> 📍 執行相對座標點擊: (163, 601)
>>> ✅ 伺服器設定視窗已開啟
>>> 🖱️ 檢查「自動偵測內建 USB 攝影機」選項...
>>> 📸 USB checkbox 圖片辨識成功: (419, 397)
>>> Checkbox 像素標準差: 36.32, 閾值: 15, 判定: 已勾選
>>> ✅ USB 攝影機選項已經勾選，跳過
>>> 🖱️ 點擊「套用」或「確定」按鈕...
>>> 📸 圖片辨識成功並點擊: desktop_settings/ok_btn.png
>>> ✅ 成功點擊「確定」按鈕
>>> 未檢測到密碼確認彈窗
>>> ✅ 設定視窗已關閉
>>> ✅ USB 攝影機自動偵測已啟用
>>> 🖱️ 左鍵點擊 Server 圖示...
>>> 📸 圖片辨識成功並點擊: desktop_main/server_icon.png
>>> ✅ 成功點擊 Server 圖示
>>> 🖱️ 雙擊攝影機: usb_cam...
>>> 📸 攝影機圖示辨識成功: (150, 235)
>>> ✅ 雙擊攝影機: usb_cam
>>> ✅ Case 1-2 完成：已開啟攝影機 usb_cam
```

---

## 🔍 故障排除

### 問題 1：找不到攝影機項目

**可能原因：**
- USB 攝影機尚未被系統偵測
- 攝影機名稱不匹配

**解決方案：**
```python
# 增加等待時間
time.sleep(2)  # 等待攝影機註冊

# 或使用更通用的名稱搜尋
camera_name = "usb"  # 只搜尋 "usb" 而不是完整名稱
```

---

### 問題 2：雙擊位置不對

**可能原因：**
- 攝影機列表尚未完全展開
- 座標保底位置不準確

**解決方案：**
```python
# 調整座標保底位置
click_x = win.left + int(win.width * 0.15)  # 調整 x
click_y = win.top + int(win.height * 0.25)  # 調整 y（往下移）
```

---

### 問題 3：攝影機畫面沒有載入

**可能原因：**
- 雙擊速度太快
- 攝影機尚未就緒

**解決方案：**
```python
# 增加雙擊後的等待時間
time.sleep(2)  # 從 1 秒增加到 2 秒
```

---

## 📸 需要的圖片資源

請準備以下圖片並放在 `res/` 目錄：

### 1. Server 圖示
- **路徑：** `res/desktop_main/server_icon.png`
- **說明：** Server 圖示的截圖
- **用途：** 辨識並點擊 Server 圖示

### 2. USB 攝影機項目
- **路徑：** `res/desktop_main/usb_cam_item.png`
- **說明：** USB 攝影機在列表中的截圖
- **用途：** 辨識並雙擊攝影機項目

**截圖建議：**
- 截取完整的圖示和文字
- 確保背景顏色一致
- 避免包含動態變化的元素

---

## ✅ 功能總結

### 已實現功能

1. ✅ **智能登錄檢查**
   - 已登錄時跳過
   - 未登錄時自動執行登錄

2. ✅ **智能 Checkbox 勾選**
   - 已勾選時跳過
   - 未勾選時執行勾選

3. ✅ **密碼確認彈窗處理**
   - 自動檢測彈窗
   - 自動輸入密碼並確認
   - 無彈窗時正常繼續

4. ✅ **展開攝影機列表**
   - 左鍵點擊 Server 圖示
   - 三級優先級策略

5. ✅ **開啟攝影機**
   - 雙擊 USB 攝影機
   - 三級優先級策略
   - 支援自定義攝影機名稱

---

## 🎉 Case 1-2 完整實現

**測試流程：** 從登錄到開啟攝影機畫面，全自動化！

**特色：**
- ✅ 冪等性：重複執行結果相同
- ✅ 智能判斷：避免重複操作
- ✅ 多級保底：圖片 → OCR → 座標
- ✅ 完整日誌：每步驟詳細記錄

---

**📌 Case 1-2 功能已完整實現，請測試驗證！**
