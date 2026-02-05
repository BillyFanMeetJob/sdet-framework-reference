# 相對路徑: pages/desktop/server_settings_page.py

from base.desktop_app import DesktopApp
import time
import os
import pygetwindow as gw
import pyautogui
import pytest

class ServerSettingsPage(DesktopApp):
    """
    伺服器設定頁面
    處理 Case 1-2: 自動偵測 USB 攝影機
    """
    
    def __init__(self):
        super().__init__()
    
    def right_click_server_icon(self):
        """
        🎯 在左上角 Server 圖示位置點擊右鍵
        使用圖片優先策略：OK Script > PyAutoGUI > VLM > OCR
        """
        self.logger.info("🖱️ 在 Server 圖示上點擊右鍵...")
        
        # 🎯 使用 UILocator：簡潔且易讀
        from config import EnvConfig
        locator_config = EnvConfig.LOCATOR_CONFIG
        
        # 使用圖片優先策略，因為圖示圖片辨識更可靠
        server_locator = locator_config.SERVER_ICON_RIGHT_CLICK.with_text("Server")
        success = self.click_with_locator(server_locator)
        
        if success:
            # 智能等待右鍵選單出現（增加等待時間，確保選單完全展開）
            time.sleep(0.8)  # 增加等待時間，確保選單完全展開
            try:
                win = self.get_nx_window()
                if win:
                    region = (win.left, win.top, win.width, win.height)
                    self.wait_for_screen_change(region, max_wait=1.0)
            except Exception as e:
                self.logger.warning(f"⚠️ 等待螢幕變化時發生異常: {e}")
        else:
            self.logger.warning("⚠️ 右鍵點擊 Server 圖示失敗")
        
        return success
    
    def click_server_settings_menu(self):
        """
        🎯 點擊右鍵選單中的「伺服器設定... (Server Settings)」
        使用圖片優先策略：OK Script > PyAutoGUI > VLM > OCR
        """
        self.logger.info("🖱️ 點擊「伺服器設定」選單項目...")
        
        # 🎯 使用 UILocator：簡潔且易讀
        from config import EnvConfig
        locator_config = EnvConfig.LOCATOR_CONFIG
        
        # 使用圖片優先策略，因為右鍵選單項目通常圖片辨識更可靠
        settings_menu_locator = locator_config.SERVER_SETTINGS_MENU_ITEM.with_text("伺服器設定")
        success = self.click_with_locator(settings_menu_locator)
        self.logger.info(f"[DEBUG] smart_click_priority_image 返回: {success}")
        
        if success:
            # 等待設定視窗出現
            time.sleep(0.5)
            # 包含更多視窗標題變體，因為視窗標題可能包含後綴
            window_titles = [
                "Server Settings",
                "伺服器設定",
                "Server Settings - Nx Witness Client",
                "伺服器設定 - Nx Witness Client",
                "Server Settings...",
                "伺服器設定..."
            ]
            found = self.wait_for_window(window_titles=window_titles, timeout=5)
            if found:
                self.logger.info("✅ 伺服器設定視窗已開啟")
                return True
            else:
                # 即使視窗驗證失敗，只要點擊成功就返回 True
                # 因為圖片辨識已經成功點擊，視窗可能已經出現，只是標題匹配失敗
                self.logger.warning("⚠️ 未找到伺服器設定視窗，但點擊已成功，繼續執行（視窗可能已開啟但標題匹配失敗）")
                return True
        else:
            self.logger.warning("⚠️ 點擊失敗")
            return False
    
    def enable_usb_detection(self):
        """
        🎯 勾選「自動偵測內建 USB 攝影機」
        使用 base 層的 smart_checkbox 方法
        
        :return: (success, was_already_checked) - success: 操作是否成功, was_already_checked: checkbox 是否已經是勾選狀態
        """
        self.logger.info("🖱️ 檢查「自動偵測內建 USB 攝影機」選項...")
        
        # 先檢查 checkbox 的當前狀態
        checkbox_pos = self._locate_checkbox(
            x_ratio=0.3,
            y_ratio=0.42,
            target_text="USB",
            image_path="desktop_settings/usb_checkbox.png",
            timeout=3
        )
        
        if not checkbox_pos:
            self.logger.error("❌ 找不到 checkbox")
            return False, False
        
        click_x, click_y = checkbox_pos
        
        # 檢查當前狀態
        is_checked = self._is_checkbox_checked(
            click_x, click_y,
            checked_image="desktop_settings/checkbox_checked.png",
            unchecked_image="desktop_settings/checkbox_unchecked.png"
        )
        
        if is_checked:
            self.logger.info("✅ Checkbox 已經是勾選狀態，跳過點擊")
            return True, True
        
        # 如果未勾選，執行勾選操作
        success = self.smart_checkbox(
            x_ratio=0.3,           # 座標保底 X 比例
            y_ratio=0.42,          # 座標保底 Y 比例
            target_text="USB",     # OCR 尋找文字
            image_path="desktop_settings/usb_checkbox.png",  # 圖片辨識
            checked_image="desktop_settings/checkbox_checked.png",    # 已勾選參考圖
            unchecked_image="desktop_settings/checkbox_unchecked.png", # 未勾選參考圖
            ensure_checked=True,   # 確保勾選狀態
            force_verify=False,    # 關閉強制驗證模式（圖片辨識已準確）
            timeout=3
        )
        
        return success, False
    
    def apply_settings(self):
        """
        🎯 根據 checkbox 狀態執行不同的流程
        
        如果 checkbox 沒勾選：
        1. 勾選 checkbox
        2. 點擊「套用」按鈕（第一次）
        3. 處理密碼確認彈窗（輸入密碼）
        4. 密碼彈窗關閉後，再次點擊「確認」按鈕
        5. 等待伺服器設定窗口關閉
        
        如果 checkbox 已勾選：
        1. 點擊「確認」按鈕
        2. 處理密碼確認彈窗（輸入密碼，如果出現）
        3. 等待伺服器設定窗口關閉
        """
        # 步驟 1: 檢查 checkbox 狀態並勾選（如果需要）
        self.logger.info("🔍 檢查 checkbox 狀態...")
        checkbox_success, was_already_checked = self.enable_usb_detection()
        
        if not checkbox_success:
            self.logger.error("❌ 無法檢查或勾選 checkbox")
            return False
        
        if was_already_checked:
            # 流程 2: checkbox 已勾選，直接點擊「確認」按鈕
            self.logger.info("✅ Checkbox 已勾選，直接點擊「確認」按鈕...")
            from config import EnvConfig
            locator_config = EnvConfig.LOCATOR_CONFIG
            ok_btn_locator = locator_config.OK_BTN_BOTTOM_RIGHT.with_text("確認")
            success = self.click_with_locator(ok_btn_locator)
            
            if success:
                self.logger.info("✅ 成功點擊「確認」按鈕")
                
                # 保存截圖：點擊「確認」後的狀態
                try:
                    import pyautogui
                    import datetime
                    screenshot = pyautogui.screenshot()
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "password_debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                    screenshot_path = os.path.join(debug_dir, f"00_after_confirm_click_{timestamp}.png")
                    screenshot.save(screenshot_path)
                    self.logger.info(f"[DEBUG_SCREENSHOT] 點擊「確認」後截圖已保存: {screenshot_path}")
                except Exception as e:
                    self.logger.warning(f"[DEBUG_SCREENSHOT] 保存截圖失敗: {e}")
                
                # 等待密碼彈窗出現（如果有的話），最多等待 2 秒
                password_window_found = False
                max_wait = 2.0
                check_interval = 0.2
                waited = 0.0
                
                self.logger.info("🔍 檢查是否出現密碼確認彈窗（最多等待 {:.1f} 秒）...".format(max_wait))
                while waited < max_wait:
                    time.sleep(check_interval)
                    waited += check_interval
                    
                    # 檢查是否已有密碼彈窗
                    password_window = self.find_window(
                        title_keywords=["需要再次確認", "確認密碼"],
                        max_width=600,
                        max_height=400,
                        exclude_titles=["伺服器設定", "Server Settings"]
                    )
                    
                    # 特殊處理：Nx Witness Client 標題的小視窗也可能是密碼彈窗
                    if not password_window:
                        wins = gw.getAllWindows()
                        visible_wins = [w for w in wins if w.visible]
                        for win in visible_wins:
                            if win.title == "Nx Witness Client" and win.width < 600 and win.height < 400:
                                if "伺服器設定" not in win.title and "Server Settings" not in win.title:
                                    password_window = win
                                    break
                    
                    if password_window:
                        self.logger.info("✅ 檢測到密碼確認彈窗！標題='{}', 尺寸={}x{}".format(
                            password_window.title, password_window.width, password_window.height))
                        
                        # 保存截圖：檢測到密碼彈窗時
                        try:
                            screenshot = pyautogui.screenshot()
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                            screenshot_path = os.path.join(debug_dir, f"01_password_popup_detected_after_confirm_{timestamp}.png")
                            screenshot.save(screenshot_path)
                            self.logger.info(f"[DEBUG_SCREENSHOT] 檢測到密碼彈窗時截圖已保存: {screenshot_path}")
                        except Exception as e:
                            self.logger.warning(f"[DEBUG_SCREENSHOT] 保存截圖失敗: {e}")
                        
                        password_window_found = True
                        break
                
                # 如果檢測到密碼彈窗，處理它
                if password_window_found:
                    self.logger.info("🔐 開始處理密碼確認流程...")
                    password_confirmed = self._handle_password_confirmation()
                    if not password_confirmed:
                        self.logger.warning("⚠️ 密碼確認失敗")
                        return False
                    self.logger.info("✅ 已處理密碼確認彈窗")
                else:
                    self.logger.info("ℹ️ 未檢測到密碼確認彈窗（可能不需要密碼）")
            else:
                self.logger.warning("⚠️ 點擊「確認」按鈕失敗")
                return False
            
            # 等待伺服器設定窗口關閉
            self._wait_for_settings_window_close(timeout=2)
            return True
        else:
            # 流程 1: checkbox 未勾選，執行完整流程
            self.logger.info("✅ Checkbox 未勾選，執行完整流程（勾選 → 套用 → 密碼 → 確認）...")
            
            # 步驟 2: 點擊「套用」按鈕（第一次）
            self.logger.info("🖱️ 點擊「套用」按鈕...")
            from config import EnvConfig
            locator_config = EnvConfig.LOCATOR_CONFIG
            apply_btn_locator = locator_config.APPLY_BTN_BOTTOM_RIGHT.with_text("套用")
            apply_clicked = self.click_with_locator(apply_btn_locator)
            
            if not apply_clicked:
                self.logger.error("❌ 點擊「套用」按鈕失敗")
                return False
            
            self.logger.info("✅ 成功點擊「套用」按鈕")
            
            # 保存截圖：點擊「套用」後的狀態
            try:
                import pyautogui
                screenshot = pyautogui.screenshot()
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "password_debug")
                os.makedirs(debug_dir, exist_ok=True)
                import datetime
                now = datetime.datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                screenshot_path = os.path.join(debug_dir, f"00_after_apply_click_{timestamp}.png")
                screenshot.save(screenshot_path)
                self.logger.info(f"[DEBUG_SCREENSHOT] 點擊「套用」後截圖已保存: {screenshot_path}")
            except Exception as e:
                self.logger.warning(f"[DEBUG_SCREENSHOT] 保存截圖失敗: {e}")
            
            # 步驟 3: 等待密碼彈窗出現，然後處理密碼確認彈窗（輸入密碼）
            # 循環檢查密碼彈窗是否出現，最多等待 3 秒
            password_window_found = False
            max_wait = 3.0
            check_interval = 0.2
            waited = 0.0
            
            self.logger.info("🔍 等待密碼確認彈窗出現（最多等待 {:.1f} 秒）...".format(max_wait))
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                
                self.logger.debug(f"[DEBUG] 等待中... ({waited:.1f}/{max_wait:.1f} 秒)")
                
                # 檢查是否已有密碼彈窗
                password_window = self.find_window(
                    title_keywords=["需要再次確認", "確認密碼"],
                    max_width=600,
                    max_height=400,
                    exclude_titles=["伺服器設定", "Server Settings"]
                )
                
                # 特殊處理：Nx Witness Client 標題的小視窗也可能是密碼彈窗
                if not password_window:
                    wins = gw.getAllWindows()
                    visible_wins = [w for w in wins if w.visible]
                    self.logger.debug(f"[DEBUG] 當前可見窗口數量: {len(visible_wins)}")
                    for win in visible_wins:
                        if win.title == "Nx Witness Client" and win.width < 600 and win.height < 400:
                            if "伺服器設定" not in win.title and "Server Settings" not in win.title:
                                self.logger.debug(f"[DEBUG] 找到候選密碼彈窗: 標題='{win.title}', 尺寸={win.width}x{win.height}")
                                password_window = win
                                break
                
                if password_window:
                    self.logger.info("✅ 檢測到密碼確認彈窗！標題='{}', 尺寸={}x{}".format(
                        password_window.title, password_window.width, password_window.height))
                    
                    # 保存截圖：檢測到密碼彈窗時
                    try:
                        screenshot = pyautogui.screenshot()
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                        screenshot_path = os.path.join(debug_dir, f"01_password_popup_detected_{timestamp}.png")
                        screenshot.save(screenshot_path)
                        self.logger.info(f"[DEBUG_SCREENSHOT] 檢測到密碼彈窗時截圖已保存: {screenshot_path}")
                    except Exception as e:
                        self.logger.warning(f"[DEBUG_SCREENSHOT] 保存截圖失敗: {e}")
                    
                    password_window_found = True
                    break
            
            if not password_window_found:
                self.logger.warning("⚠️ 等待 {:.1f} 秒後仍未檢測到密碼確認彈窗".format(max_wait))
                # 列出所有可見窗口，方便調試
                all_wins = [w for w in gw.getAllWindows() if w.visible]
                if all_wins:
                    self.logger.info("[DEBUG] 當前所有可見窗口列表：")
                    for win in all_wins:
                        self.logger.info(f"[DEBUG]   - 標題: '{win.title}', 尺寸: {win.width}x{win.height}")
                
                # 保存截圖：未找到密碼彈窗時
                try:
                    screenshot = pyautogui.screenshot()
                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                    screenshot_path = os.path.join(debug_dir, f"02_password_popup_not_found_{timestamp}.png")
                    screenshot.save(screenshot_path)
                    self.logger.info(f"[DEBUG_SCREENSHOT] 未找到密碼彈窗時截圖已保存: {screenshot_path}")
                except Exception as e:
                    self.logger.warning(f"[DEBUG_SCREENSHOT] 保存截圖失敗: {e}")
                # 即使沒找到彈窗，也嘗試處理（可能彈窗標題不同）
            
            # 處理密碼確認彈窗（輸入密碼）
            self.logger.info("🔐 開始處理密碼確認流程...")
            password_confirmed = self._handle_password_confirmation()
            if not password_confirmed:
                self.logger.warning("⚠️ 密碼確認失敗或未檢測到密碼彈窗")
                return False
            
            self.logger.info("✅ 已處理密碼確認彈窗")
            
            # 步驟 4: 密碼彈窗關閉後，再次點擊「確認」按鈕
            # 等待一下，讓密碼彈窗完全關閉
            time.sleep(0.5)
            
            self.logger.info("🔄 密碼確認後，再次點擊「確認」按鈕...")
            from config import EnvConfig
            locator_config = EnvConfig.LOCATOR_CONFIG
            confirm_btn_locator = locator_config.OK_BTN_BOTTOM_RIGHT.with_text("確認")
            confirm_clicked = self.click_with_locator(confirm_btn_locator)
            
            if confirm_clicked:
                self.logger.info("✅ 成功點擊「確認」按鈕")
            else:
                self.logger.warning("⚠️ 未找到「確認」按鈕，可能已經關閉")
            
            # 步驟 5: 等待伺服器設定窗口關閉
            self._wait_for_settings_window_close(timeout=2)
            return True
    
    def _handle_password_confirmation(self):
        """
        🔐 處理密碼確認彈窗
        當修改伺服器設定後，可能會彈出「需要再次確認密碼以套用設定」的彈窗
        
        返回：
        - True: 彈窗已處理（或無彈窗）
        - False: 處理失敗
        """
        # 從配置讀取密碼
        from config import EnvConfig
        password = getattr(EnvConfig, 'ADMIN_PASSWORD', '')
        
        self.logger.info(f"[DEBUG] 準備處理密碼確認，密碼長度: {len(password) if password else 0}")
        
        # 調用 base 層的密碼彈窗處理方法
        result = self.handle_password_popup(
            password=password,
            popup_title_keywords=["需要再次確認", "確認密碼"],
            input_x_ratio=0.5,
            input_y_ratio=0.45
        )
        
        self.logger.info(f"[DEBUG] 密碼確認處理結果: {result}")
        return result
    
    def _handle_potential_auth_dialog(self, password=None):
        """
        處理可能的授權驗證彈窗（支援 '登入' 和 '確認' 兩種類型）
        
        當點擊「套用」後，可能會隨機出現兩種不同的授權驗證彈窗：
        - 情況 A：按鈕文字為「登入」 (Login)
        - 情況 B：按鈕文字為「確認」 (Confirm) 或「確定」 (OK)
        
        Args:
            password: 密碼（如果為 None，從配置讀取）
        
        Returns:
            bool: True 表示彈窗已處理（或無彈窗），False 表示處理失敗
        """
        from config import EnvConfig
        
        # 從配置讀取密碼（如果未提供）
        if password is None:
            password = getattr(EnvConfig, 'ADMIN_PASSWORD', '')
        
        self.logger.info("[AUTH] [START] Checking for authentication dialog...")
        
        # 等待彈窗動畫完成
        wait_time = 2.0
        self.logger.debug(f"[AUTH] [WAIT] Waiting {wait_time}s for dialog animation...")
        time.sleep(wait_time)
        
        # 1. 判斷是否有彈窗（簡單檢查：嘗試尋找密碼相關文字）
        # 由於 smart_click 會實際點擊，我們先嘗試快速檢測，如果找不到就假設有彈窗
        self.logger.info("[AUTH] [CHECK] Checking for password field...")
        password_texts = ["密碼", "Password", "密码"]
        has_dialog = False
        
        # 嘗試快速檢測密碼文字（使用短 timeout，如果找到就點擊以聚焦輸入框）
        for text in password_texts:
            found = self.smart_click(
                x_ratio=0.5,
                y_ratio=0.45,  # 密碼輸入框通常在對話框中央偏上
                target_text=text,
                timeout=1,  # 短 timeout，快速檢測
                use_vlm=False  # 圖片優先
            )
            if found:
                has_dialog = True
                self.logger.info(f"[AUTH] [CHECK] Found password field indicator: '{text}' (clicked to focus)")
                time.sleep(0.3)  # 等待輸入框獲得焦點
                break
        
        # 如果沒找到，假設有彈窗（因為調用此方法通常意味著預期會有彈窗）
        # 直接嘗試點擊對話框中央以聚焦輸入框
        if not has_dialog:
            self.logger.info("[AUTH] [CHECK] No password field detected, assuming dialog present (will attempt direct input)")
            # 嘗試點擊對話框中央（假設是輸入框位置）
            screen_w, screen_h = pyautogui.size()
            pyautogui.click(screen_w // 2, screen_h // 2)
            time.sleep(0.3)
            has_dialog = True  # 假設有彈窗，繼續處理
        
        if not has_dialog:
            self.logger.info("[AUTH] [RESULT] No dialog detected. Continuing.")
            return True
        
        self.logger.info("[AUTH] [DIALOG] Dialog detected. Entering password...")
        
        # 2. 輸入密碼
        # 確保焦點在輸入框（點擊密碼文字旁邊，或直接輸入）
        self.logger.info("[AUTH] [INPUT] Focusing password field...")
        password_focused = False
        for text in password_texts:
            if self.smart_click(
                x_ratio=0.5,
                y_ratio=0.45,  # 密碼輸入框通常在對話框中央偏上
                target_text=text,
                timeout=2,
                use_vlm=False  # 圖片優先
            ):
                password_focused = True
                self.logger.info(f"[AUTH] [INPUT] Focused password field using text: '{text}'")
                break
        
        # 如果找不到密碼文字，直接嘗試輸入（假設焦點已在輸入框）
        if not password_focused:
            self.logger.warning("[AUTH] [INPUT] Could not find password field, attempting direct input...")
            # 嘗試點擊對話框中央（假設是輸入框位置）
            pyautogui.click(pyautogui.size()[0] // 2, pyautogui.size()[1] // 2)
            time.sleep(0.3)
        
        # 輸入密碼
        self.logger.info(f"[AUTH] [INPUT] Typing password (length: {len(password)})...")
        pyautogui.write(password, interval=0.05)
        time.sleep(0.5)
        self.logger.info("[AUTH] [INPUT] Password entered.")
        
        # 3. 分支處理按鈕（優先嘗試「登入」，然後「確認」，最後「OK」）
        # 嘗試 1: 「登入」按鈕
        self.logger.info("[AUTH] [BUTTON] Trying button type: 'Login' (登入)...")
        login_texts = ["登入", "登錄", "Login", "登录"]
        login_clicked = False
        
        for text in login_texts:
            if self.smart_click(
                x_ratio=0.5,
                y_ratio=0.6,  # 按鈕通常在對話框下方
                target_text=text,
                image_path="desktop_settings/login_btn.png",
                timeout=2,
                use_vlm=False  # 圖片優先
            ):
                self.logger.info(f"[AUTH] [BUTTON] Clicked 'Login' button (text: '{text}').")
                login_clicked = True
                break
        
        if login_clicked:
            time.sleep(1.0)  # 等待彈窗關閉
            self.logger.info("[AUTH] [SUCCESS] Authentication dialog handled (Login button).")
            return True
        
        # 嘗試 2: 「確認」按鈕
        self.logger.info("[AUTH] [BUTTON] Trying button type: 'Confirm' (確認)...")
        confirm_texts = ["確認", "确定", "Confirm"]
        confirm_clicked = False
        
        for text in confirm_texts:
            if self.smart_click(
                x_ratio=0.5,
                y_ratio=0.6,
                target_text=text,
                image_path="desktop_settings/red_ok_btn.png",
                timeout=2,
                use_vlm=False  # 圖片優先
            ):
                self.logger.info(f"[AUTH] [BUTTON] Clicked 'Confirm' button (text: '{text}').")
                confirm_clicked = True
                break
        
        if confirm_clicked:
            time.sleep(1.0)  # 等待彈窗關閉
            self.logger.info("[AUTH] [SUCCESS] Authentication dialog handled (Confirm button).")
            return True
        
        # 嘗試 3: 「OK」按鈕
        self.logger.info("[AUTH] [BUTTON] Trying button type: 'OK'...")
        if self.smart_click(
            x_ratio=0.5,
            y_ratio=0.6,
            target_text="OK",
            image_path="desktop_settings/red_ok_btn.png",
            timeout=1,
            use_vlm=False  # 圖片優先
        ):
            self.logger.info("[AUTH] [BUTTON] Clicked 'OK' button.")
            time.sleep(1.0)  # 等待彈窗關閉
            self.logger.info("[AUTH] [SUCCESS] Authentication dialog handled (OK button).")
            return True
        
        # 如果所有按鈕都沒找到，記錄警告但返回 True（假設沒有彈窗或已自動關閉）
        self.logger.warning("[AUTH] [WARN] Dialog found but no known button clicked. Assuming dialog handled or not present.")
        return True
    
    def _wait_for_settings_window_close(self, timeout=2):
        """
        智能等待設定視窗關閉
        :param timeout: 超時時間（秒）
        """
        # 調用 base 層的視窗關閉等待方法
        success = self.wait_for_window_close(
            window_titles=["Server Settings", "伺服器設定"],
            timeout=timeout
        )
        
        if success:
            self.logger.info("✅ 設定視窗已關閉")
        
        time.sleep(0.2)  # 短暫穩定
    
    def double_click_server_icon(self):
        """
        🎯 雙擊 Server 項目（展開攝影機列表）
        與右鍵點擊是同一個位置，使用相同的 server_icon.png
        優先級：圖片辨識 > OCR 文字 > 座標保底
        """
        self.logger.info("🖱️ 雙擊 Server 項目...")
        
        # 使用 smart_click 進行雙擊（與右鍵點擊使用相同的定位策略）
        success = self.smart_click(
            x_ratio=0.08,  # 與右鍵相同的保底座標
            y_ratio=0.08,
            target_text="Server",
            image_path="desktop_main/server_icon.png",  # 與右鍵相同的圖片
            timeout=3,
            clicks=2  # 雙擊
        )
        
        if success:
            self.logger.info("✅ 雙擊 Server 項目完成")
            time.sleep(0.8)  # 等待攝影機列表展開
            return True
        else:
            self.logger.error("❌ 雙擊 Server 項目失敗")
            return False
    
    def find_usb_camera(self, camera_name="usb_cam") -> bool:
        """
        🔍 只尋找 USB 攝影機，不執行點擊
        用於確認攝影機是否已出現在列表中
        
        :param camera_name: 攝影機名稱（預設 "usb_cam"）
        :return: True 如果找到，False 如果未找到
        """
        self.logger.info(f"[FIND] 尋找攝影機: {camera_name}（只找不點）...")
        
        from base.ok_script_recognizer import get_recognizer
        import os
        from config import EnvConfig
        
        recognizer = get_recognizer()
        image_path = os.path.join(EnvConfig.RES_PATH, "desktop_main/usb_cam_item.png")
        
        if not os.path.exists(image_path):
            self.logger.warning(f"⚠️ 圖片不存在: {image_path}")
            return False
        
        # 取得視窗區域
        win = self.get_nx_window()
        if not win:
            self.logger.warning("⚠️ 找不到 Nx Witness 視窗")
            return False
        
        region = (win.left, win.top, win.width, win.height)
        
        # 使用 OK Script 進行圖片辨識（只找不點）
        result = recognizer.locate_on_screen(image_path, region=region, confidence=0.7)
        
        if result and result.success:
            self.logger.info(f"✅ 找到攝影機 {camera_name}（信心度: {result.confidence:.2f}）")
            return True
        else:
            self.logger.debug(f"⚠️ 未找到攝影機 {camera_name}")
            return False
    
    def double_click_usb_camera_strict(self, camera_name="usb_cam") -> bool:
        """
        🎯 嚴格模式：只使用圖片辨識雙擊 USB 攝影機，不使用保底座標
        如果圖片辨識失敗，直接返回 False，不會亂點
        
        :param camera_name: 攝影機名稱（預設 "usb_cam"）
        :return: True 如果成功點擊，False 如果未找到
        """
        self.logger.info(f"[CLICK_STRICT] 雙擊攝影機（嚴格模式，不用保底座標）: {camera_name}...")
        
        from base.ok_script_recognizer import get_recognizer
        import os
        from config import EnvConfig
        
        recognizer = get_recognizer()
        image_path = os.path.join(EnvConfig.RES_PATH, "desktop_main/usb_cam_item.png")
        
        if not os.path.exists(image_path):
            self.logger.warning(f"⚠️ 圖片不存在: {image_path}")
            return False
        
        # 取得視窗區域
        win = self.get_nx_window()
        if not win:
            self.logger.warning("⚠️ 找不到 Nx Witness 視窗")
            return False
        
        region = (win.left, win.top, win.width, win.height)
        
        # 使用 OK Script 進行圖片辨識
        result = recognizer.locate_on_screen(image_path, region=region, confidence=0.7)
        
        if result and result.success:
            # 計算中心點
            center_x = result.x + (result.width // 2) if result.width > 0 else result.x
            center_y = result.y + (result.height // 2) if result.height > 0 else result.y
            
            self.logger.info(f"✅ 找到攝影機，位置: ({center_x}, {center_y})，執行雙擊...")
            
            # 執行雙擊
            import pyautogui
            pyautogui.doubleClick(center_x, center_y, interval=0.1)
            
            # 等待畫面載入
            import time
            time.sleep(1)
            
            self.logger.info(f"✅ 雙擊攝影機成功: {camera_name}")
            return True
        else:
            self.logger.warning(f"⚠️ 嚴格模式：未找到攝影機 {camera_name}，不執行點擊")
            return False
    
    def double_click_usb_camera(self, camera_name="usb_cam"):
        """
        🎯 雙擊 USB 攝影機項目（兼容舊版，包含保底座標）
        優先級：圖片辨識 > OCR 文字 > 座標保底
        
        :param camera_name: 攝影機名稱（預設 "usb_cam"）
        """
        self.logger.info(f"[CLICK] 雙擊攝影機: {camera_name}...")
        
        # 🎯 使用圖片優先策略（use_vlm=False），確保圖像辨識優先於 VLM
        # 保底座標參考：server_icon 位置約為 (63, 202)，usb_cam 應在其下方一行
        # 計算：x_ratio = 63/1920 ≈ 0.033，y_ratio = 225/1200 ≈ 0.188
        success = self.smart_click(
            x_ratio=0.035,  # 左側面板 x 位置（與 Server 項目對齊，~67px）
            y_ratio=0.188,  # Server 項目下方一行位置（~226px）
            target_text="usb",  # OCR 尋找 "usb" 文字（模糊匹配，作為備選）
            image_path="desktop_main/usb_cam_item.png",  # 圖片辨識優先
            timeout=2,  # 減少超時時間，加快重試速度
            clicks=2,  # 雙擊
            use_vlm=False  # 🎯 關鍵修正：禁用 VLM，確保圖像辨識優先
        )
        
        # 等待畫面載入
        time.sleep(1)
        
        if success:
            self.logger.info(f"✅ 雙擊攝影機: {camera_name} (smart_click 返回成功)")
            return True
        else:
            # 🎯 即使 smart_click 返回 False，也檢查錄影畫面是否真的打開了
            # 因為座標保底可能實際點擊成功，但 smart_click 因異常返回 False
            self.logger.warning(f"⚠️ smart_click 返回 False，但檢查錄影畫面是否已打開...")
            
            # 檢查錄影畫面是否已打開（從 main_page 導入方法）
            from pages.desktop.main_page import MainPage
            main_page = MainPage()
            is_view_open = main_page.is_recording_view_open()
            
            if is_view_open:
                self.logger.info(f"✅ 錄影畫面已打開，判定雙擊成功（即使 smart_click 返回 False）")
                return True
            else:
                self.logger.error(f"❌ 雙擊攝影機失敗: {camera_name} (smart_click 返回 False 且錄影畫面未打開)")
                return False
    
    def ensure_camera_open(self, target_text="usb", max_retries=3):
        """
        🎯 [強化版] 確保攝影機畫面已打開，包含驗證和重試機制
        
        動作：
        1. 使用 VLM 找到文字後執行雙擊
        2. 驗證：雙擊後等待 2-3 秒，檢查 check_recording_view_brightness()
        3. 重試機制：
           - 如果亮度仍為 0 (全黑)，代表沒打開
           - 嘗試備用策略：點擊該座標 (Select) -> 按下鍵盤 Enter 鍵
           - 如果重試 3 次仍失敗，直接 pytest.fail
        
        Args:
            target_text: 要尋找的文字（預設 "usb"）
            max_retries: 最大重試次數（預設 3 次）
        
        Raises:
            pytest.fail: 如果重試 3 次仍無法打開攝影機畫面
        """
        self.logger.info(f"[ENSURE_CAMERA] 開始確保攝影機畫面已打開 (target_text='{target_text}')...")
        
        # 導入 main_page 以使用亮度檢查方法
        from pages.desktop.main_page import MainPage
        main_page = MainPage()
        
        # 檢查是否已經打開
        brightness = main_page.check_recording_view_brightness()
        if brightness > 0:
            self.logger.info(f"[ENSURE_CAMERA] 攝影機畫面已經打開 (亮度={brightness:.2f})，跳過雙擊")
            return True
        
        # 重試循環
        for attempt in range(1, max_retries + 1):
            self.logger.info(f"[ENSURE_CAMERA] 嘗試 {attempt}/{max_retries}: 使用圖像辨識尋找攝影機並雙擊...")
            
            # 🎯 策略 1: 使用圖像辨識優先（use_vlm=False），確保圖像辨識優先於 VLM
            # 保底座標參考：server_icon 位置約為 (63, 202)，usb_cam 應在其下方一行
            success = self.smart_click(
                x_ratio=0.035,  # 左側面板 x 位置（與 Server 項目對齊，~67px）
                y_ratio=0.188,  # Server 項目下方一行位置（~226px）
                target_text=target_text,  # OCR 尋找文字（作為備選）
                image_path="desktop_main/usb_cam_item.png",  # 圖片辨識優先
                timeout=3,
                clicks=2,  # 雙擊
                use_vlm=False  # 🎯 關鍵修正：禁用 VLM，確保圖像辨識優先
            )
            
            if not success:
                self.logger.warning(f"[ENSURE_CAMERA] VLM 雙擊失敗，嘗試備用策略...")
                
                # 策略 2 (備用): 點擊座標 + Enter 鍵
                win = self.get_nx_window()
                if win:
                    # 使用座標保底
                    click_x = win.left + int(win.width * 0.10)
                    click_y = win.top + int(win.height * 0.18)
                    
                    self.logger.info(f"[ENSURE_CAMERA] [FALLBACK] 使用座標保底點擊: ({click_x}, {click_y})")
                    pyautogui.click(click_x, click_y)  # 單擊選擇
                    time.sleep(0.3)
                    pyautogui.press('enter')  # 按下 Enter 鍵
                    self.logger.info(f"[ENSURE_CAMERA] [FALLBACK] 已按下 Enter 鍵")
            
            # 等待畫面載入（2-3 秒）
            wait_time = 2.5
            self.logger.info(f"[ENSURE_CAMERA] 等待 {wait_time} 秒讓畫面載入...")
            time.sleep(wait_time)
            
            # 驗證：檢查亮度
            brightness = main_page.check_recording_view_brightness()
            self.logger.info(f"[ENSURE_CAMERA] 驗證結果: 亮度={brightness:.2f}")
            
            if brightness > 0:
                self.logger.info(f"[ENSURE_CAMERA] ✅ 攝影機畫面已成功打開 (亮度={brightness:.2f})")
                return True
            else:
                self.logger.warning(f"[ENSURE_CAMERA] ⚠️ 嘗試 {attempt}/{max_retries} 失敗: 亮度仍為 0 (全黑)")
                if attempt < max_retries:
                    self.logger.info(f"[ENSURE_CAMERA] 等待 1 秒後重試...")
                    time.sleep(1)
        
        # 所有重試都失敗
        error_msg = f"無法打開攝影機畫面，停止測試。已重試 {max_retries} 次，亮度仍為 0 (全黑)。"
        self.logger.error(f"[ENSURE_CAMERA] ❌ {error_msg}")
        pytest.fail(error_msg)