# 相對路徑: base/base_page_unified.py
"""
統一的 Page 基類 - 支援多平台
根據當前平台自動選擇對應的操作方式
"""

from typing import Optional
from toolkit.logger import get_logger
from config_enhanced import ConfigManager, PlatformType


class UnifiedPage:
    """
    統一的 Page 基類
    根據當前平台自動適配操作方式
    """
    
    def __init__(self, driver=None):
        self.logger = get_logger(self.__class__.__name__)
        self.driver = driver
        self.platform = ConfigManager.get_current_platform()
        
        # 根據平台初始化對應的基類
        if self.platform == PlatformType.DESKTOP:
            from base.desktop_app import DesktopApp
            self._platform_impl = DesktopApp()
        elif self.platform == PlatformType.WEB:
            from base.base_page import BasePage
            # Web 需要 browser context
            if driver:
                self._platform_impl = BasePage(driver)
            else:
                self._platform_impl = None
        elif self.platform == PlatformType.ANDROID:
            from base.android_app import AndroidApp
            self._platform_impl = AndroidApp(driver)
        else:
            raise ValueError(f"不支援的平台: {self.platform}")
    
    # ==================== 通用方法 ====================
    
    def click(self, *args, **kwargs):
        """
        統一的點擊方法
        - Desktop: smart_click(x_ratio, y_ratio, ...)
        - Web: click(locator)
        - Android: click_by_text(text) 或 click_by_id(id)
        """
        if self.platform == PlatformType.DESKTOP:
            return self._platform_impl.smart_click(*args, **kwargs)
        elif self.platform == PlatformType.WEB:
            return self._platform_impl.click(*args, **kwargs)
        elif self.platform == PlatformType.ANDROID:
            # Android 需要判斷參數類型
            if 'text' in kwargs:
                return self._platform_impl.click_by_text(kwargs['text'])
            elif 'resource_id' in kwargs:
                return self._platform_impl.click_by_id(kwargs['resource_id'])
            else:
                raise ValueError("Android 點擊需要 text 或 resource_id 參數")
    
    def input_text(self, *args, **kwargs):
        """
        統一的輸入方法
        - Desktop: 不支援（使用 pyautogui.typewrite）
        - Web: type(locator, text)
        - Android: input_text(resource_id, text)
        """
        if self.platform == PlatformType.DESKTOP:
            import pyautogui
            text = kwargs.get('text', args[0] if args else '')
            pyautogui.typewrite(text)
            return True
        elif self.platform == PlatformType.WEB:
            return self._platform_impl.type(*args, **kwargs)
        elif self.platform == PlatformType.ANDROID:
            return self._platform_impl.input_text(*args, **kwargs)
    
    def wait_for_element(self, *args, **kwargs):
        """
        統一的等待方法
        - Desktop: wait_for_window(window_titles, timeout)
        - Web: is_visible(locator)
        - Android: wait_for_element(text/resource_id, timeout)
        """
        if self.platform == PlatformType.DESKTOP:
            return self._platform_impl.wait_for_window(*args, **kwargs)
        elif self.platform == PlatformType.WEB:
            return self._platform_impl.is_visible(*args, **kwargs)
        elif self.platform == PlatformType.ANDROID:
            return self._platform_impl.wait_for_element(*args, **kwargs)
    
    def get_platform_impl(self):
        """獲取平台特定的實現"""
        return self._platform_impl


class PlatformSpecificPage:
    """
    平台特定 Page 的裝飾器基類
    允許為不同平台提供不同的實現
    """
    
    def __init__(self, driver=None):
        self.logger = get_logger(self.__class__.__name__)
        self.driver = driver
        self.platform = ConfigManager.get_current_platform()
    
    def get_implementation(self, method_name: str):
        """
        獲取平台特定的方法實現
        優先尋找 {method_name}_{platform} 方法
        例如: login_desktop(), login_web(), login_android()
        """
        platform_method = f"{method_name}_{self.platform.value}"
        
        if hasattr(self, platform_method):
            return getattr(self, platform_method)
        elif hasattr(self, method_name):
            return getattr(self, method_name)
        else:
            raise NotImplementedError(
                f"方法 {method_name} 在平台 {self.platform.value} 上未實現"
            )
    
    def execute(self, method_name: str, *args, **kwargs):
        """執行平台特定的方法"""
        method = self.get_implementation(method_name)
        return method(*args, **kwargs)


# ==================== 使用範例 ====================

class ExampleLoginPage(PlatformSpecificPage):
    """
    範例：登入頁面 - 支援多平台
    """
    
    def login(self, username: str, password: str):
        """統一的登入接口"""
        return self.execute('login', username, password)
    
    # Desktop 版本
    def login_desktop(self, username: str, password: str):
        self.logger.info(f"🖥️ Desktop 登入: {username}")
        # Desktop 特定邏輯
        # 使用圖片辨識、OCR、座標點擊
        pass
    
    # Web 版本
    def login_web(self, username: str, password: str):
        self.logger.info(f"🌐 Web 登入: {username}")
        # Web 特定邏輯
        # 使用 Selenium 定位器
        pass
    
    # Android 版本
    def login_android(self, username: str, password: str):
        self.logger.info(f"📱 Android 登入: {username}")
        # Android 特定邏輯
        # 使用 Appium 定位器
        pass


if __name__ == "__main__":
    from config_enhanced import ConfigManager, PlatformType
    
    print("=== 統一 Page 基類測試 ===\n")
    
    # 測試 Desktop
    ConfigManager.set_platform(PlatformType.DESKTOP)
    page = ExampleLoginPage()
    print(f"當前平台: {page.platform.value}")
    
    # 測試方法路由
    method = page.get_implementation('login')
    print(f"登入方法: {method.__name__}")
    
    print("\n範例：不同平台有不同實現")
    print("  - login_desktop() → Desktop 專用")
    print("  - login_web() → Web 專用")
    print("  - login_android() → Android 專用")
    print("  - login() → 統一接口，自動路由")