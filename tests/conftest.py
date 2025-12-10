import pytest
from toolkit.logger import get_logger
from toolkit.web_toolkit import take_screenshot
from base.browser import Browser
from pages.login_page import LoginPage
import config
logger = get_logger(__name__)
C = config.ACTIVE_CONFIG

@pytest.fixture
def browser():
    b=Browser()
    logger.info("🟢 建立 Browser 實體")
    try:
        yield b
    finally:
        logger.info("🔴 關閉 Browser")
        if hasattr(b,"quit"):
            b.quit()
        else:
            b.driver.quit()


@pytest.fixture
def logged_in_browser(browser):
    login_page = LoginPage(browser)
    login_page.open(C.BASE_URL)
    login_page.login(
        username=C.USERNAME,
        password=C.PASSWORD
        )
    logger.info("✅ logged_in_browser fixture")
    return browser


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    若測試失敗且有 browser / logged_in_browser fixture
    自動呼叫 take_screenshot()。
    """
    outcome = yield
    rep = outcome.get_result()

    # 只在測試主體階段（call）且失敗時處理
    if rep.when == "call" and rep.failed:
        # 嘗試從測試參數中拿 browser 或 logged_in_browser
        b = item.funcargs.get("logged_in_browser") or item.funcargs.get("browser")
        if b and getattr(b, "driver", None):
            logger.error(f"❌ 測試失敗，自動截圖：{item.name}")
            take_screenshot(b.driver, name_prefix=f"FAIL_{item.name}")
