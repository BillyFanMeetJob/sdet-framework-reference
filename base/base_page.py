# base/base_page.py 
from __future__ import annotations
from typing import TYPE_CHECKING, List
import toolkit.web_toolkit as tool
from toolkit.types import Locator
from selenium.webdriver.remote.webelement import WebElement


if TYPE_CHECKING:
    from base.browser import Browser  # 避免循環 import 問題


class BasePage:
    """
    所有 Page Object 的基底類別。
    封裝：
    - browser / driver / wait
    - 常用 Selenium 動作（click/type/get_text/...）
    """

    def __init__(self, browser: "Browser"):
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait

    # === 基本操作封裝 ===

    def type(self, locator: Locator, text: str, clear: bool = True):
        """
        在指定 locator 上輸入文字，預設會先清空。
        """
        return tool.type_text(self.wait, locator, text, clear=clear)

    def click(self, locator: Locator):
        """
        等待元素可點擊後執行 click。
        """
        return tool.click_when_clickable(self.wait, locator)

    def get_text(self, locator: Locator) -> str:
        """
        等待元素可見後回傳文字。
        """
        return tool.get_text_when_visible(self.wait, locator)

    def is_visible(self, locator: Locator) -> bool:
        """
        檢查元素是否可見，不拋例外，回傳 True/False。
        """
        return tool.is_element_visible(self.wait, locator)

    def wait_for_url(self, expected: str, timeout: int = 10, partial: bool = True) -> bool:
        """
        等待 URL 符合預期（部分比對或完整比對）。
        """
        return tool.wait_for_url(self.driver, expected, timeout=timeout, partial=partial)
    
    def find_all(self, locator: Locator) -> List[WebElement]:
        """
        等待並回傳所有可見元素（List[WebElement]）。
        """
        return tool.find_all_visible_elements(self.wait, locator)

    def get_all_texts(self, items_locator:Locator, text_locator=None) -> List[str]:
        """
        取得一組元素（例如列表列、卡片）的文字清單。
        - items_locator: 外層列表元素的 locator
        - text_locator: 若指定，則在每個 item 內再找子元素取 text
        """
        return tool.get_all_item_texts(self.wait, items_locator, text_locator)

    def elements_count(self,locator: Locator) -> int:
        """
        取得可見元素數量。
        """
        return tool.count_visible_elements(self.wait, locator)
    
    def find_element(self,parent_elem,locator: Locator) -> WebElement:
        """
        在指定父元素底下尋找子元素。
        """
        return tool.find_child_element(parent_elem, locator)