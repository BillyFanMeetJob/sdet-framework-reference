# 📘 作品說明書（SDET Automation Framework）


# ⭐ 1. 作品名稱（Project Title）
**SDET Web UI Automation Framework — Selenium + Python + POM**

---

# ⭐ 2. 作品目的（Purpose）

此作品旨在展示我在 **SDET（Software Development Engineer in Test）** 領域的核心能力：

- 建立可維護、可擴充的自動化測試架構  
- 使用 Page Object Model 分層式設計  
- 自動化 Web UI 操作（登入、商品列表驗證、購物車驗證）  
- 撰寫工程化、模組化、具備高可讀性的測試程式  
- 為未來加入 CI/CD、多環境設定、錯誤截圖等企業需求打下基礎  

此作品可視為 **企業級 Automation Framework 的縮小版實作**。

---

# ⭐ 3. 作品範圍（Scope）

本框架目前已完成：

### ✅ 登入流程自動化（Login Flow）
- 自動輸入帳密  
- 驗證是否成功進入後台主頁  

### ✅ 商品頁自動化測試（Inventory Page）
- 取得商品名稱列表  
- 驗證商品卡片是否與名稱一致  

### ✅ 購物車流程（Cart Flow）
- 自動加入第一項商品  
- 驗證購物車徽章是否正確遞增  

### ✅ Logging + Screenshot + 可讀性輸出
- 輸出 Log 供偵錯使用  
- 支援未來加入錯誤截圖  

---

# ⭐ 4. 使用技術（Tech Stack）

| 技術 | 用途 |
|------|------|
| **Python 3.12** | 主要程式語言 |
| **Selenium 4** | 自動化瀏覽器操作 |
| **Page Object Model (POM)** | 減少重複程式碼、提高維護性 |
| **WebDriver Manager** | 自動下載 ChromeDriver |
| **Logging 模組** | 輸出測試執行紀錄 |
| **OOP 設計** | 可擴充的類別架構 |

---

# ⭐ 5. 系統架構（Architecture Overview）

```
sdet-training/
├── base/                 # Browser handler + BasePage
│   ├── browser.py
│   ├── basepage.py
│   └── logs/
│       └── test_run.log
│
├── toolkit/              # 工具層（通用功能）
│   ├── web_toolkit.py
│   └── logger.py
│
├── pages/                # Page Object Model 層
│   ├── login_page.py
│   └── inventory_page.py
│
├── tests/                # 測試案例層
│   ├── test_login.py
│   └── test_inventory.py
│
├── screenshots_DEV/      # 暫存截圖
├── config.py             # 多環境設定架構
└── README.md
```

---

# ⭐ 6. 設計理念（Design Principles）

### ✔ 分層式架構（Layered Architecture）
- **Base**：負責 Driver 管理、等待策略、基本操作
- **Toolkit**：提供通用行為（click、type、log）
- **Pages**：封裝 UI 元素與頁面邏輯
- **Tests**：只保留測試邏輯，簡潔易讀

### ✔ 高可維護性（Maintainability）
- POM 使得 UI 變動只需更新 Page 類別
- 測試程式不需修改 XPath 或 CSS

### ✔ 可擴充性（Extensibility）
未來可增加：
- API 測試整合  
- 測試報表（pytest + allure）  
- CI/CD 自動化跑測試  
- 錯誤截圖與 Retry 機制  

---

# ⭐ 7. 使用方式（How to Run）

### ▶ 安裝套件
```
pip install -r requirements.txt
```

### ▶ 執行登入測試
```
python -m tests.test_login
```

### ▶ 執行商品與購物車測試
```
python -m tests.test_inventory
```

---

# ⭐ 8. 作品亮點（Highlights）

### ✔ 架構完整，可作為企業框架基底  
不僅能跑測試，而是能「擴充」的框架。

### ✔ 測試程式乾淨、易讀、模組化  
工程化程度高，能清楚展示 SDET 必要能力。

### ✔ 具備真實應用場景（登入、商品列表、購物車）  
不是 Demo，而是可直接放入企業中調整後使用的架構。

---

# ⭐ 9. 作者角色（Your Role）

此作品完全由本人設計並實作，包括：

- 架構規劃（POM、Base、Toolkit）
- Selenium 自動化程式撰寫
- 測試案例編寫
- Logging 與架構優化
- 未來可延展的 CI/CD 與多環境設計

此專案展示了我具備進入 SDET / 測試開發工程師職位的核心能力。

---

# ⭐ 10. 未來規劃（Roadmap）

- [ ] 整合 pytest 測試框架  
- [ ] 自動報表 + Allure  
- [ ] Screenshot 錯誤截圖  
- [ ] 多環境參數 dev/uat/prod 擴充  
- [ ] GitHub Actions CI/CD 自動化流程  
- [ ] 整合 Mobile Web Selenium（第二作品）


