# 相對路徑: pages/mobile/base_mobile_page.py
"""
移動端 Page Object 基類

提供統一的移動端操作接口，遵循 SOLID 原則：
- SRP: 單一職責 - 封裝移動端基本操作
- DIP: 依賴倒置 - 依賴 Appium WebDriver 抽象
- OCP: 開閉原則 - 可擴展但不可修改
"""

from typing import Optional, Tuple
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from toolkit.logger import get_logger
from config import EnvConfig


class BaseMobilePage:
    """
    移動端 Page Object 基類
    
    封裝 Appium WebDriver 的常用操作，提供統一的接口。
    所有移動端 Page Object 都應該繼承此類。
    
    Attributes:
        driver: Appium WebDriver 實例
        wait: WebDriverWait 實例（使用顯式等待）
        logger: Logger 實例
    """
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化移動端頁面基類
        
        Args:
            driver: Appium WebDriver 實例，如果為 None 則需要後續設置
        """
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)
        
        # 初始化 WebDriverWait（使用配置中的超時時間）
        if driver:
            timeout = getattr(EnvConfig, 'ANDROID_DEFAULT_TIMEOUT', 10)
            self.wait = WebDriverWait(driver, timeout)
        else:
            self.wait = None
    
    def set_driver(self, driver: object) -> 'BaseMobilePage':
        """
        設置 Appium WebDriver 實例
        
        Args:
            driver: Appium WebDriver 實例
            
        Returns:
            BaseMobilePage: 返回自身以支持鏈式調用
        """
        self.driver = driver
        timeout = getattr(EnvConfig, 'ANDROID_DEFAULT_TIMEOUT', 10)
        self.wait = WebDriverWait(driver, timeout)
        return self
    
    def find_element_by_id(self, resource_id: str, timeout: Optional[int] = None) -> Optional[object]:
        """
        根據 Resource ID 查找元素（使用顯式等待）
        
        Args:
            resource_id: Android Resource ID（例如：com.example:id/button）
            timeout: 超時時間（秒），如果為 None 則使用默認值
            
        Returns:
            WebElement: 找到的元素，如果超時則返回 None
        """
        if not self.driver or not self.wait:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return None
        
        try:
            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((AppiumBy.ID, resource_id))
            )
            self.logger.debug(f"[BASE_MOBILE] 找到元素 (ID): {resource_id}")
            return element
        except TimeoutException:
            self.logger.warning(f"[BASE_MOBILE] 超時：找不到元素 (ID): {resource_id}")
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (ID): {resource_id}, 錯誤: {e}")
            return None
    
    def find_element_by_text(self, text: str, timeout: Optional[int] = None) -> Optional[object]:
        """
        根據文字內容查找元素（使用顯式等待）
        
        Args:
            text: 元素顯示的文字
            timeout: 超時時間（秒），如果為 None 則使用默認值
            
        Returns:
            WebElement: 找到的元素，如果超時則返回 None
        """
        if not self.driver or not self.wait:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return None
        
        try:
            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            xpath = f'//*[@text="{text}"]'
            element = wait.until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            self.logger.debug(f"[BASE_MOBILE] 找到元素 (Text): {text}")
            return element
        except TimeoutException:
            self.logger.warning(f"[BASE_MOBILE] 超時：找不到元素 (Text): {text}")
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (Text): {text}, 錯誤: {e}")
            return None
    
    def find_element_by_xpath(self, xpath: str, timeout: Optional[int] = None) -> Optional[object]:
        """
        根據 XPath 查找元素（使用顯式等待）
        
        Args:
            xpath: XPath 表達式
            timeout: 超時時間（秒），如果為 None 則使用默認值
            
        Returns:
            WebElement: 找到的元素，如果超時則返回 None
        """
        if not self.driver or not self.wait:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return None
        
        try:
            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            self.logger.debug(f"[BASE_MOBILE] 找到元素 (XPath): {xpath}")
            return element
        except TimeoutException:
            self.logger.warning(f"[BASE_MOBILE] 超時：找不到元素 (XPath): {xpath}")
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (XPath): {xpath}, 錯誤: {e}")
            return None
    
    def click_element(self, element: object) -> bool:
        """
        點擊元素
        
        Args:
            element: WebElement 實例
            
        Returns:
            bool: 點擊是否成功
        """
        if not element:
            self.logger.error("[BASE_MOBILE] 元素為 None，無法點擊")
            return False
        
        try:
            # 確保元素可見且可點擊
            wait = WebDriverWait(self.driver, 5)
            wait.until(EC.element_to_be_clickable(element))
            element.click()
            self.logger.debug(f"[BASE_MOBILE] 成功點擊元素")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 點擊元素失敗: {e}")
            return False
    
    def click_by_id(self, resource_id: str, timeout: Optional[int] = None) -> bool:
        """
        根據 Resource ID 點擊元素
        
        Args:
            resource_id: Android Resource ID
            timeout: 超時時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            return self.click_element(element)
        return False
    
    def click_by_text(self, text: str, timeout: Optional[int] = None) -> bool:
        """
        根據文字內容點擊元素
        
        Args:
            text: 元素顯示的文字
            timeout: 超時時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        element = self.find_element_by_text(text, timeout)
        if element:
            return self.click_element(element)
        return False
    
    def input_text(self, element: object, text: str, clear: bool = True) -> bool:
        """
        在元素中輸入文字
        
        Args:
            element: WebElement 實例
            text: 要輸入的文字
            clear: 是否先清空現有內容
            
        Returns:
            bool: 輸入是否成功
        """
        if not element:
            self.logger.error("[BASE_MOBILE] 元素為 None，無法輸入文字")
            return False
        
        try:
            if clear:
                element.clear()
            element.send_keys(text)
            self.logger.debug(f"[BASE_MOBILE] 成功輸入文字: {text}")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 輸入文字失敗: {e}")
            return False
    
    def input_text_by_id(self, resource_id: str, text: str, clear: bool = True, timeout: Optional[int] = None) -> bool:
        """
        根據 Resource ID 輸入文字
        
        Args:
            resource_id: Android Resource ID
            text: 要輸入的文字
            clear: 是否先清空現有內容
            timeout: 超時時間（秒）
            
        Returns:
            bool: 輸入是否成功
        """
        element = self.find_element_by_id(resource_id, timeout)
        if element:
            return self.input_text(element, text, clear)
        return False
    
    def is_element_visible(self, element: object) -> bool:
        """
        檢查元素是否可見
        
        Args:
            element: WebElement 實例
            
        Returns:
            bool: 元素是否可見
        """
        if not element:
            return False
        
        try:
            return element.is_displayed()
        except Exception:
            return False
    
    def wait_for_element_visible(self, resource_id: Optional[str] = None, text: Optional[str] = None, 
                                  xpath: Optional[str] = None, timeout: Optional[int] = None) -> bool:
        """
        等待元素可見（使用顯式等待）
        
        Args:
            resource_id: Android Resource ID
            text: 元素顯示的文字
            xpath: XPath 表達式
            timeout: 超時時間（秒）
            
        Returns:
            bool: 元素是否在超時前變為可見
        """
        if not self.driver or not self.wait:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            
            if resource_id:
                wait.until(EC.visibility_of_element_located((AppiumBy.ID, resource_id)))
                return True
            elif text:
                xpath = f'//*[@text="{text}"]'
                wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, xpath)))
                return True
            elif xpath:
                wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, xpath)))
                return True
            else:
                self.logger.error("[BASE_MOBILE] 必須提供 resource_id、text 或 xpath 之一")
                return False
        except TimeoutException:
            return False
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 等待元素可見失敗: {e}")
            return False
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500) -> bool:
        """
        滑動操作
        
        Args:
            start_x: 起始 X 座標
            start_y: 起始 Y 座標
            end_x: 結束 X 座標
            end_y: 結束 Y 座標
            duration: 滑動持續時間（毫秒）
            
        Returns:
            bool: 滑動是否成功
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            self.logger.debug(f"[BASE_MOBILE] 滑動: ({start_x},{start_y}) -> ({end_x},{end_y})")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 滑動失敗: {e}")
            return False
    
    def swipe_up(self, duration: int = 500) -> bool:
        """
        向上滑動
        
        Args:
            duration: 滑動持續時間（毫秒）
            
        Returns:
            bool: 滑動是否成功
        """
        if not self.driver:
            return False
        
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] * 3 // 4
        end_y = size['height'] // 4
        return self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def swipe_down(self, duration: int = 500) -> bool:
        """
        向下滑動
        
        Args:
            duration: 滑動持續時間（毫秒）
            
        Returns:
            bool: 滑動是否成功
        """
        if not self.driver:
            return False
        
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] // 4
        end_y = size['height'] * 3 // 4
        return self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def get_element_text(self, element: object) -> Optional[str]:
        """
        獲取元素的文字內容
        
        Args:
            element: WebElement 實例
            
        Returns:
            str: 元素的文字內容，如果失敗則返回 None
        """
        if not element:
            return None
        
        try:
            return element.text
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 獲取元素文字失敗: {e}")
            return None
    
    def press_back(self) -> bool:
        """
        按返回鍵
        
        Returns:
            bool: 操作是否成功
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            self.driver.press_keycode(4)  # KEYCODE_BACK
            self.logger.debug("[BASE_MOBILE] 按下返回鍵")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 按返回鍵失敗: {e}")
            return False
    
    def take_screenshot(self, filename: str) -> bool:
        """
        截圖
        
        Args:
            filename: 截圖保存路徑
            
        Returns:
            bool: 截圖是否成功
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            self.driver.save_screenshot(filename)
            self.logger.debug(f"[BASE_MOBILE] 截圖已保存: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 截圖失敗: {e}")
            return False
