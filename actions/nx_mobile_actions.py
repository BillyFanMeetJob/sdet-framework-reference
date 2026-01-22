# 相對路徑: actions/nx_mobile_actions.py
"""
Nx Witness 移動端自動化操作類

處理 Test Case 4-1 和 4-2 的移動端測試流程
"""

from typing import Optional
from base.base_action import BaseAction
from pages.mobile.login_page import LoginPage
from pages.mobile.main_page import MainPage
from pages.mobile.playback_page import PlaybackPage
from toolkit.logger import get_logger


class NxMobileActions(BaseAction):
    """
    Nx Witness 移動端自動化操作類
    
    職責：
    - 協調各個 Page Object 完成測試流程
    - 處理測試步驟的執行和驗證
    """
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化移動端操作類
        
        Args:
            driver: Appium WebDriver 實例
        """
        super().__init__(browser=None)  # 移動端不使用 browser
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)
        
        # 初始化 Page Objects
        self.login_page = LoginPage(driver)
        self.main_page = MainPage(driver)
        self.playback_page = PlaybackPage(driver)
    
    def set_driver(self, driver: object) -> 'NxMobileActions':
        """
        設置 Appium WebDriver 實例
        
        Args:
            driver: Appium WebDriver 實例
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        self.driver = driver
        self.login_page.set_driver(driver)
        self.main_page.set_driver(driver)
        self.playback_page.set_driver(driver)
        return self
    
    def run_login_step(self, email: Optional[str] = None, password: Optional[str] = None, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-1: 登錄到 Nx Cloud
        
        步驟：
        1. 輸入郵箱
        2. 點擊「下一步」（如果需要）
        3. 輸入密碼
        4. 點擊登錄按鈕
        5. 驗證登錄是否成功
        
        Args:
            email: 郵箱地址，如果為 None 則使用配置中的默認值
            password: 密碼，如果為 None 則使用配置中的默認值
            **kwargs: 其他參數（用於兼容性）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果登錄失敗
        """
        self.logger.info("[CASE_4-1] 執行 Test Case 4-1: 登錄到 Nx Cloud")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 執行登錄流程
            if not self.login_page.login(email, password):
                raise AssertionError("[ERROR] 登錄失敗")
            
            self.logger.info("✅ Test Case 4-1 完成：登錄到 Nx Cloud")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-1] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 登錄流程執行失敗: {e}")
    
    def run_select_server_and_camera_step(self, server_name: Optional[str] = None, 
                                          camera_name: Optional[str] = None, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 選擇服務器和攝像頭
        
        步驟：
        1. 等待主頁面載入
        2. 選擇服務器
        3. 選擇攝像頭
        4. 導航到播放頁面
        
        Args:
            server_name: 服務器名稱，如果為 None 則使用配置中的默認值
            camera_name: 攝像頭名稱，如果為 None 則使用配置中的默認值
            **kwargs: 其他參數（用於兼容性）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果選擇失敗
        """
        self.logger.info("[CASE_4-2] 執行 Test Case 4-2 (部分): 選擇服務器和攝像頭")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 步驟 1: 等待主頁面載入
            if not self.main_page.wait_for_main_page_loaded():
                raise AssertionError("[ERROR] 主頁面載入超時")
            
            # 步驟 2: 選擇服務器
            if not self.main_page.select_server(server_name):
                raise AssertionError(f"[ERROR] 選擇服務器失敗: {server_name}")
            
            # 步驟 3: 選擇攝像頭
            if not self.main_page.select_camera(camera_name):
                raise AssertionError(f"[ERROR] 選擇攝像頭失敗: {camera_name}")
            
            # 步驟 4: 導航到播放頁面
            if not self.main_page.navigate_to_playback():
                raise AssertionError("[ERROR] 導航到播放頁面失敗")
            
            self.logger.info("✅ Test Case 4-2 (部分) 完成：選擇服務器和攝像頭")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-2] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 選擇服務器和攝像頭失敗: {e}")
    
    def run_playback_with_calendar_step(self, days_ago: int = 1, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻
        
        步驟：
        1. 等待播放頁面載入
        2. 打開日曆控件
        3. 選擇有錄影的日期
        4. 點擊播放按鈕（如果需要）
        5. 驗證視頻是否正在播放
        
        Args:
            days_ago: 幾天前的錄影（默認為 1，即昨天）
            **kwargs: 其他參數（用於兼容性）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果播放失敗
        """
        self.logger.info(f"[CASE_4-2] 執行 Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻 (days_ago={days_ago})")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 步驟 1: 等待播放頁面載入
            if not self.playback_page.wait_for_playback_page_loaded():
                raise AssertionError("[ERROR] 播放頁面載入超時")
            
            # 步驟 2-5: 播放錄製的視頻（完整流程）
            if not self.playback_page.play_recorded_video(days_ago):
                raise AssertionError(f"[ERROR] 播放錄製的視頻失敗 (days_ago={days_ago})")
            
            self.logger.info("✅ Test Case 4-2 (部分) 完成：使用日曆控件播放錄製的視頻")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-2] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 播放錄製的視頻失敗: {e}")
