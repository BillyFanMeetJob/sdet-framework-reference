# tests/test_execution.py
from engine.flow_runner import run_test_flow


def test_execution(browser):

    run_test_flow("正常購物流程",browser)



