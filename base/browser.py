# base/browser.py
from toolkit.web_toolkit import create_driver

class Browser:
    def __init__(self):
        self.driver, self.wait = create_driver()

    def quit(self):
        self.driver.quit()
