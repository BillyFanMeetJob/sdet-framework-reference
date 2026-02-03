# VLM 自癒機制使用指南

## 📋 概述

VLM (Vision-Language Model) 自癒機制是一個智能的 UI 變動觀測系統，當自動化測試因元素定位失敗時，會自動：

1. 📸 截圖當前畫面
2. 🤖 調用 AI 視覺模型分析 UI 變化
3. 📝 記錄觀測結果到知識庫
4. 💡 提供修復建議和新的 ActionKey

## 🎯 核心功能

### 1. 自動觀測 (Auto-Observation)
當 `wait_for_element` 或 `click` 等操作超時時，自動觸發 VLM 分析。

### 2. 知識庫累積 (Knowledge Base)
所有觀測結果保存到 `logs/ai_intelligence/knowledge_base.json`，作為未來修改 TestPlan 的依據。

### 3. UI Drift 分析 (Drift Analysis)
使用 `tools/analyze_ui_drift.py` 對比知識庫與 TestPlan.xlsx，找出需要更新的 ActionKey。

## 🚀 快速開始

### 步驟 1: 啟用 VLM 學習模式

在 `config.py` 中設置：

```python
class DevConfig(BaseConfig):
    # 啟用 VLM 學習模式
    ENABLE_VLM_LEARNING = True
    
    # 配置 VLM API
    VLM_PROVIDER = "gemini"  # 或 "ollama", "openai"
    VLM_API_KEY = os.getenv("GEMINI_API_KEY", "")
    VLM_MODEL = "gemini-pro-vision"
```

或通過環境變數：

```bash
set ENABLE_VLM_LEARNING=true
set GEMINI_API_KEY=your_api_key_here
```

### 步驟 2: 運行測試

正常運行測試，當元素定位失敗時，VLM 會自動觸發：

```bash
python test_case_launcher.py
```

### 步驟 3: 查看 VLM 洞察

檢查日誌輸出：

```
[VLM-TRIGGER] 已截圖: logs/ai_intelligence/screenshots/failure_login_button_20260203_143022.png
[VLM-INSIGHT] 目標元素: login_button
  觀測狀態: obscured
  潛在變化: 偵測到系統彈窗遮擋了原本的 'login_button' 按鈕
  建議 ActionKey: close_version_update_dialog
  建議定位器: //button[contains(text(), 'OK')]
```

### 步驟 4: 分析 UI Drift

運行分析工具：

```bash
python tools/analyze_ui_drift.py
```

輸出報告：

```
📊 分析完成: 發現 3 個潛在偏離
📝 報告已保存: logs/ai_intelligence/ui_drift_report_20260203_143500.md
```

## 📁 文件結構

```
nxwitness-demo/
├── utils/
│   └── ai_vision_helper.py          # AI 視覺輔助模組
├── base/
│   └── base_page.py                 # 整合 VLM 觀測的 BasePage
├── tools/
│   └── analyze_ui_drift.py          # UI Drift 分析工具
├── logs/
│   └── ai_intelligence/
│       ├── knowledge_base.json      # 觀測知識庫
│       ├── screenshots/             # 失敗截圖
│       └── ui_drift_report_*.md     # Drift 分析報告
└── config.py                        # VLM 配置
```

## 🔧 進階配置

### 隨機掃描模式

即使操作成功，也會定期執行 VLM 掃描以更新知識庫：

```python
# config.py
VLM_RANDOM_SCAN_FREQUENCY = 10  # 每 10 次操作掃描 1 次
```

### 自定義 VLM Prompt

修改 `utils/ai_vision_helper.py` 中的 `_build_analysis_prompt()` 方法。

### 整合不同的 VLM 提供商

#### Gemini API

```python
def _call_gemini_api(self, screenshot_path: str, prompt: str) -> str:
    import google.generativeai as genai
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro-vision')
    
    image = PIL.Image.open(screenshot_path)
    response = model.generate_content([prompt, image])
    
    return response.text
```

#### Ollama (本地部署)

```python
def _call_ollama_api(self, screenshot_path: str, prompt: str) -> str:
    import requests
    
    with open(screenshot_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llava",
            "prompt": prompt,
            "images": [image_data]
        }
    )
    
    return response.json()["response"]
```

## 📊 VLM 回傳格式

```json
{
  "observed_elements": [
    {
      "label": "OK",
      "type": "button",
      "position": [800, 600],
      "confidence": 0.95
    }
  ],
  "target_element_status": "obscured",
  "potential_changes": "偵測到系統彈窗遮擋了目標按鈕",
  "recommended_action_key": "close_update_dialog",
  "recommended_locator": "//button[@id='closeDialog']",
  "incident_report": "非預期的系統更新彈窗導致元素不可見",
  "severity": "medium"
}
```

## 🎓 最佳實踐

### 1. 開發階段
- ✅ 啟用 VLM 學習模式
- ✅ 定期運行 UI Drift 分析
- ✅ 根據建議更新 TestPlan.xlsx

### 2. CI/CD 階段
- ❌ 關閉 VLM 學習模式（避免消耗 API Token）
- ✅ 使用已更新的 TestPlan.xlsx
- ✅ 僅在失敗時手動啟用 VLM 診斷

### 3. 知識庫維護
- 📅 每週檢查 `knowledge_base.json`
- 🔄 定期清理過時的觀測記錄
- 📈 追蹤 UI 變動趨勢

## ⚠️ 注意事項

1. **API 成本**: VLM 調用會消耗 API Token，建議僅在開發階段啟用
2. **隱私安全**: 截圖可能包含敏感信息，注意知識庫的存取權限
3. **性能影響**: VLM 分析需要 2-5 秒，會延長測試失敗的報錯時間
4. **網路依賴**: 需要穩定的網路連接來調用雲端 VLM API

## 🐛 故障排除

### VLM 未觸發

檢查配置：
```python
# 確認 ENABLE_VLM_LEARNING = True
from config import DevConfig
print(DevConfig.ENABLE_VLM_LEARNING)
```

### API 調用失敗

檢查 API Key：
```bash
echo %GEMINI_API_KEY%
```

### 知識庫未更新

檢查文件權限：
```bash
dir logs\ai_intelligence\knowledge_base.json
```

## 📚 相關文檔

- [BasePage API 文檔](./BASE_PAGE_API.md)
- [TestPlan 欄位規範](./TESTPLAN_SCHEMA.md)
- [AI Vision Helper API](./AI_VISION_API.md)

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進 VLM 機制！

---

**最後更新**: 2026-02-03  
**維護者**: SDET Team
