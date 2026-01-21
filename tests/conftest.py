# 相對路徑: tests/conftest.py

import pytest
import sys
import os
from selenium import webdriver

# 確保能找到根目錄的 config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import EnvConfig

def pytest_addoption(parser):
    """ 
    🎯 註冊自定義參數 --test_name 
    讓 pytest -s --test_name "..." 不再報錯
    """
    parser.addoption("--test_name", action="store", default=None, help="指定要執行的 TestName")

@pytest.fixture(scope="session")
def browser_context():
    """
    Web 專用 Fixture：
    採按需啟動機制，只有被呼叫時才會開啟瀏覽器。
    """
    driver = None
    
    def _get_driver():
        nonlocal driver
        if driver is None:
            print("\n[系統] 偵測到 Web 測試需求，啟動瀏覽器...")
            # 根據 EnvConfig 決定設定
            options = webdriver.ChromeOptions()
            # 您可以在此處加入更多的 options 設定
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
        return driver

    yield _get_driver

    if driver:
        print("\n[系統] 關閉 Web 瀏覽器實體。")
        driver.quit()