# -*- coding: utf-8 -*-
"""
VLM 引擎模組 - 統一視覺語言模型接口

實現 Ollama (主) 與 Gemini (備援) 的雙重策略，提供智能座標識別與驗證功能。

Author: SDET Team
Date: 2026-01-27
"""

import json
import os
import base64
import logging
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

from toolkit.types import Area, Toolkit
from toolkit.coordinate_validator import CoordinateValidator


@dataclass
class VLMResult:
    """VLM 識別結果。
    
    Attributes:
        coordinate: 識別到的座標 (x, y)
        description: VLM 對元素的描述
        confidence: 識別信心度（0-1）
        provider: 使用的 VLM 提供商（ollama/gemini）
        style_change: 是否檢測到樣式變化
        extracted_features: 提取的特徵列表
    """
    coordinate: Tuple[int, int]
    description: str
    confidence: float = 1.0
    provider: str = "unknown"
    style_change: bool = False
    extracted_features: List[str] = None
    
    def __post_init__(self):
        """初始化後處理。"""
        if self.extracted_features is None:
            self.extracted_features = []


class UnifiedVLM:
    """統一 VLM 接口，整合 Ollama 與 Gemini 雙重備援策略。
    
    核心功能：
    1. 主策略：使用 Ollama (Llama 3.2 Vision) 進行本地運算
    2. 備援策略：Ollama 失敗時自動切換至 Gemini 1.5 Flash
    3. 智能座標庫：自動縮放歷史座標，提供精準參考
    4. 雙重驗證：歐幾里得距離校驗 + 信心校驗機制
    5. 自動更新：精準識別結果自動寫入座標庫
    
    Attributes:
        threshold: 距離閾值（像素），預設 15
        logger: 日誌記錄器
        coordinate_library_path: 座標庫文件路徑
        validator: 座標驗證器實例
    """
    
    # 預設配置
    DEFAULT_THRESHOLD = 15.0  # 距離閾值（像素）
    COORDINATE_LIBRARY_PATH = "coordinate_library.json"
    
    # Ollama 配置
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.2-vision"  # Llama 3.2 Vision
    
    # Gemini 配置
    GEMINI_MODEL = "gemini-1.5-flash"  # 免費版
    GEMINI_PRO_MODEL = "gemini-1.5-pro"  # Pro 版（用於全局掃描）
    
    # 特徵進化配置
    STYLE_CHANGE_THRESHOLD = 5.0  # 樣式變化閾值（像素）
    MAJOR_CHANGE_THRESHOLD = 50.0  # 重大改版閾值（像素）
    GEMINI_PRO_MODEL = "gemini-1.5-pro"  # Pro 版（用於全局掃描）
    
    # 特徵進化配置
    STYLE_CHANGE_THRESHOLD = 5.0  # 樣式變化閾值（像素）
    MAJOR_CHANGE_THRESHOLD = 50.0  # 重大變化閾值（像素）
    
    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        logger: Optional[logging.Logger] = None,
        ollama_model: str = OLLAMA_MODEL,
        gemini_api_key: Optional[str] = None,
        enable_feature_evolution: bool = True
    ):
        """初始化 UnifiedVLM。
        
        Args:
            threshold: 距離閾值（像素）
            logger: 日誌記錄器
            ollama_model: Ollama 模型名稱
            gemini_api_key: Gemini API 金鑰（可選）
            enable_feature_evolution: 是否啟用特徵自進化（預設 True）
        """
        self.threshold = threshold
        self.logger = logger or self._create_default_logger()
        self.ollama_model = ollama_model
        self.gemini_api_key = gemini_api_key
        self.enable_feature_evolution = enable_feature_evolution
        
        # 初始化座標驗證器
        self.validator = CoordinateValidator(threshold=threshold, logger=self.logger)
        
        # 確保座標庫存在
        self._ensure_coordinate_library()
        
        self.logger.info(
            f"[VLM_ENGINE] 初始化完成 - Ollama: {ollama_model}, "
            f"閾值: {threshold}px, 特徵進化: {enable_feature_evolution}"
        )
    
    def _create_default_logger(self) -> logging.Logger:
        """創建預設日誌記錄器。
        
        Returns:
            配置好的 Logger 實例
        """
        logger = logging.getLogger("UnifiedVLM")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _ensure_coordinate_library(self) -> None:
        """確保座標庫文件存在。"""
        if not os.path.exists(self.COORDINATE_LIBRARY_PATH):
            with open(self.COORDINATE_LIBRARY_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "2.0",
                        "feature_evolution_enabled": self.enable_feature_evolution
                    },
                    "elements": {}
                }, f, ensure_ascii=False, indent=2)
            self.logger.info(f"[VLM_ENGINE] 創建座標庫: {self.COORDINATE_LIBRARY_PATH}")
    
    def find_element(
        self,
        element_name: str,
        screenshot_path: str,
        current_resolution: Tuple[int, int] = (1920, 1080),
        enable_description_calibration: bool = True
    ) -> Optional[Area]:
        """統一接口：尋找元素並返回 Area 物件。
        
        執行流程：
        1. 從座標庫讀取歷史數據
        2. 根據解析度縮放歷史座標
        3. 生成動態 Prompt（包含歷史參考和描述要求）
        4. 嘗試 Ollama 識別
        5. Ollama 失敗則備援至 Gemini
        6. 描述校正：驗證 VLM 描述是否符合預期特徵
        7. 驗證結果並更新座標庫
        
        Args:
            element_name: 元素名稱（如 "確認按鈕"、"登錄輸入框"）
            screenshot_path: 截圖文件路徑
            current_resolution: 當前螢幕解析度 (width, height)
            enable_description_calibration: 是否啟用描述校正（預設 True）
        
        Returns:
            Area 物件，包含識別到的區域座標；失敗返回 None
            
        Example:
            >>> vlm = UnifiedVLM()
            >>> area = vlm.find_element("確認按鈕", "screenshot.png")
            >>> if area:
            ...     print(f"找到按鈕位置: {area.center}")
        """
        self.logger.info(f"[VLM_ENGINE] 開始識別元素: {element_name}")
        
        # 步驟 1: 讀取歷史數據
        historical_data = self._load_historical_data(element_name)
        
        # 步驟 2: 縮放歷史座標
        normalized_coord = self._normalize_coords(
            historical_data,
            current_resolution
        ) if historical_data else None
        
        # 步驟 3: 生成動態 Prompt
        prompt = self._generate_prompt(
            element_name,
            normalized_coord,
            historical_data
        )
        
        # 步驟 4: 嘗試 Ollama 識別
        vlm_result = self._try_ollama(screenshot_path, prompt)
        
        # 步驟 5: Ollama 失敗則備援至 Gemini
        if vlm_result is None and self.gemini_api_key:
            self.logger.warning("[VLM_ENGINE] Ollama 失敗，切換至 Gemini 備援")
            vlm_result = self._try_gemini(screenshot_path, prompt)
        
        if vlm_result is None:
            self.logger.error(f"[VLM_ENGINE] 所有 VLM 策略失敗: {element_name}")
            return None
        
        # 步驟 6: 描述校正（如果啟用）
        if enable_description_calibration and historical_data:
            is_valid = self._verify_description(
                element_name,
                vlm_result,
                historical_data
            )
            
            if not is_valid:
                self.logger.warning(
                    f"[VLM_ENGINE] 描述校正失敗，觸發重新掃描: {element_name}"
                )
                # 重新掃描（不使用歷史參考）
                rescan_prompt = self._generate_prompt(element_name, None, None)
                vlm_result = self._try_ollama(screenshot_path, rescan_prompt)
                
                if vlm_result is None and self.gemini_api_key:
                    vlm_result = self._try_gemini(screenshot_path, rescan_prompt)
                
                if vlm_result is None:
                    self._log_failed_recognition(element_name, "重新掃描失敗", screenshot_path)
                    return None
        
        # 步驟 7: 驗證結果並更新座標庫（包含特徵進化）
        validated_area = self._validate_and_update(
            element_name,
            vlm_result,
            normalized_coord,
            current_resolution,
            historical_data
        )
        
        # 如果驗證失敗，記錄日誌
        if validated_area is None:
            self._log_failed_recognition(
                element_name,
                vlm_result.description,
                screenshot_path
            )
        
        return validated_area
    
    def _load_historical_data(self, element_name: str) -> Optional[Dict[str, Any]]:
        """從座標庫讀取歷史數據。
        
        Args:
            element_name: 元素名稱
        
        Returns:
            歷史數據字典，包含 avg_coord, resolution, neighbors 等；
            若無歷史數據返回 None
        """
        try:
            with open(self.COORDINATE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            elements = library.get("elements", {})
            if element_name in elements:
                data = elements[element_name]
                self.logger.debug(f"[VLM_ENGINE] 讀取歷史數據: {element_name} -> {data}")
                return data
            
            self.logger.debug(f"[VLM_ENGINE] 無歷史數據: {element_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 讀取座標庫失敗: {e}")
            return None
    
    def _normalize_coords(
        self,
        historical_data: Dict[str, Any],
        current_resolution: Tuple[int, int]
    ) -> Optional[Tuple[int, int]]:
        """自適應縮放：根據解析度比例縮放歷史座標。
        
        縮放算法：
        1. 讀取歷史記錄的解析度 (hist_w, hist_h)
        2. 計算縮放比例：
           - scale_x = current_w / hist_w
           - scale_y = current_h / hist_h
        3. 縮放座標：
           - new_x = hist_x * scale_x
           - new_y = hist_y * scale_y
        
        Args:
            historical_data: 歷史數據，包含 avg_coord 和 resolution
            current_resolution: 當前解析度 (width, height)
        
        Returns:
            縮放後的座標 (x, y)；若數據不完整返回 None
        """
        try:
            # 讀取歷史座標和解析度
            hist_coord = historical_data.get("avg_coord")
            hist_resolution = historical_data.get("resolution")
            
            if not hist_coord or not hist_resolution:
                self.logger.debug("[VLM_ENGINE] 歷史數據不完整，無法縮放")
                return None
            
            hist_x, hist_y = hist_coord
            hist_w, hist_h = hist_resolution
            curr_w, curr_h = current_resolution
            
            # 計算縮放比例
            scale_x = curr_w / hist_w
            scale_y = curr_h / hist_h
            
            # 縮放座標
            new_x = int(hist_x * scale_x)
            new_y = int(hist_y * scale_y)
            
            self.logger.debug(
                f"[VLM_ENGINE] 座標縮放: "
                f"({hist_x}, {hist_y}) @ {hist_resolution} -> "
                f"({new_x}, {new_y}) @ {current_resolution} "
                f"(scale: {scale_x:.2f}, {scale_y:.2f})"
            )
            
            return (new_x, new_y)
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 座標縮放失敗: {e}")
            return None
    
    def _generate_prompt(
        self,
        element_name: str,
        normalized_coord: Optional[Tuple[int, int]],
        historical_data: Optional[Dict[str, Any]],
        enable_feature_evolution: bool = True
    ) -> str:
        """生成動態 Prompt，包含多維度特徵注入。
        
        Prompt 結構：
        1. 任務描述：找到指定元素並描述其外觀
        2. 歷史參考：提供縮放後的參考座標（如果有）
        3. 多維度特徵：區分關鍵特徵和次要特徵
        4. 鄰近元素：描述相對位置關係（如果有）
        5. 容錯指引：允許次要特徵變化
        6. 輸出格式：要求返回 JSON 格式（包含 description 和 coordinate）
        
        Args:
            element_name: 元素名稱
            normalized_coord: 縮放後的歷史座標
            historical_data: 歷史數據（包含特徵和鄰近元素）
            enable_feature_evolution: 是否啟用特徵進化
        
        Returns:
            生成的 Prompt 字符串
        """
        prompt_parts = [
            f"請在截圖中找到「{element_name}」。",
            ""
        ]
        
        # 添加歷史參考座標
        if normalized_coord:
            x, y = normalized_coord
            prompt_parts.append(
                f"參考資訊：歷史記錄顯示此元素通常位於 ({x}, {y}) 附近。"
            )
        
        # 添加多維度特徵（關鍵特徵 vs 次要特徵）
        if historical_data and enable_feature_evolution:
            key_features = historical_data.get("key_features", "")
            secondary_features = historical_data.get("secondary_features", "")
            observed_features = historical_data.get("observed_features", [])
            
            if key_features or secondary_features:
                prompt_parts.append("特徵參考：")
                
                if key_features:
                    prompt_parts.append(f"  關鍵特徵（必須符合）: {key_features}")
                
                if secondary_features:
                    prompt_parts.append(f"  次要特徵（可能變化）: {secondary_features}")
                
                if observed_features:
                    prompt_parts.append(f"  歷史觀察特徵: {', '.join(observed_features[:5])}")
        elif historical_data and "expected_features" in historical_data:
            # 向後兼容：使用舊的 expected_features
            features = historical_data["expected_features"]
            if features:
                prompt_parts.append(f"預期特徵：{features}")
        
        # 添加鄰近元素信息
        if historical_data and "neighbors" in historical_data:
            neighbors = historical_data["neighbors"]
            if neighbors:
                prompt_parts.append("相對位置關係：")
                for neighbor in neighbors:
                    prompt_parts.append(f"  - {neighbor}")
        
        # 添加容錯指引（特徵進化）
        if enable_feature_evolution:
            prompt_parts.extend([
                "",
                "容錯規則：",
                "- 若次要特徵（如顏色）改變，但關鍵特徵（如形狀、文字）與位置吻合，仍需回傳座標",
                "- 若檢測到樣式變化，請在 description 開頭加上 [STYLE_CHANGE] 標記",
                "- 請列出你觀察到的所有特徵關鍵字"
            ])
        
        # 添加輸出格式要求（多模態輸出）
        prompt_parts.extend([
            "",
            "請按照以下步驟完成：",
            "1. 先描述你看到的元素的外觀（顏色、形狀、文字、圖示等）",
            "2. 描述元素與周邊的關係",
            "3. 給出元素中心的座標",
            "4. 列出觀察到的特徵關鍵字",
            "",
            "請以 JSON 格式返回結果：",
            '{',
            '  "description": "你看到的元素描述（若樣式改變請加 [STYLE_CHANGE]）",',
            '  "coordinate": {"x": <整數座標>, "y": <整數座標>},',
            '  "features": ["特徵1", "特徵2", ...]  // 可選',
            '}',
            "",
            "注意：",
            "1. 座標必須是整數",
            "2. 座標原點 (0,0) 在螢幕左上角",
            "3. description 必須詳細描述元素的視覺特徵",
            "4. 只返回 JSON，不要包含其他文字"
        ])
        
        return "\n".join(prompt_parts)
    
    def _try_ollama(
        self,
        screenshot_path: str,
        prompt: str
    ) -> Optional[VLMResult]:
        """嘗試使用 Ollama 進行識別。
        
        Args:
            screenshot_path: 截圖路徑
            prompt: 識別 Prompt
        
        Returns:
            VLMResult 物件，包含座標和描述；失敗返回 None
        """
        try:
            import requests
            
            # 讀取並編碼圖片
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 構建請求
            url = f"{self.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            }
            
            self.logger.debug(f"[VLM_ENGINE] 發送 Ollama 請求: {self.ollama_model}")
            
            # 發送請求
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            # 解析響應
            result = response.json()
            response_text = result.get("response", "")
            
            self.logger.debug(f"[VLM_ENGINE] Ollama 響應: {response_text}")
            
            # 解析 JSON 結果（包含描述和座標）
            vlm_result = self._parse_vlm_response(response_text, "ollama")
            
            if vlm_result:
                self.logger.info(
                    f"[VLM_ENGINE] Ollama 識別成功: {vlm_result.coordinate}, "
                    f"描述: {vlm_result.description[:50]}..."
                )
                return vlm_result
            
            self.logger.warning("[VLM_ENGINE] Ollama 響應格式無效")
            return None
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] Ollama 請求失敗: {e}")
            return None
    
    def _try_gemini(
        self,
        screenshot_path: str,
        prompt: str
    ) -> Optional[VLMResult]:
        """嘗試使用 Gemini 進行識別（備援策略）。
        
        Args:
            screenshot_path: 截圖路徑
            prompt: 識別 Prompt
        
        Returns:
            VLMResult 物件，包含座標和描述；失敗返回 None
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            # 配置 Gemini API
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.GEMINI_MODEL)
            
            # 讀取圖片
            image = Image.open(screenshot_path)
            
            self.logger.debug(f"[VLM_ENGINE] 發送 Gemini 請求: {self.GEMINI_MODEL}")
            
            # 發送請求
            response = model.generate_content([prompt, image])
            response_text = response.text
            
            self.logger.debug(f"[VLM_ENGINE] Gemini 響應: {response_text}")
            
            # 解析 JSON 結果（包含描述和座標）
            vlm_result = self._parse_vlm_response(response_text, "gemini")
            
            if vlm_result:
                self.logger.info(
                    f"[VLM_ENGINE] Gemini 識別成功: {vlm_result.coordinate}, "
                    f"描述: {vlm_result.description[:50]}..."
                )
                return vlm_result
            
            self.logger.warning("[VLM_ENGINE] Gemini 響應格式無效")
            return None
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] Gemini 請求失敗: {e}")
            return None
    
    def _parse_vlm_response(
        self,
        response_text: str,
        provider: str = "unknown"
    ) -> Optional[VLMResult]:
        """解析 VLM 響應中的完整結果（描述 + 座標 + 特徵）。
        
        支持的格式：
        1. 完整格式: {"description": "...", "coordinate": {"x": 100, "y": 200}, "features": [...]}
        2. 簡化格式: {"description": "...", "x": 100, "y": 200}
        3. 舊格式（向後兼容）: {"x": 100, "y": 200}
        
        Args:
            response_text: VLM 響應文本
            provider: VLM 提供商名稱
        
        Returns:
            VLMResult 物件；解析失敗返回 None
        """
        try:
            import re
            
            # 嘗試提取 JSON 塊
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\})?[^{}]*\}', response_text)
            if not json_match:
                # 嘗試舊格式（僅座標）
                coord = self._parse_coordinate_response(response_text)
                if coord:
                    return VLMResult(
                        coordinate=coord,
                        description="（無描述）",
                        provider=provider
                    )
                return None
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # 解析座標
            coord = None
            if "coordinate" in data and isinstance(data["coordinate"], dict):
                # 完整格式
                coord = (int(data["coordinate"]["x"]), int(data["coordinate"]["y"]))
            elif "x" in data and "y" in data:
                # 簡化格式或舊格式
                coord = (int(data["x"]), int(data["y"]))
            
            if not coord:
                return None
            
            # 解析描述
            description = data.get("description", "（無描述）")
            
            # 檢測樣式變化
            style_change = "[STYLE_CHANGE]" in description.upper()
            
            # 解析特徵列表
            extracted_features = data.get("features", [])
            if not extracted_features:
                # 從描述中自動提取
                extracted_features = self._extract_feature_list(description)
            
            return VLMResult(
                coordinate=coord,
                description=description,
                provider=provider,
                style_change=style_change,
                extracted_features=extracted_features
            )
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 解析 VLM 響應失敗: {e}")
            # 嘗試舊格式
            coord = self._parse_coordinate_response(response_text)
            if coord:
                return VLMResult(
                    coordinate=coord,
                    description="（無描述）",
                    provider=provider
                )
            return None
    
    def _parse_coordinate_response(self, response_text: str) -> Optional[Tuple[int, int]]:
        """解析 VLM 響應中的座標 JSON。
        
        支持的格式：
        1. 純 JSON: {"x": 100, "y": 200}
        2. Markdown 包裹: ```json\n{"x": 100, "y": 200}\n```
        3. 文字混合: 座標是 {"x": 100, "y": 200}
        
        Args:
            response_text: VLM 響應文本
        
        Returns:
            解析出的座標 (x, y)；失敗返回 None
        """
        try:
            # 嘗試提取 JSON 部分
            import re
            
            # 方法 1: 直接解析
            try:
                data = json.loads(response_text.strip())
                if "x" in data and "y" in data:
                    return (int(data["x"]), int(data["y"]))
            except:
                pass
            
            # 方法 2: 提取 JSON 塊
            json_match = re.search(r'\{[^}]*"x"[^}]*"y"[^}]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if "x" in data and "y" in data:
                    return (int(data["x"]), int(data["y"]))
            
            # 方法 3: 提取數字對
            numbers = re.findall(r'"x":\s*(\d+).*?"y":\s*(\d+)', response_text)
            if numbers:
                x, y = numbers[0]
                return (int(x), int(y))
            
            return None
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 解析座標失敗: {e}")
            return None
    
    def _verify_description(
        self,
        element_name: str,
        vlm_result: VLMResult,
        historical_data: Dict[str, Any]
    ) -> bool:
        """驗證 VLM 描述是否符合預期特徵（描述校正）。
        
        檢查 VLM 描述的特徵與座標庫中記錄的 expected_features 是否匹配。
        如果嚴重不符，返回 False 觸發重新掃描。
        
        Args:
            element_name: 元素名稱
            vlm_result: VLM 識別結果
            historical_data: 歷史數據（包含 expected_features）
        
        Returns:
            True 表示描述符合預期，False 表示需要重新掃描
        """
        expected_features = historical_data.get("expected_features", "")
        
        # 如果沒有預期特徵，直接通過
        if not expected_features:
            self.logger.debug(
                f"[VLM_ENGINE] 無預期特徵記錄，跳過描述校正: {element_name}"
            )
            return True
        
        description = vlm_result.description.lower()
        expected_features_lower = expected_features.lower()
        
        # 提取關鍵字
        expected_keywords = [
            kw.strip() 
            for kw in expected_features_lower.split(',') 
            if kw.strip()
        ]
        
        # 檢查是否包含至少一個關鍵字
        matched_keywords = [
            kw for kw in expected_keywords 
            if kw in description
        ]
        
        if not matched_keywords:
            self.logger.warning(
                f"[VLM_DESCRIPTION_MISMATCH] 元素 '{element_name}' 描述校正失敗\n"
                f"  預期特徵: {expected_features}\n"
                f"  VLM 描述: {vlm_result.description}\n"
                f"  匹配度: 0/{len(expected_keywords)}"
            )
            return False
        
        match_rate = len(matched_keywords) / len(expected_keywords)
        self.logger.info(
            f"[VLM_DESCRIPTION_OK] 元素 '{element_name}' 描述校正通過\n"
            f"  匹配關鍵字: {matched_keywords}\n"
            f"  匹配度: {match_rate:.1%}"
        )
        
        return True
    
    def _log_failed_recognition(
        self,
        element_name: str,
        description: str,
        screenshot_path: str
    ) -> None:
        """記錄識別失敗的詳細信息。
        
        將 VLM 的描述寫入日誌和錯誤報告，幫助診斷問題：
        - 是「沒看到物件」
        - 還是「誤認了其他物件」
        
        Args:
            element_name: 元素名稱
            description: VLM 的描述
            screenshot_path: 截圖路徑
        """
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "element_name": element_name,
            "screenshot": screenshot_path,
            "vlm_description": description,
            "status": "RECOGNITION_FAILED"
        }
        
        # 寫入錯誤日誌文件
        error_log_path = "vlm_recognition_errors.json"
        try:
            if os.path.exists(error_log_path):
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            errors.append(error_log)
            
            with open(error_log_path, 'w', encoding='utf-8') as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
            
            self.logger.error(
                f"[VLM_RECOGNITION_FAILED] 元素識別失敗: {element_name}\n"
                f"  截圖: {screenshot_path}\n"
                f"  VLM 描述: {description}\n"
                f"  錯誤日誌已寫入: {error_log_path}"
            )
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 寫入錯誤日誌失敗: {e}")
    
    def _validate_and_update(
        self,
        element_name: str,
        vlm_result: VLMResult,
        normalized_coord: Optional[Tuple[int, int]],
        current_resolution: Tuple[int, int],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Area]:
        """驗證 VLM 結果並更新座標庫。
        
        驗證流程：
        1. 如果有歷史座標，計算歐幾里得距離
        2. 距離 > 閾值：觸發信心校驗（二次確認）
        3. 距離 <= 閾值：視為精準識別，更新座標庫（包含描述）
        4. 返回 Area 物件
        
        Args:
            element_name: 元素名稱
            vlm_result: VLM 識別結果（包含座標和描述）
            normalized_coord: 縮放後的歷史座標
            current_resolution: 當前解析度
        
        Returns:
            Area 物件；驗證失敗返回 None
        """
        vlm_coord = vlm_result.coordinate
        
        # 如果有歷史座標，進行驗證
        if normalized_coord:
            distance = Toolkit.calculate_distance(vlm_coord, normalized_coord)
            
            self.logger.info(
                f"[VLM_ENGINE] 座標驗證: "
                f"VLM={vlm_coord}, 歷史={normalized_coord}, "
                f"距離={distance:.2f}px (閾值={self.threshold}px)"
            )
            
            # 距離超過閾值：觸發信心校驗
            if distance > self.threshold:
                self.logger.warning(
                    f"[VLM_DISCREPANCY_WARNING] 元素 '{element_name}' "
                    f"座標差異過大: {distance:.2f}px > {self.threshold}px"
                )
                
                # 觸發二次確認（信心校驗）
                confidence = self._confidence_check(
                    element_name,
                    vlm_coord,
                    normalized_coord,
                    vlm_result.description
                )
                
                if not confidence:
                    self.logger.error(
                        f"[VLM_ENGINE] 信心校驗失敗，拒絕使用 VLM 結果: {element_name}"
                    )
                    return None
            else:
                # 距離在閾值內：精準識別，更新座標庫
                self.logger.info(
                    f"[VLM_VALIDATION_OK] 元素 '{element_name}' 座標驗證通過"
                )
                self._update_coordinate_library(
                    element_name,
                    vlm_coord,
                    current_resolution,
                    vlm_result.description,
                    vlm_result
                )
        else:
            # 無歷史數據：直接接受並記錄
            self.logger.info(
                f"[VLM_ENGINE] 無歷史數據，直接接受 VLM 結果: {vlm_coord}"
            )
            self._update_coordinate_library(
                element_name,
                vlm_coord,
                current_resolution,
                vlm_result.description,
                vlm_result
            )
        
        # 創建 Area 物件（假設元素大小為 40x40）
        area = Toolkit.create_area_from_center(vlm_coord, width=40, height=40)
        
        return area
    
    def _confidence_check(
        self,
        element_name: str,
        vlm_coord: Tuple[int, int],
        expected_coord: Tuple[int, int],
        description: str = ""
    ) -> bool:
        """信心校驗：要求 VLM 解釋判斷理由。
        
        當座標差異過大時，觸發此方法進行二次確認。
        要求 VLM 描述：
        1. 為什麼選擇這個座標？
        2. 是否確認這是目標元素？
        3. 是否可能誤認了相似元素？
        
        Args:
            element_name: 元素名稱
            vlm_coord: VLM 識別的座標
            expected_coord: 預期座標（歷史座標）
            description: VLM 的描述（用於日誌）
        
        Returns:
            True 表示通過信心校驗，False 表示失敗
        """
        self.logger.info(
            f"[VLM_ENGINE] 觸發信心校驗: {element_name}\n"
            f"  VLM 描述: {description}"
        )
        
        # 構建二次確認 Prompt
        prompt = f"""
剛才識別「{element_name}」時，你給出的座標是 {vlm_coord}。
但歷史記錄顯示此元素通常位於 {expected_coord} 附近。

兩個座標相差較大，請重新檢查並回答：
1. 你選擇的座標 {vlm_coord} 是否確實是「{element_name}」？
2. 為什麼選擇這個位置？
3. 是否可能誤認了相似的元素？

請以 JSON 格式回答：
{{"confidence": true/false, "reason": "解釋原因"}}
"""
        
        # 這裡簡化處理：實際應該再次調用 VLM
        # 為了演示，我們假設如果距離 < 50px 就通過
        distance = Toolkit.calculate_distance(vlm_coord, expected_coord)
        
        if distance < 50:
            self.logger.info(f"[VLM_ENGINE] 信心校驗通過: 距離 {distance:.2f}px < 50px")
            return True
        else:
            self.logger.warning(f"[VLM_ENGINE] 信心校驗失敗: 距離 {distance:.2f}px >= 50px")
            return False
    
    def _update_coordinate_library(
        self,
        element_name: str,
        coord: Tuple[int, int],
        resolution: Tuple[int, int],
        description: str = "",
        vlm_result: Optional[VLMResult] = None
    ) -> None:
        """更新座標庫，增量寫入新數據（包含特徵進化）。
        
        更新策略：
        1. 讀取現有數據
        2. 計算新的平均座標（加權平均）
        3. 更新 observed_features（去重歸檔）
        4. 檢測樣式變化並更新活躍特徵
        5. 記錄解析度和最後描述
        6. 寫回文件
        
        Args:
            element_name: 元素名稱
            coord: 新座標
            resolution: 當前解析度
            description: VLM 的描述
            vlm_result: VLM 完整結果（包含提取的特徵）
        """
        try:
            # 讀取現有數據
            with open(self.COORDINATE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            elements = library.get("elements", {})
            
            # 如果元素已存在，計算加權平均
            if element_name in elements:
                existing = elements[element_name]
                old_coord = existing.get("avg_coord", coord)
                count = existing.get("count", 0)
                
                # 加權平均：(old * count + new) / (count + 1)
                new_x = int((old_coord[0] * count + coord[0]) / (count + 1))
                new_y = int((old_coord[1] * count + coord[1]) / (count + 1))
                
                # 更新 observed_features（特徵歸檔）
                observed_features = existing.get("observed_features", [])
                if vlm_result and vlm_result.extracted_features:
                    # 添加新特徵並去重
                    for feature in vlm_result.extracted_features:
                        if feature not in observed_features:
                            observed_features.append(feature)
                    # 限制最多保留 20 個特徵
                    observed_features = observed_features[-20:]
                
                # 檢測樣式變化並更新活躍特徵
                if vlm_result and vlm_result.style_change:
                    # 樣式變化：更新活躍特徵
                    key_features = existing.get("key_features", "")
                    secondary_features = self._extract_features(description)
                    
                    self.logger.info(
                        f"[FEATURE_EVOLUTION] 檢測到樣式變化: {element_name}\n"
                        f"  舊特徵: {existing.get('secondary_features', '')}\n"
                        f"  新特徵: {secondary_features}"
                    )
                else:
                    # 無樣式變化：保留現有特徵
                    key_features = existing.get("key_features", "")
                    secondary_features = existing.get("secondary_features", "")
                    
                    # 如果沒有設置，從描述中提取
                    if not secondary_features and description and description != "（無描述）":
                        secondary_features = self._extract_features(description)
                
                # 向後兼容：保留 expected_features
                expected_features = existing.get("expected_features", "")
                if not expected_features and description and description != "（無描述）":
                    expected_features = self._extract_features(description)
                
                elements[element_name] = {
                    "avg_coord": [new_x, new_y],
                    "resolution": list(resolution),
                    "count": count + 1,
                    "last_updated": datetime.now().isoformat(),
                    "last_description": description,
                    "expected_features": expected_features,  # 向後兼容
                    "key_features": key_features,  # 關鍵特徵
                    "secondary_features": secondary_features,  # 次要特徵（活躍）
                    "observed_features": observed_features,  # 歷史觀察特徵
                    "neighbors": existing.get("neighbors", [])
                }
                
                self.logger.debug(
                    f"[VLM_ENGINE] 更新座標庫: {element_name} -> "
                    f"({new_x}, {new_y}) [count={count + 1}]"
                )
            else:
                # 新元素，直接記錄
                expected_features = ""
                secondary_features = ""
                observed_features = []
                
                if description and description != "（無描述）":
                    expected_features = self._extract_features(description)
                    secondary_features = expected_features  # 初始時次要特徵 = 預期特徵
                
                if vlm_result and vlm_result.extracted_features:
                    observed_features = vlm_result.extracted_features[:20]
                
                elements[element_name] = {
                    "avg_coord": list(coord),
                    "resolution": list(resolution),
                    "count": 1,
                    "last_updated": datetime.now().isoformat(),
                    "last_description": description,
                    "expected_features": expected_features,  # 向後兼容
                    "key_features": "",  # 初始為空，需手動設置
                    "secondary_features": secondary_features,  # 次要特徵
                    "observed_features": observed_features,  # 歷史觀察特徵
                    "neighbors": []
                }
                
                self.logger.debug(
                    f"[VLM_ENGINE] 新增座標庫: {element_name} -> {coord}"
                )
            
            # 寫回文件
            library["elements"] = elements
            with open(self.COORDINATE_LIBRARY_PATH, 'w', encoding='utf-8') as f:
                json.dump(library, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 更新座標庫失敗: {e}")
    
    def _extract_feature_list(self, description: str) -> List[str]:
        """從 VLM 描述中提取特徵列表（用於 observed_features）。
        
        Args:
            description: VLM 的描述
        
        Returns:
            特徵列表
        """
        features = []
        description_lower = description.lower()
        
        # 關鍵詞庫
        all_keywords = {
            # 顏色
            '紅', '綠', '藍', '黃', '黑', '白', '灰', '橙', '紫', '粉',
            'red', 'green', 'blue', 'yellow', 'black', 'white', 'gray', 'orange', 'purple', 'pink',
            # 形狀
            '圓', '方', '矩形', '橢圓', '三角', '菱形',
            'round', 'square', 'rectangle', 'oval', 'triangle', 'diamond', 'button', 'icon', 'circle',
            # 文字和類型
            '文字', '標籤', '按鈕', '輸入框', '圖示', '符號', '確認', '取消',
            'text', 'label', 'button', 'input', 'icon', 'symbol', 'ok', 'cancel', 'confirm',
            # 狀態
            '啟用', '禁用', '選中', '未選中', '高亮', '暗淡',
            'enabled', 'disabled', 'selected', 'unselected', 'highlighted', 'dimmed'
        }
        
        for keyword in all_keywords:
            if keyword in description_lower:
                features.append(keyword)
        
        # 去重
        return list(dict.fromkeys(features))
    
    def _extract_features_list(self, description: str) -> List[str]:
        """從 VLM 描述中提取特徵列表。
        
        提取顏色、形狀、文字等關鍵詞作為特徵列表。
        
        Args:
            description: VLM 的描述
        
        Returns:
            提取的特徵列表
        """
        # 關鍵詞列表
        color_keywords = [
            '紅', '綠', '藍', '黃', '黑', '白', '灰', '橙', '紫', '粉',
            'red', 'green', 'blue', 'yellow', 'black', 'white', 'gray', 'orange', 'purple', 'pink'
        ]
        
        shape_keywords = [
            '圓', '方', '矩形', '橢圓', '三角', '菱形',
            'round', 'square', 'rectangle', 'oval', 'triangle', 'diamond', 'button', 'icon', 'circle'
        ]
        
        text_keywords = [
            '文字', '標籤', '按鈕', '輸入框', '圖示', '符號',
            'text', 'label', 'button', 'input', 'icon', 'symbol', '確認', '取消', 'OK', 'Cancel'
        ]
        
        found_features = []
        description_lower = description.lower()
        
        # 提取顏色
        for keyword in color_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 提取形狀
        for keyword in shape_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 提取文字關鍵詞
        for keyword in text_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 去重
        unique_features = list(dict.fromkeys(found_features))
        return unique_features[:10]  # 最多保留 10 個特徵
    
    def _extract_features(self, description: str) -> str:
        """從 VLM 描述中提取關鍵特徵。
        
        提取顏色、形狀、文字等關鍵詞作為預期特徵。
        
        Args:
            description: VLM 的描述
        
        Returns:
            提取的關鍵特徵字符串（逗號分隔）
        """
        # 關鍵詞列表
        color_keywords = [
            '紅', '綠', '藍', '黃', '黑', '白', '灰', '橙', '紫', '粉',
            'red', 'green', 'blue', 'yellow', 'black', 'white', 'gray', 'orange', 'purple', 'pink'
        ]
        
        shape_keywords = [
            '圓', '方', '矩形', '橢圓', '三角', '菱形',
            'round', 'square', 'rectangle', 'oval', 'triangle', 'diamond', 'button', 'icon'
        ]
        
        text_keywords = [
            '文字', '標籤', '按鈕', '輸入框', '圖示', '符號',
            'text', 'label', 'button', 'input', 'icon', 'symbol', '確認', '取消', 'OK', 'Cancel'
        ]
        
        found_features = []
        description_lower = description.lower()
        
        # 提取顏色
        for keyword in color_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 提取形狀
        for keyword in shape_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 提取文字關鍵詞
        for keyword in text_keywords:
            if keyword in description_lower:
                found_features.append(keyword)
        
        # 去重並返回
        unique_features = list(dict.fromkeys(found_features))
        return ', '.join(unique_features[:5])  # 最多保留 5 個特徵
    
    def _extract_key_features(self, features: List[str]) -> str:
        """從特徵列表中提取關鍵特徵（形狀、文字）。
        
        Args:
            features: 特徵列表
        
        Returns:
            關鍵特徵字符串（逗號分隔）
        """
        key_keywords = [
            '圓', '方', '矩形', '橢圓', '三角', '菱形',
            'round', 'square', 'rectangle', 'oval', 'triangle', 'diamond',
            'button', 'icon', 'input', 'text', 'label',
            '按鈕', '輸入框', '文字', '標籤', '圖示', '確認', '取消'
        ]
        
        key_features = [f for f in features if any(k in f.lower() for k in key_keywords)]
        return ', '.join(key_features[:3])  # 最多 3 個關鍵特徵
    
    def _extract_secondary_features(self, features: List[str]) -> str:
        """從特徵列表中提取次要特徵（顏色等）。
        
        Args:
            features: 特徵列表
        
        Returns:
            次要特徵字符串（逗號分隔）
        """
        color_keywords = [
            '紅', '綠', '藍', '黃', '黑', '白', '灰', '橙', '紫', '粉',
            'red', 'green', 'blue', 'yellow', 'black', 'white', 'gray', 'orange', 'purple', 'pink'
        ]
        
        secondary_features = [f for f in features if any(c in f.lower() for c in color_keywords)]
        return ', '.join(secondary_features[:3])  # 最多 3 個次要特徵
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取座標庫統計信息。
        
        Returns:
            統計信息字典，包含：
            - total_elements: 總元素數
            - total_records: 總記錄數
            - avg_accuracy: 平均精準度
        """
        try:
            with open(self.COORDINATE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            # 處理兩種格式：舊格式（list）和新格式（dict with elements）
            if isinstance(library, list):
                # 舊格式：直接是記錄列表
                return {
                    "total_elements": 0,
                    "total_records": len(library),
                    "elements": []
                }
            
            # 新格式：包含 elements 字典
            elements = library.get("elements", {})
            
            total_elements = len(elements)
            total_records = sum(e.get("count", 0) for e in elements.values())
            
            return {
                "total_elements": total_elements,
                "total_records": total_records,
                "elements": list(elements.keys())
            }
            
        except Exception as e:
            self.logger.error(f"[VLM_ENGINE] 獲取統計信息失敗: {e}")
            return {
                "total_elements": 0,
                "total_records": 0,
                "elements": []
            }


# 便捷函數
def create_vlm_engine(
    threshold: float = 15.0,
    logger: Optional[logging.Logger] = None,
    gemini_api_key: Optional[str] = None
) -> UnifiedVLM:
    """創建 UnifiedVLM 實例的便捷函數。
    
    自動從 config.py 讀取 Gemini API Key（如果未提供）。
    
    Args:
        threshold: 距離閾值
        logger: 日誌記錄器
        gemini_api_key: Gemini API 金鑰（可選，未提供時從 config 讀取）
    
    Returns:
        UnifiedVLM 實例
    """
    # 如果未提供 gemini_api_key，嘗試從 config 讀取
    if gemini_api_key is None:
        try:
            from config import EnvConfig
            gemini_api_key = getattr(EnvConfig, 'GEMINI_API_KEY', None)
            if gemini_api_key and logger:
                logger.info(f"[VLM_ENGINE] 從 config.py 讀取 Gemini API Key")
        except ImportError:
            if logger:
                logger.warning("[VLM_ENGINE] 無法導入 config.py，Gemini 備援功能將不可用")
    
    return UnifiedVLM(
        threshold=threshold,
        logger=logger,
        gemini_api_key=gemini_api_key
    )
