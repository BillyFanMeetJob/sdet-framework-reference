# 相對路徑: config_enhanced.py
"""
多環境、多平台配置系統
支援: Desktop App / Web / Android App
環境: DEV / SIT / UAT / PROD
"""

import os
from enum import Enum

class PlatformType(Enum):
    """平台類型枚舉"""
    DESKTOP = "desktop"
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"  # 預留

class EnvironmentType(Enum):
    """環境類型枚舉"""
    DEV = "dev"
    SIT = "sit"
    UAT = "uat"
    PROD = "prod"


class BaseConfig:
    """基礎配置 - 所有環境共用"""
    
    # 項目路徑
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    TEST_PLAN_PATH = os.path.join(PROJECT_ROOT, "DemoData", "TestPlan.xlsx")
    RES_PATH = os.path.join(PROJECT_ROOT, "res")
    LOG_PATH = os.path.join(PROJECT_ROOT, "logs")
    OCR_FONT_PATH = os.path.join(PROJECT_ROOT, "assets", "simhei.ttf")
    
    # 通用設定
    BASE_WINDOW_SIZE = (1920, 1200)
    DEFAULT_TIMEOUT = 30
    IMPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 30
    
    # 截圖設定
    SCREENSHOT_ON_FAILURE = True
    SCREENSHOT_PATH = os.path.join(PROJECT_ROOT, "screenshots")
    
    # 日誌設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class DesktopConfig:
    """Desktop App 專用配置"""
    
    # Desktop 應用程式路徑（各環境可覆寫）
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "LAPTOP-QRJN5735"
    
    # Desktop 特定設定
    AUTO_LAUNCH = True
    CLOSE_ON_FINISH = False
    WINDOW_MAX = True


class WebConfig:
    """Web 專用配置"""
    
    # 瀏覽器設定
    BROWSER_TYPE = "chrome"  # chrome, firefox, edge
    HEADLESS = False
    BROWSER_WIDTH = 1920
    BROWSER_HEIGHT = 1080
    
    # Web 特定設定
    ACCEPT_INSECURE_CERTS = True
    DISABLE_GPU = False
    NO_SANDBOX = False
    
    # Chrome 選項
    CHROME_OPTIONS = [
        "--start-maximized",
        "--disable-extensions",
        "--disable-popup-blocking",
    ]


class AndroidConfig:
    """Android App 專用配置"""
    
    # Appium 設定
    APPIUM_SERVER = "http://127.0.0.1:4723/wd/hub"
    PLATFORM_NAME = "Android"
    PLATFORM_VERSION = "11.0"
    DEVICE_NAME = "Android Emulator"
    
    # App 設定
    APP_PACKAGE = "com.networkoptix.mobile"
    APP_ACTIVITY = ".MainActivity"
    APK_PATH = os.path.join(BaseConfig.PROJECT_ROOT, "apk", "nx_witness.apk")
    
    # Android 特定設定
    AUTO_GRANT_PERMISSIONS = True
    NO_RESET = False
    FULL_RESET = False
    AUTOMATION_NAME = "UiAutomator2"


# ==================== 環境配置 ====================

class DevConfig(BaseConfig, DesktopConfig, WebConfig, AndroidConfig):
    """開發環境配置"""
    
    ENV = EnvironmentType.DEV
    
    # Desktop
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "LAPTOP-QRJN5735"
    
    # Web
    BASE_URL = "http://localhost:7001"
    API_BASE_URL = "http://localhost:7001/api"
    
    # Android
    APPIUM_SERVER = "http://127.0.0.1:4723/wd/hub"
    
    # 測試帳號
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin"
    
    # 日誌級別
    LOG_LEVEL = "DEBUG"


class SitConfig(BaseConfig, DesktopConfig, WebConfig, AndroidConfig):
    """系統整合測試環境配置"""
    
    ENV = EnvironmentType.SIT
    
    # Desktop
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "SIT-Server-01"
    
    # Web
    BASE_URL = "http://sit-nx-witness.example.com"
    API_BASE_URL = "http://sit-nx-witness.example.com/api"
    
    # Android
    APPIUM_SERVER = "http://sit-appium.example.com:4723/wd/hub"
    
    # 測試帳號
    TEST_USERNAME = "test_user"
    TEST_PASSWORD = "test_pass"
    
    # 日誌級別
    LOG_LEVEL = "INFO"


class UatConfig(BaseConfig, DesktopConfig, WebConfig, AndroidConfig):
    """用戶驗收測試環境配置"""
    
    ENV = EnvironmentType.UAT
    
    # Desktop
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "UAT-Server-01"
    
    # Web
    BASE_URL = "http://uat-nx-witness.example.com"
    API_BASE_URL = "http://uat-nx-witness.example.com/api"
    
    # Android
    APPIUM_SERVER = "http://uat-appium.example.com:4723/wd/hub"
    
    # 測試帳號
    TEST_USERNAME = "uat_user"
    TEST_PASSWORD = "uat_pass"
    
    # 日誌級別
    LOG_LEVEL = "INFO"


class ProdConfig(BaseConfig, DesktopConfig, WebConfig, AndroidConfig):
    """生產環境配置（謹慎使用）"""
    
    ENV = EnvironmentType.PROD
    
    # Desktop
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "PROD-Server-01"
    
    # Web
    BASE_URL = "https://nx-witness.example.com"
    API_BASE_URL = "https://nx-witness.example.com/api"
    
    # Android
    APPIUM_SERVER = "http://prod-appium.example.com:4723/wd/hub"
    
    # 測試帳號
    TEST_USERNAME = "prod_readonly_user"
    TEST_PASSWORD = "prod_readonly_pass"
    
    # 日誌級別
    LOG_LEVEL = "WARNING"
    
    # 生產環境特殊設定
    SCREENSHOT_ON_FAILURE = True
    HEADLESS = True  # 生產環境建議使用 headless


# ==================== 配置管理器 ====================

class ConfigManager:
    """配置管理器 - 統一管理配置"""
    
    _configs = {
        EnvironmentType.DEV: DevConfig,
        EnvironmentType.SIT: SitConfig,
        EnvironmentType.UAT: UatConfig,
        EnvironmentType.PROD: ProdConfig,
    }
    
    _current_env = EnvironmentType.DEV
    _current_platform = PlatformType.DESKTOP
    
    @classmethod
    def get_config(cls):
        """獲取當前環境的配置"""
        return cls._configs[cls._current_env]
    
    @classmethod
    def set_environment(cls, env: EnvironmentType):
        """設置當前環境"""
        if env not in cls._configs:
            raise ValueError(f"不支援的環境: {env}")
        cls._current_env = env
        print(f"✅ 切換到環境: {env.value.upper()}")
    
    @classmethod
    def set_platform(cls, platform: PlatformType):
        """設置當前平台"""
        cls._current_platform = platform
        print(f"✅ 切換到平台: {platform.value.upper()}")
    
    @classmethod
    def get_current_env(cls):
        """獲取當前環境"""
        return cls._current_env
    
    @classmethod
    def get_current_platform(cls):
        """獲取當前平台"""
        return cls._current_platform
    
    @classmethod
    def load_from_env_var(cls):
        """從環境變數載入配置"""
        import os
        
        # 讀取環境變數
        env_name = os.getenv("TEST_ENV", "DEV").upper()
        platform_name = os.getenv("TEST_PLATFORM", "DESKTOP").upper()
        
        # 設定環境
        try:
            env = EnvironmentType[env_name]
            cls.set_environment(env)
        except KeyError:
            print(f"⚠️ 未知環境 {env_name}，使用預設環境 DEV")
        
        # 設定平台
        try:
            platform = PlatformType[platform_name]
            cls.set_platform(platform)
        except KeyError:
            print(f"⚠️ 未知平台 {platform_name}，使用預設平台 DESKTOP")
    
    @classmethod
    def get_platform_config(cls, platform: PlatformType = None):
        """獲取特定平台的配置"""
        if platform is None:
            platform = cls._current_platform
        
        config = cls.get_config()
        
        if platform == PlatformType.DESKTOP:
            return {
                "exe_path": config.NX_EXE_PATH,
                "server_name": config.DEFAULT_SERVER_NAME,
                "auto_launch": config.AUTO_LAUNCH,
                "close_on_finish": config.CLOSE_ON_FINISH,
            }
        elif platform == PlatformType.WEB:
            return {
                "base_url": config.BASE_URL,
                "api_url": config.API_BASE_URL,
                "browser": config.BROWSER_TYPE,
                "headless": config.HEADLESS,
                "width": config.BROWSER_WIDTH,
                "height": config.BROWSER_HEIGHT,
            }
        elif platform == PlatformType.ANDROID:
            return {
                "appium_server": config.APPIUM_SERVER,
                "app_package": config.APP_PACKAGE,
                "app_activity": config.APP_ACTIVITY,
                "device_name": config.DEVICE_NAME,
                "platform_version": config.PLATFORM_VERSION,
            }
        else:
            raise ValueError(f"不支援的平台: {platform}")


# ==================== 快速訪問 ====================

def get_current_config():
    """獲取當前配置（向後相容）"""
    return ConfigManager.get_config()


# 初始化：從環境變數載入配置
ConfigManager.load_from_env_var()

# 全局配置實例（向後相容）
EnvConfig = ConfigManager.get_config()


# ==================== 使用範例 ====================

if __name__ == "__main__":
    # 範例 1: 使用預設配置（DEV）
    print(f"當前環境: {ConfigManager.get_current_env().value}")
    print(f"當前平台: {ConfigManager.get_current_platform().value}")
    print(f"BASE_URL: {EnvConfig.BASE_URL}")
    
    # 範例 2: 切換環境
    ConfigManager.set_environment(EnvironmentType.SIT)
    config = ConfigManager.get_config()
    print(f"SIT 環境 URL: {config.BASE_URL}")
    
    # 範例 3: 切換平台
    ConfigManager.set_platform(PlatformType.WEB)
    web_config = ConfigManager.get_platform_config()
    print(f"Web 配置: {web_config}")
    
    # 範例 4: 獲取 Android 配置
    android_config = ConfigManager.get_platform_config(PlatformType.ANDROID)
    print(f"Android 配置: {android_config}")
