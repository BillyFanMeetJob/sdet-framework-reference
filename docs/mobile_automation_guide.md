# Nx Witness 移動端自動化測試指南

## 概述

本文檔說明如何使用移動端自動化測試框架來執行 Nx Witness Android App 的自動化測試。

## 架構設計

### 1. Page Object Model (POM) 模式

所有移動端 Page Object 都位於 `pages/mobile/` 目錄下：

- **`base_mobile_page.py`**: 移動端 Page Object 基類，提供統一的移動端操作接口
- **`login_page.py`**: 登錄頁面，處理 Test Case 4-1
- **`main_page.py`**: 主頁面，處理服務器和攝像頭選擇
- **`playback_page.py`**: 播放頁面，處理日曆控件和視頻播放

### 2. Action 層

`actions/nx_mobile_actions.py` 協調各個 Page Object 完成測試流程。

### 3. 測試用例

- **`tests/test_case_4_1.py`**: Test Case 4-1 - 登錄到 Nx Cloud
- **`tests/test_case_4_2.py`**: Test Case 4-2 - 選擇服務器和攝像頭，使用日曆控件播放錄製的視頻

## 配置說明

### 1. 更新 `config.py`

在 `config.py` 中配置以下參數：

```python
# Appium Server 配置
APPIUM_SERVER_URL = "http://localhost:4723"  # Appium Server 地址
APPIUM_COMMAND_TIMEOUT = 300  # Appium 命令超時時間（秒）

# Android 設備配置
ANDROID_PLATFORM_VERSION = "11.0"  # Android 版本
ANDROID_DEVICE_NAME = "Android Device"  # 設備名稱
ANDROID_UDID = None  # 設備 UDID（如果為 None，則使用第一個連接的設備）
ANDROID_AUTOMATION_NAME = "UiAutomator2"  # 自動化引擎

# Nx Witness App 配置
ANDROID_APP_PACKAGE = "com.networkoptix.nxwitness.mobile"  # App Package Name
ANDROID_APP_ACTIVITY = "com.networkoptix.nxwitness.mobile.ui.login.LoginActivity"  # 啟動 Activity
ANDROID_APP_PATH = None  # APK 文件路徑（如果為 None，則使用已安裝的 App）

# Android 等待超時配置
ANDROID_DEFAULT_TIMEOUT = 10  # 默認等待超時時間（秒）
ANDROID_IMPLICIT_WAIT = 5  # 隱式等待時間（秒）
```

### 2. 更新 Resource ID

**重要**: 實際的 Android Resource ID 需要根據真實的 App 進行調整。

在以下文件中更新 Resource ID：

- `pages/mobile/login_page.py`: 登錄相關元素的 Resource ID
- `pages/mobile/main_page.py`: 主頁面相關元素的 Resource ID
- `pages/mobile/playback_page.py`: 播放頁面相關元素的 Resource ID

### 3. 獲取 Resource ID 的方法

使用以下工具獲取 App 的 Resource ID：

1. **Appium Inspector**: 官方工具，可以查看元素的 Resource ID
2. **UI Automator Viewer**: Android SDK 工具
3. **adb shell uiautomator dump**: 命令行工具

## 環境準備

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

確保 `Appium-Python-Client>=2.11.0` 已安裝。

### 2. 啟動 Appium Server

```bash
# 使用 npm 安裝 Appium
npm install -g appium

# 啟動 Appium Server
appium
```

Appium Server 默認運行在 `http://localhost:4723`。

### 3. 連接 Android 設備

#### 使用真實設備

1. 在 Android 設備上啟用「開發者選項」
2. 啟用「USB 調試」
3. 使用 USB 線連接設備到電腦
4. 運行 `adb devices` 確認設備已連接

#### 使用模擬器

1. 啟動 Android 模擬器（例如：Android Studio AVD）
2. 運行 `adb devices` 確認模擬器已連接

### 4. 安裝 Nx Witness App

確保 Nx Witness App 已安裝在設備/模擬器上，或者提供 APK 路徑在 `config.py` 中配置 `ANDROID_APP_PATH`。

## 運行測試

### 1. 運行 Test Case 4-1

```bash
# 運行登錄測試
pytest tests/test_case_4_1.py -v -s

# 或使用 Python
python -m pytest tests/test_case_4_1.py -v -s
```

### 2. 運行 Test Case 4-2

```bash
# 運行播放測試（完整流程）
pytest tests/test_case_4_2.py::test_case_4_2_full_flow -v -s

# 或運行部分測試
pytest tests/test_case_4_2.py::test_case_4_2_select_server_and_camera -v -s
pytest tests/test_case_4_2.py::test_case_4_2_playback_with_calendar -v -s
```

### 3. 運行所有移動端測試

```bash
pytest tests/test_case_4_1.py tests/test_case_4_2.py -v -s
```

## 設計原則

### 1. SOLID 原則

- **SRP (單一職責原則)**: 每個 Page Object 只負責一個頁面的操作
- **OCP (開閉原則)**: Page Object 可擴展但不可修改
- **DIP (依賴倒置原則)**: 依賴 Appium WebDriver 抽象，而非具體實現

### 2. Type Hinting

所有方法都使用 Type Hints，例如：

```python
def click_by_id(self, resource_id: str, timeout: Optional[int] = None) -> bool:
    ...
```

### 3. 顯式等待

所有等待操作都使用 `WebDriverWait` 和 `expected_conditions`，**不使用 `time.sleep()`**。

### 4. Google-Style Docstrings

所有方法都包含完整的 Google-Style Docstrings，說明：
- 方法的功能
- 參數說明
- 返回值說明
- 可能的異常

### 5. 配置外部化

所有硬編碼的數據（郵箱、密碼、服務器名稱等）都從 `config.py` 讀取，**不硬編碼在代碼中**。

## 故障排除

### 1. Appium Server 連接失敗

**錯誤**: `Connection refused` 或 `Unable to connect to Appium server`

**解決方案**:
- 確認 Appium Server 已啟動: `appium`
- 確認 `APPIUM_SERVER_URL` 配置正確
- 檢查防火牆設置

### 2. 設備未連接

**錯誤**: `No devices found` 或 `Unable to find device`

**解決方案**:
- 運行 `adb devices` 確認設備已連接
- 確認設備已解鎖且允許 USB 調試
- 如果使用模擬器，確認模擬器已啟動

### 3. App 啟動失敗

**錯誤**: `Unable to launch app` 或 `App not found`

**解決方案**:
- 確認 `ANDROID_APP_PACKAGE` 和 `ANDROID_APP_ACTIVITY` 配置正確
- 確認 App 已安裝在設備上
- 如果使用 APK，確認 `ANDROID_APP_PATH` 路徑正確

### 4. 元素定位失敗

**錯誤**: `Element not found` 或 `TimeoutException`

**解決方案**:
- 使用 Appium Inspector 確認元素的 Resource ID 或文字
- 更新對應的 Page Object 中的 Locator
- 增加超時時間（如果元素載入較慢）
- 確認元素是否在可見區域內（可能需要滑動）

## 擴展指南

### 添加新的 Page Object

1. 在 `pages/mobile/` 目錄下創建新的 Page Object 文件
2. 繼承 `BaseMobilePage`
3. 實現頁面特定的操作方法
4. 使用 Google-Style Docstrings 文檔化所有方法

### 添加新的測試用例

1. 在 `tests/` 目錄下創建新的測試文件
2. 使用 `mobile_driver` fixture 獲取 Appium WebDriver
3. 使用 `mobile_actions` fixture 獲取 NxMobileActions 實例
4. 編寫測試函數，使用 `pytest` 裝飾器

## 注意事項

1. **Resource ID 需要根據實際 App 調整**: 代碼中的 Resource ID 是示例，需要根據真實的 App 進行更新。

2. **文字定位的語言**: 如果 App 支持多語言，需要考慮文字定位的語言問題。建議優先使用 Resource ID 定位。

3. **等待時間**: 某些操作可能需要較長的等待時間（例如：視頻載入），可以適當增加超時時間。

4. **設備兼容性**: 不同設備的屏幕尺寸和分辨率可能不同，某些操作（例如：滑動）可能需要調整座標。

## 參考資料

- [Appium 官方文檔](http://appium.io/docs/en/about-appium/intro/)
- [Appium Python Client 文檔](https://github.com/appium/python-client)
- [Selenium WebDriver 文檔](https://www.selenium.dev/documentation/)
- [pytest 文檔](https://docs.pytest.org/)
