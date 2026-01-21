# Base 層方法快速參考卡

> 📍 位置：`base/desktop_app.py`

---

## 🖱️ 點擊操作

### `smart_click()`
**智能點擊（圖片/OCR/座標三級保底）**

```python
self.smart_click(
    x_ratio=0.5,              # 座標保底 X 比例 (0-1)
    y_ratio=0.5,              # 座標保底 Y 比例 (0-1)
    target_text="確認",        # OCR 尋找文字（可選）
    image_path="btn.png",     # 圖片路徑（可選）
    timeout=3,                # 超時時間（秒）
    clicks=1,                 # 點擊次數（1=單擊, 2=雙擊）
    click_type='left',        # 點擊類型（'left', 'right'）
    is_relative=False,        # 是否相對座標
    from_bottom=False         # 是否從底部對齊
)
```

**返回**: `True` (成功) / `False` (失敗)

---

## ☑️ Checkbox 操作

### `smart_checkbox()`
**智能勾選/取消勾選**

```python
self.smart_checkbox(
    x_ratio=0.3,                                    # 座標保底 X 比例
    y_ratio=0.4,                                    # 座標保底 Y 比例
    target_text="USB",                              # OCR 尋找文字
    image_path="checkbox.png",                      # Checkbox 圖片
    checked_image="checkbox_checked.png",           # 已勾選參考圖
    unchecked_image="checkbox_unchecked.png",       # 未勾選參考圖
    ensure_checked=True,                            # True=確保勾選, False=確保不勾選
    force_verify=False,                             # 強制驗證模式
    timeout=3
)
```

**返回**: `True` (成功) / `False` (失敗)

**特性**:
- 自動判斷當前狀態
- 只在需要時點擊
- 圖片辨識 + 像素分析

---

## ⌨️ 鍵盤操作

### `type_text()`
**輸入文字**

```python
self.type_text(
    text="1q2w!Q@W",     # 要輸入的文字
    interval=0.05        # 字元間隔（秒）
)
```

### `press_key()`
**按下按鍵**

```python
self.press_key('enter')    # 按 Enter
self.press_key('esc')      # 按 Esc
self.press_key('tab')      # 按 Tab
```

**支援按鍵**: `'enter'`, `'esc'`, `'tab'`, `'backspace'`, `'delete'`, `'space'`, 等

---

## 🪟 視窗管理

### `get_nx_window()`
**獲取主視窗**

```python
win = self.get_nx_window()
# 返回: pygetwindow 視窗物件或 None
```

### `activate_window()`
**啟動指定視窗**

```python
self.activate_window(window_obj)
# 返回: True (成功) / False (失敗)
```

### `find_window()`
**尋找符合條件的視窗**

```python
win = self.find_window(
    title_keywords=["密碼", "確認"],    # 標題關鍵字（任一匹配）
    max_width=600,                     # 最大寬度
    max_height=400,                    # 最大高度
    exclude_titles=["設定", "主視窗"]   # 排除的標題
)
# 返回: 視窗物件或 None
```

### `wait_for_window()`
**等待視窗出現**

```python
win = self.wait_for_window(
    window_titles=["Nx Witness", "設定"],
    timeout=3
)
# 返回: 視窗物件或 None
```

### `wait_for_window_close()`
**等待視窗關閉**

```python
self.wait_for_window_close(
    window_titles=["設定", "Server Settings"],
    timeout=2
)
# 返回: True (已關閉) / False (超時)
```

---

## 🔐 彈窗處理

### `handle_password_popup()`
**處理密碼確認彈窗**

```python
self.handle_password_popup(
    password="1q2w!Q@W",                         # 密碼
    popup_title_keywords=["確認密碼", "驗證"],    # 彈窗標題關鍵字
    input_x_ratio=0.5,                           # 輸入框 X 位置比例
    input_y_ratio=0.45                           # 輸入框 Y 位置比例
)
```

**返回**: `True` (成功) / `False` (失敗)

**處理流程**:
1. 尋找密碼彈窗
2. 啟動彈窗
3. 點擊輸入框
4. 輸入密碼
5. 按 Enter

---

## ⏳ 等待條件

### `wait_for_condition()`
**通用條件等待**

```python
def is_ready():
    # 自定義判斷邏輯
    return some_condition

self.wait_for_condition(
    condition_func=is_ready,
    timeout=3,
    check_interval=0.1
)
# 返回: True (條件滿足) / False (超時)
```

### `wait_for_screen_change()`
**等待螢幕變化**

```python
self.wait_for_screen_change(
    region=(x, y, width, height),  # 檢測區域
    threshold=100000,              # 變化閾值
    max_wait=1.0                   # 最大等待時間（秒）
)
# 返回: True (檢測到變化) / False (超時)
```

---

## 🔍 OCR 工具

### `_find_text_by_ocr()`
**OCR 文字定位**

```python
result = self._find_text_by_ocr(
    target_text="確認",
    region=(x, y, width, height)
)
# 返回: (center_x, center_y) 或 None
```

---

## 📋 使用範例

### 範例 1: 點擊按鈕

```python
# Page 層
def click_ok_button(self):
    return self.smart_click(
        x_ratio=0.8,
        y_ratio=0.9,
        target_text="確認",
        image_path="ok_btn.png",
        timeout=2
    )
```

### 範例 2: 勾選 Checkbox

```python
# Page 層
def enable_option(self):
    return self.smart_checkbox(
        x_ratio=0.3,
        y_ratio=0.4,
        target_text="啟用",
        image_path="option_checkbox.png",
        checked_image="checked.png",
        unchecked_image="unchecked.png",
        ensure_checked=True
    )
```

### 範例 3: 處理密碼彈窗

```python
# Page 層
def _handle_password(self):
    from config import EnvConfig
    return self.handle_password_popup(
        password=EnvConfig.ADMIN_PASSWORD,
        popup_title_keywords=["密碼"]
    )
```

### 範例 4: 右鍵點擊

```python
# Page 層
def right_click_item(self):
    return self.smart_click(
        x_ratio=0.1,
        y_ratio=0.2,
        target_text="項目",
        image_path="item.png",
        click_type='right'  # 右鍵
    )
```

### 範例 5: 雙擊項目

```python
# Page 層
def double_click_item(self):
    return self.smart_click(
        x_ratio=0.1,
        y_ratio=0.2,
        target_text="項目",
        image_path="item.png",
        clicks=2  # 雙擊
    )
```

---

## 🎯 最佳實踐

### ✅ 推薦

1. **優先使用 `smart_click`**，讓系統自動選擇最佳定位方式
2. **提供多種定位參數**（圖片 + 文字 + 座標）確保魯棒性
3. **使用語義化的方法名**（如 `click_ok_button` 而非 `click_button_1`）
4. **配置適當的 timeout**（複雜操作用 3-5 秒，簡單操作用 1-2 秒）

### ❌ 避免

1. ❌ 不要在 Page 層直接使用 `pyautogui`
2. ❌ 不要在 Page 層實現基本操作邏輯
3. ❌ 不要硬編碼絕對座標（用比例座標）
4. ❌ 不要跳過錯誤處理（檢查返回值）

---

## 🔗 相關文檔

- [分層架構說明](./分層架構說明.md)
- [重構完成總結](./重構完成總結.md)

---

**📅 最後更新**: 2026-01-14  
**📖 Base 層版本**: v2.0
