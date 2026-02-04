# VLM 自癒機制 - 快速開始

## 🎯 5 分鐘快速上手

### 1️⃣ 啟用 VLM 學習模式

**方法 A: 修改 config.py**
```python
class DevConfig(BaseConfig):
    ENABLE_VLM_LEARNING = True  # 改為 True
```

**方法 B: 設置環境變數**
```bash
# Windows
set ENABLE_VLM_LEARNING=true
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export ENABLE_VLM_LEARNING=true
export GEMINI_API_KEY=your_api_key_here
```

### 2️⃣ 運行測試

```bash
python test_case_launcher.py
```

### 3️⃣ 查看 VLM 洞察

當測試失敗時，日誌會顯示：

```
[VLM-TRIGGER] 已截圖: logs/ai_intelligence/screenshots/failure_login_button_20260203_143022.png
[VLM-INSIGHT] 目標元素: login_button
  觀測狀態: obscured
  潛在變化: 偵測到系統彈窗遮擋了原本的 'login_button' 按鈕
  建議 ActionKey: close_version_update_dialog
  建議定位器: //button[contains(text(), 'OK')]
```

### 4️⃣ 分析 UI Drift

```bash
python tools/analyze_ui_drift.py
```

查看報告：`logs/ai_intelligence/ui_drift_report_*.md`

### 5️⃣ 更新 TestPlan

根據報告建議，更新 `DemoData/TestPlan.xlsx` 的 Translate 表。

---

## 🧪 驗證安裝

運行測試腳本：

```bash
python tools/test_vlm_mechanism.py
```

預期輸出：

```
╔==========================================================╗
║               VLM 機制測試工具                           ║
╚==========================================================╝

測試 1: AI Helper 初始化
✅ AI Helper 初始化成功

測試 2: VLM 配置檢查
✅ VLM 配置讀取成功

測試 3: 知識庫文件檢查
✅ 知識庫文件存在

測試 4: 模擬元素定位失敗
✅ VLM 分析成功

測試 5: BasePage VLM 整合
✅ BasePage VLM 整合完整

通過: 5/5
🎉 所有測試通過！VLM 機制已正確配置。
```

---

## 📁 重要文件位置

| 文件 | 路徑 | 說明 |
|------|------|------|
| AI Helper | `utils/ai_vision_helper.py` | VLM 核心模組 |
| BasePage | `base/base_page.py` | 整合 VLM 觀測 |
| 配置 | `config.py` | VLM 開關和 API 設定 |
| 知識庫 | `logs/ai_intelligence/knowledge_base.json` | 觀測記錄 |
| Drift 工具 | `tools/analyze_ui_drift.py` | UI 偏離分析 |
| 測試工具 | `tools/test_vlm_mechanism.py` | 機制驗證 |
| 使用指南 | `docs/VLM_SELF_HEALING.md` | 完整文檔 |

---

## 💡 常見問題

### Q: VLM 會影響測試速度嗎？
A: 僅在元素定位失敗時觸發，不影響正常測試流程。分析耗時約 2-5 秒。

### Q: 需要付費 API 嗎？
A: 可選。支援免費的 Ollama 本地部署，或付費的 Gemini/OpenAI API。

### Q: 知識庫會很大嗎？
A: 每筆觀測約 1-2 KB，建議定期清理過時記錄。

### Q: 可以在 CI/CD 中使用嗎？
A: 建議在 CI 中關閉 VLM，僅在失敗時手動啟用診斷。

---

## 🎓 下一步

1. 閱讀完整文檔：[VLM_SELF_HEALING.md](./docs/VLM_SELF_HEALING.md)
2. 運行測試驗證：`python tools/test_vlm_mechanism.py`
3. 嘗試觸發 VLM：故意修改一個 XPath 讓測試失敗
4. 分析 UI Drift：`python tools/analyze_ui_drift.py`
5. 更新 TestPlan：根據 VLM 建議優化測試

---

**需要幫助？** 查看 [故障排除指南](./docs/VLM_SELF_HEALING.md#故障排除)
