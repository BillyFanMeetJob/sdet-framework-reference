# 相對路徑: pages/mobile/base_mobile_page.py
"""
移動端 Page Object 基類（已廢棄）

⚠️ 注意：此文件已廢棄，實際 Android 測試使用 ADB + OpenCV 方式

真正使用的文件：
- pages/mobile/adb_login_page.py (ADB + 圖像識別 - Case 4-1)
- pages/mobile/adb_playback_page.py (ADB + 圖像識別 - Case 4-2)
- toolkit/adb_toolkit.py (ADB 工具類)

為什麼廢棄 Appium/UiAutomator2：
1. Appium 不穩定，經常超時
2. UiAutomator2 無法識別 SurfaceView 渲染的視頻畫面
3. ADB + OpenCV 更快速、更可靠

保留此文件僅為了向後兼容（避免導入錯誤）
"""

from typing import Optional
from toolkit.logger import get_logger


class BaseMobilePage:
    """
    移動端 Page Object 基類（已廢棄）
    
    ⚠️ 此類已不再使用，保留僅為了向後兼容
    
    實際 Android 測試使用：
    - ADB + OpenCV 圖像識別（Case 4-1, 4-2）
    - 參見：pages/mobile/adb_login_page.py
    - 參見：pages/mobile/adb_playback_page.py
    """
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化移動端頁面基類
        
        Args:
            driver: Appium WebDriver 實例（未使用）
        """
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)
        self.wait = None
        
        if driver:
            self.logger.warning(
                "[DEPRECATED] BaseMobilePage 已廢棄，"
                "實際測試使用 ADB + OpenCV 方式"
            )
    
    def set_driver(self, driver: object) -> 'BaseMobilePage':
        """
        設置 Appium WebDriver 實例（未使用）
        
        Args:
            driver: Appium WebDriver 實例
            
        Returns:
            BaseMobilePage: 返回自身以支持鏈式調用
        """
        self.driver = driver
        return self


# ==================== 使用說明 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("BaseMobilePage（已廢棄）")
    print("=" * 60)
    print()
    print("⚠️ 此類已不再使用於實際測試")
    print()
    print("實際 Android 測試使用：")
    print("  1. ADB + OpenCV 圖像識別（Case 4-1, 4-2）")
    print("     - pages/mobile/adb_login_page.py")
    print("     - pages/mobile/adb_playback_page.py")
    print("     - toolkit/adb_toolkit.py")
    print()
    print("  2. 優勢：")
    print("     - 更穩定（不依賴 Appium/UiAutomator2）")
    print("     - 更快速（直接使用 ADB 命令）")
    print("     - 更可靠（圖像識別 + 顏色檢測）")
    print()
    print("  3. 為什麼廢棄 Appium：")
    print("     - Appium 不穩定，經常超時")
    print("     - UiAutomator2 無法識別 SurfaceView")
    print("     - ADB 方式更適合視頻播放測試")
    print()
    print("=" * 60)
