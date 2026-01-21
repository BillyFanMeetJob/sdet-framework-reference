# -*- coding: utf-8 -*-
"""
OK Script 圖像辨識整合模組

提供基於 OK Script 的 template matching 功能，
優先於現有的 pyautogui 圖片辨識方法。

統計功能：
- 命中率 (Hit Rate)
- 平均辨識時間
- 方法對比分析
"""

import time
import os
import json
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, field, asdict
from threading import Lock

# 嘗試導入 OK Script
try:
    from ok import OK
    OK_SCRIPT_AVAILABLE = True
except ImportError:
    OK_SCRIPT_AVAILABLE = False

# 嘗試導入 cv2 用於 template matching
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

import pyautogui
from PIL import Image


@dataclass
class RecognitionResult:
    """辨識結果"""
    success: bool
    method: str  # 'ok_script', 'pyautogui', 'ocr', 'coordinate'
    x: int = 0
    y: int = 0
    width: int = 0  # 物件寬度（用於紅框標註）
    height: int = 0  # 物件高度（用於紅框標註）
    confidence: float = 0.0
    time_ms: float = 0.0
    image_path: str = ""
    target_text: str = ""


@dataclass
class RecognitionStats:
    """辨識統計"""
    total_attempts: int = 0
    ok_script_hits: int = 0
    ok_script_time_total: float = 0.0
    pyautogui_hits: int = 0
    pyautogui_time_total: float = 0.0
    ocr_hits: int = 0
    ocr_time_total: float = 0.0
    vlm_hits: int = 0
    vlm_time_total: float = 0.0
    coordinate_hits: int = 0
    
    # 每個圖片的統計
    image_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_ok_script_hit_rate(self) -> float:
        """取得 OK Script 命中率"""
        if self.total_attempts == 0:
            return 0.0
        return self.ok_script_hits / self.total_attempts * 100
    
    def get_pyautogui_hit_rate(self) -> float:
        """取得 pyautogui 命中率"""
        if self.total_attempts == 0:
            return 0.0
        return self.pyautogui_hits / self.total_attempts * 100
    
    def get_vlm_hit_rate(self) -> float:
        """取得 VLM 命中率"""
        if self.total_attempts == 0:
            return 0.0
        return self.vlm_hits / self.total_attempts * 100
    
    def get_ok_script_avg_time(self) -> float:
        """取得 OK Script 平均辨識時間（毫秒）"""
        if self.ok_script_hits == 0:
            return 0.0
        return self.ok_script_time_total / self.ok_script_hits
    
    def get_pyautogui_avg_time(self) -> float:
        """取得 pyautogui 平均辨識時間（毫秒）"""
        if self.pyautogui_hits == 0:
            return 0.0
        return self.pyautogui_time_total / self.pyautogui_hits
    
    def get_vlm_avg_time(self) -> float:
        """取得 VLM 平均辨識時間（毫秒）"""
        if self.vlm_hits == 0:
            return 0.0
        return self.vlm_time_total / self.vlm_hits


class OKScriptRecognizer:
    """
    OK Script 圖像辨識器
    
    優先使用 OK Script 的 template matching，
    如果失敗則回退到 pyautogui。
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """單例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.stats = RecognitionStats()
        self.logger = None
        self._ok_script = None
        self._use_ok_script = True  # 是否啟用 OK Script
        self._confidence_threshold = 0.7  # OK Script 信心閾值（降低以提高對畫面變化的容錯性）
        self._stats_file = "logs/recognition_stats.json"
        
        # 追蹤連續圖像辨識失敗次數（用於測試驗證）
        self._consecutive_image_recognition_failures = 0
        
        # 初始化 OK Script
        self._init_ok_script()
        
        # 載入歷史統計
        self._load_stats()
    
    def _init_ok_script(self):
        """初始化 OK Script"""
        if not OK_SCRIPT_AVAILABLE:
            if self.logger:
                self.logger.info("⚠️ OK Script 未安裝，使用 OpenCV template matching 替代")
            return
        
        try:
            self._ok_script = OK()
            if self.logger:
                self.logger.info("✅ OK Script 初始化成功")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ OK Script 初始化失敗: {e}")
            self._ok_script = None
    
    def set_logger(self, logger):
        """設置日誌記錄器"""
        self.logger = logger
    
    def enable_ok_script(self, enabled: bool = True):
        """啟用/停用 OK Script"""
        self._use_ok_script = enabled
    
    def set_confidence(self, confidence: float):
        """設置信心閾值"""
        self._confidence_threshold = confidence
    
    def locate_on_screen(
        self,
        image_path: str,
        region: Tuple[int, int, int, int] = None,
        confidence: float = None
    ) -> Optional[RecognitionResult]:
        """
        在螢幕上定位圖片
        
        優先級：OK Script > pyautogui
        
        Args:
            image_path: 圖片路徑
            region: 搜尋區域 (left, top, width, height)
            confidence: 信心閾值（覆蓋預設值）
            
        Returns:
            RecognitionResult 或 None
        """
        if not os.path.exists(image_path):
            return None
        
        conf = confidence if confidence is not None else self._confidence_threshold
        self.stats.total_attempts += 1
        
        # 記錄圖片統計
        img_name = os.path.basename(image_path)
        if img_name not in self.stats.image_stats:
            self.stats.image_stats[img_name] = {
                'attempts': 0,
                'ok_script_hits': 0,
                'pyautogui_hits': 0,
                'ok_script_time': 0.0,
                'pyautogui_time': 0.0
            }
        self.stats.image_stats[img_name]['attempts'] += 1
        
        # 【優先級 1】OK Script / OpenCV Template Matching
        if self._use_ok_script:
            result = self._locate_with_ok_script(image_path, region, conf)
            if result and result.success:
                self.stats.ok_script_hits += 1
                self.stats.ok_script_time_total += result.time_ms
                self.stats.image_stats[img_name]['ok_script_hits'] += 1
                self.stats.image_stats[img_name]['ok_script_time'] += result.time_ms
                return result
        
        # 【優先級 2】pyautogui
        result = self._locate_with_pyautogui(image_path, region, conf)
        if result and result.success:
            self.stats.pyautogui_hits += 1
            self.stats.pyautogui_time_total += result.time_ms
            self.stats.image_stats[img_name]['pyautogui_hits'] += 1
            self.stats.image_stats[img_name]['pyautogui_time'] += result.time_ms
            return result
        
        return None
    
    def _locate_with_ok_script(
        self,
        image_path: str,
        region: Tuple[int, int, int, int] = None,
        confidence: float = 0.7  # 降低默認置信度以提高對畫面變化的容錯性
    ) -> Optional[RecognitionResult]:
        """
        使用 OK Script / OpenCV 定位圖片
        """
        start_time = time.perf_counter()
        
        try:
            # 如果 OK Script 可用
            if self._ok_script is not None:
                # 使用 OK Script 的 template matching
                loc = self._ok_script.find_template(image_path, confidence=confidence)
                if loc:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    # 讀取模板尺寸
                    try:
                        from PIL import Image
                        template_img = Image.open(image_path)
                        template_w, template_h = template_img.size
                    except:
                        template_w, template_h = 50, 50  # 預設尺寸
                    
                    # 🎯 OK Script 的 find_template 可能返回中心點或左上角
                    # 根據 OK Script 文檔，find_template 返回的是 (x, y) 座標
                    # 但需要確認是左上角還是中心點
                    # 為了安全起見，我們假設返回的是中心點，需要轉換為左上角
                    ok_script_x = loc[0]
                    ok_script_y = loc[1]
                    
                    # 🎯 嘗試兩種情況：
                    # 1. 如果返回的是中心點，需要減去寬高的一半
                    # 2. 如果返回的是左上角，直接使用
                    # 由於無法確定，我們先假設是左上角（與 OpenCV 一致）
                    # 如果後續驗證發現不對，會在 camera_page.py 中進行調整
                    top_left_x = ok_script_x
                    top_left_y = ok_script_y
                    
                    return RecognitionResult(
                        success=True,
                        method='ok_script',
                        x=top_left_x,
                        y=top_left_y,
                        width=template_w,  # 使用模板圖片寬度
                        height=template_h,  # 使用模板圖片高度
                        confidence=confidence,
                        time_ms=elapsed_ms,
                        image_path=image_path
                    )
            
            # 回退到 OpenCV template matching
            elif CV2_AVAILABLE:
                result = self._locate_with_opencv(image_path, region, confidence)
                if result:
                    result.method = 'ok_script'  # 標記為 ok_script 分類統計
                    return result
                    
        except Exception as e:
            if self.logger:
                self.logger.debug(f"OK Script 辨識異常: {e}")
        
        return None
    
    def _locate_with_opencv(
        self,
        image_path: str,
        region: Tuple[int, int, int, int] = None,
        confidence: float = 0.7  # 降低默認置信度以提高對畫面變化的容錯性
    ) -> Optional[RecognitionResult]:
        """
        使用 OpenCV template matching 定位圖片
        這是 OK Script 的核心演算法
        """
        if not CV2_AVAILABLE:
            return None
        
        start_time = time.perf_counter()
        
        try:
            # 截取螢幕
            if region:
                screenshot = pyautogui.screenshot(region=region)
                offset_x, offset_y = region[0], region[1]
            else:
                screenshot = pyautogui.screenshot()
                offset_x, offset_y = 0, 0
            
            # 轉換為 OpenCV 格式
            screen_np = np.array(screenshot)
            screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
            
            # 讀取模板
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            
            # 多尺度 template matching
            best_match = None
            best_confidence = 0
            
            # 嘗試不同縮放比例
            scales = [1.0, 0.95, 1.05, 0.9, 1.1]
            
            for scale in scales:
                if scale != 1.0:
                    scaled_template = cv2.resize(
                        template,
                        None,
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_AREA
                    )
                else:
                    scaled_template = template
                
                # 確保模板不超過螢幕
                if scaled_template.shape[0] > screen_gray.shape[0] or \
                   scaled_template.shape[1] > screen_gray.shape[1]:
                    continue
                
                # Template matching
                result = cv2.matchTemplate(
                    screen_gray,
                    scaled_template,
                    cv2.TM_CCOEFF_NORMED
                )
                
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence and max_val >= confidence:
                    best_confidence = max_val
                    # 🎯 OpenCV matchTemplate 返回的是左上角座標，不是中心點
                    # max_loc[0], max_loc[1] 已經是左上角，加上 offset 即可
                    top_left_x = max_loc[0] + offset_x
                    top_left_y = max_loc[1] + offset_y
                    best_match = (top_left_x, top_left_y, max_val)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if best_match:
                # 讀取模板尺寸（使用最後匹配的模板）
                template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                template_h, template_w = template.shape if template is not None else (50, 50)
                return RecognitionResult(
                    success=True,
                    method='opencv',
                    x=best_match[0],
                    y=best_match[1],
                    width=template_w,
                    height=template_h,
                    confidence=best_match[2],
                    time_ms=elapsed_ms,
                    image_path=image_path
                )
                
        except Exception as e:
            if self.logger:
                self.logger.debug(f"OpenCV 辨識異常: {e}")
        
        return None
    
    def _locate_with_pyautogui(
        self,
        image_path: str,
        region: Tuple[int, int, int, int] = None,
        confidence: float = 0.7  # 降低默認置信度以提高對畫面變化的容錯性
    ) -> Optional[RecognitionResult]:
        """
        使用 pyautogui 定位圖片（原有方法）
        """
        start_time = time.perf_counter()
        
        try:
            loc = pyautogui.locateOnScreen(
                image_path,
                confidence=confidence,
                region=region
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if loc:
                center = pyautogui.center(loc)
                return RecognitionResult(
                    success=True,
                    method='pyautogui',
                    x=center.x,
                    y=center.y,
                    width=loc.width,  # 使用實際辨識到的物件寬度
                    height=loc.height,  # 使用實際辨識到的物件高度
                    confidence=confidence,
                    time_ms=elapsed_ms,
                    image_path=image_path
                )
                
        except Exception as e:
            if self.logger:
                self.logger.debug(f"pyautogui 辨識異常: {e}")
        
        return None
    
    def record_ocr_hit(self, time_ms: float):
        """記錄 OCR 命中"""
        self.stats.ocr_hits += 1
        self.stats.ocr_time_total += time_ms
    
    def record_vlm_hit(self, time_ms: float):
        """記錄 VLM 命中"""
        self.stats.vlm_hits += 1
        self.stats.vlm_time_total += time_ms
    
    def record_coordinate_hit(self):
        """記錄座標保底命中"""
        self.stats.coordinate_hits += 1
        # 增加連續圖像辨識失敗計數
        self._consecutive_image_recognition_failures += 1
    
    def record_image_recognition_success(self):
        """記錄圖像辨識成功（重置連續失敗計數）"""
        self._consecutive_image_recognition_failures = 0
    
    def get_consecutive_image_recognition_failures(self) -> int:
        """取得連續圖像辨識失敗次數"""
        return self._consecutive_image_recognition_failures
    
    def reset_consecutive_failures(self):
        """重置連續失敗計數（用於新的測試開始）"""
        self._consecutive_image_recognition_failures = 0
    
    def get_stats_summary(self) -> str:
        """
        取得統計摘要
        """
        # 計算 OCR 和 VLM 的命中率
        ocr_rate = (self.stats.ocr_hits / self.stats.total_attempts * 100) if self.stats.total_attempts > 0 else 0
        vlm_rate = self.stats.get_vlm_hit_rate()
        coord_rate = (self.stats.coordinate_hits / self.stats.total_attempts * 100) if self.stats.total_attempts > 0 else 0
        
        lines = [
            "=" * 60,
            "[STATS] Image Recognition Statistics Report",
            "=" * 60,
            f"Total Attempts: {self.stats.total_attempts}",
            "",
            "[Hit Rate]",
            f"  OK Script/OpenCV: {self.stats.ok_script_hits}/{self.stats.total_attempts} ({self.stats.get_ok_script_hit_rate():.1f}%)",
            f"  VLM (LLM Vision): {self.stats.vlm_hits}/{self.stats.total_attempts} ({vlm_rate:.1f}%)",
            f"  pyautogui:        {self.stats.pyautogui_hits}/{self.stats.total_attempts} ({self.stats.get_pyautogui_hit_rate():.1f}%)",
            f"  OCR:              {self.stats.ocr_hits}/{self.stats.total_attempts} ({ocr_rate:.1f}%)",
            f"  Coordinate:       {self.stats.coordinate_hits}/{self.stats.total_attempts} ({coord_rate:.1f}%)",
            "",
            "[Average Recognition Time]",
            f"  OK Script/OpenCV: {self.stats.get_ok_script_avg_time():.2f} ms",
            f"  VLM (LLM Vision): {self.stats.get_vlm_avg_time():.2f} ms",
            f"  pyautogui:        {self.stats.get_pyautogui_avg_time():.2f} ms",
            "",
            "[Per-Image Statistics]",
        ]
        
        for img_name, stats in sorted(self.stats.image_stats.items()):
            attempts = stats['attempts']
            ok_hits = stats['ok_script_hits']
            py_hits = stats['pyautogui_hits']
            ok_rate = (ok_hits / attempts * 100) if attempts > 0 else 0
            py_rate = (py_hits / attempts * 100) if attempts > 0 else 0
            lines.append(f"  {img_name}:")
            lines.append(f"    Attempts: {attempts}, OK Script: {ok_hits} ({ok_rate:.0f}%), pyautogui: {py_hits} ({py_rate:.0f}%)")
        
        if not self.stats.image_stats:
            lines.append("  (No image data yet)")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_stats(self):
        """保存統計到文件"""
        try:
            os.makedirs(os.path.dirname(self._stats_file), exist_ok=True)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_attempts': self.stats.total_attempts,
                'ok_script_hits': self.stats.ok_script_hits,
                'ok_script_time_total': self.stats.ok_script_time_total,
                'pyautogui_hits': self.stats.pyautogui_hits,
                'pyautogui_time_total': self.stats.pyautogui_time_total,
                'ocr_hits': self.stats.ocr_hits,
                'ocr_time_total': self.stats.ocr_time_total,
                'vlm_hits': self.stats.vlm_hits,
                'vlm_time_total': self.stats.vlm_time_total,
                'coordinate_hits': self.stats.coordinate_hits,
                'image_stats': self.stats.image_stats
            }
            
            with open(self._stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"保存統計失敗: {e}")
    
    def _load_stats(self):
        """載入歷史統計"""
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.stats.total_attempts = data.get('total_attempts', 0)
                self.stats.ok_script_hits = data.get('ok_script_hits', 0)
                self.stats.ok_script_time_total = data.get('ok_script_time_total', 0.0)
                self.stats.pyautogui_hits = data.get('pyautogui_hits', 0)
                self.stats.pyautogui_time_total = data.get('pyautogui_time_total', 0.0)
                self.stats.ocr_hits = data.get('ocr_hits', 0)
                self.stats.ocr_time_total = data.get('ocr_time_total', 0.0)
                self.stats.vlm_hits = data.get('vlm_hits', 0)
                self.stats.vlm_time_total = data.get('vlm_time_total', 0.0)
                self.stats.coordinate_hits = data.get('coordinate_hits', 0)
                self.stats.image_stats = data.get('image_stats', {})
                
        except Exception:
            pass  # 忽略載入錯誤，使用預設值
    
    def reset_stats(self):
        """重置統計"""
        self.stats = RecognitionStats()
        if os.path.exists(self._stats_file):
            os.remove(self._stats_file)


# 全域單例
_recognizer = None

def get_recognizer() -> OKScriptRecognizer:
    """取得全域辨識器實例"""
    global _recognizer
    if _recognizer is None:
        _recognizer = OKScriptRecognizer()
    return _recognizer
