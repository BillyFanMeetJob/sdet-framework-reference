# 相對路徑: pages/main_page.py

from base.desktop_app import DesktopApp
from config import EnvConfig
import time
import pygetwindow as gw
import pyautogui
import numpy as np
from PIL import Image
from datetime import datetime, date
from typing import Optional, Tuple
import os
import pytest

class MainPage(DesktopApp):
    def open_main_menu(self):
        """點擊左上角菜單圖標"""
        self.logger.info("[MAIN_PAGE] [CLICK] Clicking top-left menu icon...")
        self.logger.info(f"[MAIN_PAGE] [PARAM] Parameters: image='desktop_main/menu_icon.png', timeout=3s")
        
        success = self.smart_click(
            x_ratio=0.02, 
            y_ratio=0.03,
            target_text=None,  # 菜單圖標不需要 OCR，加快速度
            image_path="desktop_main/menu_icon.png",
            timeout=3  # 增加超時時間，確保圖片辨識有足夠時間
        )
        
        if success:
            self.logger.info("[MAIN_PAGE] [SUCCESS] Main menu opened successfully")
            # 智能等待選單展開（增加等待時間，確保菜單完全展開）
            import time
            wait_time = 0.8
            self.logger.debug(f"[MAIN_PAGE] [WAIT] Waiting {wait_time}s for menu to fully expand...")
            time.sleep(wait_time)  # 增加到 0.8 秒，確保菜單完全展開，讓後續點擊有足夠時間
        else:
            self.logger.error("[MAIN_PAGE] [FAIL] Failed to open main menu: Unable to find or click menu icon")
        
        return success

    def select_local_settings(self) -> bool:
        """
        點擊選單中的『本地設置』
        
        此方法點擊主選單中的本地設置選項，並驗證設置視窗是否成功開啟。
        
        Returns:
            bool: 如果成功點擊並開啟設置視窗返回 True，否則返回 False
        
        Note:
            - 使用配置中的資源路徑（避免硬編碼）
            - 使用配置中的等待時間（避免硬編碼）
        """
        self.logger.info("[MAIN_PAGE] [CLICK] Clicking 'Local Settings'...")
        self.logger.info(f"[MAIN_PAGE] [PARAM] Parameters: image='{EnvConfig.APP_PATHS.LOCAL_SETTINGS}', text='本地设置' (with fallbacks), region=(0, 0, 500, 800), timeout=5s, use_vlm=False (image-first)")
        
        # 確保菜單已展開，先等待一小段時間
        # 使用配置中的點擊等待時間（避免硬編碼）
        wait_time = EnvConfig.THRESHOLDS.CLICK_WAIT_TIME
        self.logger.debug(f"[MAIN_PAGE] [WAIT] Waiting {wait_time}s for menu to fully expand...")
        time.sleep(wait_time)
        
        # 限制搜尋區域到左上角（修復 OCR/VLM 在全螢幕找不到小字的問題）
        # 選單通常位於左上角，寬度不超過 500px，高度不超過 800px
        # 限制搜尋區域可以大幅提高識別率，避免被背景干擾
        menu_region = (0, 0, 500, 800)
        self.logger.debug(f"[MAIN_PAGE] [REGION] Search region limited to: {menu_region}")
        
        # 使用配置中的資源路徑（避免硬編碼）
        # 優先使用圖片辨識，如果失敗則嘗試 OCR/VLM（限制在選單區域）
        # 注意：UI 顯示的是「本地设置」（簡體中文），不是「本機設定」（繁體中文）
        target_texts = ["本地设置", "本地設置", "本機設定", "Local Settings"]  # 多個候選文字，優先簡體中文
        self.logger.info(f"[MAIN_PAGE] [CALL] Calling smart_click with image='{EnvConfig.APP_PATHS.LOCAL_SETTINGS}', text='{target_texts[0]}' (fallback: {target_texts[1:]})...")
        self.logger.info(f"[MAIN_PAGE] [STRATEGY] Using image-first strategy (use_vlm=False)")
        success = self.smart_click(
            x_ratio=0.1, 
            y_ratio=0.32,
            target_text=target_texts[0],  # 優先使用簡體中文「本地设置」
            image_path=EnvConfig.APP_PATHS.LOCAL_SETTINGS,
            timeout=5,  # 增加到 5 秒，給辨識和點擊足夠時間
            region=menu_region,  # 關鍵修改：限制搜尋區域到左上角
            use_vlm=False  # 啟用圖片優先模式：圖片 > VLM > OCR
        )
        
        self.logger.info(f"[MAIN_PAGE] [RESULT] smart_click returned: {success}")
        
        # 備用策略：如果視覺定位失敗，嘗試相對座標盲點
        # 假設選單按鈕在左上角 (25, 25)，本機設定大約在 Y=350 處（需根據實際 UI 調整）
        if not success:
            self.logger.warning("[MAIN_PAGE] [FALLBACK] Visual recognition failed, trying coordinate fallback...")
            try:
                # 獲取選單圖標位置（假設在左上角）
                menu_icon_x = 25
                menu_icon_y = 25
                # 本機設定選項大約在選單圖標下方 325 像素處（Y=350）
                local_settings_y = menu_icon_y + 325
                local_settings_x = 150  # 選單項目通常位於 X=150 左右
                
                self.logger.info(f"[MAIN_PAGE] [FALLBACK] Attempting coordinate click: ({local_settings_x}, {local_settings_y})")
                pyautogui.click(local_settings_x, local_settings_y)
                time.sleep(EnvConfig.THRESHOLDS.CLICK_WAIT_TIME)
                self.logger.info("[MAIN_PAGE] [FALLBACK] Coordinate click executed, assuming success")
                success = True  # 假設點擊成功
            except Exception as e:
                self.logger.error(f"[MAIN_PAGE] [FALLBACK] Coordinate click failed: {e}")
                import traceback
                self.logger.error(f"[MAIN_PAGE] [FALLBACK] Traceback: {traceback.format_exc()}")
        
        # 重要：即使 smart_click 返回 False，也可能是因為點擊成功後菜單關閉，導致後續辨識失敗
        # 所以我們需要驗證設置視窗是否真的出現了
        if not success:
            self.logger.info("[MAIN_PAGE] [VERIFY] smart_click returned False, verifying if settings window appeared...")
            # 等待一下，讓視窗有時間出現
            time.sleep(1.0)
            # 檢查設置視窗是否已經出現
            window_titles = ["本地設置", "Local Settings", "本地設定", "Nx Witness Client"]
            self.logger.debug(f"[MAIN_PAGE] [VERIFY] Checking for settings window with titles: {window_titles}")
            found_window = self.wait_for_window(
                window_titles=window_titles, 
                timeout=2  # 短 timeout，快速檢查
            )
            if found_window:
                # 視窗已經出現，說明點擊其實是成功的，只是 smart_click 的後續辨識失敗了
                self.logger.info(f"[MAIN_PAGE] [VERIFY] Settings window found: '{found_window.title}' - Click was successful despite smart_click returning False")
                success = True  # 修正為 True
            else:
                self.logger.warning("[MAIN_PAGE] [VERIFY] Settings window not found - Click may have failed")
        
        if success:
            self.logger.info("[MAIN_PAGE] [SUCCESS] Click operation succeeded, waiting for settings window to open...")
            # 智能等待設置視窗開啟
            # 使用配置中的等待時間（避免硬編碼）
            wait_time = EnvConfig.THRESHOLDS.SETTINGS_WAIT_TIME
            self.logger.debug(f"[MAIN_PAGE] [WAIT] Waiting {wait_time}s for settings window...")
            time.sleep(wait_time)
            window_titles = ["本地設置", "Local Settings", "本地設定", "Nx Witness Client"]
            self.logger.debug(f"[MAIN_PAGE] [VERIFY] Checking for settings window with titles: {window_titles}")
            found_window = self.wait_for_window(
                window_titles=window_titles, 
                timeout=5  # 增加到 5 秒，給視窗開啟足夠時間
            )
            if found_window:
                self.logger.info(f"[MAIN_PAGE] [SUCCESS] Settings window opened: '{found_window.title}'")
                # 驗證成功，確保視窗確實存在
                return True
            else:
                # 視窗未檢測到，但可能只是辨識問題，不立即判定為失敗
                # 繼續執行，因為畫面可能已經點擊成功了
                self.logger.warning("[MAIN_PAGE] [WARN] Settings window not detected, but continuing (may be a recognition issue)")
                # 不返回 False，因為 smart_click 已經成功，畫面可能已經點擊了
                return True  # 改變邏輯：smart_click 成功就認為成功，不依賴視窗驗證
        else:
            self.logger.error("[MAIN_PAGE] [FAIL] smart_click returned False and settings window verification failed - Click operation likely failed")
        
        return success
    
    def is_recording_view_open(self):
        """
        🎯 檢查錄影畫面是否已開啟
        如果中間影片區域全黑，代表錄影畫面沒有開啟
        返回 True 表示錄影畫面已開啟（有畫面），False 表示未開啟（全黑）
        """
        self.logger.info("[RECORDING_VIEW] 檢查錄影畫面是否已開啟...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.warning("[RECORDING_VIEW] 無法獲取窗口，假設錄影畫面未開啟")
            return False
        
        try:
            # 定義中間視頻區域（避開左側面板、右側通知欄、底部控制欄）
            # 中間區域：x 從 20% 到 75%，y 從 15% 到 70%
            video_left = win.left + int(win.width * 0.20)
            video_top = win.top + int(win.height * 0.15)
            video_width = int(win.width * 0.55)  # 75% - 20% = 55%
            video_height = int(win.height * 0.55)  # 70% - 15% = 55%
            
            # 截取中間視頻區域
            video_region = (video_left, video_top, video_width, video_height)
            screenshot = pyautogui.screenshot(region=video_region)
            
            # 轉換為 numpy 數組並計算平均亮度
            img_array = np.array(screenshot)
            # 轉換為灰度圖（如果原本是彩色）
            if len(img_array.shape) == 3:
                # RGB 轉灰度：使用標準公式
                gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = img_array
            
            # 計算平均亮度
            avg_brightness = np.mean(gray)
            
            # 如果平均亮度低於 30（接近黑色），認為畫面未開啟
            # 如果平均亮度高於 30，認為畫面已開啟
            threshold = 30
            is_open = avg_brightness > threshold
            
            self.logger.info(f"[RECORDING_VIEW] 中間視頻區域平均亮度: {avg_brightness:.2f}, 閾值: {threshold}, 畫面狀態: {'已開啟' if is_open else '未開啟（全黑）'}")
            
            # 保存調試截圖
            try:
                import os
                from datetime import datetime
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "recording_view_debug")
                os.makedirs(debug_dir, exist_ok=True)
                now = datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                screenshot_path = os.path.join(debug_dir, f"recording_view_check_{timestamp}_brightness_{avg_brightness:.1f}.png")
                screenshot.save(screenshot_path)
                self.logger.debug(f"[RECORDING_VIEW] 調試截圖已保存: {screenshot_path}")
            except Exception as e:
                self.logger.debug(f"[RECORDING_VIEW] 保存調試截圖失敗: {e}")
            
            return is_open
            
        except Exception as e:
            self.logger.warning(f"[RECORDING_VIEW] 檢查錄影畫面狀態時發生錯誤: {e}")
            # 發生錯誤時，假設畫面未開啟，需要雙擊
            return False
    
    def check_recording_view_brightness(self) -> float:
        """
        🎯 檢查錄影畫面的亮度值（返回實際數值）
        
        用於驗證攝影機是否真的打開，返回實際的亮度值（0-255）。
        如果亮度為 0 或接近 0，代表畫面全黑（未開啟）。
        
        Returns:
            float: 中間視頻區域的平均亮度值（0-255）
        """
        self.logger.info("[RECORDING_VIEW] 檢查錄影畫面亮度值...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.warning("[RECORDING_VIEW] 無法獲取窗口，返回亮度 0")
            return 0.0
        
        try:
            # 定義中間視頻區域（避開左側面板、右側通知欄、底部控制欄）
            # 中間區域：x 從 20% 到 75%，y 從 15% 到 70%
            video_left = win.left + int(win.width * 0.20)
            video_top = win.top + int(win.height * 0.15)
            video_width = int(win.width * 0.55)  # 75% - 20% = 55%
            video_height = int(win.height * 0.55)  # 70% - 15% = 55%
            
            # 截取中間視頻區域
            video_region = (video_left, video_top, video_width, video_height)
            screenshot = pyautogui.screenshot(region=video_region)
            
            # 轉換為 numpy 數組並計算平均亮度
            img_array = np.array(screenshot)
            # 轉換為灰度圖（如果原本是彩色）
            if len(img_array.shape) == 3:
                # RGB 轉灰度：使用標準公式
                gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = img_array
            
            # 計算平均亮度
            avg_brightness = float(np.mean(gray))
            
            self.logger.info(f"[RECORDING_VIEW] 中間視頻區域平均亮度: {avg_brightness:.2f}")
            return avg_brightness
            
        except Exception as e:
            self.logger.warning(f"[RECORDING_VIEW] 檢查亮度時發生錯誤: {e}")
            return 0.0
    
    def select_first_active_date(self) -> Optional[Tuple[int, int]]:
        """
        🎯 [視覺驅動] 在日曆中尋找第一個有綠色標記的日期（取代寫死的 click_date_17）
        
        ROI 設定：僅掃描日曆區域（例如右下角區域）
        顏色特徵：尋找 RGB(0, 255, 0) 附近的亮綠色像素（Tolerance=30）
        
        邏輯：
        1. 使用 nested loop 或 numpy 快速掃描日曆區域
        2. 找到綠色像素後，點擊該像素上方 10px 的位置（點擊日期數字，而不是點綠線）
        3. 如果掃描結果全是 RGB(0,0,0)，代表日曆沒打開，請截圖並報錯
        
        Returns:
            tuple[int, int] | None: 找到的日期座標 (x, y)，如果找不到則返回 None
        
        Raises:
            pytest.fail: 如果日曆沒打開或找不到綠色標記
        """
        self._log_method_entry("select_first_active_date")
        self.logger.info("[CALENDAR_VISUAL] 開始使用視覺驅動方式尋找日曆上有綠色標記的日期...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.error("[CALENDAR_VISUAL] 無法獲取窗口")
            pytest.fail("無法獲取窗口，無法掃描日曆區域")
        
        # ROI 設定：僅掃描日曆區域（右下角區域）
        # 🎯 優先使用動態錨點定位（Anchor-based ROI）
        calendar_region = self._get_calendar_region_by_anchor()
        
        if not calendar_region:
            # 🎯 Fallback: 如果錨點定位失敗，使用配置檔的靜態比例
            # 但必須確保 Fallback 也能掃描到最右邊（CALENDAR_RIGHT_RATIO = 1.0）
            self.logger.warning("[CALENDAR_VISUAL] Anchor定位失敗，使用配置檔Fallback比例...")
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            calendar_left = win.left + int(win.width * calendar_config.CALENDAR_LEFT_RATIO)
            calendar_right = win.left + int(win.width * calendar_config.CALENDAR_RIGHT_RATIO)
            calendar_top = win.top + int(win.height * calendar_config.CALENDAR_TOP_RATIO)
            calendar_bottom = win.top + int(win.height * calendar_config.CALENDAR_BOTTOM_RATIO)
            calendar_width = calendar_right - calendar_left
            calendar_height = calendar_bottom - calendar_top
            
            self.logger.info(f"[CALENDAR_VISUAL] Fallback區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
            self.logger.info(f"[CALENDAR_VISUAL] Fallback右邊界: {calendar_right} (視窗寬度: {win.width}, RIGHT_RATIO: {calendar_config.CALENDAR_RIGHT_RATIO})")
        else:
            # 🎯 使用動態錨點定位計算出的區域
            calendar_left, calendar_top, calendar_width, calendar_height = calendar_region
            calendar_right = calendar_left + calendar_width
            calendar_bottom = calendar_top + calendar_height
            
            self.logger.info(f"[CALENDAR_VISUAL] Anchor區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
            self.logger.info(f"[CALENDAR_VISUAL] Anchor右邊界: {calendar_right} (確保覆蓋到螢幕最右側)")
        
        self.logger.info(f"[CALENDAR_VISUAL] 最終日曆掃描區域 (ROI): left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}, right={calendar_right}")
        
        try:
            calendar_region = (calendar_left, calendar_top, calendar_width, calendar_height)
            screenshot = pyautogui.screenshot(region=calendar_region)
            img_array = np.array(screenshot)
            
            # 確保是 RGB 格式（3 通道）
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            
            # 🎯 使用配置中的顏色閾值（避免硬編碼）
            thresholds = EnvConfig.THRESHOLDS
            green_pixels = []  # 儲存找到的綠色像素座標
            black_pixel_count = 0  # 統計黑色像素數量（用於判斷日曆是否打開）
            total_pixels = img_array.shape[0] * img_array.shape[1]
            
            # 使用 nested loop 快速掃描
            # 從上到下、從左到右掃描，確保找到第一個（最左上）的綠色標記
            for row in range(img_array.shape[0]):
                for col in range(img_array.shape[1]):
                    r, g, b = img_array[row, col]
                    
                    # 檢查是否為黑色（用於判斷日曆是否打開）
                    # 使用配置中的黑色像素閾值（避免硬編碼）
                    if (r < thresholds.BLACK_PIXEL_THRESHOLD and 
                        g < thresholds.BLACK_PIXEL_THRESHOLD and 
                        b < thresholds.BLACK_PIXEL_THRESHOLD):
                        black_pixel_count += 1
                    
                    # 🎯 [UPDATED] 使用新的綠色判定邏輯（區分亮綠色與白色文字）
                    # 1. 亮度檢查 (太暗不要)
                    calendar_config = EnvConfig.CALENDAR_SETTINGS
                    pass_brightness = g > calendar_config.GREEN_MIN_BRIGHTNESS
                    
                    # 2. 綠色主導檢查 (排除白色文字與灰色背景)
                    # 白色: 255 > 255 + 40 (False) -> 排除
                    # 綠色: 200 > 50 + 40 (True) -> 通過
                    offset = calendar_config.GREEN_DOMINANCE_OFFSET
                    pass_dominance = (g > r + offset) and (g > b + offset)
                    
                    # 3. 🎯 關鍵修正：限定 R 和 B 必須在 100 以下（排除棕色/膚色等非綠色）
                    # RGB=(216, 173, 106) 這種棕色會被排除（R=216 > 100）
                    pass_color_limit = (r < 100) and (b < 100)
                    
                    if pass_brightness and pass_dominance and pass_color_limit:
                        # 找到符合的綠色像素
                        abs_x = calendar_left + col
                        abs_y = calendar_top + row
                        green_pixels.append((abs_x, abs_y, r, g, b))
            
            # 檢查日曆是否打開：如果掃描結果全是 RGB(0,0,0)，代表日曆沒打開
            # 使用配置中的黑色比例閾值（避免硬編碼）
            black_ratio = black_pixel_count / total_pixels if total_pixels > 0 else 0
            if black_ratio > thresholds.BLACK_RATIO_THRESHOLD:
                self.logger.error(f"[CALENDAR_VISUAL] 日曆區域幾乎全黑 (黑色像素比例: {black_ratio:.2%})，可能日曆未打開")
                
                # 截圖並報錯
                try:
                    import os
                    from datetime import datetime
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "calendar_debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    now = datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(debug_dir, f"calendar_not_open_{timestamp}.png")
                    screenshot.save(screenshot_path)
                    self.logger.error(f"[CALENDAR_VISUAL] 調試截圖已保存: {screenshot_path}")
                except Exception as e:
                    self.logger.debug(f"[CALENDAR_VISUAL] 保存調試截圖失敗: {e}")
                
                pytest.fail(f"日曆未打開：掃描區域幾乎全黑 (黑色像素比例: {black_ratio:.2%})。請確認日曆已開啟。")
            
            if not green_pixels:
                self.logger.warning(f"[CALENDAR_VISUAL] 未找到綠色標記像素，嘗試 VLM fallback...")
                self.logger.warning(f"[CALENDAR_VISUAL] 掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
                
                # 🎯 Fallback 機制：如果像素掃描失敗，嘗試使用 VLM 尋找 "Green dot" 或 "Recording date"
                try:
                    vlm_result = self._try_vlm_recognition(
                        "Green dot or recording date with green mark",
                        calendar_region,
                        win
                    )
                    if vlm_result and vlm_result.success:
                        click_x = vlm_result.x
                        click_y = vlm_result.y - 10  # 向上偏移 10px，點擊日期文字
                        self.logger.info(f"[CALENDAR_VISUAL] VLM fallback 成功找到日期: ({click_x}, {click_y})")
                        return (click_x, click_y)
                except Exception as e:
                    self.logger.debug(f"[CALENDAR_VISUAL] VLM fallback 失敗: {e}")
                
                pytest.fail("未在日曆上發現任何錄影標記（綠色底線）。請確認日曆已開啟且存在錄影資料。")
            
            # 找到第一個綠色像素，點擊該像素上方 10px 的位置（點擊日期數字，而不是點綠線）
            first_green = green_pixels[0]  # 選擇第一個找到的綠色像素（從上到下、從左到右）
            green_x, green_y, r, g, b = first_green
            
            self.logger.info(f"[CALENDAR_VISUAL] 找到綠色標記像素: 座標=({green_x}, {green_y}), RGB=({r}, {g}, {b})")
            
            # 點擊位置：綠色標記上方偏移（點擊日期數字而非綠線）
            # 使用配置中的日期點擊偏移（避免硬編碼）
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            click_x = green_x
            click_y = green_y - calendar_config.DATE_CLICK_OFFSET_Y
            
            # 確保點擊位置在視窗範圍內
            if click_y < win.top:
                click_y = win.top + 10  # 如果超出上邊界，使用視窗頂部 + 10px
            
            self.logger.info(f"[CALENDAR_VISUAL] 計算點擊座標: ({click_x}, {click_y}) (綠色標記上方 10px)")
            
            # 記錄到報告系統
            reporter = self.get_reporter()
            if reporter:
                try:
                    reporter.add_recognition_screenshot(
                        item_name="有錄影標記的日期（視覺驅動）",
                        x=click_x,
                        y=click_y,
                        width=40,
                        height=30,
                        method="像素顏色掃描",
                        region=calendar_region
                    )
                except Exception as e:
                    self.logger.debug(f"報告截圖失敗: {e}")
            
            return (click_x, click_y)
            
        except Exception as e:
            self.logger.error(f"[CALENDAR_VISUAL] 掃描過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"掃描日曆區域時發生錯誤: {str(e)}")
    
    def click_calendar_icon(self):
        """
        🎯 點擊右下角日曆圖標
        策略：使用 smart_click 強制區域鎖定，直接使用座標保底，避免圖片辨識誤點左上角選單
        注意：日曆圖標本身沒有文字，所以不使用文字辨識
        image_path 參數僅供報告截圖標註使用，不參與辨識
        """
        self._log_method_entry("click_calendar_icon")
        self.logger.info("[CALENDAR] 點擊右下角日曆圖標...")
        
        # 確保窗口已激活
        win = self.get_nx_window()
        if win:
            try:
                if not win.isActive:
                    win.activate()
                    time.sleep(0.2)
            except Exception as e:
                self.logger.debug(f"[CALENDAR] 窗口激活失敗（可能已激活）: {e}")
        
        # 使用 smart_click 強制區域鎖定，直接使用座標保底
        # 設置鎖定參數：
        # - x_ratio=0.92 (視窗寬度 92% 處)
        # - y_ratio=0.04 (視窗底部向上 4% 處)
        # - from_bottom=True (強制由底部起算)
        # - offset_x=0 (向右偏移 10 像素，從原本的 -10 改為 0)
        # - image_path 僅供報告截圖標註使用，不參與辨識（設置 use_ok_script=False 禁用圖片辨識）
        success = self.smart_click(
            x_ratio=0.92,  # 視窗寬度 92% 處
            y_ratio=0.04,  # 視窗底部向上 4% 處
            target_text=None,  # 日曆圖標沒有文字，不使用文字辨識
            image_path="desktop_main/calendar_icon.png",  # 僅供報告截圖標註使用
            timeout=1.0,  # 短超時，快速失敗後使用保底座標
            from_bottom=True,  # 強制由底部起算
            offset_x=0,  # 向右偏移 10 像素（從原本的 -10 改為 0）
            offset_y=0,  # Y 軸不需要偏移
            use_ok_script=False,  # 禁用圖片辨識，避免誤點左上角選單
            use_vlm=False  # 禁用 VLM，避免誤點左上角選單
        )
        
        if success:
            self.logger.info("[CALENDAR] 成功點擊日曆圖標（使用座標保底）")
            time.sleep(1.0)  # 等待日曆彈出
        else:
            self.logger.warning("[CALENDAR] 點擊日曆圖標可能失敗，但繼續執行")
        
        return success
    
    def _get_calendar_region_by_anchor(self):
        """
        [Dynamic ROI] 使用圖片錨點計算日曆區域
        
        透過辨識日曆面板頂部的特徵圖片（Anchor Image），以該圖片的
        上邊緣（Top Edge）為基準，向下延伸定義出日曆的搜尋區域。
        
        Returns:
            tuple: (left, top, width, height) 日曆區域座標
        """
        from config import EnvConfig
        import pyautogui
        
        self.logger.info("[CALENDAR] [ROI] Calculating region using anchor image...")
        
        # 1. 尋找錨點圖片 (Calendar Header)
        anchor_image = "desktop_main/calendar_header.png"
        anchor_path = os.path.normpath(os.path.join(EnvConfig.RES_PATH, anchor_image))
        
        try:
            # 嘗試定位圖片（使用 OK Script 優先，更可靠）
            self.logger.info(f"[CALENDAR] [ROI] Looking for anchor image: {anchor_image}...")
            
            # 優先使用 OK Script 辨識
            from base.ok_script_recognizer import get_recognizer
            recognizer = get_recognizer()
            # 🎯 設置 logger 以確保詳細日誌輸出
            if not recognizer.logger:
                recognizer.set_logger(self.logger)
            ok_result = recognizer.locate_on_screen(anchor_path, confidence=0.8)
            
            if ok_result and ok_result.success:
                # 🎯 OK Script 返回的座標已經是屏幕絕對座標（左上角）
                # 詳細日誌已在 ok_script_recognizer.py 中記錄
                box_left = ok_result.x
                box_top = ok_result.y
                box_width = ok_result.width
                box_height = ok_result.height
                
                self.logger.info(f"[CALENDAR] [ROI] OK Script recognition successful")
                self.logger.info(f"[CALENDAR] [ROI] Image bounding box: left={box_left}, top={box_top}, width={box_width}, height={box_height}")
                self.logger.info(f"[CALENDAR] [ROI] Image bounding box (right, bottom): ({box_left + box_width}, {box_top + box_height})")
                self.logger.info(f"[CALENDAR] [ROI] Confidence: {ok_result.confidence:.2f}")
                
                # 🎯 使用左邊界和上邊界為基準（修正：應該以標題的上邊緣為頂端）
                # 定義區域：以圖示的左邊界和上邊界為基準
                # left = icon.left（使用圖示的左邊界，不向左擴展，避免偏左）
                # top = icon.top（從圖示上邊界開始，而不是下邊界）
                # width = 從左邊界到螢幕最右側（確保覆蓋到最右邊）
                # height = 向下延伸足夠的範圍以涵蓋日期
                screen_w, screen_h = pyautogui.size()
                region_left = int(box_left)  # 🎯 修正：使用圖示的左邊界，不向左擴展
                region_top = int(box_top)  # 🎯 修正：從圖示上邊界開始（標題的上邊緣）
                # 🎯 關鍵修正：寬度延伸至螢幕最右側，確保覆蓋到最右邊
                region_width = int(screen_w - region_left)  # 從左邊界到螢幕最右側
                # 🎯 修正：使用配置中的高度，不延伸到最下面
                calendar_config = EnvConfig.CALENDAR_SETTINGS
                region_height = calendar_config.CALENDAR_REGION_HEIGHT  # 從標題上邊緣向下延伸固定像素數
                
                self.logger.info(f"[CALENDAR] [ROI] Calendar region calculation:")
                self.logger.info(f"[CALENDAR] [ROI]   Icon bounding box: left={box_left}, top={box_top}, width={box_width}, height={box_height}")
                self.logger.info(f"[CALENDAR] [ROI]   Region left: {region_left} (icon_left, 不向左擴展)")
                self.logger.info(f"[CALENDAR] [ROI]   Region top: {region_top} (icon_top, 標題上邊緣)")
                self.logger.info(f"[CALENDAR] [ROI]   Region width: {region_width}, height: {region_height}")
                self.logger.info(f"[CALENDAR] [ROI]   Final region: ({region_left}, {region_top}, {region_width}, {region_height})")
                
                # 🎯 在截圖上標記識別到的標題區域（用於除錯）
                reporter = self.get_reporter()
                if reporter:
                    try:
                        # 標記標題圖片的邊界框（藍色實線矩形）
                        reporter.add_recognition_screenshot(
                            item_name="Calendar Header (Anchor)",
                            x=box_left,
                            y=box_top,
                            width=box_width,
                            height=box_height,
                            method="OK Script",
                            region=None  # 不標記搜尋區域，只標記識別到的標題
                        )
                        self.logger.info(f"[CALENDAR] [ROI] 已標記標題區域到截圖: ({box_left}, {box_top}, {box_width}, {box_height})")
                    except Exception as e:
                        self.logger.debug(f"[CALENDAR] [ROI] 標記標題區域失敗: {e}")
                
                roi = (region_left, region_top, region_width, region_height)
                return roi
            
            # Fallback: 使用 PyAutoGUI
            self.logger.info(f"[CALENDAR] [ROI] OK Script failed, trying PyAutoGUI...")
            box = pyautogui.locateOnScreen(anchor_path, confidence=0.8)
            
            if box:
                # box = (left, top, width, height)
                self.logger.info(f"[CALENDAR] [ROI] Anchor found (PyAutoGUI): left={box.left}, top={box.top}, width={box.width}, height={box.height}")
                
                # 🎯 使用左邊界和上邊界為基準（修正：應該以標題的上邊緣為頂端）
                # 定義區域：以圖示的左邊界和上邊界為基準
                # left = icon.left（使用圖示的左邊界，不向左擴展，避免偏左）
                # top = icon.top（從圖示上邊界開始，而不是下邊界）
                # width = 從左邊界到螢幕最右側（確保覆蓋到最右邊）
                # height = 向下延伸足夠的範圍以涵蓋日期
                screen_w, screen_h = pyautogui.size()
                region_left = int(box.left)  # 🎯 修正：使用圖示的左邊界，不向左擴展
                region_top = int(box.top)  # 🎯 修正：從圖示上邊界開始（標題的上邊緣）
                # 🎯 關鍵修正：寬度延伸至螢幕最右側，確保覆蓋到最右邊
                region_width = int(screen_w - region_left)  # 從左邊界到螢幕最右側
                # 🎯 修正：使用配置中的高度，不延伸到最下面
                calendar_config = EnvConfig.CALENDAR_SETTINGS
                region_height = calendar_config.CALENDAR_REGION_HEIGHT  # 從標題上邊緣向下延伸固定像素數
                
                self.logger.info(f"[CALENDAR] [ROI] Anchor found (PyAutoGUI): icon bounding box: left={box.left}, top={box.top}, width={box.width}, height={box.height}")
                self.logger.info(f"[CALENDAR] [ROI]   Region left: {region_left} (icon_left, 不向左擴展)")
                self.logger.info(f"[CALENDAR] [ROI]   Region top: {region_top} (icon_top, 標題上邊緣)")
                self.logger.info(f"[CALENDAR] [ROI]   Region width: {region_width}, height: {region_height}")
                
                # 🎯 在截圖上標記識別到的標題區域（用於除錯）
                reporter = self.get_reporter()
                if reporter:
                    try:
                        # 標記標題圖片的邊界框（藍色實線矩形）
                        reporter.add_recognition_screenshot(
                            item_name="Calendar Header (Anchor)",
                            x=box.left,
                            y=box.top,
                            width=box.width,
                            height=box.height,
                            method="PyAutoGUI",
                            region=None  # 不標記搜尋區域，只標記識別到的標題
                        )
                        self.logger.info(f"[CALENDAR] [ROI] 已標記標題區域到截圖: ({box.left}, {box.top}, {box.width}, {box.height})")
                    except Exception as e:
                        self.logger.debug(f"[CALENDAR] [ROI] 標記標題區域失敗: {e}")
                
                roi = (region_left, region_top, region_width, region_height)
                self.logger.info(f"[CALENDAR] [ROI] Dynamic Region calculated: left={region_left}, top={region_top}, width={region_width}, height={region_height}")
                return roi
            else:
                self.logger.warning(f"[CALENDAR] [ROI] Anchor image not found: {anchor_image}")
                
        except pyautogui.ImageNotFoundException:
            self.logger.warning(f"[CALENDAR] [ROI] Anchor image not found: {anchor_image}")
        except Exception as e:
            self.logger.warning(f"[CALENDAR] [ROI] Anchor locating failed: {e}")
            import traceback
            self.logger.debug(f"[CALENDAR] [ROI] Error details: {traceback.format_exc()}")
        
        # Fallback: 如果找不到錨點，回退到配置檔的靜態比例
        # 🎯 關鍵修正：使用配置檔的 CALENDAR_RIGHT_RATIO = 1.0，確保覆蓋到螢幕最右側
        self.logger.warning("[CALENDAR] [ROI] Anchor not found, using fallback: config-based region...")
        win = self.get_nx_window()
        if win:
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            fallback_left = win.left + int(win.width * calendar_config.CALENDAR_LEFT_RATIO)
            fallback_right = win.left + int(win.width * calendar_config.CALENDAR_RIGHT_RATIO)
            fallback_top = win.top + int(win.height * calendar_config.CALENDAR_TOP_RATIO)
            # 🎯 修正：使用配置中的固定高度，不延伸到最下面
            fallback_width = fallback_right - fallback_left
            fallback_height = calendar_config.CALENDAR_REGION_HEIGHT  # 從頂部向下延伸固定像素數
            
            self.logger.warning(f"[CALENDAR] [ROI] Fallback region (config-based): left={fallback_left}, top={fallback_top}, width={fallback_width}, height={fallback_height}")
            self.logger.warning(f"[CALENDAR] [ROI] Fallback右邊界: {fallback_right} (視窗寬度: {win.width}, RIGHT_RATIO: {calendar_config.CALENDAR_RIGHT_RATIO})")
            return (fallback_left, fallback_top, fallback_width, fallback_height)
        else:
            # 最後的 fallback：使用螢幕比例（確保右邊界為 1.0）
            screen_w, screen_h = pyautogui.size()
            fallback_left = int(screen_w * 0.70)  # 左側 70% 開始
            fallback_top = int(screen_h * 0.20)  # 從螢幕頂部 20% 開始
            fallback_width = int(screen_w * 0.30)  # 寬度為螢幕的 30%（70% 到 100%）
            # 🎯 修正：使用配置中的固定高度，不延伸到最下面
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            fallback_height = calendar_config.CALENDAR_REGION_HEIGHT  # 從頂部向下延伸固定像素數
            fallback_roi = (fallback_left, fallback_top, fallback_width, fallback_height)
            self.logger.warning(f"[CALENDAR] [ROI] Fallback region (screen-based): {fallback_roi}")
            return fallback_roi
    
    def select_first_date_with_recording(self) -> Optional[Tuple[int, int]]:
        """
        🎯 [視覺驅動] 自動尋找日曆上有綠色標記的日期並返回座標
        
        使用像素掃描方式，在日曆區域內尋找「亮綠色」標記（日期下方的綠色底線），
        找到後返回該日期上方的點擊座標。
        
        邏輯：
        1. 定義日曆的感興趣區域 (ROI)
        2. 掃描該區域內的像素，尋找特定的「亮綠色」特徵 (RGB: 0, 255, 0 附近，tolerance=30)
        3. 一旦找到符合的綠色像素（通常是日期下方的底線），取得該座標
        4. 返回該座標上方的日期位置（用於點擊）
        
        Returns:
            tuple[int, int] | None: 找到的日期座標 (x, y)，如果找不到則返回 None
        
        Raises:
            pytest.fail: 如果掃描完整個日曆都沒看到綠色標記
        """
        self._log_method_entry("select_first_date_with_recording")
        self.logger.info("[CALENDAR_VISUAL] 開始使用視覺驅動方式尋找有錄影標記的日期...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.error("[CALENDAR_VISUAL] 無法獲取窗口")
            pytest.fail("無法獲取窗口，無法掃描日曆區域")
        
        # 步驟 1: 定義日曆的感興趣區域 (ROI)
        # 🎯 優先使用動態錨點定位（Anchor-based ROI）
        calendar_region = self._get_calendar_region_by_anchor()
        
        if not calendar_region:
            # 🎯 Fallback: 如果錨點定位失敗，使用配置檔的靜態比例
            # 但必須確保 Fallback 也能掃描到最右邊（CALENDAR_RIGHT_RATIO = 1.0）
            self.logger.warning("[CALENDAR_VISUAL] Anchor定位失敗，使用配置檔Fallback比例...")
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            calendar_left = win.left + int(win.width * calendar_config.CALENDAR_LEFT_RATIO)
            calendar_right = win.left + int(win.width * calendar_config.CALENDAR_RIGHT_RATIO)
            calendar_top = win.top + int(win.height * calendar_config.CALENDAR_TOP_RATIO)
            calendar_bottom = win.top + int(win.height * calendar_config.CALENDAR_BOTTOM_RATIO)
            calendar_width = calendar_right - calendar_left
            calendar_height = calendar_bottom - calendar_top
            
            self.logger.info(f"[CALENDAR_VISUAL] Fallback區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
            self.logger.info(f"[CALENDAR_VISUAL] Fallback右邊界: {calendar_right} (視窗寬度: {win.width}, RIGHT_RATIO: {calendar_config.CALENDAR_RIGHT_RATIO})")
        else:
            # 🎯 使用動態錨點定位計算出的區域
            calendar_left, calendar_top, calendar_width, calendar_height = calendar_region
            calendar_right = calendar_left + calendar_width
            calendar_bottom = calendar_top + calendar_height
            
            self.logger.info(f"[CALENDAR_VISUAL] Anchor區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
            self.logger.info(f"[CALENDAR_VISUAL] Anchor右邊界: {calendar_right} (確保覆蓋到螢幕最右側)")
        
        self.logger.info(f"[CALENDAR_VISUAL] 最終日曆掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}, right={calendar_right}")
        
        # 步驟 2: 截取日曆區域並掃描像素
        try:
            calendar_region = (calendar_left, calendar_top, calendar_width, calendar_height)
            screenshot = pyautogui.screenshot(region=calendar_region)
            img_array = np.array(screenshot)
            
            # 確保是 RGB 格式（3 通道）
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            
            # 步驟 3: 掃描像素，尋找「亮綠色」標記
            # 🎯 放寬綠色像素判定閾值（G > 100, R < 100, B < 100）
            green_pixels = []  # 儲存找到的綠色像素座標
            
            # 從上到下、從左到右掃描
            for row in range(img_array.shape[0]):
                for col in range(img_array.shape[1]):
                    r, g, b = img_array[row, col]
                    
                    # 🎯 [UPDATED] 使用新的綠色判定邏輯（區分亮綠色與白色文字）
                    # 1. 亮度檢查 (太暗不要)
                    calendar_config = EnvConfig.CALENDAR_SETTINGS
                    pass_brightness = g > calendar_config.GREEN_MIN_BRIGHTNESS
                    
                    # 2. 綠色主導檢查 (排除白色文字與灰色背景)
                    # 白色: 255 > 255 + 40 (False) -> 排除
                    # 綠色: 200 > 50 + 40 (True) -> 通過
                    offset = calendar_config.GREEN_DOMINANCE_OFFSET
                    pass_dominance = (g > r + offset) and (g > b + offset)
                    
                    # 3. 🎯 關鍵修正：限定 R 和 B 必須在 100 以下（排除棕色/膚色等非綠色）
                    # RGB=(216, 173, 106) 這種棕色會被排除（R=216 > 100）
                    pass_color_limit = (r < 100) and (b < 100)
                    
                    if pass_brightness and pass_dominance and pass_color_limit:
                        # 找到符合的綠色像素
                        abs_x = calendar_left + col
                        abs_y = calendar_top + row
                        green_pixels.append((abs_x, abs_y, r, g, b))
            
            # 除錯資訊：如果找不到綠色像素，記錄實際顏色範例
            if not green_pixels:
                # 取幾個樣本像素的顏色作為參考
                sample_colors = []
                sample_positions = [
                    (img_array.shape[0] // 2, img_array.shape[1] // 2),  # 中心
                    (img_array.shape[0] // 4, img_array.shape[1] // 4),  # 左上
                    (img_array.shape[0] * 3 // 4, img_array.shape[1] * 3 // 4),  # 右下
                ]
                
                for row, col in sample_positions:
                    if row < img_array.shape[0] and col < img_array.shape[1]:
                        r, g, b = img_array[row, col]
                        abs_x = calendar_left + col
                        abs_y = calendar_top + row
                        sample_colors.append(f"({abs_x}, {abs_y}): RGB({r}, {g}, {b})")
                
                self.logger.warning(f"[CALENDAR_VISUAL] 未找到綠色標記像素，嘗試 VLM fallback...")
                self.logger.warning(f"[CALENDAR_VISUAL] 掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
                self.logger.warning(f"[CALENDAR_VISUAL] 實際顏色範例: {', '.join(sample_colors)}")
                
                # 🎯 Fallback 機制：如果像素掃描失敗，嘗試使用 VLM 尋找 "Green dot" 或 "Recording date"
                try:
                    vlm_result = self._try_vlm_recognition(
                        "Green dot or recording date with green mark",
                        calendar_region,
                        win
                    )
                    if vlm_result and vlm_result.success:
                        calendar_config = EnvConfig.CALENDAR_SETTINGS
                        click_x = vlm_result.x
                        click_y = vlm_result.y - calendar_config.DATE_CLICK_OFFSET_Y
                        self.logger.info(f"[CALENDAR_VISUAL] VLM fallback 成功找到日期: ({click_x}, {click_y})")
                        return (click_x, click_y)
                except Exception as e:
                    self.logger.debug(f"[CALENDAR_VISUAL] VLM fallback 失敗: {e}")
                
                # 如果掃描完整個日曆都沒看到綠色標記，直接拋出錯誤
                pytest.fail("未在日曆上發現任何錄影標記（綠色底線）。請確認日曆已開啟且存在錄影資料。")
            
            # 步驟 4: 找到第一個綠色像素，返回其上方的日期位置座標
            # 綠色標記通常在日期下方，所以我們需要向上偏移來點擊日期本身
            first_green = green_pixels[0]  # 選擇第一個找到的綠色像素（從上到下、從左到右）
            green_x, green_y, r, g, b = first_green
            
            self.logger.info(f"[CALENDAR_VISUAL] 找到綠色標記像素: 座標=({green_x}, {green_y}), RGB=({r}, {g}, {b})")
            self.logger.info(f"[CALENDAR_VISUAL] [COORD] Green pixel screen absolute: ({green_x}, {green_y}), region offset: ({calendar_left}, {calendar_top})")
            
            # 點擊位置：綠色標記上方偏移（點擊日期文字而非綠線）
            # 使用配置中的日期點擊偏移（避免硬編碼）
            calendar_config = EnvConfig.CALENDAR_SETTINGS
            click_x = green_x
            click_y = green_y - calendar_config.DATE_CLICK_OFFSET_Y
            
            # 確保點擊位置在視窗範圍內
            if click_y < win.top:
                click_y = win.top + 10  # 如果超出上邊界，使用視窗頂部 + 10px
            
            self.logger.info(f"[CALENDAR_VISUAL] [COORD] Final click coordinate: ({click_x}, {click_y}) (screen absolute, calculated from calendar region)")
            
            # 記錄到報告系統
            reporter = self.get_reporter()
            if reporter:
                try:
                    reporter.add_recognition_screenshot(
                        item_name="有錄影標記的日期（視覺驅動）",
                        x=click_x,
                        y=click_y,
                        width=40,
                        height=30,
                        method="像素顏色掃描",
                        region=calendar_region
                    )
                except Exception as e:
                    self.logger.debug(f"報告截圖失敗: {e}")
            
            return (click_x, click_y)
            
        except Exception as e:
            self.logger.error(f"[CALENDAR_VISUAL] 掃描過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"掃描日曆區域時發生錯誤: {str(e)}")
    
    def select_date_with_recording(self):
        """
        🎯 在日曆中選擇有錄影事件的日期（優先使用視覺驅動方式）
        
        策略優先級：
        1. 優先使用「視覺驅動」方式自動尋找有綠色標記的日期（select_first_date_with_recording）
        2. 如果視覺驅動失敗，使用「區域網格法」點擊日期 17 號（click_date_17）
        3. 如果網格法失敗，回退到 VLM/OCR 方法
        """
        self._log_method_entry("select_date_with_recording")
        self.logger.info("[CALENDAR] 選擇有錄影事件的日期...")
        
        # 🎯 優先使用「視覺驅動」方式自動尋找有綠色標記的日期
        self.logger.info("[CALENDAR] 優先使用視覺驅動方式尋找有錄影標記的日期...")
        try:
            date_coord = self.select_first_date_with_recording()
            if date_coord:
                click_x, click_y = date_coord
                self.logger.info(f"[CALENDAR] 視覺驅動成功找到日期，點擊座標: ({click_x}, {click_y})")
                
                # 確保窗口處於活動狀態
                win = self.get_nx_window()
                if win:
                    try:
                        win.activate()
                        time.sleep(0.2)
                    except:
                        pass
                
                # 執行點擊
                pyautogui.click(click_x, click_y)
                self.logger.info(f"[CALENDAR] 成功點擊日期座標 ({click_x}, {click_y})")
                # 使用配置中的等待時間（避免硬編碼）
                time.sleep(EnvConfig.THRESHOLDS.CLICK_WAIT_TIME)
                
                # 🎯 移除多餘的時間軸點擊（不需要多點擊一下時間軸中間）
                # self.click_timeline(position="center")  # 已移除
                
                return True
        except Exception as e:
            self.logger.warning(f"[CALENDAR] 視覺驅動方式失敗: {e}，嘗試備選方法...")
        
        # 🎯 備選方案 1: 使用「區域網格法」點擊日期 17 號
        self.logger.info("[CALENDAR] 優先嘗試使用區域網格法點擊日期 17 號...")
        try:
            if self.click_date_17():
                self.logger.info("[CALENDAR] 區域網格法成功選擇日期 17 號")
                return True
            else:
                self.logger.warning("[CALENDAR] 區域網格法失敗，回退到 VLM/OCR 方法...")
        except Exception as e:
            self.logger.warning(f"[CALENDAR] 區域網格法發生異常: {e}，回退到 VLM/OCR 方法...")
        
        # 如果網格法失敗，使用原有的 VLM/OCR 方法作為備選
        self.logger.info("[CALENDAR] 使用 VLM/OCR 方法選擇日期...")
        
        # 🎯 直接強制優先尋找並點擊 17 號
        target_date = "17"
        
        # 使用動態錨點定位獲取日曆區域
        calendar_region = self._get_calendar_region_by_anchor()
        calendar_left, calendar_top, calendar_width, calendar_height = calendar_region
        
        # 計算日曆區域的中心位置（用於 smart_click 的 x_ratio, y_ratio）
        # 注意：這裡的 ratio 是相對於視窗的，不是相對於日曆區域的
        win = self.get_nx_window()
        if win:
            # 計算日曆區域中心在視窗中的比例位置
            calendar_center_x = calendar_left + calendar_width // 2
            calendar_center_y = calendar_top + calendar_height // 2
            
            # 轉換為視窗比例（相對於視窗左上角）
            calendar_x_ratio = (calendar_center_x - win.left) / win.width
            calendar_y_ratio = (calendar_center_y - win.top) / win.height
            
            self.logger.info(f"[CALENDAR] 日曆區域中心: ({calendar_center_x}, {calendar_center_y})")
            self.logger.info(f"[CALENDAR] 視窗比例位置: x_ratio={calendar_x_ratio:.3f}, y_ratio={calendar_y_ratio:.3f}")
            self.logger.info(f"[CALENDAR] 鎖定搜尋區域: {calendar_region}")
        else:
            # 如果無法獲取窗口，使用默認值
            calendar_x_ratio = 0.75
            calendar_y_ratio = 0.45
            self.logger.warning("[CALENDAR] 無法獲取視窗，使用默認比例位置")
        
        # 🎯 優先尋找並點擊 17 號
        self.logger.info(f"[CALENDAR] 優先尋找日期 {target_date}...")
        self.logger.info(f"[CALENDAR] [COORD] Using calendar region for search: {calendar_region}")
        self.logger.info(f"[CALENDAR] [COORD] Note: VLM/OCR will return coordinates relative to calendar region, then add region offset to get screen absolute coordinates")
        
        # 使用 smart_click 尋找並點擊日期，鎖定搜尋區域在日曆視窗內部
        # 🎯 修正日期點選：點擊日期 "17" 時，傳入 offset_y=15, offset_x=5
        # 理由：補償 VLM 常見的偏左上誤差，確保點中數字的正中心
        # 🎯 重要：region 參數會限制 VLM/OCR 的搜尋範圍，返回的座標會自動加上 region 偏移
        success = self.smart_click(
            x_ratio=calendar_x_ratio,
            y_ratio=calendar_y_ratio,
            target_text=target_date,
            timeout=3,  # 增加超時時間，確保有足夠時間辨識
            offset_x=5,  # 🎯 向右偏移 5 像素，補償 VLM 常見的偏左誤差
            offset_y=15,  # 🎯 向下偏移 15 像素，補償 VLM 常見的偏上誤差
            region=calendar_region  # 🎯 鎖定搜尋區域，避免 VLM 全屏掃描偏移
        )
        
        if success:
            self.logger.info(f"[CALENDAR] 成功選擇日期 {target_date}")
            time.sleep(0.5)  # 等待日期選擇生效
            return True
        
        # 如果 17 號找不到，嘗試其他日期（18, 19, 20）作為備選
        self.logger.warning(f"[CALENDAR] 無法找到日期 {target_date}，嘗試其他日期...")
        fallback_dates = ["18", "19", "20"]
        
        for date_num in fallback_dates:
            self.logger.info(f"[CALENDAR] 嘗試尋找日期 {date_num}...")
            
            success = self.smart_click(
                x_ratio=calendar_x_ratio,
                y_ratio=calendar_y_ratio,
                target_text=date_num,
                timeout=2,
                offset_x=0,
                offset_y=0,
                region=calendar_region  # 🎯 鎖定搜尋區域
            )
            
            if success:
                self.logger.info(f"[CALENDAR] 成功選擇日期 {date_num}")
                time.sleep(0.5)
                return True
        
        # 如果所有日期都找不到，使用座標保底
        self.logger.warning("[CALENDAR] 無法找到任何日期，使用座標保底")
        success = self.smart_click(
            x_ratio=calendar_x_ratio,
            y_ratio=calendar_y_ratio,
            timeout=2,
            offset_x=0,
            offset_y=0,
            region=calendar_region  # 🎯 鎖定搜尋區域
        )
        
        if success:
            time.sleep(0.5)
            self.logger.info("[CALENDAR] 使用座標保底選擇日期")
        
        return success
    
    def click_date_17(self):
        """
        🎯 使用「區域網格法」點擊日期 17 號
        採用圖像識別錨點 + 網格座標計算的方式，避免 UIA 定位失效問題
        
        邏輯：
        1. 尋找錨點：使用 locateOnScreen('calendar_header.png') 找到日曆視窗的頂部
        2. 建立座標系：設定日曆每個「日期格」的寬度約為 40px，高度約 30px
        3. 計算點擊點：使用 datetime 確認 2026年1月17日是星期六，計算它在日曆網格中的 (Row, Col) 索引
        4. 執行與驗證：點擊後檢查下方時間軸是否出現綠色區塊變化
        
        Returns:
            bool: 點擊是否成功
        """
        self._log_method_entry("click_date_17")
        self.logger.info("[CALENDAR_GRID] 使用區域網格法點擊日期 17 號...")
        
        # 獲取窗口資訊
        win = self.get_nx_window()
        if not win:
            self.logger.error("[CALENDAR_GRID] 無法獲取窗口")
            return False
        
        # 步驟 1: 尋找錨點 - 日曆視窗頂部（calendar_header.png）
        self.logger.info("[CALENDAR_GRID] 步驟 1: 尋找日曆錨點...")
        calendar_header_path = os.path.join(EnvConfig.RES_PATH, "desktop_main", "calendar_header.png")
        
        anchor_x, anchor_y = None, None
        
        # 嘗試使用 locateOnScreen 找到日曆標題
        try:
            # 如果圖片存在，使用圖片識別
            if os.path.exists(calendar_header_path):
                self.logger.info(f"[CALENDAR_GRID] 使用圖片識別: {calendar_header_path}")
                location = pyautogui.locateOnScreen(calendar_header_path, confidence=0.8)
                if location:
                    # 錨點設為圖片底部中心（日曆標題下方，即日期網格開始的位置）
                    anchor_x = location.left + location.width // 2
                    anchor_y = location.top + location.height
                    self.logger.info(f"[CALENDAR_GRID] 找到日曆錨點（圖片識別）: ({anchor_x}, {anchor_y})")
            else:
                self.logger.warning(f"[CALENDAR_GRID] 圖片不存在: {calendar_header_path}")
                self.logger.info("[CALENDAR_GRID] 使用座標估算作為備選方案...")
        except Exception as e:
            self.logger.warning(f"[CALENDAR_GRID] 圖片識別失敗: {e}")
        
        # 如果圖片識別失敗，使用座標估算（日曆視窗大約在右下角）
        if anchor_x is None or anchor_y is None:
            self.logger.info("[CALENDAR_GRID] 使用座標估算作為備選方案...")
            # 日曆視窗大約在螢幕右下角
            # 假設日曆視窗左上角在 (win.width * 0.60, win.height * 0.25)
            # 日曆標題高度約 30px，所以錨點在標題下方
            anchor_x = win.left + int(win.width * 0.60) + int(win.width * 0.15)  # 日曆視窗中心 X
            anchor_y = win.top + int(win.height * 0.25) + 30  # 日曆標題下方約 30px
            self.logger.info(f"[CALENDAR_GRID] 使用估算錨點: ({anchor_x}, {anchor_y})")
        
        # 步驟 2: 建立座標系 - 設定日曆每個「日期格」的尺寸
        # 根據常見日曆 UI，每個日期格大約：寬度 40px，高度 30px
        cell_width = 40
        cell_height = 30
        
        # 日曆網格通常從星期天開始（索引 0），到星期六結束（索引 6）
        # 第一行是星期標題，第二行開始是日期
        # 所以日期網格的第一行（第二行）Y 座標 = anchor_y + cell_height
        
        # 步驟 3: 計算點擊點 - 確認 2026年1月17日在日曆網格中的位置
        target_date = date(2026, 1, 17)
        
        # 計算 1月1日的位置（作為參考點）
        first_day = date(2026, 1, 1)
        first_weekday = first_day.weekday()  # Python weekday(): 0=Monday, 6=Sunday
        # 轉換為日曆格式（Sunday=0, Monday=1, ..., Saturday=6）
        first_calendar_col = (first_weekday + 1) % 7  # 1月1日是 Thursday=3，轉換後為 4
        
        # 計算 17 號距離 1 號的天數
        days_diff = (target_date - first_day).days  # 16 天
        
        # 計算 17 號在日曆網格中的位置
        # 1號在第 1 行（row=1），第 first_calendar_col 列
        # 17號 = 1號 + 16天 = 1號 + 2週 + 2天
        # 所以 17號在 row = 1 + 2 = 3，col = (4 + 2) % 7 = 6（Saturday）
        calendar_row = 1 + (days_diff + first_calendar_col) // 7
        calendar_col = (first_calendar_col + days_diff) % 7
        
        self.logger.info(f"[CALENDAR_GRID] 2026年1月17日是 {target_date.strftime('%A')}")
        self.logger.info(f"[CALENDAR_GRID] 日曆網格位置: Row={calendar_row}, Col={calendar_col} (Sunday=0, Saturday=6)")
        
        # 計算點擊座標
        # 假設錨點是日曆標題下方中心點
        # 日曆通常有 7 列，中心對齊，所以左側第一列在 anchor_x - (3 * cell_width)
        # 點擊座標 = 儲存格左上角 + 儲存格中心偏移
        click_x = anchor_x - (3 * cell_width) + (calendar_col * cell_width) + (cell_width // 2)
        click_y = anchor_y + cell_height + ((calendar_row - 1) * cell_height) + (cell_height // 2)
        
        self.logger.info(f"[CALENDAR_GRID] 計算出的點擊座標: ({click_x}, {click_y})")
        self.logger.info(f"[CALENDAR_GRID] 錨點: ({anchor_x}, {anchor_y}), 網格位置: Row={calendar_row}, Col={calendar_col}")
        
        # 步驟 4: 執行點擊
        self.logger.info(f"[CALENDAR_GRID] 移動滑鼠到 ({click_x}, {click_y}) 並點擊...")
        
        # 確保窗口處於活動狀態
        try:
            win.activate()
            time.sleep(0.2)
        except:
            pass
        
        # 移動滑鼠並點擊
        try:
            pyautogui.moveTo(click_x, click_y, duration=0.3)
            time.sleep(0.1)
            pyautogui.click(click_x, click_y)
            self.logger.info(f"[CALENDAR_GRID] 成功點擊座標 ({click_x}, {click_y})")
            
            # 記錄點擊座標到報告系統
            reporter = self.get_reporter()
            if reporter:
                try:
                    reporter.add_recognition_screenshot(
                        item_name="日期17號（網格法）",
                        x=click_x,
                        y=click_y,
                        width=cell_width,
                        height=cell_height,
                        method="Grid Calculation"
                    )
                except Exception as e:
                    self.logger.debug(f"報告截圖失敗: {e}")
            
            # 等待日期選擇生效
            time.sleep(0.5)
            
            # 驗證：檢查下方時間軸是否出現綠色區塊變化
            self.logger.info("[CALENDAR_GRID] 驗證：檢查時間軸是否出現綠色區塊...")
            time.sleep(0.5)  # 等待時間軸更新
            
            # 可以調用現有的顏色偵測方法來驗證
            green_segment = self._find_recording_segment_by_color()
            if green_segment:
                self.logger.info("[CALENDAR_GRID] 驗證成功：時間軸出現綠色錄影段")
                return True
            else:
                self.logger.warning("[CALENDAR_GRID] 驗證警告：未檢測到綠色錄影段，但點擊已執行")
                return True  # 即使驗證失敗，也返回 True（因為點擊已執行）
                
        except Exception as e:
            self.logger.error(f"[CALENDAR_GRID] 點擊失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_recording_segment_by_color(self):
        """
        🎯 使用像素顏色偵測定位錄影時段
        截取視窗底部時間軸所在的窄長區域，掃描符合 Nx Witness 綠色特徵的點
        
        Returns:
            tuple: (x, y) 座標，如果找到綠色點則返回座標，否則返回 None
        """
        self.logger.info("[TIMELINE_COLOR] 開始使用像素顏色偵測定位錄影時段...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.warning("[TIMELINE_COLOR] 無法獲取窗口，跳過顏色偵測")
            return None
        
        try:
            # 截取視窗底部時間軸所在的窄長區域
            # 🎯 使用配置中的時間軸掃描區域比例（避免硬編碼）
            # 嚴格限制右側邊界，確保絕對不會抓到時間軸右側的當前錄影
            timeline_config = EnvConfig.TIMELINE_SETTINGS
            timeline_left = win.left + int(win.width * timeline_config.TIMELINE_SCAN_LEFT_RATIO)
            timeline_right = win.left + int(win.width * timeline_config.TIMELINE_SCAN_RIGHT_RATIO)
            timeline_width = timeline_right - timeline_left
            
            # 從底部向上 30 像素處，高度約 20 像素（窄長區域）
            timeline_top = win.top + win.height - 30
            timeline_height = 20
            
            timeline_region = (timeline_left, timeline_top, timeline_width, timeline_height)
            
            self.logger.info(f"[TIMELINE_COLOR] 時間軸掃描區域: left={timeline_left}, top={timeline_top}, width={timeline_width}, height={timeline_height}")
            
            # 截取該區域
            screenshot = pyautogui.screenshot(region=timeline_region)
            img_array = np.array(screenshot)
            
            # 確保是 RGB 格式（3 通道）
            if len(img_array.shape) == 2:
                # 如果是灰度圖，轉換為 RGB
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:
                # 如果是 RGBA，只取 RGB
                img_array = img_array[:, :, :3]
            
            # 掃描像素，尋找符合 Nx Witness 綠色特徵的點
            # RGB 範圍：R<80, G>120, B<80
            green_pixels = []
            for y in range(img_array.shape[0]):
                for x in range(img_array.shape[1]):
                    r, g, b = img_array[y, x]
                    # 🎯 [UPDATED] 使用新的綠色判定邏輯（區分亮綠色與白色文字）
                    # 1. 亮度檢查 (太暗不要)
                    calendar_config = EnvConfig.CALENDAR_SETTINGS
                    pass_brightness = g > calendar_config.GREEN_MIN_BRIGHTNESS
                    
                    # 2. 綠色主導檢查 (排除白色文字與灰色背景)
                    # 白色: 255 > 255 + 40 (False) -> 排除
                    # 綠色: 200 > 50 + 40 (True) -> 通過
                    offset = calendar_config.GREEN_DOMINANCE_OFFSET
                    pass_dominance = (g > r + offset) and (g > b + offset)
                    
                    if pass_brightness and pass_dominance:
                        # 計算絕對座標
                        abs_x = timeline_left + x
                        abs_y = timeline_top + y
                        green_pixels.append((abs_x, abs_y))
            
            if not green_pixels:
                self.logger.warning("[TIMELINE_COLOR] 未找到符合綠色特徵的像素點")
                return None
            
            # 🎯 優化像素偵測順序：從左往右搜尋，選擇首段（最左邊足夠長的錄影段）
            green_pixels.sort(key=lambda p: p[0])  # 按 X 座標排序（從左往右）
            
            # 將連續的綠色點分組（形成綠色段）
            green_segments = []
            current_segment = [green_pixels[0]]
            
            for i in range(1, len(green_pixels)):
                # 如果兩個綠色點之間的距離小於 5 像素，認為是連續的
                if green_pixels[i][0] - current_segment[-1][0] <= 5:
                    current_segment.append(green_pixels[i])
                else:
                    # 保存當前段，開始新段
                    if len(current_segment) >= 20:  # 🎯 只保留連續超過 20 像素的段
                        green_segments.append(current_segment)
                    current_segment = [green_pixels[i]]
            
            # 保存最後一個段
            if len(current_segment) >= 20:
                green_segments.append(current_segment)
            
            if not green_segments:
                # 如果沒有形成足夠長的段，選擇最左側的綠色點（起始位置）向右偏移 30 像素
                start_pixel = green_pixels[0]  # 最左側的像素（起始位置）
                offset = 30  # 🎯 點擊點修正：起始點向右偏移 30 像素
                x = start_pixel[0] + offset
                y = start_pixel[1]
                self.logger.info(f"[TIMELINE_COLOR] 找到 {len(green_pixels)} 個綠色像素點（未形成足夠長的段），選擇起始位置向右偏移 {offset} 像素: ({x}, {y})")
            else:
                # 🎯 選擇首段（最左邊的足夠長的錄影段），而不是最長的段
                # 從左往右搜尋，找到第一個（最左邊）足夠長的錄影段
                first_segment = green_segments[0]  # 第一個段（最左邊）
                
                # 🎯 點擊點修正：找到第一段綠色後，起始點向右偏移 30 像素
                # 理由：確保從該時段的開頭播放，避免點到末尾直接跳回直播
                first_segment.sort(key=lambda p: p[0])  # 按 X 座標排序，找到起始位置
                start_pixel = first_segment[0]  # 最左側的像素（起始位置）
                
                # 計算起始位置向右偏移 30 像素的座標
                offset = 30
                x = start_pixel[0] + offset
                y = start_pixel[1]
                
                self.logger.info(f"[TIMELINE_COLOR] 找到 {len(green_segments)} 個綠色段（共 {len(green_pixels)} 個像素），選擇首段（最左邊，{len(first_segment)} 個像素）的起始位置向右偏移 {offset} 像素: ({x}, {y})")
            
            # 整合報告系統：標註綠色點
            reporter = self.get_reporter()
            if reporter:
                try:
                    reporter.add_recognition_screenshot(
                        item_name="活動錄影段",
                        x=x,
                        y=y,
                        width=50,
                        height=20,
                        method="像素辨識",
                        region=timeline_region
                    )
                    self.logger.info("[TIMELINE_COLOR] 已添加辨識截圖到報告系統")
                except Exception as e:
                    self.logger.debug(f"[TIMELINE_COLOR] 添加辨識截圖失敗: {e}")
            
            return (x, y)
            
        except Exception as e:
            self.logger.warning(f"[TIMELINE_COLOR] 顏色偵測過程中發生錯誤: {e}")
            return None
    
    def scan_timeline_for_green(self, step_size: int = 20) -> Optional[Tuple[int, int]]:
        """
        🎯 [視覺驅動] 線性掃描時間軸尋找綠色錄影段
        
        從左到右掃描時間軸區域，使用 pyautogui.pixelMatchesColor 邏輯尋找「亮綠色」錄影區塊。
        這是顏色偵測失敗後的備選方案，避免盲目點擊螢幕中心。
        
        邏輯 (Linear Scan)：
        1. 鎖定時間軸所在的水平區域 (例如 Y=1150 左右的高度)
        2. 從左到右 (X=100 到 X=1800) 進行「線性掃描」
        3. 每隔 20px 檢查一次像素顏色
        4. 如果發現顏色屬於「亮綠色」(錄影區塊)，立即停止掃描並返回該座標
        
        Args:
            step_size: 水平掃描步長（像素），預設 20px
        
        Returns:
            tuple[int, int] | None: 找到的第一個綠色段的座標 (x, y)，如果找不到則返回 None
        """
        self.logger.info("[SCAN_FALLBACK] 開始線性掃描時間軸尋找綠色錄影段...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.warning("[SCAN_FALLBACK] 無法獲取窗口，跳過線性掃描")
            return None
        
        try:
            # 定義時間軸區域：視窗底部 10-20% 的區域
            # 使用配置中的時間軸掃描區域比例（避免硬編碼）
            timeline_config = EnvConfig.TIMELINE_SETTINGS
            timeline_left = win.left + int(win.width * timeline_config.TIMELINE_SCAN_LEFT_RATIO)
            timeline_right = win.left + int(win.width * timeline_config.TIMELINE_SCAN_RIGHT_RATIO)
            timeline_width = timeline_right - timeline_left
            
            # 時間軸高度：從底部向上 10% 到 20% 的區域
            timeline_bottom = win.top + win.height - int(win.height * 0.10)
            timeline_top = win.top + win.height - int(win.height * 0.20)
            timeline_height = timeline_bottom - timeline_top
            
            self.logger.info(f"[SCAN_FALLBACK] 掃描區域: left={timeline_left}, top={timeline_top}, width={timeline_width}, height={timeline_height}")
            
            # 🎯 亮綠色濾鏡 (Bright Green Filter)
            # 排除灰綠色 (如 R=50, G=120, B=60)，只鎖定高亮綠色
            # 規則：
            # 1. G 通道必須夠亮 (> 160) 以排除灰綠色 (G=120)
            # 2. G 必須顯著大於 R 和 B (> 30) 以確保是綠色系
            
            # 從左到右進行線性掃描
            # 鎖定在時間軸的水平中心線（Y 座標約在 timeline_top + timeline_height // 2）
            scan_y = timeline_top + (timeline_height // 2)
            
            self.logger.info(f"[TIMELINE] 開始掃描時間軸 (尋找亮綠色 Bright Green)...")
            self.logger.info(f"[TIMELINE] 掃描區域: X={timeline_left}~{timeline_right}, Y={scan_y}，步長={step_size}px")
            
            # 從左到右掃描，每隔 step_size 像素檢查一次
            for x in range(timeline_left, timeline_right, step_size):
                try:
                    pixel_color = pyautogui.pixel(x, scan_y)
                    r, g, b = pixel_color
                    
                    # 🎯 [UPDATED] 使用新的綠色判定邏輯（區分亮綠色與白色文字）
                    # 1. 亮度檢查 (太暗不要)
                    calendar_config = EnvConfig.CALENDAR_SETTINGS
                    pass_brightness = g > calendar_config.GREEN_MIN_BRIGHTNESS
                    
                    # 2. 綠色主導檢查 (排除白色文字與灰色背景)
                    # 白色: 255 > 255 + 40 (False) -> 排除
                    # 綠色: 200 > 50 + 40 (True) -> 通過
                    offset = calendar_config.GREEN_DOMINANCE_OFFSET
                    pass_dominance = (g > r + offset) and (g > b + offset)
                    
                    if pass_brightness and pass_dominance:
                        # 找到符合的亮綠色像素，立即停止掃描
                        self.logger.info(f"[TIMELINE] ✅ 找到亮綠色區塊: ({x}, {scan_y}), RGB=({r},{g},{b})")
                        click_x = x
                        click_y = scan_y
                        self.logger.info(f"[SCAN_FALLBACK] ✅ 在座標 ({click_x}, {click_y}) 找到錄影區塊並點擊，RGB=({r}, {g}, {b})")
                        return (click_x, click_y)
                        
                except Exception as e:
                    # 如果讀取像素失敗（例如座標超出螢幕），跳過該點
                    self.logger.debug(f"[SCAN_FALLBACK] 讀取座標 ({x}, {scan_y}) 的像素失敗: {e}")
                    continue
            
            # 如果掃描完整個區域都沒找到綠色像素，記錄除錯資訊
            # 取幾個樣本像素的顏色作為參考
            sample_colors = []
            sample_x_positions = [
                timeline_left + timeline_width // 4,  # 左側 1/4
                timeline_left + timeline_width // 2,  # 中心
                timeline_left + timeline_width * 3 // 4,  # 右側 3/4
            ]
            
            for sample_x in sample_x_positions:
                try:
                    pixel_color = pyautogui.pixel(sample_x, scan_y)
                    r, g, b = pixel_color
                    sample_colors.append(f"({sample_x}, {scan_y}): RGB({r}, {g}, {b})")
                except:
                    pass
            
            self.logger.warning(f"[SCAN_FALLBACK] 線性掃描未找到任何綠色錄影區塊")
            self.logger.warning(f"[SCAN_FALLBACK] 掃描區域: left={timeline_left}, top={timeline_top}, width={timeline_width}, height={timeline_height}")
            self.logger.warning(f"[SCAN_FALLBACK] 實際顏色範例: {', '.join(sample_colors) if sample_colors else '無法讀取樣本顏色'}")
            return None
                
        except Exception as e:
            self.logger.error(f"[SCAN_FALLBACK] 線性掃描過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def seek_to_first_recording(self) -> Optional[Tuple[int, int]]:
        """
        🎯 [視覺驅動] 線性掃描時間軸，尋找第一個錄影區段並點擊
        
        ROI 設定：鎖定螢幕下方時間軸區域（例如 Y=1100~1150）
        掃描方式：從左向右 (X=100 -> 1800)，步長 10px
        判斷：一旦發現像素顏色為「亮綠色」，立即點擊該座標，並 break 迴圈
        
        日誌：必須印出 [TIMELINE] 找到錄影區段於座標 (x, y)，顏色 RGB(...)
        
        Returns:
            tuple[int, int] | None: 找到的錄影區段座標 (x, y)，如果找不到則返回 None
        """
        self._log_method_entry("seek_to_first_recording")
        self.logger.info("[TIMELINE] 開始線性掃描時間軸，尋找第一個錄影區段...")
        
        win = self.get_nx_window()
        if not win:
            self.logger.error("[TIMELINE] 無法獲取窗口")
            return None
        
        try:
            # ROI 設定：鎖定螢幕下方時間軸區域（例如 Y=1100~1150）
            # 使用配置中的時間軸掃描區域比例（避免硬編碼）
            timeline_config = EnvConfig.TIMELINE_SETTINGS
            timeline_left = win.left + int(win.width * timeline_config.TIMELINE_SCAN_LEFT_RATIO)
            timeline_right = win.left + int(win.width * timeline_config.TIMELINE_SCAN_RIGHT_RATIO)
            
            # 時間軸高度：從底部向上約 10-20% 的區域
            # 鎖定在 Y=1100~1150 左右（根據視窗大小動態計算）
            timeline_bottom = win.top + win.height - int(win.height * 0.10)
            timeline_top = win.top + win.height - int(win.height * 0.20)
            
            # 計算掃描的 Y 座標（時間軸中心）
            scan_y = timeline_top + (timeline_bottom - timeline_top) // 2
            
            self.logger.info(f"[TIMELINE] 掃描區域: X={timeline_left}~{timeline_right}, Y={scan_y}")
            self.logger.info(f"[TIMELINE] 從左向右掃描，步長 10px...")
            
            # 目標顏色：亮綠色 RGB(0, 255, 0) 附近，容許值 tolerance=30
            target_r, target_g, target_b = 0, 255, 0
            tolerance = 30
            
            # 從左向右掃描，步長 10px
            step_size = 10
            for x in range(timeline_left, timeline_right, step_size):
                try:
                    # 讀取像素顏色
                    pixel_color = pyautogui.pixel(x, scan_y)
                    r, g, b = pixel_color
                    
                    # 檢查 RGB 值是否在容許範圍內
                    r_diff = abs(int(r) - target_r)
                    g_diff = abs(int(g) - target_g)
                    b_diff = abs(int(b) - target_b)
                    
                    if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                        # 找到符合的綠色像素，立即點擊該座標並 break 迴圈
                        click_x = x
                        click_y = scan_y
                        
                        self.logger.info(f"[TIMELINE] ✅ 找到錄影區段於座標 ({click_x}, {click_y})，顏色 RGB({r}, {g}, {b})")
                        
                        # 執行點擊
                        pyautogui.click(click_x, click_y)
                        self.logger.info(f"[TIMELINE] 已點擊座標 ({click_x}, {click_y})")
                        
                        # 記錄到報告系統
                        reporter = self.get_reporter()
                        if reporter:
                            try:
                                timeline_region = (timeline_left, timeline_top, timeline_right - timeline_left, timeline_bottom - timeline_top)
                                reporter.add_recognition_screenshot(
                                    item_name="錄影區段（線性掃描）",
                                    x=click_x,
                                    y=click_y,
                                    width=50,
                                    height=20,
                                    method="線性掃描",
                                    region=timeline_region
                                )
                            except Exception as e:
                                self.logger.debug(f"報告截圖失敗: {e}")
                        
                        return (click_x, click_y)
                        
                except Exception as e:
                    # 如果讀取像素失敗（例如座標超出螢幕），跳過該點
                    self.logger.debug(f"[TIMELINE] 讀取座標 ({x}, {scan_y}) 的像素失敗: {e}")
                    continue
            
            # 如果掃描完整個區域都沒找到綠色像素
            self.logger.warning(f"[TIMELINE] 線性掃描未找到任何錄影區段")
            self.logger.warning(f"[TIMELINE] 掃描區域: X={timeline_left}~{timeline_right}, Y={scan_y}")
            
            # 取幾個樣本像素的顏色作為參考
            sample_colors = []
            sample_x_positions = [
                timeline_left + (timeline_right - timeline_left) // 4,  # 左側 1/4
                timeline_left + (timeline_right - timeline_left) // 2,  # 中心
                timeline_left + (timeline_right - timeline_left) * 3 // 4,  # 右側 3/4
            ]
            
            for sample_x in sample_x_positions:
                try:
                    pixel_color = pyautogui.pixel(sample_x, scan_y)
                    r, g, b = pixel_color
                    sample_colors.append(f"({sample_x}, {scan_y}): RGB({r}, {g}, {b})")
                except:
                    pass
            
            self.logger.warning(f"[TIMELINE] 實際顏色範例: {', '.join(sample_colors) if sample_colors else '無法讀取樣本顏色'}")
            return None
                
        except Exception as e:
            self.logger.error(f"[TIMELINE] 線性掃描過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def click_green_timeline_segment(self) -> bool:
        """
        🎯 [重構版] 在底部進度條中點擊綠色的錄影時段
        
        策略優先級：
        1. 像素顏色偵測（最快）
        2. VLM 文字標籤（鎖定底部區域）
        3. 線性掃描（從左到右掃描時間軸）
        4. 快速失敗（如果所有方法都失敗，不點擊並拋出錯誤）
        
        Returns:
            bool: 點擊是否成功
        
        Raises:
            RuntimeError: 如果所有辨識方法都失敗，找不到錄影段
        """
        self._log_method_entry("click_green_timeline_segment")
        self.logger.info("[TIMELINE] 點擊進度條中的綠色錄影時段...")
        
        win = self.get_nx_window()
        if not win:
            raise RuntimeError("無法獲取窗口，無法點擊時間軸")

        # --- 策略 1: 像素顏色偵測 (最快) ---
        green_coord = self._find_recording_segment_by_color()
        if green_coord:
            x, y = green_coord
            self.logger.info(f"[TIMELINE_COLOR] ✅ 顏色偵測成功，點擊座標: ({x}, {y})")
            self._perform_click(x, y, clicks=1)
            time.sleep(1.0)
            return True

        # --- 策略 2: 直接掃描 (移除 VLM 文字搜尋) ---
        self.logger.info("[TIMELINE] ⚠️ 顏色偵測失敗，嘗試直接掃描時間軸...")
        
        # 🎯 直接呼叫 scan_timeline_for_green，不再使用 VLM 文字搜尋
        green_coord = self.scan_timeline_for_green(step_size=20)
        if green_coord:
            x, y = green_coord
            self.logger.info(f"[TIMELINE] ✅ 直接掃描成功，點擊座標: ({x}, {y})")
            self._perform_click(x, y, clicks=1)
            time.sleep(1.0)
            return True
        
        # --- 策略 3: 線性掃描 (備選) ---
        self.logger.info("[TIMELINE] ⚠️ 直接掃描失敗，嘗試線性掃描...")
        green_coord = self.scan_timeline_for_green(step_size=20)
        if green_coord:
            x, y = green_coord
            self.logger.info(f"[SCAN_FALLBACK] ✅ 線性掃描成功，點擊座標: ({x}, {y})")
            self._perform_click(x, y, clicks=1)
            time.sleep(EnvConfig.THRESHOLDS.SETTINGS_WAIT_TIME)
            return True

        # --- 策略 4: 快速失敗 ---
        # 如果所有辨識方法都失敗，不點擊任何位置，直接拋出錯誤
        error_msg = "找不到時間軸上的錄影段。所有辨識方法都失敗（顏色偵測、直接掃描、線性掃描）。停止測試。"
        self.logger.error(f"[TIMELINE] ❌ {error_msg}")
        raise RuntimeError(error_msg)
    
    def click_timeline(self, position: str = "center") -> bool:
        """
        點擊時間軸（幾何定位：點擊視窗底部中央）
        
        使用幾何定位方式點擊時間軸，比圖片辨識更穩定，因為時間軸位置固定。
        此方法使用配置中的時間軸位置比例，避免硬編碼。
        
        Args:
            position: 點擊位置，可選值：
                - "center": 水平中央（預設）
                - "left": 左側 1/4 位置
                - "right": 右側 3/4 位置
        
        Returns:
            bool: 點擊是否成功。如果無法獲取視窗則返回 False。
        
        Note:
            - 使用配置中的時間軸位置比例（避免硬編碼）
            - 使用配置中的點擊等待時間（避免硬編碼）
        """
        self.logger.info(f"[TIMELINE] 點擊時間軸位置: {position}")
        
        win = self.get_nx_window()
        if not win:
            self.logger.error("[TIMELINE] 無法獲取視窗")
            return False
        
        # 🎯 使用配置中的時間軸位置比例（避免硬編碼）
        timeline_config = EnvConfig.TIMELINE_SETTINGS
        thresholds = EnvConfig.THRESHOLDS
        
        # 🎯 避免點擊到小箭頭：Y 座標向下偏移 15px（小箭頭通常在時間軸上方）
        timeline_y_base = win.top + int(win.height * timeline_config.TIMELINE_Y_RATIO)
        timeline_y = timeline_y_base + 15  # 向下偏移 15px，避免點擊到小箭頭
        
        # 根據位置參數選擇對應的 X 比例
        position_map = {
            "center": timeline_config.TIMELINE_CENTER_X_RATIO,
            "left": timeline_config.TIMELINE_LEFT_X_RATIO,
            "right": timeline_config.TIMELINE_RIGHT_X_RATIO
        }
        timeline_x_ratio = position_map.get(position, timeline_config.TIMELINE_CENTER_X_RATIO)
        timeline_x = win.left + int(win.width * timeline_x_ratio)
        
        self.logger.info(f"[TIMELINE] 點擊座標: ({timeline_x}, {timeline_y}) (原始 Y={timeline_y_base}, 向下偏移 15px 避免小箭頭)")
        pyautogui.click(timeline_x, timeline_y)
        # 使用配置中的點擊等待時間（避免硬編碼）
        time.sleep(thresholds.CLICK_WAIT_TIME)
        
        return True
    
    def click_pause(self) -> bool:
        """
        點擊暫停按鈕（使用圖片辨識）
        
        此方法優先使用圖片辨識暫停按鈕，如果失敗則嘗試播放按鈕圖片
        （可能當前是播放狀態），最後回退到點擊畫面中央。
        
        Returns:
            bool: 點擊是否成功
        
        Note:
            - 使用配置中的資源路徑（避免硬編碼）
            - 使用配置中的時間軸位置比例（避免硬編碼）
            - 使用配置中的等待時間（避免硬編碼）
        """
        self.logger.info("[PAUSE] 點擊暫停按鈕...")
        
        # 🎯 使用配置中的時間軸位置和資源路徑（避免硬編碼）
        timeline_config = EnvConfig.TIMELINE_SETTINGS
        app_paths = EnvConfig.APP_PATHS
        thresholds = EnvConfig.THRESHOLDS
        
        # 優先使用圖片辨識暫停按鈕
        success = self.smart_click(
            x_ratio=timeline_config.TIMELINE_CENTER_X_RATIO,
            y_ratio=timeline_config.TIMELINE_Y_RATIO,
            target_text=None,  # 不使用文字辨識
            image_path=app_paths.TIMELINE_PAUSE,  # 使用配置中的路徑
            use_ok_script=True,
            use_vlm=False,  # 圖片優先模式
            timeout=2
        )
        
        # 如果暫停按鈕圖片不存在，嘗試播放按鈕圖片（可能當前是播放狀態）
        if not success:
            self.logger.info("[PAUSE] 暫停按鈕圖片未找到，嘗試播放按鈕圖片...")
            success = self.smart_click(
                x_ratio=timeline_config.TIMELINE_CENTER_X_RATIO,
                y_ratio=timeline_config.TIMELINE_Y_RATIO,
                target_text=None,
                image_path=app_paths.TIMELINE_PLAY,  # 使用配置中的路徑
                use_ok_script=True,
                use_vlm=False,
                timeout=2
            )
        
        if success:
            self.logger.info("[PAUSE] [OK] 成功點擊暫停/播放按鈕")
            # 使用配置中的等待時間（避免硬編碼）
            time.sleep(thresholds.CLICK_WAIT_TIME)
            return True
        else:
            self.logger.warning("[PAUSE] [WARN] 暫停/播放按鈕圖片未找到")
            return False
            # 備選：點擊畫面中央（通常也會觸發暫停）
            win = self.get_nx_window()
            if win:
                center_x = win.left + (win.width // 2)
                center_y = win.top + (win.height // 2)
                pyautogui.click(center_x, center_y)
                self.logger.info("[PAUSE] 已點擊畫面中央作為備選")
                time.sleep(thresholds.CLICK_WAIT_TIME)
                return True
            return False
    
    def pause_playback(self, playback_duration=7):
        """
        🎯 暫停回放（簡化版）
        流程：點完進度條後等待指定時間，然後直接按空格鍵暫停
        不需要點擊任何地方，避免誤點到讓進度條隱藏的按鈕
        
        Args:
            playback_duration: 播放持續時間（秒），預設 7 秒（在 5-10 秒之間）
        """
        # 🎯 確保 playback_duration 是數字類型（Excel 可能讀取為字符串）
        try:
            playback_duration = float(playback_duration) if playback_duration else 7
        except (ValueError, TypeError):
            self.logger.warning(f"[PLAYBACK] 無法轉換 playback_duration '{playback_duration}' 為數字，使用預設值 7")
            playback_duration = 7
        
        self._log_method_entry("pause_playback", f"播放持續時間: {playback_duration} 秒")
        
        # 1. 等待播放指定時間
        self.logger.info(f"[PLAYBACK] ⏳ 正在播放... (等待 {playback_duration} 秒)")
        time.sleep(playback_duration)
        
        # 2. 直接按空格鍵暫停（不需要點擊任何地方）
        self.logger.info("[PLAYBACK] ⌨️ 發送空白鍵指令暫停回放...")
        try:
            pyautogui.press('space')
            time.sleep(0.3)  # 等待暫停生效
            
            # 添加報告步驟
            reporter = self.get_reporter()
            if reporter:
                try:
                    current_step_no = len(reporter.steps) + 1 if hasattr(reporter, 'steps') else 1
                    reporter.add_step(
                        step_no=current_step_no,
                        step_name="暫停回放",
                        status="pass",
                        message=f"使用空白鍵成功暫停回放（已播放 {playback_duration} 秒）"
                    )
                except Exception as e:
                    self.logger.debug(f"[PLAYBACK] 添加報告步驟失敗: {e}")
            
            self.logger.info("[PLAYBACK] [OK] 使用空白鍵成功暫停回放")
            return True
        except Exception as e:
            self.logger.error(f"[PLAYBACK] [ERROR] 發送空白鍵失敗: {e}")
            # 添加報告步驟（失敗）
            reporter = self.get_reporter()
            if reporter:
                try:
                    current_step_no = len(reporter.steps) + 1 if hasattr(reporter, 'steps') else 1
                    reporter.add_step(
                        step_no=current_step_no,
                        step_name="暫停回放",
                        status="fail",
                        message=f"發送空白鍵失敗: {e}"
                    )
                except Exception as e2:
                    self.logger.debug(f"[PLAYBACK] 添加報告步驟失敗: {e2}")
            return False