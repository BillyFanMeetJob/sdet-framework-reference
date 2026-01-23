# 相對路徑: pages/mobile/login_page.py
"""
Nx Witness 移動端登錄頁面

處理 Test Case 4-1: 登錄到 Nx Cloud
"""

from typing import Optional
import time
from appium.webdriver.common.appiumby import AppiumBy  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pages.mobile.base_mobile_page import BaseMobilePage
from config import EnvConfig


class LoginPage(BaseMobilePage):
    """
    Nx Witness 移動端登錄頁面
    
    職責：
    - 處理登錄相關操作（輸入郵箱、密碼、點擊登錄按鈕等）
    - 驗證登錄狀態
    """
    
    # Locators - 使用實際的 Resource ID（根據真實 App 的 XML 結構）
    EMAIL_INPUT_ID = "authorizeEmail"  # 郵箱輸入框（實際 ID）
    PASSWORD_INPUT_ID = "authorizePassword"  # 密碼輸入框（實際 ID）
    NEXT_BUTTON_TEXT = "Next"  # 下一步按鈕文字（實際文字）
    LOGIN_BUTTON_TEXT = "Log In"  # 登錄按鈕文字（實際文字）
    
    # 備用定位方式（如果主要定位失敗）
    CLOUD_TAB_ID = "com.networkoptix.nxwitness.mobile:id/cloud_tab"  # Cloud 標籤頁（備用）
    LOCAL_TAB_ID = "com.networkoptix.nxwitness.mobile:id/local_tab"  # Local 標籤頁（備用）
    LOGIN_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/login_button"  # 登錄按鈕（備用）
    SIGN_IN_BUTTON_TEXT = "登入"  # Sign In 按鈕文字（備用定位方式）
    
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
        
        try:
            # 使用實際的 Resource ID 定位
            email_field = self.driver.find_element(AppiumBy.ID, self.EMAIL_INPUT_ID)
            email_field.clear()
            email_field.send_keys(email)
            
            # 收起鍵盤（避免擋住按鈕）
            try:
                self.driver.hide_keyboard()
            except Exception:
                pass  # 如果鍵盤未顯示，忽略錯誤
            
            self.logger.info("[LOGIN_PAGE] ✅ 郵箱輸入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"[LOGIN_PAGE] ❌ 輸入郵箱失敗: {e}")
            return False
    
    def click_next_or_continue(self) -> bool:
        """
        點擊「下一步」或「繼續」按鈕（如果登錄流程分兩步）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[LOGIN_PAGE] 點擊「Next」按鈕...")
        
        try:
            # 使用 XPath 文字定位（實際文字為 "Next"）
            next_btn = self.driver.find_element(AppiumBy.XPATH, f"//*[@text='{self.NEXT_BUTTON_TEXT}']")
            next_btn.click()
            
            # 等待密碼框滑出來（根據實際測試腳本）
            time.sleep(2)
            
            self.logger.info("[LOGIN_PAGE] ✅ 「Next」按鈕點擊成功")
            return True
            
        except Exception as e:
            self.logger.warning(f"[LOGIN_PAGE] ⚠️ 點擊「Next」按鈕失敗（可能不需要這一步）: {e}")
            return False  # 不強制要求成功（某些 App 可能不需要這一步）
    
    def input_password(self, password: Optional[str] = None) -> bool:
        """
        輸入密碼（PDF Step 60）
        
        使用多種定位策略查找密碼輸入框，類似 Email 字段的定位方式。
        
        Args:
            password: 密碼，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 輸入是否成功
        """
        if password is None:
            password = EnvConfig.NX_CLOUD_PASSWORD
        
        self.logger.info("[LOGIN_PAGE] 輸入密碼（PDF Step 60）...")
        
        # 等待密碼框滑出來（點擊 Next 後可能需要等待動畫）
        time.sleep(2)
        
        password_field = None
        try:
            # 設定等待時間
            wait = WebDriverWait(self.driver, 15)
            
            # 策略 1: 嘗試使用 Resource ID 定位密碼輸入框
            try:
                password_field = wait.until(EC.presence_of_element_located((AppiumBy.ID, self.PASSWORD_INPUT_ID)))
                self.logger.info("[LOGIN_PAGE] [OK] 找到密碼欄位 (Resource ID)")
            except TimeoutException:
                # 策略 2: 如果 Resource ID 失敗，嘗試使用 Accessibility ID
                self.logger.warning("[LOGIN_PAGE] Resource ID 定位失敗，嘗試使用 Accessibility ID...")
                try:
                    password_field = wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, self.PASSWORD_INPUT_ID)))
                    self.logger.info("[LOGIN_PAGE] [OK] 找到密碼欄位 (Accessibility ID)")
                except TimeoutException:
                    # 策略 3: 嘗試使用 XPath 查找包含 "password" 的輸入框
                    self.logger.warning("[LOGIN_PAGE] Accessibility ID 定位失敗，嘗試使用 XPath...")
                    password_xpaths = [
                        f'//*[contains(@resource-id, "password") or contains(@resource-id, "Password")]',
                        f'//*[@class="android.widget.EditText" and contains(@resource-id, "password")]',
                        f'//android.widget.EditText[contains(@resource-id, "password")]',
                        f'//*[@password="true"]',  # 密碼類型的輸入框
                        f'//*[@inputType="textPassword"]',  # 密碼輸入類型
                    ]
                    for xpath in password_xpaths:
                        try:
                            password_field = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, xpath)))
                            self.logger.info(f"[LOGIN_PAGE] [OK] 找到密碼欄位 (XPath: {xpath})")
                            break
                        except TimeoutException:
                            continue
                    
                    if not password_field:
                        raise TimeoutException("所有定位策略都失敗，無法找到密碼輸入框")
            
            # 輸入密碼
            if password_field:
                password_field.clear()  # 先清空比較保險
                password_field.send_keys(password)
                
                # 再次收起鍵盤（以免擋住按鈕）
                try:
                    self.driver.hide_keyboard()
                except Exception:
                    pass  # 如果鍵盤未顯示，忽略錯誤
                
                self.logger.info("[LOGIN_PAGE] ✅ 密碼輸入成功")
                return True
            else:
                self.logger.error("[LOGIN_PAGE] ❌ 密碼欄位為 None")
                return False
            
        except Exception as e:
            self.logger.error(f"[LOGIN_PAGE] ❌ 輸入密碼失敗: {e}")
            
            # 診斷：輸出當前頁面信息
            self.logger.warning("[LOGIN_PAGE] [診斷] 開始診斷密碼輸入框查找失敗...")
            try:
                # 獲取當前 Activity
                current_activity = self.driver.current_activity
                self.logger.info(f"[LOGIN_PAGE] [診斷] 當前 Activity: {current_activity}")
                
                # 獲取頁面源碼中的關鍵信息
                page_source = self.driver.page_source
                if page_source:
                    import re
                    # 查找所有可能的輸入框
                    input_fields = re.findall(r'<.*?class="[^"]*[Ee]dit[^"]*".*?>', page_source[:5000])
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 找到的輸入框相關元素: {len(input_fields)} 個")
                    
                    # 查找所有可見文字
                    visible_texts = re.findall(r'text="([^"]+)"', page_source[:5000])
                    unique_texts = list(set([t for t in visible_texts if t.strip() and len(t) < 50]))[:30]
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面可見文字 (前30個): {unique_texts}")
                    
                    # 查找所有 Resource ID
                    resource_ids = re.findall(r'resource-id="([^"]+)"', page_source[:5000])
                    unique_ids = list(set([id for id in resource_ids if id.strip()]))[:30]
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面 Resource ID (前30個): {unique_ids}")
                    
                    # 檢查是否有包含 "password" 或 "pass" 的元素
                    password_related = [id for id in unique_ids if 'password' in id.lower() or 'pass' in id.lower()]
                    if password_related:
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 找到與 Password 相關的 Resource ID: {password_related}")
                    else:
                        self.logger.warning("[LOGIN_PAGE] [診斷] 未找到包含 'password' 或 'pass' 的 Resource ID")
                    
                    # 保存完整頁面源碼
                    try:
                        import os
                        import datetime
                        diagnostics_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                        os.makedirs(diagnostics_dir, exist_ok=True)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        page_source_path = os.path.join(diagnostics_dir, f"password_input_failed_{timestamp}.xml")
                        with open(page_source_path, "w", encoding="utf-8", errors='ignore') as f:
                            f.write(page_source)
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 完整頁面源碼已保存: {page_source_path}")
                    except Exception as save_error:
                        self.logger.debug(f"[LOGIN_PAGE] [診斷] 無法保存頁面源碼: {save_error}")
                
                # 截圖
                try:
                    import os
                    import datetime
                    screenshot_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(screenshot_dir, f"password_input_failed_{timestamp}.png")
                    if self.take_screenshot(screenshot_path):
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 錯誤截圖已保存: {screenshot_path}")
                except Exception as diag_error:
                    self.logger.warning(f"[LOGIN_PAGE] [診斷] 診斷過程發生錯誤: {diag_error}")
            except Exception as diag_error:
                self.logger.warning(f"[LOGIN_PAGE] [診斷] 診斷過程發生錯誤: {diag_error}")
            
            return False
    
    def click_login_button(self) -> bool:
        """
        點擊登錄按鈕（最終登入按鈕）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[LOGIN_PAGE] 點擊「Log In」按鈕...")
        
        try:
            # 使用 XPath 精準比對文字 "Log In"（實際文字）
            login_btn = self.driver.find_element(AppiumBy.XPATH, f"//*[@text='{self.LOGIN_BUTTON_TEXT}']")
            login_btn.click()
            
            self.logger.info("[LOGIN_PAGE] ✅ 「Log In」按鈕已點擊，等待伺服器回應...")
            return True
            
        except Exception as e:
            # 如果主要定位失敗，嘗試其他可能的文字
            self.logger.warning(f"[LOGIN_PAGE] 主要定位失敗，嘗試備用定位方式: {e}")
            alternative_texts = ["Log in", "Connect", "登錄", "Login", "Sign In", "登入"]
            for text in alternative_texts:
                try:
                    login_btn = self.driver.find_element(AppiumBy.XPATH, f"//*[@text='{text}']")
                    login_btn.click()
                    self.logger.info(f"[LOGIN_PAGE] ✅ 使用備用文字「{text}」點擊成功")
                    return True
                except Exception:
                    continue
            
            self.logger.error("[LOGIN_PAGE] ❌ 無法找到登錄按鈕")
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
    
    def switch_to_cloud_tab(self) -> bool:
        """
        切換到 Cloud 標籤頁（PDF Step 58）
        
        從 Local 標籤頁切換到 Cloud 標籤頁，以便進行雲端登錄。
        
        Returns:
            bool: 切換是否成功
        """
        self.logger.info("[LOGIN_PAGE] 切換到 Cloud 標籤頁（PDF Step 58）...")
        
        # 策略 1: 優先使用 Resource ID 定位 Cloud 標籤
        if self.click_by_id(self.CLOUD_TAB_ID):
            self.logger.info("[LOGIN_PAGE] ✅ 成功切換到 Cloud 標籤頁")
            return True
        
        # 策略 2: 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[LOGIN_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.click_by_text("Cloud") or self.click_by_text("雲端"):
            self.logger.info("[LOGIN_PAGE] ✅ 成功切換到 Cloud 標籤頁")
            return True
        
        # 策略 3: 嘗試使用 XPath 查找包含 "Cloud" 或 "雲端" 的標籤
        self.logger.warning("[LOGIN_PAGE] 文字定位失敗，嘗試 XPath 定位...")
        element = self.find_element_by_xpath('//*[contains(@text, "Cloud") or contains(@text, "雲端")]')
        if element:
            if self.click_element(element):
                self.logger.info("[LOGIN_PAGE] ✅ 成功切換到 Cloud 標籤頁")
                return True
        
        # 診斷：輸出當前頁面信息
        self.logger.error("[LOGIN_PAGE] ❌ 無法切換到 Cloud 標籤頁")
        self.logger.warning("[LOGIN_PAGE] [診斷] 開始診斷當前頁面狀態...")
        try:
            # 獲取當前 Activity
            current_activity = self.driver.current_activity
            self.logger.info(f"[LOGIN_PAGE] [診斷] 當前 Activity: {current_activity}")
            
            # 獲取頁面源碼中的關鍵信息
            page_source = self.driver.page_source
            if page_source:
                import re
                # 查找所有標籤相關的元素
                tabs = re.findall(r'<.*?class="[^"]*[Tt]ab[^"]*".*?>', page_source[:3000])
                self.logger.info(f"[LOGIN_PAGE] [診斷] 找到的標籤相關元素: {len(tabs)} 個")
                
                # 查找所有可見文字
                visible_texts = re.findall(r'text="([^"]+)"', page_source[:3000])
                unique_texts = list(set([t for t in visible_texts if t.strip() and len(t) < 50]))[:30]
                self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面可見文字 (前30個): {unique_texts}")
                
                # 查找所有 Resource ID
                resource_ids = re.findall(r'resource-id="([^"]+)"', page_source[:3000])
                unique_ids = list(set([id for id in resource_ids if id.strip()]))[:30]
                self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面 Resource ID (前30個): {unique_ids}")
                
                # 檢查是否有包含 "cloud" 或 "local" 的元素
                cloud_related = [id for id in unique_ids if 'cloud' in id.lower() or 'local' in id.lower()]
                if cloud_related:
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 找到與 Cloud/Local 相關的 Resource ID: {cloud_related}")
                else:
                    self.logger.warning("[LOGIN_PAGE] [診斷] 未找到包含 'cloud' 或 'local' 的 Resource ID")
            
            # 截圖
            import os
            import datetime
            screenshot_dir = os.path.join(os.getcwd(), "report", "diagnostics")
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshot_dir, f"cloud_tab_not_found_{timestamp}.png")
            if self.take_screenshot(screenshot_path):
                self.logger.info(f"[LOGIN_PAGE] [診斷] 診斷截圖已保存: {screenshot_path}")
        except Exception as diag_error:
            self.logger.warning(f"[LOGIN_PAGE] [診斷] 診斷過程發生錯誤: {diag_error}")
        
        return False
    
    def perform_cloud_login(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        執行雲端登錄流程（PDF Steps 59-60）
        
        完整流程（根據實際 App 行為）：
        1. 點擊座標 (550, 1500) 破解黑盒子 (SurfaceView)
        2. 等待動畫轉場（3 秒）
        3. 輸入郵箱
        4. 收起鍵盤
        5. 點擊「Next」按鈕
        6. 等待密碼框滑出來（2 秒）
        7. 輸入密碼
        8. 收起鍵盤
        9. 點擊「Log In」按鈕
        10. 驗證登錄是否成功
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的默認值
            password: 密碼，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 登錄是否成功
        """
        import time
        login_flow_start = time.time()
        self.logger.info(f"[LOGIN_PAGE] [時間戳: {time.strftime('%H:%M:%S')}] 開始執行雲端登錄流程（PDF Steps 59-60）...")
        
        try:
            # 步驟 1: 使用 W3C Action 進行穩定的點擊（破解黑盒子 SurfaceView）
            tap_coords = getattr(EnvConfig, 'LOGIN_SURFACEVIEW_TAP_COORDINATES', (550, 1500))
            tap_x, tap_y = tap_coords
            elapsed_before_tap = time.time() - login_flow_start
            self.logger.info(f"[LOGIN_PAGE] [耗時: {elapsed_before_tap:.2f}s] 準備點擊座標 ({tap_x}, {tap_y}) 以進入登入頁...")
            
            try:
                # 嘗試使用 W3C Action 進行更穩定的點擊
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                # 檢查是否有 w3c_actions 屬性
                if hasattr(actions, 'w3c_actions') and hasattr(actions.w3c_actions, 'pointer_action'):
                    finger = actions.w3c_actions.pointer_action
                    finger.move_to_location(tap_x, tap_y)
                    finger.pointer_down()
                    finger.pause(0.5)  # 按住 0.5 秒，確保 App 接收到
                    finger.pointer_up()  # 使用 pointer_up 而不是 pointer_release
                    actions.perform()
                    self.logger.info("[LOGIN_PAGE] W3C 點擊動作已執行")
                else:
                    raise AttributeError("w3c_actions not available")
            except (AttributeError, Exception) as e:
                # 如果 W3C 點擊失敗，嘗試使用 Appium 的 tap 方法
                self.logger.warning(f"[LOGIN_PAGE] W3C 點擊失敗，改用 Appium Tap: {e}")
                try:
                    # 使用 Appium 的 tap 方法（更可靠）
                    self.driver.tap([(tap_x, tap_y)], duration=500)  # 按住 500ms
                    self.logger.info(f"[LOGIN_PAGE] Appium Tap 已執行: ({tap_x}, {tap_y})")
                except Exception as tap_error:
                    # 最後嘗試使用 TouchAction
                    self.logger.warning(f"[LOGIN_PAGE] Appium Tap 失敗，改用 TouchAction: {tap_error}")
                    try:
                        from appium.webdriver.common.touch_action import TouchAction
                        action = TouchAction(self.driver)
                        action.tap(x=tap_x, y=tap_y, duration=500).perform()
                        self.logger.info(f"[LOGIN_PAGE] TouchAction 已執行: ({tap_x}, {tap_y})")
                    except Exception as touch_error:
                        self.logger.error(f"[LOGIN_PAGE] 所有點擊方法都失敗: {touch_error}")
                        raise
            
            # 步驟 2: 智慧等待登入頁面載入（關鍵修改）
            self.logger.info("[LOGIN_PAGE] 正在等待登入頁面載入 (最長等待 30 秒)...")
            
            # 先等待一下，讓頁面有時間響應點擊
            time.sleep(2)
            
            # 檢查是否需要切換到 WebView Context
            try:
                contexts = self.driver.contexts
                current_context = self.driver.current_context
                self.logger.info(f"[LOGIN_PAGE] [診斷] 可用 Contexts: {contexts}")
                self.logger.info(f"[LOGIN_PAGE] [診斷] 當前 Context: {current_context}")
                
                # 如果有 WebView Context，嘗試切換
                webview_contexts = [ctx for ctx in contexts if 'WEBVIEW' in ctx.upper()]
                if webview_contexts and current_context != webview_contexts[0]:
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 檢測到 WebView，嘗試切換 Context...")
                    try:
                        self.driver.switch_to.context(webview_contexts[0])
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 已切換到 WebView Context: {webview_contexts[0]}")
                        time.sleep(1)  # 等待 Context 切換完成
                    except Exception as ctx_error:
                        self.logger.warning(f"[LOGIN_PAGE] [診斷] 切換 WebView Context 失敗: {ctx_error}")
            except Exception as e:
                self.logger.debug(f"[LOGIN_PAGE] [診斷] 檢查 Context 時發生錯誤: {e}")
            
            email_field = None
            try:
                # 設定最長等待 30 秒（使用已導入的模組）
                wait = WebDriverWait(self.driver, 30)
                
                # 策略 1: 嘗試使用 Resource ID 定位 Email 輸入框
                try:
                    email_field = wait.until(EC.presence_of_element_located((AppiumBy.ID, self.EMAIL_INPUT_ID)))
                    self.logger.info("[LOGIN_PAGE] [OK] 成功！頁面跳轉完成，已找到 Email 欄位 (Resource ID)。")
                except TimeoutException:
                    # 策略 2: 如果 Resource ID 失敗，嘗試使用 Accessibility ID
                    self.logger.warning("[LOGIN_PAGE] Resource ID 定位失敗，嘗試使用 Accessibility ID...")
                    try:
                        email_field = wait.until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, self.EMAIL_INPUT_ID)))
                        self.logger.info("[LOGIN_PAGE] [OK] 成功！已找到 Email 欄位 (Accessibility ID)。")
                    except TimeoutException:
                        # 策略 3: 嘗試使用 XPath 查找包含 "email" 的輸入框
                        self.logger.warning("[LOGIN_PAGE] Accessibility ID 定位失敗，嘗試使用 XPath...")
                        email_xpaths = [
                            f'//*[contains(@resource-id, "email") or contains(@resource-id, "Email")]',
                            f'//*[contains(@text, "email") or contains(@text, "Email")]',
                            f'//*[@class="android.widget.EditText" and contains(@resource-id, "email")]',
                            f'//android.widget.EditText[contains(@resource-id, "email")]',
                        ]
                        for xpath in email_xpaths:
                            try:
                                email_field = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, xpath)))
                                self.logger.info(f"[LOGIN_PAGE] [OK] 成功！已找到 Email 欄位 (XPath: {xpath})。")
                                break
                            except TimeoutException:
                                continue
                        
                        if not email_field:
                            raise TimeoutException("所有定位策略都失敗")
                
            except Exception as e:
                self.logger.error("[LOGIN_PAGE] [ERROR] 等待 30 秒後依然沒看到 Email 欄位。")
                self.logger.error("[LOGIN_PAGE] 請檢查：1. 是否真的點中按鈕？ 2. 網路是否過慢？")
                
                # 診斷：輸出當前頁面信息
                self.logger.warning("[LOGIN_PAGE] [診斷] 開始診斷當前頁面狀態...")
                try:
                    # 獲取當前 Activity
                    current_activity = self.driver.current_activity
                    self.logger.info(f"[LOGIN_PAGE] [診斷] 當前 Activity: {current_activity}")
                    
                    # 檢查 Context
                    try:
                        contexts = self.driver.contexts
                        current_context = self.driver.current_context
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 可用 Contexts: {contexts}")
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 當前 Context: {current_context}")
                        
                        # 如果有 WebView Context，建議切換
                        webview_contexts = [ctx for ctx in contexts if 'WEBVIEW' in ctx.upper()]
                        if webview_contexts:
                            self.logger.warning(f"[LOGIN_PAGE] [診斷] ⚠️ 檢測到 WebView Context，可能需要切換: {webview_contexts}")
                            self.logger.warning("[LOGIN_PAGE] [診斷] 建議：如果頁面是 WebView，需要切換 Context 才能訪問元素")
                    except Exception as ctx_error:
                        self.logger.debug(f"[LOGIN_PAGE] [診斷] 檢查 Context 時發生錯誤: {ctx_error}")
                    
                    # 獲取頁面源碼中的關鍵信息
                    page_source = self.driver.page_source
                    if page_source:
                        import re
                        
                        # 檢查頁面類型
                        is_webview = 'WebView' in page_source or 'webview' in page_source.lower()
                        is_surfaceview = 'SurfaceView' in page_source or 'surfaceview' in page_source.lower()
                        
                        if is_webview:
                            self.logger.warning("[LOGIN_PAGE] [診斷] ⚠️ 檢測到 WebView，需要切換 Context")
                        if is_surfaceview:
                            self.logger.warning("[LOGIN_PAGE] [診斷] ⚠️ 檢測到 SurfaceView，可能需要使用座標點擊")
                        
                        # 查找所有可能的輸入框
                        input_fields = re.findall(r'<.*?class="[^"]*[Ee]dit[^"]*".*?>', page_source[:5000])
                        text_inputs = re.findall(r'<.*?class="[^"]*[Tt]ext[^"]*".*?>', page_source[:5000])
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 找到的輸入框相關元素: {len(input_fields)} 個")
                        
                        # 查找所有按鈕
                        buttons = re.findall(r'<.*?class="[^"]*[Bb]utton[^"]*".*?>', page_source[:5000])
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 找到的按鈕元素: {len(buttons)} 個")
                        
                        # 查找所有可見文字
                        visible_texts = re.findall(r'text="([^"]+)"', page_source[:5000])
                        unique_texts = list(set([t for t in visible_texts if t.strip() and len(t) < 50]))[:30]
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面可見文字 (前30個): {unique_texts}")
                        
                        # 查找所有 Resource ID
                        resource_ids = re.findall(r'resource-id="([^"]+)"', page_source[:5000])
                        unique_ids = list(set([id for id in resource_ids if id.strip()]))[:30]
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 頁面 Resource ID (前30個): {unique_ids}")
                        
                        # 檢查是否有包含 "email" 或 "mail" 的元素
                        email_related = [id for id in unique_ids if 'email' in id.lower() or 'mail' in id.lower()]
                        if email_related:
                            self.logger.info(f"[LOGIN_PAGE] [診斷] 找到與 Email 相關的 Resource ID: {email_related}")
                        else:
                            self.logger.warning("[LOGIN_PAGE] [診斷] 未找到包含 'email' 或 'mail' 的 Resource ID")
                        
                        # 保存完整頁面源碼
                        try:
                            import os
                            import datetime
                            diagnostics_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                            os.makedirs(diagnostics_dir, exist_ok=True)
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            page_source_path = os.path.join(diagnostics_dir, f"login_page_source_{timestamp}.xml")
                            with open(page_source_path, "w", encoding="utf-8", errors='ignore') as f:
                                f.write(page_source)
                            self.logger.info(f"[LOGIN_PAGE] [診斷] 完整頁面源碼已保存: {page_source_path}")
                        except Exception as save_error:
                            self.logger.debug(f"[LOGIN_PAGE] [診斷] 無法保存頁面源碼: {save_error}")
                    
                    # 截圖
                    import os
                    import datetime
                    screenshot_dir = os.path.join(os.getcwd(), "report", "diagnostics")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(screenshot_dir, f"login_timeout_{timestamp}.png")
                    if self.take_screenshot(screenshot_path):
                        self.logger.info(f"[LOGIN_PAGE] [診斷] 錯誤截圖已保存: {screenshot_path}")
                except Exception as diag_error:
                    self.logger.warning(f"[LOGIN_PAGE] [診斷] 診斷過程發生錯誤: {diag_error}")
                
                raise Exception(f"等待登入頁面載入超時: {e}")
            
            # 步驟 3: 輸入郵箱（PDF Step 59）
            # 注意：email_field 已經找到，可以直接使用
            try:
                email_field.clear()
                email_value = email or getattr(EnvConfig, 'NX_CLOUD_EMAIL', '')
                email_field.send_keys(email_value)
                self.logger.info(f"[LOGIN_PAGE] Email 輸入完畢: {email_value}")
                
                # 收起鍵盤 (避免擋住下一步按鈕)
                try:
                    self.driver.hide_keyboard()
                except:
                    pass
            except Exception as e:
                self.logger.error(f"[LOGIN_PAGE] [ERROR] 輸入郵箱失敗: {e}")
                return False
            
            # 步驟 4: 點擊「Next」按鈕（某些 App 的登錄流程分兩步）
            if not self.click_next_or_continue():
                # 如果找不到「Next」按鈕，可能不需要這一步，繼續執行
                self.logger.warning("[LOGIN_PAGE] ⚠️ 未找到「Next」按鈕，可能不需要這一步，繼續執行...")
            
            # 步驟 5: 輸入密碼（PDF Step 60）
            if not self.input_password(password):
                self.logger.error("[LOGIN_PAGE] ❌ 輸入密碼失敗（PDF Step 60）")
                return False
            
            # 步驟 6: 點擊「Log In」按鈕（PDF Step 60）
            if not self.click_login_button():
                self.logger.error("[LOGIN_PAGE] ❌ 點擊登入按鈕失敗（PDF Step 60）")
                return False
            
            # 步驟 7: 驗證登錄是否成功
            if not self.is_login_successful():
                self.logger.error("[LOGIN_PAGE] ❌ 登錄驗證失敗")
                return False
            
            self.logger.info("[LOGIN_PAGE] ✅ 雲端登錄流程完成（PDF Steps 59-60）")
            return True
            
        except Exception as e:
            self.logger.error(f"[LOGIN_PAGE] ❌ 雲端登錄流程執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return False