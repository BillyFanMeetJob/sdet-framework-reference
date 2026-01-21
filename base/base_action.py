# base/base_action.py 
from toolkit.logger import get_logger
from engine.runtime import get_config, get_datatable

class BaseAction:
    def __init__(self, browser=None):
        self.logger = get_logger(self.__class__.__name__)
        self.browser = browser
        # 透過 runtime 統一獲取 config 和位於 toolkit 的 datatable
        self.config = get_config()
        self.dt = get_datatable()