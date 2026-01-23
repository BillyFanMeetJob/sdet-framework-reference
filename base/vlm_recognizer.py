# -*- coding: utf-8 -*-
"""
VLM (Vision Language Model) 圖像辨識模組

支援多種 VLM 後端：
1. OpenAI GPT-4V (API)
2. Claude Vision (API)
3. Qwen-VL (本地/API)
4. LLaVA (本地)
5. Ollama (本地，支援 llava, bakllava 等)

優點：
- 更智能的 UI 元素識別
- 支援自然語言查詢（如 "找到確認按鈕"）
- 更好的上下文理解
"""

import os
import time
import base64
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from io import BytesIO

import pyautogui
from PIL import Image

# 嘗試導入各種 VLM 客戶端
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class VLMResult:
    """VLM 辨識結果"""
    success: bool
    x: int = 0
    y: int = 0
    confidence: float = 0.0
    time_ms: float = 0.0
    description: str = ""
    raw_response: str = ""
    box: Tuple[int, int, int, int] = None  # 邊界框 (xmin, ymin, xmax, ymax)


class VLMRecognizer:
    """
    VLM 視覺語言模型辨識器
    
    使用 VLM 來理解螢幕截圖並定位 UI 元素
    """
    
    def __init__(self, backend: str = "ollama", model: str = None):
        """
        初始化 VLM 辨識器
        
        Args:
            backend: 後端類型 ('openai', 'anthropic', 'ollama', 'qwen')
            model: 模型名稱（如 'gpt-4-vision-preview', 'llava'）
        """
        self.backend = backend
        self.model = model or self._get_default_model(backend)
        self.logger = None
        self._client = None
        self._initialized = False
        
        # 統計
        self.stats = {
            'attempts': 0,
            'hits': 0,
            'total_time': 0.0
        }
    
    def _get_default_model(self, backend: str) -> str:
        """取得預設模型名稱"""
        defaults = {
            'openai': 'gpt-4o',  # GPT-4o 支援視覺
            'anthropic': 'claude-3-5-sonnet-20241022',
            'ollama': 'llava',  # 本地 LLaVA
            'qwen': 'qwen-vl-plus'
        }
        return defaults.get(backend, 'llava')
    
    def set_logger(self, logger):
        """設置日誌記錄器"""
        self.logger = logger
    
    def _log(self, level: str, msg: str):
        """記錄日誌（自動清理 emoji 避免編碼錯誤）"""
        # 清理 emoji 避免 cp950 編碼錯誤
        safe_msg = msg.replace("🔍", "[DEBUG]").replace("🤖", "[VLM]").replace("📝", "[OCR]").replace("🎯", "[OK]").replace("📸", "[IMG]").replace("📊", "[STAT]").replace("❌", "[ERROR]").replace("✅", "[OK]").replace("⚠️", "[WARN]").replace("⏳", "[WAIT]").replace("🚀", "[START]").replace("💡", "[TIP]")
        if self.logger:
            getattr(self.logger, level)(safe_msg)
        else:
            print(f"[{level.upper()}] {safe_msg}")
    
    def _init_client(self):
        """延遲初始化客戶端"""
        if self._initialized:
            return
        
        try:
            if self.backend == 'openai':
                if not OPENAI_AVAILABLE:
                    raise ImportError("openai package not installed")
                self._client = openai.OpenAI()
                
            elif self.backend == 'anthropic':
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError("anthropic package not installed")
                self._client = anthropic.Anthropic()
                
            elif self.backend == 'ollama':
                if not OLLAMA_AVAILABLE:
                    raise ImportError("ollama package not installed")
                # Ollama 使用函數調用，不需要客戶端實例
                self._client = True
                
            self._initialized = True
            self._log('info', f"✅ VLM 初始化成功: {self.backend}/{self.model}")
            
        except Exception as e:
            self._log('warning', f"⚠️ VLM 初始化失敗: {e}")
            self._client = None
    
    def _screenshot_to_base64(self, region: Tuple[int, int, int, int] = None) -> tuple:
        """
        截圖並轉換為 base64
        
        Returns:
            (base64_string, original_size, resized_size)
            original_size: (width, height) 原始截圖尺寸
            resized_size: (width, height) 縮小後的截圖尺寸
        """
        if region:
            screenshot = pyautogui.screenshot(region=region)
            original_size = (region[2], region[3])  # (width, height)
        else:
            screenshot = pyautogui.screenshot()
            original_size = screenshot.size  # (width, height)
        
        # 縮小圖片以減少 API 成本和延遲
        max_size = (1280, 720)
        resized_size = screenshot.size  # 記錄縮小前的尺寸
        screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
        resized_size = screenshot.size  # 記錄縮小後的尺寸
        
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_str, original_size, resized_size
    
    def find_element(
        self,
        query: str,
        region: Tuple[int, int, int, int] = None,
        screenshot: Image.Image = None
    ) -> Optional[VLMResult]:
        """
        使用 VLM 在螢幕上尋找元素
        
        Args:
            query: 自然語言描述（如 "站點管理 按鈕" 或 "藍色的確認按鈕"）
            region: 搜尋區域 (left, top, width, height)
            screenshot: 可選的 PIL Image（不提供則自動截圖）
            
        Returns:
            VLMResult 或 None
        """
        self._init_client()
        
        if not self._client:
            return None
        
        self.stats['attempts'] += 1
        start_time = time.perf_counter()
        
        try:
            # 準備截圖
            original_size = None
            resized_size = None
            
            if screenshot:
                buffer = BytesIO()
                screenshot.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                original_size = screenshot.size
                resized_size = screenshot.size  # 如果沒有縮小，尺寸相同
            else:
                img_base64, original_size, resized_size = self._screenshot_to_base64(region)
            
            # 構建提示詞
            prompt = self._build_prompt(query, region)
            
            # 調用 VLM
            if self.backend == 'openai':
                result = self._call_openai(img_base64, prompt)
            elif self.backend == 'anthropic':
                result = self._call_anthropic(img_base64, prompt)
            elif self.backend == 'ollama':
                result = self._call_ollama(img_base64, prompt)
            else:
                return None
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if result:
                result.time_ms = elapsed_ms
                if result.success:
                    self.stats['hits'] += 1
                    self.stats['total_time'] += elapsed_ms
                    
                    # ========================================================================
                    # 🎯 座標換算邏輯（核心邏輯，請勿隨意修改）
                    # ========================================================================
                    # 
                    # 座標換算流程：
                    # 1. VLM 返回的座標是相對於縮小後的截圖（如果截圖被縮小）
                    # 2. 先將座標轉換回原始截圖尺寸
                    # 3. 如果提供了 region，再加上 region 的左上角偏移，得到屏幕絕對座標
                    #
                    # 重要：此邏輯影響所有使用 VLM 的地方，修改前請：
                    # 1. 運行 test_vlm_coordinate_conversion.py 驗證
                    # 2. 檢查所有使用 VLM 的地方是否仍然正常工作
                    # 3. 確保座標換算邏輯的正確性和穩定性
                    #
                    # ========================================================================
                    
                    if original_size and resized_size:
                        # 計算縮放比例
                        scale_x = original_size[0] / resized_size[0] if resized_size[0] > 0 else 1.0
                        scale_y = original_size[1] / resized_size[1] if resized_size[1] > 0 else 1.0
                        
                        # 🎯 VLM 返回的座標可能是比例座標（0-1）或像素座標
                        # 判斷標準：如果座標值 < 1.0，認為是比例座標；否則是像素座標
                        # 注意：result.x 和 result.y 在 _parse_response 中已經是 float
                        is_ratio_coord = (0.0 < abs(result.x) < 1.0) or (0.0 < abs(result.y) < 1.0)
                        
                        if is_ratio_coord:
                            # 比例座標：先轉換為縮小後圖片的像素座標
                            pixel_x = result.x * resized_size[0]
                            pixel_y = result.y * resized_size[1]
                            self._log('debug', f"比例座標轉換: VLM返回比例=({result.x:.3f}, {result.y:.3f}), 縮小後圖片像素=({pixel_x:.1f}, {pixel_y:.1f})")
                        else:
                            # 像素座標：直接使用（假設是相對於縮小後的圖片）
                            pixel_x = result.x
                            pixel_y = result.y
                            self._log('debug', f"像素座標: VLM返回=({pixel_x:.1f}, {pixel_y:.1f})")
                        
                        # 🎯 將座標（相對於縮小後的圖片）轉換回原始截圖尺寸
                        # 注意：original_size 是 region 的尺寸（如果提供了 region），否則是全屏尺寸
                        result.x = int(pixel_x * scale_x)
                        result.y = int(pixel_y * scale_y)
                        
                        self._log('debug', f"座標轉換: 原始尺寸={original_size}, 縮小後={resized_size}, 縮放比例=({scale_x:.3f}, {scale_y:.3f}), 轉換後=({result.x}, {result.y})")
                        
                        # 🎯 驗證轉換後的座標是否在原始截圖範圍內
                        if result.x < 0 or result.x > original_size[0] or result.y < 0 or result.y > original_size[1]:
                            self._log('warning', f"座標轉換後超出原始截圖範圍: ({result.x}, {result.y}), 原始截圖尺寸={original_size}")
                        
                        # 🎯 處理邊界框（box）的座標轉換（在 region 處理之前）
                        if result.box:
                            box_xmin, box_ymin, box_xmax, box_ymax = result.box
                            
                            # 判斷 box 是否為比例座標
                            is_box_ratio = (0.0 < abs(box_xmin) < 1.0) or (0.0 < abs(box_ymin) < 1.0)
                            
                            if is_box_ratio:
                                # 比例座標：轉換為縮小後圖片的像素座標
                                box_xmin = box_xmin * resized_size[0]
                                box_ymin = box_ymin * resized_size[1]
                                box_xmax = box_xmax * resized_size[0]
                                box_ymax = box_ymax * resized_size[1]
                            
                            # 轉換回原始截圖尺寸
                            box_xmin = int(box_xmin * scale_x)
                            box_ymin = int(box_ymin * scale_y)
                            box_xmax = int(box_xmax * scale_x)
                            box_ymax = int(box_ymax * scale_y)
                            
                            # 暫時保存轉換後的 box（還未加 region 偏移）
                            result.box = (int(box_xmin), int(box_ymin), int(box_xmax), int(box_ymax))
                            self._log('debug', f"邊界框轉換（轉換後）: box=({box_xmin}, {box_ymin}, {box_xmax}, {box_ymax})")
                    else:
                        # 如果沒有 original_size/resized_size，box 保持原樣（假設已經是像素座標）
                        if result.box:
                            self._log('debug', f"邊界框未轉換（無縮放信息）: box={result.box}")
                    
                    # 🎯 加上 region 偏移（如果有）
                    # 注意：如果提供了 region，VLM 返回的座標是相對於 region 截圖的
                    # 我們需要加上 region 的左上角座標才能得到屏幕絕對座標
                    if region:
                        region_left = region[0]
                        region_top = region[1]
                        region_width = region[2]
                        region_height = region[3]
                        
                        # 🎯 驗證座標是否在 region 範圍內（轉換後，加偏移前）
                        # 此時 result.x, result.y 應該是相對於 region 截圖的座標
                        coord_before_offset_x = result.x
                        coord_before_offset_y = result.y
                        
                        # 如果座標超出 region 範圍，記錄警告
                        if coord_before_offset_x < 0 or coord_before_offset_x > region_width or \
                           coord_before_offset_y < 0 or coord_before_offset_y > region_height:
                            self._log('warning', f"VLM 返回座標超出 region 範圍: ({coord_before_offset_x:.1f}, {coord_before_offset_y:.1f}), region 尺寸=({region_width}, {region_height})")
                            # 如果 y 座標明顯超出範圍（超過 50px），可能是 VLM 返回了相對於全屏的座標，拒絕此結果
                            if coord_before_offset_y > region_height + 50:
                                self._log('warning', f"檢測到 y 座標明顯超出 region 高度（超過 50px），可能是 VLM 返回了相對於全屏的座標，將拒絕此結果")
                                result.success = False
                                return result
                            # 如果 x 座標明顯超出範圍（超過 50px），也可能是 VLM 返回了錯誤的座標，拒絕此結果
                            if coord_before_offset_x > region_width + 50:
                                self._log('warning', f"檢測到 x 座標明顯超出 region 寬度（超過 50px），可能是 VLM 返回了錯誤的座標，將拒絕此結果")
                                result.success = False
                                return result
                        
                        # 🎯 加上 region 偏移，得到屏幕絕對座標
                        result.x += region_left
                        result.y += region_top
                        self._log('debug', f"加上 region 偏移: region=({region_left}, {region_top}), 轉換前=({coord_before_offset_x:.1f}, {coord_before_offset_y:.1f}), 最終座標=({result.x}, {result.y})")
                        
                        # 🎯 為邊界框（box）加上 region 偏移
                        if result.box:
                            box_xmin, box_ymin, box_xmax, box_ymax = result.box
                            box_xmin += region_left
                            box_ymin += region_top
                            box_xmax += region_left
                            box_ymax += region_top
                            result.box = (int(box_xmin), int(box_ymin), int(box_xmax), int(box_ymax))
                            self._log('debug', f"邊界框加上 region 偏移: 最終 box=({box_xmin}, {box_ymin}, {box_xmax}, {box_ymax})")
                
                return result
                
        except Exception as e:
            self._log('warning', f"⚠️ VLM 辨識異常: {e}")
        
        return None
    
    def _build_prompt(self, query: str, region: Tuple = None) -> str:
        """構建 VLM 提示詞"""
        # 如果有 region，在 prompt 中明確說明這是截圖的一部分
        region_info = ""
        if region:
            region_info = f"\n重要：這是一張局部截圖，只包含螢幕的一部分區域。截圖的尺寸是 {region[2]}x{region[3]} 像素。"
        
        # 🎯 優化提示詞：對於郵箱地址，提供更明確的指引
        enhanced_query = query
        if "@" in query and "gmail" in query.lower():
            enhanced_query = f"找到郵箱地址文字 '{query}'（通常前面有一個雲圖標或圖標，文字可能是白色或灰色）"
        
        return f"""你是一個 UI 自動化助手。請分析這張螢幕截圖，找到以下元素：

目標元素：{enhanced_query}
{region_info}

重要提示：
1. 如果目標是郵箱地址，請找到完整的郵箱文字（包括 @ 符號和域名）
2. 如果目標是按鈕或選單項，請找到可點擊的元素中心點
3. 座標必須是相對於截圖的像素座標（不是比例座標）
4. 如果找不到元素，請設置 "found": false

請回覆以下 JSON 格式（只回覆 JSON，不要其他文字）：
{{
    "found": true/false,
    "x": 元素中心點 X 座標（像素，相對於截圖），
    "y": 元素中心點 Y 座標（像素，相對於截圖），
    "confidence": 信心度 (0.0-1.0),
    "description": "元素描述",
    "box": [xmin, ymin, xmax, ymax]
}}

如果找不到目標元素，回覆：
{{
    "found": false,
    "x": 0,
    "y": 0,
    "confidence": 0,
    "description": "找不到目標元素的原因",
    "box": null
}}

如果找不到目標元素，回覆：
{{
    "found": false,
    "x": 0,
    "y": 0,
    "confidence": 0,
    "description": "找不到目標元素的原因",
    "box": null
}}

重要規則：
1. 座標必須是相對於這張截圖左上角 (0, 0) 的像素座標
2. X 座標範圍：0 到 {region[2] if region else "圖片寬度"}
3. Y 座標範圍：0 到 {region[3] if region else "圖片高度"}
4. 請準確定位元素的中心點
5. 如果使用比例座標（0.0-1.0），請確保轉換為像素座標後在範圍內
6. 如果有多個匹配項，選擇最可能的一個"""
    
    def _call_openai(self, img_base64: str, prompt: str) -> Optional[VLMResult]:
        """調用 OpenAI GPT-4V"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            self._log('warning', f"OpenAI API 錯誤: {e}")
            return None
    
    def _call_anthropic(self, img_base64: str, prompt: str) -> Optional[VLMResult]:
        """調用 Anthropic Claude"""
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            
            return self._parse_response(response.content[0].text)
            
        except Exception as e:
            self._log('warning', f"Anthropic API 錯誤: {e}")
            return None
    
    def _call_ollama(self, img_base64: str, prompt: str) -> Optional[VLMResult]:
        """調用本地 Ollama (LLaVA 等)"""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [img_base64]
                    }
                ]
            )
            
            return self._parse_response(response['message']['content'])
            
        except Exception as e:
            self._log('warning', f"Ollama 錯誤: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[VLMResult]:
        """解析 VLM 回應"""
        import json
        import re
        
        try:
            # 嘗試提取 JSON（支持多層嵌套的 JSON 或 code block）
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group(1) if json_match.groups() else json_match.group())
                
                x_val = data.get('x', 0)
                y_val = data.get('y', 0)
                
                # 轉換為浮點數並驗證合理性
                try:
                    x_float = float(x_val)
                    y_float = float(y_val)
                except (ValueError, TypeError):
                    self._log('warning', f"無法轉換座標值: x={x_val}, y={y_val}")
                    return VLMResult(
                        success=False,
                        description=f"座標值格式錯誤: x={x_val}, y={y_val}",
                        raw_response=response
                    )
                
                # 驗證座標合理性（不應該超過 10000 像素，通常螢幕寬度不超過 7680）
                # 如果座標異常大，可能是解析錯誤或模型輸出格式問題
                MAX_REASONABLE_COORD = 10000
                if abs(x_float) > MAX_REASONABLE_COORD or abs(y_float) > MAX_REASONABLE_COORD:
                    self._log('warning', f"VLM 返回的座標異常巨大: x={x_float}, y={y_float}，可能是解析錯誤。原始回應: {response[:500]}")
                    # 如果座標異常，標記為失敗
                    return VLMResult(
                        success=False,
                        x=0,
                        y=0,
                        confidence=0,
                        description=f"座標值異常: x={x_float}, y={y_float}",
                        raw_response=response
                    )
                
                # 判斷座標格式：如果值在 0-1 之間（比例座標），需要轉換
                # 但需要圖片尺寸才能轉換，所以先保留原始值，在 find_element 中處理
                # 這裡先標記為浮點數，如果小於 1 則認為是比例座標
                
                # 解析邊界框（box）
                box = None
                if 'box' in data and data['box']:
                    try:
                        box_list = data['box']
                        if isinstance(box_list, list) and len(box_list) == 4:
                            # box 格式: [xmin, ymin, xmax, ymax]
                            box = tuple(map(float, box_list))
                    except (ValueError, TypeError) as e:
                        self._log('debug', f"無法解析 box 座標: {e}")
                
                return VLMResult(
                    success=data.get('found', False),
                    x=x_float,  # 保留為浮點數，以便判斷是比例還是像素
                    y=y_float,  # 保留為浮點數，以便判斷是比例還是像素
                    confidence=float(data.get('confidence', 0)),
                    description=data.get('description', ''),
                    raw_response=response,
                    box=box  # 邊界框（可能是比例座標或像素座標，需要在 find_element 中轉換）
                )
        except (json.JSONDecodeError, ValueError) as e:
            self._log('debug', f"解析 VLM 回應失敗: {e}")
        
        return VLMResult(
            success=False,
            description=f"無法解析回應: {response[:200]}",
            raw_response=response
        )
    
    def get_stats_summary(self) -> str:
        """取得統計摘要"""
        hit_rate = (self.stats['hits'] / self.stats['attempts'] * 100) if self.stats['attempts'] > 0 else 0
        avg_time = (self.stats['total_time'] / self.stats['hits']) if self.stats['hits'] > 0 else 0
        
        return f"""
[VLM Stats] {self.backend}/{self.model}
  Attempts: {self.stats['attempts']}
  Hits: {self.stats['hits']} ({hit_rate:.1f}%)
  Avg Time: {avg_time:.0f}ms
"""


# 全域實例
_vlm_recognizer = None

def get_vlm_recognizer(backend: str = None, model: str = None) -> VLMRecognizer:
    """取得 VLM 辨識器實例"""
    global _vlm_recognizer
    
    # 從環境變數讀取設定
    if backend is None:
        backend = os.environ.get('VLM_BACKEND', 'ollama')
    if model is None:
        model = os.environ.get('VLM_MODEL', None)
    
    if _vlm_recognizer is None or _vlm_recognizer.backend != backend:
        _vlm_recognizer = VLMRecognizer(backend=backend, model=model)
    
    return _vlm_recognizer
