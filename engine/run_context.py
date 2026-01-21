# 相對路徑: engine/run_context.py

import sys
import os

# 確保路徑能正確找到根目錄
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 修正引用：config 和 toolkit 在根目錄與其子目錄
from config import get_current_config as get_config
from toolkit.datatable import shared_dt

class RunContext:
    def __init__(self, browser=None):
        # 解決 image_7c5990.png 中的引用波浪線
        self.config = get_config()
        self.browser = browser
        self.dt = shared_dt
        self.logger_name = "RunContext"

# 保留此定義以維護舊架構兼容性