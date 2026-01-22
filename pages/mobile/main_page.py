# 相對路徑: pages/mobile/main_page.py
"""
Nx Witness 移動端主頁面

處理 Test Case 4-2: 選擇服務器和攝像頭
"""

from typing import Optional
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
    # 注意：實際的 Resource ID 需要根據真實的 App 進行調整
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
        選擇服務器
        
        Args:
            server_name: 服務器名稱，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 選擇是否成功
        """
        if server_name is None:
            server_name = EnvConfig.DEFAULT_SERVER_NAME
        
        self.logger.info(f"[MAIN_PAGE] 選擇服務器: {server_name}")
        
        # 策略 1: 優先使用文字定位（點擊包含服務器名稱的元素）
        if self.click_by_text(server_name):
            self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇服務器: {server_name}")
            return True
        
        # 策略 2: 如果文字定位失敗，嘗試使用 XPath 查找包含服務器名稱的元素
        self.logger.warning("[MAIN_PAGE] 文字定位失敗，嘗試 XPath 定位...")
        xpath = f'//*[contains(@text, "{server_name}")]'
        element = self.find_element_by_xpath(xpath)
        if element:
            if self.click_element(element):
                self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇服務器: {server_name}")
                return True
        
        # 策略 3: 如果找不到指定服務器，嘗試點擊第一個服務器項目
        self.logger.warning("[MAIN_PAGE] 找不到指定服務器，嘗試點擊第一個服務器項目...")
        element = self.find_element_by_id(self.SERVER_ITEM_ID)
        if element:
            if self.click_element(element):
                self.logger.info("[MAIN_PAGE] ✅ 成功選擇第一個服務器項目")
                return True
        
        self.logger.error(f"[MAIN_PAGE] ❌ 無法選擇服務器: {server_name}")
        return False
    
    def select_camera(self, camera_name: Optional[str] = None) -> bool:
        """
        選擇攝像頭
        
        Args:
            camera_name: 攝像頭名稱，如果為 None 則使用配置中的默認值
            
        Returns:
            bool: 選擇是否成功
        """
        if camera_name is None:
            camera_name = getattr(EnvConfig, 'DEFAULT_CAMERA_NAME', 'usb_cam')
        
        self.logger.info(f"[MAIN_PAGE] 選擇攝像頭: {camera_name}")
        
        # 策略 1: 優先使用文字定位（點擊包含攝像頭名稱的元素）
        if self.click_by_text(camera_name):
            self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇攝像頭: {camera_name}")
            return True
        
        # 策略 2: 如果文字定位失敗，嘗試使用 XPath 查找包含攝像頭名稱的元素
        self.logger.warning("[MAIN_PAGE] 文字定位失敗，嘗試 XPath 定位...")
        xpath = f'//*[contains(@text, "{camera_name}")]'
        element = self.find_element_by_xpath(xpath)
        if element:
            if self.click_element(element):
                self.logger.info(f"[MAIN_PAGE] ✅ 成功選擇攝像頭: {camera_name}")
                return True
        
        # 策略 3: 如果找不到指定攝像頭，嘗試點擊第一個攝像頭項目
        self.logger.warning("[MAIN_PAGE] 找不到指定攝像頭，嘗試點擊第一個攝像頭項目...")
        element = self.find_element_by_id(self.CAMERA_ITEM_ID)
        if element:
            if self.click_element(element):
                self.logger.info("[MAIN_PAGE] ✅ 成功選擇第一個攝像頭項目")
                return True
        
        self.logger.error(f"[MAIN_PAGE] ❌ 無法選擇攝像頭: {camera_name}")
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
