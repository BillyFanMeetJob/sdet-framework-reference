# pages/inventory_page.py
from selenium.webdriver.common.by import By
from base.basepage import BasePage


class InventoryPage(BasePage):
    """
    SauceDemo 登入後的商品列表頁面
    """

    # 商品卡片外層
    ITEM_CARD = (By.CSS_SELECTOR, ".inventory_item")
    # 商品名稱
    ITEM_NAME = (By.CSS_SELECTOR, ".inventory_item_name")
    # 商品價格
    ITEM_PRICE = (By.CSS_SELECTOR, ".inventory_item_price")
    # 加入購物車按鈕
    ITEM_ADD_BUTTON = (By.CSS_SELECTOR, "button.btn_inventory")
    # 購物車右上角徽章
    CART_BADGE = (By.CSS_SELECTOR, ".shopping_cart_badge")

    def get_all_item_names(self):
        """
        回傳目前頁面上所有商品名稱（list[str]）
        """
        names = []
        cards = self.driver.find_elements(*self.ITEM_CARD)
        for card in cards:
            name = card.find_element(*self.ITEM_NAME)
            names.append(name.text.strip())
        return names
       

    def get_item_count(self):
        """
        回傳商品卡片數量
        """
        return len(self.driver.find_elements(*self.ITEM_CARD))
        

    def add_item_to_cart_by_index(self, index: int):
        """
        依照索引（從 0 開始）點擊該商品的「加入購物車」按鈕
        """
        cards = self.driver.find_elements(*self.ITEM_CARD)
        if index<0 or index>=len(cards):
            raise f"索引 {index} 超出範圍，商品數量為 {len(cards)}"
        card = cards[index]
        btn = card.find_element(*self.ITEM_ADD_BUTTON)
        btn.click()
        

    def get_cart_badge_count(self) -> int:
        """
        讀取右上角購物車徽章數字，沒顯示時回傳 0
        """
        badge=self.driver.find_elements(*self.CART_BADGE)
        if not badge:
            return 0
        text = badge[0].text.strip()
        return int(text) if text.isdigit() else 0
        
