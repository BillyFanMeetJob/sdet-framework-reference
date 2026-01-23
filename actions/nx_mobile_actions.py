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
    
    def run_login_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-1: 登錄到 Nx Cloud (對應 Excel FlowName: login_mobile)
        
        步驟：
        1. 切換到 Cloud 標籤頁
        2. 執行雲端登錄流程（輸入郵箱、密碼、點擊登入）
        3. 驗證登錄是否成功
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數（此步驟無參數）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果登錄失敗
        """
        import time
        start_time = time.time()
        self.logger.info(f"[CASE_4-1] [時間戳: {time.strftime('%H:%M:%S')}] 開始執行 Test Case 4-1: 登錄到 Nx Cloud (login_mobile)")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 從 config.py 獲取 email 和 password（因為 Excel params 為空）
            from config import EnvConfig
            email = EnvConfig.NX_CLOUD_EMAIL
            password = EnvConfig.NX_CLOUD_PASSWORD
            
            elapsed = time.time() - start_time
            self.logger.info(f"[CASE_4-1] [耗時: {elapsed:.2f}s] 使用配置中的登錄資訊: email={email}")
            
            # 步驟 1: 切換到 Cloud 標籤頁（如果存在）
            # 注意：某些 App 版本可能不需要這一步，如果找不到 Cloud 標籤則跳過
            switch_start = time.time()
            if not self.login_page.switch_to_cloud_tab():
                self.logger.warning("[CASE_4-1] ⚠️ 未找到 Cloud 標籤頁，可能不需要這一步，繼續執行...")
            switch_elapsed = time.time() - switch_start
            self.logger.info(f"[CASE_4-1] [耗時: {switch_elapsed:.2f}s] 切換到 Cloud 標籤頁完成")
            
            # 步驟 2: 執行雲端登錄流程
            login_start = time.time()
            self.logger.info(f"[CASE_4-1] [時間戳: {time.strftime('%H:%M:%S')}] 準備執行雲端登錄流程（即將點擊座標 550, 1500）...")
            if not self.login_page.perform_cloud_login(email, password):
                raise AssertionError("[ERROR] 雲端登錄失敗")
            login_elapsed = time.time() - login_start
            self.logger.info(f"[CASE_4-1] [耗時: {login_elapsed:.2f}s] 雲端登錄流程完成")
            
            total_elapsed = time.time() - start_time
            self.logger.info(f"[CASE_4-1] [總耗時: {total_elapsed:.2f}s] ✅ Test Case 4-1 完成：登錄到 Nx Cloud")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-1] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 登錄流程執行失敗: {e}")
    
    def run_select_server_and_camera_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 選擇服務器和攝像頭 (對應 Excel FlowName: select_server_and_camera)
        
        步驟：
        1. 處理首次連接彈窗（如果存在）
        2. 等待主頁面載入
        3. 選擇服務器
        4. 選擇攝像頭
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
                - server_name: 服務器名稱（例如：server_name=LAPTOP-QRJN5735）
                - camera_name: 攝像頭名稱（例如：camera_name=usb_cam）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果選擇失敗
        """
        self.logger.info("[CASE_4-2] 執行 Test Case 4-2 (部分): 選擇服務器和攝像頭 (select_server_and_camera)")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 從 kwargs 提取參數
            server_name = kwargs.get('server_name', None)
            camera_name = kwargs.get('camera_name', None)
            
            self.logger.info(f"[CASE_4-2] 參數: server_name={server_name}, camera_name={camera_name}")
            
            # 步驟 1: 處理首次連接彈窗（如果存在）
            if not self.main_page.handle_first_time_connection():
                self.logger.warning("[CASE_4-2] 處理首次連接彈窗失敗，但繼續執行...")
            
            # 步驟 2: 等待主頁面載入（若為 SurfaceView 可能偵測不到，超時時仍繼續執行第一步點擊）
            if not self.main_page.wait_for_main_page_loaded():
                self.logger.warning("[CASE_4-2] 主頁面載入偵測超時（可能為 SurfaceView），繼續執行第一步點擊 server 座標 (550, 500)...")
            
            # 步驟 3: 選擇服務器（Case 4-2 第一步：點擊 (550, 500)）
            if not self.main_page.select_server(server_name):
                raise AssertionError(f"[ERROR] 選擇服務器失敗: {server_name}")
            
            # 步驟 4: 選擇攝像頭（會自動點擊影片座標 (300, 400)）
            if not self.main_page.select_camera(camera_name):
                raise AssertionError(f"[ERROR] 選擇攝像頭失敗: {camera_name}")
            
            # 步驟 5: 驗證影片是否成功打開（通過截圖比對）
            import time
            time.sleep(1.0)  # 等待影片開始載入
            if not self.playback_page.verify_video_opened_by_screenshot_comparison(
                screenshot_interval=2.0,
                difference_threshold=0.01
            ):
                raise AssertionError("[ERROR] 影片驗證失敗：截圖比對差異未超過 1%，影片可能未成功打開")
            
            self.logger.info("✅ Test Case 4-2 (部分) 完成：選擇服務器和攝像頭，並驗證影片已打開")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-2] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 選擇服務器和攝像頭失敗: {e}")
    
    def run_playback_with_calendar_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻 (對應 Excel FlowName: playback_with_calendar)
        
        步驟：
        1. 等待播放頁面載入
        2. 使用日曆控件播放錄製的視頻
        3. 暫停視頻播放
        4. 驗證視頻已暫停
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
                - days_ago: 幾天前的錄影（例如：days_ago=17），默認為 1
        
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果播放或暫停失敗
        """
        # 從 kwargs 提取 days_ago，如果沒有則默認為 1
        days_ago_str = kwargs.get('days_ago', '1')
        try:
            days_ago = int(days_ago_str)
        except (ValueError, TypeError):
            self.logger.warning(f"[CASE_4-2] 無法解析 days_ago 參數 '{days_ago_str}'，使用默認值 1")
            days_ago = 1
        
        self.logger.info(f"[CASE_4-2] 執行 Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻 (days_ago={days_ago})")
        
        if not self.driver:
            raise AssertionError("[ERROR] Appium WebDriver 未初始化，請先初始化 WebDriver")
        
        try:
            # 步驟 1: 等待播放頁面載入
            if not self.playback_page.wait_for_playback_page_loaded():
                raise AssertionError("[ERROR] 播放頁面載入超時")
            
            # 步驟 2: 使用日曆控件播放錄製的視頻
            if not self.playback_page.play_recorded_video(days_ago):
                raise AssertionError(f"[ERROR] 播放錄製的視頻失敗 (days_ago={days_ago})")
            
            # 步驟 3: 暫停視頻播放
            if not self.playback_page.pause_playback():
                raise AssertionError("[ERROR] 暫停視頻播放失敗")
            
            # 步驟 4: 驗證視頻已暫停
            if not self.playback_page.is_playback_paused():
                raise AssertionError("[ERROR] 驗證失敗：視頻未處於暫停狀態")
            
            self.logger.info("✅ Test Case 4-2 (部分) 完成：使用日曆控件播放錄製的視頻並暫停")
            return self
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_4-2] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 播放錄製的視頻失敗: {e}")
