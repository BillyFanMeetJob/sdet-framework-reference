# -*- coding: utf-8 -*-
"""
Web 自動化基礎頁面類 (WebBasePage)

封裝 Web 自動化的核心操作，實作反封號機制：
- 擬人化點擊（隨機延遲）
- 智能等待（WebDriverWait）
- 統一錯誤處理

設計原則：
- SRP (Single Responsibility Principle)：每個方法只負責一個職責
- DIP (Dependency Inversion Principle)：依賴抽象而非具體實作
- OCP (Open/Closed Principle)：對擴展開放，對修改封閉

Author: SDET Team
Date: 2026-01-27
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Optional
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from toolkit.types import Locator

if TYPE_CHECKING:
    from base.browser import Browser  # 避免循環 import


class WebBasePage:
    """
    Web 自動化基礎頁面類
    
    提供統一的 Web 操作接口，內建反封號機制：
    1. 所有點擊動作自動加入隨機延遲（模擬人類思考時間）
    2. 智能顯式等待（WebDriverWait）確保元素可操作
    3. 完整的錯誤處理和重試機制
    
    Attributes:
        browser (Browser): 瀏覽器實例
        driver (WebDriver): Selenium WebDriver 實例
        wait (WebDriverWait): WebDriverWait 實例
    
    Example:
        >>> from base.browser import Browser
        >>> browser = Browser()
        >>> page = WebBasePage(browser)
        >>> page.smart_click(("id", "submit-btn"))
    """
    
    # 擬人化延遲配置（可被子類覆寫）
    MIN_HUMAN_DELAY = 0.5  # 最小延遲（秒）
    MAX_HUMAN_DELAY = 2.0  # 最大延遲（秒）
    MIN_TYPING_DELAY = 0.05  # 打字最小延遲（秒/字元）
    MAX_TYPING_DELAY = 0.15  # 打字最大延遲（秒/字元）
    
    def __init__(self, browser: "Browser"):
        """
        初始化 WebBasePage
        
        Args:
            browser (Browser): 瀏覽器實例，包含 driver 和 wait
        
        Example:
            >>> browser = Browser()
            >>> page = WebBasePage(browser)
        """
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait
    
    # ==================== 擬人化工具方法 ====================
    
    def _random_human_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None) -> None:
        """
        擬人化隨機延遲（模擬人類視線停頓與思考時間）
        
        此方法用於在操作前加入隨機延遲，避免機器人行為被偵測：
        - 人類在點擊前通常會有 0.5-2 秒的視線停頓
        - 隨機化的延遲可以打破固定的操作節奏
        - 降低被網站反爬蟲機制偵測的風險
        
        Args:
            min_delay (float, optional): 最小延遲秒數，預設使用類屬性 MIN_HUMAN_DELAY
            max_delay (float, optional): 最大延遲秒數，預設使用類屬性 MAX_HUMAN_DELAY
        
        Returns:
            None
        
        Note:
            - 此方法會阻塞當前線程
            - 延遲時間為 [min_delay, max_delay] 之間的隨機值
            - 在高頻操作時可適當縮短延遲範圍
        
        Example:
            >>> self._random_human_delay()  # 使用預設範圍 0.5-2.0 秒
            >>> self._random_human_delay(0.1, 0.5)  # 自訂範圍
        """
        min_d = min_delay if min_delay is not None else self.MIN_HUMAN_DELAY
        max_d = max_delay if max_delay is not None else self.MAX_HUMAN_DELAY
        
        # 使用 uniform 生成均勻分布的隨機浮點數
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
    
    def _random_typing_delay(self) -> None:
        """
        擬人化打字延遲（模擬人類打字速度）
        
        人類打字時每個字元之間有微小的時間間隔：
        - 快速打字者：約 50-100ms/字元
        - 慢速打字者：約 100-200ms/字元
        
        此方法用於在每個字元輸入間加入微小隨機延遲，
        使打字行為更接近真人，降低被偵測風險。
        
        Returns:
            None
        
        Example:
            >>> for char in "password":
            >>>     element.send_keys(char)
            >>>     self._random_typing_delay()
        """
        delay = random.uniform(self.MIN_TYPING_DELAY, self.MAX_TYPING_DELAY)
        time.sleep(delay)
    
    # ==================== 智能等待操作 ====================
    
    def smart_click(
        self,
        locator: Tuple[str, str],
        timeout: int = 10,
        enable_human_delay: bool = True,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ) -> bool:
        """
        智能點擊（內建顯式等待 + 擬人化延遲）
        
        此方法實作完整的反封號點擊策略：
        1. WebDriverWait 顯式等待元素可點擊（確保 DOM 已載入）
        2. 擬人化隨機延遲（模擬視線停頓，0.5-2.0 秒）
        3. 執行點擊操作
        4. 錯誤處理和自動重試
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器，格式為 (策略, 值)
                                      例如: ("id", "submit-btn"), ("xpath", "//button[@text='確認']")
            timeout (int): 等待超時時間（秒），預設 10 秒
            enable_human_delay (bool): 是否啟用擬人化延遲，預設 True
            min_delay (float, optional): 最小延遲秒數，預設使用類屬性
            max_delay (float, optional): 最大延遲秒數，預設使用類屬性
        
        Returns:
            bool: 點擊成功返回 True，失敗返回 False
        
        Raises:
            不會拋出異常，失敗時返回 False 並記錄日誌
        
        Note:
            - 顯式等待確保元素真正可點擊（避免 ElementNotInteractableException）
            - 擬人化延遲可降低被反爬蟲機制偵測的風險
            - StaleElementReferenceException 會自動重試一次
        
        Example:
            >>> # 基本使用
            >>> success = page.smart_click(("id", "login-btn"))
            >>> 
            >>> # 自訂等待時間
            >>> success = page.smart_click(("xpath", "//button"), timeout=15)
            >>> 
            >>> # 禁用擬人化延遲（測試環境）
            >>> success = page.smart_click(("id", "btn"), enable_human_delay=False)
            >>> 
            >>> # 自訂延遲範圍（快速操作）
            >>> success = page.smart_click(("id", "btn"), min_delay=0.1, max_delay=0.3)
        """
        try:
            # 步驟 1: 顯式等待元素可點擊
            # 使用 EC.element_to_be_clickable 確保：
            # - 元素已存在於 DOM
            # - 元素可見（visible）
            # - 元素可交互（enabled）
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            
            # 步驟 2: 擬人化延遲（模擬視線停頓）
            # 降低被偵測風險的關鍵步驟：
            # - 真人在點擊前會有視線追蹤和思考時間
            # - 隨機延遲避免固定節奏被識別為機器人
            if enable_human_delay:
                self._random_human_delay(min_delay, max_delay)
            
            # 步驟 3: 執行點擊
            element.click()
            
            return True
            
        except StaleElementReferenceException:
            # 元素在等待過程中被重新渲染（常見於動態頁面）
            # 自動重試一次
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable(locator)
                )
                if enable_human_delay:
                    self._random_human_delay(min_delay, max_delay)
                element.click()
                return True
            except Exception:
                return False
                
        except TimeoutException:
            # 元素在指定時間內未變為可點擊狀態
            return False
            
        except Exception:
            # 其他未預期的異常
            return False
    
    def smart_type(
        self,
        locator: Tuple[str, str],
        text: str,
        timeout: int = 10,
        clear: bool = True,
        enable_human_typing: bool = True
    ) -> bool:
        """
        智能輸入（內建顯式等待 + 擬人化打字）
        
        實作反封號的輸入策略：
        1. WebDriverWait 等待元素可見
        2. 可選清空原有內容
        3. 擬人化逐字輸入（每個字元間隔 50-150ms）
        4. 完整錯誤處理
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            text (str): 要輸入的文字
            timeout (int): 等待超時時間（秒），預設 10 秒
            clear (bool): 是否先清空欄位，預設 True
            enable_human_typing (bool): 是否啟用擬人化打字，預設 True
        
        Returns:
            bool: 輸入成功返回 True，失敗返回 False
        
        Note:
            - 擬人化打字會逐字元輸入，每個字元間有隨機延遲
            - 禁用擬人化打字時會一次性輸入全部文字（速度更快）
            - 建議在非敏感操作（如搜尋）時禁用擬人化以提升速度
        
        Example:
            >>> # 擬人化輸入帳號
            >>> page.smart_type(("id", "username"), "admin@example.com")
            >>> 
            >>> # 快速輸入（禁用擬人化）
            >>> page.smart_type(("id", "search"), "keyword", enable_human_typing=False)
        """
        try:
            # 步驟 1: 等待元素可見
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            
            # 步驟 2: 清空欄位（如果需要）
            if clear:
                element.clear()
                # 清空後短暫延遲（避免輸入過快）
                time.sleep(0.1)
            
            # 步驟 3: 輸入文字
            if enable_human_typing:
                # 擬人化打字：逐字元輸入，模擬真人打字節奏
                # 降低被偵測風險的關鍵：
                # - 機器人通常會瞬間輸入完整字串
                # - 真人打字有明顯的時間間隔（受限於手指速度）
                # - 隨機化的間隔可避免固定節奏被識別
                for char in text:
                    element.send_keys(char)
                    self._random_typing_delay()
            else:
                # 快速輸入：一次性輸入（適用於非敏感場景）
                element.send_keys(text)
            
            return True
            
        except StaleElementReferenceException:
            # 元素在等待過程中被重新渲染，重試一次
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(locator)
                )
                if clear:
                    element.clear()
                    time.sleep(0.1)
                
                if enable_human_typing:
                    for char in text:
                        element.send_keys(char)
                        self._random_typing_delay()
                else:
                    element.send_keys(text)
                
                return True
            except Exception:
                return False
                
        except TimeoutException:
            # 元素在指定時間內未變為可見
            return False
            
        except Exception:
            # 其他未預期的異常
            return False
    
    def smart_get_text(
        self,
        locator: Tuple[str, str],
        timeout: int = 10
    ) -> Optional[str]:
        """
        智能取得文字（內建顯式等待）
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒），預設 10 秒
        
        Returns:
            Optional[str]: 成功返回元素文字，失敗返回 None
        
        Example:
            >>> text = page.smart_get_text(("id", "message"))
            >>> if text:
            >>>     print(f"訊息: {text}")
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return element.text.strip()
            
        except TimeoutException:
            return None
            
        except Exception:
            return None
    
    def is_element_visible(
        self,
        locator: Tuple[str, str],
        timeout: int = 3
    ) -> bool:
        """
        檢查元素是否可見（不拋出異常）
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒），預設 3 秒
        
        Returns:
            bool: 元素可見返回 True，否則返回 False
        
        Example:
            >>> if page.is_element_visible(("id", "error-msg")):
            >>>     print("錯誤訊息出現")
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
        except Exception:
            return False
    
    def is_element_clickable(
        self,
        locator: Tuple[str, str],
        timeout: int = 3
    ) -> bool:
        """
        檢查元素是否可點擊（不拋出異常）
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒），預設 3 秒
        
        Returns:
            bool: 元素可點擊返回 True，否則返回 False
        
        Example:
            >>> if page.is_element_clickable(("id", "submit-btn")):
            >>>     page.smart_click(("id", "submit-btn"))
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return True
        except TimeoutException:
            return False
        except Exception:
            return False
    
    # ==================== 進階操作 ====================
    
    def smart_click_with_retry(
        self,
        locator: Tuple[str, str],
        timeout: int = 10,
        max_retries: int = 3,
        enable_human_delay: bool = True
    ) -> bool:
        """
        智能點擊（帶重試機制）
        
        對於不穩定的元素（如動態載入的按鈕），提供自動重試功能：
        - 失敗時自動重試（最多 max_retries 次）
        - 每次重試前短暫等待（允許頁面完成渲染）
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 每次嘗試的超時時間（秒）
            max_retries (int): 最大重試次數，預設 3 次
            enable_human_delay (bool): 是否啟用擬人化延遲
        
        Returns:
            bool: 點擊成功返回 True，所有重試失敗返回 False
        
        Example:
            >>> # 點擊動態載入的按鈕（自動重試）
            >>> success = page.smart_click_with_retry(("xpath", "//button[@dynamic='true']"))
        """
        for attempt in range(max_retries):
            success = self.smart_click(
                locator=locator,
                timeout=timeout,
                enable_human_delay=enable_human_delay
            )
            
            if success:
                return True
            
            # 重試前短暫等待（允許頁面重新渲染）
            if attempt < max_retries - 1:
                time.sleep(0.5)
        
        return False
    
    def smart_type_with_validation(
        self,
        locator: Tuple[str, str],
        text: str,
        timeout: int = 10,
        clear: bool = True,
        enable_human_typing: bool = True,
        validate: bool = True
    ) -> bool:
        """
        智能輸入（帶驗證機制）
        
        輸入後驗證欄位值是否正確（防止輸入失敗）：
        - 輸入文字
        - 讀取欄位值
        - 比對是否一致
        - 不一致時自動重試
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            text (str): 要輸入的文字
            timeout (int): 等待超時時間（秒）
            clear (bool): 是否先清空欄位
            enable_human_typing (bool): 是否啟用擬人化打字
            validate (bool): 是否驗證輸入結果，預設 True
        
        Returns:
            bool: 輸入並驗證成功返回 True，失敗返回 False
        
        Example:
            >>> # 輸入帳號並驗證
            >>> success = page.smart_type_with_validation(
            >>>     ("id", "username"),
            >>>     "admin@example.com"
            >>> )
        """
        # 步驟 1: 輸入文字
        success = self.smart_type(
            locator=locator,
            text=text,
            timeout=timeout,
            clear=clear,
            enable_human_typing=enable_human_typing
        )
        
        if not success:
            return False
        
        # 步驟 2: 驗證輸入（如果啟用）
        if validate:
            try:
                element = self.driver.find_element(*locator)
                actual_value = element.get_attribute("value") or ""
                
                # 比對實際值與預期值
                if actual_value.strip() == text.strip():
                    return True
                else:
                    # 輸入值不符，返回失敗
                    return False
                    
            except Exception:
                # 驗證失敗（可能元素已消失）
                return False
        
        return True
    
    def wait_for_url_change(
        self,
        expected_url: str,
        timeout: int = 10,
        partial: bool = True
    ) -> bool:
        """
        等待 URL 變更（用於驗證頁面跳轉）
        
        Args:
            expected_url (str): 預期的 URL（或 URL 片段）
            timeout (int): 等待超時時間（秒）
            partial (bool): 是否部分匹配，預設 True
                          - True: URL 包含 expected_url 即可
                          - False: URL 必須完全等於 expected_url
        
        Returns:
            bool: URL 符合預期返回 True，超時返回 False
        
        Example:
            >>> # 等待跳轉到儀表板
            >>> success = page.wait_for_url_change("/dashboard")
            >>> 
            >>> # 等待完整 URL 匹配
            >>> success = page.wait_for_url_change(
            >>>     "https://example.com/home",
            >>>     partial=False
            >>> )
        """
        try:
            if partial:
                condition = EC.url_contains(expected_url)
            else:
                condition = EC.url_to_be(expected_url)
            
            WebDriverWait(self.driver, timeout).until(condition)
            return True
            
        except TimeoutException:
            return False
            
        except Exception:
            return False
    
    # ==================== 批量操作 ====================
    
    def find_all_visible(
        self,
        locator: Tuple[str, str],
        timeout: int = 10
    ) -> List[WebElement]:
        """
        查找所有可見元素
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒）
        
        Returns:
            List[WebElement]: 可見元素列表，找不到時返回空列表
        
        Example:
            >>> # 查找所有商品卡片
            >>> items = page.find_all_visible(("class name", "product-card"))
            >>> print(f"找到 {len(items)} 個商品")
        """
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_all_elements_located(locator)
            )
            return elements
            
        except TimeoutException:
            return []
            
        except Exception:
            return []
    
    def get_all_texts(
        self,
        locator: Tuple[str, str],
        timeout: int = 10
    ) -> List[str]:
        """
        取得所有可見元素的文字內容
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒）
        
        Returns:
            List[str]: 文字內容列表，找不到時返回空列表
        
        Example:
            >>> # 取得所有選項文字
            >>> options = page.get_all_texts(("xpath", "//select/option"))
            >>> print(f"可用選項: {options}")
        """
        elements = self.find_all_visible(locator, timeout)
        return [elem.text.strip() for elem in elements if elem.text]
    
    def count_visible_elements(
        self,
        locator: Tuple[str, str],
        timeout: int = 10
    ) -> int:
        """
        計算可見元素數量
        
        Args:
            locator (Tuple[str, str]): Selenium 定位器
            timeout (int): 等待超時時間（秒）
        
        Returns:
            int: 可見元素數量
        
        Example:
            >>> # 計算購物車商品數量
            >>> count = page.count_visible_elements(("class name", "cart-item"))
            >>> print(f"購物車有 {count} 件商品")
        """
        elements = self.find_all_visible(locator, timeout)
        return len(elements)
    
    # ==================== 向後兼容方法 ====================
    
    def click(self, locator: Locator) -> WebElement:
        """
        基本點擊（向後兼容舊版 BasePage）
        
        注意：此方法為向後兼容而保留，建議使用 smart_click()
        
        Args:
            locator (Locator): Selenium 定位器
        
        Returns:
            WebElement: 被點擊的元素
        
        Raises:
            TimeoutException: 元素不可點擊時拋出
        """
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
        return element
    
    def type(
        self,
        locator: Locator,
        text: str,
        clear: bool = True
    ) -> WebElement:
        """
        基本輸入（向後兼容舊版 BasePage）
        
        注意：此方法為向後兼容而保留，建議使用 smart_type()
        
        Args:
            locator (Locator): Selenium 定位器
            text (str): 要輸入的文字
            clear (bool): 是否先清空欄位
        
        Returns:
            WebElement: 輸入欄位元素
        
        Raises:
            TimeoutException: 元素不可見時拋出
        """
        element = self.wait.until(EC.visibility_of_element_located(locator))
        if clear:
            element.clear()
        element.send_keys(text)
        return element
    
    def get_text(self, locator: Locator) -> str:
        """
        基本取得文字（向後兼容舊版 BasePage）
        
        注意：此方法為向後兼容而保留，建議使用 smart_get_text()
        
        Args:
            locator (Locator): Selenium 定位器
        
        Returns:
            str: 元素文字內容
        
        Raises:
            TimeoutException: 元素不可見時拋出
        """
        element = self.wait.until(EC.visibility_of_element_located(locator))
        return element.text.strip()
    
    def is_visible(self, locator: Locator) -> bool:
        """
        檢查元素是否可見（向後兼容舊版 BasePage）
        
        Args:
            locator (Locator): Selenium 定位器
        
        Returns:
            bool: 元素可見返回 True，否則返回 False
        """
        return self.is_element_visible(locator, timeout=3)
    
    def find_all(self, locator: Locator) -> List[WebElement]:
        """
        查找所有可見元素（向後兼容舊版 BasePage）
        
        Args:
            locator (Locator): Selenium 定位器
        
        Returns:
            List[WebElement]: 可見元素列表
        """
        return self.find_all_visible(locator, timeout=10)
