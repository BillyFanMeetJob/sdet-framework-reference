# toolkit/web_toolkit.py

import os
import time
from typing import Optional, List

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

def create_driver(timeout: Optional[int] = None) -> tuple[webdriver.Chrome, WebDriverWait]:
    if timeout is None:
        timeout = C.DEFAULT_TIMEOUT

    chrome_options = Options()

    # 乾淨 profile（避免讀到本機 Chrome 的登入/同步/密碼庫）
    profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")

    # 訪客模式
    chrome_options.add_argument("--guest")

    # 關閉密碼管理相關提示
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 🎯 檢查 HEADLESS 配置，如果不存在則默認為 False
    headless = getattr(C, 'HEADLESS', False)
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, timeout)
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





