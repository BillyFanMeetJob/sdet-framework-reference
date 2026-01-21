# 測試案例啟動器 - EXE 打包說明

## 概述

將 `test_case_launcher.py` 打包成可執行檔案 (`.exe`)，無需安裝 Python 即可直接運行。

## 快速打包

### 方法一：使用自動打包腳本（推薦）

```bash
# 執行打包腳本
python build_exe.py
```

打包完成後，EXE 檔案位於 `dist\TestCaseLauncher.exe`

### 方法二：使用 PyInstaller 直接打包

```bash
# 1. 安裝 PyInstaller（如未安裝）
pip install pyinstaller

# 2. 打包成 EXE
pyinstaller --name TestCaseLauncher --onefile --windowed --noconfirm test_case_launcher.py
```

### 方法三：使用規格檔案（進階設定）

```bash
# 使用預設的 TestCaseLauncher.spec 檔案
pyinstaller TestCaseLauncher.spec
```

## 打包參數說明

| 參數 | 說明 |
|------|------|
| `--name TestCaseLauncher` | 輸出檔案名稱 |
| `--onefile` | 打包成單一執行檔（不生成資料夾） |
| `--windowed` | 不顯示控制台視窗（GUI 應用） |
| `--noconfirm` | 自動覆蓋已存在的檔案 |
| `--clean` | 清理暫存檔 |
| `--hidden-import` | 隱藏的匯入模組（確保包含所有依賴） |

## 打包後的檔案結構

```
nxwitness-demo/
├── dist/
│   └── TestCaseLauncher.exe  ← 這就是可執行的檔案！
├── build/                    ← 暫存檔案（可刪除）
└── TestCaseLauncher.spec     ← 規格檔案（可保留）
```

## 使用打包後的 EXE

### 1. 直接執行

雙擊 `dist\TestCaseLauncher.exe` 即可運行。

### 2. 分發給其他人

只需複製 `TestCaseLauncher.exe` 檔案即可，**不需要**：
- ❌ Python 環境
- ❌ 安裝任何套件
- ❌ 原始碼檔案

### 3. 注意事項

**重要**：EXE 檔案需要能訪問到 Excel 測試計劃檔案！

- 確保 `DemoData\TestPlan.xlsx` 存在於正確的路徑
- 或修改 `config.py` 中的 `TEST_PLAN_PATH` 設定
- 如果 Excel 檔案路徑不同，需要重新打包或使用相對路徑

## 檔案大小優化

如果 EXE 檔案太大，可以：

1. **排除不需要的模組**

編輯 `TestCaseLauncher.spec`，在 `excludes` 中添加不需要的套件：

```python
excludes=[
    'matplotlib',
    'numpy.testing',
    'scipy',
    'pytest',  # 如果不需要真實測試執行
]
```

2. **使用 UPX 壓縮**（可選）

```bash
# 下載 UPX: https://upx.github.io/
# 將 upx.exe 放在 PATH 中
# PyInstaller 會自動使用 UPX 壓縮
```

## 疑難排解

### 問題：打包失敗，提示缺少模組

**解決方案**：
```bash
# 確保所有依賴都已安裝
pip install -r requirements.txt
pip install pyinstaller
```

### 問題：EXE 執行時提示找不到模組

**解決方案**：
編輯 `TestCaseLauncher.spec`，在 `hiddenimports` 中添加缺少的模組。

### 問題：EXE 檔案太大（>100MB）

**解決方案**：
- 使用 `--exclude-module` 排除不需要的套件
- 使用 UPX 壓縮
- 使用 `--onedir` 代替 `--onefile`（會生成資料夾，但檔案較小）

### 問題：EXE 無法讀取 Excel 檔案

**解決方案**：
- 檢查 Excel 檔案路徑是否正確
- 確保 Excel 檔案未被其他程式鎖定
- 檢查檔案權限

## 進階設定

### 自訂圖示

1. 準備 `.ico` 圖示檔案（如 `icon.ico`）
2. 修改打包命令：

```bash
pyinstaller --icon=icon.ico --onefile --windowed test_case_launcher.py
```

或在 `TestCaseLauncher.spec` 中設定：

```python
icon='icon.ico'
```

### 版本資訊

創建 `version_info.txt` 並在打包時使用：

```bash
pyinstaller --version-file=version_info.txt test_case_launcher.py
```

## 測試打包後的 EXE

打包完成後，建議：

1. ✅ 在沒有 Python 的電腦上測試
2. ✅ 檢查所有功能是否正常
3. ✅ 確認 Excel 檔案讀取正常
4. ✅ 測試全選/全不選功能
5. ✅ 測試執行功能（模擬模式）

## 依賴套件

打包所需的最小依賴：

```
pyinstaller>=5.0.0
pandas>=2.0.0
openpyxl>=3.1.0
```

（tkinter 是 Python 標準庫，無需安裝）
