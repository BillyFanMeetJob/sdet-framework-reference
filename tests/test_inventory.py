# tests/test_inventory.py
from base.browser import Browser
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from toolkit.logger import get_logger
import config

logger = get_logger(__name__)


def login_and_go_to_inventory() -> tuple[Browser, InventoryPage]:
    """
    共用流程：
    1. 建立 Browser
    2. 登入
    3. 回傳 (browser, inventory_page)
    """
    C = config.ACTIVE_CONFIG
    browser = Browser()
    login_page = LoginPage(browser)

    logger.info("🔑 開始登入流程")
    login_page.open(C.BASE_URL)
    login_page.login(C.USERNAME, C.PASSWORD)

    # 到這裡應該已經在 inventory 頁面
    inv_page = InventoryPage(browser)
    return browser, inv_page


def test_inventory_has_items():
    """
    測試一：登入後，商品列表不應為空
    """
    browser, inv_page = login_and_go_to_inventory()
    try:
        count = inv_page.get_item_count()
        names = inv_page.get_all_item_names()

        logger.info(f"⚾商品數量：{count}")
        logger.info(f"📋商品名稱列表：{names}")

        assert count > 0, "登入後商品數量應大於 0"
        assert len(names) == count, "商品名稱數量應與商品卡片數量一致"

        logger.info("✅ test_inventory_has_items 通過")

    finally:
        logger.info("關閉瀏覽器")
        browser.driver.quit()


def test_add_first_item_to_cart():
    """
    測試二：加入第一個商品到購物車，徽章數量應為 1
    """
    browser, inv_page = login_and_go_to_inventory()
    try:
        # 加入第一個商品（index = 0）
        inv_page.add_item_to_cart_by_index(0)
        badge = inv_page.get_cart_badge_count()
        logger.info(f"🛒購物車徽章數量：{badge}")

        assert badge == 1, f"🛒預期購物車徽章為 1，但實際為 {badge}"

        logger.info("✅ test_add_first_item_to_cart 通過")

    finally:
        logger.info("關閉瀏覽器")
        browser.driver.quit()


if __name__ == "__main__":
    # 方便你直接用 python -m 跑單檔
    test_inventory_has_items()
    test_add_first_item_to_cart()
