# tests/test_execution.py
import os
import pytest

from engine.flow_runner import run_test_flow


def _parse_test_names() -> list[str]:
    """
    CI 透過環境變數傳入執行順序：
        TEST_NAMES="正常購物流程,流程B,流程C"
    若未提供，使用預設值（本地也能跑）。
    """
    raw = os.environ.get("TEST_NAMES", "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]


    # 本地預設（可自行維護）
    return ["正常購物流程"]


@pytest.mark.parametrize("test_name", _parse_test_names())
def test_execution(browser, test_name: str):
    """
    測試入口不綁死案例名稱，由 CI 以 TEST_NAMES 控制順序與清單。
    """
    run_test_flow(test_name, browser)
