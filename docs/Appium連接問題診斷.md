# Appium WebDriver 連接超時問題診斷指南

## 🔍 問題現象

從測試日誌可以看到：
- ✅ Appium Server 已啟動（端口 4723 正常）
- ✅ Android 設備已連接（emulator-5554 device）
- ❌ 創建 WebDriver 實例時超時（120 秒）
- ⚠️ 期間一直顯示"無法檢查 Appium Server 狀態"

## 🔎 可能原因分析

### 1. Appium Server 處理連接時卡住
**症狀**：Server 狀態正常，但無法處理新的 session 請求

**檢查方法**：
```bash
# 檢查 Appium Server 日誌
# 查看是否有錯誤訊息或警告

# 檢查是否有現有 session
curl http://localhost:4723/sessions
```

### 2. 設備被其他 Session 占用
**症狀**：設備已連接，但無法創建新 session

**檢查方法**：
```bash
# 檢查現有 session
curl http://localhost:4723/sessions

# 如果有多個 session，需要先關閉
# 或者重啟 Appium Server
```

### 3. Capabilities 配置問題
**症狀**：Capabilities 設置不正確，導致 Appium 無法啟動 App

**檢查項目**：
- `app_package`: `com.networkoptix.nxwitness`
- `app_activity`: `com.nxvms.mobile.QnActivity`
- 確認 App 已安裝在設備上

### 4. Appium Server 版本兼容性
**症狀**：Appium 3.1.2 可能與某些配置不兼容

**解決方法**：
- 檢查 Appium 版本：`appium --version`
- 確認 UiAutomator2 驅動已安裝：`appium driver list`
- 更新到最新版本或使用穩定版本

### 5. 設備狀態問題
**症狀**：設備雖然連接，但可能未解鎖或未授權

**檢查方法**：
```bash
# 檢查設備狀態
adb devices -l

# 檢查設備是否解鎖
adb shell dumpsys window | grep mDreamingLockscreen

# 檢查 USB 調試授權
adb devices
# 如果顯示 "unauthorized"，需要在設備上點擊"允許 USB 調試"
```

## 🛠️ 診斷步驟

### 步驟 1: 檢查 Appium Server 日誌
查看 Appium Server 的輸出日誌，尋找錯誤訊息：
- 連接錯誤
- Session 創建失敗
- 設備通信問題

### 步驟 2: 檢查現有 Session
```bash
# 使用 curl 檢查
curl http://localhost:4723/sessions

# 或使用 Python
python -c "import requests; print(requests.get('http://localhost:4723/sessions').json())"
```

### 步驟 3: 手動測試連接
```python
from appium import webdriver
from appium.options.android import UiAutomator2Options

options = UiAutomator2Options()
options.platform_name = "Android"
options.device_name = "Android Device"
options.automation_name = "UIAutomator2"
options.app_package = "com.networkoptix.nxwitness"
options.app_activity = "com.nxvms.mobile.QnActivity"
options.no_reset = True

try:
    driver = webdriver.Remote('http://localhost:4723', options=options)
    print("連接成功！")
    driver.quit()
except Exception as e:
    print(f"連接失敗: {e}")
```

### 步驟 4: 檢查設備狀態
```bash
# 檢查設備詳細信息
adb devices -l

# 檢查 App 是否已安裝
adb shell pm list packages | grep nxwitness

# 檢查 App 的主 Activity
adb shell pm dump com.networkoptix.nxwitness | grep -A 5 "android.intent.action.MAIN"
```

### 步驟 5: 重啟服務
```bash
# 停止 Appium Server
# 在啟動 Appium 的終端按 Ctrl+C

# 重啟 Appium Server
appium

# 或使用 Test Case Launcher 的"停止 Appium Server"功能
```

## 🔧 改進建議

### 1. 添加更詳細的診斷信息
在 `mobile_toolkit.py` 中添加：
- Appium Server 日誌檢查
- 現有 Session 檢查
- 設備詳細狀態檢查
- Capabilities 驗證

### 2. 改進錯誤處理
- 捕獲更詳細的異常信息
- 提供具體的修復建議
- 自動嘗試修復常見問題

### 3. 添加重試機制
- 自動重試連接
- 清理舊 Session
- 重啟 Appium Server（可選）

### 4. 添加超時前的診斷
在超時前（例如 30 秒、60 秒）進行診斷檢查：
- 檢查 Appium Server 是否還在響應
- 檢查設備狀態
- 檢查是否有錯誤日誌

## 📋 快速檢查清單

- [ ] Appium Server 是否正常運行？
  ```bash
  curl http://localhost:4723/status
  ```

- [ ] 設備是否已連接？
  ```bash
  adb devices
  ```

- [ ] 設備是否已解鎖？
  - 手動解鎖設備屏幕

- [ ] USB 調試是否已授權？
  - 檢查設備上的授權提示

- [ ] 是否有現有 Session？
  ```bash
  curl http://localhost:4723/sessions
  ```

- [ ] App 是否已安裝？
  ```bash
  adb shell pm list packages | grep nxwitness
  ```

- [ ] Appium Server 日誌是否有錯誤？
  - 查看啟動 Appium Server 的終端輸出

- [ ] 嘗試重啟 Appium Server
  - 停止當前 Server
  - 重新啟動

## 🚀 建議的改進代碼

在 `mobile_toolkit.py` 的 `_create_driver` 函數中添加更詳細的錯誤捕獲：

```python
def _create_driver():
    try:
        # ... 現有代碼 ...
        
        # 嘗試創建 WebDriver
        driver_result[0] = webdriver.Remote(
            command_executor=server_url,
            options=options
        )
        
    except Exception as e:
        # 捕獲詳細錯誤信息
        error_type = type(e).__name__
        error_msg = str(e)
        
        # 記錄詳細錯誤
        logger.error(f"[MOBILE_TOOLKIT] [背景線程] WebDriver 創建失敗")
        logger.error(f"[MOBILE_TOOLKIT] 錯誤類型: {error_type}")
        logger.error(f"[MOBILE_TOOLKIT] 錯誤訊息: {error_msg}")
        
        # 如果是連接錯誤，提供診斷建議
        if "Connection" in error_type or "timeout" in error_msg.lower():
            logger.warning("[MOBILE_TOOLKIT] [診斷] 這可能是連接問題，請檢查：")
            logger.warning("  1. Appium Server 是否正常運行")
            logger.warning("  2. 設備是否已連接且已解鎖")
            logger.warning("  3. 是否有其他 Appium session 正在使用設備")
        
        driver_exception[0] = e
```

---

**最後更新**: 2026-01-23  
**問題狀態**: 待解決
