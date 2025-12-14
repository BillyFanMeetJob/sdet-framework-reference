# SDET Web UI Automation Framework (Python + Selenium + Pytest)

> 作品定位：企業級 Web UI 自動化測試框架示範專案  
> 面試目標：SDET / 測試自動化工程師（期望薪資約 90K）

本專案以 [SauceDemo](https://www.saucedemo.com/) 為示範系統，展示如何從 0 設計並實作一套  
**具多環境設定、Page Object Model (POM)、pytest 測試框架、自動截圖機制** 的 Web UI 測試框架。

---

## 1. 專案結構

根目錄結構與實際程式碼對應如下：

```text
sdet-training/
│
├── base/                   # 框架基礎層：Browser 抽象、BasePage 共用操作
│   ├── __init__.py
│   ├── basepage.py         # BasePage：封裝共用元素操作、等待、截圖呼叫等
│   └── browser.py          # 建立與管理 Selenium WebDriver
│
├── pages/                  # Page Object 層（業務頁面封裝）
│   ├── __init__.py
│   ├── login_page.py       # LoginPage：登入頁面元素與操作
│   └── inventory_page.py   # InventoryPage：商品列表 / 購物車相關操作
│
├── tests/                  # 測試案例層（pytest）
│   ├── __init__.py
│   ├── conftest.py         # pytest fixtures：driver 建立、環境切換、自動截圖等集中管理
│   ├── test_login.py       # 登入相關測試案例
│   └── test_inventory.py   # 商品列表、加入購物車等測試案例
│
├── toolkit/                # 工具層（通用工具與輔助函式）
│   ├── __init__.py         
│   ├── logger.py			# log相关设定
│   └── web_toolkit.py		# 例如封裝 click / type / wait / logging / screenshot 等
│
├── config.py               # 多環境設定檔（DEV / SIT / UAT / PROD 等）
├── chromedriver.exe        # 本機開發用 WebDriver 執行檔（亦可改用 webdriver-manager）
├── .gitignore              # Git 忽略規則
└── README.md               # 本說明文件
```

> 專案分成 **base / pages / tests / toolkit / config** 五個層次，  
> 測試只負責描述「做什麼」、細節由 Page Object 與基礎工具處理。

---

## 2. 多環境設定（config.py）

`config.py` 負責集中管理所有環境相關參數，設計理念類似 UFT 的 Environment + 多組 XML：

- 使用 `@dataclass` 定義單一環境結構，例如：

  - `NAME`：環境名稱（DEV / SIT / UAT / PROD）
  - `BASE_URL`：站台網址
  - `USERNAME` / `PASSWORD`：預設測試帳號
- 定義多組環境實例：`DEV_CONFIG`、`SIT_CONFIG`、`UAT_CONFIG`、`PROD_CONFIG`
- 定義共用設定：
  - `DEFAULT_TIMEOUT`：顯性等待秒數
  - `HEADLESS`：是否啟用無頭模式
  - `SCREENSHOT_ROOT`：截圖儲存根目錄（預設 `<專案根目錄>/screenshots`）

程式使用方式（節錄）：

```python
from config import ACTIVE_CONFIG as C

def test_example(driver):
    driver.get(C.BASE_URL)
    # 使用 C.USERNAME / C.PASSWORD 等進行測試
```

> 說明重點：  
> - 測試程式不需要關心 URL 與帳密，全部從 `ACTIVE_CONFIG` 取得。  
> - 之後只需修改 `config.py` 或環境變數，即可切換 DEV / SIT / UAT / PROD。

---

## 3. 框架分層設計

### 3.1 base：Browser 與 BasePage

- `browser.py`
  - 統一建立 Selenium WebDriver（Chrome 為主，可擴充其他瀏覽器）
  - 負責設定 driver 參數（逾時、視窗大小、headless 等）
- `basepage.py`
  - 所有頁面的共同父類別
  - 封裝常用操作，如：
    - `find_element` / `find_elements`
    - 安全 click / type（內含等待）
    - 讀取文字、確認元素是否存在
    - 呼叫截圖與 logging

> 面試可說明：**任何新頁面只要繼承 BasePage，就能重用所有共用邏輯。**

---

### 3.2 pages：Page Object Model

目前已實作兩個主要頁面：

- `login_page.py`
  - 封裝登入頁元素 locator
  - 封裝動作方法：
    - `open()`：打開登入頁
    - `login(username, password)`：輸入帳密並送出
  - 可擴充驗證方法，例如：
    - 驗證錯誤訊息、登入按鈕狀態等

- `inventory_page.py`
  - 代表登入後的商品列表頁
  - 封裝功能包含：
    - 取得所有商品名稱列表
    - 點選商品、加入購物車
    - 驗證購物車徽章（badge）數字是否正確

> 設計重點：測試程式不直接操作 Selenium，而是呼叫 Page Object 的方法，  
> 例如 `inventory_page.add_to_cart("Sauce Labs Backpack")`。

---

### 3.3 toolkit：通用工具層

`toolkit/` 主要存放各種共用工具，供 base / pages / tests 使用，例如：

- 封裝 Selenium 常用操作（click / type / wait）
- 日誌紀錄（logging 設定）
- 截圖工具（依 `config.SCREENSHOT_ROOT` 存檔）

> 目的：將「技術性的細節」從 Page / Test 中抽離，降低重複與耦合。

---

### 3.4 tests：pytest 測試案例

`tests/` 資料夾以 pytest 傳統結構設計：

- `conftest.py`
  - 定義共用 fixtures，例如：
    - `driver`：建立與關閉瀏覽器
    - 依 `config.ACTIVE_CONFIG` 載入環境
    - 測試失敗時自動截圖，存到 `screenshots/` 以利除錯
- `test_login.py`
  - 測試成功登入
  - 測試錯誤帳密登入時的錯誤訊息等（可持續擴充）
- `test_inventory.py`
  - 測試登入後商品列表顯示是否正確
  - 測試加入多個商品到購物車，驗證徽章數量是否與實際加入數量一致

---

## 4. 如何在本機執行測試

### 4.1 安裝相依套件

建議使用虛擬環境（venv / conda），然後安裝 Selenium 等套件：

```bash
pip install selenium pytest
```

若專案中有 `requirements.txt`，亦可使用：

```bash
pip install -r requirements.txt
```

### 4.2 執行所有測試

於專案根目錄執行：

```bash
pytest -v
```

### 4.3 執行單一測試檔

```bash
pytest tests/test_login.py -v
pytest tests/test_inventory.py -v
```

> 測試執行完後，如有失敗案例，可在 `screenshots/`（或 `config.SCREENSHOT_ROOT`）中查看對應截圖。

---

## 5. 企業級實務考量

本專案雖然以示範為主，但設計上已考慮實務導入情境：

1. **多環境支援**  
   - 所有 URL / 帳密 / timeout / screenshot 目錄都集中在 `config.py`  
   - 日後導入 DEV / SIT / UAT / PROD 只需調整設定，不需改動測試程式

2. **架構可擴充**  
   - 新增頁面（Page）只要新增對應檔案並繼承 `BasePage`  
   - 新增測試只需在 `tests/` 中新增 `test_xxx.py` 並使用現有 fixtures

3. **易於整合 CI/CD**  
   - 使用 pytest：可直接接入 GitHub Actions / Jenkins / GitLab CI  
   - 日後可加入：
     - 測試報告（Allure / HTML）
     - 測試結果與截圖上傳到報告或測試管理系統

4. **程式碼可讀性與維護性**  
   - 明確分層與命名（base / pages / tests / toolkit / config）  
   - 測試檔聚焦在「行為與驗證」，不沾 Selenium 細節

---

## 6. 未來 Roadmap（強化為完整 SDET 作品）

可在後續開發中，依下列方向持續演進本專案：

- [ ] 完善測試資料管理（CSV / Excel / JSON / DB）  
- [ ] 導入測試報告系統（如 Allure、pytest-html）  
- [ ] 新增 API 測試模組（requests）並整合 UI + API 驗證  
- [ ] 支援多瀏覽器（Chrome / Edge / Firefox）與 headless 模式  
- [ ] 加入 CI/CD pipeline 範例（GitHub Actions / Jenkinsfile）  
- [ ] 與實際專案（如銀行、電商系統）對接，形成可重用的顧問級框架模板  

---

## 7. 本框架能展現的能力

此專案框架展示了以下工程化能力，面試時能有效證明候選人在自動化領域的深度：

1. **具備獨立設計企業級自動化框架的能力**  
	- 能從底層組件（BasePage、Browser Handler）建立框架基礎
	- 能將 Selenium 操作抽象化，避免測試程式出現過度重複邏輯
2. **具備大型專案經驗並能轉化成工程方法論**  
	- 將 UFT 一些成熟的做法（Environment、多層架構）轉換到 Python 生態系
	- 彌補許多使用 Selenium 生態常忽略的維運設計面
3. **清楚分層與降低耦合的設計能力**  
	- base / pages / tests / toolkit / config 的分層設計有助於長期維護
	- 測試碼只負責行為，不與 Selenium 元素操作耦合
4. **考慮企業導入場景與可擴充性**  
	- 框架預留多環境、多瀏覽器、CI/CD、測試報告整合空間
	- 模組化設計方便團隊協作與日後功能擴充
5. **能將不完整或混亂的自動化流程重新整理成框架**  
	- 若企業已有部分測試腳本，可基於此框架快速收斂
	- 若從零開始，也能當成自動化專案模板直接使用
