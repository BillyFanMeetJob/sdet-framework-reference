# Excel-Driven Test Automation Framework (SDET Reference)

This repository demonstrates an **Excel-driven test automation framework**
designed with an **execution-engine mindset**, not just isolated Selenium scripts.

It is inspired by real-world **UFT (Unified Functional Testing)** enterprise frameworks
and reimplemented using **Python + Selenium + pytest**, with **CI execution** in mind.

---

## Who Is This Repo For

- SDET / Automation Engineers transitioning from UFT to Selenium
- Engineers working on **enterprise / banking / regulated projects**
- Teams that require **Excel-based test control** instead of hard-coded scripts
- Interviewers who want to see **framework design thinking**, not just tool usage

---

## Core Design Philosophy

### Test Definition ≠ Test Execution

Test flows are defined in **Excel**.  
Python code only focuses on **loading, translating, and executing** those flows.

This keeps responsibilities clear:

- Excel: **What to test / execution order**
- Engine: **How to execute**
- Action / Page: **How the system behaves**

> 中文補充：  
> 這個設計不是教學範例，而是來自我實際在企業專案中使用  
> **UFT + DataTable + Business Flow** 的經驗。  
> 我刻意保留「流程由資料驅動，而非程式碼硬寫」的模式，  
> 讓測試流程可以被非開發人員（QA / BA）維護。

---

## Why Excel-Driven (Inspired by UFT)

In many enterprise projects (especially banking systems),
test cases and execution flows are maintained in Excel rather than source code.

This framework mirrors that reality:

- `TestDir` → controls which TestName maps to which flow sheet
- `TestPlan` → defines ordered steps (FlowName + Params)
- `Translate` → maps business flow names to Action methods

> 中文補充：  
> 這套 Excel 結構直接對應 UFT 的 DataTable + Flow 設計。  
> 在 Python 中，我將它拆解為：  
> - TestPlan Loader（讀流程）  
> - Step Translator（Flow → Action）  
> - Action Map（執行對照表）  
>  
> 目的不是炫技，而是讓 Selenium 也能落地在企業流程中。

---

## Framework Architecture

```
project-root/
│
├─ engine/              # Execution engine (runtime / flow runner)
│├─ runtime.py
│├─ run_context.py
│├─ testplan_loader.py
│├─ step_translator.py
│├─ flow_runner.py
│
├─ actions/             # Business actions (flow-level logic)
│├─ login_actions.py
│├─ inventory_actions.py
│
├─ pages/               # Page Objects
│├─ login_page.py
│├─ inventory_page.py
│
├─ base/                # Base abstractions
│├─ browser.py
│├─ base_page.py
│├─ base_action.py
│
├─ toolkit/             # Shared utilities
│├─ datatable.py
│├─ xpath.py
│├─ web_toolkit.py
│├─ logger.py
│├─ funlib.py
│├─ types.py
│
├─ tests/
│├─ conftest.py
│├─ test_execution.py
│
├─ config.py            # Multi-environment config (DEV / SIT / UAT / PROD)
├─ requirements.txt
└─ .github/workflows/ci.yml
```

---

## CI Execution (GitHub Actions)

This project is designed to be **CI-triggered**, not manually hard-coded.

### Key Environment Variables

- `TEST_NAMES`  
  Controls execution order from CI  
  Example:
  ```
  TEST_NAMES="正常購物流程,流程B"
  ```

- `HEADLESS=true`  
  Enables headless Chrome for CI environments

- `TEST_ENV=DEV | SIT | UAT | PROD`

> 中文補充：  
> CI 只負責「觸發測試引擎」，  
> 不關心每個案例怎麼寫，這是框架層該處理的事。

---

## Current Status

- Excel-driven execution engine: ✅
- Multi-environment config: ✅
- GitHub Actions CI: ✅
- Screenshot on failure: ✅
- Report module: ⏳ (planned)

> 中文說明：  
> 目前尚未加入報告模組，是刻意的設計階段切分。  
> 報告屬於「輸出層」，不影響執行引擎的正確性，  
> 後續可無痛接入 Allure / HTML Report。

---

## Interview Talking Point (30 seconds)

> This project is not about writing Selenium scripts.  
> It is about designing a test execution engine inspired by UFT,
> where test flows live in Excel and code only executes them.
>
> I focused on separation of responsibility, CI execution,
> and real enterprise constraints rather than demo-style automation.

---

## Note

Chinese explanations are intentionally included  
to preserve real enterprise context from previous UFT projects.
