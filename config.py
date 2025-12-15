# config.py
"""
多環境設定檔，類似 UFT 的 Environment + 多組環境 XML。
支援 DEV / SIT / UAT / PROD 切換。

用法：
    from config import ACTIVE_CONFIG as C
    driver.get(C.BASE_URL)
"""

import os
from dataclasses import dataclass

# === 通用設定（所有環境共用） ===
DEFAULT_TIMEOUT = 10
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"#本機跑有畫面，接CI無畫面


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_ROOT = os.path.join(ROOT_DIR, "screenshots")


@dataclass(frozen=True)
class EnvConfig:
    """單一環境的設定結構"""
    NAME: str
    BASE_URL: str
    USERNAME: str
    PASSWORD: str
    TESTPLANPATH: str
    


# === 各環境個別設定 ===
DEV_CONFIG = EnvConfig(
    NAME="DEV",
    BASE_URL="https://www.saucedemo.com/",  # 這裡先都用同一個，之後你有真的 DEV/UAT 再改
    USERNAME="standard_user",
    PASSWORD="secret_sauce",
    TESTPLANPATH= os.path.join(ROOT_DIR, "DemoData", "TestPlan.xlsx"),
)

SIT_CONFIG = EnvConfig(
    NAME="SIT",
    BASE_URL="https://www.saucedemo.com/",
    USERNAME="standard_user",
    PASSWORD="secret_sauce",
    TESTPLANPATH= os.path.join(ROOT_DIR, "DemoData", "TestPlan.xlsx"),
)

UAT_CONFIG = EnvConfig(
    NAME="UAT",
    BASE_URL="https://www.saucedemo.com/",
    USERNAME="standard_user",
    PASSWORD="secret_sauce",
    TESTPLANPATH= os.path.join(ROOT_DIR, "DemoData", "TestPlan.xlsx"),
)

PROD_CONFIG = EnvConfig(
    NAME="PROD",
    BASE_URL="https://www.saucedemo.com/",
    USERNAME="standard_user",
    PASSWORD="secret_sauce",
    TESTPLANPATH= os.path.join(ROOT_DIR, "DemoData", "TestPlan.xlsx"),
)


# 全部環境集中在一個 map 裡，方便依 key 取得
ENVIRONMENTS = {
    "DEV": DEV_CONFIG,
    "SIT": SIT_CONFIG,
    "UAT": UAT_CONFIG,
    "PROD": PROD_CONFIG,
}


# === 選擇目前啟用的環境 ===
# 優先順序：
#   1. 系統環境變數 TEST_ENV
#   2. 預設使用 "DEV"
ACTIVE_ENV_NAME = os.environ.get("TEST_ENV", "DEV").upper()

if ACTIVE_ENV_NAME not in ENVIRONMENTS:
    raise ValueError(f"Unknown TEST_ENV: {ACTIVE_ENV_NAME!r}, "
                     f"expected one of {list(ENVIRONMENTS.keys())}")

ACTIVE_CONFIG: EnvConfig = ENVIRONMENTS[ACTIVE_ENV_NAME]


# === 依環境建立對應的 screenshot 目錄 ===
SCREENSHOT_DIR = os.path.join(SCREENSHOT_ROOT, ACTIVE_CONFIG.NAME)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
