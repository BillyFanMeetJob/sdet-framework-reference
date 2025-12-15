# SDET Framework Reference

這是一套以 **Excel TestPlan / DataTable 驅動** 的 Selenium + pytest 自動化測試框架。  
專案重點不在單一測試腳本，而在於設計一個 **可擴充、可維護的測試執行引擎**。  
測試流程、步驟與參數由 Excel 定義，程式碼僅負責解析與執行。  
整體架構採 Engine / Action / Page 分層，**已可直接接入 CI / GitHub Actions**。

---

## CI / GitHub Actions（已實作）

本專案已整合 **GitHub Actions CI**，可在以下情境自動或手動觸發測試引擎：

- Push / Pull Request 至 main 分支
- 手動觸發（可指定 TestName 執行順序與環境）

CI 特色：
- 使用 **Headless Chrome** 執行 Selenium 測試
- 由 Excel（TestPlan / Translate）完整驅動流程
- 失敗自動截圖、完整 log，並上傳為 CI artifacts

### CI 參數說明
| 參數 | 說明 |
|----|----|
| TEST_NAMES | 以逗號分隔的 TestName 清單（順序即執行順序） |
| TEST_ENV | DEV / SIT / UAT / PROD |
| HEADLESS | 是否使用 Headless Browser（CI 預設 true） |

---

## 一、設計目標

- 將「測試流程」與「測試程式碼」解耦  
- 測試案例、流程、參數 **全部由 Excel 驅動**
- Action / Page / Engine 分層清楚，可長期維護
- 支援多環境（DEV / SIT / UAT / PROD）
- 可直接導入 CI，自動化回歸測試

---

## 二、設計原則（Design Philosophy）

- 我不是在寫測試腳本，而是在設計「測試執行引擎」
- 流程由 Excel 定義，程式僅負責解析與執行
- Engine / Action / Page 各層責任單一
- 架構設計以企業 CI / 回歸測試為導向

---

## 三、整體架構總覽

```
pytest
  |
  |-- tests/test_execution.py
        |
        |-- run_test_flow(test_name, browser)
              |
              |-- set_ctx(RunContext)
              |
              |-- load_test_plan(test_name)
              |     |
              |     |-- TestDir → FunctionalClassification
              |     |-- TestPlan Sheet → StepList
              |
              |-- StepTranslator(browser)
              |     |
              |     |-- Translate Sheet
              |     |-- FlowName → Action Method
              |
              |-- for step in StepList
                    |
                    |-- execute_step()
                          |
                          |-- Action(**params)
                                |
                                |-- Page Object
                                      |
                                      |-- Selenium Toolkit
```

---

## 四、專案目錄結構

```
sdet-framework-reference/
│
├── actions/
│   ├── login_actions.py
│   └── inventory_actions.py
│
├── base/
│   ├── browser.py
│   ├── base_page.py
│   └── base_action.py
│
├── config.py
│
├── engine/
│   ├── flow_runner.py
│   ├── runtime.py
│   ├── run_context.py
│   ├── testplan_loader.py
│   └── step_translator.py
│
├── pages/
│   ├── login_page.py
│   └── inventory_page.py
│
├── toolkit/
│   ├── datatable.py
│   ├── xpath.py
│   ├── web_toolkit.py
│   ├── logger.py
│   ├── funlib.py
│   └── types.py
│
├── tests/
│   ├── conftest.py
│   └── test_execution.py
│
├── logs/
│   └── test_run.log
│
└── DemoData/
    └── TestPlan.xlsx
```

---

## 五、核心模組說明

### 1. config.py（多環境設定）
- 支援 DEV / SIT / UAT / PROD
- 定義 BASE_URL / 帳密 / TESTPLANPATH
- 由 `ACTIVE_CONFIG` 指定當前環境

---

### 2. toolkit/datatable.py（UFT DataTable 重構）
- `DataTable`：管理多個 Sheet
- `SheetData`：每個 Sheet 對應一組 row dict
- 功能：
  - add_sheet_from_excel
  - set_current_row
  - get / iter_rows
- 具備欄位防呆（空白 / 重複）

---

### 3. engine/runtime.py（執行期 Context）
- 使用 `ContextVar` 保存 RunContext
- RunContext 包含：
  - DataTable
  - EnvConfig
- 所有 Loader / Translator / Action **一律從 runtime 取 config 與 datatable**

---

### 4. engine/testplan_loader.py
- 從 Excel 讀取：
  - TestDir：找流程分頁（FunctionalClassification）
  - TestPlan：組 StepList
- 支援 Params 字串解析：
  ```
  index=0; retry=true; amount=100
  ```

---

### 5. engine/step_translator.py
- 讀取 Translate Sheet
- 建立：
  ```
  FlowName → Action Method
  ```
- 檢查：
  - ActionKey 是否存在
  - ActionMethod 是否存在

---

### 6. engine/flow_runner.py
- 框架核心入口
- 負責：
  - 建立 RunContext
  - 載入 TestPlan
  - 翻譯 FlowName
  - 逐步執行 Action
- 每一步皆有 log 與例外處理

---

## 六、Action / Page 分層設計

### Action 層（流程 + 驗證）
- login_actions.py
- inventory_actions.py
- 特點：
  - 使用 BaseAction 統一 logger / config
  - 專注「流程語意」與 assert

### Page 層（UI 操作）
- login_page.py
- inventory_page.py
- 特點：
  - Locator 集中定義
  - 不寫 assert
  - 不直接操作 driver

---

## 七、pytest 整合

### conftest.py
- browser fixture：
  - 建立 / 回收 WebDriver
- pytest_runtest_makereport：
  - 測試失敗自動截圖
- **不依賴 RunContext / get_config（避免時序問題）**

### test_execution.py
```python
def test_execution(browser):
    run_test_flow("正常購物流程", browser)
```

只需指定 TestName，即可跑完整流程。

---

## 八、Excel TestPlan 設計概念

### TestDir
| TestName | FunctionalClassification |
|--------|---------------------------|
| 正常購物流程 | ShoppingFlow |

### TestPlan（ShoppingFlow）
| TestName | StepNo | FlowName | Params |
|--------|--------|----------|--------|
| 正常購物流程 | 1 | LoginSuccess | |
| 正常購物流程 | 2 | InventoryHasItems | |
| 正常購物流程 | 3 | AddItemToCart | index=0 |

### Translate
| FlowName | ActionKey | ActionMethod |
|--------|-----------|--------------|
| LoginSuccess | login | login_success |
| InventoryHasItems | inventory | inventory_has_items |
| AddItemToCart | inventory | add_item_to_cart |

---

## 九、適合對象

- SDET / Automation Engineer
- UFT 轉 Selenium 架構設計者
- 想展示「工程化測試框架」的面試作品

---

## 十、Roadmap / Next Steps

- pytest 多 TestName 批次執行（CI matrix）
- 測試報告（JUnit XML / Allure）
- API / Mobile Action 擴充

---

**Author**  
Billy Fan
