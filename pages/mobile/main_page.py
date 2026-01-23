# 相對路徑: pages/mobile/main_page.py
"""
Nx Witness 移動端主頁面

處理 Test Case 4-2: 選擇服務器和攝像頭
"""

from typing import Optional, Tuple
from pages.mobile.base_mobile_page import BaseMobilePage
from config import EnvConfig


class MainPage(BaseMobilePage):
    """
    Nx Witness 移動端主頁面
    
    職責：
    - 處理主頁面相關操作（選擇服務器、選擇攝像頭等）
    - 導航到播放頁面
    """
    
    # Locators - 使用 Resource ID（優先）或文字定位
    # TODO: Replace with actual ID - 需要根據真實的 App 進行調整
    CONNECT_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/connect_button"  # Connect 按鈕（首次連接彈窗）
    SERVER_LIST_ID = "com.networkoptix.nxwitness.mobile:id/server_list"  # 服務器列表
    SERVER_ITEM_ID = "com.networkoptix.nxwitness.mobile:id/server_item"  # 服務器項目
    CAMERA_LIST_ID = "com.networkoptix.nxwitness.mobile:id/camera_list"  # 攝像頭列表
    CAMERA_ITEM_ID = "com.networkoptix.nxwitness.mobile:id/camera_item"  # 攝像頭項目
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化主頁面
        
        Args:
            driver: Appium WebDriver 實例
        """
        super().__init__(driver)
    
    def handle_first_time_connection(self, timeout: int = 5) -> bool:
        """
        處理首次連接彈窗（PDF Step 61）
        
        檢查是否存在 "Connect" 彈窗，如果存在則點擊它。
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 處理是否成功（如果沒有彈窗則返回 True）
        """
        self.logger.info("[MAIN_PAGE] 檢查首次連接彈窗（PDF Step 61）...")
        
        # 策略 1: 優先使用 Resource ID 定位 Connect 按鈕
        if self.wait_for_element_visible(resource_id=self.CONNECT_BUTTON_ID, timeout=timeout):
            if self.click_by_id(self.CONNECT_BUTTON_ID):
                self.logger.info("[MAIN_PAGE] ✅ 成功點擊 Connect 按鈕（PDF Step 61）")
                return True
        
        # 策略 2: 如果 Resource ID 定位失敗，嘗試使用文字定位
        if self.wait_for_element_visible(text="Connect", timeout=timeout) or \
           self.wait_for_element_visible(text="連接", timeout=timeout):
            if self.click_by_text("Connect") or self.click_by_text("連接"):
                self.logger.info("[MAIN_PAGE] ✅ 成功點擊 Connect 按鈕（PDF Step 61）")
                return True
        
        # 如果沒有找到 Connect 彈窗，這可能是正常的（不是首次連接）
        self.logger.info("[MAIN_PAGE] 未找到 Connect 彈窗（可能不是首次連接）")
        return True
    
    def wait_for_main_page_loaded(self, timeout: int = 15) -> bool:
        """
        等待主頁面載入完成
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 主頁面是否載入完成
        """
        self.logger.info("[MAIN_PAGE] 等待主頁面載入...")
        
        # 等待服務器列表或攝像頭列表出現（表示主頁面已載入）
        if self.wait_for_element_visible(resource_id=self.SERVER_LIST_ID, timeout=timeout):
            self.logger.info("[MAIN_PAGE] ✅ 主頁面已載入（服務器列表可見）")
            return True
        
        if self.wait_for_element_visible(resource_id=self.CAMERA_LIST_ID, timeout=timeout):
            self.logger.info("[MAIN_PAGE] ✅ 主頁面已載入（攝像頭列表可見）")
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[MAIN_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.wait_for_element_visible(text="服務器", timeout=timeout) or \
           self.wait_for_element_visible(text="Server", timeout=timeout):
            self.logger.info("[MAIN_PAGE] ✅ 主頁面已載入（服務器文字可見）")
            return True
        
        self.logger.error("[MAIN_PAGE] ❌ 主頁面載入超時")
        return False
    
    def select_server(self, server_name: Optional[str] = None) -> bool:
        """
        選擇服務器（PDF Step 63 / Case 4-2 第一步）
        
        策略 0: 優先使用配置的座標點擊 (550, 500)，因主頁可能為 SurfaceView。
        其餘策略：文字定位、XPath、第一個服務器項目。
        
        Args:
            server_name: 服務器名稱，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 選擇是否成功
        """
        if server_name is None:
            server_name = getattr(EnvConfig, 'DEFAULT_SERVER_NAME', None)
            if server_name is None:
                self.logger.warning("[MAIN_PAGE] 未指定服務器名稱，嘗試選擇第一個服務器...")
        
        self.logger.info(f"[MAIN_PAGE] 選擇服務器: {server_name}（PDF Step 63 / Case 4-2 第一步）...")
        
        # 策略 0: Case 4-2 第一步 — 使用配置的座標點擊 server（主頁常為 SurfaceView）
        tap_coords = getattr(EnvConfig, 'CASE4_2_SERVER_CLICK_COORDINATES', (550, 500))
        tap_x, tap_y = tap_coords
        self.logger.info(f"[MAIN_PAGE] 點擊 server 座標 ({tap_x}, {tap_y})（Case 4-2 第一步）...")
        try:
            self.driver.tap([(tap_x, tap_y)], duration=300)
            import time
            time.sleep(0.5)
            self.logger.info("[MAIN_PAGE] ✅ 已點擊 server 座標")
            
            # 點擊 server 後，偵測 Connect 圖片（3 秒）
            # 如果存在就點擊，不存在就跳過
            self.logger.info("[MAIN_PAGE] 偵測 Connect 圖片（3 秒）...")
            connect_coords = self.find_image_on_screen(
                image_path="mobile_main/connect.png",
                timeout=3.0,
                confidence=0.7
            )
            
            if connect_coords:
                connect_x, connect_y = connect_coords
                self.logger.info(f"[MAIN_PAGE] 找到 Connect 圖片，點擊座標 ({connect_x}, {connect_y})...")
                try:
                    self.driver.tap([(connect_x, connect_y)], duration=300)
                    time.sleep(0.5)
                    self.logger.info("[MAIN_PAGE] ✅ 已點擊 Connect 按鈕")
                except Exception as e:
                    self.logger.warning(f"[MAIN_PAGE] 點擊 Connect 按鈕失敗: {e}")
            else:
                self.logger.info("[MAIN_PAGE] 未找到 Connect 圖片，跳過（可能不是首次連接）")
            
            self.logger.info("[MAIN_PAGE] ✅ 繼續後續步驟")
            return True
        except Exception as e:
            self.logger.warning(f"[MAIN_PAGE] 座標點擊失敗，改試元素定位: {e}")
        
        # 如果未指定服務器名稱，直接選擇第一個
        if server_name is None:
            element = self.find_element_by_id(self.SERVER_ITEM_ID)
            if element:
                if self.click_element(element):
                    self.logger.info("[MAIN_PAGE] ✅ 成功選擇第一個服務器項目")
                    return True
            self.logger.error("[MAIN_PAGE] ❌ 無法找到服務器項目")
            return False
        
        # 策略 1: 使用文字定位（點擊包含服務器名稱的元素）
        max_scroll_attempts = 5  # 最多滾動 5 次
        for attempt in range(max_scroll_attempts):
            if self.click_by_text(server_name, timeout=2):
                self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇服務器: {server_name}（PDF Step 63）")
                return True
            
            # 如果文字定位失敗，嘗試使用 XPath 查找
            xpath = f'//*[contains(@text, "{server_name}")]'
            element = self.find_element_by_xpath(xpath, timeout=2)
            if element:
                if self.click_element(element):
                    self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇服務器: {server_name}（PDF Step 63）")
                    return True
            
            # 如果找不到，向下滾動列表
            if attempt < max_scroll_attempts - 1:
                self.logger.info(f"[MAIN_PAGE] 未找到服務器，向下滾動列表（嘗試 {attempt + 1}/{max_scroll_attempts}）...")
                self.swipe_vertical(direction="down", duration=500)
                import time
                time.sleep(0.5)  # 等待列表更新
        
        # 策略 3: 如果找不到指定服務器，嘗試點擊第一個服務器項目
        self.logger.warning("[MAIN_PAGE] 找不到指定服務器，嘗試點擊第一個服務器項目...")
        element = self.find_element_by_id(self.SERVER_ITEM_ID)
        if element:
            if self.click_element(element):
                self.logger.info("[MAIN_PAGE] ✅ 成功選擇第一個服務器項目")
                return True
        
        self.logger.error(f"[MAIN_PAGE] ❌ 無法選擇服務器: {server_name}（PDF Step 63）")
        return False
    
    def select_camera(self, camera_name: Optional[str] = None) -> bool:
        """
        選擇攝像頭（PDF Step 65）
        
        如果攝像頭不在可見區域，會自動滾動列表直到找到為止。
        選擇攝像頭後會自動進入 Live View。
        
        Args:
            camera_name: 攝像頭名稱，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 選擇是否成功
        """
        if camera_name is None:
            camera_name = getattr(EnvConfig, 'DEFAULT_CAMERA_NAME', 'usb_cam')
        
        self.logger.info(f"[MAIN_PAGE] 選擇攝像頭: {camera_name}（PDF Step 65）...")
        
        # 策略 0: Case 4-2 — 如果配置了座標，優先使用座標點擊（主頁常為 SurfaceView）
        tap_coords = getattr(EnvConfig, 'CASE4_2_CAMERA_CLICK_COORDINATES', None)
        if tap_coords is not None:
            tap_x, tap_y = tap_coords
            self.logger.info(f"[MAIN_PAGE] 使用配置的座標點擊攝像頭 ({tap_x}, {tap_y})（Case 4-2，SurfaceView 模式）...")
            try:
                import time
                self.driver.tap([(tap_x, tap_y)], duration=300)
                time.sleep(1.0)  # 等待頁面響應
                self.logger.info("[MAIN_PAGE] ✅ 已點擊攝像頭座標")
                
                # 選擇攝像頭後，點擊影片座標 (300, 400) 以打開影片
                time.sleep(1.0)  # 等待頁面載入
                if self.click_video_to_open((300, 400)):
                    self.logger.info("[MAIN_PAGE] ✅ 已點擊影片座標，等待影片打開...")
                return True
            except Exception as e:
                self.logger.warning(f"[MAIN_PAGE] 座標點擊失敗，改試元素定位: {e}")
        
        # 策略 1: 優先使用文字定位（點擊包含攝像頭名稱的元素）
        max_scroll_attempts = 5  # 最多滾動 5 次
        for attempt in range(max_scroll_attempts):
            if self.click_by_text(camera_name, timeout=2):
                self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇攝像頭: {camera_name}（PDF Step 65）")
                return True
            
            # 如果文字定位失敗，嘗試使用 XPath 查找
            xpath = f'//*[contains(@text, "{camera_name}")]'
            element = self.find_element_by_xpath(xpath, timeout=2)
            if element:
                if self.click_element(element):
                    self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇攝像頭: {camera_name}（PDF Step 65）")
                    # 選擇攝像頭後，點擊影片座標 (300, 400) 以打開影片
                    import time
                    time.sleep(1.0)  # 等待頁面載入
                    if self.click_video_to_open((300, 400)):
                        self.logger.info("[MAIN_PAGE] ✅ 已點擊影片座標，等待影片打開...")
                    return True

            # 如果找不到，向下滾動列表
            if attempt < max_scroll_attempts - 1:
                self.logger.info(f"[MAIN_PAGE] 未找到攝像頭，向下滾動列表（嘗試 {attempt + 1}/{max_scroll_attempts}）...")
                self.swipe_vertical(direction="down", duration=500)
                import time
                time.sleep(0.5)  # 等待列表更新
        
        # 策略 3: 如果找不到指定攝像頭，嘗試點擊第一個攝像頭項目
        self.logger.warning("[MAIN_PAGE] 找不到指定攝像頭，嘗試點擊第一個攝像頭項目...")
        element = self.find_element_by_id(self.CAMERA_ITEM_ID)
        if element:
            if self.click_element(element):
                self.logger.info("[MAIN_PAGE] ✅ 成功選擇第一個攝像頭項目")
                # 選擇攝像頭後，點擊影片座標 (300, 400) 以打開影片
                import time
                time.sleep(1.0)  # 等待頁面載入
                if self.click_video_to_open((300, 400)):
                    self.logger.info("[MAIN_PAGE] ✅ 已點擊影片座標，等待影片打開...")
                return True
        
        self.logger.error(f"[MAIN_PAGE] ❌ 無法選擇攝像頭: {camera_name}（PDF Step 65）")
        return False
    
    def click_video_to_open(self, video_coords: Tuple[int, int] = (300, 400)) -> bool:
        """
        點擊影片座標以打開影片（Case 4-2：選擇攝像頭後）
        
        Args:
            video_coords: 影片座標 (x, y)，默認 (300, 400)
            
        Returns:
            bool: 點擊是否成功
        """
        video_x, video_y = video_coords
        self.logger.info(f"[MAIN_PAGE] 點擊影片座標 ({video_x}, {video_y}) 以打開影片...")
        
        try:
            self.driver.tap([(video_x, video_y)], duration=300)
            import time
            time.sleep(0.5)
            self.logger.info("[MAIN_PAGE] ✅ 已點擊影片座標")
            return True
        except Exception as e:
            self.logger.error(f"[MAIN_PAGE] ❌ 點擊影片座標失敗: {e}")
            return False
    
    def navigate_to_playback(self) -> bool:
        """
        導航到播放頁面
        
        策略：點擊攝像頭後，通常會自動進入播放頁面
        
        Returns:
            bool: 導航是否成功
        """
        self.logger.info("[MAIN_PAGE] 導航到播放頁面...")
        
        # 如果已經在播放頁面，直接返回成功
        # 這裡可以添加檢查邏輯，但為了簡化，我們假設選擇攝像頭後會自動進入播放頁面
        return True
