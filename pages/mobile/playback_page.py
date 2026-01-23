# 相對路徑: pages/mobile/playback_page.py
"""
Nx Witness 移動端播放頁面

處理 Test Case 4-2: 使用日曆控件播放錄製的視頻
"""

from typing import Optional, Tuple
from pages.mobile.base_mobile_page import BaseMobilePage
from config import EnvConfig
from datetime import datetime, timedelta


class PlaybackPage(BaseMobilePage):
    """
    Nx Witness 移動端播放頁面
    
    職責：
    - 處理視頻播放相關操作（打開日曆、選擇日期、播放視頻等）
    - 驗證視頻播放狀態
    """
    
    # Locators - 使用 Resource ID（優先）或文字定位
    # 注意：實際的 Resource ID 需要根據真實的 App 進行調整
    CALENDAR_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/calendar_button"  # 日曆按鈕
    CALENDAR_VIEW_ID = "com.networkoptix.nxwitness.mobile:id/calendar_view"  # 日曆視圖
    DATE_ITEM_ID = "com.networkoptix.nxwitness.mobile:id/date_item"  # 日期項目
    PLAY_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/play_button"  # 播放按鈕
    PAUSE_BUTTON_ID = "com.networkoptix.nxwitness.mobile:id/pause_button"  # 暫停按鈕
    VIDEO_VIEW_ID = "com.networkoptix.nxwitness.mobile:id/video_view"  # 視頻視圖
    
    def __init__(self, driver: Optional[object] = None):
        """
        初始化播放頁面
        
        Args:
            driver: Appium WebDriver 實例
        """
        super().__init__(driver)
    
    def wait_for_playback_page_loaded(self, timeout: int = 15) -> bool:
        """
        等待播放頁面載入完成
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 播放頁面是否載入完成
        """
        self.logger.info("[PLAYBACK_PAGE] 等待播放頁面載入...")
        
        # 等待視頻視圖或日曆按鈕出現（表示播放頁面已載入）
        if self.wait_for_element_visible(resource_id=self.VIDEO_VIEW_ID, timeout=timeout):
            self.logger.info("[PLAYBACK_PAGE] ✅ 播放頁面已載入（視頻視圖可見）")
            return True
        
        if self.wait_for_element_visible(resource_id=self.CALENDAR_BUTTON_ID, timeout=timeout):
            self.logger.info("[PLAYBACK_PAGE] ✅ 播放頁面已載入（日曆按鈕可見）")
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[PLAYBACK_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.wait_for_element_visible(text="日曆", timeout=timeout) or \
           self.wait_for_element_visible(text="Calendar", timeout=timeout):
            self.logger.info("[PLAYBACK_PAGE] ✅ 播放頁面已載入（日曆文字可見）")
            return True
        
        self.logger.error("[PLAYBACK_PAGE] ❌ 播放頁面載入超時")
        return False
    
    def open_calendar(self) -> bool:
        """
        打開日曆控件
        
        Returns:
            bool: 打開是否成功
        """
        self.logger.info("[PLAYBACK_PAGE] 打開日曆控件...")
        
        # 策略 1: 優先使用 Resource ID 定位日曆按鈕
        if self.click_by_id(self.CALENDAR_BUTTON_ID):
            self.logger.info("[PLAYBACK_PAGE] ✅ 成功打開日曆控件")
            return True
        
        # 策略 2: 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[PLAYBACK_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.click_by_text("日曆") or self.click_by_text("Calendar"):
            self.logger.info("[PLAYBACK_PAGE] ✅ 成功打開日曆控件")
            return True
        
        # 策略 3: 嘗試查找包含日曆圖標的元素
        self.logger.warning("[PLAYBACK_PAGE] 文字定位失敗，嘗試查找日曆圖標...")
        element = self.find_element_by_xpath('//*[contains(@content-desc, "calendar") or contains(@content-desc, "日曆")]')
        if element:
            if self.click_element(element):
                self.logger.info("[PLAYBACK_PAGE] ✅ 成功打開日曆控件")
                return True
        
        self.logger.error("[PLAYBACK_PAGE] ❌ 無法打開日曆控件")
        return False
    
    def is_calendar_open(self, timeout: int = 5) -> bool:
        """
        檢查日曆是否已打開
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 日曆是否已打開
        """
        # 等待日曆視圖出現
        if self.wait_for_element_visible(resource_id=self.CALENDAR_VIEW_ID, timeout=timeout):
            return True
        
        # 如果 Resource ID 定位失敗，嘗試使用文字定位（查找日期元素）
        if self.wait_for_element_visible(resource_id=self.DATE_ITEM_ID, timeout=timeout):
            return True
        
        return False
    
    def select_date(self, target_date: Optional[datetime] = None) -> bool:
        """
        在日曆中選擇日期
        
        Args:
            target_date: 目標日期，如果為 None 則選擇今天
            
        Returns:
            bool: 選擇是否成功
        """
        if target_date is None:
            target_date = datetime.now()
        
        self.logger.info(f"[PLAYBACK_PAGE] 選擇日期: {target_date.strftime('%Y-%m-%d')}")
        
        # 確保日曆已打開
        if not self.is_calendar_open():
            if not self.open_calendar():
                self.logger.error("[PLAYBACK_PAGE] ❌ 無法打開日曆")
                return False
        
        # 獲取日期字符串（格式：YYYY-MM-DD 或 DD）
        date_str = target_date.strftime('%d')  # 只取日期部分（例如：15）
        date_full_str = target_date.strftime('%Y-%m-%d')  # 完整日期（例如：2024-01-15）
        
        # 策略 1: 優先使用文字定位（點擊包含日期的元素）
        if self.click_by_text(date_str):
            self.logger.info(f"[PLAYBACK_PAGE] ✅ 成功選擇日期: {date_str}")
            return True
        
        # 策略 2: 如果文字定位失敗，嘗試使用 XPath 查找包含日期的元素
        self.logger.warning("[PLAYBACK_PAGE] 文字定位失敗，嘗試 XPath 定位...")
        xpath = f'//*[contains(@text, "{date_str}")]'
        element = self.find_element_by_xpath(xpath)
        if element:
            if self.click_element(element):
                self.logger.info(f"[PLAYBACK_PAGE] ✅ 成功選擇日期: {date_str}")
                return True
        
        # 策略 3: 如果找不到指定日期，嘗試點擊第一個日期項目
        self.logger.warning("[PLAYBACK_PAGE] 找不到指定日期，嘗試點擊第一個日期項目...")
        element = self.find_element_by_id(self.DATE_ITEM_ID)
        if element:
            if self.click_element(element):
                self.logger.info("[PLAYBACK_PAGE] ✅ 成功選擇第一個日期項目")
                return True
        
        self.logger.error(f"[PLAYBACK_PAGE] ❌ 無法選擇日期: {date_str}")
        return False
    
    def select_date_with_recording(self, days_ago: int = 1) -> bool:
        """
        選擇有錄影的日期（從今天往前推）
        
        Args:
            days_ago: 幾天前（默認為 1，即昨天）
            
        Returns:
            bool: 選擇是否成功
        """
        target_date = datetime.now() - timedelta(days=days_ago)
        self.logger.info(f"[PLAYBACK_PAGE] 選擇 {days_ago} 天前的日期: {target_date.strftime('%Y-%m-%d')}")
        
        # 先打開日曆
        if not self.open_calendar():
            return False
        
        # 選擇日期
        if not self.select_date(target_date):
            return False
        
        # 等待日曆關閉（表示已選擇日期）
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from appium.webdriver.common.appiumby import AppiumBy
            
            wait = WebDriverWait(self.driver, 5)
            wait.until_not(
                EC.presence_of_element_located((AppiumBy.ID, self.CALENDAR_VIEW_ID))
            )
            self.logger.info("[PLAYBACK_PAGE] ✅ 日曆已關閉，日期選擇完成")
            return True
        except Exception:
            # 如果日曆沒有自動關閉，這可能也是正常的（取決於 App 的實現）
            self.logger.warning("[PLAYBACK_PAGE] 日曆未自動關閉，但繼續執行...")
            return True
    
    def click_play_button(self) -> bool:
        """
        點擊播放按鈕
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[PLAYBACK_PAGE] 點擊播放按鈕...")
        
        # 策略 1: 優先使用 Resource ID 定位
        if self.click_by_id(self.PLAY_BUTTON_ID):
            self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊播放按鈕")
            return True
        
        # 策略 2: 如果 Resource ID 定位失敗，嘗試使用文字定位
        self.logger.warning("[PLAYBACK_PAGE] Resource ID 定位失敗，嘗試文字定位...")
        if self.click_by_text("播放") or self.click_by_text("Play"):
            self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊播放按鈕")
            return True
        
        # 策略 3: 嘗試查找包含播放圖標的元素
        self.logger.warning("[PLAYBACK_PAGE] 文字定位失敗，嘗試查找播放圖標...")
        element = self.find_element_by_xpath('//*[contains(@content-desc, "play") or contains(@content-desc, "播放")]')
        if element:
            if self.click_element(element):
                self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊播放按鈕")
                return True
        
        self.logger.error("[PLAYBACK_PAGE] ❌ 無法找到播放按鈕")
        return False
    
    def is_video_playing(self, timeout: int = 10) -> bool:
        """
        檢查視頻是否正在播放
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 視頻是否正在播放
        """
        self.logger.info("[PLAYBACK_PAGE] 檢查視頻播放狀態...")
        
        # 策略 1: 檢查暫停按鈕是否存在（如果存在，表示視頻正在播放）
        if self.wait_for_element_visible(resource_id=self.PAUSE_BUTTON_ID, timeout=timeout):
            self.logger.info("[PLAYBACK_PAGE] ✅ 視頻正在播放（暫停按鈕可見）")
            return True
        
        # 策略 2: 檢查視頻視圖是否存在且可見
        element = self.find_element_by_id(self.VIDEO_VIEW_ID, timeout=timeout)
        if element and self.is_element_visible(element):
            self.logger.info("[PLAYBACK_PAGE] ✅ 視頻視圖可見（可能正在播放）")
            return True
        
        self.logger.warning("[PLAYBACK_PAGE] ⚠️ 無法確認視頻是否正在播放")
        return False
    
    def verify_video_opened_by_screenshot_comparison(
        self,
        screenshot_interval: float = 2.0,
        difference_threshold: float = 0.01
    ) -> bool:
        """
        通過截圖比對驗證影片是否成功打開
        
        流程：
        1. 拍攝第一張截圖
        2. 等待指定時間（默認 2 秒）
        3. 拍攝第二張截圖
        4. 比對兩張截圖的差異
        5. 如果差異超過閾值（默認 1%），視為影片成功打開
        
        Args:
            screenshot_interval: 兩張截圖的時間間隔（秒），默認 2.0 秒
            difference_threshold: 差異閾值（0.0-1.0），默認 0.01 (1%)
            
        Returns:
            bool: 影片是否成功打開（差異超過閾值）
        """
        import time
        import os
        from datetime import datetime
        
        self.logger.info(
            f"[PLAYBACK_PAGE] 開始驗證影片是否打開（截圖間隔: {screenshot_interval} 秒，"
            f"差異閾值: {difference_threshold*100:.1f}%）..."
        )
        
        # 創建診斷目錄
        diagnostic_dir = os.path.join(os.getcwd(), "report", "diagnostics")
        os.makedirs(diagnostic_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot1_path = os.path.join(diagnostic_dir, f"video_check_1_{timestamp}.png")
        screenshot2_path = os.path.join(diagnostic_dir, f"video_check_2_{timestamp}.png")
        
        try:
            # 步驟 1: 拍攝第一張截圖
            self.logger.info("[PLAYBACK_PAGE] 拍攝第一張截圖...")
            if not self.take_screenshot(screenshot1_path):
                self.logger.error("[PLAYBACK_PAGE] ❌ 第一張截圖失敗")
                return False
            
            # 步驟 2: 等待指定時間
            self.logger.info(f"[PLAYBACK_PAGE] 等待 {screenshot_interval} 秒...")
            time.sleep(screenshot_interval)
            
            # 步驟 3: 拍攝第二張截圖
            self.logger.info("[PLAYBACK_PAGE] 拍攝第二張截圖...")
            if not self.take_screenshot(screenshot2_path):
                self.logger.error("[PLAYBACK_PAGE] ❌ 第二張截圖失敗")
                return False
            
            # 步驟 4: 比對兩張截圖
            self.logger.info("[PLAYBACK_PAGE] 比對兩張截圖...")
            exceeds_threshold, actual_difference = self.compare_screenshots(
                screenshot1_path,
                screenshot2_path,
                threshold=difference_threshold
            )
            
            if exceeds_threshold:
                self.logger.info(
                    f"[PLAYBACK_PAGE] ✅ 影片驗證成功！差異度 {actual_difference*100:.2f}% "
                    f"超過閾值 {difference_threshold*100:.1f}%，影片已成功打開"
                )
                return True
            else:
                self.logger.warning(
                    f"[PLAYBACK_PAGE] ❌ 影片驗證失敗！差異度 {actual_difference*100:.2f}% "
                    f"未超過閾值 {difference_threshold*100:.1f}%，影片可能未成功打開"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"[PLAYBACK_PAGE] ❌ 影片驗證過程發生異常: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False
    
    def play_recorded_video(self, days_ago: int = 1) -> bool:
        """
        播放錄製的視頻（完整流程）
        
        Args:
            days_ago: 幾天前的錄影（默認為 1，即昨天）
            
        Returns:
            bool: 播放是否成功
        """
        self.logger.info(f"[PLAYBACK_PAGE] 開始播放 {days_ago} 天前的錄影...")
        
        # 步驟 1: 打開日曆
        if not self.open_calendar():
            self.logger.error("[PLAYBACK_PAGE] ❌ 打開日曆失敗")
            return False
        
        # 步驟 2: 選擇有錄影的日期
        if not self.select_date_with_recording(days_ago):
            self.logger.error("[PLAYBACK_PAGE] ❌ 選擇日期失敗")
            return False
        
        # 步驟 3: 點擊播放按鈕（如果需要）
        # 注意：某些 App 可能在選擇日期後自動開始播放，不需要額外點擊播放按鈕
        self.click_play_button()  # 不強制要求成功
        
        # 步驟 4: 驗證視頻是否正在播放
        if not self.is_video_playing():
            self.logger.error("[PLAYBACK_PAGE] ❌ 視頻播放驗證失敗")
            return False
        
        self.logger.info("[PLAYBACK_PAGE] ✅ 視頻播放成功")
        return True
    
    def pause_playback(self) -> bool:
        """
        暫停視頻播放（PDF Step 66-67）
        
        策略：
        1. 點擊視頻容器中心以顯示控制按鈕
        2. 點擊暫停按鈕
        
        Returns:
            bool: 暫停是否成功
        """
        self.logger.info("[PLAYBACK_PAGE] 暫停視頻播放（PDF Step 66-67）...")
        
        # 步驟 1: 點擊視頻容器中心以顯示控制按鈕
        if not self.driver:
            self.logger.error("[PLAYBACK_PAGE] WebDriver 未初始化")
            return False
        
        try:
            # 獲取屏幕尺寸
            size = self.driver.get_window_size()
            center_x = size['width'] // 2
            center_y = size['height'] // 2
            
            # 點擊視頻容器中心
            self.logger.info(f"[PLAYBACK_PAGE] 點擊視頻容器中心 ({center_x}, {center_y}) 以顯示控制按鈕...")
            if not self.tap_at_coordinates(center_x, center_y):
                self.logger.warning("[PLAYBACK_PAGE] 點擊視頻容器中心失敗，但繼續嘗試點擊暫停按鈕...")
            
            # 等待控制按鈕出現
            import time
            time.sleep(0.5)
            
            # 步驟 2: 點擊暫停按鈕
            # 策略 1: 優先使用 Resource ID 定位
            if self.click_by_id(self.PAUSE_BUTTON_ID, timeout=3):
                self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊暫停按鈕（PDF Step 67）")
                return True
            
            # 策略 2: 如果 Resource ID 定位失敗，嘗試使用文字定位
            self.logger.warning("[PLAYBACK_PAGE] Resource ID 定位失敗，嘗試文字定位...")
            if self.click_by_text("暫停") or self.click_by_text("Pause"):
                self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊暫停按鈕（PDF Step 67）")
                return True
            
            # 策略 3: 嘗試查找包含暫停圖標的元素
            self.logger.warning("[PLAYBACK_PAGE] 文字定位失敗，嘗試查找暫停圖標...")
            element = self.find_element_by_xpath('//*[contains(@content-desc, "pause") or contains(@content-desc, "暫停")]')
            if element:
                if self.click_element(element):
                    self.logger.info("[PLAYBACK_PAGE] ✅ 成功點擊暫停按鈕（PDF Step 67）")
                    return True
            
            self.logger.error("[PLAYBACK_PAGE] ❌ 無法找到暫停按鈕（PDF Step 67）")
            return False
            
        except Exception as e:
            self.logger.error(f"[PLAYBACK_PAGE] ❌ 暫停視頻播放失敗: {e}")
            return False
    
    def is_playback_paused(self, timeout: int = 5) -> bool:
        """
        檢查視頻是否已暫停（PDF Step 67 驗證）
        
        策略：
        1. 檢查播放按鈕是否存在（如果存在，表示視頻已暫停）
        2. 檢查暫停按鈕是否不存在（如果不存在，表示視頻已暫停）
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            bool: 視頻是否已暫停
        """
        self.logger.info("[PLAYBACK_PAGE] 檢查視頻是否已暫停（PDF Step 67 驗證）...")
        
        # 策略 1: 檢查播放按鈕是否存在（如果存在，表示視頻已暫停）
        if self.wait_for_element_visible(resource_id=self.PLAY_BUTTON_ID, timeout=timeout):
            self.logger.info("[PLAYBACK_PAGE] ✅ 視頻已暫停（播放按鈕可見）")
            return True
        
        # 策略 2: 檢查暫停按鈕是否不存在（如果不存在，表示視頻已暫停）
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from appium.webdriver.common.appiumby import AppiumBy
            
            wait = WebDriverWait(self.driver, timeout)
            # 等待暫停按鈕消失
            wait.until_not(
                EC.presence_of_element_located((AppiumBy.ID, self.PAUSE_BUTTON_ID))
            )
            self.logger.info("[PLAYBACK_PAGE] ✅ 視頻已暫停（暫停按鈕已消失）")
            return True
        except Exception:
            # 如果暫停按鈕仍然存在，表示視頻可能還在播放
            self.logger.warning("[PLAYBACK_PAGE] ⚠️ 無法確認視頻是否已暫停（暫停按鈕仍然存在）")
            return False
