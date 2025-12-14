# actions/login_actions.py
from base.browser import Browser
from base.base_action import BaseAction
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage

class LoginActions(BaseAction):

    def __init__(self,browser:Browser):
        super().__init__()
        self.login_page = LoginPage(browser)
        self.inventory_page = InventoryPage(browser)

    def login_success(self):
        """
        驗證：使用正確帳密可以成功登入並進入商品列表頁。
        - 使用 LoginPage 封裝登入流程
        - 使用 BasePage.wait_for_url() 等待導頁穩定
        - 使用 InventoryPage 驗證頁面狀態
        """
        self.logger.info("開始登入流程")
        self.login_page.open(self.config.BASE_URL).login(username=self.config.USERNAME, password=self.config.PASSWORD)
        
        # 等待 URL 進入 inventory 頁（內部會封裝 WebDriverWait）
        assert self.login_page.wait_for_url("inventory.html", partial=True), "登入後未導向商品列表頁"
        # 使用 InventoryPage 做進一步驗證（例如：商品數量 > 0）
        item_count = self.inventory_page.get_item_count()
        self.logger.info(f"登入成功，商品數量：{item_count}")
        assert item_count > 0, "登入後商品列表應該至少有一項商品"
    

    def login_fail(self):
        pass