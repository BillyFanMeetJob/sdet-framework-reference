# 相對路徑: pages/web/nx_cloud_web_page.py

from base.base_page import BasePage
from config import EnvConfig
import time
import os
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
    Nx Cloud 網頁版登入頁面處理類
    
    處理 Case 2-1 的網頁版登入流程：
    1. 初始化 WebDriver（連接到已打開的 Chrome 視窗）
    2. 檢查登入按鈕是否存在
    3. 點擊登入按鈕
    4. 輸入郵箱
    5. 點擊【下一步】
    6. 輸入密碼
    7. 點擊【登入】
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
    
    def _add_connection_options(self, chrome_options):
        """
        添加解決 "Could not reach host" 問題的 Chrome 選項
        
        Args:
            chrome_options: ChromeOptions 實例
        """
        # 🎯 關鍵：解決 "Could not reach host"
        chrome_options.add_argument('--dns-prefetch-disable')          # 禁用預解析，防止卡死
        chrome_options.add_argument('--no-proxy-server')               # 絕對必要：跳過熱點可能提供的 Proxy
        chrome_options.add_argument('--proxy-server=direct://')        # 強制直連
        chrome_options.add_argument('--proxy-bypass-list=*')          # 繞過所有代理
        
        # 🎯 穩定連線
        chrome_options.add_argument('--ignore-certificate-errors')    # 忽略憑證錯誤
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
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
            
            # 添加連接相關選項
            self._add_connection_options(chrome_options)
            
            # 🎯 關鍵：不設置 --user-data-dir 和 --guest，避免創建新的 Chrome 實例
            # 而是嘗試連接到已存在的 Chrome
            
            # 嘗試使用常見的 remote debugging port
            # 注意：如果 Nx Witness 沒有以 remote debugging 模式啟動 Chrome，這會失敗
            try:
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9223")
                self.logger.info("[NX_CLOUD_WEB] [INFO] 嘗試使用 Remote Debugging Port 9223 連接...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)
                self.logger.info("[NX_CLOUD_WEB] [OK] 成功連接到已打開的 Chrome（Remote Debugging）")
                return True
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD_WEB] Remote Debugging 連接失敗: {e}，嘗試其他方法...")
                # 清除 debuggerAddress，使用其他方法
                chrome_options = Options()
                # 重新添加連接相關選項
                self._add_connection_options(chrome_options)
            
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
                    common_ports = [9223, 9222, 9224, 9225]
                    
                    for port in common_ports:
                        try:
                            chrome_options = Options()
                            # 添加連接相關選項
                            self._add_connection_options(chrome_options)
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
    
    def switch_to_traditional_chinese(self) -> bool:
        """
        切換網頁語言為繁體中文
        
        步驟：
        1. 點擊語言下拉選單箭頭（//div[@class='dropdown-arrow-wrapper']）
        2. 點擊繁體中文選項（//ul[@aria-labelledby='dropdownMenuButton']//li[contains(@class,'dropdown-item-container') and contains(.,'繁體中文')]）
        
        Returns:
            bool: 切換是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [LANG] 切換語言為繁體中文...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 步驟 1: 點擊語言下拉選單箭頭
            self.logger.info("[NX_CLOUD_WEB] [LANG] 步驟 1: 點擊語言下拉選單箭頭...")
            dropdown_arrow = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='dropdown-arrow-wrapper']"))
            )
            dropdown_arrow.click()
            self.logger.info("[NX_CLOUD_WEB] [LANG] 成功點擊語言下拉選單箭頭")
            time.sleep(0.5)  # 等待選單展開
            
            # 步驟 2: 點擊繁體中文選項 (暴力遍歷法)
            self.logger.info("[NX_CLOUD_WEB] [LANG] 步驟 2: 嘗試暴力點擊所有可能的繁體中文選項...")
            
            try:
                # 🎯 診斷：先截圖記錄當前頁面狀態
                try:
                    screenshot_path = os.path.join(EnvConfig.LOG_PATH, f"lang_switch_before_{int(time.time())}.png")
                    self.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 已截圖（點擊前）: {screenshot_path}")
                except Exception as screenshot_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 截圖失敗: {screenshot_e}")
                
                # 🎯 診斷：先檢查下拉選單是否已展開
                try:
                    dropdown_menu = self.driver.find_elements(By.XPATH, "//ul[@aria-labelledby='dropdownMenuButton']")
                    if dropdown_menu:
                        menu_visible = dropdown_menu[0].is_displayed()
                        self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 下拉選單是否存在: {len(dropdown_menu) > 0}, 是否可見: {menu_visible}")
                    else:
                        self.logger.warning("[NX_CLOUD_WEB] [LANG] [DEBUG] 找不到下拉選單元素")
                except Exception as menu_check_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 檢查下拉選單時發生錯誤: {menu_check_e}")
                
                # 1. 找出所有包含 '繁體中文' 的連結 (a 標籤) 或 列表項 (li)
                # 使用 presence_of_all_elements_located (注意是 all)
                # 這裡放寬條件，只要文字包含繁體中文都抓出來
                xpath_candidates = "//li//a[contains(., '繁体中文')] | //a[contains(., '繁体中文')]"
                
                self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 嘗試 XPath: {xpath_candidates}")
                
                elements = self.wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, xpath_candidates))
                )
                
                self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 找到 {len(elements)} 個可能的 '繁體中文' 元素")
                
                # 🎯 診斷：詳細記錄每個元素的屬性
                clicked_success = False
                for idx, elem in enumerate(elements):
                    try:
                        # 印出元素的詳細資訊幫忙除錯
                        is_displayed = elem.is_displayed()
                        tag_name = elem.tag_name
                        elem_text = elem.text
                        elem_location = elem.location
                        elem_size = elem.size
                        is_enabled = elem.is_enabled()
                        
                        self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 元素 {idx} 詳細信息:")
                        self.logger.info(f"   - Tag: {tag_name}")
                        self.logger.info(f"   - Text: '{elem_text}'")
                        self.logger.info(f"   - Visible: {is_displayed}")
                        self.logger.info(f"   - Enabled: {is_enabled}")
                        self.logger.info(f"   - Location: {elem_location}")
                        self.logger.info(f"   - Size: {elem_size}")
                        
                        # 策略 A: 如果它是可見的，優先嘗試 JS 點擊
                        if is_displayed:
                            self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 嘗試對元素 {idx} 執行 JS 點擊...")
                            self.driver.execute_script("arguments[0].click();", elem)
                            self.logger.info(f"[NX_CLOUD_WEB] [LANG] [SUCCESS] 已對可見元素 {idx} 執行 JS 點擊")
                            
                            # 🎯 診斷：點擊後等待並檢查是否成功
                            time.sleep(0.5)
                            try:
                                # 檢查頁面是否有變化（例如 URL 變化或元素消失）
                                current_url_after = self.driver.current_url
                                self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 點擊後 URL: {current_url_after}")
                                
                                # 再次檢查元素是否還存在（如果語言切換成功，選單可能會關閉）
                                try:
                                    elem_after = self.driver.find_element(By.XPATH, xpath_candidates)
                                    still_exists = elem_after.is_displayed() if elem_after else False
                                    self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 點擊後元素是否仍可見: {still_exists}")
                                except:
                                    self.logger.info("[NX_CLOUD_WEB] [LANG] [DEBUG] 點擊後元素已消失（可能是正常的，表示選單已關閉）")
                            except Exception as check_e:
                                self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 檢查點擊結果時發生錯誤: {check_e}")
                            
                            clicked_success = True
                            break # 成功就跳出
                        
                        # 策略 B: 如果上面沒 break，且只有一個元素，就算不可見也硬點
                        if len(elements) == 1:
                            self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 只有一個元素，強制執行 JS 點擊（即使不可見）...")
                            self.driver.execute_script("arguments[0].click();", elem)
                            self.logger.info(f"[NX_CLOUD_WEB] [LANG] [FORCE] 已強制執行 JS 點擊")
                            clicked_success = True
                            break
                            
                    except Exception as inner_e:
                        self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 點擊元素 {idx} 失敗: {inner_e}")
                        import traceback
                        self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 錯誤詳情: {traceback.format_exc()[:300]}")
                        continue
                
                if not clicked_success:
                    # 如果迴圈跑完都沒點到，嘗試最後一招：直接用文字完全匹配
                    self.logger.warning("[NX_CLOUD_WEB] [LANG] [RETRY] 前面嘗試失敗，嘗試最後一招：精確文字匹配")
                    try:
                        exact_elem = self.driver.find_element(By.XPATH, "//*[text()='繁體中文']")
                        self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 找到精確匹配元素，執行點擊...")
                        self.driver.execute_script("arguments[0].click();", exact_elem)
                        self.logger.info("[NX_CLOUD_WEB] [LANG] [SUCCESS] 精確匹配點擊成功")
                        clicked_success = True
                    except Exception as exact_e:
                        self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 精確匹配也失敗: {exact_e}")
                        # 🎯 診斷：如果所有方法都失敗，截圖並列出頁面中所有文字
                        try:
                            all_texts = self.driver.find_elements(By.XPATH, "//*[contains(text(), '繁') or contains(text(), '中') or contains(text(), '文')]")
                            self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 頁面中包含 '繁'、'中' 或 '文' 的元素數量: {len(all_texts)}")
                            for i, text_elem in enumerate(all_texts[:10]):  # 只顯示前10個
                                try:
                                    self.logger.warning(f"   - 元素 {i}: '{text_elem.text}' (Tag: {text_elem.tag_name}, Visible: {text_elem.is_displayed()})")
                                except:
                                    pass
                        except Exception as debug_e:
                            self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 無法列出頁面文字: {debug_e}")

                # 🎯 診斷：點擊後再次截圖
                try:
                    screenshot_path_after = os.path.join(EnvConfig.LOG_PATH, f"lang_switch_after_{int(time.time())}.png")
                    self.driver.save_screenshot(screenshot_path_after)
                    self.logger.info(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 已截圖（點擊後）: {screenshot_path_after}")
                except Exception as screenshot_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 點擊後截圖失敗: {screenshot_e}")

                time.sleep(2.0) # 等待語言切換
                
                if clicked_success:
                    self.logger.info("[NX_CLOUD_WEB] [LANG] [SUCCESS] 語言切換操作完成")
                else:
                    self.logger.error("[NX_CLOUD_WEB] [LANG] [ERROR] 所有點擊嘗試都失敗")
                
            except Exception as e:
                self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 點擊失敗: {e}")
                import traceback
                self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 錯誤詳情: {traceback.format_exc()}")
                # 🎯 診斷：發生錯誤時截圖
                try:
                    screenshot_path_error = os.path.join(EnvConfig.LOG_PATH, f"lang_switch_error_{int(time.time())}.png")
                    self.driver.save_screenshot(screenshot_path_error)
                    self.logger.error(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 錯誤截圖已保存: {screenshot_path_error}")
                except Exception as screenshot_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [LANG] [DEBUG] 錯誤截圖失敗: {screenshot_e}")
                raise e
            return True
            
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [LANG] [ERROR] 等待語言切換元素超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [LANG] [ERROR] 切換語言時發生異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_login_button_exists(self) -> bool:
        """
        檢查網頁右上角登入按鈕是否存在
        
        Returns:
            bool: 登入按鈕是否存在
        """
        self.logger.info("[NX_CLOUD_WEB] [CHECK] 檢查網頁右上角登入按鈕是否存在...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        # 記錄當前頁面信息
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"[NX_CLOUD_WEB] [CHECK] 當前 URL: {current_url}")
            self.logger.info(f"[NX_CLOUD_WEB] [CHECK] 頁面標題: {page_title}")
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [CHECK] 無法獲取頁面信息: {e}")
        
        # 直接使用單一 xpath 查找登入按鈕
        xpath = "//a[normalize-space()='登入']"
        self.logger.info(f"[NX_CLOUD_WEB] [CHECK] 嘗試 locator: By.XPATH = '{xpath}'")
        
        try:
            login_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if login_button:
                # 獲取按鈕的詳細信息
                try:
                    button_text = login_button.text
                    button_tag = login_button.tag_name
                    is_displayed = login_button.is_displayed()
                    is_enabled = login_button.is_enabled()
                    self.logger.info(f"[NX_CLOUD_WEB] [OK] 找到登入按鈕")
                    self.logger.info(f"[NX_CLOUD_WEB] [OK] 按鈕信息: tag={button_tag}, text='{button_text}', displayed={is_displayed}, enabled={is_enabled}")
                    return True
                except Exception as e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [CHECK] 找到元素但無法獲取詳細信息: {e}")
                    return True
        except TimeoutException:
            self.logger.warning("[NX_CLOUD_WEB] [WARN] 未找到登入按鈕（超時）")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 查找登入按鈕時發生異常: {e}")
            return False
    
    def click_login_button(self) -> bool:
        """
        點擊登入按鈕
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊登入按鈕...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到登入按鈕並點擊
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='登入']"))
            )
            login_button.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊登入按鈕")
            time.sleep(1)  # 等待頁面跳轉
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待登入按鈕超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊登入按鈕時發生異常: {e}")
            return False
    
    def input_email(self, email: str = None) -> bool:
        """
        在登入畫面輸入郵箱
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的郵箱
        
        Returns:
            bool: 輸入是否成功
        """
        if email is None:
            email = getattr(EnvConfig, 'NX_CLOUD_EMAIL', 'billy.19920917@gmail.com')
        
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
        點擊【登入】按鈕（提交登入表單）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊【登入】按鈕...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        try:
            # 使用 xpath 找到【登入】按鈕並點擊
            login_submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_submit_button.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊【登入】按鈕")
            time.sleep(2)  # 等待登入完成
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待【登入】按鈕超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊【登入】按鈕時發生異常: {e}")
            return False
    
    def start_new_driver_and_open_url(self, url: str) -> bool:
        """
        [Web] 啟動全新的 Selenium Driver 並開啟指定 URL
        
        策略：
        1. 使用 Browser 類創建全新的 Chrome WebDriver 實例（符合分層架構）
        2. 導航到指定的 URL
        3. 最大化視窗
        4. 更新 self.driver 和 self.wait 引用
        
        注意：這是一個全新的 session，不會嘗試連接已存在的 Chrome 視窗
        
        Args:
            url: 要導航到的 URL
            
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
        
        self.logger.info(f"[NX_CLOUD_WEB] [START_NEW] 啟動新 Driver 並導航至: {url}")
        
        try:
            # 如果已經有 browser 和 driver，先關閉它們
            if hasattr(self, 'browser') and self.browser:
                try:
                    self.browser.quit()
                except:
                    pass
                self.browser = None
            
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self.wait = None
            
            # 使用 Browser 類創建全新的 WebDriver 實例（符合分層架構）
            # Browser 類內部會調用 create_driver()
            from base.browser import Browser
            self.browser = Browser()
            self.driver = self.browser.driver
            self.wait = self.browser.wait
            
            if self.driver:
                # 導航到指定 URL
                self.driver.get(url)
                # 最大化視窗
                self.driver.maximize_window()
                self.logger.info(f"[NX_CLOUD_WEB] [START_NEW] 成功啟動新 Driver 並導航至: {url}")
                
                # 切換語言為繁體中文
                if not self.switch_to_traditional_chinese():
                    self.logger.warning("[NX_CLOUD_WEB] [START_NEW] 語言切換失敗，但繼續執行後續流程")
                
                return True
            else:
                self.logger.error("[NX_CLOUD_WEB] [START_NEW] Browser 初始化失敗，driver 為 None")
                return False
                
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [START_NEW] 啟動新 Driver 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def attach_to_debug_chrome(self, port: int = 9223) -> bool:
        """
        連接到已存在的 Chrome 實例（通過 Remote Debugging Port）
        如果無法連接，則自動啟動一個新的 Chrome 實例（使用 remote debugging port）
        
        策略：
        1. 嘗試使用指定的 remote debugging port 連接到已存在的 Chrome 實例
        2. 如果連接失敗，自動啟動一個新的 Chrome 實例（使用 remote debugging port）
        3. 如果連接成功，更新 self.driver 和 self.wait
        
        Args:
            port: Remote debugging port，默認為 9223
        
        Returns:
            bool: 連接是否成功
        """
        if not self.logger:
            try:
                from toolkit.logger import get_logger
                self.logger = get_logger(self.__class__.__name__)
            except:
                import logging
                self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] 嘗試連接到 Remote Debugging Port {port}...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from webdriver_manager.chrome import ChromeDriverManager
            import config as C
            import tempfile
            
            # 創建 Chrome 選項
            chrome_options = Options()
            
            # 添加連接相關選項
            self._add_connection_options(chrome_options)
            
            # 使用 remote debugging port 連接到已存在的 Chrome
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
            # 獲取 timeout
            timeout = getattr(C, 'DEFAULT_TIMEOUT', 10)
            
            # 創建 Service
            service = Service(ChromeDriverManager().install())
            
            # 創建 WebDriver（連接到已存在的 Chrome）
            driver = webdriver.Chrome(service=service, options=chrome_options)
            wait = WebDriverWait(driver, timeout)
            
            # 更新實例變量
            self.driver = driver
            self.wait = wait
            
            # 記錄當前 URL
            try:
                current_url = driver.current_url
                self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] ✅ 成功連接到 Chrome，當前 URL: {current_url}")
            except:
                self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] ✅ 成功連接到 Chrome")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [ATTACH] ⚠️ 無法連接到 Port {port} 的 Chrome: {e}")
            self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] 自動啟動一個新的 Chrome 實例（使用 Remote Debugging Port {port}）...")
            
            # 如果連接失敗，自動啟動一個新的 Chrome 實例
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.support.ui import WebDriverWait
                from webdriver_manager.chrome import ChromeDriverManager
                import config as C
                import tempfile
                
                # 創建 Chrome 選項（啟動新的 Chrome 實例）
                chrome_options = Options()
                
                # 添加連接相關選項（包含 --no-proxy-server 和 --disable-blink-features=AutomationControlled）
                self._add_connection_options(chrome_options)
                
                # 2. 繞過沙盒模式（避免權限問題）
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                
                # 4. 禁用網絡檢查（避免 "Could not reach host" 錯誤）
                chrome_options.add_argument('--disable-background-networking')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                
                # 乾淨 profile（避免讀到本機 Chrome 的登入/同步/密碼庫）
                profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
                chrome_options.add_argument(f"--user-data-dir={profile_dir}")
                
                # 訪客模式
                chrome_options.add_argument("--guest")
                
                # 🎯 使用 remote-debugging-port 讓瀏覽器在 driver 關閉後仍然保持打開
                chrome_options.add_argument(f"--remote-debugging-port={port}")
                chrome_options.add_experimental_option("detach", True)
                
                # 關閉密碼管理相關提示
                prefs = {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                # 檢查 HEADLESS 配置
                headless = getattr(C, 'HEADLESS', False)
                if headless:
                    chrome_options.add_argument("--headless=new")
                
                # 獲取 timeout
                timeout = getattr(C, 'DEFAULT_TIMEOUT', 10)
                
                # 創建 Service（添加額外的服務參數）
                try:
                    service = Service(ChromeDriverManager().install())
                except Exception as service_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [ATTACH] ChromeDriverManager 安裝失敗: {service_e}，嘗試使用系統 ChromeDriver")
                    # 備選：嘗試使用系統 PATH 中的 chromedriver
                    service = Service()
                
                # 創建 WebDriver（啟動新的 Chrome 實例）
                try:
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    wait = WebDriverWait(driver, timeout)
                    
                    # 更新實例變量
                    self.driver = driver
                    self.wait = wait
                    
                    self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] ✅ 成功啟動新的 Chrome 實例（Remote Debugging Port {port}）")
                    
                    return True
                except Exception as driver_e:
                    # 如果使用 remote debugging port 失敗，嘗試不使用 remote debugging port（備選方案）
                    self.logger.warning(f"[NX_CLOUD_WEB] [ATTACH] 使用 Remote Debugging Port 啟動失敗: {driver_e}")
                    self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] 嘗試不使用 Remote Debugging Port 啟動 Chrome（備選方案）...")
                    
                    # 移除 remote debugging port 相關選項
                    chrome_options = Options()
                    # 添加連接相關選項（包含 --no-proxy-server 和 --disable-blink-features=AutomationControlled）
                    self._add_connection_options(chrome_options)
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-background-networking')
                    chrome_options.add_argument('--disable-background-timer-throttling')
                    chrome_options.add_argument('--disable-renderer-backgrounding')
                    chrome_options.add_argument('--disable-features=TranslateUI')
                    chrome_options.add_argument('--disable-ipc-flooding-protection')
                    
                    profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
                    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
                    chrome_options.add_argument("--guest")
                    
                    prefs = {
                        "credentials_enable_service": False,
                        "profile.password_manager_enabled": False,
                    }
                    chrome_options.add_experimental_option("prefs", prefs)
                    
                    if headless:
                        chrome_options.add_argument("--headless=new")
                    
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    wait = WebDriverWait(driver, timeout)
                    
                    self.driver = driver
                    self.wait = wait
                    
                    self.logger.info(f"[NX_CLOUD_WEB] [ATTACH] ✅ 成功啟動新的 Chrome 實例（不使用 Remote Debugging Port，備選方案）")
                    
                    return True
                
            except Exception as e2:
                self.logger.error(f"[NX_CLOUD_WEB] [ATTACH] ❌ 啟動新的 Chrome 實例失敗: {e2}")
                import traceback
                self.logger.debug(f"[NX_CLOUD_WEB] [ATTACH] 錯誤詳情: {traceback.format_exc()}")
                return False
    
    def click_view_tab(self) -> bool:
        """
        點擊「查看」頁簽
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊「查看」頁簽...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        # 記錄當前頁面信息
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 當前 URL: {current_url}")
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 頁面標題: {page_title}")
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [CLICK] 無法獲取頁面信息: {e}")
        
        # 記錄使用的 XPath
        xpath = "//div[@class='menu-items']//div[contains(normalize-space(@class),'outer-menu-item') and normalize-space()='查看']/a[contains(normalize-space(@class),'anchor')]"
        self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 嘗試 locator: By.XPATH = '{xpath}'")
        
        try:
            view_tab = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            view_tab.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊「查看」頁簽")
            time.sleep(1.5)  # 等待頁面切換
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待「查看」頁簽超時")
            # 診斷：嘗試查找所有包含「查看」的元素
            try:
                all_view_elements = self.driver.find_elements(By.XPATH, "//*[contains(.,'查看')]")
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 頁面中包含「查看」的元素數量: {len(all_view_elements)}")
                for i, elem in enumerate(all_view_elements[:5]):  # 只顯示前5個
                    try:
                        self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG]   元素 {i}: Tag={elem.tag_name}, Text='{elem.text[:50]}', Visible={elem.is_displayed()}")
                    except:
                        pass
            except Exception as debug_e:
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 無法查找「查看」相關元素: {debug_e}")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊「查看」頁簽時發生異常: {e}")
            return False
    
    def click_server(self) -> bool:
        """
        點擊 server 元素
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊 server...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        # 記錄當前頁面信息
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 當前 URL: {current_url}")
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 頁面標題: {page_title}")
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [CLICK] 無法獲取頁面信息: {e}")
        
        # 記錄使用的 XPath
        xpath = "//div[@class='server online ng-star-inserted']"
        self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 嘗試 locator: By.XPATH = '{xpath}'")
        
        try:
            server = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            server.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊 server")
            time.sleep(1.5)  # 等待頁面加載
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待 server 元素超時")
            # 診斷：嘗試查找所有 server 相關的元素
            try:
                all_server_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class,'server')]")
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 頁面中包含 'server' class 的元素數量: {len(all_server_elements)}")
                for i, elem in enumerate(all_server_elements[:5]):  # 只顯示前5個
                    try:
                        class_attr = elem.get_attribute('class')
                        self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG]   元素 {i}: Tag={elem.tag_name}, Class='{class_attr}', Visible={elem.is_displayed()}")
                    except:
                        pass
            except Exception as debug_e:
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 無法查找 server 相關元素: {debug_e}")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊 server 時發生異常: {e}")
            return False
    
    def click_usb_cam(self) -> bool:
        """
        點擊 usb-cam 元素
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD_WEB] [CLICK] 點擊 usb-cam...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        # 記錄當前頁面信息
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 當前 URL: {current_url}")
            self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 頁面標題: {page_title}")
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [CLICK] 無法獲取頁面信息: {e}")
        
        # 記錄使用的 XPath
        xpath = "//span[nx-search-highlight[normalize-space()='usb_cam-ACER HD User Facing']]"
        self.logger.info(f"[NX_CLOUD_WEB] [CLICK] 嘗試 locator: By.XPATH = '{xpath}'")
        
        try:
            usb_cam = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            usb_cam.click()
            self.logger.info("[NX_CLOUD_WEB] [OK] 成功點擊 usb-cam")
            time.sleep(1.5)  # 等待頁面加載
            return True
        except TimeoutException:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] 等待 usb-cam 元素超時")
            # 診斷：嘗試查找所有包含 usb_cam 的元素
            try:
                all_usb_elements = self.driver.find_elements(By.XPATH, "//*[contains(.,'usb_cam') or contains(.,'usb-cam')]")
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 頁面中包含 'usb_cam' 的元素數量: {len(all_usb_elements)}")
                for i, elem in enumerate(all_usb_elements[:5]):  # 只顯示前5個
                    try:
                        self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG]   元素 {i}: Tag={elem.tag_name}, Text='{elem.text[:50]}', Visible={elem.is_displayed()}")
                    except:
                        pass
            except Exception as debug_e:
                self.logger.warning(f"[NX_CLOUD_WEB] [DEBUG] 無法查找 usb_cam 相關元素: {debug_e}")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [ERROR] 點擊 usb-cam 時發生異常: {e}")
            return False
    
    def verify_video_playback_status(self, timeout: int = 20) -> bool:
        """
        [Web] 驗證頁面上的 <video> 物件是否載入完成且可播放
        
        策略：
        1. 尋找頁面上的 <video> 元素
        2. 使用 JavaScript 檢查 video 元素的內部狀態：
           - readyState >= 3 (HAVE_FUTURE_DATA) 或 4 (HAVE_ENOUGH_DATA)
           - duration > 0 (有效影片長度)
           - error == null (無載入錯誤)
        3. 在指定 timeout 內循環檢查，直到滿足條件或超時
        
        Args:
            timeout: 等待超時時間 (秒)，默認為 20 秒
        
        Returns:
            bool: 影片是否載入成功且可播放
        """
        self.logger.info(f"[NX_CLOUD_WEB] [VIDEO] 開始檢查影片載入狀態 (Timeout: {timeout}s)...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [ERROR] WebDriver 未初始化")
            return False
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 1. 尋找 <video> 元素
                # 如果頁面有多個 video，可能需要更精確的 XPath，這裡預設找第一個
                video_element = self.driver.find_element(By.TAG_NAME, "video")
                
                # 2. 執行 JavaScript 檢查內部狀態
                # readyState >= 3: HAVE_FUTURE_DATA (可以開始播放)
                # readyState >= 4: HAVE_ENOUGH_DATA (有足夠資料可以播放)
                # duration > 0: 有效長度
                # error == null: 無錯誤
                video_status = self.driver.execute_script("""
                    var v = arguments[0];
                    return {
                        readyState: v.readyState,
                        duration: v.duration,
                        error: v.error,
                        paused: v.paused,
                        src: v.currentSrc
                    };
                """, video_element)
                
                # 3. [關鍵修改] 安全獲取數值類型
                ready_state = video_status.get('readyState', 0)
                
                # 安全處理 duration: 如果是 None 則設為 0.0
                raw_duration = video_status.get('duration')
                if raw_duration is None:
                    duration = 0.0
                else:
                    try:
                        duration = float(raw_duration)
                        # 處理 Infinity 或 NaN 的情況
                        if not (duration >= 0 and duration != float('inf')):
                            duration = 0.0
                    except (ValueError, TypeError):
                        duration = 0.0
                
                error = video_status.get('error')
                paused = video_status.get('paused', True)
                src = video_status.get('src', '')
                
                # 記錄當前狀態（確保 duration 是數字類型，可以安全格式化）
                duration_str = f"{duration:.2f}s" if duration != float('inf') else "Infinity"
                self.logger.info(f"[NX_CLOUD_WEB] [VIDEO] 當前狀態: ReadyState={ready_state}, Duration={duration_str}, Paused={paused}, Src={src[:50]}...")
                
                # 檢查是否有錯誤
                if error:
                    error_msg = error.get('message', 'Unknown error') if isinstance(error, dict) else str(error)
                    self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] 影片載入錯誤: {error_msg}")
                    return False
                
                # 檢查是否已準備好播放
                # readyState >= 3 表示至少有未來資料可以播放（HAVE_FUTURE_DATA 或 HAVE_ENOUGH_DATA）
                # 對於直播流，duration 可能是 0 或 Infinity，所以主要依賴 readyState 判斷
                is_ready = ready_state >= 3
                
                if is_ready:
                    self.logger.info(f"[NX_CLOUD_WEB] [OK] 影片載入成功且可播放! (ReadyState: {ready_state}, Duration: {duration_str})")
                    return True
                
                # 還沒準備好，繼續等待
                elapsed = time.time() - start_time
                # 詳細記錄為什麼不滿足條件
                reasons = []
                if ready_state < 3:
                    reasons.append(f"ReadyState={ready_state} < 3")
                reason_str = ", ".join(reasons) if reasons else "未知原因"
                self.logger.info(f"[NX_CLOUD_WEB] [VIDEO] [WAIT] 影片載入中... (已等待: {elapsed:.1f}s, 原因: {reason_str})")
                
            except NoSuchElementException:
                # 可能是還沒 render 出來
                elapsed = time.time() - start_time
                self.logger.info(f"[NX_CLOUD_WEB] [VIDEO] [WAIT] 尚未找到 video 元素 (已等待: {elapsed:.1f}s)")
                
                # 每 5 秒記錄一次頁面狀態
                if int(elapsed) % 5 == 0:
                    try:
                        current_url = self.driver.current_url
                        self.logger.info(f"[NX_CLOUD_WEB] [VIDEO] [WAIT] 當前 URL: {current_url}")
                    except:
                        pass
            except Exception as e:
                # 其他異常
                elapsed = time.time() - start_time
                self.logger.debug(f"[NX_CLOUD_WEB] [VIDEO] [WAIT] 檢查影片狀態時發生異常: {e} (已等待: {elapsed:.1f}s)")
            
            time.sleep(1.0)
        
        # 超時 - 進行詳細診斷
        self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [TIMEOUT] 等待影片載入超時 ({timeout}s)")
        
        # 🎯 診斷：檢查頁面上是否有 video 元素
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 當前 URL: {current_url}")
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 頁面標題: {page_title}")
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 無法獲取頁面信息: {e}")
        
        # 🎯 診斷：檢查頁面上是否有 video 元素
        try:
            all_videos = self.driver.find_elements(By.TAG_NAME, "video")
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 頁面上找到 {len(all_videos)} 個 <video> 元素")
            
            if len(all_videos) > 0:
                # 如果有 video 元素，檢查它們的狀態
                for i, video in enumerate(all_videos):
                    try:
                        video_status = self.driver.execute_script("""
                            var v = arguments[0];
                            return {
                                readyState: v.readyState,
                                duration: v.duration,
                                error: v.error ? (v.error.message || v.error.code || 'Unknown error') : null,
                                paused: v.paused,
                                src: v.currentSrc || v.src || '',
                                networkState: v.networkState,
                                videoWidth: v.videoWidth,
                                videoHeight: v.videoHeight
                            };
                        """, video)
                        
                        ready_state = video_status.get('readyState', 0)
                        
                        # 安全處理 duration
                        raw_duration = video_status.get('duration')
                        if raw_duration is None:
                            duration = 0.0
                        else:
                            try:
                                duration = float(raw_duration)
                                if not (duration >= 0 and duration != float('inf')):
                                    duration = 0.0
                            except (ValueError, TypeError):
                                duration = 0.0
                        
                        error = video_status.get('error')
                        paused = video_status.get('paused', True)
                        src = video_status.get('src', '')
                        network_state = video_status.get('networkState', -1)
                        video_width = video_status.get('videoWidth', 0)
                        video_height = video_status.get('videoHeight', 0)
                        
                        self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] Video {i+1} 詳細狀態:")
                        self.logger.error(f"   - ReadyState: {ready_state} (0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA)")
                        duration_str = f"{duration:.2f}s" if duration != float('inf') else "Infinity"
                        self.logger.error(f"   - Duration: {duration_str}")
                        self.logger.error(f"   - NetworkState: {network_state} (0=EMPTY, 1=IDLE, 2=LOADING, 3=NO_SOURCE)")
                        self.logger.error(f"   - VideoSize: {video_width}x{video_height}")
                        self.logger.error(f"   - Paused: {paused}")
                        self.logger.error(f"   - Src: {src[:100]}...")
                        if error:
                            error_msg = error.get('message', 'Unknown error') if isinstance(error, dict) else str(error)
                            self.logger.error(f"   - Error: {error_msg}")
                        else:
                            self.logger.error(f"   - Error: None")
                        
                        # 檢查為什麼不滿足條件
                        if ready_state < 3:
                            self.logger.error(f"   - ❌ ReadyState 不足: {ready_state} < 3 (需要至少 HAVE_FUTURE_DATA)")
                        if error:
                            self.logger.error(f"   - ❌ 有錯誤: {error_msg if error else 'Unknown'}")
                    except Exception as video_e:
                        self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 檢查 video {i+1} 時發生錯誤: {video_e}")
            else:
                # 沒有找到 video 元素
                self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] ❌ 頁面上沒有找到 <video> 元素")
                
                # 🎯 診斷：嘗試查找可能的視頻相關元素
                try:
                    # 查找可能的視頻容器
                    video_containers = self.driver.find_elements(By.XPATH, "//*[contains(@class,'video') or contains(@class,'player') or contains(@class,'playback')]")
                    self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 找到 {len(video_containers)} 個可能的視頻容器元素")
                    for i, container in enumerate(video_containers[:5]):  # 只顯示前5個
                        try:
                            class_attr = container.get_attribute('class')
                            tag_name = container.tag_name
                            self.logger.error(f"   - 容器 {i+1}: Tag={tag_name}, Class='{class_attr}'")
                        except:
                            pass
                except Exception as container_e:
                    self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 查找視頻容器時發生錯誤: {container_e}")
                
                # 🎯 診斷：檢查頁面源碼中是否有 video 相關內容
                try:
                    page_source = self.driver.page_source
                    if '<video' in page_source.lower():
                        self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 頁面源碼中包含 '<video' 標籤，但 Selenium 無法找到元素（可能是動態加載）")
                    else:
                        self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 頁面源碼中沒有找到 '<video' 標籤")
                except Exception as source_e:
                    self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 無法檢查頁面源碼: {source_e}")
                
        except Exception as debug_e:
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 診斷時發生錯誤: {debug_e}")
            import traceback
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 錯誤詳情: {traceback.format_exc()[:500]}")
        
        # 🎯 診斷：截圖保存（如果可能）
        try:
            screenshot_path = os.path.join(EnvConfig.LOG_PATH, f"video_timeout_{int(time.time())}.png")
            self.driver.save_screenshot(screenshot_path)
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 超時截圖已保存: {screenshot_path}")
        except Exception as screenshot_e:
            self.logger.error(f"[NX_CLOUD_WEB] [VIDEO] [DEBUG] 保存截圖失敗: {screenshot_e}")
        
        return False
    
    def close_webdriver(self):
        """
        關閉 WebDriver 和瀏覽器視窗（強制清理版）
        
        功能：
        1. 嘗試透過 Selenium 標準的 quit() 斷開連接
        2. 針對 Debug 模式，執行 taskkill 強制關閉 Chrome 進程，確保視窗不殘留
        
        注意：
        - 使用 debuggerAddress 連接 Chrome 後，driver.quit() 只會斷開連接，不會真正關閉瀏覽器視窗
        - 因此需要在 quit() 之後執行系統級的 taskkill 來強制關閉 Chrome 進程
        """
        if not self.logger:
            try:
                from toolkit.logger import get_logger
                self.logger = get_logger(self.__class__.__name__)
            except:
                import logging
                self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("[NX_CLOUD_WEB] [CLOSE] 開始關閉瀏覽器與清理環境...")
        
        # 1. 先嘗試正規的 Selenium 關閉（這在 Debug 模式下通常只會 Detach）
        try:
            if hasattr(self, 'browser') and self.browser:
                try:
                    self.browser.quit()
                    self.logger.info("[NX_CLOUD_WEB] [CLOSE] WebDriver 連接已斷開（通過 Browser）")
                except Exception as browser_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [CLOSE] Browser.quit() 發生異常: {browser_e}")
            elif self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("[NX_CLOUD_WEB] [CLOSE] WebDriver 連接已斷開（通過 Driver）")
                except Exception as driver_e:
                    self.logger.warning(f"[NX_CLOUD_WEB] [CLOSE] Driver.quit() 發生異常: {driver_e}")
            else:
                self.logger.warning("[NX_CLOUD_WEB] [CLOSE] 沒有找到可關閉的 WebDriver 實例")
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [CLOSE] WebDriver quit() 發生異常（不影響後續強制清理）: {e}")
        finally:
            # 清除引用
            if hasattr(self, 'browser'):
                self.browser = None
            self.driver = None
            if hasattr(self, 'wait'):
                self.wait = None
            
            # 2. [關鍵修正] 執行系統級強制關閉
            # 因為在 debuggerAddress 模式下，quit() 不會關閉視窗，必須手動殺進程
            self.logger.info("[NX_CLOUD_WEB] [CLOSE] 執行系統級強制清理 (taskkill chrome)...")
            try:
                import os
                import subprocess
                import time
                
                if os.name == 'nt':  # Windows
                    # 🎯 策略 1: 使用 /t 參數終止進程樹（更強力）
                    # /f: 強制終止
                    # /t: 終止指定的進程及其所有子進程
                    # /im: 指定映像名稱
                    self.logger.info("[NX_CLOUD_WEB] [CLOSE] 嘗試終止 Chrome 進程樹...")
                    result1 = subprocess.run(
                        ["taskkill", "/f", "/t", "/im", "chrome.exe"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    # 等待一下，讓進程有時間關閉
                    time.sleep(1.0)
                    
                    # 🎯 策略 2: 如果第一次失敗，再嘗試一次（可能是進程正在關閉中）
                    if result1.returncode != 0:
                        self.logger.info("[NX_CLOUD_WEB] [CLOSE] 第一次嘗試失敗，再次嘗試...")
                        time.sleep(0.5)
                        result2 = subprocess.run(
                            ["taskkill", "/f", "/t", "/im", "chrome.exe"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result2.returncode == 0:
                            self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程已強制終止（第二次嘗試成功）")
                        else:
                            # 檢查是否是因為進程不存在
                            if "找不到進程" in result2.stderr or "not found" in result2.stderr.lower() or "找不到" in result2.stderr:
                                self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程不存在（可能已關閉）")
                            else:
                                self.logger.warning(f"[NX_CLOUD_WEB] [CLOSE] ⚠️ 第二次嘗試也失敗: {result2.stderr}")
                    else:
                        self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程已強制終止（第一次嘗試成功）")
                    
                    # 🎯 策略 3: 驗證 Chrome 進程是否真的被關閉
                    time.sleep(0.5)
                    check_result = subprocess.run(
                        ["tasklist", "/fi", "imagename eq chrome.exe"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if "chrome.exe" in check_result.stdout:
                        # 還有 Chrome 進程存在，嘗試更強力的方法
                        self.logger.warning("[NX_CLOUD_WEB] [CLOSE] ⚠️ 仍有 Chrome 進程存在，嘗試更強力的關閉方法...")
                        # 使用 os.system 作為最後手段（可能會更強力）
                        os.system("taskkill /f /t /im chrome.exe >nul 2>&1")
                        time.sleep(1.0)
                        # 再次檢查
                        check_result2 = subprocess.run(
                            ["tasklist", "/fi", "imagename eq chrome.exe"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if "chrome.exe" in check_result2.stdout:
                            self.logger.error("[NX_CLOUD_WEB] [CLOSE] ❌ Chrome 進程仍然存在，可能需要手動關閉")
                        else:
                            self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程已完全關閉（使用 os.system）")
                    else:
                        self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ 驗證：Chrome 進程已完全關閉")
                        
                else:  # Linux/Mac
                    # Linux/Mac 使用 pkill，並嘗試多次
                    result1 = subprocess.run(
                        ["pkill", "-9", "-f", "chrome"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    time.sleep(1.0)
                    if result1.returncode != 0:
                        # 再試一次
                        result2 = subprocess.run(
                            ["pkill", "-9", "-f", "chrome"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result2.returncode == 0:
                            self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程已強制終止（第二次嘗試成功）")
                        else:
                            self.logger.warning(f"[NX_CLOUD_WEB] [CLOSE] ⚠️ pkill 返回非 0（可能進程不存在）")
                    else:
                        self.logger.info("[NX_CLOUD_WEB] [CLOSE] ✅ Chrome 進程已強制終止（第一次嘗試成功）")
                        
            except subprocess.TimeoutExpired:
                self.logger.error("[NX_CLOUD_WEB] [CLOSE] ❌ 強制清理超時")
            except Exception as kill_e:
                self.logger.error(f"[NX_CLOUD_WEB] [CLOSE] ❌ 強制清理失敗: {kill_e}")
                import traceback
                self.logger.error(f"[NX_CLOUD_WEB] [CLOSE] 錯誤詳情: {traceback.format_exc()}")

    # ==================== Case 2-2: Web Admin 操作方法 ====================
    # 以下方法用於 Nx Cloud 或 Web Admin 頁面的操作
    
    def login_via_nx_cloud(self, email: str = None, password: str = None) -> bool:
        """
        通過 Nx Cloud OAuth 登錄
        
        方案 A（優先）：使用 Case 2-1 保存的 Nx Cloud URL
        方案 B（備用）：使用 localhost:7001 Web Admin
        
        完整流程：
        1. 嘗試讀取 Case 2-1 保存的 URL，如果失敗則使用 localhost:7001
        2. 點擊「登入 Nx Cloud」按鈕（如果存在）
        3. 接受風險並繼續（如果存在）
        4. 輸入郵箱 → 下一步 → 輸入密碼 → 登錄
        
        Args:
            email: 郵箱（如果為 None，使用 config 中的值）
            password: 密碼（如果為 None，使用 config 中的值）
            
        Returns:
            bool: 登錄是否成功
        """
        from config import LocatorConfig
        
        email = email or EnvConfig.NX_CLOUD_EMAIL
        password = password or EnvConfig.NX_CLOUD_PASSWORD
        
        self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] 開始 Nx Cloud OAuth 登錄流程...")
        self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] 使用帳號: {email}")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [LOGIN] WebDriver 未初始化")
            return False
        
        try:
            # Step 1: 嘗試讀取 Case 2-1 保存的 URL（方案 A）
            target_url = None
            url_file = os.path.join(os.path.dirname(__file__), '..', '..', '.nx_cloud_url')
            
            try:
                if os.path.exists(url_file):
                    with open(url_file, 'r') as f:
                        saved_url = f.read().strip()
                    if saved_url and saved_url.startswith('http'):
                        target_url = saved_url
                        self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] ✅ 使用 Case 2-1 保存的 URL: {target_url}")
                    else:
                        self.logger.warning(f"[NX_CLOUD_WEB] [LOGIN] URL 文件內容無效: {saved_url}")
                else:
                    self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] URL 文件不存在: {url_file}")
            except Exception as e:
                self.logger.warning(f"[NX_CLOUD_WEB] [LOGIN] 讀取 URL 文件失敗: {e}")
            
            # 如果沒有有效的 URL，使用備用方案（localhost:7001）
            if not target_url:
                target_url = 'https://localhost:7001'
                self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] 使用備用方案: {target_url}")
            
            self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] Step 1: 導航到 {target_url}...")
            self.driver.get(target_url)
            time.sleep(3)
            
            # Step 1.5: 自動置頂瀏覽器視窗（強力模式）
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 1.5: 自動置頂瀏覽器視窗（強力模式）...")
            try:
                import pygetwindow as gw
                import win32gui
                import win32con
                import win32process
                
                # 方法 1: 使用 pygetwindow 查找 Chrome 視窗
                chrome_windows = gw.getWindowsWithTitle('Chrome')
                if chrome_windows:
                    for chrome_win in chrome_windows:
                        try:
                            hwnd = chrome_win._hWnd
                            
                            # 🎯 強力置頂序列
                            # 1. 先恢復視窗（如果被最小化）
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            time.sleep(0.1)
                            
                            # 2. 最大化視窗
                            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                            time.sleep(0.1)
                            
                            # 3. 強制置頂（多次嘗試）
                            for _ in range(3):
                                win32gui.SetForegroundWindow(hwnd)
                                win32gui.BringWindowToTop(hwnd)
                                # 使用 SetWindowPos 確保置頂
                                win32gui.SetWindowPos(
                                    hwnd,
                                    win32con.HWND_TOPMOST,  # 設為最頂層
                                    0, 0, 0, 0,
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                                )
                                time.sleep(0.05)
                            
                            # 4. 取消永久置頂（但保持在前景）
                            win32gui.SetWindowPos(
                                hwnd,
                                win32con.HWND_NOTOPMOST,  # 取消永久置頂
                                0, 0, 0, 0,
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                            )
                            
                            self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] ✅ 瀏覽器視窗已強力置頂: {chrome_win.title}")
                            break  # 只處理第一個 Chrome 視窗
                        except Exception as e:
                            self.logger.warning(f"[NX_CLOUD_WEB] [LOGIN] 置頂視窗失敗（嘗試下一個）: {e}")
                            continue
                else:
                    self.logger.warning("[NX_CLOUD_WEB] [LOGIN] 未找到 Chrome 視窗")
                    
            except Exception as e:
                self.logger.warning(f"[NX_CLOUD_WEB] [LOGIN] 置頂視窗失敗: {e}")
            
            # Step 1.6: 修改語言為繁體中文（在登錄前）
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 1.6: 嘗試修改語言為繁體中文...")
            self._try_change_language_to_chinese()
            
            # Step 2: 點擊右上角「登入」按鈕
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 2: 點擊右上角「登入」按鈕...")
            login_btn_clicked = False
            
            # 嘗試多個 XPath 找到登入按鈕
            login_btn_xpaths = [
                LocatorConfig.WEB_NX_CLOUD_LOGIN_BTN_XPATH,  # //a[@href='/authorize']
                "//a[contains(@class, 'login') and contains(@class, 'nx-button')]",
                "//a[normalize-space()='登入']",
                "//a[normalize-space()='登录']",
                "//a[contains(text(), '登入')]",
            ]
            
            for xpath in login_btn_xpaths:
                try:
                    self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] 嘗試 XPath: {xpath}")
                    login_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath)))
                    if login_btn.is_displayed():
                        login_btn.click()
                        self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] ✅ 已點擊「登入」按鈕 (XPath: {xpath})")
                        login_btn_clicked = True
                        time.sleep(3)
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not login_btn_clicked:
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] 未找到「登入」按鈕，可能已登錄")
            
            # Step 3: 點擊「接受風險並繼續」
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 3: 點擊「接受風險並繼續」...")
            try:
                accept_btn = self.driver.find_element(By.XPATH, LocatorConfig.WEB_ACCEPT_RISK_BTN_XPATH)
                if accept_btn.is_displayed():
                    accept_btn.click()
                    self.logger.info("[NX_CLOUD_WEB] [LOGIN] ✅ 已點擊「接受風險並繼續」")
                    time.sleep(3)
            except NoSuchElementException:
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] 未找到「接受風險」按鈕，跳過")
            
            # Step 4: 輸入郵箱
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 4: 輸入郵箱...")
            try:
                email_input = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, LocatorConfig.WEB_EMAIL_INPUT_XPATH)))
                email_input.clear()
                email_input.send_keys(email)
                self.logger.info(f"[NX_CLOUD_WEB] [LOGIN] ✅ 已輸入郵箱: {email}")
                time.sleep(1)
            except TimeoutException:
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] 未找到郵箱輸入框，可能已登錄")
                return self._check_login_success()
            
            # Step 5: 點擊下一步
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 5: 點擊下一步...")
            try:
                next_btn = self.driver.find_element(By.XPATH, LocatorConfig.WEB_NEXT_BTN_XPATH)
                next_btn.click()
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] ✅ 已點擊下一步")
                time.sleep(3)
            except NoSuchElementException:
                self.logger.warning("[NX_CLOUD_WEB] [LOGIN] 未找到下一步按鈕")
            
            # Step 6: 輸入密碼
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 6: 輸入密碼...")
            try:
                pwd_input = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, LocatorConfig.WEB_PASSWORD_INPUT_XPATH)))
                pwd_input.send_keys(password)
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] ✅ 已輸入密碼")
                time.sleep(1)
            except TimeoutException:
                self.logger.warning("[NX_CLOUD_WEB] [LOGIN] 未找到密碼輸入框")
            
            # Step 7: 點擊登錄
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] Step 7: 點擊登錄...")
            try:
                login_btn = self.driver.find_element(By.XPATH, LocatorConfig.WEB_LOGIN_SUBMIT_BTN_XPATH)
                login_btn.click()
                self.logger.info("[NX_CLOUD_WEB] [LOGIN] ✅ 已點擊登錄")
                time.sleep(8)
            except NoSuchElementException:
                self.logger.warning("[NX_CLOUD_WEB] [LOGIN] 未找到登錄按鈕")
            
            # 驗證登錄結果
            return self._check_login_success()
            
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [LOGIN] ❌ 登錄失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _try_change_language_to_chinese(self) -> bool:
        """
        嘗試將網頁語言修改為繁體中文
        
        嘗試多種語言選擇器定位方式：
        1. 右上角語言下拉選單
        2. 設定頁面中的語言選項
        
        Returns:
            bool: 修改是否成功
        """
        from config import LocatorConfig
        
        self.logger.info("[NX_CLOUD_WEB] [LANG] 嘗試修改語言為繁體中文...")
        
        if not self.driver:
            return False
        
        try:
            # 使用配置中的語言選擇器 XPath
            language_selectors = LocatorConfig.WEB_LANGUAGE_DROPDOWN_XPATHS
            
            for selector in language_selectors:
                try:
                    lang_btn = self.driver.find_element(By.XPATH, selector)
                    if lang_btn.is_displayed():
                        lang_btn.click()
                        self.logger.info(f"[NX_CLOUD_WEB] [LANG] 點擊語言選擇器: {selector}")
                        time.sleep(1)
                        
                        # 使用配置中的繁體中文選項 XPath
                        chinese_options = LocatorConfig.WEB_CHINESE_OPTION_XPATHS
                        
                        for chinese_selector in chinese_options:
                            try:
                                chinese_btn = self.driver.find_element(By.XPATH, chinese_selector)
                                if chinese_btn.is_displayed():
                                    chinese_btn.click()
                                    self.logger.info(f"[NX_CLOUD_WEB] [LANG] ✅ 已選擇繁體中文: {chinese_selector}")
                                    time.sleep(2)
                                    return True
                            except NoSuchElementException:
                                continue
                        
                        # 如果下拉選單打開但沒找到繁體中文，點擊其他地方關閉
                        self.logger.warning("[NX_CLOUD_WEB] [LANG] 下拉選單已打開但未找到繁體中文選項")
                        try:
                            self.driver.find_element(By.TAG_NAME, 'body').click()
                        except:
                            pass
                        
                except NoSuchElementException:
                    continue
            
            self.logger.info("[NX_CLOUD_WEB] [LANG] 未找到語言選擇器，跳過語言修改")
            return False
            
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD_WEB] [LANG] 修改語言失敗: {e}")
            return False
    
    def _check_login_success(self) -> bool:
        """
        檢查是否登錄成功
        
        Returns:
            bool: 是否登錄成功
        """
        try:
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            if '登录' in body_text or 'login' in body_text.lower() or '邮箱' in body_text:
                self.logger.warning("[NX_CLOUD_WEB] [LOGIN] ⚠️ 仍在登錄頁面")
                return False
            self.logger.info("[NX_CLOUD_WEB] [LOGIN] ✅ 登錄成功")
            return True
        except:
            return False
    
    def click_browse_tab(self, max_wait: int = 30) -> bool:
        """
        點擊「瀏覽 / View / 查看」分頁 Tab
        
        支持多語言：View (英文) / 瀏覽 (繁體) / 查看 (簡體)
        登錄後需要等待頁面完全載入，View 頁籤才會出現
        
        Args:
            max_wait: 最大等待時間（秒）
        
        Returns:
            bool: 點擊是否成功
        """
        from config import LocatorConfig
        
        self.logger.info(f"[NX_CLOUD_WEB] [BROWSE] 等待並點擊「View / 瀏覽 / 查看」分頁（最多等待 {max_wait} 秒）...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [BROWSE] WebDriver 未初始化")
            return False
        
        # 嘗試多種 XPath 定位策略（優先使用 href，最可靠）
        xpaths_to_try = [
            # 策略 1: 使用 href 包含 /view（最可靠，不依賴語言）
            "//a[contains(@href, '/view')]",
            "//div[@class='menu-items']//a[contains(@href, '/view')]",
            # 策略 2: 使用 class 和 href
            "//a[contains(@class, 'inner-menu-item') and contains(@href, '/view')]",
            # 策略 3: 使用文字匹配（多語言）
            "//div[@class='menu-items']//a[normalize-space()='View']",
            "//div[@class='menu-items']//a[normalize-space()='瀏覽']",
            "//div[@class='menu-items']//a[normalize-space()='查看']",
            # 策略 4: 使用 class 和文字
            "//a[contains(@class, 'inner-menu-item') and (contains(text(), 'View') or contains(text(), '瀏覽') or contains(text(), '查看'))]",
            # 策略 5: 原有的配置 XPath
            LocatorConfig.WEB_BROWSE_TAB_XPATH,
            LocatorConfig.WEB_BROWSE_TAB_FALLBACK_XPATH,
        ]
        
        # 智能等待：每秒檢查一次，直到找到 View 頁籤或超時
        start_time = time.time()
        while time.time() - start_time < max_wait:
            for xpath in xpaths_to_try:
                try:
                    browse_tab = self.driver.find_element(By.XPATH, xpath)
                    if browse_tab.is_displayed():
                        self.logger.info(f"[NX_CLOUD_WEB] [BROWSE] ✅ 找到 View 頁籤: '{browse_tab.text.strip()}' (等待 {int(time.time() - start_time)} 秒)")
                        browse_tab.click()
                        self.logger.info("[NX_CLOUD_WEB] [BROWSE] ✅ 已點擊「View / 瀏覽」")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
                except Exception as e:
                    continue
            
            # 未找到，等待 1 秒後重試
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0 and elapsed > 0:
                self.logger.info(f"[NX_CLOUD_WEB] [BROWSE] ⏳ 等待 View 頁籤出現... ({elapsed}/{max_wait} 秒)")
            time.sleep(1)
        
        # 超時，所有策略都失敗，列出頁面上所有可能的選項
        self.logger.error(f"[NX_CLOUD_WEB] [BROWSE] ❌ 等待 {max_wait} 秒後仍未找到 View 頁籤")
        try:
            menu_items = self.driver.find_elements(By.XPATH, "//div[@class='menu-items']//a")
            if menu_items:
                self.logger.info(f"[NX_CLOUD_WEB] [BROWSE] 頁面上的選項卡: {[item.text.strip() for item in menu_items]}")
            else:
                self.logger.info("[NX_CLOUD_WEB] [BROWSE] 頁面上沒有找到任何選項卡")
        except:
            pass
        
        return False
    
    def click_server_item(self, max_wait: int = 15) -> bool:
        """
        點擊 Server 選項卡（展開 Server 以顯示攝影機列表）
        
        Args:
            max_wait: 最大等待時間（秒）
        
        Returns:
            bool: 點擊是否成功
        """
        from config import LocatorConfig
        
        self.logger.info(f"[NX_CLOUD_WEB] [SERVER] 點擊 Server 選項卡（最多等待 {max_wait} 秒）...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [SERVER] WebDriver 未初始化")
            return False
        
        # 多策略 XPath（根據實際 DOM 結構）
        xpaths_to_try = [
            # 策略 1: 精確匹配 server-name/span（優先）
            "//div[@class='server-name']/span[contains(@class, 'name')]",
            # 策略 2: 配置中的 XPath
            LocatorConfig.WEB_SERVER_XPATH,
            LocatorConfig.WEB_SERVER_FALLBACK_XPATH,
            # 策略 3: 根據文字找
            LocatorConfig.WEB_SERVER_TEXT_XPATH,
            # 策略 4: 更泛用的匹配
            "//div[contains(@class, 'server-name')]//span",
            "//span[contains(@class, 'name') and contains(@class, 'Online')]",
        ]
        
        # 智能等待
        start_time = time.time()
        while time.time() - start_time < max_wait:
            for xpath in xpaths_to_try:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            self.logger.info(f"[NX_CLOUD_WEB] [SERVER] ✅ 找到 Server: '{elem.text.strip()[:30]}' (等待 {int(time.time() - start_time)} 秒)")
                            elem.click()
                            self.logger.info("[NX_CLOUD_WEB] [SERVER] ✅ 已點擊 Server")
                            time.sleep(2)  # 等待展開動畫
                            return True
                except Exception:
                    continue
            
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0 and elapsed > 0:
                self.logger.info(f"[NX_CLOUD_WEB] [SERVER] ⏳ 等待 Server 出現... ({elapsed}/{max_wait} 秒)")
            time.sleep(1)
        
        self.logger.error(f"[NX_CLOUD_WEB] [SERVER] ❌ 等待 {max_wait} 秒後仍未找到 Server")
        return False
    
    def click_camera_item(self, max_wait: int = 20) -> bool:
        """
        點擊攝影機項目
        
        Args:
            max_wait: 最大等待時間（秒）
        
        Returns:
            bool: 點擊是否成功
        """
        from config import LocatorConfig
        
        self.logger.info(f"[NX_CLOUD_WEB] [CAMERA] 點擊攝影機（最多等待 {max_wait} 秒）...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [CAMERA] WebDriver 未初始化")
            return False
        
        # 多策略 XPath（根據實際 DOM 結構）
        # 注意：點擊 Server 後，cameras 區域需要時間展開
        xpaths_to_try = [
            # 策略 1: 使用 contains 匹配（更靈活，處理多個 class）
            "//div[contains(@class, 'cameras')]//div[contains(@class, 'preview')]",
            # 策略 2: 精確匹配
            "//div[@class='cameras ng-star-inserted']/div[@class='preview']",
            # 策略 3: 配置中的 XPath
            LocatorConfig.WEB_CAMERA_XPATH,
            LocatorConfig.WEB_CAMERA_FALLBACK_XPATH,
            # 策略 4: 更泛用的匹配
            "//div[@class='preview']",
            "//div[contains(@class, 'preview') and ancestor::div[contains(@class, 'cameras')]]",
            # 策略 5: 根據文字找（備選）
            LocatorConfig.WEB_CAMERA_TEXT_XPATH,
        ]
        
        # 智能等待
        start_time = time.time()
        debug_logged = False
        while time.time() - start_time < max_wait:
            for xpath in xpaths_to_try:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            camera_name = elem.text.strip()[:40] if elem.text else "camera"
                            self.logger.info(f"[NX_CLOUD_WEB] [CAMERA] ✅ 找到攝影機: '{camera_name}' (等待 {int(time.time() - start_time)} 秒, XPath: {xpath[:50]})")
                            elem.click()
                            self.logger.info("[NX_CLOUD_WEB] [CAMERA] ✅ 已點擊攝影機")
                            time.sleep(3)  # 等待影片加載
                            return True
                except Exception:
                    continue
            
            elapsed = int(time.time() - start_time)
            
            # 每 5 秒輸出調試信息
            if elapsed % 5 == 0 and elapsed > 0:
                self.logger.info(f"[NX_CLOUD_WEB] [CAMERA] ⏳ 等待攝影機出現... ({elapsed}/{max_wait} 秒)")
                # 輸出頁面上的所有 div class 包含 cameras 或 preview 的元素（僅一次）
                if not debug_logged:
                    try:
                        cameras_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cameras')]")
                        preview_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'preview')]")
                        self.logger.info(f"[NX_CLOUD_WEB] [CAMERA] [DEBUG] 找到 {len(cameras_divs)} 個 cameras div, {len(preview_divs)} 個 preview div")
                        debug_logged = True
                    except:
                        pass
            time.sleep(1)
        
        self.logger.error(f"[NX_CLOUD_WEB] [CAMERA] ❌ 等待 {max_wait} 秒後仍未找到攝影機")
        return False
    
    def click_timeline_green_block(self, max_wait: int = 15) -> bool:
        """
        點擊進度條中的綠色區塊（錄影區段）開始播放
        
        Args:
            max_wait: 最大等待時間（秒）
        
        Returns:
            bool: 點擊是否成功
        """
        from selenium.webdriver.common.action_chains import ActionChains
        
        self.logger.info(f"[NX_CLOUD_WEB] [TIMELINE] 點擊進度條綠色區塊（最多等待 {max_wait} 秒）...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [TIMELINE] WebDriver 未初始化")
            return False
        
        # 多策略 XPath（根據截圖中的 DOM 結構）
        xpaths_to_try = [
            # 策略 1: nx-timeline-selection（綠色選區）
            "//nx-timeline-selection",
            # 策略 2: 選區內的可拖動元素
            "//nx-timeline-selection//div[contains(@class, 'selected-range')]",
            # 策略 3: 時間線區域
            "//nx-timeline//div[contains(@class, 'timeline')]",
            "//div[contains(@class, 'timeline-selection')]",
            # 策略 4: canvas 元素
            "//nx-timeline//canvas",
        ]
        
        # 智能等待
        start_time = time.time()
        while time.time() - start_time < max_wait:
            for xpath in xpaths_to_try:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            self.logger.info(f"[NX_CLOUD_WEB] [TIMELINE] ✅ 找到進度條元素 (XPath: {xpath[:40]})")
                            
                            # 使用 ActionChains 點擊元素中心
                            actions = ActionChains(self.driver)
                            actions.move_to_element(elem).click().perform()
                            
                            self.logger.info("[NX_CLOUD_WEB] [TIMELINE] ✅ 已點擊進度條綠色區塊")
                            time.sleep(2)  # 等待播放開始
                            return True
                except Exception as e:
                    continue
            
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0 and elapsed > 0:
                self.logger.info(f"[NX_CLOUD_WEB] [TIMELINE] ⏳ 等待進度條出現... ({elapsed}/{max_wait} 秒)")
            time.sleep(1)
        
        self.logger.warning(f"[NX_CLOUD_WEB] [TIMELINE] ⚠️ 等待 {max_wait} 秒後仍未找到進度條")
        return False
    
    def click_timeline(self) -> bool:
        """
        點擊錄影進度條 (Timeline Canvas)
        
        Returns:
            bool: 點擊是否成功
        """
        from config import LocatorConfig
        from selenium.webdriver.common.action_chains import ActionChains
        
        self.logger.info("[NX_CLOUD_WEB] [TIMELINE] 點擊錄影進度條...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [TIMELINE] WebDriver 未初始化")
            return False
        
        try:
            timeline = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, LocatorConfig.WEB_TIMELINE_XPATH)))
            
            size = timeline.size
            self.logger.info(f"[NX_CLOUD_WEB] [TIMELINE] 找到進度條，大小: {size['width']} x {size['height']}")
            
            # 使用 ActionChains 點擊 canvas 中心
            actions = ActionChains(self.driver)
            actions.move_to_element(timeline).click().perform()
            
            self.logger.info("[NX_CLOUD_WEB] [TIMELINE] ✅ 已點擊錄影進度條")
            time.sleep(3)
            return True
            
        except TimeoutException:
            self.logger.info("[NX_CLOUD_WEB] [TIMELINE] 精確 XPath 失敗，嘗試 fallback...")
            try:
                timeline = self.driver.find_element(By.XPATH, LocatorConfig.WEB_TIMELINE_FALLBACK_XPATH)
                actions = ActionChains(self.driver)
                actions.move_to_element(timeline).click().perform()
                self.logger.info("[NX_CLOUD_WEB] [TIMELINE] ✅ 已點擊錄影進度條 (fallback)")
                time.sleep(3)
                return True
            except Exception:
                self.logger.error("[NX_CLOUD_WEB] [TIMELINE] ❌ 找不到錄影進度條")
                return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD_WEB] [TIMELINE] ❌ 點擊失敗: {e}")
            return False
    
    def click_pause_button(self, max_wait: int = 10) -> bool:
        """
        點擊暫停按鈕
        
        Args:
            max_wait: 最大等待時間（秒）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[NX_CLOUD_WEB] [PAUSE] 點擊暫停按鈕（最多等待 {max_wait} 秒）...")
        
        if not self.driver:
            self.logger.error("[NX_CLOUD_WEB] [PAUSE] WebDriver 未初始化")
            return False
        
        # 多策略 XPath
        xpaths_to_try = [
            # 策略 1: 播放控制區域
            "//nx-playback-controls",
            "//nx-playback-controls//button[contains(@class, 'pause')]",
            "//nx-playback-controls//button",
            # 策略 2: 暫停按鈕
            "//button[contains(@class, 'pause')]",
            "//button[@aria-label='Pause']",
            "//*[contains(@class, 'playback')]//button",
        ]
        
        # 智能等待
        start_time = time.time()
        while time.time() - start_time < max_wait:
            for xpath in xpaths_to_try:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elements:
                        if elem.is_displayed():
                            self.logger.info(f"[NX_CLOUD_WEB] [PAUSE] ✅ 找到暫停控制 (XPath: {xpath[:40]})")
                            elem.click()
                            self.logger.info("[NX_CLOUD_WEB] [PAUSE] ✅ 已點擊暫停")
                            time.sleep(1)
                            return True
                except Exception:
                    continue
            
            elapsed = int(time.time() - start_time)
            if elapsed % 3 == 0 and elapsed > 0:
                self.logger.info(f"[NX_CLOUD_WEB] [PAUSE] ⏳ 等待暫停按鈕... ({elapsed}/{max_wait} 秒)")
            time.sleep(1)
        
        self.logger.warning(f"[NX_CLOUD_WEB] [PAUSE] ⚠️ 等待 {max_wait} 秒後仍未找到暫停按鈕")
        return False