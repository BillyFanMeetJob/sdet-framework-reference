# 相對路徑: actions/settings_actions.py
from base.base_action import BaseAction
from pages.desktop.main_page import MainPage
from pages.desktop.settings_page import SettingsPage

class SettingsActions(BaseAction):
    def __init__(self, browser=None):
        super().__init__(browser)
        self.main_page = MainPage()
        self.settings_page = SettingsPage()

    def run_change_language_step(self, **kwargs):
        """ Case 1-1 語系切換：從開啟選單開始 """
        self.logger.info("⚙️ 執行語系切換步驟")
        
        # 🎯 使用正確的圖片：menu_icon.png
        # 這裡會呼叫 main_page.open_main_menu()，內容即為點擊 menu_icon.png
        self.main_page.open_main_menu()
        
        # 後續流程...
        self.main_page.select_local_settings()
        self.settings_page.switch_to_appearance_tab()
        self.settings_page.change_language(language=kwargs.get("language", "繁體中文"))
        return self