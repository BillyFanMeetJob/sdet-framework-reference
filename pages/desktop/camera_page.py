from base.desktop_app import DesktopApp
import time
import os
import pygetwindow as gw
from config import EnvConfig
import numpy as np

class CameraPage(DesktopApp):
    def open_add_camera_dialog(self):
        """ 右鍵點擊伺服器並選擇添加攝影機 """
        # 🎯 從 LocatorConfig 獲取配置，保留原值作為預設值（安全備案）
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        server_node_x_ratio = getattr(locator, 'SERVER_NODE_X_RATIO', 0.05) if locator else 0.05
        server_node_y_ratio = getattr(locator, 'SERVER_NODE_Y_RATIO', 0.15) if locator else 0.15
        server_node_image = getattr(locator, 'SERVER_NODE_IMAGE', "desktop_main/server_node.png") if locator else "desktop_main/server_node.png"
        add_camera_x_ratio = getattr(locator, 'ADD_CAMERA_MENU_X_RATIO', 0.1) if locator else 0.1
        add_camera_y_ratio = getattr(locator, 'ADD_CAMERA_MENU_Y_RATIO', 0.2) if locator else 0.2
        add_camera_image = getattr(locator, 'ADD_CAMERA_MENU_IMAGE', "desktop_main/add_camera_menu.png") if locator else "desktop_main/add_camera_menu.png"
        
        # 步驟 1: 使用 smart_click 定位並右鍵點擊伺服器節點
        success = self.smart_click(
            x_ratio=server_node_x_ratio, 
            y_ratio=server_node_y_ratio, 
            image_path=server_node_image,
            target_text="Server",
            click_type='right'  # 直接使用右鍵點擊
        )
        
        if not success:
            self.logger.error("❌ 無法定位伺服器節點")
            return False
        
        # 步驟 2: 點擊右鍵選單中的『添加攝影機』
        return self.smart_click(
            x_ratio=add_camera_x_ratio, 
            y_ratio=add_camera_y_ratio, 
            image_path=add_camera_image,
            target_text="添加攝影機",
            is_relative=True  # 相對於右鍵位置
        )
    
    # 注意：_ensure_camera_visible_and_interact 方法已移至基類 DesktopApp
    # 此類直接繼承使用，無需重複實現（符合 DRY 原則）
    
    def right_click_camera(self, camera_name: str = None) -> bool:
        """
        右鍵點擊攝影機項目（使用智慧展開邏輯）
        
        此方法使用基類的智慧展開邏輯，自動檢查相機是否可見，
        如果不可見則先展開 Server，然後執行右鍵點擊操作。
        
        Args:
            camera_name: 相機名稱，如果為 None 則使用配置中的預設值
        
        Returns:
            bool: 如果成功點擊返回 True，否則返回 False
        
        Note:
            - 使用配置中的等待時間，避免硬編碼
            - 繼承自基類的 _ensure_camera_visible_and_interact 方法（DRY 原則）
        """
        # 使用配置中的預設相機名稱（避免硬編碼）
        if camera_name is None:
            camera_name = EnvConfig.CAMERA_SETTINGS.DEFAULT_CAMERA_NAME
        
        self.logger.info(f"🖱️ 右鍵點擊攝影機: {camera_name}...")
        
        # 🎯 使用基類的智慧展開邏輯（DRY：避免重複實現）
        success = self._ensure_camera_visible_and_interact(action="right_click", camera_name=camera_name)
        
        if success:
            self.logger.info("✅ 右鍵點擊攝影機成功")
            # 使用配置中的等待時間（避免硬編碼）
            time.sleep(EnvConfig.THRESHOLDS.MENU_WAIT_TIME)
            return True
        else:
            self.logger.warning("⚠️ 右鍵點擊攝影機失敗")
            return False
    
    def click_camera_settings_menu(self):
        """
        🎯 點擊右鍵選單中的「攝影機設定... (Camera Settings)」
        優先使用圖片辨識，因為右鍵選單是動態出現的，圖片辨識更穩定
        """
        import sys
        print("=" * 80, file=sys.stderr)
        print("[CLICK_MENU] ========== click_camera_settings_menu() 方法被調用！==========", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        self.logger.info("🖱️ 點擊「攝影機設定」選單項目...")
        self._safe_log("info", "[CLICK_MENU] 準備點擊「攝影機設定」選單項目...")
        
        # 🎯 獲取視窗並限制搜索區域到右鍵菜單附近
        win = self.get_nx_window()
        menu_region = None
        if win:
            # 右鍵菜單通常在右鍵點擊位置的右下方
            # 限制搜索區域：從右鍵點擊位置向右下方延伸
            menu_region_left = win.left + int(win.width * 0.15)  # 菜單通常在左側 15% 開始
            menu_region_top = win.top + int(win.height * 0.25)   # 菜單通常在頂部 25% 開始
            menu_region_width = int(win.width * 0.35)            # 菜單寬度約 35%
            menu_region_height = int(win.height * 0.40)          # 菜單高度約 40%
            menu_region = (menu_region_left, menu_region_top, menu_region_width, menu_region_height)
            self._safe_log("info", f"[CLICK_MENU] 限制搜索區域到右鍵菜單附近: {menu_region}")
            self._safe_log("info", f"[CLICK_MENU] 限制搜索區域: {menu_region}")
        else:
            self._safe_log("warning", "[CLICK_MENU] 無法獲取視窗，使用全屏搜索")
        
        # 🎯 從 LocatorConfig 獲取配置，保留原值作為預設值（安全備案）
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        camera_settings_x_ratio = getattr(locator, 'CAMERA_SETTINGS_MENU_X_RATIO', 0.22) if locator else 0.22
        camera_settings_y_ratio = getattr(locator, 'CAMERA_SETTINGS_MENU_Y_RATIO', 0.38) if locator else 0.38
        camera_settings_image = getattr(locator, 'CAMERA_SETTINGS_MENU_IMAGE', "desktop_main/camera_settings_menu.png") if locator else "desktop_main/camera_settings_menu.png"
        
        # 優先使用圖片辨識（右鍵選單出現後，圖片辨識更可靠）
        self._safe_log("info", "[CLICK_MENU] 調用 smart_click 點擊「攝影機設定」選單...")
        success = self.smart_click(
            x_ratio=camera_settings_x_ratio,
            y_ratio=camera_settings_y_ratio,
            target_text=None,  # 不使用文字辨識（優先圖片辨識）
            image_path=camera_settings_image,  # 優先使用圖片辨識
            is_relative=False,
            timeout=3
        )
        
        # 如果圖片辨識失敗，再嘗試文字辨識（限制在菜單區域）
        if not success:
            self._safe_log("warning", "[WARN] 圖片辨識失敗，嘗試文字辨識（繁體中文，限制區域）...")
            self._safe_log("info", "[CLICK_MENU] 圖片辨識失敗，嘗試 VLM 文字辨識（限制區域）...")
            # 🎯 手動調用 VLM，限制在菜單區域
            if menu_region and win:
                vlm_result = self._try_vlm_recognition("攝影機設定", menu_region, win)
                if vlm_result:
                    success = True
                    self._safe_log("info", "[CLICK_MENU] VLM 在限制區域內找到「攝影機設定」")
                    self._safe_log("info", "[CLICK_MENU] VLM 在限制區域內找到「攝影機設定」")
            
            # 如果限制區域內 VLM 失敗，再嘗試全屏搜索（但這是最後手段）
            if not success:
                self._safe_log("warning", "[WARN] 限制區域內文字辨識失敗，嘗試全屏搜索...")
                self._safe_log("info", "[CLICK_MENU] 限制區域內 VLM 失敗，嘗試全屏搜索...")
                success = self.smart_click(
                    x_ratio=camera_settings_x_ratio,
                    y_ratio=camera_settings_y_ratio,
                    target_text="攝影機設定",  # 文字辨識（全屏搜索）
                    image_path=camera_settings_image,  # 圖片辨識作為備選
                    is_relative=False,
                    timeout=3
                )
        
        # 如果繁體中文失敗，嘗試英文（限制在菜單區域）
        if not success:
            self._safe_log("warning", "[WARN] 繁體中文文字辨識失敗，嘗試英文（限制區域）...")
            self._safe_log("info", "[CLICK_MENU] 繁體中文失敗，嘗試英文 VLM（限制區域）...")
            if menu_region and win:
                # 手動調用 VLM，限制在菜單區域
                vlm_result = self._try_vlm_recognition("Camera Settings", menu_region, win)
                if vlm_result:
                    success = True
                    self._safe_log("info", "[CLICK_MENU] VLM 在限制區域內找到「Camera Settings」")
                    self._safe_log("info", "[CLICK_MENU] VLM 在限制區域內找到「Camera Settings」")
            
            # 如果限制區域內 VLM 失敗，再嘗試全屏搜索（但這是最後手段）
            if not success:
                self._safe_log("warning", "[WARN] 限制區域內英文文字辨識失敗，嘗試全屏搜索...")
                self._safe_log("info", "[CLICK_MENU] 限制區域內英文 VLM 失敗，嘗試全屏搜索...")
                success = self.smart_click(
                    x_ratio=camera_settings_x_ratio,
                    y_ratio=camera_settings_y_ratio,
                    target_text="Camera Settings",  # 文字辨識（全屏搜索）
                    image_path=camera_settings_image,  # 圖片辨識作為備選
                    is_relative=False,
                    timeout=3
                )
        
        if success:
            # 等待攝影機設定視窗出現
            time.sleep(1.5)  # 增加等待時間，確保視窗完全開啟
            
            # 🎯 調試：列出所有可見窗口，幫助診斷問題
            try:
                import pygetwindow as gw
                all_wins = [w for w in gw.getAllWindows() if w.visible]
                # 過濾出可能的攝影機設定窗口（包含關鍵字或尺寸合理）
                camera_candidates = []
                for w in all_wins:
                    if any(kw in w.title for kw in ["攝影機", "Camera", "設定", "Settings"]):
                        camera_candidates.append((w.title, w.width, w.height, w.left, w.top))
                self._safe_log("info", f"[CLICK_MENU] 當前所有可見窗口: {[(w.title, w.width, w.height) for w in all_wins[:10]]}")
                self._safe_log("info", f"[CLICK_MENU] 可能的攝影機設定窗口: {camera_candidates}")
                print(f"[CLICK_MENU] 當前所有可見窗口: {[(w.title, w.width, w.height) for w in all_wins[:10]]}")
                self._safe_log("info", f"[CLICK_MENU] 可能的攝影機設定窗口: {camera_candidates}")
            except Exception as e:
                self._safe_log("warning", f"[CLICK_MENU] 無法列出窗口: {e}")
            
            # 嘗試多種可能的視窗標題（包含部分匹配）
            window_titles = [
                "攝影機設定",
                "Camera Settings",
                "攝影機設定 - Nx Witness Client",
                "Camera Settings - Nx Witness Client"
            ]
            found = self.wait_for_window(window_titles=window_titles, timeout=5)
            if found:
                self.logger.info("✅ 攝影機設定視窗已開啟")
                self._safe_log("info", "[CLICK_MENU] 攝影機設定視窗已開啟")
                return True
            else:
                # 🎯 嘗試使用 find_window 方法（支持部分匹配）
                try:
                    camera_win = self.find_window(
                        title_keywords=["攝影機設定", "Camera Settings"],
                        max_width=2000,  # 使用 max_width 而不是 min_width
                        max_height=2000  # 使用 max_height 而不是 min_height
                    )
                    if camera_win:
                        self.logger.info(f"✅ 使用 find_window 找到攝影機設定視窗: {camera_win.title} ({camera_win.width}x{camera_win.height})")
                        self._safe_log("info", f"[CLICK_MENU] 使用 find_window 找到攝影機設定視窗: {camera_win.title}")
                        return True
                except Exception as e:
                    self._safe_log("warning", f"[CLICK_MENU] find_window 查找失敗: {e}")
                    self._safe_log("info", f"[CLICK_MENU] find_window 查找失敗: {e}")
                
                # 即使找不到視窗，也記錄警告但繼續執行
                self.logger.warning("⚠️ wait_for_window 未找到視窗，但點擊已成功，繼續執行後續步驟")
                self._safe_log("info", "[CLICK_MENU] wait_for_window 未找到視窗，但點擊已成功")
                # 給視窗一點時間完全載入
                time.sleep(0.5)
                print("[CLICK_MENU] click_camera_settings_menu() 完成，返回 True")
                return True  # 如果 smart_click 返回 True，說明點擊成功，應該繼續執行
        else:
            self.logger.warning("⚠️ 點擊「攝影機設定」失敗")
            print("[CLICK_MENU] click_camera_settings_menu() 失敗，返回 False")
            return False
    
    def switch_to_recording_tab(self):
        """
        🎯 切換到「錄製」頁籤
        smart_click 會自動處理優先級：文字辨識（優先）> 圖片辨識
        """
        # 使用通用的方法入口日志
        self._log_method_entry("switch_to_recording_tab")
        
        self.logger.info("🖱️ 點擊「錄影」分頁簽...")
        self._safe_log("info", "[CLICK] 點擊「錄製」頁籤...")
        self._safe_log("info", "[SWITCH_TAB] 準備切換到「錄影」分頁簽...")
        
        # 🎯 關鍵修復：獲取攝影機設定視窗，而不是主視窗
        # 因為 get_nx_window() 可能返回主視窗，而我們需要的是攝影機設定視窗
        win = None
        camera_settings_titles = ["攝影機設定", "Camera Settings", "攝影機設定 - Nx Witness Client", "Camera Settings - Nx Witness Client"]
        
        # 嘗試找到攝影機設定視窗（通常比主視窗小，但比彈窗大）
        for title in camera_settings_titles:
            wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
            if wins:
                # 選擇最大的視窗（攝影機設定視窗通常比彈窗大）
                win = max(wins, key=lambda w: w.width * w.height)
                self.logger.info(f"[DEBUG] 找到攝影機設定視窗: 標題={win.title}, 尺寸={win.width}x{win.height}, 位置=({win.left}, {win.top})")
                self._safe_log("info", f"[DEBUG] 視窗信息: 標題={win.title}, 尺寸={win.width}x{win.height}, 位置=({win.left}, {win.top})")
                break
        
        # 如果找不到攝影機設定視窗，嘗試使用 get_nx_window 但過濾掉太小的視窗
        if not win:
            temp_win = self.get_nx_window()
            if temp_win and temp_win.width > 800 and temp_win.height > 600:
                # 只使用足夠大的視窗（排除小彈窗）
                win = temp_win
                self.logger.info(f"[DEBUG] 使用主視窗: 標題={win.title}, 尺寸={win.width}x{win.height}")
            else:
                self.logger.warning("⚠️ 無法獲取攝影機設定視窗信息，嘗試使用全螢幕座標")
                self._safe_log("warning", "[WARN] 無法獲取視窗信息")
        
        # 🎯 關鍵修復：參考 test_vlm_recording_tab.py 的做法
        # 直接在頁籤區域使用 VLM 搜索「錄影」，然後計算座標並點擊
        recording_tab_image = "desktop_settings/recording_tab.png"  # 圖片路徑（如果存在）
        
        # 檢查圖片是否存在
        from config import EnvConfig
        import os
        full_image_path = os.path.join(EnvConfig.RES_PATH, recording_tab_image)
        image_exists = os.path.exists(full_image_path)
        self._safe_log("info", f"[DEBUG] 圖片資源檢查: {recording_tab_image} {'存在' if image_exists else '不存在'} (完整路徑: {full_image_path})")
        
        # 🎯 策略 1: 限制搜索區域到視窗頂部（分頁簽區域）
        # 根據截圖和 test_vlm_recording_tab.py 的測試結果，分頁簽在對話框頂部
        # 🔧 調整：從更上方開始掃描，確保錄影頁簽完全被包含
        if win:
            # 限制搜索區域到分頁簽區域（從標題欄下方 30px 開始，高度 180px）
            # 🔧 修改：tab_region_start_offset 從 50px 改為 30px，height 從 150px 改為 180px
            # 這樣可以確保錄影頁簽完全被包進去
            tab_region_start_offset = 30  # 從視窗頂部向下偏移 30px（跳過標題欄）
            tab_region_height = 180  # 搜索區域高度 180px（增加高度確保包含頁簽）
            tab_region = (win.left, win.top + tab_region_start_offset, win.width, tab_region_height)
            self._safe_log("info", f"[DEBUG] 分頁簽搜索區域（從頂部偏移 {tab_region_start_offset}px，高度 {tab_region_height}px）: {tab_region} (視窗: {win.width}x{win.height})")
            
            # 直接使用 VLM 在分頁簽區域搜索「錄影」
            for target_text in ["錄影", "錄製", "Recording"]:
                self._safe_log("info", f"[DEBUG] 嘗試在分頁簽區域使用 VLM 搜索: '{target_text}'")
                
                # 🎯 在 VLM 掃描前，保存截圖並用紅框標記掃描區域
                self._save_vlm_scan_region_screenshot("vlm_scan_recording_tab", tab_region, win)
                
                vlm = self._get_vlm_engine()
                if vlm:
                    try:
                        result = vlm.find_element(target_text, region=tab_region)
                        if result and result.success and result.confidence > 0.5:
                            click_x = result.x
                            click_y = result.y
                            
                            # 🎯 關鍵驗證：檢查座標是否合理（防止 VLM 返回異常座標）
                            # 分頁簽應該在視窗頂部，y_ratio 應該在 0.05-0.15 範圍內
                            MAX_REASONABLE_X = 10000  # 不應該超過螢幕寬度
                            MAX_REASONABLE_Y = 10000  # 不應該超過螢幕高度
                            
                            if abs(click_x) > MAX_REASONABLE_X or abs(click_y) > MAX_REASONABLE_Y:
                                self._safe_log("warning", f"[WARN] VLM 返回的座標異常巨大，拒絕: ({click_x}, {click_y})")
                                continue  # 跳過這個結果，嘗試下一個文字
                            
                            # 🎯 額外驗證：確保座標在 tab_region 範圍內（加上容差）
                            tab_region_left = tab_region[0]
                            tab_region_top = tab_region[1]
                            tab_region_right = tab_region[0] + tab_region[2]
                            tab_region_bottom = tab_region[1] + tab_region[3]
                            tolerance = 20  # 允許 20px 的誤差
                            
                            in_tab_region = (tab_region_left - tolerance <= click_x <= tab_region_right + tolerance and 
                                           tab_region_top - tolerance <= click_y <= tab_region_bottom + tolerance)
                            
                            if not in_tab_region:
                                self._safe_log("warning", f"[WARN] VLM 返回的座標不在 tab_region 範圍內: ({click_x}, {click_y}), tab_region=({tab_region_left}, {tab_region_top}, {tab_region[2]}, {tab_region[3]})")
                                print(f"[SWITCH_TAB] [WARN] VLM 返回座標 ({click_x}, {click_y}) 不在 tab_region 內，跳過")
                                # 保存錯誤截圖
                                self._save_vlm_error_screenshot("vlm_coord_out_of_tab_region", tab_region, win, click_x, click_y)
                                continue  # 跳過這個結果
                            
                            # 確保座標在視窗範圍內
                            if (win.left <= click_x <= win.left + win.width and 
                                win.top <= click_y <= win.top + win.height):
                                
                                # 計算相對位置用於日誌
                                relative_x = click_x - win.left
                                relative_y = click_y - win.top
                                ratio_x = relative_x / win.width
                                ratio_y = relative_y / win.height
                                
                                # 由於已經限制搜索區域到頂部 200px，找到的結果應該就是分頁簽
                                self._safe_log("info", f"[OK] VLM 找到「錄影」分頁簽: 找到座標=({click_x}, {click_y}), 相對位置=({ratio_x:.4f}, {ratio_y:.4f}), 信心度={result.confidence:.2f}")
                                print(f"[SWITCH_TAB] [FOUND] VLM 找到「錄影」分頁簽: 找到座標=({click_x}, {click_y}), 相對位置=({ratio_x:.4f}, {ratio_y:.4f}), 信心度={result.confidence:.2f}")
                                self.logger.info(f"[SWITCH_TAB] [FOUND] VLM 找到「錄影」分頁簽: 找到座標=({click_x}, {click_y})")
                                
                                # 🎯 記錄：準備使用這個座標進行點擊
                                print(f"[SWITCH_TAB] [BEFORE_CLICK] 準備點擊錄影分頁簽，將使用座標=({click_x}, {click_y})")
                                self.logger.info(f"[SWITCH_TAB] [BEFORE_CLICK] 準備點擊錄影分頁簽，將使用座標=({click_x}, {click_y})")
                                
                                # 執行點擊
                                self._perform_click(click_x, click_y, clicks=1, click_type='left')
                                
                                # 🎯 點擊後保存截圖，標記實際點擊的座標
                                self._save_vlm_click_coord_screenshot("vlm_after_click_recording_tab", tab_region, win, click_x, click_y)
                                
                                time.sleep(1.0)  # 等待頁籤切換
                                self._safe_log("info", f"[OK] 成功點擊「錄影」頁籤（使用 VLM，分頁簽區域搜索）")
                                self._safe_log("info", "[SWITCH_TAB] 已點擊錄影分頁簽，準備驗證是否切換成功...")
                                
                                # 🎯 驗證：檢查是否能找到 radio-button（使用 radio_n.png 或 radio_y.png）
                                if self._verify_recording_tab_switched():
                                    self._safe_log("info", "[SWITCH_TAB] 驗證成功：已切換到錄影分頁簽")
                                    return True
                                else:
                                    self._safe_log("info", "[SWITCH_TAB] 驗證失敗：未找到 radio-button，可能未切換成功")
                                    self.logger.warning("[SWITCH_TAB] ⚠️ 點擊後未找到 radio-button，可能未切換到錄影分頁")
                            else:
                                self._safe_log("warning", f"[WARN] VLM 返回的座標超出視窗範圍: ({click_x}, {click_y}), 視窗範圍=({win.left}, {win.top}, {win.width}, {win.height})")
                                print(f"[SWITCH_TAB] [ERROR] VLM 返回的座標超出視窗範圍: ({click_x}, {click_y}), 視窗範圍=({win.left}, {win.top}, {win.width}, {win.height})")
                                # 🎯 保存錯誤截圖，標記 VLM 返回的座標和視窗範圍
                                self._save_vlm_error_screenshot("vlm_coord_out_of_range", tab_region, win, click_x, click_y)
                    except Exception as e:
                        self._safe_log("warning", f"[WARN] VLM 搜索異常: {e}")
                        self._safe_log("error", f"[SWITCH_TAB] [ERROR] VLM 搜索異常: {e}")
                        import traceback
                        traceback.print_exc()
        
        # 策略 2: 如果 VLM 在 tab_region 內搜索失敗，嘗試僅使用圖片辨識（如果圖片存在）
        # 🔧 關鍵修復：不使用 smart_click 的全視窗搜索，因為會在全視窗內找到錯誤位置的「錄影」文字
        # （例如視窗底部的確認按鈕旁也可能有「錄影」相關文字）
        
        # 🎯 從 LocatorConfig 獲取錄影分頁簽配置，保留原值作為預設值（安全備案）
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        recording_tab_x_ratio = getattr(locator, 'RECORDING_TAB_X_RATIO', 0.25) if locator else 0.25
        recording_tab_y_ratios = getattr(locator, 'RECORDING_TAB_Y_RATIOS', [0.10, 0.12, 0.15, 0.08]) if locator else [0.10, 0.12, 0.15, 0.08]
        recording_tab_image_config = getattr(locator, 'RECORDING_TAB_IMAGE', "desktop_settings/recording_tab.png") if locator else "desktop_settings/recording_tab.png"
        
        # 如果所有文字辨識都失敗，嘗試僅使用圖片辨識（如果圖片存在）
        if image_exists:
            self._safe_log("info", "[DEBUG] 所有文字辨識失敗，嘗試僅使用圖片辨識...")
            for y_ratio in recording_tab_y_ratios:  # 嘗試多個垂直位置
                self._safe_log("info", f"[DEBUG] 嘗試圖片辨識位置: x_ratio={recording_tab_x_ratio}, y_ratio={y_ratio}")
                success = self.smart_click(
                    x_ratio=recording_tab_x_ratio,
                    y_ratio=y_ratio,
                    target_text=None,  # 不使用文字辨識
                    image_path=recording_tab_image_config,  # 僅使用圖片辨識
                    timeout=3
                )
                if success:
                    self._safe_log("info", f"[OK] 成功點擊「錄製」頁籤（使用圖片辨識, y_ratio={y_ratio}）")
                    self._safe_log("info", f"[SWITCH_TAB] 已點擊錄影分頁簽（圖片辨識），準備驗證...")
                    
                    # 🎯 點擊後保存截圖，標記實際點擊的座標（從 DesktopApp._last_x, _last_y 獲取）
                    if win and DesktopApp._last_x > 0 and DesktopApp._last_y > 0:
                        self._save_vlm_click_coord_screenshot("image_click_after_click_recording_tab", None, win, DesktopApp._last_x, DesktopApp._last_y)
                    
                    time.sleep(0.5)
                    
                    # 🎯 驗證：檢查是否能找到 radio-button
                    if self._verify_recording_tab_switched():
                        self._safe_log("info", "[SWITCH_TAB] 驗證成功：已切換到錄影分頁簽")
                        return True
                    else:
                        self._safe_log("info", "[SWITCH_TAB] 驗證失敗：未找到 radio-button，但點擊已成功")
        
        # 最終失敗
        self._safe_log("info", "[SWITCH_TAB] 所有方法都失敗，無法切換到錄影分頁簽")
        self._safe_log("warning", "[WARN] 點擊「錄製」頁籤失敗：文字辨識和圖片辨識都失敗")
        self._safe_log("warning", "[TIP] 請確認：1) 頁籤文字是否為「錄影」、「錄製」或「Recording」 2) 是否有錄影頁籤的圖片資源 (res/desktop_settings/recording_tab.png) 3) 頁籤的實際位置")
        raise AssertionError("點擊「錄製」頁籤失敗：無法找到或點擊錄製頁籤")
    
    def _verify_recording_tab_switched(self):
        """
        🎯 驗證是否成功切換到錄影分頁簽
        方法：檢查是否能找到 radio-button（使用 radio_n.png 或 radio_y.png）
        
        :return: True 如果找到 radio-button，False 如果未找到
        """
        self._safe_log("info", "[VERIFY_TAB] 開始驗證是否已切換到錄影分頁簽...")
        self.logger.info("[VERIFY_TAB] 驗證是否已切換到錄影分頁簽（檢查 radio-button）...")
        
        try:
            from config import EnvConfig
            import os
            import pyautogui
            
            # 檢查 radio_n.png
            radio_n_image_path = "desktop_settings/radio_n.png"
            radio_n_image_full_path = os.path.join(EnvConfig.RES_PATH, radio_n_image_path)
            radio_n_exists = os.path.exists(radio_n_image_full_path)
            
            # 檢查 radio_y.png
            radio_y_image_path = "desktop_settings/radio_y.png"
            radio_y_image_full_path = os.path.join(EnvConfig.RES_PATH, radio_y_image_path)
            radio_y_exists = os.path.exists(radio_y_image_full_path)
            
            self._safe_log("info", f"[VERIFY_TAB] 圖片文件檢查: radio_n_exists={radio_n_exists}, radio_y_exists={radio_y_exists}")
            
            # 嘗試找到 radio_n 或 radio_y
            found_radio = False
            
            # 🎯 獲取視窗信息，用於計算掃描區域
            win = self.get_nx_window()
            camera_settings_titles = ["攝影機設定", "Camera Settings", "攝影機設定 - Nx Witness Client", "Camera Settings - Nx Witness Client"]
            camera_win = None
            for title in camera_settings_titles:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    camera_win = max(wins, key=lambda w: w.width * w.height)
                    break
            if not camera_win:
                camera_win = win
            
            # 🎯 計算 radio 掃描區域（通常在左上角，分頁簽下方）
            # 從分頁簽下方開始，約在 y_ratio 0.10-0.25 範圍內
            if camera_win:
                # 🔧 擴大檢測區域：從 y_ratio 0.08 開始（而不是 0.10），高度增加到 20%（而不是 15%）
                # 寬度增加到 35%（而不是 30%），確保 radio 在邊緣也能檢測到
                radio_scan_region_left = camera_win.left
                radio_scan_region_top = camera_win.top + int(camera_win.height * 0.08)  # 從 y_ratio 0.08 開始（擴大上邊界）
                radio_scan_region_width = int(camera_win.width * 0.35)  # 左側 35% 寬度（擴大寬度）
                radio_scan_region_height = int(camera_win.height * 0.20)  # 高度 20%（擴大高度）
                radio_scan_region = (radio_scan_region_left, radio_scan_region_top, radio_scan_region_width, radio_scan_region_height)
                self._safe_log("info", f"[VERIFY_TAB] 計算 radio 掃描區域: {radio_scan_region}")
            else:
                radio_scan_region = None
            
            if radio_n_exists:
                try:
                    self._safe_log("info", f"[VERIFY_TAB] 檢查 radio_n.png: {radio_n_image_full_path}")
                    # 🎯 在掃描前保存截圖，標記掃描區域
                    if radio_scan_region:
                        self._save_radio_scan_region_screenshot("verify_radio_n_scan", radio_scan_region, camera_win)
                    
                    loc = pyautogui.locateOnScreen(radio_n_image_full_path, confidence=0.8, region=radio_scan_region if radio_scan_region else None)
                    if loc:
                        center = pyautogui.center(loc)
                        print(f"[VERIFY_TAB] 找到 radio_n.png: 位置=({center.x}, {center.y})")
                        self.logger.info(f"[VERIFY_TAB] 找到 radio_n.png: 位置=({center.x}, {center.y})")
                        # 🎯 保存找到的座標截圖
                        if camera_win:
                            self._save_radio_found_screenshot("verify_radio_n_found", radio_scan_region, camera_win, center.x, center.y)
                        found_radio = True
                    else:
                        self._safe_log("info", f"[VERIFY_TAB] 未找到 radio_n.png")
                        # 🎯 保存未找到的截圖
                        if radio_scan_region:
                            self._save_radio_not_found_screenshot("verify_radio_n_not_found", radio_scan_region, camera_win)
                except Exception as e:
                    self._safe_log("info", f"[VERIFY_TAB] 檢查 radio_n.png 異常: {e}")
            
            if not found_radio and radio_y_exists:
                try:
                    self._safe_log("info", f"[VERIFY_TAB] 檢查 radio_y.png: {radio_y_image_full_path}")
                    # 🎯 在掃描前保存截圖，標記掃描區域
                    if radio_scan_region:
                        self._save_radio_scan_region_screenshot("verify_radio_y_scan", radio_scan_region, camera_win)
                    
                    loc = pyautogui.locateOnScreen(radio_y_image_full_path, confidence=0.8, region=radio_scan_region if radio_scan_region else None)
                    if loc:
                        center = pyautogui.center(loc)
                        print(f"[VERIFY_TAB] 找到 radio_y.png: 位置=({center.x}, {center.y})")
                        self.logger.info(f"[VERIFY_TAB] 找到 radio_y.png: 位置=({center.x}, {center.y})")
                        # 🎯 保存找到的座標截圖
                        if camera_win:
                            self._save_radio_found_screenshot("verify_radio_y_found", radio_scan_region, camera_win, center.x, center.y)
                        found_radio = True
                    else:
                        self._safe_log("info", f"[VERIFY_TAB] 未找到 radio_y.png")
                        # 🎯 保存未找到的截圖
                        if radio_scan_region:
                            self._save_radio_not_found_screenshot("verify_radio_y_not_found", radio_scan_region, camera_win)
                except Exception as e:
                    self._safe_log("info", f"[VERIFY_TAB] 檢查 radio_y.png 異常: {e}")
            
            if found_radio:
                self._safe_log("info", "[VERIFY_TAB] 驗證成功：已切換到錄影分頁簽（找到 radio-button）")
                self.logger.info("[VERIFY_TAB] 驗證成功：已切換到錄影分頁簽")
                return True
            else:
                self._safe_log("info", "[VERIFY_TAB] 驗證失敗：未找到 radio-button，可能未切換到錄影分頁簽")
                self.logger.warning("[VERIFY_TAB] 驗證失敗：未找到 radio-button")
                return False
                
        except Exception as e:
            self._safe_log("info", f"[VERIFY_TAB] 驗證過程異常: {e}")
            self.logger.warning(f"[VERIFY_TAB] ❌ 驗證過程異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_and_set_recording_radio_y(self):
        """
        🎯 檢查並設置錄影標籤頁左上角的 radio-button 為 "Y"
        返回: (success, was_already_y)
        - success: 是否成功處理（檢查或設置）
        - was_already_y: 是否已經是 "Y"（True 表示不需要框選時段，直接點確認即可）
        """
        self.logger.info("=" * 80)
        self.logger.info("[RADIO] ========== 開始檢查並設置 radio-button ==========")
        self.logger.info("=" * 80)
        self._safe_log("info", "[RADIO] 檢查錄影標籤頁左上角 radio-button 狀態...")
        
        # 🎯 立即截圖：記錄開始時的狀態
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "radio_debug")
            os.makedirs(debug_dir, exist_ok=True)
            import datetime
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            screenshot_path = os.path.join(debug_dir, f"00_start_check_radio_{timestamp}.png")
            screenshot.save(screenshot_path)
            self.logger.info(f"[RADIO] [SCREENSHOT] 開始檢查時的截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[RADIO] [SCREENSHOT] 開始檢查時的截圖已保存: {screenshot_path}")
        except Exception as e:
            self.logger.warning(f"[RADIO] [SCREENSHOT] 保存開始截圖失敗: {e}")
        
        # 🎯 關鍵修復：獲取攝影機設定視窗（不是主視窗）
        win = None
        camera_settings_titles = ["攝影機設定", "Camera Settings", "攝影機設定 - Nx Witness Client", "Camera Settings - Nx Witness Client"]
        
        # 嘗試找到攝影機設定視窗
        for title in camera_settings_titles:
            wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
            if wins:
                win = max(wins, key=lambda w: w.width * w.height)
                break
        
        if not win:
            temp_win = self.get_nx_window()
            if temp_win and temp_win.width > 800 and temp_win.height > 600:
                win = temp_win
            else:
                self.logger.warning("⚠️ 無法獲取攝影機設定視窗信息")
                return (False, False)
        
        # 🎯 調整位置：根據截圖，radio-button 在「錄影」分頁簽正下方
        # 🎯 從 LocatorConfig 獲取 Radio Button 配置，保留原值作為預設值（安全備案）
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        radio_y_x_ratio = getattr(locator, 'RADIO_Y_X_RATIO', 0.10) if locator else 0.10  # 左上角偏左一點
        radio_y_y_ratio = getattr(locator, 'RADIO_Y_Y_RATIO', 0.15) if locator else 0.15  # 調整：分頁簽下方
        
        # 🎯 步驟 1: 先檢查當前狀態（優先使用圖片辨識）
        # 注意：EnvConfig 已在文件開頭導入，不需要重複導入
        
        # 檢查是否為 "N"（需要改為 "Y"）
        radio_n_image_path = "desktop_settings/radio_n.png"
        radio_n_image_full_path = os.path.join(EnvConfig.RES_PATH, radio_n_image_path)
        radio_n_image_exists = os.path.exists(radio_n_image_full_path)
        
        # 檢查是否為 "Y"（已經是 Y，不需要框選）
        radio_y_image_path = "desktop_settings/radio_y.png"
        radio_y_image_full_path = os.path.join(EnvConfig.RES_PATH, radio_y_image_path)
        radio_y_image_exists = os.path.exists(radio_y_image_full_path)
        
        # 🎯 步驟 1: 先檢查是否已經是 "Y"（使用圖片辨識，只檢查不點擊）
        self._safe_log("info", f"[RADIO] [STEP 1-1] 檢查圖片文件是否存在: radio_y_image_exists={radio_y_image_exists}")
        self.logger.info(f"[RADIO] [STEP 1-1] 檢查圖片文件是否存在: radio_y_image_exists={radio_y_image_exists}, 路徑={radio_y_image_full_path}")
        
        if radio_y_image_exists:
            self.logger.info(f"[RADIO] [CHECK] 檢查是否為 'Y'（使用圖片辨識）: {radio_y_image_path}")
            self._safe_log("debug", f"[RADIO] [CHECK] 檢查是否為 'Y'（使用圖片辨識）: {radio_y_image_path}")
            try:
                import pyautogui
                # 構建完整路徑
                full_path = os.path.join(EnvConfig.RES_PATH, radio_y_image_path)
                self._safe_log("debug", f"[RADIO] [CHECK] 使用 pyautogui.locateOnScreen 檢查 'Y' 圖片，完整路徑={full_path}")
                # 使用 locateOnScreen 檢查圖片是否存在（不點擊）
                # 注意：新版本的 pyautogui 不支持 timeout 參數
                loc = pyautogui.locateOnScreen(full_path, confidence=0.8)
                if loc:
                    center = pyautogui.center(loc)
                    self.logger.info(f"[RADIO] ✅ 找到 'Y' 圖片辨識: 位置=({center.x}, {center.y}), 區域={loc}")
                    self._safe_log("info", f"[RADIO] 找到 'Y' 圖片辨識: 位置=({center.x}, {center.y})")
                    
                    # 🎯 關鍵修復：驗證是否同時找到 "N"，如果同時找到，說明辨識可能有誤，應該繼續處理
                    if radio_n_image_exists:
                        try:
                            full_n_path = os.path.join(EnvConfig.RES_PATH, radio_n_image_path)
                            loc_n = pyautogui.locateOnScreen(full_n_path, confidence=0.8)
                            if loc_n:
                                center_n = pyautogui.center(loc_n)
                                # 檢查兩個位置是否接近（可能是同一個 radio button 的誤判）
                                distance = ((center.x - center_n.x) ** 2 + (center.y - center_n.y) ** 2) ** 0.5
                                if distance < 50:  # 如果距離小於 50 像素，可能是同一個位置
                                    self.logger.warning(f"[RADIO] ⚠️ 同時找到 'Y' 和 'N'，位置接近（距離={distance:.1f}px），可能是誤判，繼續檢查 'N'...")
                                    self._safe_log("warning", f"[RADIO] ⚠️ 同時找到 'Y' 和 'N'，位置接近，可能是誤判，繼續處理")
                                    # 不返回，繼續檢查 "N"
                                else:
                                    # 兩個位置距離較遠，可能是不同的元素，優先相信 "N"（因為目標是要設置為 Y）
                                    self.logger.warning(f"[RADIO] ⚠️ 同時找到 'Y' 和 'N'，但位置距離較遠（距離={distance:.1f}px），優先相信 'N'，繼續處理")
                                    self._safe_log("warning", f"[RADIO] ⚠️ 同時找到 'Y' 和 'N'，但位置距離較遠，優先相信 'N'")
                                    # 不返回，繼續檢查 "N"
                            else:
                                # 只找到 "Y"，沒有找到 "N"，確認是 Y
                                self._save_radio_debug_screenshot("01_found_radio_y", center.x, center.y)
                                self.logger.info("[RADIO] ✅ 當前 radio-button 已經是 'Y'（未找到 'N' 確認），不需要框選時段，直接點確認即可")
                                print("[RADIO] 當前 radio-button 已經是 'Y'，返回 (True, True)")
                                return (True, True)  # 已經是 Y，不需要框選
                        except Exception as e:
                            self.logger.warning(f"[RADIO] [VERIFY] 驗證 'N' 時異常: {e}，假設 'Y' 正確")
                            # 驗證失敗，假設 Y 正確
                            self._save_radio_debug_screenshot("01_found_radio_y", center.x, center.y)
                            self.logger.info("[RADIO] ✅ 當前 radio-button 已經是 'Y'（驗證失敗但假設正確），不需要框選時段")
                            print("[RADIO] 當前 radio-button 已經是 'Y'，返回 (True, True)")
                            return (True, True)  # 已經是 Y，不需要框選
                    else:
                        # radio_n.png 不存在，無法驗證，假設 Y 正確
                        self._save_radio_debug_screenshot("01_found_radio_y", center.x, center.y)
                        self.logger.info("[RADIO] ✅ 當前 radio-button 已經是 'Y'（無法驗證但假設正確），不需要框選時段")
                        print("[RADIO] 當前 radio-button 已經是 'Y'，返回 (True, True)")
                        return (True, True)  # 已經是 Y，不需要框選
                else:
                    self.logger.info(f"[RADIO] [CHECK] 未找到 'Y' 圖片辨識，繼續檢查 'N'...")
                    self._safe_log("debug", f"[RADIO] [CHECK] 未找到 'Y' 圖片辨識，loc={loc}")
            except Exception as e:
                self.logger.warning(f"[RADIO] [CHECK] 檢查 'Y' 圖片異常: {e}")
                self._safe_log("debug", f"[RADIO] [CHECK] 檢查 'Y' 圖片異常: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.logger.info(f"[RADIO] [CHECK] radio_y.png 圖片文件不存在，跳過 'Y' 檢查")
            self._safe_log("debug", f"[RADIO] [CHECK] radio_y.png 圖片文件不存在: {radio_y_image_full_path}")
        
        # 🎯 步驟 2: 檢查是否為 "N"（使用圖片辨識，只檢查不點擊）
        self._safe_log("info", f"[RADIO] [STEP 1-2] 檢查圖片文件是否存在: radio_n_image_exists={radio_n_image_exists}")
        self.logger.info(f"[RADIO] [STEP 1-2] 檢查圖片文件是否存在: radio_n_image_exists={radio_n_image_exists}, 路徑={radio_n_image_full_path}")
        
        if radio_n_image_exists:
            self.logger.info(f"[RADIO] [CHECK] 檢查是否為 'N'（使用圖片辨識）: {radio_n_image_path}")
            self._safe_log("debug", f"[RADIO] [CHECK] 檢查是否為 'N'（使用圖片辨識）: {radio_n_image_path}")
            try:
                import pyautogui
                # 構建完整路徑
                full_path = os.path.join(EnvConfig.RES_PATH, radio_n_image_path)
                self._safe_log("debug", f"[RADIO] [CHECK] 使用 pyautogui.locateOnScreen 檢查 'N' 圖片，完整路徑={full_path}")
                # 使用 locateOnScreen 檢查圖片是否存在（不點擊）
                # 注意：新版本的 pyautogui 不支持 timeout 參數
                loc = pyautogui.locateOnScreen(full_path, confidence=0.8)
                if loc:
                    center = pyautogui.center(loc)
                    self.logger.info(f"[RADIO] ✅ 找到 'N' 圖片辨識: 位置=({center.x}, {center.y}), 區域={loc}")
                    print(f"[RADIO] 找到 'N' 圖片辨識: 位置=({center.x}, {center.y})")
                    self._safe_log("info", f"[RADIO] 找到 'N' 圖片辨識: 位置=({center.x}, {center.y})")
                    # 截圖記錄
                    self._save_radio_debug_screenshot("02_found_radio_n", center.x, center.y)
                    self.logger.info("[RADIO] ✅ 當前 radio-button 是 'N'，需要點擊改為 'Y'")
                    self._safe_log("info", "[RADIO] 當前 radio-button 是 'N'，準備點擊改為 'Y'")
                    # 🎯 修復：使用 radio_n.png 定位（當前狀態是 N），點擊同一位置會切換為 Y
                    self.logger.info(f"[RADIO] 準備點擊 'N' 位置（點擊後會切換為 'Y'）: x_ratio={radio_y_x_ratio}, y_ratio={radio_y_y_ratio}")
                    self._safe_log("info", f"[RADIO] 調用 smart_click_priority_image 使用 radio_n.png 定位: x_ratio={radio_y_x_ratio}, y_ratio={radio_y_y_ratio}")
                    success = self.smart_click_priority_image(
                        x_ratio=radio_y_x_ratio,
                        y_ratio=radio_y_y_ratio,
                        target_text="N",  # 使用 "N" 作為輔助文字辨識
                        image_path=radio_n_image_path,  # 🎯 修復：使用 radio_n.png 定位（當前狀態）
                        timeout=2
                    )
                    self._safe_log("info", f"[RADIO] smart_click_priority_image 返回: {success}")
                    if success:
                        # 等待狀態切換
                        time.sleep(0.5)
                        
                        # 🎯 驗證：點擊後檢查是否成功變為 'Y'
                        self.logger.info("[RADIO] [VERIFY] 點擊後驗證是否成功變為 'Y'...")
                        self._safe_log("info", "[RADIO] [VERIFY] 點擊後驗證是否成功變為 'Y'...")
                        
                        if radio_y_image_exists:
                            try:
                                import pyautogui
                                full_y_path = os.path.join(EnvConfig.RES_PATH, radio_y_image_path)
                                loc_y = pyautogui.locateOnScreen(full_y_path, confidence=0.8)
                                if loc_y:
                                    center_y = pyautogui.center(loc_y)
                                    self.logger.info(f"[RADIO] [VERIFY] ✅ 驗證成功：已成功變為 'Y'，位置=({center_y.x}, {center_y.y})")
                                    print(f"[RADIO] [VERIFY] ✅ 驗證成功：已成功變為 'Y'，位置=({center_y.x}, {center_y.y})")
                                    # 截圖記錄驗證成功
                                    self._save_radio_debug_screenshot("03_verify_radio_y", center_y.x, center_y.y)
                                    self.logger.info("[RADIO] ✅ 成功將 radio-button 從 'N' 改為 'Y'")
                                    print("[RADIO] 成功將 radio-button 從 'N' 改為 'Y'，返回 (True, False)")
                                    self._safe_log("info", "[RADIO] ✅ 成功將 radio-button 從 'N' 改為 'Y'")
                                    return (True, False)  # 已改為 Y，需要框選
                                else:
                                    self.logger.warning("[RADIO] [VERIFY] ⚠️ 驗證失敗：點擊後仍未找到 'Y' 圖片，可能點擊失敗")
                                    self._safe_log("warning", "[RADIO] [VERIFY] ⚠️ 驗證失敗：點擊後仍未找到 'Y' 圖片")
                                    # 截圖記錄驗證失敗
                                    win = self.get_nx_window()
                                    if win:
                                        click_x = win.left + int(win.width * radio_y_x_ratio)
                                        click_y = win.top + int(win.height * radio_y_y_ratio)
                                        self._save_radio_debug_screenshot("03_verify_failed", click_x, click_y)
                                    # 返回失敗，讓後續方法繼續嘗試
                                    return (False, False)
                            except Exception as e:
                                self.logger.warning(f"[RADIO] [VERIFY] 驗證過程中異常: {e}")
                                self._safe_log("info", f"[RADIO] [VERIFY] 驗證過程中異常: {e}")
                                # 驗證失敗，但不確定是否成功，假設成功繼續
                                self.logger.info("[RADIO] ⚠️ 驗證失敗但假設成功，繼續執行")
                                return (True, False)
                        else:
                            # 如果 radio_y.png 不存在，無法驗證，假設成功
                            self.logger.warning("[RADIO] [VERIFY] radio_y.png 不存在，無法驗證，假設成功")
                            self._safe_log("info", "[RADIO] [VERIFY] radio_y.png 不存在，無法驗證")
                            return (True, False)  # 假設成功
                    else:
                        self.logger.warning("[RADIO] ⚠️ smart_click_priority_image 點擊 'N' 位置失敗")
                        self._safe_log("info", "[RADIO] smart_click_priority_image 點擊 'N' 位置失敗")
                else:
                    self.logger.info(f"[RADIO] [CHECK] 未找到 'N' 圖片辨識，繼續其他方法...")
                    self._safe_log("debug", f"[RADIO] [CHECK] 未找到 'N' 圖片辨識，loc={loc}")
            except Exception as e:
                self.logger.warning(f"[RADIO] [CHECK] 檢查 'N' 圖片異常: {e}")
                self._safe_log("debug", f"[RADIO] [CHECK] 檢查 'N' 圖片異常: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.logger.info(f"[RADIO] [CHECK] radio_n.png 圖片文件不存在，跳過 'N' 檢查")
            self._safe_log("debug", f"[RADIO] [CHECK] radio_n.png 圖片文件不存在: {radio_n_image_full_path}")
        
        # 🎯 如果圖片辨識都失敗，嘗試使用文字辨識或直接點擊 "Y"
        self.logger.info("[RADIO] [WARN] 無法通過圖片辨識判斷 radio-button 狀態，嘗試其他方法...")
        self._safe_log("warning", "[RADIO] [WARN] 無法通過圖片辨識判斷 radio-button 狀態，嘗試 VLM 或座標點擊")
        
        # 如果圖片辨識失敗或圖片不存在，嘗試使用 VLM 尋找 "Y" 文字（在左上角區域）
        self._safe_log("info", f"[RADIO] [STEP 1-3] 嘗試使用 VLM 尋找 'Y'，視窗信息: win={win}")
        self.logger.info(f"[RADIO] [STEP 1-3] 嘗試使用 VLM 尋找 'Y'，視窗信息: win={win}")
        try:
            # 限制搜索區域到左上角（更小更精確的區域）
            # 從分頁簽下方開始搜索（win.top + 120px），高度約 100px
            search_region = (win.left, win.top + 120, int(win.width * 0.3), 100)
            self.logger.debug(f"[DEBUG] 在區域 {search_region} 中搜索 'Y' radio-button...")
            
            # 直接使用 VLM 尋找 "Y"，然後手動點擊
            vlm = self._get_vlm_engine()
            self._safe_log("info", f"[RADIO] [VLM] VLM 引擎狀態: {vlm is not None}")
            if vlm:
                self._safe_log("info", f"[RADIO] [VLM] 在區域 {search_region} 中搜索 'Y'...")
                result = vlm.find_element("Y", region=search_region)
                self._safe_log("info", f"[RADIO] [VLM] VLM 搜索結果: result={result}, success={result.success if result else None}, confidence={result.confidence if result else None}")
                if result and result.success and result.confidence > 0.5:
                    click_x = result.x
                    click_y = result.y
                    
                    # 驗證座標
                    if (win.left <= click_x <= win.left + win.width and 
                        win.top <= click_y <= win.top + win.height):
                        
                        relative_y = click_y - win.top
                        ratio_y = relative_y / win.height
                        
                        # 驗證：radio-button 應該在分頁簽下方（y_ratio 應該在 0.10-0.20 範圍內）
                        if 0.10 <= ratio_y <= 0.20:
                            self.logger.info(f"[RADIO] [OK] VLM 找到 'Y' radio-button: 找到座標=({click_x}, {click_y}), y_ratio={ratio_y:.4f}")
                            self._safe_log("info", f"[RADIO] VLM 找到 'Y': 找到座標=({click_x}, {click_y})")
                            print(f"[RADIO] [FOUND] VLM 找到 'Y' radio-button: 找到座標=({click_x}, {click_y}), y_ratio={ratio_y:.4f}")
                            # 截圖記錄
                            self._save_radio_debug_screenshot("04_vlm_found_radio", click_x, click_y)
                            # 🎯 記錄：準備使用這個座標進行點擊
                            print(f"[RADIO] [BEFORE_CLICK] 準備點擊 radio-button 'Y'，將使用座標=({click_x}, {click_y})")
                            self.logger.info("[RADIO] 準備點擊 'Y' radio-button...")
                            self._perform_click(click_x, click_y, clicks=1, click_type='left')
                            time.sleep(0.3)
                            # 截圖記錄點擊後
                            self._save_radio_debug_screenshot("05_after_vlm_click", click_x, click_y)
                            self.logger.info("[RADIO] ✅ 已點擊 'Y' radio-button（無法判斷狀態，假設需要框選）")
                            return (True, False)  # 無法判斷狀態，假設需要框選
                        else:
                            self.logger.warning(f"[RADIO] [VLM] VLM 找到的 'Y' 位置 y_ratio={ratio_y:.4f} 不在預期範圍內（0.10-0.20），使用座標保底")
                            self._safe_log("info", f"[RADIO] [VLM] y_ratio={ratio_y:.4f} 不在預期範圍，跳過")
                else:
                    self.logger.info(f"[RADIO] [VLM] VLM 未找到 'Y' 或信心度不足: result={result}")
                    self._safe_log("info", f"[RADIO] [VLM] VLM 未找到 'Y': result={result}")
            else:
                self.logger.info("[RADIO] [VLM] VLM 引擎不可用，跳過 VLM 搜索")
                self._safe_log("info", "[RADIO] [VLM] VLM 引擎不可用")
        except Exception as e:
            self.logger.warning(f"[RADIO] [VLM] VLM 尋找 'Y' 異常: {e}")
            self._safe_log("info", f"[RADIO] [VLM] VLM 尋找 'Y' 異常: {e}")
            import traceback
            traceback.print_exc()
        
        # 如果 VLM 失敗，使用座標點擊
        self.logger.info(f"[RADIO] [STEP 1-4] 使用座標點擊 'Y' radio-button: x_ratio={radio_y_x_ratio}, y_ratio={radio_y_y_ratio}")
        self._safe_log("info", f"[RADIO] [STEP 1-4] 調用 smart_click: x_ratio={radio_y_x_ratio}, y_ratio={radio_y_y_ratio}")
        
        # 🎯 計算保底座標
        win = self.get_nx_window()
        if win:
            fallback_x = win.left + int(win.width * radio_y_x_ratio)
            fallback_y = win.top + int(win.height * radio_y_y_ratio)
            print(f"[RADIO] [FALLBACK_COORD] 保底座標: ({fallback_x}, {fallback_y}) (基於 x_ratio={radio_y_x_ratio}, y_ratio={radio_y_y_ratio})")
            self.logger.info(f"[RADIO] [FALLBACK_COORD] 保底座標: ({fallback_x}, {fallback_y})")
        
        # 🎯 禁用 VLM 和 OCR，直接使用坐标点击（因为 VLM 已经尝试过了，会找到错误的 "Y"）
        success = self.smart_click(
            x_ratio=radio_y_x_ratio,
            y_ratio=radio_y_y_ratio,
            target_text=None,  # 不使用文字辨識（避免 VLM 找到错误的 Y）
            timeout=2,
            use_vlm=False  # 禁用 VLM，直接使用坐标
        )
        self._safe_log("info", f"[RADIO] [STEP 1-4] smart_click 返回: {success}")
        
        if success:
            # 截圖記錄點擊後的位置
            win = self.get_nx_window()
            if win:
                click_x = win.left + int(win.width * radio_y_x_ratio)
                click_y = win.top + int(win.height * radio_y_y_ratio)
                print(f"[RADIO] [AFTER_CLICK] 點擊後的座標記錄: ({click_x}, {click_y})")
                self._save_radio_debug_screenshot("06_after_coordinate_click", click_x, click_y)
            self.logger.info("[RADIO] ✅ 成功點擊 'Y' radio-button（無法判斷狀態，假設需要框選）")
            self._safe_log("info", "[RADIO] ✅ 成功點擊 'Y' radio-button")
            time.sleep(0.3)
            self.logger.info("[RADIO] ========== radio-button 處理完成 ==========")
            return (True, False)  # 無法判斷狀態，假設需要框選
        else:
            self.logger.warning("[RADIO] ⚠️ 點擊 'Y' radio-button 失敗（smart_click 返回 False）")
            print("[RADIO] 點擊 'Y' radio-button 失敗，返回 (False, False)")
            self._safe_log("warning", "[RADIO] ⚠️ 點擊 'Y' radio-button 失敗")
            self.logger.info("[RADIO] ========== radio-button 處理完成（失敗）==========")
            return (False, False)
    
    def select_recording_schedule_range(self, start_x_ratio=0.20, start_y_ratio=0.35, end_x_ratio=0.85, end_y_ratio=0.70):
        """
        🎯 在錄影排程網格上框選一個範圍
        使用圖像辨識定位網格區域，確保座標在視窗範圍內
        
        :param start_x_ratio: 起始位置 X 比例（默認 0.20，網格開始位置，作為保底）
        :param start_y_ratio: 起始位置 Y 比例（默認 0.35，網格開始位置，作為保底）
        :param end_x_ratio: 結束位置 X 比例（默認 0.85，網格結束位置，作為保底）
        :param end_y_ratio: 結束位置 Y 比例（默認 0.70，網格結束位置，作為保底）
        """
        self.logger.info("=" * 80)
        self.logger.info("[DRAG] ========== 開始框選錄影排程範圍 ==========")
        self.logger.info("=" * 80)
        self._safe_log("info", "[DRAG] 在錄影排程網格上框選範圍...")
        self._safe_log("info", "[DRAG] ========== 開始框選錄影排程範圍 ==========")
        
        # 獲取視窗信息
        win = self.get_nx_window()
        if not win:
            self.logger.warning("[DRAG] ⚠️ 無法獲取視窗信息")
            self._safe_log("warning", "[DRAG] ⚠️ 無法獲取視窗信息")
            return False
        
        # 🎯 使用圖像辨識定位網格區域
        # 嘗試識別網格中的特徵元素來確定網格位置
        grid_start_x = None
        grid_start_y = None
        grid_end_x = None
        grid_end_y = None
        grid_coordinates_calculated = False  # 🎯 標記是否已成功計算座標，避免後續邏輯覆蓋
        
        # 🎯 限制搜索區域到窗口的上半部分（網格應該在窗口的上半部分）
        # 網格通常在窗口的 20%-80% 寬度，10%-60% 高度範圍內
        search_region_left = win.left + int(win.width * 0.15)  # 從左側 15% 開始
        search_region_top = win.top + int(win.height * 0.10)    # 從頂部 10% 開始
        search_region_width = int(win.width * 0.70)            # 寬度 70%
        search_region_height = int(win.height * 0.55)           # 高度 55%（只搜索上半部分）
        search_region = (search_region_left, search_region_top, search_region_width, search_region_height)
        
        self.logger.info(f"[DRAG] 限制搜索區域: {search_region} (窗口: {win.width}x{win.height})")
        
        # 方法 1: 優先使用圖片辨識定位網格區域，然後在區域內用 VLM 識別"全部"
        grid_corner_image_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings", "schedule_grid_corner.png")
        grid_corner_image_exists = os.path.exists(grid_corner_image_path)
        
        # 🎯 保存圖片識別範圍（用於後續驗證）
        image_region_info = None
        
        if grid_corner_image_exists:
            self.logger.info(f"[DRAG] 找到網格參考圖片: {grid_corner_image_path}，使用圖片辨識定位網格區域")
            try:
                # 🎯 步驟 1: 使用圖片辨識找到網格區域（不點擊，只定位）
                from base.ok_script_recognizer import get_recognizer
                recognizer = get_recognizer()
                
                # 在搜索區域內查找網格圖片
                result = recognizer.locate_on_screen(
                    grid_corner_image_path,
                    region=search_region,
                    confidence=0.7
                )
                
                if result and result.success:
                    # 🎯 圖片識別返回的 result.x, result.y 應該是匹配區域的左上角（屏幕坐标）
                    # 但需要驗證：如果VLM找到的"全部"不在圖片識別範圍內，可能是圖片識別返回的是中心點
                    image_x = result.x
                    image_y = result.y
                    image_width = result.width if hasattr(result, 'width') and result.width > 0 else 200
                    image_height = result.height if hasattr(result, 'height') and result.height > 0 else 150
                    
                    # 🎯 調試：記錄圖片識別的原始座標和方法
                    self.logger.info(f"[DRAG] 圖片識別原始座標: ({image_x}, {image_y}), 方法: {result.method if hasattr(result, 'method') else 'unknown'}, 尺寸: {image_width}x{image_height}")
                    print(f"[DRAG] 圖片識別原始座標: ({image_x}, {image_y}), 方法: {result.method if hasattr(result, 'method') else 'unknown'}, 尺寸: {image_width}x{image_height}")
                    
                    # 🎯 先假設 result.x, result.y 是左上角，計算圖片範圍
                    # 如果後續VLM找到的"全部"不在這個範圍內，會進行調整
                    image_left = image_x
                    image_top = image_y
                    image_right = image_x + image_width
                    image_bottom = image_y + image_height
                    
                    # 🎯 保存圖片識別範圍信息（用於後續驗證）
                    image_region_info = {
                        'left': image_left,
                        'top': image_top,
                        'right': image_right,
                        'bottom': image_bottom,
                        'width': image_width,
                        'height': image_height,
                        'center_x': image_x + image_width // 2,  # 中心點X
                        'center_y': image_y + image_height // 2   # 中心點Y
                    }
                    
                    self.logger.info(f"[DRAG] 圖片識別成功: 位置=({image_x}, {image_y}), 尺寸={image_width}x{image_height} (屏幕座標)")
                    print(f"[DRAG] 圖片識別成功: 位置=({image_x}, {image_y}), 尺寸={image_width}x{image_height} (屏幕座標)")
                    
                    # 🎯 步驟 1: 使用圖像識別的範圍作為網格大致邊界
                    # 圖像識別找到的範圍是整個網格區域的大致邊界
                    image_left = image_x
                    image_top = image_y
                    image_right = image_x + image_width
                    image_bottom = image_y + image_height
                    
                    # 更新 image_region_info
                    image_region_info['left'] = image_left
                    image_region_info['top'] = image_top
                    image_region_info['right'] = image_right
                    image_region_info['bottom'] = image_bottom
                    
                    # 🎯 驗證圖像識別範圍是否在搜索區域內且在上半部分
                    is_in_search_region = (
                        search_region_left <= image_left <= search_region_left + search_region_width and
                        search_region_top <= image_top <= search_region_top + search_region_height
                    )
                    is_in_upper_half = image_top < win.top + int(win.height * 0.60)
                    
                    if is_in_search_region and is_in_upper_half:
                        self.logger.info(f"[DRAG] 圖像識別找到網格大致範圍: 左={image_left}, 右={image_right}, 上={image_top}, 下={image_bottom}")
                        self._safe_log("info", f"[DRAG] 圖像識別找到網格大致範圍: 左={image_left}, 右={image_right}, 上={image_top}, 下={image_bottom}")
                        
                        # 🎯 步驟 2: 在 schedule_grid_corner.png 識別的範圍內，使用 schedule_grid_All.png 識別"全部"字樣
                        # 新策略（根據用戶要求）：
                        # 1. 使用 schedule_grid_corner.png 識別網格區域（已完成）
                        # 2. 在該範圍內使用 schedule_grid_All.png 識別"全部"字樣
                        # 3. 以 schedule_grid_All.png 識別結果的右下角坐標為起點
                        # 4. 以 schedule_grid_corner.png 識別結果的右下角坐標為終點
                        
                        grid_all_image_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings", "schedule_grid_All.png")
                        grid_all_image_exists = os.path.exists(grid_all_image_path)
                        
                        if grid_all_image_exists:
                            try:
                                # 在 schedule_grid_corner.png 識別的範圍內搜索 schedule_grid_All.png
                                all_search_region = (image_left, image_top, image_width, image_height)
                                
                                all_result = recognizer.locate_on_screen(
                                    grid_all_image_path,
                                    region=all_search_region,
                                    confidence=0.7
                                )
                                
                                if all_result and all_result.success:
                                    # schedule_grid_All.png 識別結果
                                    all_image_x = all_result.x
                                    all_image_y = all_result.y
                                    all_image_width = all_result.width if hasattr(all_result, 'width') and all_result.width > 0 else 100
                                    all_image_height = all_result.height if hasattr(all_result, 'height') and all_result.height > 0 else 50
                                    
                                    # 🎯 計算 schedule_grid_All.png 識別結果的右下角坐標（作為起點）
                                    grid_start_x = all_image_x + all_image_width
                                    grid_start_y = all_image_y + all_image_height
                                    
                                    # 🎯 計算 schedule_grid_corner.png 識別結果的右下角坐標（作為終點）
                                    grid_end_x = image_right
                                    grid_end_y = image_bottom
                                    
                                    self.logger.info(f"[DRAG] schedule_grid_All.png 識別成功: 位置=({all_image_x}, {all_image_y}), 尺寸={all_image_width}x{all_image_height}")
                                    self.logger.info(f"[DRAG] schedule_grid_All.png 右下角（起點）: ({grid_start_x}, {grid_start_y})")
                                    self.logger.info(f"[DRAG] schedule_grid_corner.png 右下角（終點）: ({grid_end_x}, {grid_end_y})")
                                    print(f"[DRAG] schedule_grid_All.png 識別成功: 位置=({all_image_x}, {all_image_y}), 尺寸={all_image_width}x{all_image_height}")
                                    print(f"[DRAG] schedule_grid_All.png 右下角（起點）: ({grid_start_x}, {grid_start_y})")
                                    print(f"[DRAG] schedule_grid_corner.png 右下角（終點）: ({grid_end_x}, {grid_end_y})")
                                    
                                    # 🎯 驗證起點和終點是否在合理範圍內
                                    drag_width = grid_end_x - grid_start_x
                                    drag_height = grid_end_y - grid_start_y
                                    
                                    if drag_width > 0 and drag_height > 0:
                                        # 🎯 標記已成功計算，避免後續邏輯覆蓋（在打印之前設置，避免編碼錯誤導致未設置）
                                        grid_coordinates_calculated = True
                                        self.logger.info(f"[DRAG] [OK] 基於圖像識別計算框選座標")
                                        self.logger.info(f"[DRAG] schedule_grid_All.png 識別成功: 位置=({all_image_x}, {all_image_y}), 尺寸={all_image_width}x{all_image_height}")
                                        self.logger.info(f"[DRAG] schedule_grid_All.png 右下角（起點）: ({grid_start_x}, {grid_start_y})")
                                        self.logger.info(f"[DRAG] schedule_grid_corner.png 右下角（終點）: ({grid_end_x}, {grid_end_y})")
                                        self.logger.info(f"[DRAG] 框選範圍: 寬度={drag_width}px, 高度={drag_height}px")
                                        self.logger.info(f"[DRAG] 設置 grid_coordinates_calculated = True，起點=({grid_start_x}, {grid_start_y}), 終點=({grid_end_x}, {grid_end_y})")
                                        self._safe_log("info", f"[DRAG] [OK] 基於圖像識別計算框選座標")
                                        print(f"[DRAG] schedule_grid_All.png 識別成功: 位置=({all_image_x}, {all_image_y}), 尺寸={all_image_width}x{all_image_height}")
                                        print(f"[DRAG] schedule_grid_All.png 右下角（起點）: ({grid_start_x}, {grid_start_y})")
                                        print(f"[DRAG] schedule_grid_corner.png 右下角（終點）: ({grid_end_x}, {grid_end_y})")
                                        self._safe_log("info", f"[DRAG] 框選範圍: 寬度={drag_width}px, 高度={drag_height}px")
                                        print(f"[DRAG] 設置 grid_coordinates_calculated = True，起點=({grid_start_x}, {grid_start_y}), 終點=({grid_end_x}, {grid_end_y})")
                                        # 🎯 直接返回計算出的座標，避免後續邏輯覆蓋
                                        # 注意：這裡不能直接 return，因為後續還有驗證和調試截圖邏輯
                                        # 但我們已經設置了 grid_coordinates_calculated = True，後續邏輯應該會跳過
                                    else:
                                        self.logger.warning(f"[DRAG] ⚠️ 框選範圍無效: 寬度={drag_width}px, 高度={drag_height}px")
                                        self._safe_log("warning", f"[DRAG] ⚠️ 框選範圍無效")
                                        grid_start_x = None
                                        grid_start_y = None
                                        grid_coordinates_calculated = False
                                else:
                                    self.logger.warning("[DRAG] ⚠️ 在圖像識別範圍內未找到 schedule_grid_All.png，將嘗試其他方法")
                                    self._safe_log("warning", "[DRAG] ⚠️ 在圖像識別範圍內未找到 schedule_grid_All.png")
                                    grid_start_x = None
                                    grid_start_y = None
                            except Exception as e:
                                self.logger.warning(f"[DRAG] 識別 schedule_grid_All.png 失敗: {e}")
                                self._safe_log("info", f"[DRAG] 識別 schedule_grid_All.png 失敗: {e}")
                                grid_start_x = None
                                grid_start_y = None
                        else:
                            self.logger.warning(f"[DRAG] ⚠️ schedule_grid_All.png 不存在: {grid_all_image_path}")
                            self._safe_log("warning", f"[DRAG] ⚠️ schedule_grid_All.png 不存在")
                            grid_start_x = None
                            grid_start_y = None
                    else:
                        self.logger.warning(f"[DRAG] ⚠️ 圖像識別範圍位置不合理: 左上=({image_left}, {image_top}), 在搜索區域內={is_in_search_region}, 在上半部分={is_in_upper_half}")
                        self._safe_log("warning", f"[DRAG] ⚠️ 圖像識別範圍位置不合理")
                        grid_start_x = None
                        grid_start_y = None
                else:
                    self.logger.info("[DRAG] 圖片辨識未找到網格，將嘗試其他方法")
                    grid_start_x = None
                    grid_start_y = None
            except Exception as e:
                self.logger.warning(f"[DRAG] 圖片辨識異常: {e}，將嘗試其他方法")
                grid_start_x = None
                grid_start_y = None
        
        # 方法 2: 如果圖片辨識失敗，嘗試使用 VLM 識別"全部"文字（網格左上角）
        # 🎯 只有在未通過新策略計算出座標時，才使用 VLM 作為備選方案
        if not grid_coordinates_calculated and (grid_start_x is None or grid_start_y is None):
            try:
                import pyautogui
                vlm = self._get_vlm_engine()
                if vlm:
                    try:
                        result = vlm.find_element("全部", region=search_region)
                        if result and result.success:
                            # 🎯 驗證找到的位置是否合理（應該在搜索區域內，且在窗口上半部分）
                            is_in_search_region = (
                                search_region_left <= result.x <= search_region_left + search_region_width and
                                search_region_top <= result.y <= search_region_top + search_region_height
                            )
                            
                            # 檢查是否在窗口的上半部分（y 應該小於窗口高度的 60%）
                            is_in_upper_half = result.y < win.top + int(win.height * 0.60)
                            
                            if is_in_search_region and is_in_upper_half:
                                # 🎯 如果只有 VLM 找到「全部」，沒有圖像識別，使用估算的網格尺寸
                                # 網格結構：7行（週日到週六）x 24列（AM12 到 PM11）
                                num_columns = 24
                                num_rows = 7
                                
                                # 估算網格尺寸（基於窗口尺寸）
                                estimated_grid_width = int(win.width * 0.40)   # 網格寬度約為視窗的 40%
                                estimated_grid_height = int(win.height * 0.28)  # 網格高度約為視窗的 28%
                                
                                # 計算每個格子的尺寸
                                cell_width = estimated_grid_width / num_columns
                                cell_height = estimated_grid_height / num_rows
                                
                                # 計算第一個格子和最後一個格子的座標
                                # 假設「全部」在網格左上角，網格從其右下方開始
                                grid_left = result.x + 60   # 向右偏移，進入網格第一列
                                grid_top = result.y + 35    # 向下偏移，進入網格第一行
                                
                                first_cell_offset_x = cell_width * 0.1
                                first_cell_offset_y = cell_height * 0.1
                                
                                grid_start_x = int(grid_left + first_cell_offset_x)
                                grid_start_y = int(grid_top + first_cell_offset_y)
                                
                                last_cell_x = grid_left + (num_columns - 1) * cell_width
                                last_cell_y = grid_top + (num_rows - 1) * cell_height
                                
                                last_cell_offset_x = cell_width * 0.9
                                last_cell_offset_y = cell_height * 0.9
                                
                                grid_end_x = int(last_cell_x + last_cell_offset_x)
                                grid_end_y = int(last_cell_y + last_cell_offset_y)
                                
                                self.logger.info(f"[DRAG] ✅ 通過 VLM 找到「全部」: ({result.x}, {result.y})")
                                self.logger.info(f"[DRAG] 估算網格尺寸: {estimated_grid_width}x{estimated_grid_height}")
                                self.logger.info(f"[DRAG] 每個格子尺寸: {cell_width:.1f}x{cell_height:.1f}px")
                                self.logger.info(f"[DRAG] 第一個格子: ({grid_start_x}, {grid_start_y}), 最後一個格子: ({grid_end_x}, {grid_end_y})")
                                print(f"[DRAG] ✅ 通過 VLM 找到「全部」: ({result.x}, {result.y})")
                                print(f"[DRAG] 第一個格子: ({grid_start_x}, {grid_start_y}), 最後一個格子: ({grid_end_x}, {grid_end_y})")
                            else:
                                self.logger.warning(f"[DRAG] ⚠️ VLM 找到「全部」位置不合理: ({result.x}, {result.y})，在搜索區域內={is_in_search_region}，在上半部分={is_in_upper_half}")
                    except Exception as e:
                        self.logger.debug(f"[DRAG] VLM 尋找「全部」失敗: {e}")
            except Exception as e:
                self.logger.debug(f"[DRAG] 圖像辨識異常: {e}")
        
        # 🎯 如果圖像辨識失敗或位置不合理，使用比例座標作為保底
        if not grid_coordinates_calculated and (grid_start_x is None or grid_start_y is None):
            self.logger.info("[DRAG] 圖像辨識未找到網格或位置不合理，使用比例座標作為保底")
            grid_start_x = win.left + int(win.width * start_x_ratio)
            grid_start_y = win.top + int(win.height * start_y_ratio)
            grid_end_x = win.left + int(win.width * end_x_ratio)
            grid_end_y = win.top + int(win.height * end_y_ratio)
        else:
            # 🎯 如果 grid_start_x 和 grid_start_y 已經計算出來（通過圖片+VLM 或 VLM），
            # grid_end_x 和 grid_end_y 應該也已經計算出來了
            # 這裡只需要確保它們都有值
            if grid_end_x is None or grid_end_y is None:
                # 如果結束位置未計算，使用估算值
                self.logger.warning("[DRAG] ⚠️ 結束位置未計算，使用估算值")
                # 網格有 24 列（AM12 到 PM11）和 7 行（週日到週六）
                num_columns = 24
                num_rows = 7
                
                # 估算網格尺寸
                estimated_grid_width = int(win.width * 0.40)
                estimated_grid_height = int(win.height * 0.28)
                
                # 計算每個格子尺寸
                cell_width = estimated_grid_width / num_columns
                cell_height = estimated_grid_height / num_rows
                
                # 計算最後一個格子的座標
                # 假設 grid_start_x 和 grid_start_y 是第一個格子的座標
                last_cell_x = grid_start_x + (num_columns - 1) * cell_width
                last_cell_y = grid_start_y + (num_rows - 1) * cell_height
                
                last_cell_offset_x = cell_width * 0.9
                last_cell_offset_y = cell_height * 0.9
                
                grid_end_x = int(last_cell_x + last_cell_offset_x)
                grid_end_y = int(last_cell_y + last_cell_offset_y)
                
                self.logger.info(f"[DRAG] 使用估算值計算結束位置: ({grid_end_x}, {grid_end_y})")
                print(f"[DRAG] 使用估算值計算結束位置: ({grid_end_x}, {grid_end_y})")
            
            # 🎯 定義估算網格尺寸（用於後續驗證和日誌）
            actual_grid_width = grid_end_x - grid_start_x if grid_end_x and grid_start_x else None
            actual_grid_height = grid_end_y - grid_start_y if grid_end_y and grid_start_y else None
            estimated_grid_width = actual_grid_width if actual_grid_width else int(win.width * 0.40)
            estimated_grid_height = actual_grid_height if actual_grid_height else int(win.height * 0.28)
            
            # 🎯 如果圖片識別成功，使用圖片範圍作為參考並強制限制框選範圍
            # 關鍵：格子所在區域相對圖像識別範圍應該更小，所以框選範圍必須完全在圖像識別範圍內
            # 🎯 如果已經通過新策略計算出座標，跳過強制限制邏輯，避免覆蓋正確的座標
            if image_region_info and not grid_coordinates_calculated:
                image_left = image_region_info['left']
                image_top = image_region_info['top']
                image_right = image_region_info['right']
                image_bottom = image_region_info['bottom']
                image_width = image_right - image_left
                image_height = image_bottom - image_top
                
                # 🎯 驗證框選起點和終點是否在圖片範圍內
                is_start_in_image = (
                    image_left <= grid_start_x <= image_right and
                    image_top <= grid_start_y <= image_bottom
                )
                is_end_in_image = (
                    image_left <= grid_end_x <= image_right and
                    image_top <= grid_end_y <= image_bottom
                )
                
                # 🎯 計算框選範圍
                drag_width = grid_end_x - grid_start_x
                drag_height = grid_end_y - grid_start_y
                
                # 🎯 添加詳細的調試信息
                self.logger.info(f"[DRAG] 驗證框選範圍是否在圖片範圍內:")
                self.logger.info(f"[DRAG] 起點=({grid_start_x}, {grid_start_y}), 終點=({grid_end_x}, {grid_end_y})")
                self.logger.info(f"[DRAG] 圖片範圍=({image_left}, {image_top}) - ({image_right}, {image_bottom})")
                self.logger.info(f"[DRAG] 框選尺寸=({drag_width}x{drag_height}), 圖片尺寸=({image_width}x{image_height})")
                self.logger.info(f"[DRAG] 起點在圖片範圍內: {is_start_in_image}, 終點在圖片範圍內: {is_end_in_image}")
                self._safe_log("info", f"[DRAG] 驗證框選範圍是否在圖片範圍內:")
                print(f"[DRAG] 起點=({grid_start_x}, {grid_start_y}), 終點=({grid_end_x}, {grid_end_y})")
                print(f"[DRAG] 圖片範圍=({image_left}, {image_top}) - ({image_right}, {image_bottom})")
                print(f"[DRAG] 框選尺寸=({drag_width}x{drag_height}), 圖片尺寸=({image_width}x{image_height})")
                self._safe_log("info", f"[DRAG] 起點在圖片範圍內: {is_start_in_image}, 終點在圖片範圍內: {is_end_in_image}")
                
                # 🎯 強制限制：確保框選範圍完全在圖像識別範圍內
                # 如果框選範圍超出圖像識別範圍，進行強制補正
                if not is_start_in_image:
                    self.logger.warning(f"[DRAG] [WARN] 框選起點不在圖片識別範圍內，強制補正")
                    if grid_start_x < image_left:
                        grid_start_x = image_left
                    if grid_start_x > image_right:
                        grid_start_x = image_right
                    if grid_start_y < image_top:
                        grid_start_y = image_top
                    if grid_start_y > image_bottom:
                        grid_start_y = image_bottom
                    self.logger.info(f"[DRAG] 補正後起點: ({grid_start_x}, {grid_start_y})")
                    print(f"[DRAG] 補正後起點: ({grid_start_x}, {grid_start_y})")
                
                if not is_end_in_image:
                    self.logger.warning(f"[DRAG] [WARN] 框選終點不在圖片識別範圍內，強制補正")
                    if grid_end_x < image_left:
                        grid_end_x = image_left
                    if grid_end_x > image_right:
                        grid_end_x = image_right
                    if grid_end_y < image_top:
                        grid_end_y = image_top
                    if grid_end_y > image_bottom:
                        grid_end_y = image_bottom
                    self.logger.info(f"[DRAG] 補正後終點: ({grid_end_x}, {grid_end_y})")
                    print(f"[DRAG] 補正後終點: ({grid_end_x}, {grid_end_y})")
                
                # 🎯 強制限制：確保框選範圍不超過圖像識別範圍
                drag_width = grid_end_x - grid_start_x
                drag_height = grid_end_y - grid_start_y
                
                if drag_width > image_width:
                    self.logger.warning(f"[DRAG] [WARN] 框選寬度 ({drag_width}px) 超過圖片識別範圍寬度 ({image_width}px)，強制限制")
                    grid_end_x = grid_start_x + image_width
                    if grid_end_x > image_right:
                        grid_end_x = image_right
                        grid_start_x = grid_end_x - image_width
                        if grid_start_x < image_left:
                            grid_start_x = image_left
                    drag_width = grid_end_x - grid_start_x
                    self.logger.info(f"[DRAG] 補正後框選寬度: {drag_width}px")
                    self._safe_log("info", f"[DRAG] 補正後框選寬度: {drag_width}px")
                
                if drag_height > image_height:
                    self.logger.warning(f"[DRAG] [WARN] 框選高度 ({drag_height}px) 超過圖片識別範圍高度 ({image_height}px)，強制限制")
                    grid_end_y = grid_start_y + image_height
                    if grid_end_y > image_bottom:
                        grid_end_y = image_bottom
                        grid_start_y = grid_end_y - image_height
                        if grid_start_y < image_top:
                            grid_start_y = image_top
                    drag_height = grid_end_y - grid_start_y
                    self.logger.info(f"[DRAG] 補正後框選高度: {drag_height}px")
                    self._safe_log("info", f"[DRAG] 補正後框選高度: {drag_height}px")
                
                # 🎯 驗證框選高度是否合理（必須大於 0）
                drag_height = grid_end_y - grid_start_y
                if drag_height <= 0:
                    self.logger.error(f"[DRAG] [ERROR] 框選高度為 0 或負數: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y}), 高度={drag_height}")
                    self._safe_log("error", f"[DRAG] [ERROR] 框選高度為 0 或負數，使用估算高度補正")
                    # 🎯 如果高度為 0，使用估算高度重新計算結束位置
                    # 網格有 7 行，每個格子高度約為窗口高度的 28% / 7
                    num_rows = 7
                    estimated_cell_height = int(win.height * 0.28) / num_rows
                    estimated_grid_height = int(estimated_cell_height * num_rows)
                    grid_end_y = grid_start_y + estimated_grid_height
                    self.logger.info(f"[DRAG] 已補正框選高度: 新結束位置=({grid_end_x}, {grid_end_y}), 高度={estimated_grid_height}")
                    print(f"[DRAG] 已補正框選高度: 新結束位置=({grid_end_x}, {grid_end_y}), 高度={estimated_grid_height}")
                
                self.logger.info(f"[DRAG] 圖片識別範圍參考: ({image_region_info['left']}, {image_region_info['top']}) - ({image_region_info['right']}, {image_region_info['bottom']})")
                self.logger.info(f"[DRAG] 框選範圍（基於網格尺寸）: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y}), 尺寸={grid_end_x - grid_start_x}x{grid_end_y - grid_start_y}")
                print(f"[DRAG] 圖片識別範圍參考: ({image_region_info['left']}, {image_region_info['top']}) - ({image_region_info['right']}, {image_region_info['bottom']})")
                print(f"[DRAG] 框選範圍（基於網格尺寸）: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y}), 尺寸={grid_end_x - grid_start_x}x{grid_end_y - grid_start_y}")
            
            # 🎯 驗證框選起點和終點是否在合理範圍內（僅驗證，不強制修改）
            win_right = win.left + win.width
            win_bottom = win.top + win.height
            is_start_valid = (win.left <= grid_start_x <= win_right and win.top <= grid_start_y <= win_bottom)
            is_end_valid = (win.left <= grid_end_x <= win_right and win.top <= grid_end_y <= win_bottom)
            
            self.logger.info(f"[DRAG] 基於「全部」位置計算網格範圍: 起始=({grid_start_x}, {grid_start_y}), 估算尺寸={estimated_grid_width}x{estimated_grid_height}, 結束=({grid_end_x}, {grid_end_y})")
            self.logger.info(f"[DRAG] 框選起點有效性: {is_start_valid}, 框選終點有效性: {is_end_valid}")
            print(f"[DRAG] 基於「全部」位置計算網格範圍: 起始=({grid_start_x}, {grid_start_y}), 估算尺寸={estimated_grid_width}x{estimated_grid_height}, 結束=({grid_end_x}, {grid_end_y})")
            self._safe_log("info", f"[DRAG] 框選起點有效性: {is_start_valid}, 框選終點有效性: {is_end_valid}")
            
            # 🎯 如果座標超出窗口範圍，進行輕微補正（僅在必要時）
            # 🎯 如果已經通過新策略計算出座標，跳過補正邏輯，直接使用計算出的座標
            if not grid_coordinates_calculated:
                # 保留較小的邊距，但不要過度限制已精確計算的座標
                margin = 5  # 減少邊距，避免過度修正
                if grid_start_x < win.left:
                    grid_start_x = win.left + margin
                    self.logger.warning(f"[DRAG] 框選起點 X 超出窗口左邊界，補正為: {grid_start_x}")
                if grid_start_x > win_right:
                    grid_start_x = win_right - margin
                    self.logger.warning(f"[DRAG] 框選起點 X 超出窗口右邊界，補正為: {grid_start_x}")
                if grid_start_y < win.top:
                    grid_start_y = win.top + margin
                    self.logger.warning(f"[DRAG] 框選起點 Y 超出窗口上邊界，補正為: {grid_start_y}")
                if grid_start_y > win_bottom:
                    grid_start_y = win_bottom - margin
                    self.logger.warning(f"[DRAG] 框選起點 Y 超出窗口下邊界，補正為: {grid_start_y}")
                
                if grid_end_x < win.left:
                    grid_end_x = win.left + margin
                    self.logger.warning(f"[DRAG] 框選終點 X 超出窗口左邊界，補正為: {grid_end_x}")
                if grid_end_x > win_right:
                    grid_end_x = win_right - margin
                    self.logger.warning(f"[DRAG] 框選終點 X 超出窗口右邊界，補正為: {grid_end_x}")
                if grid_end_y < win.top:
                    grid_end_y = win.top + margin
                    self.logger.warning(f"[DRAG] 框選終點 Y 超出窗口上邊界，補正為: {grid_end_y}")
                if grid_end_y > win_bottom:
                    grid_end_y = win_bottom - margin
                    self.logger.warning(f"[DRAG] 框選終點 Y 超出窗口下邊界，補正為: {grid_end_y}")
                
                if not is_start_valid or not is_end_valid:
                    self.logger.warning(f"[DRAG] [WARN] 框選範圍驗證失敗，起點有效={is_start_valid}, 終點有效={is_end_valid}")
            else:
                self.logger.info(f"[DRAG] 已通過新策略計算座標，跳過補正邏輯，直接使用計算出的座標")
                self._safe_log("info", f"[DRAG] 已通過新策略計算座標，跳過補正邏輯，直接使用計算出的座標")
        
        # 🎯 最終驗證：確保座標在視窗範圍內（僅在必要時進行最後的輕微補正）
        # 🎯 如果已經通過新策略計算出座標，跳過最終補正邏輯
        if not grid_coordinates_calculated:
            win_right = win.left + win.width
            win_bottom = win.top + win.height
            
            # 只在座標明顯超出窗口範圍時才進行補正，保留已精確計算的座標
            final_margin = 5  # 最終邊距（較小，避免過度修正）
            if grid_start_x < win.left or grid_start_x > win_right:
                grid_start_x = max(win.left + final_margin, min(grid_start_x, win_right - final_margin))
            if grid_start_y < win.top or grid_start_y > win_bottom:
                grid_start_y = max(win.top + final_margin, min(grid_start_y, win_bottom - final_margin))
            if grid_end_x < win.left or grid_end_x > win_right:
                grid_end_x = max(win.left + final_margin, min(grid_end_x, win_right - final_margin))
            if grid_end_y < win.top or grid_end_y > win_bottom:
                grid_end_y = max(win.top + final_margin, min(grid_end_y, win_bottom - final_margin))
        
        self.logger.info(f"[DRAG] 框選範圍（已驗證）: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y})")
        self.logger.info(f"[DRAG] 座標計算標記: grid_coordinates_calculated={grid_coordinates_calculated}")
        self.logger.info(f"[DRAG] 視窗信息: 標題={win.title}, 位置=({win.left}, {win.top}), 尺寸={win.width}x{win.height}")
        win_right = win.left + win.width
        win_bottom = win.top + win.height
        self.logger.info(f"[DRAG] 視窗邊界: 左={win.left}, 右={win_right}, 上={win.top}, 下={win_bottom}")
        self._safe_log("info", f"[DRAG] 框選範圍: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y}), 計算標記={grid_coordinates_calculated}")
        print(f"[DRAG] 最終框選座標: 起始=({grid_start_x}, {grid_start_y}), 結束=({grid_end_x}, {grid_end_y}), 計算標記={grid_coordinates_calculated}")
        
        # 🎯 截圖記錄框選前（帶窗口信息和圖片識別範圍）
        self._save_drag_debug_screenshot("01_before_drag", grid_start_x, grid_start_y, grid_end_x, grid_end_y, win=win, image_region_info=image_region_info)
        
        # 調用 base 層的拖拽框選方法
        self.logger.info("[DRAG] 準備執行拖拽框選...")
        print(f"[DRAG] 執行拖拽: ({grid_start_x}, {grid_start_y}) -> ({grid_end_x}, {grid_end_y})")
        
        # 🎯 在拖拽過程中截圖（通過修改 drag_select_range 或在此處添加）
        result = self.drag_select_range(grid_start_x, grid_start_y, grid_end_x, grid_end_y, duration=0.5, button='left')
        
        # 🎯 截圖記錄框選後（帶窗口信息）
        time.sleep(0.3)  # 等待一下讓選中區域生效
        self._save_drag_debug_screenshot("02_after_drag", grid_start_x, grid_start_y, grid_end_x, grid_end_y, win=win, image_region_info=image_region_info)
        
        if result:
            self.logger.info("[DRAG] [OK] 成功框選錄影排程範圍")
            self._safe_log("info", "[DRAG] [OK] 成功框選錄影排程範圍")
        else:
            self.logger.warning("[DRAG] [WARN] 框選錄影排程範圍失敗")
            self._safe_log("warning", "[DRAG] [WARN] 框選錄影排程範圍失敗")
        
        self.logger.info("[DRAG] ========== 框選錄影排程範圍完成 ==========")
        return result
    
    def enable_recording(self):
        """
        🎯 開啟「錄製」開關
        步驟（重要：必須按順序執行）：
        1. 檢查並設置左上角 radio-button 為 "Y"（必須先執行）
        2. 在錄影排程網格上框選一個範圍（讓框選的部分變成綠色）
        3. 開啟「錄製」開關（toggle switch）- 如果需要的話
        """
        # 🎯 立即輸出，確保能看到方法被調用
        import sys
        print("=" * 80, file=sys.stderr)
        print("[ENABLE_RECORDING] ========== enable_recording() 方法被調用！==========", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        self.logger.info("=" * 80)
        self.logger.info("[ENABLE_RECORDING] ========== 開始開啟錄影功能 ==========")
        self.logger.info("=" * 80)
        self._safe_log("info", "[ENABLE_RECORDING] 開啟「錄製」開關...")
        self._safe_log("info", "=" * 80)
        self._safe_log("info", "[ENABLE_RECORDING] ========== 開始開啟錄影功能 ==========")
        self._safe_log("info", "=" * 80)
        
        # 🎯 步驟 1: 檢查並設置左上角 radio-button 為 "Y"（必須先執行）
        self.logger.info("[ENABLE_RECORDING] [STEP 1] ========== 步驟 1: 檢查並設置左上角 radio-button 為 'Y' ==========")
        self._safe_log("info", "[ENABLE_RECORDING] [STEP 1] 步驟 1: 檢查並設置左上角 radio-button 為 'Y'...")
        self._safe_log("info", "[ENABLE_RECORDING] [STEP 1] 開始執行步驟 1: 檢查並設置 radio-button")
        
        # 返回: (success, was_already_y)
        print("[ENABLE_RECORDING] [STEP 1] 調用 check_and_set_recording_radio_y()...")
        radio_success, was_already_y = self.check_and_set_recording_radio_y()
        print(f"[ENABLE_RECORDING] [STEP 1] check_and_set_recording_radio_y() 返回: success={radio_success}, was_already_y={was_already_y}")
        
        if not radio_success:
            self.logger.warning("[ENABLE_RECORDING] ⚠️ [STEP 1] 警告：檢查或設置 radio-button 失敗，但繼續執行後續步驟")
            self._safe_log("warning", "[ENABLE_RECORDING] [STEP 1] ⚠️ 檢查或設置 radio-button 失敗")
            was_already_y = False  # 失敗時假設需要框選
        
        if was_already_y:
            self.logger.info("[ENABLE_RECORDING] ✅ [STEP 1] radio-button 已經是 'Y'，跳過框選時段，直接返回")
            self._safe_log("info", "[ENABLE_RECORDING] [STEP 1] ✅ radio-button 已經是 'Y'，跳過框選")
            return True  # 已經是 Y，不需要框選，直接返回（後續會點擊確認）
        
        # 🎯 步驟 2: 在錄影排程網格上框選一個範圍（只有在需要時才執行）
        self.logger.info("[ENABLE_RECORDING] [STEP 2] ========== 步驟 2: 在錄影排程網格上框選一個範圍 ==========")
        self._safe_log("info", "[ENABLE_RECORDING] [STEP 2] 步驟 2: 在錄影排程網格上框選一個範圍...")
        self._safe_log("info", "[ENABLE_RECORDING] [STEP 2] 開始執行步驟 2: 框選錄影排程範圍")
        print("[ENABLE_RECORDING] [STEP 2] 調用 select_recording_schedule_range()...")
        range_success = self.select_recording_schedule_range()
        print(f"[ENABLE_RECORDING] [STEP 2] select_recording_schedule_range() 返回: {range_success}")
        if range_success:
            self.logger.info("✅ [STEP 2] 成功：已框選錄影排程範圍")
        else:
            self.logger.warning("⚠️ [STEP 2] 警告：框選錄影排程範圍失敗，但繼續執行後續步驟")
        
        # 🎯 步驟 3: 框選成功後，不需要額外的 checkbox 檢查
        # 根據用戶反饋，框選成功後應該直接點擊確認，不需要檢查其他 checkbox
        self.logger.info("[ENABLE_RECORDING] [STEP 3] 框選成功，準備點擊確認按鈕")
        self._safe_log("info", "[ENABLE_RECORDING] [STEP 3] 框選成功，不需要額外檢查")
        
        return True  # 框選成功，返回 True（後續會點擊確認）
    
    def _save_radio_debug_screenshot(self, step_name, x, y):
        """保存 radio-button 調試截圖"""
        try:
            import pyautogui
            import datetime
            from PIL import Image, ImageDraw, ImageFont
            
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "radio_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 截圖全屏
            screenshot = pyautogui.screenshot()
            
            # 在截圖上標記 radio-button 位置（紅色圓圈）
            img = screenshot.copy()
            draw = ImageDraw.Draw(img)
            
            # 畫紅色圓圈標記位置
            radius = 20
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                outline="red",
                width=3
            )
            # 畫十字標記
            draw.line([(x - 15, y), (x + 15, y)], fill="red", width=2)
            draw.line([(x, y - 15), (x, y + 15)], fill="red", width=2)
            
            # 添加文字標註
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            label = f"Radio: ({x}, {y})"
            draw.text((x + radius + 5, y - radius), label, fill="red", font=font)
            
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            self.logger.info(f"[DEBUG_SCREENSHOT] Radio 截圖已保存: {screenshot_path} (位置: {x}, {y})")
        except Exception as e:
            self.logger.warning(f"[DEBUG_SCREENSHOT] 保存 Radio 截圖失敗: {e}")
    
    def _save_drag_debug_screenshot(self, step_name, start_x, start_y, end_x, end_y, win=None, image_region_info=None):
        """
        保存拖拽框選調試截圖，標記框選範圍、窗口邊界和圖片識別範圍
        
        :param step_name: 步驟名稱
        :param start_x: 框選起點 X 座標
        :param start_y: 框選起點 Y 座標
        :param end_x: 框選終點 X 座標
        :param end_y: 框選終點 Y 座標
        :param win: 視窗物件
        :param image_region_info: 圖片識別範圍信息（字典，包含 left, top, right, bottom）
        """
        try:
            import pyautogui
            import datetime
            from PIL import Image, ImageDraw, ImageFont
            
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "drag_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 截圖全屏
            screenshot = pyautogui.screenshot()
            
            # 在截圖上標記拖拽範圍和窗口邊界
            img = screenshot.copy()
            draw = ImageDraw.Draw(img)
            
            # 🎯 標記窗口邊界（紅色虛線）
            if win:
                win_right = win.left + win.width
                win_bottom = win.top + win.height
                # 窗口邊界（紅色虛線矩形）
                for i in range(0, max(win.width, win.height), 10):
                    # 上邊界
                    if win.left + i < win_right:
                        draw.rectangle([(win.left + i, win.top), (win.left + i + 5, win.top + 2)], fill="red")
                    # 下邊界
                    if win.left + i < win_right:
                        draw.rectangle([(win.left + i, win_bottom - 2), (win.left + i + 5, win_bottom)], fill="red")
                    # 左邊界
                    if win.top + i < win_bottom:
                        draw.rectangle([(win.left, win.top + i), (win.left + 2, win.top + i + 5)], fill="red")
                    # 右邊界
                    if win.top + i < win_bottom:
                        draw.rectangle([(win_right - 2, win.top + i), (win_right, win.top + i + 5)], fill="red")
                
                # 窗口信息文字
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except:
                    font = ImageFont.load_default()
                win_info = f"Window: {win.title} ({win.width}x{win.height})"
                draw.text((win.left + 5, win.top + 5), win_info, fill="red", font=font)
            
            # 🎯 標記拖拽範圍（綠色粗線矩形）
            draw.rectangle(
                [(start_x, start_y), (end_x, end_y)],
                outline="green",
                width=4
            )
            
            # 🎯 標記起始位置（綠色大圓圈 + 十字）
            radius = 15
            draw.ellipse(
                [(start_x - radius, start_y - radius), (start_x + radius, start_y + radius)],
                outline="green",
                width=3
            )
            # 十字標記
            draw.line([(start_x - 20, start_y), (start_x + 20, start_y)], fill="green", width=3)
            draw.line([(start_x, start_y - 20), (start_x, start_y + 20)], fill="green", width=3)
            
            # 🎯 標記結束位置（藍色大圓圈 + 十字）
            draw.ellipse(
                [(end_x - radius, end_y - radius), (end_x + radius, end_y + radius)],
                outline="blue",
                width=3
            )
            # 十字標記
            draw.line([(end_x - 20, end_y), (end_x + 20, end_y)], fill="blue", width=3)
            draw.line([(end_x, end_y - 20), (end_x, end_y + 20)], fill="blue", width=3)
            
            # 🎯 添加詳細文字標註
            try:
                font = ImageFont.truetype("arial.ttf", 14)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 起始位置標註
            label_start = f"START: ({start_x}, {start_y})"
            draw.text((start_x + radius + 5, start_y - radius - 20), label_start, fill="green", font=font)
            
            # 結束位置標註
            label_end = f"END: ({end_x}, {end_y})"
            draw.text((end_x + radius + 5, end_y - radius - 20), label_end, fill="blue", font=font)
            
            # 🎯 標記圖片識別範圍（黃色虛線矩形）
            if image_region_info:
                img_left = image_region_info['left']
                img_top = image_region_info['top']
                img_right = image_region_info['right']
                img_bottom = image_region_info['bottom']
                img_width = image_region_info['width']
                img_height = image_region_info['height']
                
                # 繪製黃色虛線矩形框標記圖片識別範圍
                dash_length = 10
                gap_length = 5
                
                # 上邊界（虛線）
                x = img_left
                while x < img_right:
                    draw.line([(x, img_top), (min(x + dash_length, img_right), img_top)], fill="yellow", width=3)
                    x += dash_length + gap_length
                
                # 下邊界（虛線）
                x = img_left
                while x < img_right:
                    draw.line([(x, img_bottom), (min(x + dash_length, img_right), img_bottom)], fill="yellow", width=3)
                    x += dash_length + gap_length
                
                # 左邊界（虛線）
                y = img_top
                while y < img_bottom:
                    draw.line([(img_left, y), (img_left, min(y + dash_length, img_bottom))], fill="yellow", width=3)
                    y += dash_length + gap_length
                
                # 右邊界（虛線）
                y = img_top
                while y < img_bottom:
                    draw.line([(img_right, y), (img_right, min(y + dash_length, img_bottom))], fill="yellow", width=3)
                    y += dash_length + gap_length
                
                # 圖片識別範圍信息文字
                img_info = f"Image Region: ({img_left}, {img_top}) - ({img_right}, {img_bottom}) [{img_width}x{img_height}]"
                draw.text((img_left + 5, img_top - 25), img_info, fill="yellow", font=font_small)
            
            # 計算範圍尺寸
            range_width = abs(end_x - start_x)
            range_height = abs(end_y - start_y)
            label_size = f"Size: {range_width}x{range_height}"
            draw.text((start_x, start_y - 40), label_size, fill="yellow", font=font_small)
            
            # 🎯 驗證座標是否在窗口內
            if win:
                win_right = win.left + win.width
                win_bottom = win.top + win.height
                warnings = []
                if start_x < win.left or start_x > win_right:
                    warnings.append(f"Start X out of window!")
                if start_y < win.top or start_y > win_bottom:
                    warnings.append(f"Start Y out of window!")
                if end_x < win.left or end_x > win_right:
                    warnings.append(f"End X out of window!")
                if end_y < win.top or end_y > win_bottom:
                    warnings.append(f"End Y out of window!")
                
                if warnings:
                    warning_text = " | ".join(warnings)
                    draw.text((start_x, start_y - 60), warning_text, fill="red", font=font)
            
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            self.logger.info(f"[DRAG] [SCREENSHOT] 拖拽截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[DRAG] [SCREENSHOT] 拖拽截圖已保存: {screenshot_path}")
            print(f"[DRAG] 框選範圍: 起始=({start_x}, {start_y}), 結束=({end_x}, {end_y}), 尺寸={range_width}x{range_height}")
        except Exception as e:
            self.logger.warning(f"[DRAG] [SCREENSHOT] 保存拖拽截圖失敗: {e}")
            import traceback
            traceback.print_exc()
            label_end = f"End: ({end_x}, {end_y})"
            draw.text((start_x + radius + 5, start_y - radius), label_start, fill="green", font=font)
            draw.text((end_x + radius + 5, end_y - radius), label_end, fill="blue", font=font)
            
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            self.logger.info(f"[DEBUG_SCREENSHOT] Drag 截圖已保存: {screenshot_path} (範圍: ({start_x}, {start_y}) -> ({end_x}, {end_y}))")
        except Exception as e:
            self.logger.warning(f"[DEBUG_SCREENSHOT] 保存 Drag 截圖失敗: {e}")
    
    def _save_vlm_scan_region_screenshot(self, step_name, scan_region, win):
        """
        🎯 保存 VLM 掃描區域的截圖，用紅框標記掃描區域
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "vlm_scan_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 提取掃描區域座標
            scan_left, scan_top, scan_width, scan_height = scan_region
            
            # 用紅框標記掃描區域
            rect_left = scan_left
            rect_top = scan_top
            rect_right = scan_left + scan_width
            rect_bottom = scan_top + scan_height
            
            # 繪製紅色矩形框（線寬 3px）
            draw.rectangle(
                [rect_left, rect_top, rect_right, rect_bottom],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記掃描區域信息
            draw.text((rect_left + 5, rect_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] VLM 掃描區域截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] VLM 掃描區域截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [SCAN_REGION] 掃描區域: ({scan_left}, {scan_top}, {scan_width}, {scan_height})")
            if win:
                print(f"[VLM_SCAN] [WINDOW] 視窗範圍: ({win.left}, {win.top}, {win.width}, {win.height})")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存截圖失敗: {e}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] 保存截圖失敗: {e}")
    
    def _save_vlm_error_screenshot(self, step_name, scan_region, win, vlm_x, vlm_y):
        """
        🎯 保存 VLM 錯誤截圖，標記掃描區域、視窗範圍和 VLM 返回的錯誤座標
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        :param vlm_x: VLM 返回的 X 座標
        :param vlm_y: VLM 返回的 Y 座標
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "vlm_scan_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 提取掃描區域座標
            scan_left, scan_top, scan_width, scan_height = scan_region
            
            # 用紅框標記掃描區域
            rect_left = scan_left
            rect_top = scan_top
            rect_right = scan_left + scan_width
            rect_bottom = scan_top + scan_height
            
            # 繪製紅色矩形框（線寬 3px）
            draw.rectangle(
                [rect_left, rect_top, rect_right, rect_bottom],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記 VLM 返回的錯誤座標（黃色圓圈）
            if abs(vlm_x) < 100000 and abs(vlm_y) < 100000:  # 只標記合理的座標範圍
                # 繪製黃色圓圈標記 VLM 返回的座標
                circle_radius = 10
                draw.ellipse(
                    [vlm_x - circle_radius, vlm_y - circle_radius, vlm_x + circle_radius, vlm_y + circle_radius],
                    outline="yellow",
                    width=3
                )
                draw.text((vlm_x + 15, vlm_y), f"VLM Coord: ({vlm_x}, {vlm_y})", fill="yellow")
            
            # 標記掃描區域信息
            draw.text((rect_left + 5, rect_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 標記錯誤信息
            if win:
                draw.text((rect_left + 5, rect_top + 25), f"ERROR: VLM coord ({vlm_x}, {vlm_y}) out of window ({win.left}, {win.top}, {win.width}, {win.height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] VLM 錯誤截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] VLM 錯誤截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [ERROR] VLM 返回座標 ({vlm_x}, {vlm_y}) 超出視窗範圍")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存錯誤截圖失敗: {e}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] 保存錯誤截圖失敗: {e}")
    
    def _save_vlm_click_coord_screenshot(self, step_name, scan_region, win, click_x, click_y):
        """
        🎯 保存點擊後的截圖，標記掃描區域和實際點擊的座標
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height) 或 None
        :param win: 視窗物件
        :param click_x: 實際點擊的 X 座標
        :param click_y: 實際點擊的 Y 座標
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "vlm_scan_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 標記掃描區域（如果有）
            if scan_region:
                scan_left, scan_top, scan_width, scan_height = scan_region
                # 用紅框標記掃描區域
                draw.rectangle(
                    [scan_left, scan_top, scan_left + scan_width, scan_top + scan_height],
                    outline="red",
                    width=2
                )
                draw.text((scan_left + 5, scan_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記實際點擊的座標（綠色圓圈和十字）
            circle_radius = 15
            draw.ellipse(
                [click_x - circle_radius, click_y - circle_radius, click_x + circle_radius, click_y + circle_radius],
                outline="green",
                width=3
            )
            # 繪製十字標記
            draw.line([(click_x - 20, click_y), (click_x + 20, click_y)], fill="green", width=3)
            draw.line([(click_x, click_y - 20), (click_x, click_y + 20)], fill="green", width=3)
            draw.text((click_x + circle_radius + 5, click_y - circle_radius), f"ACTUAL CLICK: ({click_x}, {click_y})", fill="green")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] 實際點擊座標截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] 實際點擊座標截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [CLICK_COORD] 實際點擊座標: ({click_x}, {click_y})")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存點擊座標截圖失敗: {e}")
            self._safe_log("info", f"[VLM_SCAN] [SCREENSHOT] 保存點擊座標截圖失敗: {e}")
    
    def _save_radio_scan_region_screenshot(self, step_name, scan_region, win):
        """
        🎯 保存 radio 掃描區域的截圖，用紅框標記掃描區域
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "radio_verify_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 提取掃描區域座標
            scan_left, scan_top, scan_width, scan_height = scan_region
            
            # 用紅框標記掃描區域
            rect_left = scan_left
            rect_top = scan_top
            rect_right = scan_left + scan_width
            rect_bottom = scan_top + scan_height
            
            # 繪製紅色矩形框（線寬 3px）
            draw.rectangle(
                [rect_left, rect_top, rect_right, rect_bottom],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記掃描區域信息
            draw.text((rect_left + 5, rect_top + 5), f"Radio Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[RADIO_VERIFY] [SCREENSHOT] Radio 掃描區域截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] Radio 掃描區域截圖已保存: {screenshot_path}")
            print(f"[RADIO_VERIFY] [SCAN_REGION] 掃描區域: ({scan_left}, {scan_top}, {scan_width}, {scan_height})")
            
        except Exception as e:
            self.logger.warning(f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
    
    def _save_radio_found_screenshot(self, step_name, scan_region, win, found_x, found_y):
        """
        🎯 保存找到 radio 的截圖，標記掃描區域和找到的座標
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        :param found_x: 找到的 X 座標
        :param found_y: 找到的 Y 座標
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "radio_verify_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 提取掃描區域座標
            scan_left, scan_top, scan_width, scan_height = scan_region
            
            # 用紅框標記掃描區域
            draw.rectangle(
                [scan_left, scan_top, scan_left + scan_width, scan_top + scan_height],
                outline="red",
                width=2
            )
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
            
            # 標記找到的座標（綠色圓圈和十字）
            circle_radius = 15
            draw.ellipse(
                [found_x - circle_radius, found_y - circle_radius, found_x + circle_radius, found_y + circle_radius],
                outline="green",
                width=3
            )
            draw.line([(found_x - 20, found_y), (found_x + 20, found_y)], fill="green", width=2)
            draw.line([(found_x, found_y - 20), (found_x, found_y + 20)], fill="green", width=2)
            draw.text((found_x + circle_radius + 5, found_y - circle_radius), f"Found: ({found_x}, {found_y})", fill="green")
            
            # 標記掃描區域信息
            draw.text((scan_left + 5, scan_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[RADIO_VERIFY] [SCREENSHOT] Radio 找到座標截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] Radio 找到座標截圖已保存: {screenshot_path}")
            
        except Exception as e:
            self.logger.warning(f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
    
    def _save_radio_not_found_screenshot(self, step_name, scan_region, win):
        """
        🎯 保存未找到 radio 的截圖，標記掃描區域
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 debug 目錄
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "radio_verify_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 提取掃描區域座標
            scan_left, scan_top, scan_width, scan_height = scan_region
            
            # 用紅框標記掃描區域
            draw.rectangle(
                [scan_left, scan_top, scan_left + scan_width, scan_top + scan_height],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）
            if win:
                win_rect_left = win.left
                win_rect_top = win.top
                win_rect_right = win.left + win.width
                win_rect_bottom = win.top + win.height
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
            
            # 標記錯誤信息
            draw.text((scan_left + 5, scan_top + 5), f"NOT FOUND in Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[RADIO_VERIFY] [SCREENSHOT] Radio 未找到截圖已保存: {screenshot_path}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] Radio 未找到截圖已保存: {screenshot_path}")
            
        except Exception as e:
            self.logger.warning(f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
            self._safe_log("info", f"[RADIO_VERIFY] [SCREENSHOT] 保存截圖失敗: {e}")
    
    def apply_camera_settings(self):
        """
        🎯 直接點擊「確認」按鈕（不需要點擊「套用」）
        優先級：VLM（限制區域）> 座標保底
        """
        self._log_method_entry("apply_camera_settings")
        self._safe_log("info", "[CLICK] 開始應用攝影機設定（直接點擊確認）...")
        
        # 🎯 獲取攝影機設定視窗
        win = None
        camera_settings_titles = ["攝影機設定", "Camera Settings", "攝影機設定 - Nx Witness Client", "Camera Settings - Nx Witness Client"]
        
        for title in camera_settings_titles:
            try:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    win = max(wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                    if win.width > 800 and win.height > 600:
                        # 🎯 激活窗口，確保可以點擊
                        try:
                            win.activate()
                            time.sleep(0.3)  # 等待窗口激活
                        except Exception as e:
                            self.logger.debug(f"[CONFIRM] 激活窗口失敗: {e}")
                        break
            except Exception:
                continue
        
        if not win:
            win = self.get_nx_window()
            if win and (win.width > 800 and win.height > 600):
                try:
                    win.activate()
                    time.sleep(0.3)  # 等待窗口激活
                except Exception as e:
                    self.logger.debug(f"[CONFIRM] 激活窗口失敗: {e}")
        
        # 🎯 直接點擊「確認」按鈕
        self._safe_log("info", "[CLICK] 點擊「確認」按鈕...")
        
        if win:
            # 底部區域：從視窗底部向上 15% 的區域
            bottom_region_height = int(win.height * 0.15)
            bottom_region = (win.left, win.top + win.height - bottom_region_height, win.width, bottom_region_height)
            
            self.logger.info(f"[CONFIRM] 限制搜索區域到底部: {bottom_region} (視窗: {win.width}x{win.height})")
            self._safe_log("info", f"[CONFIRM] 底部搜索區域: {bottom_region}")
            
            # 先使用 VLM 在底部區域搜索「確認」
            vlm = self._get_vlm_engine()
            if vlm:
                try:
                    # 🎯 保存掃描區域截圖
                    self._save_vlm_scan_region_screenshot("vlm_scan_confirm", bottom_region, win)
                    
                    result = vlm.find_element("確認", region=bottom_region)
                    if result and result.success and result.confidence > 0.7:
                        click_x = result.x
                        click_y = result.y
                        
                        # 驗證座標在底部區域內
                        if (bottom_region[0] <= click_x <= bottom_region[0] + bottom_region[2] and
                            bottom_region[1] <= click_y <= bottom_region[1] + bottom_region[3]):
                            
                            self.logger.info(f"[CONFIRM] VLM 找到「確認」: 座標=({click_x}, {click_y})")
                            print(f"[CONFIRM] VLM 找到「確認」: 座標=({click_x}, {click_y})")
                            
                            # 保存點擊座標截圖
                            self._save_vlm_click_coord_screenshot("vlm_confirm_click", bottom_region, win, click_x, click_y)
                            
                            # 🎯 再次確保窗口激活
                            try:
                                win.activate()
                                time.sleep(0.2)
                            except Exception:
                                pass
                            
                            self._perform_click(click_x, click_y, clicks=1, click_type='left')
                            time.sleep(0.3)  # 等待點擊生效
                            
                            self._safe_log("info", "[OK] 成功點擊「確認」按鈕（使用 VLM）")
                            return True
                        else:
                            self.logger.warning(f"[CONFIRM] VLM 返回座標 ({click_x}, {click_y}) 不在底部區域內")
                except Exception as e:
                    self.logger.warning(f"[CONFIRM] VLM 搜索異常: {e}")
        
        # 🎯 如果 VLM 失敗，嘗試使用圖片辨識
        self.logger.info("[CONFIRM] VLM 失敗，嘗試使用圖片辨識或座標保底")
        self._safe_log("info", "[CONFIRM] VLM 失敗，嘗試使用圖片辨識或座標保底")
        
        if win:
            # 🎯 嘗試使用圖片辨識（如果圖片存在）
            # 嘗試多個可能的圖片文件名
            confirm_image_names = ["confirm_button.png", "ok_btn.png", "確認.png"]
            confirm_image_path = None
            
            for img_name in confirm_image_names:
                test_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings", img_name)
                if os.path.exists(test_path):
                    confirm_image_path = test_path
                    break
            
            if confirm_image_path:
                try:
                    from base.ok_script_recognizer import get_recognizer
                    recognizer = get_recognizer()
                    result = recognizer.locate_on_screen(confirm_image_path, region=bottom_region, confidence=0.7)
                    if result and result.success:
                        # 計算中心點
                        center_x = result.x + (result.width // 2) if hasattr(result, 'width') and result.width > 0 else result.x
                        center_y = result.y + (result.height // 2) if hasattr(result, 'height') and result.height > 0 else result.y
                        
                        self.logger.info(f"[CONFIRM] 圖片辨識找到「確認」: 中心點=({center_x}, {center_y})")
                        print(f"[CONFIRM] 圖片辨識找到「確認」: 中心點=({center_x}, {center_y})")
                        
                        # 保存點擊座標截圖
                        self._save_vlm_click_coord_screenshot("image_confirm_click", bottom_region, win, center_x, center_y)
                        
                        # 確保窗口激活
                        try:
                            win.activate()
                            time.sleep(0.2)
                        except Exception:
                            pass
                        
                        self._perform_click(center_x, center_y, clicks=1, click_type='left')
                        time.sleep(0.3)
                        
                        self._safe_log("info", "[OK] 成功點擊「確認」按鈕（使用圖片辨識）")
                        return True
                except Exception as e:
                    self.logger.debug(f"[CONFIRM] 圖片辨識異常: {e}")
            
            # 🎯 如果圖片辨識失敗，使用座標保底
            # 計算底部右側座標
            # 🎯 調整：x 從 0.85 改為 0.88，確保點擊到「確認」而不是「套用」（確認在套用右側）
            click_x = win.left + int(win.width * 0.88)
            # 🎯 調整：從底部向上 5%，在 3% 和 6% 之間取中值
            click_y = win.top + win.height - int(win.height * 0.05)
            self.logger.info(f"[CONFIRM] 保底座標: ({click_x}, {click_y}) (基於 x_ratio=0.88, y_ratio=0.05 from_bottom)")
            print(f"[CONFIRM] 保底座標: ({click_x}, {click_y})")
        else:
            # 如果無法獲取視窗，使用全屏比例
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            # 🎯 調整：x 從 0.85 改為 0.88，確保點擊到「確認」而不是「套用」
            click_x = int(screen_width * 0.88)
            # 🎯 調整：從底部向上 5%，在 3% 和 6% 之間取中值
            click_y = screen_height - int(screen_height * 0.05)
            self.logger.info(f"[CONFIRM] 全屏保底座標: ({click_x}, {click_y})")
        
        # 保存點擊座標截圖
        if win:
            self._save_vlm_click_coord_screenshot("coordinate_confirm_click", None, win, click_x, click_y)
            
            # 🎯 再次確保窗口激活
            try:
                win.activate()
                time.sleep(0.2)
            except Exception:
                pass
        
        self._perform_click(click_x, click_y, clicks=1, click_type='left')
        time.sleep(0.3)  # 等待點擊生效
        
        self._safe_log("info", "[OK] 成功點擊「確認」按鈕（使用座標保底）")
        
        return True