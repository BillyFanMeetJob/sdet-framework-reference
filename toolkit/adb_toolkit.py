# -*- coding: utf-8 -*-
"""
ADB 移動端自動化工具類

提供基於 ADB 的 Android 設備控制功能，繞過 UiAutomator2 的穩定性問題。
使用 ADB 命令 + OpenCV 圖像識別進行自動化操作。
"""

import os
import time
import subprocess
import tempfile
from typing import Optional, Tuple
from toolkit.logger import get_logger

# 嘗試導入 cv2 用於圖像辨識
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = get_logger(__name__)


class AdbController:
    """
    使用 ADB 控制 Android 設備
    
    提供基本的設備控制功能：截圖、點擊、輸入文字等。
    不依賴 UiAutomator2，更加穩定。
    """
    
    def __init__(self, device_id: Optional[str] = None):
        """
        初始化 ADB 控制器
        
        Args:
            device_id: 設備 ID（可選），如果有多個設備需要指定
        """
        self.device_id = device_id
        self.adb_prefix = ['adb']
        if device_id:
            self.adb_prefix = ['adb', '-s', device_id]
        
        self._width = None
        self._height = None
        logger.info(f"[ADB_TOOLKIT] 初始化 ADB 控制器，設備: {device_id or '自動選擇'}")
    
    def run_cmd(self, cmd: list, timeout: int = 30, silent: bool = False) -> subprocess.CompletedProcess:
        """
        執行 ADB 命令
        
        Args:
            cmd: 命令參數列表
            timeout: 超時時間（秒）
            silent: 是否靜默執行（不打印日誌）
            
        Returns:
            subprocess.CompletedProcess: 命令執行結果
        """
        full_cmd = self.adb_prefix + cmd
        if not silent:
            logger.debug(f"[ADB_TOOLKIT] 執行: {' '.join(full_cmd)}")
        result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
        return result
    
    def screenshot(self, save_path: Optional[str] = None) -> str:
        """
        截取螢幕
        
        Args:
            save_path: 保存路徑（可選）
            
        Returns:
            str: 截圖保存路徑
        """
        if save_path is None:
            save_path = tempfile.mktemp(suffix='.png')
        
        # 截圖到設備
        self.run_cmd(['shell', 'screencap', '-p', '/sdcard/screenshot.png'], silent=True)
        # 拉取到本地
        self.run_cmd(['pull', '/sdcard/screenshot.png', save_path], silent=True)
        
        return save_path
    
    def tap(self, x: int, y: int, duration: int = 100, wait: float = 0.2) -> None:
        """
        點擊座標
        
        Args:
            x: X 座標
            y: Y 座標
            duration: 點擊持續時間（毫秒），目前未使用
            wait: 點擊後等待時間（秒）
        """
        logger.info(f"[ADB_TOOLKIT] 點擊座標: ({x}, {y})")
        self.run_cmd(['shell', 'input', 'tap', str(int(x)), str(int(y))], silent=True)
        time.sleep(wait)
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> None:
        """
        長按座標
        
        Args:
            x: X 座標
            y: Y 座標
            duration: 長按持續時間（毫秒）
        """
        logger.info(f"[ADB_TOOLKIT] 長按座標: ({x}, {y})，持續 {duration}ms")
        self.run_cmd(['shell', 'input', 'swipe', str(int(x)), str(int(y)), 
                      str(int(x)), str(int(y)), str(duration)], silent=True)
        time.sleep(0.5)
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500) -> None:
        """
        滑動操作
        
        Args:
            start_x: 起始 X 座標
            start_y: 起始 Y 座標
            end_x: 結束 X 座標
            end_y: 結束 Y 座標
            duration: 滑動持續時間（毫秒）
        """
        logger.info(f"[ADB_TOOLKIT] 滑動: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        self.run_cmd(['shell', 'input', 'swipe', 
                      str(int(start_x)), str(int(start_y)), 
                      str(int(end_x)), str(int(end_y)), str(duration)], silent=True)
        time.sleep(0.5)
    
    def input_text(self, text: str) -> None:
        """
        輸入文字（只支援 ASCII 字符）
        
        Args:
            text: 要輸入的文字
        """
        logger.info(f"[ADB_TOOLKIT] 輸入文字: {text}")
        logger.debug(f"[ADB_TOOLKIT] [DEBUG] 原始文字長度: {len(text)}")
        
        # 轉義特殊字符
        escaped_text = text.replace(' ', '%s').replace('@', '\\@').replace('!', '\\!')
        logger.debug(f"[ADB_TOOLKIT] [DEBUG] 轉義後文字: {escaped_text}")
        
        try:
            result = self.run_cmd(['shell', 'input', 'text', escaped_text], silent=True)
            logger.debug(f"[ADB_TOOLKIT] [DEBUG] ADB 命令執行完成，返回碼: {result.returncode}")
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ''
                logger.error(f"[ADB_TOOLKIT] [ERROR] 輸入文字失敗，錯誤: {stderr}")
            else:
                logger.debug(f"[ADB_TOOLKIT] [DEBUG] 輸入文字成功")
        except Exception as e:
            logger.error(f"[ADB_TOOLKIT] [ERROR] 輸入文字時發生異常: {e}")
            import traceback
            logger.error(f"[ADB_TOOLKIT] [ERROR] 詳細錯誤: {traceback.format_exc()}")
            raise
        
        time.sleep(0.5)
    
    def press_keycode(self, keycode: int) -> None:
        """
        按下按鍵
        
        Args:
            keycode: Android 按鍵碼
        """
        self.run_cmd(['shell', 'input', 'keyevent', str(keycode)], silent=True)
    
    def press_enter(self) -> None:
        """按 Enter 鍵"""
        self.press_keycode(66)  # KEYCODE_ENTER
    
    def press_back(self) -> None:
        """按返回鍵"""
        self.press_keycode(4)  # KEYCODE_BACK
    
    def press_delete(self) -> None:
        """按刪除鍵"""
        self.press_keycode(67)  # KEYCODE_DEL
    
    def hide_keyboard(self) -> None:
        """隱藏鍵盤"""
        self.press_keycode(111)  # KEYCODE_ESCAPE
    
    def clear_input(self, x: int, y: int) -> None:
        """
        清空輸入框（三擊全選 + 刪除）
        
        Args:
            x: 輸入框 X 座標
            y: 輸入框 Y 座標
        """
        logger.info(f"[ADB_TOOLKIT] 清空輸入框: ({x}, {y})")
        logger.debug(f"[ADB_TOOLKIT] [DEBUG] 開始三擊選中文字...")
        
        # 三擊選中全部文字
        for i in range(3):
            logger.debug(f"[ADB_TOOLKIT] [DEBUG] 第 {i+1} 次點擊...")
            self.run_cmd(['shell', 'input', 'tap', str(x), str(y)], silent=True)
            time.sleep(0.1)
        
        time.sleep(0.3)
        logger.debug(f"[ADB_TOOLKIT] [DEBUG] 三擊完成，按刪除鍵...")
        
        # 刪除選中文字
        self.press_delete()
        logger.debug(f"[ADB_TOOLKIT] [DEBUG] 刪除鍵已按下")
        time.sleep(0.3)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        獲取螢幕尺寸
        
        Returns:
            Tuple[int, int]: (寬度, 高度)
        """
        if self._width and self._height:
            return self._width, self._height
        
        result = self.run_cmd(['shell', 'wm', 'size'], silent=True)
        output = result.stdout.decode('utf-8', errors='ignore')
        
        import re
        match = re.search(r'(\d+)x(\d+)', output)
        if match:
            self._width = int(match.group(1))
            self._height = int(match.group(2))
        else:
            self._width, self._height = 1080, 2400  # 預設值
        
        logger.info(f"[ADB_TOOLKIT] 螢幕尺寸: {self._width} x {self._height}")
        return self._width, self._height
    
    def wait_for_page_stable(
        self, 
        timeout: float = 10.0, 
        check_interval: float = 0.5,
        stability_threshold: float = 0.99
    ) -> bool:
        """
        智能等待：等待頁面穩定（連續兩次截圖相似度超過閾值）
        
        原理：
        - 頁面加載中時，截圖會不斷變化
        - 頁面加載完成後，截圖趨於穩定
        - 通過比較連續截圖的相似度來判斷頁面是否穩定
        
        Args:
            timeout: 最大等待時間（秒），默認 10 秒
            check_interval: 檢查間隔（秒），默認 0.5 秒
            stability_threshold: 穩定性閾值（0.0-1.0），默認 0.99
            
        Returns:
            bool: 頁面是否在超時前穩定
        """
        if not CV2_AVAILABLE:
            logger.warning("[ADB_TOOLKIT] OpenCV 不可用，使用固定等待")
            time.sleep(timeout / 2)
            return True
        
        logger.info(f"[ADB_TOOLKIT] 智能等待頁面穩定（超時: {timeout}s, 閾值: {stability_threshold}）...")
        
        start_time = time.time()
        prev_screenshot = None
        
        while time.time() - start_time < timeout:
            # 截取當前畫面
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                self.screenshot(tmp_path)
                current_screenshot = cv2.imread(tmp_path, cv2.IMREAD_GRAYSCALE)
                os.unlink(tmp_path)
                
                if current_screenshot is None:
                    time.sleep(check_interval)
                    continue
                
                if prev_screenshot is not None:
                    # 計算相似度
                    similarity = self._calculate_similarity(prev_screenshot, current_screenshot)
                    elapsed = time.time() - start_time
                    
                    if similarity >= stability_threshold:
                        logger.info(f"[ADB_TOOLKIT] 頁面已穩定（相似度: {similarity:.3f}，耗時: {elapsed:.2f}s）")
                        return True
                    else:
                        logger.debug(f"[ADB_TOOLKIT] 頁面變化中（相似度: {similarity:.3f}）")
                
                prev_screenshot = current_screenshot
                
            except Exception as e:
                logger.debug(f"[ADB_TOOLKIT] 智能等待異常: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            time.sleep(check_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"[ADB_TOOLKIT] 頁面等待超時（{elapsed:.2f}s），繼續執行...")
        return False
    
    def _calculate_similarity(self, img1: 'np.ndarray', img2: 'np.ndarray') -> float:
        """
        計算兩張圖片的相似度
        
        Args:
            img1: 第一張圖片（灰度）
            img2: 第二張圖片（灰度）
            
        Returns:
            float: 相似度（0.0-1.0）
        """
        if img1.shape != img2.shape:
            # 調整尺寸
            h = min(img1.shape[0], img2.shape[0])
            w = min(img1.shape[1], img2.shape[1])
            img1 = cv2.resize(img1, (w, h))
            img2 = cv2.resize(img2, (w, h))
        
        # 計算差異
        diff = cv2.absdiff(img1, img2)
        total_pixels = diff.shape[0] * diff.shape[1]
        
        # 設定閾值：像素差異 > 10 視為不同
        _, thresh = cv2.threshold(diff, 10, 255, cv2.THRESH_BINARY)
        different_pixels = cv2.countNonZero(thresh)
        
        similarity = 1.0 - (different_pixels / total_pixels)
        return similarity
    
    def wait_for_element_by_color(
        self,
        target_color_hsv: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        region: Optional[Tuple[int, int, int, int]] = None,
        timeout: float = 10.0,
        check_interval: float = 0.5
    ) -> Optional[Tuple[int, int]]:
        """
        智能等待：等待特定顏色的元素出現
        
        Args:
            target_color_hsv: HSV 顏色範圍 ((H_min, S_min, V_min), (H_max, S_max, V_max))
            region: 搜索區域 (x, y, width, height)，None 表示全屏
            timeout: 最大等待時間（秒）
            check_interval: 檢查間隔（秒）
            
        Returns:
            Optional[Tuple[int, int]]: 元素中心座標，未找到則返回 None
        """
        if not CV2_AVAILABLE:
            logger.warning("[ADB_TOOLKIT] OpenCV 不可用")
            return None
        
        logger.info(f"[ADB_TOOLKIT] 等待顏色元素出現（超時: {timeout}s）...")
        
        start_time = time.time()
        lower_hsv, upper_hsv = target_color_hsv
        
        while time.time() - start_time < timeout:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                self.screenshot(tmp_path)
                img = cv2.imread(tmp_path)
                os.unlink(tmp_path)
                
                if img is None:
                    time.sleep(check_interval)
                    continue
                
                # 裁剪區域
                if region:
                    x, y, w, h = region
                    img = img[y:y+h, x:x+w]
                    offset_x, offset_y = x, y
                else:
                    offset_x, offset_y = 0, 0
                
                # 轉換為 HSV
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # 創建遮罩
                mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
                
                # 找到輪廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # 找最大的輪廓
                    largest = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(largest) > 100:  # 最小面積閾值
                        M = cv2.moments(largest)
                        if M["m00"] > 0:
                            cx = int(M["m10"] / M["m00"]) + offset_x
                            cy = int(M["m01"] / M["m00"]) + offset_y
                            elapsed = time.time() - start_time
                            logger.info(f"[ADB_TOOLKIT] 找到顏色元素: ({cx}, {cy})，耗時: {elapsed:.2f}s")
                            return (cx, cy)
                
            except Exception as e:
                logger.debug(f"[ADB_TOOLKIT] 顏色檢測異常: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            time.sleep(check_interval)
        
        logger.warning(f"[ADB_TOOLKIT] 等待顏色元素超時")
        return None
    
    def wait_for_thumbnail(
        self,
        region: Tuple[int, int, int, int] = (0, 200, 600, 400),
        min_brightness: int = 50,
        timeout: float = 30.0,
        check_interval: float = 1.0
    ) -> bool:
        """
        等待縮略圖出現（等待 Connecting... 結束）
        
        原理：
        - Connecting 畫面是深色的，沒有亮色縮略圖
        - 連接完成後，影片目錄頁面會顯示縮略圖（亮色區域）
        - 通過檢測指定區域的平均亮度來判斷縮略圖是否出現
        
        Args:
            region: 搜索區域 (x, y, width, height)
            min_brightness: 最小亮度閾值，超過表示縮略圖出現
            timeout: 最大等待時間（秒）
            check_interval: 檢查間隔（秒）
            
        Returns:
            bool: 縮略圖是否在超時前出現
        """
        if not CV2_AVAILABLE:
            logger.warning("[ADB_TOOLKIT] OpenCV 不可用，使用固定等待")
            time.sleep(timeout / 2)
            return True
        
        logger.info(f"[ADB_TOOLKIT] 等待縮略圖出現（超時: {timeout}s）...")
        
        start_time = time.time()
        x, y, w, h = region
        
        while time.time() - start_time < timeout:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                self.screenshot(tmp_path)
                img = cv2.imread(tmp_path, cv2.IMREAD_GRAYSCALE)
                os.unlink(tmp_path)
                
                if img is None:
                    time.sleep(check_interval)
                    continue
                
                # 檢查指定區域的平均亮度
                roi = img[y:y+h, x:x+w]
                avg_brightness = np.mean(roi)
                elapsed = time.time() - start_time
                
                logger.debug(f"[ADB_TOOLKIT] 區域亮度: {avg_brightness:.1f}，閾值: {min_brightness}")
                
                if avg_brightness >= min_brightness:
                    logger.info(f"[ADB_TOOLKIT] 縮略圖已出現（亮度: {avg_brightness:.1f}，耗時: {elapsed:.2f}s）")
                    return True
                
            except Exception as e:
                logger.debug(f"[ADB_TOOLKIT] 縮略圖檢測異常: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            time.sleep(check_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"[ADB_TOOLKIT] 等待縮略圖超時（{elapsed:.2f}s），繼續執行...")
        return False
    
    def is_connected(self) -> bool:
        """
        檢查設備是否連接
        
        Returns:
            bool: 設備是否連接
        """
        try:
            result = self.run_cmd(['devices'], silent=True)
            output = result.stdout.decode('utf-8', errors='ignore')
            # 檢查是否有 "device" 狀態的設備
            lines = output.strip().split('\n')
            for line in lines[1:]:  # 跳過標題行
                if 'device' in line and 'offline' not in line:
                    return True
            return False
        except Exception as e:
            logger.error(f"[ADB_TOOLKIT] 檢查設備連接失敗: {e}")
            return False


def find_image_on_screen(
    screenshot_path: str,
    template_path: str,
    confidence: float = 0.7
) -> Optional[Tuple[int, int, float]]:
    """
    在截圖中找到模板圖像
    
    Args:
        screenshot_path: 截圖路徑
        template_path: 模板圖像路徑
        confidence: 匹配置信度閾值
        
    Returns:
        Optional[Tuple[int, int, float]]: (x, y, 置信度) 或 None
    """
    if not CV2_AVAILABLE:
        logger.warning("[ADB_TOOLKIT] OpenCV 未安裝，無法進行圖像識別")
        return None
    
    screenshot = cv2.imread(screenshot_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    
    if screenshot is None:
        logger.error(f"[ADB_TOOLKIT] 無法讀取截圖: {screenshot_path}")
        return None
    if template is None:
        logger.error(f"[ADB_TOOLKIT] 無法讀取模板: {template_path}")
        return None
    
    # 轉換為灰度圖
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    
    # Template matching
    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= confidence:
        # 計算中心座標
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        logger.info(f"[ADB_TOOLKIT] 找到模板，座標: ({center_x}, {center_y})，置信度: {max_val:.3f}")
        return (center_x, center_y, max_val)
    
    logger.info(f"[ADB_TOOLKIT] 未找到模板，最高置信度: {max_val:.3f}")
    return None


def find_color_region(
    screenshot_path: str,
    color_lower: Tuple[int, int, int],
    color_upper: Tuple[int, int, int],
    min_area: int = 3000
) -> Optional[Tuple[int, int, int, int]]:
    """
    在截圖中找到特定顏色的區域（用於找按鈕等）
    
    Args:
        screenshot_path: 截圖路徑
        color_lower: HSV 顏色下限
        color_upper: HSV 顏色上限
        min_area: 最小面積閾值
        
    Returns:
        Optional[Tuple[int, int, int, int]]: (center_x, center_y, width, height) 或 None
    """
    if not CV2_AVAILABLE:
        logger.warning("[ADB_TOOLKIT] OpenCV 未安裝，無法進行顏色識別")
        return None
    
    img = cv2.imread(screenshot_path)
    if img is None:
        return None
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array(color_lower)
    upper = np.array(color_upper)
    mask = cv2.inRange(hsv, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_result = None
    max_area = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area and area > max_area:
            x, y, w, h = cv2.boundingRect(cnt)
            center_x = x + w // 2
            center_y = y + h // 2
            best_result = (center_x, center_y, w, h)
            max_area = area
    
    if best_result:
        logger.info(f"[ADB_TOOLKIT] 找到顏色區域，中心: ({best_result[0]}, {best_result[1]})")
    
    return best_result


# 常用顏色範圍（HSV）
BLUE_BUTTON = ((90, 50, 50), (130, 255, 255))  # 藍色按鈕
RED_INPUT = ((0, 50, 50), (10, 255, 255))       # 紅色輸入框邊框


def find_element_by_brightness(
    screenshot_path: str,
    region: Tuple[int, int, int, int],
    min_brightness: int = 30,
    min_area: int = 5000
) -> Optional[Tuple[int, int]]:
    """
    通過亮度檢測找到元素（適用於非黑色區域如縮圖）
    
    Args:
        screenshot_path: 截圖路徑
        region: 搜索區域 (x, y, width, height)
        min_brightness: 最小亮度閾值
        min_area: 最小面積
        
    Returns:
        Optional[Tuple[int, int]]: 元素中心座標
    """
    if not CV2_AVAILABLE:
        return None
    
    img = cv2.imread(screenshot_path)
    if img is None:
        return None
    
    x, y, w, h = region
    search_area = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(search_area, cv2.COLOR_BGR2GRAY)
    
    _, mask = cv2.threshold(gray, min_brightness, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            return (x + cx + cw // 2, y + cy + ch // 2)
    
    return None


def find_circle_button(
    screenshot_path: str,
    region: Tuple[int, int, int, int],
    min_radius: int = 25,
    max_radius: int = 60
) -> Optional[Tuple[int, int]]:
    """
    通過圓形檢測找到按鈕（適用於播放/暫停按鈕）
    
    Args:
        screenshot_path: 截圖路徑
        region: 搜索區域 (x, y, width, height)
        min_radius: 最小半徑
        max_radius: 最大半徑
        
    Returns:
        Optional[Tuple[int, int]]: 按鈕中心座標
    """
    if not CV2_AVAILABLE:
        return None
    
    img = cv2.imread(screenshot_path)
    if img is None:
        return None
    
    x, y, w, h = region
    search_area = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(search_area, cv2.COLOR_BGR2GRAY)
    
    # 使用霍夫圓檢測
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, 1, 50,
        param1=80, param2=25,
        minRadius=min_radius, maxRadius=max_radius
    )
    
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        # 返回最大的圓
        best = max(circles, key=lambda c: c[2])
        return (x + int(best[0]), y + int(best[1]))
    
    return None


def find_green_marker(
    screenshot_path: str,
    min_y: int = 0
) -> Optional[Tuple[int, int]]:
    """
    找到綠色標記（適用於錄影指示線）
    
    Args:
        screenshot_path: 截圖路徑
        min_y: 最小 Y 座標（過濾上半部分）
        
    Returns:
        Optional[Tuple[int, int]]: 綠色標記中心座標
    """
    if not CV2_AVAILABLE:
        return None
    
    img = cv2.imread(screenshot_path)
    if img is None:
        return None
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 擴大綠色範圍
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    green_marks = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 20 < area < 15000:
            x, y, w, h = cv2.boundingRect(cnt)
            if y > min_y:
                green_marks.append((x + w // 2, y + h // 2, area))
    
    if green_marks:
        green_marks.sort(key=lambda p: p[1])
        logger.info(f"[ADB_TOOLKIT] 找到綠色標記: {green_marks[0][:2]}")
        return green_marks[0][:2]
    
    return None


class SmartLocator:
    """
    智能元素定位器
    
    結合多種識別方式自動定位 UI 元素：
    1. 圖像模板匹配（最可靠）
    2. 顏色區域檢測
    3. OCR 文字識別
    4. 配置座標作為 Fallback
    
    Example:
        locator = SmartLocator(adb_controller)
        # 使用圖片找按鈕
        pos = locator.find_element(template='res/mobile_main/calendar.png')
        # 使用文字找按鈕
        pos = locator.find_element(text='Log In')
        # 使用顏色找藍色按鈕
        pos = locator.find_element(color='blue_button')
        # 帶有 Fallback 座標
        pos = locator.find_element(template='calendar.png', fallback=(35, 2230))
    """
    
    # 預定義顏色範圍（HSV）
    COLOR_PRESETS = {
        'blue_button': ((90, 50, 50), (130, 255, 255)),
        'green_indicator': ((35, 80, 80), (85, 255, 255)),
        'red_error': ((0, 50, 50), (10, 255, 255)),
        'white_text': ((0, 0, 200), (180, 30, 255)),
        'gray_card': ((0, 0, 60), (180, 30, 140)),
    }
    
    def __init__(self, adb: 'AdbController'):
        """
        初始化智能定位器
        
        Args:
            adb: AdbController 實例
        """
        self.adb = adb
        self._screenshot_path = None
        
    def _take_screenshot(self) -> str:
        """截取並緩存螢幕截圖"""
        import tempfile
        self._screenshot_path = tempfile.mktemp(suffix='.png')
        self.adb.screenshot(self._screenshot_path)
        return self._screenshot_path
    
    def find_element(
        self,
        template: Optional[str] = None,
        text: Optional[str] = None,
        color: Optional[str] = None,
        color_range: Optional[Tuple[Tuple, Tuple]] = None,
        fallback: Optional[Tuple[int, int]] = None,
        confidence: float = 0.7,
        region: Optional[Tuple[int, int, int, int]] = None,
        refresh_screenshot: bool = True
    ) -> Optional[Tuple[int, int]]:
        """
        智能定位 UI 元素
        
        定位優先級：
        1. 圖像模板匹配（如果提供 template）
        2. OCR 文字識別（如果提供 text）
        3. 顏色區域檢測（如果提供 color 或 color_range）
        4. Fallback 座標（如果以上都失敗）
        
        Args:
            template: 模板圖片路徑（相對於專案根目錄或絕對路徑）
            text: 要搜索的文字（使用 OCR）
            color: 預設顏色名稱（'blue_button', 'green_indicator' 等）
            color_range: 自定義 HSV 顏色範圍 ((H_min, S_min, V_min), (H_max, S_max, V_max))
            fallback: 當所有識別方式都失敗時使用的座標
            confidence: 圖像匹配置信度閾值
            region: 搜索區域 (x, y, width, height)，限制搜索範圍
            refresh_screenshot: 是否重新截圖（否則使用緩存）
            
        Returns:
            Optional[Tuple[int, int]]: (x, y) 座標，或 None
        """
        # 截圖
        if refresh_screenshot or not self._screenshot_path:
            self._take_screenshot()
        
        result = None
        method_used = None
        
        # 方法 1: 圖像模板匹配
        if template and result is None:
            result = self._find_by_template(template, confidence, region)
            if result:
                method_used = f"圖像匹配 ({template})"
        
        # 方法 2: OCR 文字識別
        if text and result is None:
            result = self._find_by_text(text, region)
            if result:
                method_used = f"OCR 文字 ({text})"
        
        # 方法 3: 顏色區域檢測
        if (color or color_range) and result is None:
            result = self._find_by_color(color, color_range, region)
            if result:
                method_used = f"顏色檢測 ({color or 'custom'})"
        
        # 方法 4: Fallback 座標
        if result is None and fallback:
            result = fallback
            method_used = f"Fallback 座標 {fallback}"
        
        if result:
            logger.info(f"[SmartLocator] 定位成功: {result}，方法: {method_used}")
        else:
            logger.warning(f"[SmartLocator] 定位失敗: template={template}, text={text}, color={color}")
        
        return result
    
    def _find_by_template(
        self,
        template: str,
        confidence: float,
        region: Optional[Tuple[int, int, int, int]]
    ) -> Optional[Tuple[int, int]]:
        """使用圖像模板匹配定位"""
        import os
        
        # 處理路徑
        if not os.path.isabs(template):
            # 嘗試相對於專案根目錄
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template = os.path.join(project_root, template)
        
        if not os.path.exists(template):
            logger.warning(f"[SmartLocator] 模板圖片不存在: {template}")
            return None
        
        result = find_image_on_screen(self._screenshot_path, template, confidence)
        if result:
            return (result[0], result[1])
        return None
    
    def _find_by_text(
        self,
        text: str,
        region: Optional[Tuple[int, int, int, int]]
    ) -> Optional[Tuple[int, int]]:
        """使用 OCR 文字識別定位"""
        try:
            # 嘗試使用 pytesseract
            import pytesseract
            from PIL import Image
            
            img = Image.open(self._screenshot_path)
            
            # 如果指定了區域，裁切圖片
            if region:
                x, y, w, h = region
                img = img.crop((x, y, x + w, y + h))
                offset_x, offset_y = x, y
            else:
                offset_x, offset_y = 0, 0
            
            # OCR 識別並取得位置資訊
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            for i, txt in enumerate(data['text']):
                if text.lower() in str(txt).lower():
                    x = data['left'][i] + data['width'][i] // 2 + offset_x
                    y = data['top'][i] + data['height'][i] // 2 + offset_y
                    return (x, y)
            
            return None
            
        except ImportError:
            logger.warning("[SmartLocator] pytesseract 未安裝，無法使用 OCR")
            return None
        except Exception as e:
            logger.warning(f"[SmartLocator] OCR 識別失敗: {e}")
            return None
    
    def _find_by_color(
        self,
        color_name: Optional[str],
        color_range: Optional[Tuple[Tuple, Tuple]],
        region: Optional[Tuple[int, int, int, int]]
    ) -> Optional[Tuple[int, int]]:
        """使用顏色區域檢測定位"""
        if color_name and color_name in self.COLOR_PRESETS:
            lower, upper = self.COLOR_PRESETS[color_name]
        elif color_range:
            lower, upper = color_range
        else:
            return None
        
        result = find_color_region(self._screenshot_path, lower, upper)
        
        if result:
            center_x, center_y, w, h = result
            
            # 如果指定了區域，檢查是否在區域內
            if region:
                rx, ry, rw, rh = region
                if not (rx <= center_x <= rx + rw and ry <= center_y <= ry + rh):
                    return None
            
            return (center_x, center_y)
        
        return None
    
    def tap_element(
        self,
        template: Optional[str] = None,
        text: Optional[str] = None,
        color: Optional[str] = None,
        fallback: Optional[Tuple[int, int]] = None,
        wait: float = 0.5,
        **kwargs
    ) -> bool:
        """
        智能定位並點擊元素
        
        Args:
            template: 模板圖片路徑
            text: 要搜索的文字
            color: 顏色預設名稱
            fallback: Fallback 座標
            wait: 點擊後等待時間
            **kwargs: 傳遞給 find_element 的其他參數
            
        Returns:
            bool: 是否成功點擊
        """
        pos = self.find_element(
            template=template,
            text=text,
            color=color,
            fallback=fallback,
            **kwargs
        )
        
        if pos:
            self.adb.tap(pos[0], pos[1], wait=wait)
            return True
        
        return False
    
    def find_thumbnail(self, fallback: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        智能定位影片縮圖
        
        使用亮度檢測找到非黑色的縮圖區域
        """
        self._take_screenshot()
        
        # 在上半部分搜索縮圖
        width, height = self.adb.get_screen_size()
        pos = find_element_by_brightness(
            self._screenshot_path,
            region=(0, 100, width, 400),
            min_brightness=30,
            min_area=8000
        )
        
        if pos:
            logger.info(f"[SmartLocator] 找到影片縮圖: {pos}")
            return pos
        
        if fallback:
            logger.info(f"[SmartLocator] 使用 Fallback: {fallback}")
            return fallback
        
        return None
    
    def find_play_pause_button(self, fallback: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        智能定位播放/暫停按鈕
        
        使用圓形檢測找到控制按鈕，或使用模板匹配
        """
        self._take_screenshot()
        
        width, height = self.adb.get_screen_size()
        
        # 方法 1: 嘗試模板匹配（優先使用正確的模板）
        import os
        templates = [
            'res/mobile_main/pause_correct.png',
            'res/mobile_main/play_button.png',
            'res/mobile_main/pause.png'
        ]
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for tmpl in templates:
            tmpl_path = os.path.join(project_root, tmpl)
            if os.path.exists(tmpl_path):
                result = find_image_on_screen(self._screenshot_path, tmpl_path, confidence=0.5)
                if result:
                    logger.info(f"[SmartLocator] 找到播放/暫停按鈕 (模板): {result[:2]}")
                    return (result[0], result[1])
        
        # 方法 2: 圓形檢測 - 暫停按鈕在螢幕中央偏下 Y=1800-2000
        pos = find_circle_button(
            self._screenshot_path,
            region=(width // 4, int(height * 0.75), width // 2, int(height * 0.1)),
            min_radius=30,
            max_radius=60
        )
        
        if pos:
            logger.info(f"[SmartLocator] 找到播放/暫停按鈕 (圓形): {pos}")
            return pos
        
        if fallback:
            logger.info(f"[SmartLocator] 使用 Fallback: {fallback}")
            return fallback
        
        return None
    
    def find_calendar_icon(self, fallback: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        智能定位日曆圖標
        
        日曆圖標位於底部工具欄左側，使用模板匹配。
        嘗試多個模板，只搜索螢幕底部區域以避免誤匹配。
        """
        self._take_screenshot()
        
        width, height = self.adb.get_screen_size()
        
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 嘗試多個模板（優先使用正確的模板）
        templates = [
            ('res/mobile_main/calendar_correct.png', 0.6),
            ('res/mobile_main/calendar.png', 0.6),
        ]
        
        for tmpl, conf_threshold in templates:
            tmpl_path = os.path.join(project_root, tmpl)
            if os.path.exists(tmpl_path):
                result = find_image_on_screen(self._screenshot_path, tmpl_path, confidence=conf_threshold)
                if result:
                    x, y, conf = result
                    # 日曆圖標應該在底部區域 (Y > height * 0.85)
                    if y > height * 0.85:
                        logger.info(f"[SmartLocator] 找到日曆圖標: ({x}, {y}), 置信度={conf:.3f}")
                        return (x, y)
                    else:
                        logger.debug(f"[SmartLocator] 模板匹配位置不在底部 ({x}, {y})，忽略")
        
        if fallback:
            logger.info(f"[SmartLocator] 日曆圖標使用 Fallback: {fallback}")
            return fallback
        
        return None
    
    def find_green_recording_date(self, fallback: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        智能定位有錄影的日期（綠色標記）
        """
        self._take_screenshot()
        
        width, height = self.adb.get_screen_size()
        
        pos = find_green_marker(self._screenshot_path, min_y=height // 2)
        
        if pos:
            # 點擊綠線上方（日期位置）
            return (pos[0], pos[1] - 20)
        
        if fallback:
            logger.info(f"[SmartLocator] 使用 Fallback: {fallback}")
            return fallback
        
        return None
