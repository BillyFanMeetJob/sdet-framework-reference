# tests/conftest.py
from collections.abc import Generator

import pytest

from toolkit.logger import get_logger
from toolkit.web_toolkit import take_screenshot
from toolkit.datatable import DataTable
from base.browser import Browser

logger = get_logger(__name__)

@pytest.fixture(scope="function")
def browser() -> Generator[Browser, None, None]:
    """
    建立並管理一個 Browser 實體：
    - 測試開始前建立 Browser（內含 driver / wait）
    - 測試結束後自動呼叫 browser.quit() 關閉瀏覽器
    """
    browser = Browser()
    logger.info("建立 Browser 實體")
    try:
        yield browser
    finally:
        logger.info("關閉 Browser")
        # Browser 類別應該要統一提供 quit() 介面
        browser.quit()


# 單元測試用
@pytest.fixture(scope="function")
def datatable():
    return DataTable()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    若測試失敗且有 browser / logged_in_browser fixture，
    自動呼叫 take_screenshot()，將畫面截圖存檔。

    這個 hook 會在每個測試的 setup/call/teardown 階段後被呼叫，
    我們只在「call 階段且失敗」時處理截圖。
    """
    outcome = yield
    rep = outcome.get_result()

    # 只在測試主體階段（call）且失敗時處理
    if rep.when == "call" and rep.failed:
        # 嘗試從測試參數中拿 browser 或 logged_in_browser fixture
        browser = item.funcargs.get("logged_in_browser") or item.funcargs.get("browser")

        if browser and getattr(browser, "driver", None):
            logger.error(f"測試失敗，自動截圖：{item.name}")
            take_screenshot(browser.driver, name_prefix=f"FAIL_{item.name}")
