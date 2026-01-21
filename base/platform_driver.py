# 相對路徑: base/platform_driver.py
"""
平台驅動工廠
統一管理 Desktop / Web / Android 的驅動創建和管理
"""

from abc import ABC, abstractmethod
from typing import Optional
from toolkit.logger import get_logger


class BasePlatformDriver(ABC):
    """平台驅動基類"""
    
    def __init__(self, config):
        self.logger = get_logger(self.__class__.__name__)
        self.config = config
        self.driver = None
    
    @abstractmethod
    def start(self):
        """啟動驅動"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止驅動"""
        pass
    
    @abstractmethod
    def get_driver(self):
        """獲取驅動實例"""
        pass


class DesktopDriver(BasePlatformDriver):
    """Desktop App 驅動（無需 Selenium/Appium）"""
    
    def start(self):
        """啟動 Desktop App"""
        self.logger.info("🖥️ Desktop App 驅動已初始化")
        # Desktop 使用 pyautogui + pygetwindow，無需額外驅動
        self.driver = "desktop_app"  # 標記
        return self
    
    def stop(self):
        """停止 Desktop App"""
        self.logger.info("🛑 Desktop App 驅動已停止")
        # 如需關閉應用程式，在此實現
        pass
    
    def get_driver(self):
        """返回標記（Desktop 不使用 WebDriver）"""
        return self.driver


class WebDriver(BasePlatformDriver):
    """Web 驅動（使用 Selenium）"""
    
    def start(self):
        """啟動 Web 瀏覽器"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            
            self.logger.info("🌐 啟動 Web 瀏覽器...")
            
            # Chrome 選項
            options = Options()
            
            if self.config.HEADLESS:
                options.add_argument("--headless")
            
            for opt in self.config.CHROME_OPTIONS:
                options.add_argument(opt)
            
            # 創建驅動
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_window_size(
                self.config.BROWSER_WIDTH,
                self.config.BROWSER_HEIGHT
            )
            
            self.logger.info("✅ Web 瀏覽器已啟動")
            return self
            
        except Exception as e:
            self.logger.error(f"❌ 啟動 Web 瀏覽器失敗: {e}")
            raise
    
    def stop(self):
        """關閉 Web 瀏覽器"""
        if self.driver:
            self.logger.info("🛑 關閉 Web 瀏覽器...")
            self.driver.quit()
            self.driver = None
    
    def get_driver(self):
        """返回 Selenium WebDriver"""
        return self.driver


class AndroidDriver(BasePlatformDriver):
    """Android App 驅動（使用 Appium）"""
    
    def start(self):
        """啟動 Android App"""
        try:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options
            
            self.logger.info("📱 啟動 Android App...")
            
            # Appium 配置
            options = UiAutomator2Options()
            options.platform_name = self.config.PLATFORM_NAME
            options.platform_version = self.config.PLATFORM_VERSION
            options.device_name = self.config.DEVICE_NAME
            options.app_package = self.config.APP_PACKAGE
            options.app_activity = self.config.APP_ACTIVITY
            
            if self.config.AUTO_GRANT_PERMISSIONS:
                options.auto_grant_permissions = True
            
            if self.config.NO_RESET:
                options.no_reset = True
            
            self.driver = webdriver.Remote(
                self.config.APPIUM_SERVER,
                options=options
            )
            
            self.logger.info("✅ Android App 已啟動")
            return self
            
        except Exception as e:
            self.logger.error(f"❌ 啟動 Android App 失敗: {e}")
            self.logger.warning("💡 請確認:")
            self.logger.warning("  1. Appium Server 已啟動")
            self.logger.warning("  2. Android 設備/模擬器已連接")
            self.logger.warning("  3. APP_PACKAGE 和 APP_ACTIVITY 正確")
            raise
    
    def stop(self):
        """關閉 Android App"""
        if self.driver:
            self.logger.info("🛑 關閉 Android App...")
            self.driver.quit()
            self.driver = None
    
    def get_driver(self):
        """返回 Appium WebDriver"""
        return self.driver


class DriverFactory:
    """驅動工廠 - 根據平台類型創建對應的驅動"""
    
    _instance: Optional[BasePlatformDriver] = None
    
    @classmethod
    def create_driver(cls, platform_type=None, config=None):
        """
        創建平台驅動
        :param platform_type: 平台類型（PlatformType 枚舉）
        :param config: 配置物件
        :return: 平台驅動實例
        """
        # 如果沒有指定，從 ConfigManager 獲取
        if platform_type is None:
            from config_enhanced import ConfigManager, PlatformType
            platform_type = ConfigManager.get_current_platform()
        
        if config is None:
            from config_enhanced import ConfigManager
            config = ConfigManager.get_config()
        
        # 創建對應的驅動
        from config_enhanced import PlatformType
        
        if platform_type == PlatformType.DESKTOP:
            cls._instance = DesktopDriver(config)
        elif platform_type == PlatformType.WEB:
            cls._instance = WebDriver(config)
        elif platform_type == PlatformType.ANDROID:
            cls._instance = AndroidDriver(config)
        else:
            raise ValueError(f"不支援的平台類型: {platform_type}")
        
        # 啟動驅動
        cls._instance.start()
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """獲取當前驅動實例"""
        return cls._instance
    
    @classmethod
    def destroy_driver(cls):
        """銷毀驅動實例"""
        if cls._instance:
            cls._instance.stop()
            cls._instance = None


# ==================== 使用範例 ====================

if __name__ == "__main__":
    from config_enhanced import ConfigManager, PlatformType, EnvironmentType
    
    print("=== 平台驅動工廠測試 ===\n")
    
    # 範例 1: Desktop App
    print("1. 測試 Desktop 驅動")
    ConfigManager.set_platform(PlatformType.DESKTOP)
    desktop_driver = DriverFactory.create_driver()
    print(f"   Driver: {desktop_driver.get_driver()}\n")
    DriverFactory.destroy_driver()
    
    # 範例 2: Web（需要安裝 Selenium）
    print("2. 測試 Web 驅動")
    ConfigManager.set_platform(PlatformType.WEB)
    try:
        web_driver = DriverFactory.create_driver()
        print(f"   Driver: {web_driver.get_driver()}")
        print(f"   Web 驅動創建成功\n")
        DriverFactory.destroy_driver()
    except Exception as e:
        print(f"   Web 驅動創建失敗: {e}\n")
    
    # 範例 3: Android（需要 Appium Server）
    print("3. 測試 Android 驅動")
    ConfigManager.set_platform(PlatformType.ANDROID)
    try:
        android_driver = DriverFactory.create_driver()
        print(f"   Driver: {android_driver.get_driver()}")
        print(f"   Android 驅動創建成功\n")
        DriverFactory.destroy_driver()
    except Exception as e:
        print(f"   Android 驅動創建失敗: {e}\n")
