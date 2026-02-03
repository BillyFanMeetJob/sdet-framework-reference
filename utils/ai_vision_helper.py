# -*- coding: utf-8 -*-
"""
AI 視覺輔助模組 (VLM Integration)

透過 VLM (如 Gemini/Ollama) 對測試畫面進行語義分析，
用於 UI 變動紀錄與自動化修復建議。

Author: SDET Team
Date: 2026-02-03
"""

import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# 配置日誌
logger = logging.getLogger(__name__)


class AIVisionHelper:
    """
    提供基於視覺語言模型的螢幕分析功能
    
    用於在自動化測試失敗時，透過 VLM 分析畫面變化，
    並提供修復建議和 ActionKey 更新建議。
    
    Attributes:
        enabled (bool): 是否啟用 VLM 學習模式
        log_dir (Path): AI 分析結果存放目錄
        knowledge_base_path (Path): 知識庫 JSON 文件路徑
    """

    def __init__(self, log_dir: str = "logs/ai_intelligence"):
        """
        初始化 AI Vision Helper
        
        Args:
            log_dir: AI 分析結果存放目錄路徑
        """
        # 從環境變數或配置讀取開關
        self.enabled = os.getenv("ENABLE_VLM_LEARNING", "false").lower() == "true"
        self.log_dir = Path(log_dir)
        self.knowledge_base_path = self.log_dir / "knowledge_base.json"
        
        # 確保目錄存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化知識庫
        if not self.knowledge_base_path.exists():
            self._init_knowledge_base()
        
        logger.info(f"[AI_VISION] 初始化完成 (enabled={self.enabled})")

    def _init_knowledge_base(self) -> None:
        """初始化空的知識庫文件"""
        initial_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "description": "UI 變動觀測知識庫"
            },
            "observations": []
        }
        with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def _encode_image(self, image_path: str) -> str:
        """
        將截圖編碼為 Base64 格式
        
        Args:
            image_path: 圖片文件路徑
            
        Returns:
            Base64 編碼的圖片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _build_analysis_prompt(self, target_element: str) -> str:
        """
        構建 VLM 分析提示詞
        
        Args:
            target_element: 目標元素名稱（如 ActionKey）
            
        Returns:
            格式化的提示詞字符串
        """
        return f"""你是一位資深測試開發工程師 (SDET)，專精於 Nx Witness VMS 自動化測試維護。

當前情況：
- 自動化測試在執行 '{target_element}' 操作時失敗（元素定位超時）
- 需要你分析隨附的截圖，判斷 UI 是否發生變化

請仔細觀察截圖並回答：

1. **當前畫面描述**：
   - 畫面上有哪些主要 UI 元素？（標題、按鈕、輸入框、彈窗等）
   - 是否有非預期的彈窗或遮擋？

2. **目標元素分析**：
   - 原本要操作的 '{target_element}' 是否可見？
   - 如果不可見，是否有功能相似的替代按鈕？
   - 列出畫面上最顯眼的 5 個可點擊元素及其位置

3. **變化診斷**：
   - UI 與預期有什麼不同？（文字改變、位置偏移、解析度問題等）
   - 為什麼原本的定位會失敗？

4. **修復建議**：
   - 建議的新 ActionKey 名稱（如果需要更新）
   - 建議的定位策略（XPath、座標、圖像識別等）

**重要提示**：
- Nx Witness 桌面端使用 Qt 渲染
- 特別注意 "OK"、"Cancel"、"Apply"、"Connect"、"Login" 等常見按鈕
- 回傳格式必須是有效的 JSON

**回傳格式**：
{{
  "observed_elements": [
    {{"label": "按鈕文字", "type": "button", "position": [x, y], "confidence": 0.95}}
  ],
  "target_element_status": "not_found" | "found" | "obscured",
  "potential_changes": "描述 UI 變化的詳細說明",
  "recommended_action_key": "建議的新 ActionKey",
  "recommended_locator": "建議的定位方式",
  "incident_report": "失敗原因分析",
  "severity": "low" | "medium" | "high"
}}"""

    def analyze_failure(
        self, 
        screenshot_path: str, 
        target_element: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析測試失敗時的畫面，提供 UI 變動診斷
        
        Args:
            screenshot_path: 失敗時的截圖路徑
            target_element: 目標元素名稱（ActionKey）
            context: 額外上下文信息（如當前測試步驟、期望行為等）
            
        Returns:
            包含分析結果的字典，格式如下：
            {
                "timestamp": "ISO 時間戳",
                "target": "目標元素",
                "screenshot": "截圖路徑",
                "vlm_analysis": {...},  # VLM 回傳的 JSON
                "status": "success" | "error"
            }
            
        Raises:
            FileNotFoundError: 截圖文件不存在
        """
        if not self.enabled:
            logger.debug("[AI_VISION] VLM 學習模式未啟用，跳過分析")
            return {"status": "disabled"}
        
        if not os.path.exists(screenshot_path):
            logger.error(f"[AI_VISION] 截圖文件不存在: {screenshot_path}")
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
        
        logger.info(f"[AI_VISION] 開始分析失敗畫面: target={target_element}")
        
        try:
            # 構建提示詞
            prompt = self._build_analysis_prompt(target_element)
            
            # TODO: 實際調用 VLM API (Gemini/Ollama)
            # 這裡需要根據您使用的模型進行實現
            # 範例：
            # vlm_response = self._call_gemini_api(screenshot_path, prompt)
            # vlm_analysis = json.loads(vlm_response)
            
            # 模擬 VLM 回傳（實際使用時需替換）
            vlm_analysis = self._simulate_vlm_response(target_element)
            
            # 組裝完整結果
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "target": target_element,
                "screenshot": screenshot_path,
                "context": context or {},
                "vlm_analysis": vlm_analysis,
                "status": "success"
            }
            
            # 保存到知識庫
            self._save_to_knowledge_base(analysis_result)
            
            logger.info(f"[AI_VISION] ✅ 分析完成: {vlm_analysis.get('recommended_action_key', 'N/A')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"[AI_VISION] ❌ 分析失敗: {e}", exc_info=True)
            return {
                "timestamp": datetime.now().isoformat(),
                "target": target_element,
                "screenshot": screenshot_path,
                "status": "error",
                "error": str(e)
            }

    def _simulate_vlm_response(self, target_element: str) -> Dict[str, Any]:
        """
        模擬 VLM 回傳（用於開發測試）
        
        實際部署時應替換為真實的 VLM API 調用
        
        Args:
            target_element: 目標元素名稱
            
        Returns:
            模擬的 VLM 分析結果
        """
        return {
            "observed_elements": [
                {"label": "OK", "type": "button", "position": [800, 600], "confidence": 0.95},
                {"label": "Cancel", "type": "button", "position": [900, 600], "confidence": 0.92},
                {"label": "Version Update", "type": "dialog_title", "position": [640, 300], "confidence": 0.98}
            ],
            "target_element_status": "obscured",
            "potential_changes": f"偵測到系統彈窗遮擋了原本的 '{target_element}' 按鈕。彈窗標題為 'Version Update'，建議先關閉彈窗。",
            "recommended_action_key": "close_version_update_dialog",
            "recommended_locator": "//button[contains(text(), 'OK')] | //button[@id='closeDialog']",
            "incident_report": "原定位失敗原因：非預期的系統更新彈窗遮擋了目標按鈕，導致元素不可見。",
            "severity": "medium"
        }

    def _save_to_knowledge_base(self, analysis_result: Dict[str, Any]) -> None:
        """
        將分析結果保存到知識庫
        
        Args:
            analysis_result: 完整的分析結果字典
        """
        try:
            # 讀取現有知識庫
            with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
                knowledge_base = json.load(f)
            
            # 追加新觀測記錄
            knowledge_base["observations"].append(analysis_result)
            knowledge_base["metadata"]["last_updated"] = datetime.now().isoformat()
            knowledge_base["metadata"]["total_observations"] = len(knowledge_base["observations"])
            
            # 寫回文件
            with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"[AI_VISION] 已保存到知識庫: {self.knowledge_base_path}")
            
        except Exception as e:
            logger.error(f"[AI_VISION] 保存知識庫失敗: {e}", exc_info=True)

    def get_screen_analysis(
        self, 
        screenshot_path: str, 
        target_element: str
    ) -> Optional[Dict[str, Any]]:
        """
        便捷方法：獲取畫面分析結果
        
        這是一個簡化的接口，用於在 BasePage 中快速調用
        
        Args:
            screenshot_path: 截圖路徑
            target_element: 目標元素名稱
            
        Returns:
            VLM 分析結果，如果失敗則返回 None
        """
        try:
            result = self.analyze_failure(screenshot_path, target_element)
            return result.get("vlm_analysis") if result.get("status") == "success" else None
        except Exception as e:
            logger.error(f"[AI_VISION] get_screen_analysis 失敗: {e}")
            return None


# 全局單例
_ai_helper_instance: Optional[AIVisionHelper] = None


def get_ai_helper() -> AIVisionHelper:
    """
    獲取 AI Vision Helper 單例
    
    Returns:
        AIVisionHelper 實例
    """
    global _ai_helper_instance
    if _ai_helper_instance is None:
        _ai_helper_instance = AIVisionHelper()
    return _ai_helper_instance