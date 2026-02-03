# -*- coding: utf-8 -*-
"""
Playwright Toolkit - Playwright 工具函數集

提供 Playwright 的創建、配置和基礎操作工具函數。
實作反封號機制：
- User-Agent 隨機化
- 瀏覽器指紋隱藏
- 視窗大小隨機擾動
- 自動等待機制（取代 Selenium 的顯式等待）

Author: SDET Team
Date: 2026-01-27
"""

import os
import time
import random
from typing import Optional, Tuple, Dict, Any

from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Error as PlaywrightError
)

import config as C


def create_playwright_browser(
    enable_anti_bot: Optional[bool] = None,
    headless: Optional[bool] = None,
    slow_mo: Optional[int] = None
) -> Tuple[Playwright, Browser]:
    """
    創建 Playwright Browser 實例（內建反封號機制）
    
    實作完整的反偵測策略：
    1. User-Agent 隨機化（從 config 的 USER_AGENT_POOL 隨機選擇）
    2. 視窗大小隨機擾動（±5-10 像素）
    3. 忽略 HTTPS 錯誤
    4. 自動等待機制（Playwright 內建，無需 WebDriverWait）
    
    與 Selenium 的關鍵差異：
    - Playwright 不需要 WebDriver Manager（內建瀏覽器驅動）
    - 自動等待機制更穩定（無需顯式 WebDriverWait）
    - 支援多個瀏覽器引擎（Chromium, Firefox, WebKit）
    - 原生支援反爬蟲繞過（無 navigator.webdriver）
    
    Args:
        enable_anti_bot (bool, optional): 是否啟用反封號機制，None 時從 config 讀取
        headless (bool, optional): 無頭模式，None 時從 config 讀取
        slow_mo (int, optional): 慢動作模式（毫秒），None 時從 config 讀取
    
    Returns:
        Tuple[Playwright, Browser]: (playwright, browser) 元組
    
    Raises:
        PlaywrightError: Playwright 初始化失敗
    
    Note:
        - Playwright 不會暴露 navigator.webdriver（原生反爬蟲）
        - Browser 實例需手動關閉（調用 browser.close()）
        - Playwright 實例需手動停止（調用 playwright.stop()）
    
    Example:
        >>> # 使用預設配置（啟用反封號）
        >>> playwright, browser = create_playwright_browser()
        >>> context = create_browser_context(browser)
        >>> page = context.new_page()
        >>> 
        >>> # 清理
        >>> browser.close()
        >>> playwright.stop()
    """
    # 從 config 讀取配置
    if enable_anti_bot is None:
        enable_anti_bot = getattr(C, 'ENABLE_ANTI_BOT', True)
    
    if headless is None:
        headless = getattr(C, 'PLAYWRIGHT_HEADLESS', False)
    
    if slow_mo is None:
        slow_mo = getattr(C, 'PLAYWRIGHT_SLOW_MO', 0)
    
    # 啟動 Playwright
    playwright = sync_playwright().start()
    
    # 選擇瀏覽器引擎
    browser_type = getattr(C, 'PLAYWRIGHT_BROWSER', 'chromium').lower()
    
    if browser_type == 'firefox':
        browser_engine = playwright.firefox
    elif browser_type == 'webkit':
        browser_engine = playwright.webkit
    else:
        browser_engine = playwright.chromium
    
    # 準備啟動參數
    launch_options: Dict[str, Any] = {
        'headless': headless,
        'slow_mo': slow_mo,
    }
    
    # Chromium 特定參數（反爬蟲增強）
    if browser_type == 'chromium':
        launch_options['args'] = [
            '--disable-blink-features=AutomationControlled',  # 移除自動化標記
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-gpu',
        ]
    
    # 啟動瀏覽器
    browser = browser_engine.launch(**launch_options)
    
    return playwright, browser


def create_browser_context(
    browser: Browser,
    enable_anti_bot: Optional[bool] = None
) -> BrowserContext:
    """
    創建 BrowserContext（瀏覽器上下文）
    
    BrowserContext 是 Playwright 的核心概念：
    - 類似於 Selenium 的 Incognito 模式
    - 每個 Context 擁有獨立的 Cookies、Storage、Cache
    - 適合並行執行多個測試（隔離性）
    
    反封號機制：
    1. User-Agent 隨機化
    2. 視窗大小隨機擾動（±5-10 像素）
    3. Accept-Language 隨機化
    4. Device Scale Factor 設定
    5. 忽略 HTTPS 錯誤
    
    Args:
        browser (Browser): Playwright Browser 實例
        enable_anti_bot (bool, optional): 是否啟用反封號機制
    
    Returns:
        BrowserContext: 瀏覽器上下文實例
    
    Note:
        - Context 需手動關閉（調用 context.close()）
        - 每個 Context 可以創建多個 Page
        - Context 關閉時，其下所有 Page 也會關閉
    
    Example:
        >>> context = create_browser_context(browser)
        >>> page = context.new_page()
        >>> page.goto("https://example.com")
        >>> context.close()
    """
    # 從 config 讀取配置
    if enable_anti_bot is None:
        enable_anti_bot = getattr(C, 'ENABLE_ANTI_BOT', True)
    
    # 準備 Context 參數
    context_options: Dict[str, Any] = {}
    
    if enable_anti_bot:
        # 1. User-Agent 隨機化
        # Playwright 優勢：直接在 Context 層級設定，比 Selenium 更簡潔
        if getattr(C, 'ENABLE_RANDOM_USER_AGENT', True):
            user_agent_pool = getattr(C, 'USER_AGENT_POOL', [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ])
            context_options['user_agent'] = random.choice(user_agent_pool)
        
        # 2. 視窗大小隨機擾動
        # Playwright 優勢：使用 viewport 而非 window size，更精確
        if getattr(C, 'ENABLE_RANDOM_VIEWPORT', True):
            viewport_pool = getattr(C, 'VIEWPORT_SIZE_POOL', [(1920, 1080)])
            base_width, base_height = random.choice(viewport_pool)
            
            # 隨機擾動（±5-10 像素）
            jitter = getattr(C, 'PLAYWRIGHT_VIEWPORT_JITTER', 10)
            width = base_width + random.randint(-jitter, jitter)
            height = base_height + random.randint(-jitter, jitter)
            
            context_options['viewport'] = {'width': width, 'height': height}
        
        # 3. Accept-Language 隨機化
        accept_language_pool = getattr(C, 'ACCEPT_LANGUAGE_POOL', None)
        if accept_language_pool:
            # Playwright 支援直接設定 locale
            accept_language = random.choice(accept_language_pool)
            context_options['locale'] = accept_language.split(',')[0].split(';')[0]
        
        # 4. Device Scale Factor（模擬不同 DPI 設備）
        device_scale_factor = getattr(C, 'PLAYWRIGHT_DEVICE_SCALE_FACTOR', 1.0)
        if 'viewport' in context_options:
            context_options['device_scale_factor'] = device_scale_factor
    
    # 5. 忽略 HTTPS 錯誤
    ignore_https_errors = getattr(C, 'PLAYWRIGHT_IGNORE_HTTPS_ERRORS', True)
    context_options['ignore_https_errors'] = ignore_https_errors
    
    # 創建 Context
    context = browser.new_context(**context_options)
    
    # 設定超時
    default_timeout = getattr(C, 'PLAYWRIGHT_DEFAULT_TIMEOUT', 30000)
    context.set_default_timeout(default_timeout)
    
    navigation_timeout = getattr(C, 'PLAYWRIGHT_NAVIGATION_TIMEOUT', 60000)
    context.set_default_navigation_timeout(navigation_timeout)
    
    return context


def take_screenshot(page: Page, name_prefix: str = "error") -> str:
    """
    截圖並保存到指定資料夾
    
    Playwright 優勢：
    - 支援完整頁面截圖（full_page=True）
    - 支援元素截圖（element.screenshot()）
    - 支援 PDF 導出（page.pdf()）
    
    Args:
        page (Page): Playwright Page 實例
        name_prefix (str): 檔案名稱前綴
    
    Returns:
        str: 截圖檔案路徑
    
    Example:
        >>> path = take_screenshot(page, "login_error")
        >>> print(f"截圖已保存: {path}")
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{timestamp}.png"
    
    screenshot_dir = getattr(C, 'SCREENSHOT_DIR', './screenshots')
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir, exist_ok=True)
    
    filepath = os.path.join(screenshot_dir, filename)
    
    # Playwright 截圖（預設為可見區域）
    page.screenshot(path=filepath)
    
    return filepath


def wait_for_page_load(page: Page, timeout: Optional[int] = None) -> None:
    """
    等待頁面載入完成
    
    Playwright 優勢：
    - 自動等待 DOM 載入（無需顯式等待）
    - 支援等待網路閒置（wait_until='networkidle'）
    - 支援等待特定事件（page.wait_for_event()）
    
    Args:
        page (Page): Playwright Page 實例
        timeout (int, optional): 超時時間（毫秒）
    
    Example:
        >>> page.goto("https://example.com")
        >>> wait_for_page_load(page)  # 等待頁面完全載入
    """
    if timeout is None:
        timeout = getattr(C, 'PLAYWRIGHT_NAVIGATION_TIMEOUT', 60000)
    
    # Playwright 的 goto 已內建等待機制
    # 此函數僅用於兼容性和明確性
    page.wait_for_load_state('networkidle', timeout=timeout)


def get_element_count(page: Page, selector: str) -> int:
    """
    取得符合選擇器的元素數量
    
    Playwright 優勢：
    - Locator API 更直觀（page.locator()）
    - 自動重試機制（元素出現前會自動等待）
    
    Args:
        page (Page): Playwright Page 實例
        selector (str): CSS 選擇器或其他 Playwright 支援的選擇器
    
    Returns:
        int: 元素數量
    
    Example:
        >>> count = get_element_count(page, ".product-card")
        >>> print(f"找到 {count} 個商品卡片")
    """
    locator = page.locator(selector)
    return locator.count()


def is_element_visible(page: Page, selector: str, timeout: int = 3000) -> bool:
    """
    檢查元素是否可見
    
    Playwright 優勢：
    - 自動等待機制（無需 try-except）
    - is_visible() 方法更直觀
    
    Args:
        page (Page): Playwright Page 實例
        selector (str): 選擇器
        timeout (int): 超時時間（毫秒）
    
    Returns:
        bool: 元素可見返回 True，否則返回 False
    
    Example:
        >>> if is_element_visible(page, "#error-message"):
        >>>     print("錯誤訊息出現")
    """
    try:
        locator = page.locator(selector)
        locator.wait_for(state='visible', timeout=timeout)
        return True
    except PlaywrightError:
        return False


def get_all_texts(page: Page, selector: str) -> list:
    """
    取得所有符合選擇器的元素文字
    
    Playwright 優勢：
    - all_text_contents() 方法一次取得所有文字
    - 無需迴圈處理
    
    Args:
        page (Page): Playwright Page 實例
        selector (str): 選擇器
    
    Returns:
        list: 文字內容列表
    
    Example:
        >>> texts = get_all_texts(page, ".menu-item")
        >>> print(f"選單項目: {texts}")
    """
    locator = page.locator(selector)
    return locator.all_text_contents()
