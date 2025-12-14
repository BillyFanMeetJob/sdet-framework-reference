# run_demo.py
from base.browser import Browser
from engine.flow_runner import run_test_flow
from toolkit.datatable import DataTable

if __name__ == "__main__":
    b = Browser()
    try:
        run_test_flow("正常購物流程", b)
    finally:
        b.quit()
