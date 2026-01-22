# 相對路徑: tests/test_case_4_1.py
"""
Test Case 4-1: 登錄到 Nx Cloud (移動端)

測試步驟：
1. 啟動 Appium WebDriver
2. 初始化登錄頁面
3. 輸入郵箱
4. 輸入密碼
5. 點擊登錄按鈕
6. 驗證登錄是否成功
"""

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from config import EnvConfig
from actions.nx_mobile_actions import NxMobileActions
from toolkit.logger import get_logger


logger = get_logger(__name__)


@pytest.fixture(scope="function")
def mobile_driver():
    """
    Appium WebDriver Fixture
    
    初始化 Appium WebDriver 並返回 driver 實例。
    測試結束後自動關閉 driver。
    
    Yields:
        webdriver.Remote: Appium WebDriver 實例
    """
    logger.info("[FIXTURE] 初始化 Appium WebDriver...")
    
    # 構建 Appium capabilities
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = EnvConfig.ANDROID_PLATFORM_VERSION
    options.device_name = EnvConfig.ANDROID_DEVICE_NAME
    options.automation_name = EnvConfig.ANDROID_AUTOMATION_NAME
    
    # App 配置
    if EnvConfig.ANDROID_APP_PATH:
        options.app = EnvConfig.ANDROID_APP_PATH
    else:
        options.app_package = EnvConfig.ANDROID_APP_PACKAGE
        options.app_activity = EnvConfig.ANDROID_APP_ACTIVITY
    
    # 如果指定了 UDID，則使用它
    if EnvConfig.ANDROID_UDID:
        options.udid = EnvConfig.ANDROID_UDID
    
    # 其他配置
    options.no_reset = False  # 每次測試前重置 App
    options.full_reset = False  # 不完整重置（保留數據）
    
    # 創建 WebDriver 實例
    driver = webdriver.Remote(
        command_executor=EnvConfig.APPIUM_SERVER_URL,
        options=options
    )
    
    # 設置隱式等待
    driver.implicitly_wait(EnvConfig.ANDROID_IMPLICIT_WAIT)
    
    logger.info("[FIXTURE] ✅ Appium WebDriver 初始化成功")
    
    yield driver
    
    # 清理：關閉 driver
    logger.info("[FIXTURE] 關閉 Appium WebDriver...")
    try:
        driver.quit()
        logger.info("[FIXTURE] ✅ Appium WebDriver 已關閉")
    except Exception as e:
        logger.error(f"[FIXTURE] ❌ 關閉 Appium WebDriver 失敗: {e}")


@pytest.fixture(scope="function")
def mobile_actions(mobile_driver):
    """
    NxMobileActions Fixture
    
    初始化 NxMobileActions 實例並返回。
    
    Args:
        mobile_driver: Appium WebDriver Fixture
        
    Yields:
        NxMobileActions: NxMobileActions 實例
    """
    logger.info("[FIXTURE] 初始化 NxMobileActions...")
    actions = NxMobileActions(mobile_driver)
    logger.info("[FIXTURE] ✅ NxMobileActions 初始化成功")
    yield actions


def test_case_4_1_login_to_nx_cloud(mobile_actions):
    """
    Test Case 4-1: 登錄到 Nx Cloud
    
    測試目標：
    驗證移動端 App 可以成功登錄到 Nx Cloud。
    
    Args:
        mobile_actions: NxMobileActions Fixture
    """
    logger.info("=" * 60)
    logger.info("開始執行 Test Case 4-1: 登錄到 Nx Cloud")
    logger.info("=" * 60)
    
    try:
        # 執行登錄流程
        mobile_actions.run_login_step()
        
        logger.info("=" * 60)
        logger.info("✅ Test Case 4-1 通過：登錄到 Nx Cloud 成功")
        logger.info("=" * 60)
        
    except AssertionError as e:
        logger.error(f"❌ Test Case 4-1 失敗: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Test Case 4-1 執行異常: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
