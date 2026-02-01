# 相對路徑: pages/mobile/adb_login_page.py
"""
Nx Witness 移動端登錄頁面 (ADB 版本)

基於 ADB 的 Page Object，提供原子操作：
- 檢測頁面狀態（已登錄/登錄頁面）
- 找到藍色按鈕（Log In / Next）
- 點擊輸入框
- 輸入文字

遵循 SOLID 原則：
- SRP: 只負責登錄頁面的元素操作，不包含業務邏輯
- OCP: 通過配置參數擴展，不修改核心邏輯
"""

import os
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from toolkit.adb_toolkit import AdbController
from toolkit.logger import get_logger


class AdbLoginPage:
    """
    Nx Witness 移動端登錄頁面 (ADB 版本)
    
    職責：
    - 封裝登錄頁面的原子操作（檢測狀態、找按鈕、點擊、輸入等）
    - 提供元素位置查詢
    
    禁止：
    - 包含斷言 (Assertions)
    - 包含業務流程邏輯
    """
    
    def __init__(self, adb: Optional[AdbController] = None):
        """
        初始化登錄頁面
        
        Args:
            adb: AdbController 實例，如果為 None 則自動創建
        """
        self.adb = adb or AdbController()
        self.logger = get_logger(self.__class__.__name__)
        self._width, self._height = self.adb.get_screen_size()
    
    def _imread_unicode(self, img_path: str) -> Optional[np.ndarray]:
        """
        讀取圖片文件，支持中文路徑
        
        使用 np.fromfile + cv2.imdecode 繞過 OpenCV 的路徑編碼問題
        
        Args:
            img_path: 圖片路徑（可包含中文字符）
            
        Returns:
            numpy 數組或 None（如果讀取失敗）
        """
        try:
            # 使用 numpy 讀取文件字節，再用 cv2 解碼
            img_array = np.fromfile(img_path, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            self.logger.error(f"[ADB_LOGIN] 無法讀取圖片 {img_path}: {e}")
            return None
    
    # ==================== 頁面狀態檢測 ====================
    
    def detect_page_state(self, img_path: str) -> str:
        """
        檢測當前頁面狀態
        
        通過分析截圖特徵判斷：
        - 左上角有藍色圓形 → 已登錄 (logged_in)
        - 有藍色按鈕 + 按鈕在屏幕中央 → 初始登錄頁面 (login_page)
        - 有藍色按鈕 + 按鈕在右側 + 有輸入框邊框 → Email/密碼輸入頁面 (email_input)
        - 其他 → 未知 (unknown)
        
        Args:
            img_path: 截圖路徑
            
        Returns:
            str: 'logged_in' | 'login_page' | 'email_input' | 'unknown'
        """
        img = self._imread_unicode(img_path)
        if img is None:
            self.logger.warning(f"[ADB_LOGIN] 無法讀取圖片: {img_path}")
            return 'unknown'
        
        height, width = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 藍色範圍
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 檢查左上角藍色區域（已登錄時會有用戶頭像）
        top_left = blue_mask[60:260, 10:210]
        blue_pixels_tl = cv2.countNonZero(top_left)
        if blue_pixels_tl > 300:
            self.logger.debug("[ADB_LOGIN] 檢測到已登錄狀態（有藍色頭像）")
            return 'logged_in'
        
        # 檢查頂部是否有搜索框（已登錄頁面的特徵）
        # 搜索框是深灰色背景，位於頂部（約 60-110 像素高）
        search_region = gray[60:130, int(width * 0.1):int(width * 0.85)]
        search_mean = np.mean(search_region)
        # 搜索框區域的亮度在 30-80 之間（深灰色背景）
        has_search_bar = 25 < search_mean < 90
        
        # 檢查是否有卡片區域（已登錄頁面特徵）
        # 卡片區域在屏幕中部，是淺色塊狀
        card_region = gray[int(height * 0.1):int(height * 0.35), int(width * 0.05):int(width * 0.95)]
        card_edges = cv2.Canny(card_region, 30, 100)
        card_edge_pixels = cv2.countNonZero(card_edges)
        has_cards = card_edge_pixels > 500
        
        # 如果有搜索框且有卡片，但沒有藍色按鈕 -> 已登錄
        # (這種情況下沒有 Log In 按鈕可見)
        
        # 找到藍色按鈕位置
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blue_button_info = None
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 5000:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = w / h if h > 0 else 0
                # 按鈕形狀：寬高比 1.5-10，寬度 100-1000
                if 1.5 < aspect < 10.0 and 100 < w < 1000:
                    center_x = x + w // 2
                    center_x_ratio = center_x / width
                    blue_button_info = {
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x_ratio': center_x_ratio,
                        'area': area
                    }
                    break
        
        if not blue_button_info:
            # 沒有藍色按鈕，檢查是否是已登錄狀態
            # 已登錄狀態的特徵：有搜索框（或灰色頂部工具欄）且沒有 Login 按鈕
            if has_search_bar:
                self.logger.debug("[ADB_LOGIN] 檢測到已登錄狀態（有搜索框，無登錄按鈕）")
                return 'logged_in'
            return 'unknown'
        
        # 根據按鈕的水平位置判斷頁面類型
        # - 初始登錄頁: 按鈕在中央 (center_x_ratio 約 0.4-0.6)
        # - Email輸入頁: 按鈕在右側 (center_x_ratio > 0.7)
        center_x_ratio = blue_button_info['center_x_ratio']
        
        self.logger.debug(f"[ADB_LOGIN] 按鈕水平位置比例: {center_x_ratio:.2f}")
        
        if center_x_ratio > 0.70:
            # 按鈕在右側 → Email/密碼輸入頁面
            self.logger.debug("[ADB_LOGIN] 檢測到輸入頁面（按鈕在右側）")
            return 'email_input'
        elif 0.35 < center_x_ratio < 0.65:
            # 按鈕在中央 → 初始登錄頁面
            self.logger.debug("[ADB_LOGIN] 檢測到初始登錄頁面（按鈕在中央）")
            return 'login_page'
        else:
            self.logger.debug(f"[ADB_LOGIN] 未知頁面（按鈕位置: {center_x_ratio:.2f}）")
            return 'unknown'
    
    def find_blue_button(self, img_path: str) -> Optional[Tuple[int, int]]:
        """
        找到藍色按鈕的中心坐標
        
        用於定位 Log In / Next 等藍色按鈕
        
        Args:
            img_path: 截圖路徑
            
        Returns:
            Optional[Tuple[int, int]]: 按鈕中心座標 (x, y)，未找到返回 None
        """
        img = self._imread_unicode(img_path)
        if img is None:
            self.logger.warning(f"[ADB_LOGIN] 無法讀取圖片: {img_path}")
            return None
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best = None
        max_area = 0
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 5000:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = w / h if h > 0 else 0
                # 按鈕形狀：寬高比 2-10，寬度 150-1000
                if 2.0 < aspect < 10.0 and 150 < w < 1000:
                    if area > max_area:
                        max_area = area
                        best = (x + w // 2, y + h // 2)
        
        if best:
            self.logger.debug(f"[ADB_LOGIN] 找到藍色按鈕: {best}")
        return best
    
    # ==================== 原子操作 ====================
    
    def tap_login_button(self, img_path: str, fallback: Optional[Tuple[int, int]] = None) -> bool:
        """
        點擊 Log In 按鈕
        
        Args:
            img_path: 截圖路徑（用於找按鈕）
            fallback: 備用座標
            
        Returns:
            bool: 點擊是否成功
        """
        pos = self.find_blue_button(img_path)
        if pos:
            self.logger.info(f"[ADB_LOGIN] 點擊 Log In 按鈕: {pos}")
            self.adb.tap(pos[0], pos[1])
            return True
        elif fallback:
            self.logger.info(f"[ADB_LOGIN] 使用 Fallback 點擊: {fallback}")
            self.adb.tap(fallback[0], fallback[1])
            return True
        return False
    
    def tap_email_input(self, wait: float = 0.5) -> bool:
        """
        點擊 Email 輸入框
        
        Email 輸入框位於屏幕中央偏上（約 46% 高度）
        
        Args:
            wait: 點擊後等待時間
            
        Returns:
            bool: 點擊是否成功
        """
        email_x = self._width // 2
        email_y = int(self._height * 0.46)
        self.logger.debug(f"[ADB_LOGIN] 點擊 Email 輸入框: ({email_x}, {email_y})")
        self.adb.tap(email_x, email_y, wait=wait)
        return True
    
    def tap_password_input(self, wait: float = 0.5) -> bool:
        """
        點擊密碼輸入框
        
        密碼輸入框位於屏幕中央偏上（約 47% 高度）
        
        Args:
            wait: 點擊後等待時間
            
        Returns:
            bool: 點擊是否成功
        """
        password_x = self._width // 2
        password_y = int(self._height * 0.47)
        self.logger.debug(f"[ADB_LOGIN] 點擊密碼輸入框: ({password_x}, {password_y})")
        self.adb.tap(password_x, password_y, wait=wait)
        return True
    
    def input_text(self, text: str) -> bool:
        """
        輸入文字
        
        Args:
            text: 要輸入的文字
            
        Returns:
            bool: 輸入是否成功
        """
        self.adb.input_text(text)
        return True
    
    def clear_and_input(self, x: int, y: int, text: str) -> bool:
        """
        清空輸入框並輸入文字
        
        Args:
            x: 輸入框 X 座標
            y: 輸入框 Y 座標
            text: 要輸入的文字
            
        Returns:
            bool: 操作是否成功
        """
        self.adb.clear_input(x, y)
        self.adb.input_text(text)
        return True
    
    def dismiss_keyboard(self, tap_y_ratio: float = 0.15) -> bool:
        """
        關閉鍵盤
        
        通過點擊屏幕上方區域來關閉鍵盤
        
        Args:
            tap_y_ratio: 點擊位置的 Y 比例
            
        Returns:
            bool: 操作是否成功
        """
        tap_x = self._width // 2
        tap_y = int(self._height * tap_y_ratio)
        self.adb.tap(tap_x, tap_y, wait=0.5)
        return True
    
    def press_back(self) -> bool:
        """
        按返回鍵（關閉彈窗等）
        
        Returns:
            bool: 操作是否成功
        """
        self.adb.run_cmd(['shell', 'input', 'keyevent', '4'], silent=True)
        return True
    
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
            return True
        except Exception as e:
            self.logger.error(f"[ADB_LOGIN] 截圖失敗: {e}")
            return False
    
    @property
    def screen_size(self) -> Tuple[int, int]:
        """獲取屏幕尺寸"""
        return self._width, self._height
