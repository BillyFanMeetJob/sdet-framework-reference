# 瀏覽器持久化測試指南

## 測試目標

驗證以下修復：
1. ✅ 瀏覽器完全最大化（視窗佔滿螢幕）
2. ✅ 內容填充整個視窗（無縮放、無留白）
3. ✅ 測試完成後瀏覽器保持打開
4. ✅ Case 2-2 能成功連接到 Case 2-1 的瀏覽器

## 測試步驟

### 步驟 1: 執行 Case 2-1

```bash
cd d:\nxwitness-demo
python TestCaseLauncher.exe
```

選擇：**進入 Nx Cloud**

### 步驟 2: 觀察日誌

在 `terminal_output.log` 中查找以下關鍵日誌：

#### 啟動階段
```
[BROWSER] 嘗試 Attach 模式: http://127.0.0.1:9222
[BROWSER] Attach 模式失敗: ...
[BROWSER] 嘗試 Launch 模式
[BROWSER] Playwright 實例已啟動（類別變數）
```

#### 最大化階段
```
[BROWSER] ✅ 瀏覽器已最大化
```

#### 視口同步階段
```
[BROWSER] ✅ 視口已強制同步: 1920x1080
```

#### 啟動成功
```
[BROWSER] ✅ Launch 成功
[PLAYWRIGHT] 模式: launch
```

#### 斷開連接階段
```
[BROWSER] Launch 模式：釋放連接（瀏覽器保持運行）
[BROWSER] ✅ 已釋放連接，瀏覽器保持運行
```

### 步驟 3: 驗證瀏覽器狀態

**檢查項目：**
1. ✅ 瀏覽器視窗完全最大化（佔滿整個螢幕）
2. ✅ 網頁內容填充整個視窗（無縮放、無留白、無黑邊）
3. ✅ 測試完成後瀏覽器保持打開（不自動關閉）
4. ✅ 沒有 EPIPE 錯誤

### 步驟 4: 執行 Case 2-2

**不要關閉瀏覽器！** 直接執行：

```bash
python TestCaseLauncher.exe
```

選擇：**調閱一個錄影事件回放**

### 步驟 5: 觀察 Case 2-2 日誌

在 `terminal_output.log` 中查找：

#### 連接階段
```
[BROWSER] 嘗試 Attach 模式: http://127.0.0.1:9222
[BROWSER] ✅ Attach 成功，找到目標頁面: https://...
```

#### 視口同步
```
[BROWSER] ✅ 視口已強制同步: 1920x1080
```

#### 連接成功
```
[PLAYWRIGHT] 模式: attach
```

### 步驟 6: 驗證 Case 2-2

**檢查項目：**
1. ✅ 成功連接到現有瀏覽器（Attach Mode）
2. ✅ 不需要重新登錄
3. ✅ 內容正常顯示（無縮放問題）
4. ✅ 測試完成後瀏覽器仍然保持打開

## 常見問題排查

### 問題 1: 瀏覽器被關閉

**症狀：**
- 測試完成後瀏覽器自動關閉
- 出現 EPIPE 錯誤

**檢查：**
```bash
# 搜尋日誌中是否有錯誤的 close() 調用
grep "browser.close()" terminal_output.log
grep "pw.stop()" terminal_output.log
```

**應該看到：**
```
[BROWSER] ✅ 已釋放連接，瀏覽器保持運行
```

### 問題 2: 內容縮放或留白

**症狀：**
- 瀏覽器最大化後，內容被縮放
- 內容周圍有黑邊或留白

**檢查：**
```bash
# 搜尋視口同步日誌
grep "視口已強制同步" terminal_output.log
```

**應該看到：**
```
[BROWSER] ✅ 視口已強制同步: 1920x1080
```

**如果沒有看到，檢查：**
1. `new_context` 是否設置了 `no_viewport=True`
2. `_force_sync_viewport` 是否被調用

### 問題 3: Case 2-2 無法連接

**症狀：**
- Case 2-2 啟動失敗
- 日誌顯示 "Attach 模式失敗"

**檢查：**
```bash
# 檢查 CDP 端口是否開啟
netstat -ano | findstr "9222"
```

**應該看到：**
```
TCP    127.0.0.1:9222    ...    LISTENING
```

**如果沒有，檢查：**
1. Case 2-1 是否成功啟動瀏覽器
2. 瀏覽器是否使用了 `--remote-debugging-port=9222` 參數

## 成功標準

### Case 2-1 成功標準

- [x] 瀏覽器完全最大化
- [x] 內容填充整個視窗（無縮放、無留白）
- [x] 測試完成後瀏覽器保持打開
- [x] 沒有 EPIPE 錯誤
- [x] 日誌顯示：`[BROWSER] ✅ 視口已強制同步: 1920x1080`
- [x] 日誌顯示：`[BROWSER] ✅ 已釋放連接，瀏覽器保持運行`

### Case 2-2 成功標準

- [x] 成功連接到現有瀏覽器（Attach Mode）
- [x] 日誌顯示：`[BROWSER] ✅ Attach 成功，找到目標頁面`
- [x] 不需要重新登錄
- [x] 內容正常顯示（無縮放問題）
- [x] 測試完成後瀏覽器仍然保持打開

## 日誌檢查清單

### 必須出現的日誌

```
✅ [BROWSER] Playwright 實例已啟動（類別變數）
✅ [BROWSER] ✅ 瀏覽器已最大化
✅ [BROWSER] ✅ 視口已強制同步: 1920x1080
✅ [BROWSER] ✅ Launch 成功
✅ [BROWSER] ✅ 已釋放連接，瀏覽器保持運行
```

### 不應該出現的日誌

```
❌ browser.close()
❌ pw.stop()
❌ EPIPE
❌ 同步視口失敗
```

## 快速驗證命令

```bash
# 檢查瀏覽器進程
tasklist | findstr "chrome.exe"

# 檢查 CDP 端口
netstat -ano | findstr "9222"

# 檢查日誌中的關鍵信息
findstr /C:"視口已強制同步" terminal_output.log
findstr /C:"已釋放連接" terminal_output.log
findstr /C:"EPIPE" terminal_output.log
```

---

**測試指南版本：** 1.0  
**創建時間：** 2026-01-31  
**適用於：** 單例模式瀏覽器管理器重構
