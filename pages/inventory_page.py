# pages/inventory_page.py
from selenium.webdriver.common.by import By

from base.base_page import BasePage
from toolkit.types import Locator


class InventoryPage(BasePage):
    """
    SauceDemo 登入後的商品列表頁面。
    封裝：
    - 商品列表資訊
    - 加入購物車操作
    - 購物車徽章讀取
    """

    # 商品卡片外層
    ITEM_CARD: Locator = (By.CSS_SELECTOR, ".inventory_item")
    # 商品名稱
    ITEM_NAME: Locator = (By.CSS_SELECTOR, ".inventory_item_name")
    # 商品價格
    ITEM_PRICE: Locator = (By.CSS_SELECTOR, ".inventory_item_price")
    # 加入購物車按鈕
    ITEM_ADD_BUTTON: Locator = (By.CSS_SELECTOR, "button.btn_inventory")
    # 購物車右上角徽章
    CART_BADGE: Locator = (By.CSS_SELECTOR, ".shopping_cart_badge")

    def get_all_item_names(self) -> list[str]:
        """
        回傳目前頁面上所有商品名稱（list[str]）。
        """
        return self.get_all_texts(
            items_locator=self.ITEM_CARD,
            text_locator=self.ITEM_NAME,
        )

    def get_item_count(self) -> int:
        """
        回傳商品卡片數量。
        """
        return self.elements_count(self.ITEM_CARD)

    def add_item_to_cart_by_index(self, index: int) -> None:
        """
        依照索引（從 0 開始）點擊該商品的「加入購物車」按鈕。
        """
        cards = self.find_all(self.ITEM_CARD)
        total = len(cards)

        if index < 0 or index >= total:
            raise IndexError(f"索引 {index} 超出範圍，商品數量為 {total}")

        card = cards[index]
        add_button = self.find_element(card,self.ITEM_ADD_BUTTON)
        add_button.click()

    def get_cart_badge_count(self) -> int:
        """
        讀取右上角購物車徽章數字，沒顯示時回傳 0。
        """
        badges_text = self.get_all_texts(items_locator=self.CART_BADGE)
        if not badges_text:
            return 0

        text = badges_text[0]
        try:
            return int(text)
        except ValueError:
            return 0
