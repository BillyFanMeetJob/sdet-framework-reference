# 相對路徑: base/mobile_app.py
"""
移動端應用基礎類別

提供 Android 自動化的基礎設施，類似於 DesktopApp 的角色。
使用 ADB + OpenCV 圖像識別方式，不依賴 Appium/UiAutomator2。

職責：
- 封裝 ADB 控制器和智能定位器的初始化
- 提供通用的圖像處理工具方法
- 管理螢幕尺寸和設備連接

遵循 SOLID 原則：
- SRP: 只負責移動端基礎設施，不包含業務邏輯
- DIP: 依賴 AdbController 抽象
- OCP: 可擴展但不可修改
"""

import os
from typing import Optional, Tuple
import cv2
import numpy as np

from toolkit.adb_toolkit import AdbController, SmartLocator
from toolkit.logger import get_logger


class MobileApp:
    """
    移動端應用基礎類別
    
    提供 Android 自動化的基礎設施，包括：
    - ADB 控制器管理
    - 智能定位器 (SmartLocator)
    - 螢幕尺寸獲取
    - 圖像處理工具方法
    
    使用方式：
        app = MobileApp()
        width, height = app.screen_size
        app.adb.tap(100, 200)
    """
    
    def __init__(self, adb: Optional[AdbController] = None):
        """
        初始化移動端應用
        
        Args:
            adb: AdbController 實例，如果為 None 則自動創建
        """
        self.adb = adb or AdbController()
        self.locator = SmartLocator(self.adb)
        self.logger = get_logger(self.__class__.__name__)
        
        # 獲取螢幕尺寸
        self._width, self._height = self.adb.get_screen_size()
        
        if not self.adb.is_connected():
            self.logger.error("[MOBILE_APP] 未找到已連接的 Android 設備")
        else:
            self.logger.info(f"[MOBILE_APP] 已連接設備，螢幕尺寸: {self._width} x {self._height}")
    
    @property
    def screen_size(self) -> Tuple[int, int]:
        """
        獲取螢幕尺寸
        
        Returns:
            Tuple[int, int]: (寬度, 高度)
        """
        return self._width, self._height
    
    @property
    def screen_width(self) -> int:
        """獲取螢幕寬度"""
        return self._width
    
    @property
    def screen_height(self) -> int:
        """獲取螢幕高度"""
        return self._height
    
    def is_connected(self) -> bool:
        """
        檢查設備是否已連接
        
        Returns:
            bool: 設備是否已連接
        """
        return self.adb.is_connected()
    
    # ==================== 圖像處理工具方法 ====================
    
    @staticmethod
    def imread_unicode(img_path: str) -> Optional[np.ndarray]:
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
            logger = get_logger("MobileApp")
            logger.error(f"[MOBILE_APP] 無法讀取圖片 {img_path}: {e}")
            return None
    
    @staticmethod
    def save_image_unicode(img: np.ndarray, img_path: str) -> bool:
        """
        保存圖片文件，支持中文路徑
        
        使用 cv2.imencode + tofile 繞過 OpenCV 的路徑編碼問題
        
        Args:
            img: numpy 數組（圖片）
            img_path: 保存路徑（可包含中文字符）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            
            # 使用 cv2 編碼，再用 numpy 寫入文件
            ext = os.path.splitext(img_path)[1]
            is_success, buffer = cv2.imencode(ext, img)
            if is_success:
                buffer.tofile(img_path)
                return True
            return False
        except Exception as e:
            logger = get_logger("MobileApp")
            logger.error(f"[MOBILE_APP] 無法保存圖片 {img_path}: {e}")
            return False
    
    def take_screenshot(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        截取當前螢幕
        
        Args:
            save_path: 保存路徑（可選），如果提供則保存到文件
            
        Returns:
            numpy 數組（圖片）或 None（如果失敗）
        """
        try:
            screenshot = self.adb.screenshot()
            
            if screenshot is not None and save_path:
                self.save_image_unicode(screenshot, save_path)
                self.logger.debug(f"[MOBILE_APP] 截圖已保存: {save_path}")
            
            return screenshot
        except Exception as e:
            self.logger.error(f"[MOBILE_APP] 截圖失敗: {e}")
            return None
    
    # ==================== 通用操作方法 ====================
    
    def tap(self, x: int, y: int, wait: float = 1.0) -> bool:
        """
        點擊指定座標
        
        Args:
            x: X 座標
            y: Y 座標
            wait: 點擊後等待時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        try:
            self.adb.tap(x, y, wait=wait)
            self.logger.debug(f"[MOBILE_APP] 點擊座標: ({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"[MOBILE_APP] 點擊失敗: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """
        輸入文字
        
        Args:
            text: 要輸入的文字
            
        Returns:
            bool: 輸入是否成功
        """
        try:
            self.adb.input_text(text)
            self.logger.debug(f"[MOBILE_APP] 輸入文字: {text}")
            return True
        except Exception as e:
            self.logger.error(f"[MOBILE_APP] 輸入文字失敗: {e}")
            return False
    
    def press_back(self) -> bool:
        """
        按返回鍵
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.adb.press_back()
            self.logger.debug("[MOBILE_APP] 按下返回鍵")
            return True
        except Exception as e:
            self.logger.error(f"[MOBILE_APP] 按返回鍵失敗: {e}")
            return False
    
    def press_home(self) -> bool:
        """
        按 Home 鍵
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.adb.press_home()
            self.logger.debug("[MOBILE_APP] 按下 Home 鍵")
            return True
        except Exception as e:
            self.logger.error(f"[MOBILE_APP] 按 Home 鍵失敗: {e}")
            return False


# ==================== 使用範例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("MobileApp 基礎類別")
    print("=" * 60)
    print()
    print("提供 Android 自動化的基礎設施：")
    print("  - ADB 控制器管理")
    print("  - 智能定位器 (SmartLocator)")
    print("  - 螢幕尺寸獲取")
    print("  - 圖像處理工具方法")
    print()
    print("使用範例:")
    print("""
    from base.mobile_app import MobileApp
    
    # 初始化
    app = MobileApp()
    
    # 獲取螢幕尺寸
    width, height = app.screen_size
    print(f"螢幕尺寸: {width} x {height}")
    
    # 點擊座標
    app.tap(100, 200)
    
    # 輸入文字
    app.input_text("Hello World")
    
    # 截圖
    screenshot = app.take_screenshot("screenshot.png")
    """)
    print()
    print("=" * 60)
