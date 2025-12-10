from pages.inventory_page import InventoryPage
from toolkit.logger import get_logger

logger = get_logger(__name__)


def test_inventory_has_items(logged_in_browser):
    """
    測試一：登入後，商品列表不應為空
    """
    inv_page = InventoryPage(logged_in_browser)

    count = inv_page.get_item_count()
    names = inv_page.get_all_item_names()

    logger.info(f"⚾商品數量：{count}")
    logger.info(f"📋商品名稱列表：{names}")

    assert count > 0, "登入後商品數量應大於 0"
    assert len(names) == count, "商品名稱數量應與商品卡片數量一致"

    logger.info("✅ test_inventory_has_items 通過")

def test_add_first_item_to_cart(logged_in_browser):
    """
    測試二：加入第一個商品到購物車，徽章數量應為 1
    """
    inv_page = InventoryPage(logged_in_browser)

    # 加入第一個商品（index = 0）
    inv_page.add_item_to_cart_by_index(0)
    badge = inv_page.get_cart_badge_count()
    logger.info(f"🛒購物車徽章數量：{badge}")

    assert badge == 1, f"🛒預期購物車徽章為 1，但實際為 {badge}"

    logger.info("✅ test_add_first_item_to_cart 通過")
