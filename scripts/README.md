# 🛠️ 工具腳本集合

## 📋 功能說明

### 1. 座標提取工具 (`extract_coordinates.py`)

自動從測試日誌中提取 UI 元件的比例座標，並生成座標庫文檔。

### 2. UI 樹狀結構傾倒工具 (`dump_ui_tree.py`)

使用 pywinauto 導出 Nx Witness 應用程式的 UI 元件結構，用於分析 UI 元件屬性。

---

## 🚀 快速使用

### 步驟 1：執行測試

```powershell
cd D:\nxwitness-demo
pytest tests/test_runner.py -s --test_name "自動登入伺服器並切換繁體中文"
```

### 步驟 2：提取座標

```powershell
# 使用預設日誌文件
python scripts/extract_coordinates.py

# 或指定日誌文件
python scripts/extract_coordinates.py logs/automation.log
```

### 步驟 3：查看結果

生成的文件：
- `座標庫.md` - Markdown 表格格式
- `coord_library.py` - Python 字典格式

---

## 📊 輸出範例

### Markdown 格式

```markdown
## ⚙️ 設置頁面

| 元件識別 | 類型 | x_ratio | y_ratio | 測試視窗 | 絕對座標 |
|---------|------|---------|---------|---------|----------|
| appearance_tab | 🖼️ 圖片 | 0.1523 | 0.1489 | 800x600 | (122, 89) |
```

### Python 格式

```python
COORD_LIBRARY = {
    'desktop_settings': {
        'appearance_tab': {
            'x_ratio': 0.1523,
            'y_ratio': 0.1489,
            'window_size': '800x600',
            'type': 'image'
        },
    },
}
```

---

## 🔧 使用座標庫

### 方式 1：手動複製

從日誌或 `座標庫.md` 中複製座標值：

```python
self.app.smart_click(
    x_ratio=0.1523,  # 從座標庫複製
    y_ratio=0.1489,
    image_path="desktop_settings/appearance_tab.png"
)
```

### 方式 2：Import 使用

```python
from coord_library import COORD_LIBRARY

coord = COORD_LIBRARY['desktop_settings']['appearance_tab']
self.app.smart_click(
    x_ratio=coord['x_ratio'],
    y_ratio=coord['y_ratio'],
    image_path="desktop_settings/appearance_tab.png"
)
```

---

## 📚 詳細文檔

- [自學習座標庫_快速開始.md](../自學習座標庫_快速開始.md)
- [自學習座標庫使用指南.md](../自學習座標庫使用指南.md)
- [自學習座標庫_實現說明.md](../自學習座標庫_實現說明.md)

---

---

## 🌳 UI 樹狀結構傾倒工具

### 功能說明

使用 pywinauto 導出 Nx Witness 應用程式的完整 UI 元件樹狀結構，用於分析 UI 元件屬性（如日曆、日期按鈕等）。

### 前置需求

```powershell
pip install pywinauto
```

### 使用步驟

#### 步驟 1：啟動 Nx Witness 應用程式

確保 Nx Witness 應用程式已經啟動，並且視窗標題包含 "Nx Witness"。

#### 步驟 2：執行傾倒腳本

```powershell
cd D:\nxwitness-demo
python scripts/dump_ui_tree.py
```

#### 步驟 3：查看輸出

腳本會生成 `nx_tree_dump.txt` 檔案，包含完整的 UI 元件樹狀結構（深度 10 層）。

#### 步驟 4：分析結果

將 `nx_tree_dump.txt` 提供給 AI，AI 會分析「日曆 (Calendar)」和「日期按鈕 (Date Button)」的精確 `child_window` 屬性組合。

### 輸出範例

```
ControlType: WindowControl - "Nx Witness Client"
  ├─ ControlType: PaneControl
  │   ├─ ControlType: CalendarControl - "日曆"
  │   │   ├─ ControlType: ButtonControl - "17"
  │   │   ├─ ControlType: ButtonControl - "18"
  │   │   └─ ...
```

### 錯誤處理

- 如果找不到視窗，腳本會提示檢查應用程式是否已啟動
- 支援 uia 和 win32 兩種 backend，自動切換
- 包含詳細的錯誤訊息和除錯資訊

---

**🎯 開始建立您的座標庫！**
