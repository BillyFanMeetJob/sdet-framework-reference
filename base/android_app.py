# 相對路徑: base/android_app.py
"""
Android App 基礎類別
提供類似 DesktopApp 的 Android 自動化基礎功能
"""

import time
from typing import Tuple, Optional
from toolkit.logger import get_logger


class AndroidApp:
    """Android App 基礎類別"""
    
    def __init__(self, driver=None):
        self.logger = get_logger(self.__class__.__name__)
        self.driver = driver
    
    def set_driver(self, driver):
        """設置 Appium driver"""
        self.driver = driver
        return self
    
    def find_element_by_text(self, text: str, timeout: int = 10):
        """根據文字尋找元素"""
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            xpath = f'//*[@text="{text}"]'
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            self.logger.info(f"✅ 找到文字元素: {text}")
            return element
        except Exception as e:
            self.logger.warning(f"⚠️ 找不到文字元素: {text}")
            return None
    
    def find_element_by_id(self, resource_id: str, timeout: int = 10):
        """根據 Resource ID 尋找元素"""
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((AppiumBy.ID, resource_id))
            )
            self.logger.info(f"✅ 找到 ID 元素: {resource_id}")
            return element
        except Exception as e:
            self.logger.warning(f"⚠️ 找不到 ID 元素: {resource_id}")
            return None
    
    def click_by_text(self, text: str, timeout: int = 10):
        """根據文字點擊元素"""
        element = self.find_element_by_text(text, timeout)
        if element:
            element.click()
            self.logger.info(f"🖱️ 點擊文字: {text}")
            return True
        return False
    
    def click_by_id(self, resource_id: str, timeout: int = 10):
        """根據 Resource ID 點擊元素"""
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            element.click()
            self.logger.info(f"🖱️ 點擊 ID: {resource_id}")
            return True
        return False
    
    def input_text(self, resource_id: str, text: str, timeout: int = 10):
        """在指定元素中輸入文字"""
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            element.clear()
            element.send_keys(text)
            self.logger.info(f"⌨️ 輸入文字: {text}")
            return True
        return False
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500):
        """滑動操作"""
        try:
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            self.logger.info(f"👆 滑動: ({start_x},{start_y}) -> ({end_x},{end_y})")
            return True
        except Exception as e:
            self.logger.error(f"❌ 滑動失敗: {e}")
            return False
    
    def swipe_up(self, duration: int = 500):
        """向上滑動"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] * 3 // 4
        end_y = size['height'] // 4
        return self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def swipe_down(self, duration: int = 500):
        """向下滑動"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] // 4
        end_y = size['height'] * 3 // 4
        return self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def wait_for_element(self, text: str = None, resource_id: str = None, timeout: int = 10):
        """等待元素出現"""
        if text:
            return self.find_element_by_text(text, timeout) is not None
        elif resource_id:
            return self.find_element_by_id(resource_id, timeout) is not None
        return False
    
    def is_element_visible(self, text: str = None, resource_id: str = None):
        """檢查元素是否可見"""
        try:
            if text:
                element = self.find_element_by_text(text, timeout=2)
            elif resource_id:
                element = self.find_element_by_id(resource_id, timeout=2)
            else:
                return False
            
            return element is not None and element.is_displayed()
        except:
            return False
    
    def take_screenshot(self, filename: str):
        """截圖"""
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"📸 截圖已保存: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 截圖失敗: {e}")
            return False
    
    def get_current_activity(self):
        """獲取當前 Activity"""
        try:
            activity = self.driver.current_activity
            self.logger.info(f"📱 當前 Activity: {activity}")
            return activity
        except Exception as e:
            self.logger.error(f"❌ 獲取 Activity 失敗: {e}")
            return None
    
    def press_back(self):
        """按返回鍵"""
        try:
            self.driver.press_keycode(4)  # KEYCODE_BACK
            self.logger.info("⬅️ 按下返回鍵")
            return True
        except Exception as e:
            self.logger.error(f"❌ 按返回鍵失敗: {e}")
            return False
    
    def press_home(self):
        """按 Home 鍵"""
        try:
            self.driver.press_keycode(3)  # KEYCODE_HOME
            self.logger.info("🏠 按下 Home 鍵")
            return True
        except Exception as e:
            self.logger.error(f"❌ 按 Home 鍵失敗: {e}")
            return False


# ==================== 使用範例 ====================

if __name__ == "__main__":
    print("AndroidApp 基礎類別已載入")
    print("使用範例:")
    print("""
    # 1. 初始化
    from base.platform_driver import DriverFactory
    from base.android_app import AndroidApp
    
    driver = DriverFactory.create_driver(PlatformType.ANDROID)
    app = AndroidApp(driver.get_driver())
    
    # 2. 基本操作
    app.click_by_text("登入")
    app.input_text("com.example:id/username", "admin")
    app.swipe_up()
    
    # 3. 等待和檢查
    if app.wait_for_element(text="登入成功"):
        print("登入成功")
    """)