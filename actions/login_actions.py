# 相對路徑: actions/login_actions.py
from base.base_action import BaseAction # 🎯 從 base 層引用
from pages.desktop.desktop_login_page import DesktopLoginPage
from pages.desktop.main_page import MainPage

class LoginActions(BaseAction):
    def __init__(self, browser=None):
        super().__init__(browser)
        self.login_page = DesktopLoginPage()
        self.main_page = MainPage()

    def run_server_login_step(self, **kwargs):
        """ Case 1-1 強制登錄 """
        self.logger.info("🎬 執行 Case 1-1 登錄流程")
        self.login_page.launch_app(self.config.NX_EXE_PATH)
        # 點擊伺服器，超時設為 10s 應對軟體啟動慢的問題
        success = self.login_page.smart_click(0.5, 0.6, image_path="desktop_login/server_tile.png", timeout=10)
        if success:
            self.main_page.smart_click(0.05, 0.1, image_path="desktop_main/resource_tree_root.png", timeout=5)
        return self

    def run_ensure_login_step(self, **kwargs):
        """ Case 1-2 智能檢查 """
        self.logger.info("🎬 執行 Case 1-2 狀態檢查")
        if not self.login_page.get_nx_window():
            self.login_page.launch_app(self.config.NX_EXE_PATH)
        # 判定
        if self.login_page.smart_click(0.5, 0.6, image_path="desktop_login/login_indicator.png", timeout=3):
            self.main_page.smart_click(0.05, 0.1, image_path="desktop_main/resource_tree_root.png", timeout=5)
        return self