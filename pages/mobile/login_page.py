# 相對路徑: pages/mobile/login_page.py
"""
Nx Witness 移動端登錄頁面

處理 Test Case 4-1: 登錄到 Nx Cloud
"""

from typing import Optional
from pages.mobile.base_mobile_page import BaseMobilePage
from config import EnvConfig


class LoginPage(BaseMobilePage):
    """
    Nx Witness 移動端登錄頁面
    
    職責：
    - 處理登錄相關操作（輸入郵箱、密碼、點擊登錄按鈕等）
    - 驗證登錄狀態
    """
    
    # Locators - 使用 Resource ID（優先）或文字定位
    # 注意：實際的 Resource ID 需要根據真實的 App 進行調整
    EMAIL_INPUT_ID = "com.networkoptix.nxwitness.mobile:id/email_input"  # 郵箱輸入框
    PASSWORD_INPUT_ID = "com.networkoptix.nxwitness.mobile:id/password_input"  # 密碼輸入框
    LOGIN_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/login_button"  # 登錄按鈕
    LOGIN_BUTTON_TEXT = "登入"  # 登錄按鈕文字（備用定位方式）
    NEXT_BUTTON_TEXT = "下一步"  # 下一步按鈕文字（如果登錄流程分兩步）
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化登錄頁面
        
        Args:
            driver: Appium WebDriver 實例
        """
        super().__init__(driver)
    
    def input_email(self, email: Optional[str] = None) -> bool:
        """
        輸入郵箱地址
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 輸入是否成功
        """
        if email is None:
            email = EnvConfig.NX_CLOUD_EMAIL
        
        self.logger.info(f"[LOGIN_PAGE] 輸入郵箱: {email}")
        
        # 優先使用 Resource ID 定位
        if self.input_text_by_id(self.EMAIL_INPUT_ID, email):
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位（查找包含 "Email" 或 "郵箱" 的輸入框）
        self.logger.warning(f"[LOGIN_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        element = self.find_element_by_xpath('//android.widget.EditText[contains(@hint, "Email") or contains(@hint, "郵箱")]')
        if element:
            return self.input_text(element, email)
        
        self.logger.error("[LOGIN_PAGE] 無法找到郵箱輸入框")
        return False
    
    def click_next_or_continue(self) -> bool:
        """
        點擊「下一步」或「繼續」按鈕（如果登錄流程分兩步）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[LOGIN_PAGE] 點擊「下一步」按鈕...")
        
        # 優先使用文字定位
        if self.click_by_text(self.NEXT_BUTTON_TEXT):
            return True
        
        # 如果文字定位失敗，嘗試使用 Resource ID
        self.logger.warning("[LOGIN_PAGE] 文字定位失敗，嘗試 Resource ID 定位...")
        if self.click_by_id(self.LOGIN_BUTTON_ID):
            return True
        
        self.logger.error("[LOGIN_PAGE] 無法找到「下一步」按鈕")
        return False
    
    def input_password(self, password: Optional[str] = None) -> bool:
        """
        輸入密碼
        
        Args:
            password: 密碼，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 輸入是否成功
        """
        if password is None:
            password = EnvConfig.NX_CLOUD_PASSWORD
        
        self.logger.info("[LOGIN_PAGE] 輸入密碼...")
        
        # 優先使用 Resource ID 定位
        if self.input_text_by_id(self.PASSWORD_INPUT_ID, password):
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning(f"[LOGIN_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        element = self.find_element_by_xpath('//android.widget.EditText[contains(@hint, "Password") or contains(@hint, "密碼")]')
        if element:
            return self.input_text(element, password)
        
        self.logger.error("[LOGIN_PAGE] 無法找到密碼輸入框")
        return False
    
    def click_login_button(self) -> bool:
        """
        點擊登錄按鈕
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[LOGIN_PAGE] 點擊登錄按鈕...")
        
        # 優先使用 Resource ID 定位
        if self.click_by_id(self.LOGIN_BUTTON_ID):
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[LOGIN_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.click_by_text(self.LOGIN_BUTTON_TEXT):
            return True
        
        # 嘗試其他可能的登錄按鈕文字
        alternative_texts = ["登錄", "Login", "Sign In", "登入"]
        for text in alternative_texts:
            if self.click_by_text(text):
                return True
        
        self.logger.error("[LOGIN_PAGE] 無法找到登錄按鈕")
        return False
    
    def is_login_successful(self, timeout: int = 15) -> bool:
        """
        檢查登錄是否成功
        
        策略：等待登錄頁面消失，或等待主頁面元素出現
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 登錄是否成功
        """
        self.logger.info("[LOGIN_PAGE] 檢查登錄狀態...")
        
        # 等待登錄按鈕消失（表示已離開登錄頁面）
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from appium.webdriver.common.appiumby import AppiumBy
            
            wait = WebDriverWait(self.driver, timeout)
            
            # 檢查登錄按鈕是否消失
            wait.until_not(
                EC.presence_of_element_located((AppiumBy.ID, self.LOGIN_BUTTON_ID))
            )
            self.logger.info("[LOGIN_PAGE] ✅ 登錄成功（登錄按鈕已消失）")
            return True
        except Exception as e:
            # 如果登錄按鈕仍然存在，檢查是否有錯誤提示
            self.logger.warning(f"[LOGIN_PAGE] 登錄按鈕仍然存在，可能登錄失敗: {e}")
            return False
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        執行完整的登錄流程
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的默認值
            password: 密碼，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 登錄是否成功
        """
        self.logger.info("[LOGIN_PAGE] 開始登錄流程...")
        
        # 步驟 1: 輸入郵箱
        if not self.input_email(email):
            self.logger.error("[LOGIN_PAGE] ❌ 輸入郵箱失敗")
            return False
        
        # 步驟 2: 點擊「下一步」（如果登錄流程分兩步）
        # 注意：某些 App 可能不需要這一步，如果找不到「下一步」按鈕則跳過
        self.click_next_or_continue()  # 不強制要求成功
        
        # 步驟 3: 輸入密碼
        if not self.input_password(password):
            self.logger.error("[LOGIN_PAGE] ❌ 輸入密碼失敗")
            return False
        
        # 步驟 4: 點擊登錄按鈕
        if not self.click_login_button():
            self.logger.error("[LOGIN_PAGE] ❌ 點擊登錄按鈕失敗")
            return False
        
        # 步驟 5: 驗證登錄是否成功
        if not self.is_login_successful():
            self.logger.error("[LOGIN_PAGE] ❌ 登錄驗證失敗")
            return False
        
        self.logger.info("[LOGIN_PAGE] ✅ 登錄流程完成")
        return True
