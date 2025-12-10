from pages.login_page import LoginPage
from toolkit.logger import get_logger
import config
C = config.ACTIVE_CONFIG

logger = get_logger(__name__)

def test_login_success(browser):
    """
    驗證使用正確帳密可以成功登入。
    browser 參數由 pytest 的 browser fixture 自動注入。
    """
    logger.info("開始登入流程")

    login_page = LoginPage(browser)
    login_page.open(C.BASE_URL)
    login_page.login(
        username=C.USERNAME,
        password=C.PASSWORD,
    )

    current_url = browser.driver.current_url
    assert "inventory.html" in current_url
