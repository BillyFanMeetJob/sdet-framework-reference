# -*- coding: utf-8 -*-
"""
Web Toolkit - WebDriver 工具函數集

提供 WebDriver 的創建、配置和基礎操作工具函數。
實作反封號機制：
- User-Agent 隨機化
- 瀏覽器指紋隱藏
- 視窗大小隨機化

Author: SDET Team
Date: 2026-01-27
"""

import os
import time
import random
from typing import Optional, List, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement
from toolkit.types import Locator
import tempfile

import config as C  


def create_driver(
    timeout: Optional[int] = None,
    enable_anti_bot: Optional[bool] = None
) -> Tuple[webdriver.Chrome, WebDriverWait]:
    """
    創建 Chrome WebDriver 實例（內建反封號機制）
    
    實作完整的反偵測策略：
    1. User-Agent 隨機化（從 config 的 USER_AGENT_POOL 隨機選擇）
    2. 移除 Selenium 自動化標記（--disable-blink-features=AutomationControlled）
    3. 隨機化視窗大小（從 VIEWPORT_SIZE_POOL 隨機選擇）
    4. 隨機化 Accept-Language Header
    5. 清理自動化痕跡（excludeSwitches、useAutomationExtension）
    
    Args:
        timeout (int, optional): WebDriverWait 超時時間（秒），預設從 config 讀取或使用 10 秒
        enable_anti_bot (bool, optional): 是否啟用反封號機制，None 時從 config 讀取
    
    Returns:
        Tuple[webdriver.Chrome, WebDriverWait]: (driver, wait) 元組
    
    Raises:
        不會拋出異常，失敗時會使用預設配置
    
    Note:
        - 反封號機制的有效性取決於目標網站的檢測強度
        - User-Agent 池應定期更新以匹配最新瀏覽器版本
        - 臨時 Profile 會在 Browser.quit() 時自動清理
    
    Example:
        >>> # 使用預設配置（啟用反封號）
        >>> driver, wait = create_driver()
        >>> 
        >>> # 禁用反封號機制（測試環境）
        >>> driver, wait = create_driver(enable_anti_bot=False)
    """
    if timeout is None:
        # 如果 config 中有 DEFAULT_TIMEOUT，使用它；否則使用默認值 10 秒
        timeout = getattr(C, 'DEFAULT_TIMEOUT', 10)
    
    # 從 config 讀取反封號配置
    if enable_anti_bot is None:
        enable_anti_bot = getattr(C, 'ENABLE_ANTI_BOT', True)

    chrome_options = Options()

    # ==================== 反封號機制配置 ====================
    
    if enable_anti_bot:
        # 1. User-Agent 隨機化
        # 降低被偵測風險的關鍵：每次啟動使用不同的瀏覽器特徵
        # - 網站會記錄 User-Agent 來追蹤自動化行為
        # - 隨機化可避免被識別為固定的機器人
        # - 使用真實瀏覽器的 User-Agent 提高偽裝效果
        if getattr(C, 'ENABLE_RANDOM_USER_AGENT', True):
            user_agent_pool = getattr(C, 'USER_AGENT_POOL', [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ])
            user_agent = random.choice(user_agent_pool)
            chrome_options.add_argument(f'user-agent={user_agent}')
        
        # 2. 移除 Selenium 自動化標記
        # 降低被偵測風險的核心：
        # - Selenium 會在 navigator.webdriver 屬性中暴露自動化標記
        # - 網站可通過 JavaScript 檢測此屬性來識別自動化
        # - 此選項會移除該標記，使網站無法輕易識別
        if getattr(C, 'DISABLE_AUTOMATION_CONTROLLED', True):
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 3. 排除自動化擴展和開關
        # 進一步清理自動化痕跡：
        # - 'enable-automation' 開關會在 DevTools 協議中暴露自動化標記
        # - 'useAutomationExtension' 會載入額外的自動化擴展
        # - 移除這些可降低被高級反爬蟲檢測的機率
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 4. Accept-Language 隨機化
        # 模擬不同地區的使用者：
        # - 網站可能根據 Accept-Language 調整內容
        # - 隨機化可避免固定的語言偏好被追蹤
        if getattr(C, 'ACCEPT_LANGUAGE_POOL', None):
            accept_language = random.choice(C.ACCEPT_LANGUAGE_POOL)
            chrome_options.add_argument(f'--lang={accept_language.split(",")[0]}')
            prefs = chrome_options.experimental_options.get("prefs", {})
            prefs["intl.accept_languages"] = accept_language
            chrome_options.add_experimental_option("prefs", prefs)
    
    # ==================== 標準配置 ====================
    
    # 🎯 關鍵：解決 "Could not reach host"
    chrome_options.add_argument('--dns-prefetch-disable')          # 禁用預解析，防止卡死
    chrome_options.add_argument('--no-proxy-server')               # 絕對必要：跳過熱點可能提供的 Proxy
    chrome_options.add_argument('--proxy-server=direct://')        # 強制直連
    chrome_options.add_argument('--proxy-bypass-list=*')          # 繞過所有代理
    
    # 🎯 穩定連線
    chrome_options.add_argument('--ignore-certificate-errors')    # 忽略憑證錯誤
    
    # 效能優化
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 如果不需要看圖，這能加快網頁載入

    # 繞過沙盒模式（避免權限問題）
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 乾淨 profile（避免讀到本機 Chrome 的登入/同步/密碼庫）
    profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")

    # 訪客模式
    chrome_options.add_argument("--guest")
    
    # 🎯 保持瀏覽器打開：使用 remote-debugging-port 讓瀏覽器在 driver 關閉後仍然保持打開
    # 這樣即使 Python 進程退出，瀏覽器也會保持打開狀態
    # 使用固定的 port 9223，方便後續重新連接
    debug_port = 9223
    chrome_options.add_argument(f"--remote-debugging-port={debug_port}")
    chrome_options.add_experimental_option("detach", True)  # 嘗試使用 detach 選項

    # 關閉密碼管理相關提示
    prefs = chrome_options.experimental_options.get("prefs", {})
    prefs.update({
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    })
    chrome_options.add_experimental_option("prefs", prefs)

    # 🎯 檢查 HEADLESS 配置，如果不存在則默認為 False
    headless = getattr(C, 'HEADLESS', False)
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # ==================== 反封號：隨機視窗大小 ====================
    
    if enable_anti_bot and getattr(C, 'ENABLE_RANDOM_VIEWPORT', True):
        # 隨機化視窗大小
        # 降低被偵測風險：
        # - 固定的視窗大小容易被識別為自動化腳本
        # - 真實使用者的視窗大小會因螢幕解析度和個人偏好而不同
        # - 隨機化可模擬不同使用者的設備環境
        viewport_pool = getattr(C, 'VIEWPORT_SIZE_POOL', [(1920, 1080)])
        viewport_width, viewport_height = random.choice(viewport_pool)
        chrome_options.add_argument(f"--window-size={viewport_width},{viewport_height}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, timeout)
    
    # ==================== 反封號：JavaScript 注入 ====================
    
    if enable_anti_bot:
        # 覆寫 navigator.webdriver 屬性
        # 即使使用了 --disable-blink-features=AutomationControlled，
        # 部分網站仍可能檢測到此屬性，透過 JavaScript 注入進一步隱藏
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })
        except Exception:
            # CDP 命令失敗不影響主流程（舊版 ChromeDriver 可能不支援）
            pass
    
    return driver, wait


def take_screenshot(driver, name_prefix: str = "error") -> str:
    """
    依照目前環境將 screenshot 存到指定資料夾，回傳實際路徑。
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{timestamp}.png"
    filepath = os.path.join(C.SCREENSHOT_DIR, filename)

    driver.save_screenshot(filepath)
    return filepath


def type_text(wait: WebDriverWait, locator: Locator, text: str, clear: bool = True):
    """
    通用輸入文字動作：
    - 等待元素可見
    - 選擇性清空
    - send_keys
    """
    elem = wait.until(EC.visibility_of_element_located(locator))
    if clear:
        elem.clear()
    elem.send_keys(text)
    return elem


def click_when_clickable(wait: WebDriverWait, locator: Locator):
    """
    通用點擊動作：
    - 等待元素可被點擊
    - click
    """
    elem = wait.until(EC.element_to_be_clickable(locator))
    elem.click()
    return elem


def get_text_when_visible(wait: WebDriverWait, locator: Locator) -> str:
    """
    等到元素可見後回傳文字。
    """
    elem = wait.until(EC.visibility_of_element_located(locator))
    return elem.text


def is_element_visible(wait: WebDriverWait, locator: Locator) -> bool:
    """
    檢查元素是否在畫面上可見。
    不會拋出例外，而是回傳 True/False。
    """
    try:
        wait.until(EC.visibility_of_element_located(locator))
        return True
    except TimeoutException:
        return False


def wait_for_url(driver, expected: str, timeout: int = 10, partial: bool = True) -> bool:
    """
    等待 URL 變成指定內容（可設定部分比對）。
    partial = True 代表 URL 包含 expected 就算成功。
    """
    if partial:
        condition = EC.url_contains(expected)
    else:
        condition = EC.url_to_be(expected)

    try:
        WebDriverWait(driver, timeout).until(condition)
        return True
    except TimeoutException:
        return False


def find_all_visible_elements(wait: WebDriverWait, locator: Locator) -> List[WebElement]:
    """
    等待並回傳所有可見元素（List[WebElement]）。
    """
    return wait.until(EC.visibility_of_all_elements_located(locator))


def find_visible_element(wait: WebDriverWait, locator: Locator)->WebElement:
    """
    等待並回傳單一可見元素。
    """
    return wait.until(EC.visibility_of_element_located(locator))


def find_any_visible_elements(wait: WebDriverWait, locator: Locator) -> List[WebElement]:
    """
    只要有任一元素變為可見，就回傳當前可見元素集合。
    """
    return wait.until(EC.visibility_of_any_elements_located(locator))


def find_child_element(parent_elem, locator: Locator) -> WebElement:
    """
    在指定父元素底下尋找子元素。
    """
    return parent_elem.find_element(*locator)


def get_all_item_texts(wait: WebDriverWait, items_locator: Locator, text_locator: Optional[Locator] = None) -> list[str]:
    """
    取得一組元素（例如列表列、卡片）的文字清單。
    - items_locator: 外層列表元素的 locator
    - text_locator: 若指定，則在每個 item 內再找子元素取 text
    """
    items = find_all_visible_elements(wait, items_locator)

    texts: list[str] = []
    for item in items:
        if text_locator:
            elem = item.find_element(*text_locator)
            texts.append(elem.text.strip())
        else:
            texts.append(item.text.strip())
    return texts


def count_visible_elements(wait: WebDriverWait, locator: Locator) -> int:
    """
    取得可見元素數量。
    """
    elements = find_all_visible_elements(wait, locator)
    return len(elements)





