# actions/inventory_actions.py
from base.browser import Browser
from base.base_action import BaseAction
from pages.inventory_page import InventoryPage

class InventoryActions(BaseAction):
    def __init__(self, browser: Browser):
        super().__init__()
        self.inventory_page = InventoryPage(browser)

    def inventory_has_items(self) -> None:
        """
        測試一：登入後，商品列表不應為空。
        驗證重點：
        - 商品卡片數量 > 0
        - 商品名稱清單長度與商品卡片數量一致
        """
        # Act
        item_count = self.inventory_page.get_item_count()
        item_names = self.inventory_page.get_all_item_names()

        self.logger.info(f"商品數量：{item_count}")
        self.logger.info(f"商品名稱列表：{item_names}")

        # Assert
        assert item_count > 0, "登入後商品數量應大於 0"
        assert len(item_names) == item_count, "商品名稱數量應與商品卡片數量一致"

        self.logger.info("✅ test_inventory_has_items 通過")


    def add_item_to_cart(self,index:int=0) -> None:
        """
        測試二：加入一個商品到購物車，徽章數量應為 1。

        說明：
        - logged_in_browser fixture 會為每個測試建立全新的瀏覽器與登入狀態（scope=function）
        - 因此本測試可以假設購物車一開始為空
        - 默認加入第一個商品
        """
        # Arrange
        # Act：加入商品
        index = int(index)
        self.inventory_page.add_item_to_cart_by_index(index)
        badge_count = self.inventory_page.get_cart_badge_count()

        self.logger.info(f"🛒 購物車徽章數量：{badge_count}")

        # Assert
        assert badge_count == 1, f"預期購物車徽章為 1，但實際為 {badge_count}"

        self.logger.info("✅ test_add_first_item_to_cart 通過")


