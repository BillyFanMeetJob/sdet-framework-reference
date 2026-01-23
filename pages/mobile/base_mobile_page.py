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
import os
import time
import tempfile
import numpy as np

# 嘗試導入 cv2 用於圖像辨識
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


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
            # 診斷：輸出當前頁面信息
            self._log_page_diagnostics("找不到元素 (ID)", resource_id)
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (ID): {resource_id}, 錯誤: {e}")
            self._log_page_diagnostics("查找元素失敗 (ID)", resource_id)
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
            # 診斷：輸出當前頁面信息
            self._log_page_diagnostics("找不到元素 (Text)", text)
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (Text): {text}, 錯誤: {e}")
            self._log_page_diagnostics("查找元素失敗 (Text)", text)
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
            # 診斷：輸出當前頁面信息
            self._log_page_diagnostics("找不到元素 (XPath)", xpath)
            return None
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找元素失敗 (XPath): {xpath}, 錯誤: {e}")
            self._log_page_diagnostics("查找元素失敗 (XPath)", xpath)
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
    
    def find_image_on_screen(
        self,
        image_path: str,
        timeout: float = 3.0,
        confidence: float = 0.7,
        check_interval: float = 0.2
    ) -> Optional[Tuple[int, int]]:
        """
        在螢幕截圖中查找圖像（使用 OpenCV template matching）
        
        Args:
            image_path: 要查找的圖像路徑（相對於 res 目錄或絕對路徑）
            timeout: 超時時間（秒），默認 3 秒
            confidence: 匹配置信度（0.0-1.0），默認 0.7
            check_interval: 檢查間隔（秒），默認 0.2 秒
            
        Returns:
            Optional[Tuple[int, int]]: 找到圖像的中心座標 (x, y)，如果未找到則返回 None
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return None
        
        if not CV2_AVAILABLE:
            self.logger.warning("[BASE_MOBILE] OpenCV 未安裝，無法進行圖像辨識")
            return None
        
        # 解析圖像路徑
        if not os.path.isabs(image_path):
            # 相對路徑，從 res 目錄查找
            full_image_path = os.path.join(EnvConfig.RES_PATH, image_path)
        else:
            full_image_path = image_path
        
        if not os.path.exists(full_image_path):
            self.logger.error(f"[BASE_MOBILE] 圖像文件不存在: {full_image_path}")
            return None
        
        self.logger.info(f"[BASE_MOBILE] 開始偵測圖像: {os.path.basename(full_image_path)}（超時: {timeout} 秒）...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            try:
                # 截圖
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    screenshot_path = tmp_file.name
                
                if not self.take_screenshot(screenshot_path):
                    time.sleep(check_interval)
                    continue
                
                # 讀取截圖和模板
                screenshot = cv2.imread(screenshot_path)
                template = cv2.imread(full_image_path, cv2.IMREAD_GRAYSCALE)
                
                if screenshot is None or template is None:
                    os.unlink(screenshot_path)
                    time.sleep(check_interval)
                    continue
                
                # 轉換為灰度圖
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                
                # Template matching
                result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # 清理臨時文件
                os.unlink(screenshot_path)
                
                if max_val >= confidence:
                    # 計算中心座標
                    template_h, template_w = template.shape[:2]
                    center_x = max_loc[0] + template_w // 2
                    center_y = max_loc[1] + template_h // 2
                    
                    self.logger.info(
                        f"[BASE_MOBILE] ✅ 找到圖像: {os.path.basename(full_image_path)} "
                        f"座標: ({center_x}, {center_y}), 置信度: {max_val:.3f}, "
                        f"耗時: {time.time() - start_time:.2f} 秒"
                    )
                    return (center_x, center_y)
                
                # 未找到，繼續等待
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.debug(f"[BASE_MOBILE] 圖像辨識異常（嘗試 {attempt}）: {e}")
                if 'screenshot_path' in locals():
                    try:
                        os.unlink(screenshot_path)
                    except:
                        pass
                time.sleep(check_interval)
        
        self.logger.info(
            f"[BASE_MOBILE] ⏱️ 圖像偵測超時: {os.path.basename(full_image_path)} "
            f"（已嘗試 {attempt} 次，耗時 {time.time() - start_time:.2f} 秒）"
        )
        return None
    
    def compare_screenshots(
        self,
        screenshot1_path: str,
        screenshot2_path: str,
        threshold: float = 0.01
    ) -> Tuple[bool, float]:
        """
        比較兩張截圖的差異度
        
        Args:
            screenshot1_path: 第一張截圖路徑
            screenshot2_path: 第二張截圖路徑
            threshold: 差異閾值（0.0-1.0），默認 0.01 (1%)
            
        Returns:
            Tuple[bool, float]: (是否超過閾值, 實際差異度)
        """
        if not CV2_AVAILABLE:
            self.logger.warning("[BASE_MOBILE] OpenCV 未安裝，無法進行截圖比對")
            return False, 0.0
        
        try:
            # 讀取兩張截圖
            img1 = cv2.imread(screenshot1_path)
            img2 = cv2.imread(screenshot2_path)
            
            if img1 is None or img2 is None:
                self.logger.error(f"[BASE_MOBILE] 無法讀取截圖: {screenshot1_path} 或 {screenshot2_path}")
                return False, 0.0
            
            # 確保兩張圖片尺寸相同
            if img1.shape != img2.shape:
                self.logger.warning(f"[BASE_MOBILE] 截圖尺寸不一致，調整為相同尺寸...")
                h, w = min(img1.shape[0], img2.shape[0]), min(img1.shape[1], img2.shape[1])
                img1 = cv2.resize(img1, (w, h))
                img2 = cv2.resize(img2, (w, h))
            
            # 計算差異
            diff = cv2.absdiff(img1, img2)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # 計算差異像素比例
            total_pixels = diff_gray.shape[0] * diff_gray.shape[1]
            different_pixels = np.count_nonzero(diff_gray)
            difference_ratio = different_pixels / total_pixels
            
            # 判斷是否超過閾值
            exceeds_threshold = difference_ratio > threshold
            
            self.logger.info(
                f"[BASE_MOBILE] 截圖比對結果: 差異度={difference_ratio*100:.2f}%, "
                f"閾值={threshold*100:.2f}%, 超過閾值={exceeds_threshold}"
            )
            
            return exceeds_threshold, difference_ratio
            
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 截圖比對失敗: {e}")
            return False, 0.0
    
    def _log_page_diagnostics(self, context: str, search_value: str):
        """
        輸出頁面診斷信息（當找不到元素時）
        
        Args:
            context: 上下文信息（例如 "找不到元素 (ID)"）
            search_value: 搜索的值（例如 Resource ID 或文字）
        """
        if not self.driver:
            return
        
        try:
            self.logger.warning(f"[BASE_MOBILE] [診斷] {context}: {search_value}")
            
            # 1. 獲取當前 Activity
            try:
                current_activity = self.driver.current_activity
                self.logger.info(f"[BASE_MOBILE] [診斷] 當前 Activity: {current_activity}")
            except Exception as e:
                self.logger.debug(f"[BASE_MOBILE] [診斷] 無法獲取 Activity: {e}")
            
            # 2. 獲取頁面源碼並分析
            try:
                page_source = self.driver.page_source
                if page_source:
                    import re
                    
                    # 檢查頁面類型
                    is_webview = 'WebView' in page_source or 'webview' in page_source.lower()
                    is_surfaceview = 'SurfaceView' in page_source or 'surfaceview' in page_source.lower()
                    
                    if is_webview:
                        self.logger.warning("[BASE_MOBILE] [診斷] ⚠️ 檢測到 WebView，可能需要切換 Context")
                        try:
                            contexts = self.driver.contexts
                            current_context = self.driver.current_context
                            self.logger.info(f"[BASE_MOBILE] [診斷] 可用 Contexts: {contexts}")
                            self.logger.info(f"[BASE_MOBILE] [診斷] 當前 Context: {current_context}")
                        except:
                            pass
                    
                    if is_surfaceview:
                        self.logger.warning("[BASE_MOBILE] [診斷] ⚠️ 檢測到 SurfaceView，可能需要使用座標點擊")
                    
                    # 提取關鍵信息：所有可見的文字和 Resource ID
                    # 提取所有 text 屬性
                    text_matches = re.findall(r'text="([^"]*)"', page_source)
                    # 提取所有 resource-id
                    id_matches = re.findall(r'resource-id="([^"]*)"', page_source)
                    # 提取所有 class 屬性
                    class_matches = re.findall(r'class="([^"]*)"', page_source[:5000])
                    
                    # 統計頁面元素
                    total_elements = len(re.findall(r'<[^>]+>', page_source))
                    self.logger.info(f"[BASE_MOBILE] [診斷] 頁面總元素數: {total_elements}")
                    
                    if text_matches:
                        unique_texts = list(set([t for t in text_matches if t.strip()]))[:30]  # 最多顯示 30 個
                        self.logger.info(f"[BASE_MOBILE] [診斷] 頁面可見文字 (前30個): {unique_texts}")
                    else:
                        self.logger.warning("[BASE_MOBILE] [診斷] ⚠️ 頁面沒有可見文字，可能是 SurfaceView 或 WebView")
                    
                    if id_matches:
                        unique_ids = list(set([id for id in id_matches if id.strip()]))[:30]  # 最多顯示 30 個
                        self.logger.info(f"[BASE_MOBILE] [診斷] 頁面 Resource ID (前30個): {unique_ids}")
                    else:
                        self.logger.warning("[BASE_MOBILE] [診斷] ⚠️ 頁面沒有 Resource ID，可能是 SurfaceView 或 WebView")
                    
                    # 顯示常見的 class 類型
                    if class_matches:
                        unique_classes = list(set([c for c in class_matches if c.strip()]))[:20]
                        self.logger.info(f"[BASE_MOBILE] [診斷] 頁面 Class 類型 (前20個): {unique_classes}")
                    
                    # 保存完整的頁面源碼到文件（用於深度分析）
                    try:
                        import os
                        import datetime
                        diagnostics_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                        os.makedirs(diagnostics_dir, exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        page_source_path = os.path.join(diagnostics_dir, f"page_source_{timestamp}.xml")
                        with open(page_source_path, "w", encoding="utf-8", errors='ignore') as f:
                            f.write(page_source)
                        self.logger.info(f"[BASE_MOBILE] [診斷] 完整頁面源碼已保存: {page_source_path}")
                    except Exception as e:
                        self.logger.debug(f"[BASE_MOBILE] [診斷] 無法保存頁面源碼: {e}")
                else:
                    self.logger.warning("[BASE_MOBILE] [診斷] ⚠️ 無法獲取頁面源碼（為空）")
            except Exception as e:
                self.logger.debug(f"[BASE_MOBILE] [診斷] 無法獲取頁面源碼: {e}")
            
            # 3. 截圖
            try:
                import os
                import datetime
                screenshot_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                os.makedirs(screenshot_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(screenshot_dir, f"diagnostic_{timestamp}.png")
                if self.take_screenshot(screenshot_path):
                    self.logger.info(f"[BASE_MOBILE] [診斷] 診斷截圖已保存: {screenshot_path}")
            except Exception as e:
                self.logger.debug(f"[BASE_MOBILE] [診斷] 無法保存截圖: {e}")
            
            # 4. 獲取窗口大小和屏幕信息
            try:
                window_size = self.driver.get_window_size()
                self.logger.info(f"[BASE_MOBILE] [診斷] 窗口大小: {window_size}")
                
                # 獲取設備信息
                try:
                    device_info = {
                        'platform_version': self.driver.capabilities.get('platformVersion', 'N/A'),
                        'device_name': self.driver.capabilities.get('deviceName', 'N/A'),
                        'automation_name': self.driver.capabilities.get('automationName', 'N/A'),
                    }
                    self.logger.info(f"[BASE_MOBILE] [診斷] 設備信息: {device_info}")
                except:
                    pass
            except Exception as e:
                self.logger.debug(f"[BASE_MOBILE] [診斷] 無法獲取窗口大小: {e}")
                
        except Exception as e:
            self.logger.debug(f"[BASE_MOBILE] [診斷] 診斷過程發生錯誤: {e}")
    
    def swipe_vertical(self, direction: str = "down", duration: int = 500) -> bool:
        """
        垂直滑動（用於滾動服務器/攝像頭列表）
        
        Args:
            direction: 滑動方向，"up" 或 "down"（默認為 "down"）
            duration: 滑動持續時間（毫秒）
            
        Returns:
            bool: 滑動是否成功
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        if direction.lower() == "down":
            return self.swipe_down(duration)
        elif direction.lower() == "up":
            return self.swipe_up(duration)
        else:
            self.logger.error(f"[BASE_MOBILE] 不支援的滑動方向: {direction}")
            return False
    
    def tap_at_coordinates(self, x: int, y: int, duration: int = 100) -> bool:
        """
        在指定座標點擊（用於控制視頻時間軸）
        
        Args:
            x: X 座標
            y: Y 座標
            duration: 點擊持續時間（毫秒）
            
        Returns:
            bool: 點擊是否成功
        """
        if not self.driver:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            from appium.webdriver.common.touch_action import TouchAction
            action = TouchAction(self.driver)
            action.tap(x=x, y=y, duration=duration).perform()
            self.logger.debug(f"[BASE_MOBILE] 在座標 ({x}, {y}) 點擊成功")
            return True
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 在座標 ({x}, {y}) 點擊失敗: {e}")
            return False
    
    def find_and_click(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> bool:
        """
        查找元素並點擊（通用方法）
        
        Args:
            locator: 定位器元組 (定位策略, 定位值)，例如 (AppiumBy.ID, "com.example:id/button")
            timeout: 超時時間（秒）
            
        Returns:
            bool: 點擊是否成功
        """
        if not self.driver or not self.wait:
            self.logger.error("[BASE_MOBILE] WebDriver 未初始化")
            return False
        
        try:
            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            if element:
                return self.click_element(element)
            return False
        except TimeoutException:
            self.logger.warning(f"[BASE_MOBILE] 超時：找不到元素 {locator}")
            return False
        except Exception as e:
            self.logger.error(f"[BASE_MOBILE] 查找並點擊元素失敗 {locator}: {e}")
            return False
