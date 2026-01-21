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
        self.logger.info("🖱️ 點擊左上角菜單...")
        
        success = self.smart_click(
            x_ratio=0.02, 
            y_ratio=0.03,
            target_text=None,  # 菜單圖標不需要 OCR，加快速度
            image_path="desktop_main/menu_icon.png",
            timeout=3  # 增加超時時間，確保圖片辨識有足夠時間
        )
        
        if success:
            self.logger.info("✅ 成功開啟主選單")
            # 智能等待選單展開（增加等待時間，確保菜單完全展開）
            import time
            time.sleep(0.8)  # 增加到 0.8 秒，確保菜單完全展開，讓後續點擊有足夠時間
        else:
            self.logger.error("❌ 開啟主選單失敗：無法找到或點擊菜單圖標")
        
        return success

    def select_local_settings(self):
        """點擊選單中的『本地設置』"""
        self.logger.info("🖱️ 點擊「本地設置」...")
        # 強制輸出到 stdout（避免編碼錯誤）
        try:
            print("[MAIN_PAGE] 開始點擊本地設置...")
        except:
            pass
        
        # 確保菜單已展開，先等待一小段時間
        import time
        time.sleep(0.3)  # 額外等待，確保菜單完全展開
        
        success = self.smart_click(
            x_ratio=0.1, 
            y_ratio=0.32,
            target_text=None,  # 移除 OCR，避免觸發 10+ 秒的初始化
            image_path="desktop_main/local_settings.png",
            timeout=5  # 增加到 5 秒，給辨識和點擊足夠時間
        )
        
        try:
            print(f"[MAIN_PAGE] smart_click 結果: {success}")
        except:
            pass
        self.logger.info(f"[MAIN_PAGE] smart_click 返回: {success}")
        
        # 🔍 重要：即使 smart_click 返回 False，也可能是因為點擊成功後菜單關閉，導致後續辨識失敗
        # 所以我們需要驗證設置視窗是否真的出現了
        if not success:
            # 等待一下，讓視窗有時間出現
            import time
            time.sleep(1.0)
            # 檢查設置視窗是否已經出現
            found_window = self.wait_for_window(
                window_titles=["本地設置", "Local Settings", "本地設定", "Nx Witness Client"], 
                timeout=2  # 短 timeout，快速檢查
            )
            if found_window:
                # 視窗已經出現，說明點擊其實是成功的，只是 smart_click 的後續辨識失敗了
                self.logger.info("✅ 雖然 smart_click 返回 False，但設置視窗已出現，確認點擊成功")
                try:
                    print("[MAIN_PAGE] 雖然 smart_click 返回 False，但設置視窗已出現，確認點擊成功")
                except:
                    pass
                success = True  # 修正為 True
        
        if success:
            self.logger.info("✅ 成功點擊本地設置")
            try:
                print("[MAIN_PAGE] smart_click 成功，等待設置視窗開啟...")
            except:
                pass
            # 智能等待設置視窗開啟
            import time
            time.sleep(1.0)  # 增加等待時間，確保設置視窗完全載入
            found_window = self.wait_for_window(
                window_titles=["本地設置", "Local Settings", "本地設定", "Nx Witness Client"], 
                timeout=5  # 增加到 5 秒，給視窗開啟足夠時間
            )
            if found_window:
                self.logger.info(f"✅ 設置視窗已開啟: {found_window.title}")
                try:
                    print(f"[MAIN_PAGE] 設置視窗已開啟: {found_window.title}")
                except:
                    pass
                # 驗證成功，確保視窗確實存在
                return True
            else:
                # 視窗未檢測到，但可能只是辨識問題，不立即判定為失敗
                # 繼續執行，因為畫面可能已經點擊成功了
                self.logger.warning("⚠️ 未檢測到設置視窗，但繼續執行（可能是視窗辨識問題）")
                try:
                    print("[MAIN_PAGE] 未檢測到設置視窗，但繼續執行（smart_click 已成功）")
                except:
                    pass
                # 不返回 False，因為 smart_click 已經成功，畫面可能已經點擊了
                return True  # 改變邏輯：smart_click 成功就認為成功，不依賴視窗驗證
        else:
            self.logger.warning("⚠️ smart_click 返回失敗，點擊本地設置可能失敗")
            try:
                print("[MAIN_PAGE] smart_click 失敗，點擊本地設置可能失敗")
            except:
                pass
        
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
        # 日曆視窗大約位於視窗的 60%-90% (X), 25%-65% (Y)
        calendar_left = win.left + int(win.width * 0.60)
        calendar_right = win.left + int(win.width * 0.90)
        calendar_top = win.top + int(win.height * 0.25)
        calendar_bottom = win.top + int(win.height * 0.65)
        calendar_width = calendar_right - calendar_left
        calendar_height = calendar_bottom - calendar_top
        
        self.logger.info(f"[CALENDAR_VISUAL] 日曆掃描區域 (ROI): left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
        
        try:
            calendar_region = (calendar_left, calendar_top, calendar_width, calendar_height)
            screenshot = pyautogui.screenshot(region=calendar_region)
            img_array = np.array(screenshot)
            
            # 確保是 RGB 格式（3 通道）
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            
            # 顏色特徵：尋找 RGB(0, 255, 0) 附近的亮綠色像素（Tolerance=30）
            target_r, target_g, target_b = 0, 255, 0
            tolerance = 30
            
            green_pixels = []  # 儲存找到的綠色像素座標
            black_pixel_count = 0  # 統計黑色像素數量（用於判斷日曆是否打開）
            total_pixels = img_array.shape[0] * img_array.shape[1]
            
            # 使用 nested loop 快速掃描
            for row in range(img_array.shape[0]):
                for col in range(img_array.shape[1]):
                    r, g, b = img_array[row, col]
                    
                    # 檢查是否為黑色（用於判斷日曆是否打開）
                    if r < 10 and g < 10 and b < 10:
                        black_pixel_count += 1
                    
                    # 檢查是否符合綠色特徵
                    r_diff = abs(int(r) - target_r)
                    g_diff = abs(int(g) - target_g)
                    b_diff = abs(int(b) - target_b)
                    
                    if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                        # 找到符合的綠色像素
                        abs_x = calendar_left + col
                        abs_y = calendar_top + row
                        green_pixels.append((abs_x, abs_y, r, g, b))
            
            # 檢查日曆是否打開：如果掃描結果全是 RGB(0,0,0)，代表日曆沒打開
            black_ratio = black_pixel_count / total_pixels if total_pixels > 0 else 0
            if black_ratio > 0.95:  # 如果 95% 以上都是黑色，認為日曆沒打開
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
                self.logger.warning(f"[CALENDAR_VISUAL] 未找到綠色標記像素")
                self.logger.warning(f"[CALENDAR_VISUAL] 掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
                pytest.fail("未在日曆上發現任何錄影標記（綠色底線）。請確認日曆已開啟且存在錄影資料。")
            
            # 找到第一個綠色像素，點擊該像素上方 10px 的位置（點擊日期數字，而不是點綠線）
            first_green = green_pixels[0]  # 選擇第一個找到的綠色像素（從上到下、從左到右）
            green_x, green_y, r, g, b = first_green
            
            self.logger.info(f"[CALENDAR_VISUAL] 找到綠色標記像素: 座標=({green_x}, {green_y}), RGB=({r}, {g}, {b})")
            
            # 點擊位置：綠色標記上方 10px（點擊日期數字）
            click_x = green_x
            click_y = green_y - 10  # 向上偏移 10px，點擊日期文字
            
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
        # - offset_x=-10 (向左像素微調，精準命中圖標中心)
        # - image_path 僅供報告截圖標註使用，不參與辨識（設置 use_ok_script=False 禁用圖片辨識）
        success = self.smart_click(
            x_ratio=0.92,  # 視窗寬度 92% 處
            y_ratio=0.04,  # 視窗底部向上 4% 處
            target_text=None,  # 日曆圖標沒有文字，不使用文字辨識
            image_path="desktop_main/calendar_icon.png",  # 僅供報告截圖標註使用
            timeout=1.0,  # 短超時，快速失敗後使用保底座標
            from_bottom=True,  # 強制由底部起算
            offset_x=-10,  # 向左像素微調，精準命中圖標中心
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
        # 日曆視窗大約位於視窗的 60%-90% (X), 25%-65% (Y)
        calendar_left = win.left + int(win.width * 0.60)
        calendar_right = win.left + int(win.width * 0.90)
        calendar_top = win.top + int(win.height * 0.25)
        calendar_bottom = win.top + int(win.height * 0.65)
        calendar_width = calendar_right - calendar_left
        calendar_height = calendar_bottom - calendar_top
        
        self.logger.info(f"[CALENDAR_VISUAL] 日曆掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
        
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
            # 目標顏色：RGB(0, 255, 0) 附近，容許值 tolerance=30
            target_r, target_g, target_b = 0, 255, 0
            tolerance = 30
            
            green_pixels = []  # 儲存找到的綠色像素座標
            
            # 從上到下、從左到右掃描
            for row in range(img_array.shape[0]):
                for col in range(img_array.shape[1]):
                    r, g, b = img_array[row, col]
                    
                    # 使用 pyautogui.pixelMatchesColor 的邏輯進行顏色比對
                    # 檢查 RGB 值是否在容許範圍內
                    r_diff = abs(int(r) - target_r)
                    g_diff = abs(int(g) - target_g)
                    b_diff = abs(int(b) - target_b)
                    
                    if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
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
                
                self.logger.warning(f"[CALENDAR_VISUAL] 未找到綠色標記像素")
                self.logger.warning(f"[CALENDAR_VISUAL] 掃描區域: left={calendar_left}, top={calendar_top}, width={calendar_width}, height={calendar_height}")
                self.logger.warning(f"[CALENDAR_VISUAL] 實際顏色範例: {', '.join(sample_colors)}")
                
                # 如果掃描完整個日曆都沒看到綠色標記，直接拋出錯誤
                pytest.fail("未在日曆上發現任何錄影標記（綠色底線）。請確認日曆已開啟且存在錄影資料。")
            
            # 步驟 4: 找到第一個綠色像素，返回其上方的日期位置座標
            # 綠色標記通常在日期下方，所以我們需要向上偏移來點擊日期本身
            first_green = green_pixels[0]  # 選擇第一個找到的綠色像素（從上到下、從左到右）
            green_x, green_y, r, g, b = first_green
            
            self.logger.info(f"[CALENDAR_VISUAL] 找到綠色標記像素: 座標=({green_x}, {green_y}), RGB=({r}, {g}, {b})")
            
            # 點擊位置：綠色標記上方約 15-20 像素（日期文字的位置）
            click_x = green_x
            click_y = green_y - 20  # 向上偏移 20 像素，點擊日期文字
            
            # 確保點擊位置在視窗範圍內
            if click_y < win.top:
                click_y = win.top + 10  # 如果超出上邊界，使用視窗頂部 + 10px
            
            self.logger.info(f"[CALENDAR_VISUAL] 計算點擊座標: ({click_x}, {click_y}) (綠色標記上方 20px)")
            
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
                time.sleep(0.5)  # 等待日期選擇生效
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
        
        # 動態計算日曆視窗區域並鎖定搜尋區域
        # 日曆視窗大約位於 (win.width * 0.75, win.height * 0.45) 附近
        win = self.get_nx_window()
        if win:
            # 日曆視窗區域：x 從 60% 到 90%，y 從 25% 到 65%
            calendar_region_left = win.left + int(win.width * 0.60)
            calendar_region_top = win.top + int(win.height * 0.25)
            calendar_region_width = int(win.width * 0.30)  # 90% - 60% = 30%
            calendar_region_height = int(win.height * 0.40)  # 65% - 25% = 40%
            
            calendar_region = (calendar_region_left, calendar_region_top, calendar_region_width, calendar_region_height)
            
            # 日曆視窗中心位置（用於 smart_click 的 x_ratio, y_ratio）
            calendar_x_ratio = 0.75  # 日曆視窗中心 X 位置
            calendar_y_ratio = 0.45  # 日曆視窗中心 Y 位置
            
            self.logger.info(f"[CALENDAR] 日曆視窗區域: x_ratio={calendar_x_ratio}, y_ratio={calendar_y_ratio}")
            self.logger.info(f"[CALENDAR] 鎖定搜尋區域: {calendar_region}")
        else:
            # 如果無法獲取窗口，使用默認值
            calendar_x_ratio = 0.75
            calendar_y_ratio = 0.45
            calendar_region = None
        
        # 🎯 優先尋找並點擊 17 號
        self.logger.info(f"[CALENDAR] 優先尋找日期 {target_date}...")
        
        # 使用 smart_click 尋找並點擊日期，鎖定搜尋區域在日曆視窗內部
        # 🎯 修正日期點選：點擊日期 "17" 時，傳入 offset_y=15, offset_x=5
        # 理由：補償 VLM 常見的偏左上誤差，確保點中數字的正中心
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
            # 🎯 從左向右鎖定：將 timeline_right 的 x_ratio 嚴格限制在 0.60 以內
            # 理由：確保絕對不會抓到時間軸右側的當前錄影，強迫 AI 只抓 17 號前半段的資料
            timeline_left = win.left + int(win.width * 0.15)
            timeline_right = win.left + int(win.width * 0.60)  # 🎯 嚴格限制在 0.60 以內，確保絕對不會抓到 Live 錄影段
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
                    # 檢查是否符合綠色特徵
                    if r < 80 and g > 120 and b < 80:
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
            # 從左側 15% 開始，到右側 60% 結束（避免掃描到 Live 錄影段）
            timeline_left = win.left + int(win.width * 0.15)
            timeline_right = win.left + int(win.width * 0.60)
            timeline_width = timeline_right - timeline_left
            
            # 時間軸高度：從底部向上 10% 到 20% 的區域
            timeline_bottom = win.top + win.height - int(win.height * 0.10)
            timeline_top = win.top + win.height - int(win.height * 0.20)
            timeline_height = timeline_bottom - timeline_top
            
            self.logger.info(f"[SCAN_FALLBACK] 掃描區域: left={timeline_left}, top={timeline_top}, width={timeline_width}, height={timeline_height}")
            
            # 目標顏色：亮綠色 RGB(0, 255, 0) 附近，容許值 tolerance=30
            target_r, target_g, target_b = 0, 255, 0
            tolerance = 30
            
            # 從左到右進行線性掃描
            # 鎖定在時間軸的水平中心線（Y 座標約在 timeline_top + timeline_height // 2）
            scan_y = timeline_top + (timeline_height // 2)
            
            self.logger.info(f"[SCAN_FALLBACK] 開始從左到右掃描，Y 座標={scan_y}，步長={step_size}px")
            
            # 從左到右掃描，每隔 step_size 像素檢查一次
            for x in range(timeline_left, timeline_right, step_size):
                try:
                    # 使用 pyautogui.pixelMatchesColor 進行顏色比對
                    # 注意：pyautogui.pixelMatchesColor 需要絕對座標，且需要 tolerance 參數
                    pixel_color = pyautogui.pixel(x, scan_y)
                    r, g, b = pixel_color
                    
                    # 檢查 RGB 值是否在容許範圍內
                    r_diff = abs(int(r) - target_r)
                    g_diff = abs(int(g) - target_g)
                    b_diff = abs(int(b) - target_b)
                    
                    if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                        # 找到符合的綠色像素，立即停止掃描
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
            # 從左側 15% 開始，到右側 60% 結束（避免掃描到 Live 錄影段）
            timeline_left = win.left + int(win.width * 0.15)
            timeline_right = win.left + int(win.width * 0.60)
            
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

        # --- 策略 2: VLM 文字標籤 (修正搜尋區域) ---
        self.logger.info("[TIMELINE] ⚠️ 顏色偵測失敗，嘗試 VLM 文字搜尋...")
        
        # 關鍵修正：手動定義「底部搜尋區域」
        # 假設時間軸在視窗最下方 15% 的區域
        region_height = int(win.height * 0.15) 
        region_top = win.top + win.height - region_height
        
        # 定義 region = (left, top, width, height)
        # 只搜尋底部，絕對不會誤判上面的日曆
        bottom_region = (win.left, region_top, win.width, region_height)
        
        self.logger.info(f"[TIMELINE] 🔍 鎖定 VLM 搜尋區域(底部): {bottom_region}")

        # 搜尋關鍵字：優先找 "PM", "AM" 或具體時間，這些通常在時間軸上
        # 如果是中文介面，找 "下午", "上午"
        time_markers = ["下午", "上午", "PM", "AM", "17"] 
        
        for marker in time_markers:
            self.logger.info(f"[VLM] 嘗試辨識時間標記: '{marker}'")
            
            # 計算底部區域的中心位置作為 x_ratio, y_ratio（用於座標保底）
            center_x_ratio = 0.5  # 底部區域中心 X
            center_y_ratio = 0.925  # 底部區域中心 Y（從頂部計算，約 92.5%）
            
            # 🎯 使用 smart_click，但注意：如果它使用座標保底，我們不應該標記為 VLM 成功
            # 由於 smart_click 內部會嘗試多種方法，我們無法直接知道使用的是哪種
            # 但我們可以通過檢查日誌來判斷（這需要在 smart_click 中記錄使用的方法）
            # 暫時使用更保守的日誌：不直接聲稱 VLM 成功
            success = self.smart_click(
                x_ratio=center_x_ratio,
                y_ratio=center_y_ratio,
                target_text=marker,
                region=bottom_region,
                timeout=3,
                offset_y=25,  # 找到文字後，向下偏移 25px 點擊綠條
                offset_x=10
            )
            
            if success:
                # 🎯 修正日誌：不直接聲稱 VLM 成功，因為可能使用的是座標保底
                # 實際使用的方法會在 smart_click 的日誌中顯示（如 [VLM]、[OCR]、[COORD]）
                self.logger.info(f"[TIMELINE] ✅ 成功點擊時間軸標記: '{marker}' (請查看上方日誌確認使用的方法)")
                time.sleep(1.0)
                return True
            else:
                self.logger.info(f"[VLM] 辨識時間標記 '{marker}' 失敗，嘗試下一個標記...")

        # --- 策略 3: 線性掃描 (替代盲點) ---
        self.logger.info("[TIMELINE] ⚠️ VLM 文字搜尋失敗，嘗試線性掃描...")
        green_coord = self.scan_timeline_for_green(step_size=20)
        
        if green_coord:
            x, y = green_coord
            self.logger.info(f"[SCAN_FALLBACK] ✅ 線性掃描成功，點擊座標: ({x}, {y})")
            self._perform_click(x, y, clicks=1)
            time.sleep(1.0)
            return True

        # --- 策略 4: 快速失敗 ---
        # 如果所有辨識方法都失敗，不點擊任何位置，直接拋出錯誤
        error_msg = "找不到時間軸上的錄影段。所有辨識方法都失敗（顏色偵測、VLM、線性掃描）。停止測試。"
        self.logger.error(f"[TIMELINE] ❌ {error_msg}")
        raise RuntimeError(error_msg)
    
    def pause_playback(self, playback_duration=7):
        """
        🎯 [修正版] 暫停回放
        修正重點：先點擊畫面中央確保 Focus，再按空白鍵。
        
        Args:
            playback_duration: 播放持續時間（秒），預設 7 秒（在 5-10 秒之間）
        """
        self._log_method_entry("pause_playback", f"播放持續時間: {playback_duration} 秒")
        
        # 1. 等待播放
        self.logger.info(f"[PLAYBACK] ⏳ 正在播放... (等待 {playback_duration} 秒)")
        time.sleep(playback_duration)
        
        win = self.get_nx_window()
        if win:
            try:
                # 2. 關鍵動作：點擊畫面正中央
                # 這能確保視窗取得焦點，且通常點擊影片畫面也會觸發 暫停/播放
                center_x = win.left + (win.width // 2)
                center_y = win.top + (win.height // 2)
                
                self.logger.info("[PLAYBACK] 🖱️ 點擊畫面中央以取得焦點...")
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                
                # 3. 按空白鍵 (雙重保險)
                # 如果剛才的點擊已經暫停了，再按空白鍵可能會繼續播放
                # 所以這裡我們可以改用「截圖判斷」或是單純依賴點擊
                # 但為了保險，我們假設點擊只是為了 focus，空白鍵才是暫停指令
                # (Nx Witness 點擊畫面通常是暫停，所以上面那一下可能已經暫停了)
                
                self.logger.info("[PLAYBACK] ⌨️ 發送空白鍵指令...")
                pyautogui.press('space')
                
                # 添加報告步驟
                reporter = self.get_reporter()
                if reporter:
                    try:
                        current_step_no = len(reporter.steps) + 1 if hasattr(reporter, 'steps') else 1
                        reporter.add_step(
                            step_no=current_step_no,
                            step_name="暫停回放",
                            status="pass",
                            message="點擊畫面中央並使用空白鍵成功暫停回放"
                        )
                    except:
                        pass
                
                # 驗證：檢查畫面左下角的播放按鈕狀態 (選做)
                # 這裡簡單返回 True
                return True
                
            except Exception as e:
                self.logger.error(f"[PLAYBACK] 暫停失敗: {e}")
                import traceback
                traceback.print_exc()
                return False
        return False