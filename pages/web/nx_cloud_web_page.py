# 相對路徑: pages/web/nx_cloud_web_page.py

from base.base_page import BasePage
from config import EnvConfig
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from toolkit.web_toolkit import create_driver
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base.browser import Browser


class NxCloudWebPage(BasePage):
    """
    Nx Cloud 網頁版登錄頁面處理類
    
    處理 Case 2-1 的網頁版登錄流程：
    1. 初始化 WebDriver（連接到已打開的 Chrome 視窗）
    2. 檢查登錄按鈕是否存在
    3. 點擊登錄按鈕
    4. 輸入郵箱
    5. 點擊【下一步】
    6. 輸入密碼
    7. 點擊【登錄】
    """
    
    def __init__(self, browser: "Browser" = None):
        """
        初始化 Nx Cloud 網頁版頁面
        
        Args:
            browser: Browser 實例，如果為 None 則需要手動初始化 WebDriver
        """
        if browser:
            super().__init__(browser)
        else:
            # 如果沒有 browser，需要手動初始化 WebDriver
            # 這種情況適用於 Chrome 已經由 Nx Witness 客戶端打開的情況
            self.browser = None
            self.driver = None
            self.wait = None
            self._manual_driver = True
            self.logger = None  # 將在 initialize_webdriver 中初始化
            try:
                from toolkit.logger import get_logger
                self.logger = get_logger(self.__class__.__name__)
            except:
                import logging
                self.logger = logging.getLogger(self.__class__.__name__)
    
    def initialize_webdriver(self) -> bool:
        """
        初始化 WebDriver（連接到已打開的 Chrome 視窗）
        
        注意：Chrome 已經由 Nx Witness 客戶端自動打開並跳轉到 Nx Cloud 網頁。
        🎯 關鍵：不要創建新的 Chrome 視窗，而是連接到已存在的 Chrome 實例。
        
        策略：
        1. 嘗試使用 Chrome Remote Debugging Port 連接到已打開的 Chrome
        2. 如果失敗，嘗試查找並切換到已打開的 Chrome 視窗
        
        Returns:
            bool: 初始化是否成功
        """
        if not self.logger:
            try:
                from toolkit.logger import get_logger
                self.logger = get_logger(self.__class__.__name__)
            except:
                import logging
                self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("[NX_CLOUD_WEB] [INIT] 初始化 WebDriver（連接到已打開的 Chrome，不創建新視窗）...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from webdriver_manager.chrome import ChromeDriverManager
            import time
            
            # 🎯 策略 1: 嘗試使用 Remote Debugging Port 連接到已打開的 Chrome
            # 注意：這需要 Chrome 以 remote debugging 模式啟動，但 Nx Witness 可能沒有這樣做
            # 所以我們先嘗試這個方法，如果失敗則使用策略 2
            
            # 🎯 策略 2: 創建一個新的 WebDriver 實例，但立即查找並切換到已打開的 Chrome 視窗
            # 注意：這可能會創建一個新的 Chrome 視窗，但我們會立即切換到已存在的視窗
            
            chrome_options = Options()
            
            # 🎯 關鍵：不設置 --user-data-dir 和 --guest，避免創建新的 Chrome 實例
            # 而是嘗試連接到已存在的 Chrome
            
            # 嘗試使用常見的 remote debugging port
            # 注意：如果 Nx Witness 沒有以 remote debugging 模式啟動 Chrome，這會失敗
            try:
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                self.logger.info("[NX_CLOUD_WEB] [INFO] 嘗試使用 Remote Debugging Port 9222 連接...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)
                self.logger.info("[NX_CLOUD_WEB] [OK] 成功連接到已打開的 Chrome（Remote Debugging）")
                return True
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD_WEB] Remote Debugging 連接失敗: {e}，嘗試其他方法...")
                # 清除 debuggerAddress，使用其他方法
                chrome_options = Options()
            
            # 🎯 策略 2: 使用 pyautogui 查找已打開的 Chrome 視窗，然後嘗試通過 CDP 連接
            # 注意：這需要 Chrome 支持 CDP，但即使不支持，我們也可以使用其他方法
            
            # 首先，嘗試查找已打開的 Chrome 視窗
            try:
                import pygetwindow as gw
                chrome_wins = []
                possible_titles = ["Chrome", "Google Chrome", "Nx Cloud", "Cloud Portal", "新分頁", "New Tab"]
                
                for title in possible_titles:
                    try:
                        wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                        chrome_wins.extend(wins)
                    except:
                        continue
                
                if chrome_wins:
                    # 找到 Chrome 視窗，嘗試使用 CDP 連接
                    self.logger.info(f"[NX_CLOUD_WEB] [INFO] 找到 {len(chrome_wins)} 個 Chrome 視窗")
                    
                    # 🎯 嘗試多個常見的 remote debugging port
                    # 注意：如果 Chrome 沒有以 remote debugging 模式啟動，這些都會失敗
                    common_ports = [9222, 9223, 9224, 9225]
                    
                    for port in common_ports:
                        try:
                            chrome_options = Options()
                            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
                            self.logger.info(f"[NX_CLOUD_WEB] [INFO] 嘗試使用 Remote Debugging Port {port} 連接...")
                            service = Service(ChromeDriverManager().install())
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            self.wait = WebDriverWait(self.driver, 10)
                            
                            # 檢查是否成功連接到 Nx Cloud 視窗
                            all_handles = self.driver.window_handles
                            for handle in all_handles:
                                try:
                                    self.driver.switch_to.window(handle)
                                    current_url = self.driver.current_url
                                    if any(keyword in current_url.lower() for keyword in ['nx', 'cloud', 'network', 'optix']):
                                        self.logger.info(f"[NX_CLOUD_WEB] [OK] 成功連接到 Nx Cloud 視窗（Port {port}）")
                                        self.logger.info(f"[NX_CLOUD_WEB] [INFO] 當前 URL: {current_url}")
                                        return True
                                except:
                                    continue
                            
                            # 如果連接到 Chrome 但沒找到 Nx Cloud 視窗，關閉這個連接
                            self.driver.quit()
                            self.driver = None
                        except Exception as e:
                            self.logger.debug(f"[NX_CLOUD_WEB] Port {port} 連接失敗: {e}")
                            continue
                    
                    # 如果所有 remote debugging port 都失敗，記錄警告
                    self.logger.warning("[NX_CLOUD_WEB] [WARN] 無法通過 Remote Debugging 連接，Chrome 可能沒有以 remote debugging 模式啟動")
                    
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD_WEB] 查找 Chrome 視窗時發生異常: {e}")
            
            # 🎯 策略 3: 如果無法連接到已存在的 Chrome，記錄錯誤並返回 False
            # 注意：我們不應該創建新的 Chrome 視窗，因為它會擋住原本的 Nx Cloud 網頁
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 無法連接到已打開的 Chrome 視窗")
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 請確保 Chrome 以 remote debugging 模式啟動，或使用其他方法連接")
            return False
                
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] WebDriver 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_login_button_exists(self) -> bool:
        """
        檢查網頁右上角登錄按鈕是否存在
        
        Returns:
            bool: 登錄按鈕是否存在
        """
        self.logger.info("[NX_CLOUD_WEB] [CHECK] 檢查網頁右上角登錄按鈕是否存在...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 嘗試找到登錄按鈕（使用 xpath）
            login_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[normalize-space()='登錄']"))
            )
            if login_button:
                self.logger.info("[NX_CLOUD_WEB] [OK] 找到登錄按鈕")
                return True
        except TimeoutException:
            self.logger.warning("[NX_CLOUD_WEB] [WARN] 未找到登錄按鈕（可能已經登錄）")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 檢查登錄按鈕時發生異常: {e}")
            return False
    
    def click_login_button(self) -> bool:
        """
        點擊登錄按鈕
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊登錄按鈕...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到登錄按鈕並點擊
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='登錄']"))
            )
            login_button.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊登錄按鈕")
            time.sleep(1)  # 等待頁面跳轉
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待登錄按鈕超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊登錄按鈕時發生異常: {e}")
            return False
    
    def input_email(self, email: str = None) -> bool:
        """
        在登錄畫面輸入郵箱
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的郵箱
        
        Returns:
            bool: 輸入是否成功
        """
        if email is None:
            email = getattr(EnvConfig, 'NX_CLOUD_EMAIL', 'billy.19920717@gmail.com')
        
        self.logger.info(f"[NX_CLOUD_WEB] [INPUT] 輸入郵箱: {email}")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到郵箱輸入框
            email_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='authorizeEmail']"))
            )
            email_input.clear()
            email_input.send_keys(email)
            self.logger.info(f"[NX_CLOUD_WEB] [OK] 成功輸入郵箱: {email}")
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待郵箱輸入框超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 輸入郵箱時發生異常: {e}")
            return False
    
    def click_next_button(self) -> bool:
        """
        點擊【下一步】按鈕
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊【下一步】按鈕...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到【下一步】按鈕並點擊
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            next_button.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊【下一步】按鈕")
            time.sleep(1)  # 等待頁面跳轉
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待【下一步】按鈕超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊【下一步】按鈕時發生異常: {e}")
            return False
    
    def input_password(self, password: str = None) -> bool:
        """
        輸入密碼
        
        Args:
            password: 密碼，如果為 None 則使用配置中的密碼
        
        Returns:
            bool: 輸入是否成功
        """
        if password is None:
            password = getattr(EnvConfig, 'NX_CLOUD_PASSWORD', EnvConfig.ADMIN_PASSWORD)
        
        self.logger.info("[NX_CLOUD_WEB] [INPUT] 輸入密碼...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到密碼輸入框
            password_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='authorizePassword']"))
            )
            password_input.clear()
            password_input.send_keys(password)
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功輸入密碼")
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待密碼輸入框超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 輸入密碼時發生異常: {e}")
            return False
    
    def click_login_submit_button(self) -> bool:
        """
        點擊【登錄】按鈕（提交登錄表單）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊【登錄】按鈕...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到【登錄】按鈕並點擊
            login_submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_submit_button.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊【登錄】按鈕")
            time.sleep(2)  # 等待登錄完成
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待【登錄】按鈕超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊【登錄】按鈕時發生異常: {e}")
            return False
    
    def close_webdriver(self):
        """
        關閉 WebDriver
        """
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("[NX_CLOUD_WEB] [CLOSE] WebDriver 已關閉")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"[NX_CLOUD_WEB] 關閉 WebDriver 時發生異常: {e}")
            finally:
                self.driver = None
                self.wait = None
