# -*- coding: utf-8 -*-
"""
Playwright 瀏覽器管理類 (PlaywrightBrowser)

封裝 Playwright 的初始化和生命週期管理。
整合反封號機制：User-Agent 隨機化、瀏覽器指紋隱藏、視窗擾動。

與 Selenium Browser 的關鍵差異：
- 無需 WebDriver Manager（Playwright 內建瀏覽器驅動）
- 支援 Browser -> Context -> Page 三層架構（更好的隔離性）
- 原生反爬蟲（無 navigator.webdriver 標記）
- 自動等待機制（無需 WebDriverWait）

Author: SDET Team
Date: 2026-01-27
"""

from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from toolkit.playwright_toolkit import (
    create_playwright_browser,
    create_browser_context
)


class PlaywrightBrowser:
    """
    Playwright 瀏覽器管理類
    
    負責 Playwright 的創建、配置和清理，內建反封號機制：
    - 自動隨機化 User-Agent（從 config 讀取）
    - 原生移除 Selenium 自動化標記（Playwright 特性）
    - 隨機化瀏覽器視窗大小（±5-10 像素擾動）
    - 自動清理資源（Browser、Context、Playwright）
    
    架構層級：
    Playwright -> Browser -> Context -> Page
    
    Attributes:
        playwright (Playwright): Playwright 實例
        browser (Browser): Playwright Browser 實例
        context (BrowserContext): 瀏覽器上下文
        page (Page): 當前頁面實例
    
    Example:
        >>> browser = PlaywrightBrowser()
        >>> browser.open("https://example.com")
        >>> browser.quit()
    """
    
    def __init__(
        self,
        enable_anti_bot: Optional[bool] = None,
        headless: Optional[bool] = None
    ):
        """
        初始化 Playwright 瀏覽器
        
        Args:
            enable_anti_bot (bool, optional): 是否啟用反封號機制
                                            None 時從 config 讀取
            headless (bool, optional): 無頭模式，None 時從 config 讀取
        
        Note:
            - Playwright 會自動下載瀏覽器驅動（首次使用時）
            - Context 提供隔離的環境（類似 Incognito 模式）
            - Page 是實際操作的頁面實例
        """
        # 創建 Playwright 和 Browser
        self.playwright, self.browser = create_playwright_browser(
            enable_anti_bot=enable_anti_bot,
            headless=headless
        )
        
        # 創建 Context（反封號配置在此層級注入）
        self.context = create_browser_context(
            self.browser,
            enable_anti_bot=enable_anti_bot
        )
        
        # 創建第一個 Page
        self.page = self.context.new_page()
    
    def open(self, url: str, wait_until: str = 'load') -> None:
        """
        開啟指定 URL
        
        Playwright 優勢：
        - 內建多種等待策略（load, domcontentloaded, networkidle, commit）
        - 自動等待頁面載入完成（無需額外等待）
        
        Args:
            url (str): 目標 URL
            wait_until (str): 等待策略
                - 'load': 等待 load 事件（預設）
                - 'domcontentloaded': 等待 DOM 載入
                - 'networkidle': 等待網路閒置
                - 'commit': 等待提交（最快）
        
        Example:
            >>> browser.open("https://example.com")
            >>> browser.open("https://spa-app.com", wait_until='networkidle')
        """
        self.page.goto(url, wait_until=wait_until)
    
    def new_page(self) -> Page:
        """
        創建新的頁面（相當於新分頁）
        
        Playwright 優勢：
        - 支援多頁面並行操作
        - 每個 Page 共享 Context 的 Cookies 和 Storage
        
        Returns:
            Page: 新的頁面實例
        
        Example:
            >>> page2 = browser.new_page()
            >>> page2.goto("https://another-site.com")
        """
        return self.context.new_page()
    
    def switch_to_page(self, page_index: int = 0) -> None:
        """
        切換到指定頁面
        
        Args:
            page_index (int): 頁面索引（0 為第一個頁面）
        
        Example:
            >>> browser.switch_to_page(1)  # 切換到第二個頁面
        """
        pages = self.context.pages
        if 0 <= page_index < len(pages):
            self.page = pages[page_index]
    
    def close_page(self, page: Optional[Page] = None) -> None:
        """
        關閉指定頁面
        
        Args:
            page (Page, optional): 要關閉的頁面，None 時關閉當前頁面
        
        Example:
            >>> browser.close_page()  # 關閉當前頁面
        """
        if page is None:
            page = self.page
        
        page.close()
        
        # 如果關閉的是當前頁面，切換到第一個可用頁面
        if page == self.page and self.context.pages:
            self.page = self.context.pages[0]
    
    def quit(self) -> None:
        """
        關閉瀏覽器並清理資源
        
        Playwright 資源清理順序：
        1. 關閉所有 Pages（可選，Context 關閉時會自動關閉）
        2. 關閉 Context
        3. 關閉 Browser
        4. 停止 Playwright
        
        Note:
            - 資源清理失敗不會中斷程式
            - Playwright 不需要清理臨時 Profile（自動管理）
        
        Example:
            >>> browser.quit()
        """
        try:
            # 關閉 Context（會自動關閉所有 Pages）
            if self.context:
                self.context.close()
        except Exception:
            pass
        
        try:
            # 關閉 Browser
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        
        try:
            # 停止 Playwright
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
    
    def __enter__(self):
        """
        Context Manager 支援（with 語句）
        
        Example:
            >>> with PlaywrightBrowser() as browser:
            >>>     browser.open("https://example.com")
            >>>     # 自動清理資源
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context Manager 退出時自動清理
        """
        self.quit()
