# -*- coding: utf-8 -*-
"""
Playwright 基礎頁面類 (PlaywrightBasePage)

封裝 Playwright 的核心操作，實作反封號機制：
- 擬人化點擊（隨機延遲 + Hover）
- 自動等待（Playwright 內建，取代 Selenium WebDriverWait）
- 統一錯誤處理

與 Selenium WebBasePage 的關鍵差異：
- 無需 WebDriverWait（Playwright 自動等待）
- Locator API 更直觀（page.locator()）
- 支援內建的文本定位器（get_by_text, get_by_role）
- 點擊自帶 delay 參數（無需額外 sleep）
- 自動重試機制（StaleElementReference 不再出現）

設計原則：
- SRP (Single Responsibility Principle)：每個方法只負責一個職責
- DIP (Dependency Inversion Principle)：依賴抽象而非具體實作
- OCP (Open/Closed Principle)：對擴展開放，對修改封閉

Author: SDET Team
Date: 2026-01-27
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import time
import random

from playwright.sync_api import Page, Locator, Error as PlaywrightError

import config as C

if TYPE_CHECKING:
    from base.playwright_browser import PlaywrightBrowser


class PlaywrightBasePage:
    """
    Playwright 基礎頁面類
    
    提供統一的 Playwright 操作接口，內建反封號機制：
    1. 所有點擊動作自動加入隨機延遲（Playwright 的 delay 參數）
    2. 自動等待機制（Playwright 內建，無需 WebDriverWait）
    3. 完整的錯誤處理和自動重試
    
    Playwright 核心優勢：
    - **自動等待**：無需 WebDriverWait，Locator 會自動等待元素出現
    - **自動重試**：ActionabilityChecks 確保元素可操作
    - **無 Flaky 問題**：StaleElementReference 不再出現
    
    Attributes:
        browser (PlaywrightBrowser): 瀏覽器實例
        page (Page): Playwright Page 實例
    
    Example:
        >>> from base.playwright_browser import PlaywrightBrowser
        >>> browser = PlaywrightBrowser()
        >>> page_obj = PlaywrightBasePage(browser)
        >>> page_obj.smart_click("#submit-btn")
    """
    
    # 擬人化延遲配置（可被子類覆寫）
    MIN_HUMAN_DELAY = 0.5  # 最小延遲（秒）
    MAX_HUMAN_DELAY = 2.0  # 最大延遲（秒）
    
    def __init__(self, browser: "PlaywrightBrowser"):
        """
        初始化 PlaywrightBasePage
        
        Args:
            browser (PlaywrightBrowser): Playwright 瀏覽器實例
        
        Example:
            >>> browser = PlaywrightBrowser()
            >>> page_obj = PlaywrightBasePage(browser)
        """
        self.browser = browser
        self.page = browser.page
    
    # ==================== 擬人化工具方法 ====================
    
    def _random_human_delay(
        self,
        min_delay: Optional[float] = None,
        max_delay: Optional[float] = None
    ) -> None:
        """
        擬人化隨機延遲（模擬人類視線停頓與思考時間）
        
        注意：Playwright 的 click(delay=...) 已內建點擊延遲，
        此方法主要用於點擊前的「思考時間」模擬。
        
        Args:
            min_delay (float, optional): 最小延遲秒數
            max_delay (float, optional): 最大延遲秒數
        
        Returns:
            None
        
        Example:
            >>> self._random_human_delay()  # 0.5-2.0 秒隨機延遲
        """
        min_d = min_delay if min_delay is not None else self.MIN_HUMAN_DELAY
        max_d = max_delay if max_delay is not None else self.MAX_HUMAN_DELAY
        
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
    
    def _get_random_click_delay(self) -> int:
        """
        取得隨機點擊延遲（毫秒）
        
        Playwright 優勢：click(delay=...) 參數可模擬真人點擊速度
        - 真人點擊：50-200ms 按壓時間
        - 機器人：0ms 瞬間點擊
        
        Returns:
            int: 隨機延遲（毫秒）
        
        Example:
            >>> delay_ms = self._get_random_click_delay()
            >>> locator.click(delay=delay_ms)
        """
        min_delay = getattr(C, 'PLAYWRIGHT_CLICK_DELAY_MIN', 50)
        max_delay = getattr(C, 'PLAYWRIGHT_CLICK_DELAY_MAX', 200)
        return random.randint(min_delay, max_delay)
    
    def _get_random_hover_offset(self) -> tuple:
        """
        取得隨機 Hover 偏移（像素）
        
        擬人化策略：
        - 真人滑鼠不會精確移動到元素中心
        - 會有 ±3-5 像素的自然偏移
        
        Returns:
            tuple: (x_offset, y_offset)
        
        Example:
            >>> offset = self._get_random_hover_offset()
            >>> locator.hover(position={'x': center_x + offset[0], 'y': center_y + offset[1]})
        """
        max_offset = getattr(C, 'PLAYWRIGHT_HOVER_OFFSET_MAX', 5)
        x_offset = random.randint(-max_offset, max_offset)
        y_offset = random.randint(-max_offset, max_offset)
        return (x_offset, y_offset)
    
    # ==================== 核心操作方法 ====================
    
    def smart_click(
        self,
        selector: str,
        enable_human_delay: bool = True,
        enable_hover: Optional[bool] = None,
        timeout: Optional[int] = None
    ) -> bool:
        """
        智能點擊（內建擬人化延遲 + 自動等待）
        
        Playwright 核心優勢解析：
        
        1. **自動等待機制**（取代 Selenium WebDriverWait）
           - Playwright 的 Locator.click() 會自動等待：
             ✓ 元素存在於 DOM
             ✓ 元素可見（visible）
             ✓ 元素可啟用（enabled）
             ✓ 元素穩定（不再移動）
             ✓ 元素未被遮蓋
           - 無需手動 WebDriverWait.until(EC.element_to_be_clickable())
        
        2. **Actionability Checks**（解決 Selenium Flaky 問題）
           - Selenium 問題：
             ❌ 元素找到時可點擊，點擊時已被遮蓋 → ElementClickInterceptedException
             ❌ 元素在動畫中移動 → StaleElementReferenceException
           - Playwright 解決方案：
             ✓ 自動等待元素穩定（500ms 無變化）
             ✓ 自動重試（最多 30 秒）
             ✓ 自動滾動到可見區域
        
        3. **擬人化點擊**
           - delay 參數：模擬真人按壓時間（50-200ms）
           - hover 前置動作：模擬滑鼠移動軌跡
           - 隨機延遲：模擬思考時間（0.5-2.0 秒）
        
        Args:
            selector (str): 選擇器（支援 CSS, XPath, 文本等）
            enable_human_delay (bool): 是否啟用擬人化延遲
            enable_hover (bool, optional): 是否在點擊前 hover，None 時從 config 讀取
            timeout (int, optional): 超時時間（毫秒），None 時使用預設值
        
        Returns:
            bool: 點擊成功返回 True，失敗返回 False
        
        Raises:
            不會拋出異常，失敗時返回 False
        
        Example:
            >>> # CSS 選擇器
            >>> success = page.smart_click("#submit-btn")
            >>> 
            >>> # 文本選擇器（Playwright 特色）
            >>> success = page.smart_click("text=確認")
            >>> 
            >>> # XPath
            >>> success = page.smart_click("xpath=//button[@type='submit']")
            >>> 
            >>> # 禁用擬人化延遲（快速測試）
            >>> success = page.smart_click("#btn", enable_human_delay=False)
        """
        try:
            # 取得 Locator（Playwright 核心概念）
            locator = self.page.locator(selector)
            
            # 步驟 1: 擬人化延遲（模擬思考時間）
            if enable_human_delay:
                self._random_human_delay()
            
            # 步驟 2: Hover 前置動作（模擬滑鼠移動）
            # 降低被偵測風險：真人不會瞬間傳送到按鈕位置
            if enable_hover is None:
                enable_hover = getattr(C, 'PLAYWRIGHT_ENABLE_HOVER_BEFORE_CLICK', True)
            
            if enable_hover:
                try:
                    # Playwright 優勢：hover() 會自動等待元素可見
                    locator.hover(timeout=timeout if timeout else 5000)
                    
                    # 短暫停頓（模擬滑鼠懸停）
                    time.sleep(random.uniform(0.1, 0.3))
                except PlaywrightError:
                    # Hover 失敗不影響點擊（某些元素無法 hover）
                    pass
            
            # 步驟 3: 執行點擊（內建擬人化延遲）
            # Playwright 優勢：
            # - delay 參數模擬按壓時間（真人：50-200ms，機器人：0ms）
            # - 自動滾動到可見區域
            # - 自動等待元素穩定
            # - 自動重試（預設 30 秒）
            click_delay_ms = self._get_random_click_delay()
            
            locator.click(
                delay=click_delay_ms,  # 按壓延遲（毫秒）
                timeout=timeout  # 超時時間（毫秒）
            )
            
            return True
        
        except PlaywrightError as e:
            # Playwright 異常處理
            # 注意：Playwright 不會出現 StaleElementReferenceException
            # 因為 Locator 是惰性的，每次操作都會重新查找元素
            return False
        
        except Exception:
            # 其他未預期異常
            return False
    
    def smart_type(
        self,
        selector: str,
        text: str,
        clear: bool = True,
        enable_human_typing: bool = True,
        timeout: Optional[int] = None
    ) -> bool:
        """
        智能輸入（內建逐字元輸入 + 自動等待）
        
        Playwright 核心優勢：
        
        1. **fill() vs type()**
           - fill()：快速填充（適合非敏感場景）
           - type()：逐字元輸入（模擬真人，適合敏感場景）
        
        2. **自動等待機制**
           - 自動等待元素可見
           - 自動等待元素可啟用
           - 自動聚焦（focus）
        
        3. **擬人化輸入**
           - delay 參數：每個字元間隔（50-150ms）
           - 無需手動迴圈
        
        Args:
            selector (str): 選擇器
            text (str): 要輸入的文字
            clear (bool): 是否先清空欄位
            enable_human_typing (bool): 是否啟用擬人化打字（逐字元輸入）
            timeout (int, optional): 超時時間（毫秒）
        
        Returns:
            bool: 輸入成功返回 True，失敗返回 False
        
        Example:
            >>> # 擬人化輸入（推薦）
            >>> success = page.smart_type("#username", "admin@example.com")
            >>> 
            >>> # 快速輸入（測試環境）
            >>> success = page.smart_type("#search", "keyword", enable_human_typing=False)
        """
        try:
            locator = self.page.locator(selector)
            
            # 步驟 1: 清空欄位（如果需要）
            if clear:
                locator.fill("", timeout=timeout)
                time.sleep(0.1)
            
            # 步驟 2: 輸入文字
            if enable_human_typing:
                # 擬人化打字：逐字元輸入
                # Playwright 優勢：type() 方法內建 delay 參數
                min_delay = getattr(C, 'MIN_TYPING_DELAY', 0.05) * 1000  # 轉換為毫秒
                max_delay = getattr(C, 'MAX_TYPING_DELAY', 0.15) * 1000
                typing_delay = random.uniform(min_delay, max_delay)
                
                locator.type(text, delay=typing_delay, timeout=timeout)
            else:
                # 快速輸入：fill() 方法（瞬間完成）
                locator.fill(text, timeout=timeout)
            
            return True
        
        except PlaywrightError:
            return False
        
        except Exception:
            return False
    
    def smart_get_text(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        智能取得文字（內建自動等待）
        
        Playwright 優勢：
        - text_content() 方法直接取得文字
        - inner_text() 方法取得可見文字（推薦）
        - 自動等待元素可見
        
        Args:
            selector (str): 選擇器
            timeout (int, optional): 超時時間（毫秒）
        
        Returns:
            Optional[str]: 成功返回文字，失敗返回 None
        
        Example:
            >>> text = page.smart_get_text("#message")
            >>> print(f"訊息: {text}")
        """
        try:
            locator = self.page.locator(selector)
            # inner_text() 取得可見文字（排除隱藏元素）
            return locator.inner_text(timeout=timeout).strip()
        
        except PlaywrightError:
            return None
        
        except Exception:
            return None
    
    def is_visible(
        self,
        selector: str,
        timeout: int = 3000
    ) -> bool:
        """
        檢查元素是否可見
        
        Playwright 優勢：
        - is_visible() 方法更直觀
        - 無需 try-except（內建超時處理）
        
        Args:
            selector (str): 選擇器
            timeout (int): 超時時間（毫秒）
        
        Returns:
            bool: 元素可見返回 True，否則返回 False
        
        Example:
            >>> if page.is_visible("#error-msg"):
            >>>     print("錯誤訊息出現")
        """
        try:
            locator = self.page.locator(selector)
            locator.wait_for(state='visible', timeout=timeout)
            return True
        except PlaywrightError:
            return False
    
    def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[int] = None
    ) -> bool:
        """
        等待 URL 變更
        
        Playwright 優勢：
        - wait_for_url() 方法內建
        - 支援正則表達式匹配
        - 支援通配符（glob pattern）
        
        Args:
            url_pattern (str): URL 模式（支援正則、通配符）
            timeout (int, optional): 超時時間（毫秒）
        
        Returns:
            bool: URL 符合預期返回 True，超時返回 False
        
        Example:
            >>> # 通配符匹配
            >>> success = page.wait_for_url("**/dashboard")
            >>> 
            >>> # 正則表達式
            >>> success = page.wait_for_url(r"https://.*\.example\.com/.*")
        """
        try:
            self.page.wait_for_url(url_pattern, timeout=timeout)
            return True
        except PlaywrightError:
            return False
    
    # ==================== 進階操作 ====================
    
    def smart_click_with_retry(
        self,
        selector: str,
        max_retries: int = 3,
        enable_human_delay: bool = True
    ) -> bool:
        """
        智能點擊（帶重試機制）
        
        注意：Playwright 的自動重試已經很強大，
        此方法主要用於極端不穩定的場景。
        
        Args:
            selector (str): 選擇器
            max_retries (int): 最大重試次數
            enable_human_delay (bool): 是否啟用擬人化延遲
        
        Returns:
            bool: 點擊成功返回 True，所有重試失敗返回 False
        
        Example:
            >>> success = page.smart_click_with_retry("text=動態按鈕")
        """
        for attempt in range(max_retries):
            success = self.smart_click(
                selector,
                enable_human_delay=enable_human_delay
            )
            
            if success:
                return True
            
            # 重試前短暫等待
            if attempt < max_retries - 1:
                time.sleep(0.5)
        
        return False
    
    def get_all_texts(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> List[str]:
        """
        取得所有符合選擇器的元素文字
        
        Playwright 優勢：
        - all_text_contents() 一次取得所有文字
        - 無需迴圈處理
        
        Args:
            selector (str): 選擇器
            timeout (int, optional): 超時時間（毫秒）
        
        Returns:
            List[str]: 文字內容列表
        
        Example:
            >>> items = page.get_all_texts(".menu-item")
            >>> print(f"選單: {items}")
        """
        try:
            locator = self.page.locator(selector)
            return locator.all_text_contents()
        except PlaywrightError:
            return []
    
    def count_elements(
        self,
        selector: str
    ) -> int:
        """
        計算符合選擇器的元素數量
        
        Playwright 優勢：
        - count() 方法直接取得數量
        - 自動等待元素出現
        
        Args:
            selector (str): 選擇器
        
        Returns:
            int: 元素數量
        
        Example:
            >>> count = page.count_elements(".product-card")
            >>> print(f"商品數: {count}")
        """
        locator = self.page.locator(selector)
        return locator.count()
    
    # ==================== Playwright 特色方法 ====================
    
    def click_by_text(
        self,
        text: str,
        exact: bool = False,
        enable_human_delay: bool = True
    ) -> bool:
        """
        根據文字點擊元素（Playwright 特色）
        
        Playwright 核心優勢：
        - 內建文本選擇器（無需複雜 XPath）
        - 支援模糊匹配和精確匹配
        - 比 XPath 更穩定（不受 DOM 結構變化影響）
        
        Args:
            text (str): 文字內容
            exact (bool): 是否精確匹配
            enable_human_delay (bool): 是否啟用擬人化延遲
        
        Returns:
            bool: 點擊成功返回 True，失敗返回 False
        
        Example:
            >>> # 模糊匹配（推薦）
            >>> page.click_by_text("確認")  # 匹配 "確認", "確認提交" 等
            >>> 
            >>> # 精確匹配
            >>> page.click_by_text("確認", exact=True)  # 僅匹配 "確認"
        """
        selector = f"text={text}" if exact else f"text='{text}'"
        return self.smart_click(selector, enable_human_delay=enable_human_delay)
    
    def click_by_role(
        self,
        role: str,
        name: Optional[str] = None,
        enable_human_delay: bool = True
    ) -> bool:
        """
        根據 ARIA 角色點擊元素（Playwright 特色）
        
        Playwright 核心優勢：
        - 符合無障礙標準（Accessibility）
        - 比 ID/Class 更穩定（語義化選擇器）
        - 推薦用於按鈕、連結、輸入框等標準元素
        
        常用角色：
        - button: 按鈕
        - link: 連結
        - textbox: 文字輸入框
        - checkbox: 複選框
        - radio: 單選按鈕
        
        Args:
            role (str): ARIA 角色
            name (str, optional): 可訪問名稱（文字、aria-label 等）
            enable_human_delay (bool): 是否啟用擬人化延遲
        
        Returns:
            bool: 點擊成功返回 True，失敗返回 False
        
        Example:
            >>> # 點擊任意按鈕
            >>> page.click_by_role("button")
            >>> 
            >>> # 點擊特定名稱的按鈕
            >>> page.click_by_role("button", name="提交")
            >>> 
            >>> # 點擊連結
            >>> page.click_by_role("link", name="了解更多")
        """
        try:
            if name:
                locator = self.page.get_by_role(role, name=name)
            else:
                locator = self.page.get_by_role(role)
            
            if enable_human_delay:
                self._random_human_delay()
            
            click_delay_ms = self._get_random_click_delay()
            locator.click(delay=click_delay_ms)
            
            return True
        except PlaywrightError:
            return False
