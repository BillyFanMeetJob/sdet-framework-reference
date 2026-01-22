# 相對路徑: toolkit/mobile_toolkit.py
"""
移動端自動化工具類

提供 Appium WebDriver 的初始化和管理功能。
"""

from typing import Optional, Tuple
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from config import EnvConfig
from toolkit.logger import get_logger


logger = get_logger(__name__)


def create_appium_driver(timeout: Optional[int] = None) -> Tuple[webdriver.Remote, WebDriverWait]:
    """
    創建 Appium WebDriver 實例
    
    根據 config.py 中的配置創建並返回 Appium WebDriver 和 WebDriverWait 實例。
    
    Args:
        timeout: 顯式等待超時時間（秒），如果為 None 則使用配置中的默認值
        
    Returns:
        Tuple[webdriver.Remote, WebDriverWait]: Appium WebDriver 和 WebDriverWait 實例
        
    Raises:
        Exception: 如果創建 WebDriver 失敗
    """
    logger.info("[MOBILE_TOOLKIT] 初始化 Appium WebDriver...")
    
    # 構建 Appium capabilities
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = EnvConfig.ANDROID_PLATFORM_VERSION
    options.device_name = EnvConfig.ANDROID_DEVICE_NAME
    options.automation_name = EnvConfig.ANDROID_AUTOMATION_NAME
    
    # App 配置
    if EnvConfig.ANDROID_APP_PATH:
        # 如果提供了 APK 路徑，使用它
        options.app = EnvConfig.ANDROID_APP_PATH
        logger.info(f"[MOBILE_TOOLKIT] 使用 APK 路徑: {EnvConfig.ANDROID_APP_PATH}")
    else:
        # 否則使用已安裝的 App
        options.app_package = EnvConfig.ANDROID_APP_PACKAGE
        options.app_activity = EnvConfig.ANDROID_APP_ACTIVITY
        logger.info(f"[MOBILE_TOOLKIT] 使用已安裝的 App: {EnvConfig.ANDROID_APP_PACKAGE}/{EnvConfig.ANDROID_APP_ACTIVITY}")
    
    # 如果指定了 UDID，則使用它
    if EnvConfig.ANDROID_UDID:
        options.udid = EnvConfig.ANDROID_UDID
        logger.info(f"[MOBILE_TOOLKIT] 使用設備 UDID: {EnvConfig.ANDROID_UDID}")
    
    # 其他配置
    options.no_reset = False  # 每次測試前重置 App
    options.full_reset = False  # 不完整重置（保留數據）
    
    try:
        # 創建 WebDriver 實例
        driver = webdriver.Remote(
            command_executor=EnvConfig.APPIUM_SERVER_URL,
            options=options
        )
        
        # 設置隱式等待
        driver.implicitly_wait(EnvConfig.ANDROID_IMPLICIT_WAIT)
        
        # 創建 WebDriverWait 實例
        if timeout is None:
            timeout = getattr(EnvConfig, 'ANDROID_DEFAULT_TIMEOUT', 10)
        wait = WebDriverWait(driver, timeout)
        
        logger.info("[MOBILE_TOOLKIT] ✅ Appium WebDriver 初始化成功")
        return driver, wait
        
    except Exception as e:
        logger.error(f"[MOBILE_TOOLKIT] ❌ 初始化 Appium WebDriver 失敗: {e}")
        logger.warning("[MOBILE_TOOLKIT] 💡 請確認:")
        logger.warning("  1. Appium Server 已啟動 (通常運行在 http://localhost:4723)")
        logger.warning("  2. Android 設備/模擬器已連接 (使用 'adb devices' 檢查)")
        logger.warning("  3. APP_PACKAGE 和 APP_ACTIVITY 配置正確")
        logger.warning("  4. 設備已解鎖且允許 USB 調試")
        raise
