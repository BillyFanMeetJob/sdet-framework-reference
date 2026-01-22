# 相對路徑: tests/test_case_4_2.py
"""
Test Case 4-2: 選擇服務器和攝像頭，使用日曆控件播放錄製的視頻 (移動端)

測試步驟：
1. 登錄到 Nx Cloud（依賴 Test Case 4-1）
2. 選擇服務器
3. 選擇攝像頭
4. 打開日曆控件
5. 選擇有錄影的日期
6. 播放錄製的視頻
7. 驗證視頻是否正在播放
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
    options.no_reset = True  # 不重置 App（保留登錄狀態）
    options.full_reset = False  # 不完整重置
    
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


def test_case_4_2_select_server_and_camera(mobile_actions):
    """
    Test Case 4-2 (部分): 選擇服務器和攝像頭
    
    測試目標：
    驗證移動端 App 可以成功選擇服務器和攝像頭。
    
    注意：
    此測試假設已經登錄（可以手動登錄或依賴 Test Case 4-1）。
    
    Args:
        mobile_actions: NxMobileActions Fixture
    """
    logger.info("=" * 60)
    logger.info("開始執行 Test Case 4-2 (部分): 選擇服務器和攝像頭")
    logger.info("=" * 60)
    
    try:
        # 執行選擇服務器和攝像頭流程
        mobile_actions.run_select_server_and_camera_step()
        
        logger.info("=" * 60)
        logger.info("✅ Test Case 4-2 (部分) 通過：選擇服務器和攝像頭成功")
        logger.info("=" * 60)
        
    except AssertionError as e:
        logger.error(f"❌ Test Case 4-2 (部分) 失敗: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Test Case 4-2 (部分) 執行異常: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_case_4_2_playback_with_calendar(mobile_actions):
    """
    Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻
    
    測試目標：
    驗證移動端 App 可以使用日曆控件選擇日期並播放錄製的視頻。
    
    注意：
    此測試假設已經登錄並選擇了服務器和攝像頭。
    
    Args:
        mobile_actions: NxMobileActions Fixture
    """
    logger.info("=" * 60)
    logger.info("開始執行 Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻")
    logger.info("=" * 60)
    
    try:
        # 執行播放錄製的視頻流程
        mobile_actions.run_playback_with_calendar_step(days_ago=1)
        
        logger.info("=" * 60)
        logger.info("✅ Test Case 4-2 (部分) 通過：使用日曆控件播放錄製的視頻成功")
        logger.info("=" * 60)
        
    except AssertionError as e:
        logger.error(f"❌ Test Case 4-2 (部分) 失敗: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Test Case 4-2 (部分) 執行異常: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_case_4_2_full_flow(mobile_actions):
    """
    Test Case 4-2 (完整流程): 選擇服務器和攝像頭，使用日曆控件播放錄製的視頻
    
    測試目標：
    驗證移動端 App 的完整播放流程。
    
    步驟：
    1. 選擇服務器和攝像頭
    2. 使用日曆控件播放錄製的視頻
    
    注意：
    此測試假設已經登錄（可以手動登錄或依賴 Test Case 4-1）。
    
    Args:
        mobile_actions: NxMobileActions Fixture
    """
    logger.info("=" * 60)
    logger.info("開始執行 Test Case 4-2 (完整流程)")
    logger.info("=" * 60)
    
    try:
        # 步驟 1: 選擇服務器和攝像頭
        mobile_actions.run_select_server_and_camera_step()
        
        # 步驟 2: 使用日曆控件播放錄製的視頻
        mobile_actions.run_playback_with_calendar_step(days_ago=1)
        
        logger.info("=" * 60)
        logger.info("✅ Test Case 4-2 (完整流程) 通過")
        logger.info("=" * 60)
        
    except AssertionError as e:
        logger.error(f"❌ Test Case 4-2 (完整流程) 失敗: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Test Case 4-2 (完整流程) 執行異常: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
