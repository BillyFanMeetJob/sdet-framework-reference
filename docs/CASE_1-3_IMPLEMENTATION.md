# Case 1-3: 啟用免費錄製授權 - 實現說明

## 📋 測試需求

根據 TestPlan 步驟 20-24，實現啟用免費一個月的錄製授權功能。

## 🎯 測試步驟

| 步驟 | 操作說明 | 實現方法 |
|------|---------|---------|
| 20 | 在左側 Server 上右鍵，點選「系統管理」 | `open_system_administration()` |
| 21 | 進入「系統管理」視窗（預設在「一般」頁籤） | 自動檢測視窗開啟 |
| 22 | 切換到「授權」頁籤，點選「啟用免費授權」 | `switch_to_license_tab()` + `click_activate_free_license()` |
| 23 | 顯示已啟用授權，點選 OK | `confirm_license_activation()` |
| 24 | 回到「授權」頁籤，顯示授權碼，點選 OK | `close_system_administration()` |

## 🏗️ 架構設計

### 新增檔案

```
pages/desktop/
├── license_settings_page.py    # ✅ 新增：授權設定頁面
```

### 類別結構

```python
LicenseSettingsPage (繼承 DesktopApp)
├── open_system_administration()      # 開啟系統管理視窗
├── switch_to_license_tab()           # 切換到授權分頁
├── click_activate_free_license()     # 點擊啟用免費授權
├── confirm_license_activation()      # 確認授權啟動
└── close_system_administration()     # 關閉系統管理視窗
```

## 🔧 核心方法說明

### 1. `open_system_administration(via_menu=False)`

開啟系統管理視窗，支援兩種方式：
- **方式 1**（預設）：在 Server 上右鍵 → 系統管理
- **方式 2**：點擊左上角三條線選單 → 系統管理

**實現要點：**
- 使用 `smart_click` 的 `click_type='right'` 實現右鍵點擊
- 使用 `wait_for_window()` 等待系統管理視窗開啟
- 支援多語言視窗標題檢測

```python
# 右鍵點擊 Server
self.smart_click(
    x_ratio=0.08, y_ratio=0.08,
    target_text="Server",
    image_path="desktop_main/server_icon.png",
    click_type='right'
)

# 點擊系統管理選項
self.smart_click(
    x_ratio=0.08, y_ratio=0.08,
    y_offset=70,  # 右鍵選單第 2 項
    target_text="系統管理"
)
```

### 2. `switch_to_license_tab()`

切換到「授權」分頁。

**實現要點：**
- 授權是第 4 個分頁（一般、使用者管理、更新、**授權**...）
- 使用相對座標 `x_ratio=0.25` 定位
- 搭配 OCR 文字搜尋提高準確性

### 3. `click_activate_free_license()`

點擊「啟用免費授權」按鈕。

**實現要點：**
- 按鈕在「線上啟動」標籤下方中間位置
- 按鈕文字：「啟動試用授權」或「Activate Free License」
- 點擊後等待 2 秒讓授權處理完成

### 4. `confirm_license_activation()`

確認授權啟動成功彈窗。

**實現要點：**
- 尋找「確認」或「OK」按鈕
- 彈窗按鈕通常在底部中間或右側
- 容錯處理：若未找到彈窗，可能已經啟用過

### 5. `close_system_administration()`

關閉系統管理視窗。

**實現要點：**
- 點擊右下角的「確認」或「OK」按鈕
- 使用 `wait_for_window_close()` 確保視窗已關閉

## 🎮 使用方式

### 在 Actions 中調用

```python
# 在 nx_poc_actions.py 中
def run_activate_free_license_step(self, **kwargs):
    # 1. 開啟系統管理
    self.license_settings_page.open_system_administration()
    
    # 2. 切換到授權分頁
    self.license_settings_page.switch_to_license_tab()
    
    # 3. 啟用免費授權
    self.license_settings_page.click_activate_free_license()
    
    # 4. 確認授權
    self.license_settings_page.confirm_license_activation()
    
    # 5. 關閉視窗
    self.license_settings_page.close_system_administration()
```

### 執行測試

```bash
# 執行 Case 1-3 測試
python tests/test_case_1_3.py
```

## 📊 參數說明

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `use_menu` | bool | False | 是否使用左上角選單開啟系統管理 |

**使用範例：**

```python
# 使用 Server 右鍵（預設）
actions.run_activate_free_license_step()

# 使用左上角選單
actions.run_activate_free_license_step(use_menu=True)
```

## 🔄 流程圖

```
開始
  ↓
確保已登入 (run_ensure_login_step)
  ↓
右鍵點擊 Server / 點擊選單
  ↓
點擊「系統管理」
  ↓
等待系統管理視窗開啟
  ↓
切換到「授權」分頁
  ↓
點擊「啟用免費授權」按鈕
  ↓
等待授權處理 (2秒)
  ↓
確認授權成功彈窗 (點擊 OK)
  ↓
顯示授權碼
  ↓
關閉系統管理視窗 (點擊 OK)
  ↓
完成 ✅
```

## 🎨 UI 元素定位

### 系統管理視窗

| 元素 | 定位方式 | 座標/偏移 |
|------|---------|----------|
| Server 圖示 | 圖片 + OCR | `x=0.08, y=0.08` |
| 右鍵選單 | 相對偏移 | `y_offset=70` (第2項) |
| 授權分頁 | OCR + 座標 | `x=0.25, y=0.09` |
| 啟用授權按鈕 | OCR | `x=0.5, y=0.45` |
| 確認按鈕 | OCR | `x=0.65, y=0.85` |
| 關閉按鈕 | OCR | `x=0.72, y=0.95` |

## 🧪 測試驗證

### 成功標準

- ✅ 成功開啟系統管理視窗
- ✅ 成功切換到授權分頁
- ✅ 成功點擊啟用免費授權按鈕
- ✅ 檢測到授權啟動成功彈窗
- ✅ 授權碼顯示在授權分頁
- ✅ 系統管理視窗正確關閉

### 錯誤處理

| 錯誤情況 | 處理方式 |
|---------|---------|
| 系統管理視窗開啟失敗 | 記錄錯誤並返回 |
| 授權分頁切換失敗 | 記錄警告並繼續 |
| 授權已啟用 | 自動跳過確認彈窗 |
| 視窗關閉失敗 | 記錄警告 |

## 📝 日誌輸出範例

```
🎬 執行 Case 1-3: 啟用免費錄製授權
🖱️ 在 Server 上右鍵開啟系統管理...
✅ 成功點擊系統管理選項
✅ 系統管理視窗已開啟: 站點管理 - Nx Witness Client
🖱️ 點擊「授權」分頁...
✅ 成功切換到授權分頁
🖱️ 點擊「啟用免費授權」按鈕...
✅ 成功點擊啟用免費授權按鈕
🖱️ 確認授權啟動...
✅ 已確認授權啟動
🖱️ 關閉系統管理視窗...
✅ 成功關閉系統管理視窗
✅ Case 1-3 完成：免費授權已啟用
```

## 🎯 與現有架構的整合

### 遵循分層架構

```
actions/nx_poc_actions.py          # 業務邏輯層
    ↓ 調用
pages/desktop/license_settings_page.py  # 頁面操作層
    ↓ 調用
base/desktop_app.py                # 基礎操作層
```

### 使用 Base 層方法

所有點擊操作都使用 `DesktopApp` 提供的方法：
- ✅ `smart_click()` - 智能點擊（圖片 > OCR > 座標）
- ✅ `wait_for_window()` - 等待視窗開啟
- ✅ `wait_for_window_close()` - 等待視窗關閉
- ✅ `wait_for_screen_change()` - 等待畫面變化

## 🚀 後續優化建議

1. **圖片資源準備**
   - 截取「系統管理」選單項目圖片
   - 截取「授權」分頁圖片
   - 截取「啟用免費授權」按鈕圖片

2. **錯誤處理增強**
   - 檢測授權是否已啟用
   - 檢測授權碼是否有效
   - 處理網路連線失敗情況

3. **多語言支援**
   - 支援繁體中文、簡體中文、英文
   - 動態檢測 UI 語言

4. **驗證功能**
   - 讀取並驗證授權碼
   - 檢查授權有效期
   - 記錄授權資訊到日誌

## ✅ 實現完成清單

- [x] 建立 `LicenseSettingsPage` 類別
- [x] 實現開啟系統管理功能
- [x] 實現切換授權分頁功能
- [x] 實現啟用免費授權功能
- [x] 實現確認授權彈窗功能
- [x] 實現關閉系統管理功能
- [x] 整合到 `NxPocActions`
- [x] 建立測試腳本
- [x] 撰寫實現文件

---

**版本：** 1.0  
**日期：** 2026-01-16  
**狀態：** ✅ 實現完成，待測試驗證
