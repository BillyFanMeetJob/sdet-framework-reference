# 相對路徑: base/android_app.py
"""
Android App 基礎類別

⚠️ 注意：此文件僅用於 base_page_unified.py 的多平台統一接口
實際的 Android 測試使用 ADB + OpenCV 圖像識別（更穩定）

真正使用的 Android 基類是 pages/mobile/base_mobile_page.py
"""

from typing import Optional
from toolkit.logger import get_logger


class AndroidApp:
    """
    Android App 基礎類別
    
    此類僅用於 base_page_unified.py 的統一接口，
    實際 Android 測試（Case 4-1, 4-2）使用 ADB + OpenCV 方式。
    
    真正的實現在：
    - pages/mobile/base_mobile_page.py (完整的 Appium 封裝)
    - pages/mobile/adb_login_page.py (ADB + 圖像識別)
    - pages/mobile/adb_playback_page.py (ADB + 圖像識別)
    """
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化 Android App 基類
        
        Args:
            driver: Appium WebDriver 實例（可選）
        """
        self.logger = get_logger(self.__class__.__name__)
        self.driver = driver
    
    def set_driver(self, driver: object) -> 'AndroidApp':
        """
        設置 Appium driver
        
        Args:
            driver: Appium WebDriver 實例
            
        Returns:
            AndroidApp: 返回自身以支持鏈式調用
        """
        self.driver = driver
        return self


# ==================== 使用說明 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("AndroidApp 基礎類別")
    print("=" * 60)
    print()
    print("⚠️ 此類僅用於 base_page_unified.py 的統一接口")
    print()
    print("實際 Android 測試使用：")
    print("  1. ADB + OpenCV 圖像識別（Case 4-1, 4-2）")
    print("     - pages/mobile/adb_login_page.py")
    print("     - pages/mobile/adb_playback_page.py")
    print()
    print("  2. Appium/UiAutomator2（備用方案）")
    print("     - pages/mobile/base_mobile_page.py")
    print("     - pages/mobile/login_page.py")
    print("     - pages/mobile/main_page.py")
    print("     - pages/mobile/playback_page.py")
    print()
    print("=" * 60)