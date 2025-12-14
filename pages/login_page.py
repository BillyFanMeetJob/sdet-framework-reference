# pages/login_page.py
from selenium.webdriver.common.by import By
from toolkit.types import Locator
from base.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT: Locator = (By.ID, "user-name")
    PASSWORD_INPUT: Locator = (By.ID, "password")
    LOGIN_BUTTON:   Locator = (By.ID, "login-button")

    def open(self, base_url: str) -> "LoginPage":
        self.driver.get(base_url)
        return self

    def login(self, username: str, password: str) -> None:
        self.type(self.USERNAME_INPUT, username)
        self.type(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
