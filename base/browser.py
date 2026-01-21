import os
import shutil
from toolkit.web_toolkit import create_driver, type_text, click_when_clickable, get_text_when_visible
from toolkit.types import Locator

class Browser:
    def __init__(self):
        # create_driver 內部產生的 profile_dir 會被儲存
        self.driver, self.wait = create_driver()
        self._profile_path = self.driver.capabilities.get("chrome", {}).get("userDataDir")

    def open(self, url: str):
        self.driver.get(url)

    def type(self, locator: Locator, text: str):
        return type_text(self.wait, locator, text)

    def click(self, locator: Locator):
        return click_when_clickable(self.wait, locator)

    def quit(self):
        self.driver.quit()
        # 優化點：自動清理暫存的 Chrome Profile
        if self._profile_path and os.path.exists(self._profile_path):
            try:
                shutil.rmtree(self._profile_path, ignore_errors=True)
            except:
                pass