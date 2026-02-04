# 相對路徑: pages/mobile/adb_playback_page.py
"""
Nx Witness 移動端播放頁面 (ADB 版本)

基於 ADB 的 Page Object，提供原子操作：
- 點擊日曆圖標
- 點擊有錄影的日期
- 點擊暫停按鈕
- 顯示/隱藏控制欄

遵循 SOLID 原則：
- SRP: 只負責播放頁面的元素操作，不包含業務邏輯
- OCP: 通過配置參數擴展，不修改核心邏輯
- ISP: 繼承 MobileApp 獲取基礎設施
"""

import time
from typing import Optional, Tuple, List

import cv2
import numpy as np

from base.mobile_app import MobileApp
from toolkit.adb_toolkit import AdbController
from config import EnvConfig


class AdbPlaybackPage(MobileApp):
    """
    Nx Witness 移動端播放頁面 (ADB 版本)
    
    職責：
    - 封裝播放頁面的原子操作（點擊日曆、點擊日期、點擊暫停等）
    - 提供元素座標和狀態查詢
    
    禁止：
    - 包含斷言 (Assertions)
    - 包含業務流程邏輯
    """
    
    def __init__(self, adb: Optional[AdbController] = None):
        """
        初始化播放頁面
        
        Args:
            adb: AdbController 實例，如果為 None 則自動創建
        """
        super().__init__(adb)
        
        # 從配置讀取座標（Data-Driven 原則）
        self._calendar_coords = EnvConfig.CASE4_2_CALENDAR_ICON_COORDINATES
        self._today_coords = EnvConfig.CASE4_2_TODAY_DATE_COORDINATES
        self._pause_coords = EnvConfig.CASE4_2_PAUSE_BUTTON_COORDINATES
        self._show_controls_coords = EnvConfig.CASE4_2_SHOW_CONTROLS_TAP
    
    # ==================== 原子操作 ====================
    
    def tap_calendar_icon(self, wait: float = 2.0) -> bool:
        """
        點擊日曆圖標
        
        設計考量：
        - 從影片縮圖進入後，控制欄通常已顯示
        - 直接點擊日曆座標，避免額外操作導致控制欄隱藏
        
        Args:
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[ADB_PLAYBACK] 點擊日曆圖標: {self._calendar_coords}")
        try:
            self.adb.tap(self._calendar_coords[0], self._calendar_coords[1], wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 點擊日曆圖標失敗: {e}")
            return False
    
    def tap_recording_date(self, wait: float = 3.0) -> bool:
        """
        點擊有錄影的日期（日曆視圖中有綠線標記的日期）
        
        Args:
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[ADB_PLAYBACK] 點擊有錄影的日期: {self._today_coords}")
        try:
            # 等待日曆動畫完成
            time.sleep(0.5)
            self.adb.tap(self._today_coords[0], self._today_coords[1], wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 點擊日期失敗: {e}")
            return False
    
    def tap_pause_button(self, wait: float = 1.0) -> bool:
        """
        點擊暫停按鈕
        
        設計考量：
        - 直接點擊暫停按鈕座標
        - 不先點畫面，避免切換控制欄狀態
        
        Args:
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[ADB_PLAYBACK] 點擊暫停按鈕: {self._pause_coords}")
        try:
            self.adb.tap(self._pause_coords[0], self._pause_coords[1], wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 點擊暫停按鈕失敗: {e}")
            return False
    
    def tap_play_button(self, wait: float = 1.0) -> bool:
        """
        點擊播放按鈕（與暫停按鈕位置相同，狀態不同）
        
        Args:
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[ADB_PLAYBACK] 點擊播放按鈕: {self._pause_coords}")
        try:
            self.adb.tap(self._pause_coords[0], self._pause_coords[1], wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 點擊播放按鈕失敗: {e}")
            return False
    
    def toggle_controls(self, wait: float = 0.3) -> bool:
        """
        切換控制欄顯示狀態（點擊畫面中心區域）
        
        注意：此操作會切換控制欄狀態
        - 如果控制欄顯示 → 點擊會隱藏
        - 如果控制欄隱藏 → 點擊會顯示
        
        Args:
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[ADB_PLAYBACK] 切換控制欄: {self._show_controls_coords}")
        try:
            self.adb.tap(self._show_controls_coords[0], self._show_controls_coords[1], wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 切換控制欄失敗: {e}")
            return False
    
    def tap_at(self, x: int, y: int, wait: float = 0.5) -> bool:
        """
        在指定座標點擊（通用方法）
        
        Args:
            x: X 座標
            y: Y 座標
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.debug(f"[ADB_PLAYBACK] 點擊座標: ({x}, {y})")
        try:
            self.adb.tap(x, y, wait=wait)
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 點擊座標失敗: {e}")
            return False
    
    # ==================== 元素查找 ====================
    
    def find_green_date_in_calendar(self, img_path: str) -> Optional[Tuple[int, int]]:
        """
        在日曆中找到有綠線的日期
        
        綠線表示該日期有錄影，用於選擇要播放的日期
        
        Args:
            img_path: 截圖路徑
            
        Returns:
            Optional[Tuple[int, int]]: 綠色日期座標 (x, y)，未找到返回 None
        """
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        height, width = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 綠色範圍（進度條/錄影指示）
        lower_green = np.array([35, 80, 80])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 找到日曆區域內的綠色標記（日曆通常在螢幕下半部分）
        calendar_y_min = height // 2
        
        green_dates: List[Tuple[int, int, float]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 5000:  # 綠線標記大小
                x, y, w, h = cv2.boundingRect(cnt)
                if y > calendar_y_min:
                    center_x = x + w // 2
                    center_y = y + h // 2
                    green_dates.append((center_x, center_y, area))
        
        if green_dates:
            # 返回第一個（最靠近左上的）綠色日期
            green_dates.sort(key=lambda p: (p[1], p[0]))
            result = (green_dates[0][0], green_dates[0][1])
            self.logger.info(f"[ADB_PLAYBACK] 找到綠色日期: {result}")
            return result
        
        self.logger.warning("[ADB_PLAYBACK] 未找到綠色日期")
        return None
    
    def find_pause_button(self, img_path: str) -> Optional[Tuple[int, int]]:
        """
        找到暫停按鈕位置
        
        暫停按鈕通常在螢幕下半部中央
        
        Args:
            img_path: 截圖路徑（用於獲取尺寸）
            
        Returns:
            Optional[Tuple[int, int]]: 暫停按鈕座標 (x, y)
        """
        img = cv2.imread(img_path)
        if img is None:
            # 使用配置的座標
            return self._pause_coords
        
        height, width = img.shape[:2]
        
        # 暫停按鈕在螢幕中央偏下（約 66% 高度）
        pause_x = width // 2
        pause_y = int(height * 0.66)
        
        self.logger.debug(f"[ADB_PLAYBACK] 暫停按鈕估計位置: ({pause_x}, {pause_y})")
        return (pause_x, pause_y)
    
    # ==================== 截圖與診斷 ====================
    
    def take_screenshot(self, save_path: str) -> bool:
        """
        截取當前畫面
        
        Args:
            save_path: 截圖保存路徑
            
        Returns:
            bool: 截圖是否成功
        """
        try:
            self.adb.screenshot(save_path)
            self.logger.debug(f"[ADB_PLAYBACK] 截圖已保存: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 截圖失敗: {e}")
            return False
    
    def take_screenshot_with_click_marker(
        self,
        save_path: str,
        click_x: int,
        click_y: int,
        element_name: str = "點擊位置",
        element_box: Optional[Tuple[int, int, int, int]] = None
    ) -> bool:
        """
        截圖並在圖中標記點擊位置
        
        Args:
            save_path: 截圖保存路徑
            click_x: 點擊 X 座標
            click_y: 點擊 Y 座標
            element_name: 元素名稱
            element_box: 元素邊界框 (x, y, width, height)，用於框出匹配的物件
            
        Returns:
            bool: 截圖是否成功
        """
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        import os
        
        try:
            # 先截圖到臨時文件
            temp_path = tempfile.mktemp(suffix='.png')
            self.adb.screenshot(temp_path)
            
            # 讀取截圖
            img = Image.open(temp_path)
            draw = ImageDraw.Draw(img)
            
            # 繪製十字準星（綠色）
            cross_size = 20
            draw.line([(click_x - cross_size, click_y), (click_x + cross_size, click_y)], 
                      fill='green', width=4)
            draw.line([(click_x, click_y - cross_size), (click_x, click_y + cross_size)], 
                      fill='green', width=4)
            
            # 繪製圓點（綠色）
            circle_radius = 8
            draw.ellipse(
                [click_x - circle_radius, click_y - circle_radius,
                 click_x + circle_radius, click_y + circle_radius],
                fill='green', outline='darkgreen', width=2
            )
            
            # 標註元素名稱和座標
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            label = f"{element_name} ({click_x}, {click_y})"
            text_bbox = draw.textbbox((click_x + 15, click_y - 30), label, font=font)
            draw.rectangle(
                [text_bbox[0] - 3, text_bbox[1] - 3, text_bbox[2] + 3, text_bbox[3] + 3],
                fill='green'
            )
            draw.text((click_x + 15, click_y - 30), label, fill='white', font=font)
            
            # 如果有元素邊界框，繪製紅色框
            if element_box:
                box_x, box_y, box_w, box_h = element_box
                draw.rectangle(
                    [box_x, box_y, box_x + box_w, box_y + box_h],
                    outline='red', width=3
                )
            
            # 保存
            img.save(save_path)
            
            # 清理臨時文件
            try:
                os.unlink(temp_path)
            except:
                pass
            
            self.logger.debug(f"[ADB_PLAYBACK] 標記截圖已保存: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ADB_PLAYBACK] 標記截圖失敗: {e}")
            return False
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        獲取設備屏幕尺寸
        
        Returns:
            Tuple[int, int]: (寬度, 高度)
        """
        return self.adb.get_screen_size()
    
    # ==================== 座標屬性（唯讀）====================
    
    @property
    def calendar_icon_coords(self) -> Tuple[int, int]:
        """日曆圖標座標"""
        return self._calendar_coords
    
    @property
    def recording_date_coords(self) -> Tuple[int, int]:
        """有錄影的日期座標"""
        return self._today_coords
    
    @property
    def pause_button_coords(self) -> Tuple[int, int]:
        """暫停按鈕座標"""
        return self._pause_coords
