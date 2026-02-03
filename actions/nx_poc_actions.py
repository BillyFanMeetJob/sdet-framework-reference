# 相對路徑: actions/nx_poc_actions.py
from base.base_action import BaseAction
import time
import pygetwindow as gw
import pyautogui

class NxPocActions(BaseAction):
    def __init__(self, browser_context):
        # 🎯 繼承 BaseAction，確保 browser_context, config, dt 同步載入
        super().__init__(browser=browser_context)
        
        # 按需實例化 Page，桌面端不傳 browser
        from pages.desktop.desktop_login_page import DesktopLoginPage
        from pages.desktop.main_page import MainPage
        from pages.desktop.settings_page import SettingsPage
        from pages.desktop.server_settings_page import ServerSettingsPage
        from pages.desktop.license_settings_page import LicenseSettingsPage
        from pages.desktop.camera_page import CameraPage
        from pages.desktop.nx_cloud_page import NxCloudPage
        from pages.web.nx_cloud_web_page import NxCloudWebPage
        
        self.login_page = DesktopLoginPage()
        self.main_page = MainPage()
        self.settings_page = SettingsPage()
        self.server_settings_page = ServerSettingsPage()
        self.camera_page = CameraPage()
        self.license_settings_page = LicenseSettingsPage()
        self.nx_cloud_page = NxCloudPage()  # 桌面端操作
        self.nx_cloud_web_page = NxCloudWebPage(browser=None)  # 網頁端操作（手動初始化 WebDriver）

    def run_server_login_step(self, **kwargs):
        """ ✅ 1-1 登錄流程：優先點擊 LAPTOP-QRJN5735，失敗則點擊連接服務器 """
        self.logger.info("[CASE_1-1] 執行 Case 1-1 登錄流程")
        self.login_page.launch_app(self.config.NX_EXE_PATH)
        
        server_name = kwargs.get("server_name", "LAPTOP-QRJN5735")
        password = kwargs.get("password", self.config.ADMIN_PASSWORD)
        
        # 優先嘗試點擊 LAPTOP-QRJN5735 卡片
        self.logger.info(f"[LOGIN] 優先嘗試點擊伺服器卡片: {server_name}")
        self.logger.info(f"[DEBUG] 使用圖片優先策略：OK Script > PyAutoGUI > VLM > OCR")
        # 使用圖片優先策略，因為圖片辨識更準確，避免 VLM 文字辨識位置偏差
        success = self.login_page.smart_click_priority_image(
            x_ratio=0.25,  # 左側卡片區域
            y_ratio=0.65,  # 卡片位置
            target_text=server_name,  # 作為備選文字辨識
            image_path="desktop_login/server_tile.png",  # 圖片辨識優先
            timeout=5
        )
        self.logger.info(f"[DEBUG] smart_click 返回結果: {success}")
        
        # 🔍 驗證：檢查是否誤點擊了「連接服務器」（如果出現對話框，表示點擊了「連接服務器」）
        # 因為保底坐標可能剛好對應到「連接服務器」的位置
        if success:
            self.logger.info("[VERIFY] 驗證點擊結果：檢查是否誤點擊了「連接服務器」...")
            time.sleep(2)  # 等待對話框出現（如果點擊了「連接服務器」）
            
            # 檢查是否出現連接服務器對話框（多次檢查，確保不會漏掉）
            dialog_titles = [
                "连接到服务器",
                "Connect to server",
                "连接到服务器...",
                "连接到服务器... - Nx Witness Client",
                "連線至伺服器",
                "連線至伺服器...",
                "連線至伺服器... - Nx Witness Client"
            ]
            
            dialog_found = False
            # 嘗試多次檢查（因為對話框可能出現較慢）
            for check_round in range(3):
                for title in dialog_titles:
                    try:
                        wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                        if wins:
                            dialog_found = True
                            self.logger.warning(f"[WARN] 檢測到連接服務器對話框出現: {title}（檢查輪次: {check_round+1}），表示點擊了「連接服務器」而非「{server_name}」")
                            self.logger.info("[SWITCH] 自動切換到「連接服務器」處理流程...")
                            break
                    except Exception as e:
                        self.logger.debug(f"檢查對話框標題 '{title}' 時發生異常: {e}")
                
                if dialog_found:
                    break
                
                if check_round < 2:  # 最後一次不需要等待
                    time.sleep(0.5)  # 等待後再次檢查
            
            if dialog_found:
                # 標記為未成功點擊 LAPTOP-QRJN5735，進入「連接服務器」處理流程
                success = False
            else:
                self.logger.info("[OK] 未檢測到連接服務器對話框，確認成功點擊了「LAPTOP-QRJN5735」")
        
        # 如果找不到 LAPTOP-QRJN5735 或誤點擊了「連接服務器」，嘗試點擊「連接服務器」
        if not success:
            self.logger.info("[WARN] 未找到伺服器卡片，嘗試點擊「連接服務器」...")
            self.logger.info(f"[DEBUG] 第一次嘗試失敗原因：可能是 VLM/OCR/圖片辨識都無法找到 '{server_name}' 或 'server_tile.png'")
            # 使用文字優先策略點擊「連接服務器」
            success = self.login_page.smart_click_priority_text(
                x_ratio=0.75,  # 右側「連接服務器」卡片
                y_ratio=0.65,
                target_text="連接服務器",  # 使用文字辨識
                timeout=5
            )
            
            if success:
                self.logger.info("[OK] 已點擊「連接服務器」，等待對話框出現...")
                time.sleep(2)  # 等待對話框完全出現
                
                # 驗證對話框是否出現（使用更寬鬆的匹配）
                dialog_found = False
                try:
                    # 檢查多種可能的對話框標題
                    dialog_titles = [
                        "连接到服务器",
                        "Connect to server",
                        "连接到服务器...",
                        "连接到服务器... - Nx Witness Client",
                        "Nx Witness Client"  # 如果對話框是主視窗的子視窗
                    ]
                    
                    win = self.login_page.get_nx_window()
                    if win:
                        # 檢查是否有包含這些關鍵字的視窗（gw 已在文件頂部導入）
                        for title in dialog_titles:
                            wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                            if wins:
                                dialog_found = True
                                self.logger.info(f"[OK] 連接服務器對話框已出現: {title}")
                                break
                    
                    if not dialog_found:
                        self.logger.warning("[WARN] 未檢測到連接服務器對話框，但繼續執行密碼輸入...")
                except Exception as e:
                    self.logger.warning(f"⚠️ 檢測對話框時發生異常: {e}，繼續執行...")
                
                # 先點擊密碼輸入框確保獲得焦點（根據圖片描述，密碼框在對話框中間偏下）
                self.logger.info("🖱️ 點擊密碼輸入框...")
                password_clicked = self.login_page.smart_click(
                    x_ratio=0.5,  # 對話框中間
                    y_ratio=0.55,  # 密碼框位置（在登錄框下方）
                    target_text="密码",  # 使用文字辨識找到密碼標籤
                    timeout=2
                )
                
                if not password_clicked:
                    # 如果文字辨識失敗，嘗試使用 smart_click 點擊密碼框區域（根據圖片，密碼框在對話框中間）
                    self.logger.info("⚠️ 文字辨識失敗，嘗試使用 smart_click 點擊密碼框區域...")
                    win = self.login_page.get_nx_window()
                    if win:
                        # 使用 smart_click 而非直接 pyautogui.click，避免亂點
                        password_clicked = self.login_page.smart_click(
                            x_ratio=0.5,  # 對話框中心
                            y_ratio=0.55,  # 對話框中間偏下
                            target_text=None,  # 不使用文字辨識
                            image_path=None,  # 不使用圖像辨識（因為這是保底策略）
                            timeout=0.5
                        )
                        if not password_clicked:
                            # 如果 smart_click 也失敗（因為保底坐標被禁用），記錄警告
                            self.logger.warning("⚠️ smart_click 失敗，跳過密碼框點擊（保底坐標已禁用）")
                
                # 處理密碼輸入
                self.logger.info(f"⌨️ 輸入密碼（長度: {len(password)} 字元）...")
                self.login_page.type_text(password)
                time.sleep(0.5)  # 等待輸入完成
                
                # 按 Enter 確認
                self.logger.info("⌨️ 按 Enter 確認登錄...")
                self.login_page.press_key('enter')
                
                # 等待登錄處理（最多 5 秒）
                self.logger.info("⏳ 等待登錄處理...")
                time.sleep(1)  # 初始等待
                
                # 🔍 檢查對話框是否已關閉（如果仍然存在，表示登錄失敗）
                dialog_still_open = False
                max_check = 4  # 檢查 4 次，每次間隔 1 秒
                for i in range(max_check):
                    time.sleep(1)
                    try:
                        dialog_titles = [
                            "连接到服务器",
                            "Connect to server",
                            "连接到服务器...",
                            "连接到服务器... - Nx Witness Client",
                            "連線至伺服器",
                            "連線至伺服器...",
                            "連線至伺服器... - Nx Witness Client"
                        ]
                        for title in dialog_titles:
                            wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                            if wins:
                                dialog_still_open = True
                                self.logger.warning(f"⚠️ 檢測到連接服務器對話框仍存在: {title}（嘗試 {i+1}/{max_check}）")
                                break
                        if dialog_still_open:
                            break
                    except Exception:
                        pass
                
                if dialog_still_open:
                    raise AssertionError("登錄失敗：連接服務器對話框仍然存在，可能是密碼錯誤或登錄失敗")
                
                self.logger.info("✅ 連接服務器對話框已關閉，繼續驗證登錄狀態...")
                time.sleep(1)  # 額外等待，確保系統完成登錄處理
        
        if success:
            self.logger.info("✅ 伺服器點擊成功，等待系統載入...")
            time.sleep(1.5) # 必要的進入緩衝（縮短至1.5秒）
            
            # 🔍 驗證：點擊後應該進入主畫面
            # 首先檢查視窗標題是否存在（主畫面視窗標題）
            win = self.main_page.get_nx_window()
            if not win:
                raise AssertionError("登錄驗證失敗：未找到主畫面視窗，可能登錄失敗或點錯位置")
            
            self.logger.info("✅ 找到主畫面視窗，繼續驗證...")
            
            # 檢查是否還在登錄畫面（如果還在登錄畫面，表示登錄失敗）
            # 注意：使用 verify_element_exists 而不是 smart_click，避免誤點擊
            login_indicator_found = False
            try:
                # 檢查登錄畫面的元素是否存在（如果存在，表示還在登錄畫面）
                # 使用 verify_element_exists 只檢查不點擊，避免誤操作
                login_indicators = [
                    "desktop_login/server_tile.png",
                    "desktop_login/login_indicator.png"
                ]
                for indicator in login_indicators:
                    try:
                        # 只驗證元素是否存在，不點擊
                        found = self.login_page.verify_element_exists(
                            image_path=indicator,
                            timeout=1,  # 短超時，快速檢查
                            raise_on_failure=False  # 不拋出異常，只返回結果
                        )
                        if found:
                            login_indicator_found = True
                            self.logger.warning(f"⚠️ 檢測到登錄畫面元素: {indicator}，可能仍在登錄畫面")
                            break
                    except Exception as e:
                        self.logger.debug(f"檢查登錄畫面元素 {indicator} 時發生異常: {e}")
            except Exception as e:
                self.logger.debug(f"檢查登錄畫面時發生異常: {e}")
            
            if login_indicator_found:
                # 再次確認：檢查主畫面元素是否存在（如果主畫面元素也存在，可能是誤判）
                main_page_found = False
                try:
                    main_page_found = self.main_page.verify_element_exists(
                        image_path="desktop_main/server_icon.png",
                        timeout=1,
                        raise_on_failure=False
                    )
                except Exception:
                    pass
                
                if not main_page_found:
                    # 主畫面元素不存在，確認仍在登錄畫面
                    raise AssertionError("登錄驗證失敗：仍在登錄畫面，登錄可能失敗")
                else:
                    # 主畫面元素也存在，可能是誤判，記錄警告但不拋出異常
                    self.logger.warning("⚠️ 檢測到登錄畫面元素，但主畫面元素也存在，可能是誤判，繼續執行...")
            
            # 嘗試驗證主畫面元素（圖片檢查失敗不導致整個驗證失敗，只記錄警告）
            try:
                self.main_page.verify_element_exists(
                    image_path="desktop_main/server_icon.png",  # 主畫面應該有 Server 圖示
                    window_titles=["Nx Witness Client"],  # 主畫面視窗標題
                    timeout=3,  # 縮短超時
                    raise_on_failure=False,  # 圖片檢查失敗不導致整個驗證失敗
                    error_message="登錄驗證：未找到主畫面圖示（可能是圖片辨識失敗）"
                )
                self.logger.info("✅ 登錄驗證成功：找到主畫面圖示")
            except Exception as e:
                self.logger.warning(f"⚠️ 圖片驗證失敗（可能是圖片辨識問題）: {e}")
                # 不拋出異常，因為視窗標題驗證已經通過
            
            self.logger.info("✅ 登錄驗證成功：已進入主畫面（視窗標題驗證通過）")
        else:
            raise AssertionError("登錄失敗：無法點擊伺服器卡片或連接服務器")
        
        return self

    def run_ensure_login_step(self, **kwargs):
        """
        ✅ 智能登錄檢查：檢查是否已登錄，未登錄則執行登錄
        用於 Case 1-2 等需要在已登錄狀態下執行的測試
        
        注意：如果軟件剛重新啟動，需要等待軟件完全啟動
        """
        server_name = kwargs.get("server_name", "LAPTOP-QRJN5735")
        self.logger.info(f"🔍 檢查登錄狀態（目標伺服器: {server_name}）")
        
        # 等待軟件完全啟動（最多 10 秒）
        max_wait = 10
        wait_interval = 0.5
        waited = 0
        
        while waited < max_wait:
            # 檢查是否已經在主畫面（尋找 Nx Witness Client 視窗）
            main_windows = gw.getWindowsWithTitle("Nx Witness Client")
            
            if main_windows:
                # 驗證視窗是否有效（嘗試訪問屬性）
                valid_window = None
                for w in main_windows:
                    if w.visible:
                        try:
                            # 驗證視窗物件是否有效
                            _ = w.left, w.top, w.width, w.height
                            if w.width > 0 and w.height > 0:
                                valid_window = w
                                break
                        except Exception:
                            # 視窗尚未完全初始化，繼續等待
                            continue
                
                if valid_window:
                    # 🔍 重要：不僅要檢查視窗是否存在，還要檢查是否真的已經登錄
                    # 因為登錄畫面的視窗標題也可能是 "Nx Witness Client"
                    # 我們需要檢查主畫面元素（如 server_icon.png）來確認是否已經登錄
                    
                    # 檢查是否在主畫面（通過檢查主畫面元素）
                    main_page_found = False
                    try:
                        main_page_found = self.main_page.verify_element_exists(
                            image_path="desktop_main/server_icon.png",  # 主畫面應該有 Server 圖示
                            timeout=2,  # 短超時，快速檢查
                            raise_on_failure=False  # 不拋出異常，只返回結果
                        )
                    except Exception as e:
                        self.logger.debug(f"檢查主畫面元素時發生異常: {e}")
                    
                    # 檢查是否還在登錄畫面（通過檢查登錄畫面元素）
                    login_page_found = False
                    try:
                        login_indicators = [
                            "desktop_login/server_tile.png",
                            "desktop_login/login_indicator.png"
                        ]
                        for indicator in login_indicators:
                            found = self.login_page.verify_element_exists(
                                image_path=indicator,
                                timeout=1,  # 短超時，快速檢查
                                raise_on_failure=False
                            )
                            if found:
                                login_page_found = True
                                self.logger.debug(f"檢測到登錄畫面元素: {indicator}")
                                break
                    except Exception as e:
                        self.logger.debug(f"檢查登錄畫面元素時發生異常: {e}")
                    
                    # 判斷是否已經登錄
                    if main_page_found and not login_page_found:
                        # 在主畫面且不在登錄畫面，確認已登錄
                        self.logger.info("✅ 已在主畫面，無需重新登錄（已通過主畫面元素驗證）")
                        return self
                    elif login_page_found and not main_page_found:
                        # 在登錄畫面且不在主畫面，需要登錄
                        self.logger.info("⚠️ 視窗存在但仍在登錄畫面，需要執行登錄")
                        break  # 跳出循環，執行登錄流程
                    elif main_page_found and login_page_found:
                        # 兩個都存在（可能誤判），但主畫面元素存在，認為已登錄
                        self.logger.warning("⚠️ 同時檢測到主畫面元素和登錄畫面元素，但主畫面元素存在，認為已登錄")
                        return self
                    else:
                        # 都不存在（可能視窗還在載入），繼續等待或執行登錄
                        self.logger.debug("⚠️ 未檢測到主畫面元素和登錄畫面元素，可能視窗還在載入，繼續檢查...")
                        # 繼續循環，等待視窗完全載入
            
            # 如果視窗不存在或無效，等待後重試
            if waited == 0:
                self.logger.info("⏳ 等待軟件啟動...")
            time.sleep(wait_interval)
            waited += wait_interval
        
        # 等待超時，執行登錄流程
        self.logger.info("⚠️ 未檢測到主畫面或軟件尚未完全啟動，執行登錄...")
        return self.run_server_login_step(**kwargs)

    def run_change_language_step(self, **kwargs):
        """ ✅ 1-1 語系流程：從 menu_icon.png 開始 """
        lang = kwargs.get("language", "繁體中文")
        self.logger.info(f"⚙️ 修改語系為: {lang}")
        
        # 立即開始語系切換流程，不額外等待
        # 步驟 1: 開啟主選單
        if not self.main_page.open_main_menu():
            error_msg = "開啟主選單失敗：無法點擊左上角菜單圖標"
            self.logger.error(f"[ERROR] {error_msg}")
            raise AssertionError(error_msg)
        
        # 步驟 2: 點擊本地設置
        self.logger.info("[DEBUG] 準備點擊本地設置...")
        try:
            print("[NX_POC_ACTIONS] 準備點擊本地設置...")
        except:
            pass
        
        local_settings_result = self.main_page.select_local_settings()
        self.logger.info(f"[DEBUG] select_local_settings 返回: {local_settings_result}")
        try:
            print(f"[NX_POC_ACTIONS] select_local_settings 返回: {local_settings_result}")
        except:
            pass
        
        if not local_settings_result:
            error_msg = "點擊本地設置失敗：無法找到或點擊本地設置選項"
            self.logger.error(f"[ERROR] {error_msg}")
            try:
                print(f"[NX_POC_ACTIONS] 錯誤: {error_msg}")
            except:
                pass
            raise AssertionError(error_msg)
        
        # 給設置視窗足夠時間完全載入
        self.logger.info("[DEBUG] 本地設置點擊成功，等待視窗載入...")
        try:
            print("[NX_POC_ACTIONS] 本地設置點擊成功，等待視窗載入...")
        except:
            pass
        time.sleep(1)
        
        # 步驟 3: 切換到外觀分頁
        self.logger.info("[DEBUG] 準備切換到外觀分頁...")
        try:
            print("[NX_POC_ACTIONS] 準備切換到外觀分頁...")
        except:
            pass
        self.settings_page.switch_to_appearance_tab()
        
        # 步驟 4: 修改語言
        self.settings_page.change_language(language=lang)
        
        self.logger.info(f"✅ 語系切換流程完成")
        return self

    def run_enable_usb_webcam_step(self, **kwargs):
        """
        ✅ Case 1-2: 自動偵測 USB 攝影機
        流程：
        1. 在左上 Server 點右鍵 -> 伺服器設定
        2. 勾選自動偵測 USB 攝影機 -> 套用
        3. 左鍵點擊 Server 圖示 -> 展開攝影機列表
        4. 雙擊 USB 攝影機
        """
        self.logger.info("🎬 執行 Case 1-2: 啟用 USB 攝影機自動偵測")
        
        # 🎯 獲取 TestReporter（如果存在）
        from base.desktop_app import DesktopApp
        reporter = DesktopApp.get_reporter()
        step_no = 1
        
        # 步驟 1: 在 Server 圖示上點擊右鍵
        if not self.server_settings_page.right_click_server_icon():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="右鍵點擊 Server 圖示",
                    status="fail",
                    message="右鍵點擊 Server 圖示失敗",
                    verification_items=[self.server_settings_page.create_verification_item("Server 圖示")]
                )
            raise AssertionError("❌ 右鍵點擊 Server 圖示失敗")
        
        # 🔍 驗證：右鍵點擊後應該出現選單
        time.sleep(0.8)  # 增加等待時間，讓選單完全出現
        menu_verified = False
        try:
            # 使用圖片和文字雙重驗證（任一成功即可）
            # 先嘗試圖片驗證
            try:
                self.server_settings_page.verify_element_exists(
                    image_path="desktop_settings/system_admin_menu.png",  # 選單中的項目
                    timeout=2,
                    raise_on_failure=False,  # 不拋出異常，繼續嘗試其他方法
                    error_message="圖片驗證失敗"
                )
                self.logger.info("✅ 選單驗證成功（圖片匹配）")
                menu_verified = True
            except AssertionError:
                # 圖片驗證失敗，嘗試文字驗證（使用 VLM 或 OCR）
                self.logger.debug("圖片驗證失敗，嘗試文字驗證...")
                try:
                    self.server_settings_page.verify_element_exists(
                        target_text="站點管理",  # 選單中的文字（優先使用 VLM）
                        timeout=2,
                        raise_on_failure=True,
                        error_message="右鍵點擊驗證失敗：選單未出現（圖片和文字驗證都失敗），可能點錯位置"
                    )
                    self.logger.info("✅ 選單驗證成功（文字匹配）")
                    menu_verified = True
                except AssertionError:
                    # 如果文字驗證也失敗，但選單可能已經出現（只是辨識失敗）
                    # 繼續執行，但記錄警告
                    self.logger.warning("⚠️ 選單驗證失敗，但繼續執行（選單可能已出現但辨識失敗）")
        except AssertionError as e:
            self.logger.error(f"❌ {str(e)}")
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="右鍵點擊 Server 圖示",
                    status="fail",
                    message=f"選單驗證失敗: {str(e)}",
                    verification_items=[self.server_settings_page.create_verification_item("右鍵選單")]
                )
            raise
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="右鍵點擊 Server 圖示",
                status="pass" if menu_verified else "warning",
                message="成功右鍵點擊 Server 圖示" + ("，選單已驗證" if menu_verified else "，選單驗證未通過但繼續執行"),
                verification_items=[
                    self.server_settings_page.create_verification_item("Server 圖示"),
                    self.server_settings_page.create_verification_item("右鍵選單")
                ]
            )
        step_no += 1
        
        # 步驟 2: 點擊右鍵選單中的「伺服器設定」
        if not self.server_settings_page.click_server_settings_menu():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊伺服器設定選單",
                    status="fail",
                    message="點擊伺服器設定選單失敗",
                    verification_items=[self.server_settings_page.create_verification_item("伺服器設定選單")]
                )
            raise AssertionError("❌ 點擊伺服器設定選單失敗")
        
        # 🔍 驗證：點擊選單後應該開啟伺服器設定視窗
        time.sleep(1)  # 等待視窗開啟
        window_verified = False
        try:
            self.server_settings_page.verify_element_exists(
                window_titles=["伺服器設定", "Server Settings"],
                timeout=3,
                raise_on_failure=True,
                error_message="點擊選單驗證失敗：伺服器設定視窗未開啟"
            )
            window_verified = True
        except AssertionError as e:
            self.logger.error(f"❌ {str(e)}")
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊伺服器設定選單",
                    status="fail",
                    message=f"伺服器設定視窗未開啟: {str(e)}",
                    verification_items=[self.server_settings_page.create_verification_item("伺服器設定視窗")]
                )
            raise
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="點擊伺服器設定選單",
                status="pass",
                message="成功點擊伺服器設定選單，視窗已開啟",
                verification_items=[self.server_settings_page.create_verification_item("伺服器設定視窗")]
            )
        step_no += 1
        
        # 步驟 3: 在設定視窗中勾選 USB 選項（如果未勾選）
        # 返回 (success, was_already_checked)
        success, was_already_checked = self.server_settings_page.enable_usb_detection()
        
        if not success:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="勾選 USB 攝影機選項",
                    status="fail",
                    message="檢查或勾選 USB 選項失敗",
                    verification_items=[self.server_settings_page.create_verification_item("USB 攝影機 checkbox")]
                )
            raise AssertionError("❌ 檢查或勾選 USB 選項失敗")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="勾選 USB 攝影機選項",
                status="pass",
                message=f"USB 選項已勾選{'（原本已勾選）' if was_already_checked else '（新勾選）'}",
                verification_items=[self.server_settings_page.create_verification_item("USB 攝影機 checkbox")]
            )
        step_no += 1
        
        # 步驟 4: 點擊套用或確定
        # 無論 checkbox 是否已經勾選，都需要點擊確認
        if not self.server_settings_page.apply_settings():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊套用/確定按鈕",
                    status="fail",
                    message="點擊套用/確定按鈕失敗",
                    verification_items=[self.server_settings_page.create_verification_item("套用/確定按鈕")]
                )
            self.logger.warning("⚠️ 套用設定可能失敗")
        else:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊套用/確定按鈕",
                    status="pass",
                    message="成功點擊套用/確定按鈕",
                    verification_items=[self.server_settings_page.create_verification_item("套用/確定按鈕")]
                )
        step_no += 1
        
        self.logger.info("✅ USB 攝影機自動偵測已啟用")
        
        # 步驟 5: 等待 USB 攝影機新增完成，然後展開列表
        # 新增攝影機需要幾秒鐘，完成後可能直接顯示 usb_cam，或需要點擊 Server 才會展開
        self.logger.info("⏳ 等待設定生效並偵測 USB 攝影機...")
        
        camera_name = kwargs.get("camera_name", "usb_cam")
        max_attempts = 8  # 最多嘗試 8 次
        camera_found = False
        expanded_server = False
        need_expand = True  # 是否需要展開 Server（首次或找不到時才展開）
        
        for attempt in range(max_attempts):
            self.logger.info(f"⏳ 第 {attempt + 1}/{max_attempts} 次嘗試尋找 USB 攝影機...")
            
            # 先等待 2 秒，讓系統有時間偵測
            time.sleep(2)
            
            # 嘗試找 usb_cam
            if self.server_settings_page.find_usb_camera(camera_name):
                self.logger.info(f"✅ 找到 USB 攝影機，準備雙擊...")
                # 找到了，執行雙擊（使用圖片辨識，不用保底坐標）
                if self.server_settings_page.double_click_usb_camera_strict(camera_name):
                    camera_found = True
                    self.logger.info(f"✅ 成功雙擊 USB 攝影機")
                    break
                else:
                    # 找到但點擊失敗，可能是圖片匹配不精確，繼續重試找
                    self.logger.warning(f"⚠️ 找到攝影機但雙擊失敗，繼續重試...")
                    need_expand = False  # 已經找到過，不需要再展開
                    continue
            
            # 沒找到 usb_cam
            if need_expand:
                # 嘗試雙擊 Server 展開列表
                self.logger.info(f"⚠️ 未找到攝影機，嘗試雙擊 Server 展開列表...")
                if self.server_settings_page.double_click_server_icon():
                    expanded_server = True
                    need_expand = False  # 已展開，下次不再展開
                    # 等待列表展開動畫
                    time.sleep(1.0)
            else:
                self.logger.debug(f"⚠️ 攝影機尚未出現或匹配失敗，繼續等待...")
        
        # 報告步驟 5: 展開列表
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="展開攝影機列表",
                status="pass" if expanded_server or camera_found else "warning",
                message="已嘗試展開攝影機列表" if expanded_server else "攝影機可能已自動展開",
                verification_items=[self.server_settings_page.create_verification_item("Server 圖示")]
            )
        step_no += 1
        
        # 報告步驟 6: 雙擊 USB 攝影機
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="雙擊 USB 攝影機",
                status="pass" if camera_found else "fail",
                message=f"{'成功找到並雙擊 USB 攝影機' if camera_found else '未找到攝影機（僅使用圖片辨識，未使用保底坐標）'}",
                verification_items=[self.server_settings_page.create_verification_item(f"USB 攝影機 ({camera_name})")]
            )
        
        if camera_found:
            self.logger.info(f"✅ Case 1-2 完成：已開啟攝影機 {camera_name}")
        else:
            self.logger.warning(f"⚠️ 嘗試 {max_attempts} 次後，仍未找到攝影機 {camera_name}（未使用保底坐標點擊）")
        
        return self
    
    def run_activate_free_license_step(self, **kwargs):
        """
        ✅ Case 1-3: 啟用免費一個月的錄製授權
        流程：
        1. 在左側 Server 上右鍵 -> 站點管理 (系統管理)
        2. 進入「站點管理」視窗（預設在「一般」頁籤）
        3. 切換到「授權」頁籤
        4. 嘗試點擊「啟用免費授權」按鈕（如果存在）
        5. 如果找到按鈕，確認授權成功彈窗
        6. 關閉站點管理視窗
        
        注意：如果授權已經啟用過，啟用按鈕將不存在，直接關閉視窗
        """
        self.logger.info("🎬 執行 Case 1-3: 啟用免費錄製授權")
        
        # 處理 use_menu 參數（可能是字符串 'False' 或布爾值 False）
        use_menu_raw = kwargs.get("use_menu", False)
        if isinstance(use_menu_raw, str):
            use_menu = use_menu_raw.lower() == 'true'
        else:
            use_menu = bool(use_menu_raw)
        
        # 步驟 1: 開啟站點管理視窗
        if not self.license_settings_page.open_system_administration(via_menu=use_menu):
            self.logger.error("[ERROR] 開啟站點管理視窗失敗")
            return self
        
        # 步驟 2: 切換到「授權」分頁
        if not self.license_settings_page.switch_to_license_tab():
            self.logger.error("[ERROR] 切換到授權分頁失敗")
            # 即使切換失敗，也嘗試關閉視窗
            self.license_settings_page.close_system_administration()
            return self
        
        # 步驟 3: 嘗試點擊「啟用免費授權」按鈕
        if self.license_settings_page.click_activate_free_license():
            # 找到按鈕並點擊成功
            self.logger.info("✅ 正在啟用免費授權...")
            
            # 步驟 4: 確認授權啟動成功彈窗
            if self.license_settings_page.confirm_license_activation():
                self.logger.info("✅ 授權啟動成功")
            else:
                self.logger.warning("⚠️ 未檢測到授權確認彈窗")
        else:
            # 按鈕不存在，授權可能已經啟用過
            self.logger.info("ℹ️ 授權已存在或按鈕不可用，直接關閉視窗")
        
        # 步驟 5: 關閉站點管理視窗
        if self.license_settings_page.close_system_administration():
            self.logger.info("✅ Case 1-3 完成")
        else:
            self.logger.warning("⚠️ 站點管理視窗可能未正確關閉")
        
        return self
    
    def run_enable_recording_step(self, **kwargs):
        """
        ✅ Case 1-4: 開啟錄影功能
        流程：
        1. 找到要開啟錄製功能的攝影機，右鍵點選「攝影機設定」
        2. 進入「攝影機設定」視窗，點選「錄製」頁籤
        3. 開啟左上角「錄製」開關，點選 OK，就會開始錄影
        """
        camera_name = kwargs.get("camera_name", "usb_cam")
        self.logger.info(f"[CASE_1-4] 執行 Case 1-4: 開啟錄影功能（攝影機: {camera_name}）")
        
        # 步驟 1: 右鍵點擊攝影機，點選「攝影機設定」
        if not self.camera_page.right_click_camera(camera_name):
            raise AssertionError("[ERROR] 右鍵點擊攝影機失敗")
        
        # 點擊「攝影機設定」選單項
        if not self.camera_page.click_camera_settings_menu():
            raise AssertionError("[ERROR] 點擊「攝影機設定」選單失敗")
        
        # 🔍 驗證：點擊選單後應該開啟攝影機設定視窗
        time.sleep(1.5)  # 增加等待時間，確保視窗完全開啟
        try:
            self.camera_page.verify_element_exists(
                window_titles=["攝影機設定", "Camera Settings"],
                timeout=5,  # 增加超時時間
                raise_on_failure=True,
                error_message="點擊選單驗證失敗：攝影機設定視窗未開啟"
            )
        except AssertionError as e:
            self.logger.error(f"❌ {str(e)}")
            raise
        
        # 額外等待，確保視窗完全載入
        time.sleep(0.5)
        
        # 步驟 2: 點選「錄製」頁籤
        import sys
        print("[ACTION] [STEP 2] 準備切換到錄影分頁簽...", file=sys.stderr)
        self.logger.info("[DEBUG] 準備切換到錄影分頁簽...")
        try:
            print("[ACTION] [STEP 2] 調用 camera_page.switch_to_recording_tab()...", file=sys.stderr)
            self.camera_page.switch_to_recording_tab()
            print("[ACTION] [STEP 2] switch_to_recording_tab() 完成", file=sys.stderr)
            self.logger.info("[DEBUG] 成功切換到錄影分頁簽")
        except Exception as e:
            print(f"[ACTION] [STEP 2] switch_to_recording_tab() 異常: {e}", file=sys.stderr)
            self.logger.error(f"❌ 切換到錄影分頁簽失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # 步驟 3: 開啟左上角「錄製」開關
        print("[ACTION] [STEP 3] 準備調用 camera_page.enable_recording()...", file=sys.stderr)
        self.logger.info("[ACTION] [STEP 3] 準備調用 enable_recording()...")
        try:
            print("[ACTION] [STEP 3] 調用 camera_page.enable_recording()...", file=sys.stderr)
            self.camera_page.enable_recording()
            print("[ACTION] [STEP 3] enable_recording() 完成", file=sys.stderr)
        except Exception as e:
            print(f"[ACTION] [STEP 3] enable_recording() 異常: {e}", file=sys.stderr)
            self.logger.error(f"❌ enable_recording() 失敗: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # 步驟 4: 點選「確認」按鈕
        self.camera_page.apply_camera_settings()
        
        self.logger.info("✅ Case 1-4 完成：已開啟錄影功能")
        return self
    
    def run_playback_recording_step(self, **kwargs):
        """
        ✅ Case 1-5: 回放錄影事件後停止
        流程：
        1. 選擇一支已開啟錄影的攝影機（假設已在前置步驟中選擇）
        2. 點擊右下角日曆圖標
        3. 在日曆中選擇有綠色標記的日期（表示有錄影事件）
        4. 在底部進度條中點擊綠色的錄影時段
        5. 等待播放 5-10 秒後，暫停回放
        """
        playback_duration = kwargs.get("playback_duration", 7)  # 預設 7 秒（在 5-10 秒之間）
        # 🎯 確保 playback_duration 是數字類型（Excel 可能讀取為字符串）
        try:
            playback_duration = float(playback_duration) if playback_duration else 7
        except (ValueError, TypeError):
            self.logger.warning(f"[CASE_1-5] 無法轉換 playback_duration '{playback_duration}' 為數字，使用預設值 7")
            playback_duration = 7
        self.logger.info(f"[CASE_1-5] 執行 Case 1-5: 回放錄影事件後停止（播放持續時間: {playback_duration} 秒）")
        
        # 🎯 獲取 TestReporter 實例（由 test_runner.py 初始化並設置）
        from base.desktop_app import DesktopApp
        reporter = DesktopApp._reporter
        
        # 如果沒有 reporter，嘗試初始化一個（為了向後兼容）
        if reporter is None:
            try:
                from engine.test_reporter import TestReporter
                reporter = TestReporter("Case 1-5: 回放錄影事件後停止")
                DesktopApp.set_reporter(reporter)
                self.logger.warning("[CASE_1-5] TestReporter 未初始化，自動創建一個實例")
            except Exception as e:
                self.logger.warning(f"[CASE_1-5] 無法初始化 TestReporter: {e}")
                reporter = None
        
        # 🎯 獲取當前 reporter 的步驟數量，用於子步驟編號
        # test_runner.py 會在步驟執行後添加主步驟，所以這裡的子步驟編號
        # 應該從當前步驟數量 + 1 開始（作為主步驟的詳細子步驟）
        if reporter and hasattr(reporter, 'steps'):
            # 獲取當前已記錄的步驟數量，子步驟從下一個編號開始
            base_step_no = len(reporter.steps)
            step_no = base_step_no + 1
        else:
            step_no = 1
        
        # 步驟 0: 檢查錄影畫面是否已開啟，如果全黑則雙擊 usb_cam 打開錄影畫面
        self.logger.info("[CASE_1-5] 步驟 0: 檢查錄影畫面是否已開啟...")
        
        try:
            # 檢查錄影畫面是否已開啟
            is_view_open = self.main_page.is_recording_view_open()
            
            if not is_view_open:
                # 畫面全黑，需要雙擊 usb_cam 打開錄影畫面
                self.logger.info("[CASE_1-5] 錄影畫面未開啟（全黑），雙擊 usb_cam 打開錄影畫面...")
                
                if not self.server_settings_page.double_click_usb_camera("usb_cam"):
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="雙擊 usb_cam 打開錄影畫面",
                            status="fail",
                            message="雙擊 usb_cam 失敗，無法打開錄影畫面",
                            verification_items=[{"name": "usb_cam"}]
                        )
                    raise AssertionError("[ERROR] 雙擊 usb_cam 失敗，無法打開錄影畫面")
                
                time.sleep(1.0)  # 等待錄影畫面完全載入
                
                # 再次檢查錄影畫面是否已開啟
                is_view_open_after = self.main_page.is_recording_view_open()
                if not is_view_open_after:
                    self.logger.warning("[CASE_1-5] 雙擊 usb_cam 後，錄影畫面仍然全黑，但繼續執行")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="雙擊 usb_cam 打開錄影畫面",
                        status="pass",
                        message="成功雙擊 usb_cam，錄影畫面已開啟",
                        verification_items=[{"name": "usb_cam"}]
                    )
            else:
                # 畫面已開啟，跳過雙擊
                self.logger.info("[CASE_1-5] 錄影畫面已開啟，跳過雙擊 usb_cam")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="檢查錄影畫面狀態",
                        status="pass",
                        message="錄影畫面已開啟，無需雙擊 usb_cam",
                        verification_items=[{"name": "錄影畫面"}]
                    )
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="檢查錄影畫面狀態",
                    status="fail",
                    message=f"執行失敗: {str(e)}",
                    verification_items=[{"name": "錄影畫面"}]
                )
            raise
        
        step_no += 1
        
        # 步驟 1: 點擊右下角日曆圖標
        self.logger.info("[CASE_1-5] 步驟 1: 點擊右下角日曆圖標...")
        
        try:
            # 計算日曆圖標的預期座標（用於檢核點）
            win = self.main_page.get_nx_window()
            calendar_icon_x = None
            calendar_icon_y = None
            if win:
                # 日曆圖標位置：x_ratio=0.92, y_ratio=0.04 (from_bottom=True), offset_x=0
                calendar_icon_x = int(win.left + win.width * 0.92)
                calendar_icon_y = int(win.top + win.height - win.height * 0.04)
            
            if not self.main_page.click_calendar_icon():
                if reporter:
                    verification_items = [self.main_page.create_verification_item(
                        "右下角日曆圖標",
                        center_x=calendar_icon_x,
                        center_y=calendar_icon_y,
                        width=40,
                        height=40
                    )] if calendar_icon_x else [self.main_page.create_verification_item("右下角日曆圖標")]
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊右下角日曆圖標",
                        status="fail",
                        message="點擊日曆圖標失敗",
                        verification_items=verification_items
                    )
                raise AssertionError("[ERROR] 點擊日曆圖標失敗")
            
            if reporter:
                verification_items = [
                    self.main_page.create_verification_item(
                        "右下角日曆圖標",
                        center_x=calendar_icon_x,
                        center_y=calendar_icon_y,
                        width=40,
                        height=40
                    ) if calendar_icon_x else self.main_page.create_verification_item("右下角日曆圖標"),
                    self.main_page.create_verification_item("日曆彈窗")
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊右下角日曆圖標",
                    status="pass",
                    message="成功點擊右下角日曆圖標，日曆已彈出",
                    verification_items=verification_items
                )
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊右下角日曆圖標",
                    status="fail",
                    message=f"執行失敗: {str(e)}",
                    verification_items=[{"name": "右下角日曆"}]
                )
            raise
        
        step_no += 1
        time.sleep(0.5)  # 等待日曆彈出
        
        # 步驟 2: 在日曆中選擇有綠色標記的日期
        self.logger.info("[CASE_1-5] 步驟 2: 在日曆中選擇有綠色標記的日期...")
        
        try:
            if not self.main_page.select_date_with_recording():
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="選擇有錄影事件的日期",
                        status="fail",
                        message="選擇有錄影事件的日期失敗",
                        verification_items=[{"name": "錄影日期"}]
                    )
                raise AssertionError("[ERROR] 選擇有錄影事件的日期失敗")
            
            if reporter:
                # 添加多個檢核點：日期、綠色標記、日曆區域
                verification_items = [
                    self.main_page.create_verification_item("錄影日期"),
                    self.main_page.create_verification_item("綠色錄影標記"),
                    self.main_page.create_verification_item("日曆區域")
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="選擇有錄影事件的日期",
                    status="pass",
                    message="成功選中有錄影事件的日期（通常是 17-20 號），綠色標記已驗證",
                    verification_items=verification_items
                )
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="選擇有錄影事件的日期",
                    status="fail",
                    message=f"執行失敗: {str(e)}",
                    verification_items=[{"name": "錄影日期"}]
                )
            raise
        
        step_no += 1
        time.sleep(0.5)  # 等待日期選擇生效
        
        # 步驟 3: 在底部進度條中點擊綠色的錄影時段（這是 1-5 的 Demo 重點）
        self.logger.info("[CASE_1-5] 步驟 3: 在底部進度條中點擊綠色的錄影時段...")
        
        try:
            if not self.main_page.click_green_timeline_segment():
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊錄影時段（綠色條）",
                        status="fail",
                        message="點擊進度條中的綠色錄影時段失敗",
                        verification_items=[{"name": "錄影時段選擇"}]
                    )
                raise AssertionError("[ERROR] 點擊進度條中的綠色錄影時段失敗")
            
            # 🎯 Demo 重點：確保記錄點擊後的截圖
            if reporter:
                # 添加多個檢核點：時間軸、綠色時段、播放狀態
                verification_items = [
                    self.main_page.create_verification_item("底部時間軸"),
                    self.main_page.create_verification_item("綠色錄影時段"),
                    self.main_page.create_verification_item("播放狀態指示")
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊錄影時段（綠色條）",
                    status="pass",
                    message="成功點擊時間軸上的綠色錄影時段，開始播放錄影",
                    verification_items=verification_items
                )
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊錄影時段（綠色條）",
                    status="fail",
                    message=f"執行失敗: {str(e)}",
                    verification_items=[{"name": "錄影時段選擇"}]
                )
            raise
        
        step_no += 1
        time.sleep(1.0)  # 等待播放開始
        
        # 步驟 4: 等待播放指定時間後暫停
        self.logger.info(f"[CASE_1-5] 步驟 4: 等待播放 {playback_duration} 秒後暫停...")
        
        try:
            if not self.main_page.pause_playback(playback_duration=playback_duration):
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="暫停回放",
                        status="fail",
                        message="暫停播放失敗",
                        verification_items=[{"name": "暫停按鈕"}]
                    )
                raise AssertionError("[ERROR] 暫停播放失敗")
            
            if reporter:
                # 添加多個檢核點：暫停狀態、播放進度、時間軸位置
                verification_items = [
                    self.main_page.create_verification_item("暫停狀態"),
                    self.main_page.create_verification_item("播放進度指示"),
                    self.main_page.create_verification_item("時間軸位置")
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="暫停回放",
                    status="pass",
                    message=f"成功播放錄影 {playback_duration} 秒後暫停（使用空白鍵）",
                    verification_items=verification_items
                )
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="暫停回放",
                    status="fail",
                    message=f"執行失敗: {str(e)}",
                    verification_items=[{"name": "暫停按鈕"}]
                )
            raise
        
        self.logger.info("✅ Case 1-5 完成：已回放錄影並暫停")
        return self
    
    def run_enter_nx_cloud_step(self, **kwargs):
        """
        Case 2-1: 進入 Nx Cloud
        
        流程：
        1. 點擊畫面右上角的賬號（會出現 menu）
        2. 點擊「開啟 Nx Cloud 介面」（使用圖片 desktop_settings/open_nx_web.png）
        3. 等待 Chrome 打開網頁
        4. 如果右上角登錄按鈕存在，進入網頁版登錄流程
        
        網頁版登錄流程：
        1. 點擊登錄按鈕
        2. 輸入郵箱
        3. 點擊【下一步】
        4. 輸入密碼
        5. 點擊【登錄】
        """
        self.logger.info("[CASE_2-1] 執行 Case 2-1: 進入 Nx Cloud")
        
        try:
            # 初始化 TestReporter
            reporter = None
            try:
                from engine.test_reporter import TestReporter
                reporter = TestReporter.get_instance()
                if not reporter:
                    self.logger.warning("[CASE_2-1] TestReporter 未初始化，自動創建一個實例")
                    reporter = TestReporter()
            except Exception as e:
                self.logger.warning(f"[CASE_2-1] 無法初始化 TestReporter: {e}")
            
            step_no = 1
            
            # 步驟 1: 點擊畫面右上角的賬號
            self.logger.info("[CASE_2-1] 步驟 1: 點擊畫面右上角的賬號...")
            if not self.nx_cloud_page.click_account_menu():
                error_msg = "點擊右上角賬號失敗"
                self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊右上角賬號",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊右上角賬號",
                    status="pass",
                    message="成功點擊右上角賬號，選單已展開"
                )
            step_no += 1
            
            # 步驟 2: 點擊「開啟 Nx Cloud 介面」
            self.logger.info("[CASE_2-1] 步驟 2: 點擊「開啟 Nx Cloud 介面」...")
            if not self.nx_cloud_page.click_open_nx_cloud_interface():
                error_msg = "點擊「開啟 Nx Cloud 介面」失敗"
                self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊「開啟 Nx Cloud 介面」",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊「開啟 Nx Cloud 介面」",
                    status="pass",
                    message="成功點擊「開啟 Nx Cloud 介面」，Chrome 正在打開"
                )
            step_no += 1
            
            # 步驟 3: 等待 Chrome 視窗出現
            self.logger.info("[CASE_2-1] 步驟 3: 等待 Chrome 視窗出現...")
            if not self.nx_cloud_page.wait_for_chrome_window(timeout=10):
                error_msg = "等待 Chrome 視窗超時"
                self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="等待 Chrome 視窗",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="等待 Chrome 視窗",
                    status="pass",
                    message="Chrome 視窗已打開"
                )
            step_no += 1
            
            # 步驟 4: 從瀏覽器獲取 URL（桌面端）
            self.logger.info("[CASE_2-1] 步驟 4: 從瀏覽器獲取 URL...")
            target_url = self.nx_cloud_page.get_current_browser_url()
            
            if not target_url:
                error_msg = "無法從瀏覽器獲取 Nx Cloud 網址"
                self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="獲取瀏覽器 URL",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="獲取瀏覽器 URL",
                    status="pass",
                    message=f"成功獲取 URL: {target_url}"
                )
            step_no += 1
            
            # 步驟 5: 啟動新的 WebDriver 並導航到 URL（網頁端）
            self.logger.info("[CASE_2-1] 步驟 5: 啟動新的 WebDriver 並導航到 URL...")
            if not self.nx_cloud_web_page.start_new_driver_and_open_url(target_url):
                error_msg = "啟動新 WebDriver 並導航到 URL 失敗"
                self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="啟動新 WebDriver",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="啟動新 WebDriver",
                    status="pass",
                    message="成功啟動新 WebDriver 並導航到 URL"
                )
            step_no += 1
            
            # 步驟 6: 檢查登錄按鈕是否存在（網頁端）
            self.logger.info("[CASE_2-1] 步驟 6: 檢查登錄按鈕是否存在...")
            if self.nx_cloud_web_page.check_login_button_exists():
                self.logger.info("[CASE_2-1] 登錄按鈕存在，進入網頁版登錄流程...")
                
                # 步驟 6.1: 點擊登錄按鈕（網頁端）
                self.logger.info("[CASE_2-1] 步驟 6.1: 點擊登錄按鈕...")
                if not self.nx_cloud_web_page.click_login_button():
                    error_msg = "點擊登錄按鈕失敗"
                    self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="點擊登錄按鈕",
                            status="fail",
                            message=error_msg
                        )
                    raise AssertionError(f"[ERROR] {error_msg}")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊登錄按鈕",
                        status="pass",
                        message="成功點擊登錄按鈕"
                    )
                step_no += 1
                
                # 步驟 6.2: 輸入郵箱（網頁端）
                self.logger.info("[CASE_2-1] 步驟 6.2: 輸入郵箱...")
                email = kwargs.get("email", self.config.NX_CLOUD_EMAIL)
                if not self.nx_cloud_web_page.input_email(email):
                    error_msg = f"輸入郵箱失敗: {email}"
                    self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="輸入郵箱",
                            status="fail",
                            message=error_msg
                        )
                    raise AssertionError(f"[ERROR] {error_msg}")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="輸入郵箱",
                        status="pass",
                        message=f"成功輸入郵箱: {email}"
                    )
                step_no += 1
                
                # 步驟 6.3: 點擊【下一步】（網頁端）
                self.logger.info("[CASE_2-1] 步驟 6.3: 點擊【下一步】...")
                if not self.nx_cloud_web_page.click_next_button():
                    error_msg = "點擊【下一步】失敗"
                    self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="點擊【下一步】",
                            status="fail",
                            message=error_msg
                        )
                    raise AssertionError(f"[ERROR] {error_msg}")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊【下一步】",
                        status="pass",
                        message="成功點擊【下一步】"
                    )
                step_no += 1
                
                # 步驟 6.4: 輸入密碼（網頁端）
                self.logger.info("[CASE_2-1] 步驟 6.4: 輸入密碼...")
                password = kwargs.get("password", self.config.NX_CLOUD_PASSWORD)
                if not self.nx_cloud_web_page.input_password(password):
                    error_msg = "輸入密碼失敗"
                    self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="輸入密碼",
                            status="fail",
                            message=error_msg
                        )
                    raise AssertionError(f"[ERROR] {error_msg}")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="輸入密碼",
                        status="pass",
                        message="成功輸入密碼"
                    )
                step_no += 1
                
                # 步驟 6.5: 點擊【登錄】（網頁端）
                self.logger.info("[CASE_2-1] 步驟 6.5: 點擊【登錄】...")
                if not self.nx_cloud_web_page.click_login_submit_button():
                    error_msg = "點擊【登錄】失敗"
                    self.logger.error(f"[CASE_2-1] [ERROR] {error_msg}")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="點擊【登錄】",
                            status="fail",
                            message=error_msg
                        )
                    raise AssertionError(f"[ERROR] {error_msg}")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊【登錄】",
                        status="pass",
                        message="成功點擊【登錄】，登錄流程完成"
                    )
            else:
                self.logger.info("[CASE_2-1] 登錄按鈕不存在，可能已經登錄，跳過登錄流程")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="檢查登錄按鈕",
                        status="pass",
                        message="登錄按鈕不存在，可能已經登錄，跳過登錄流程"
                    )
            
        except Exception as e:
            self.logger.error(f"[CASE_2-1] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            # 🎯 不關閉 WebDriver，保留瀏覽器以便後續步驟使用
            # 如果確實需要關閉，可以在測試完成後手動調用 close_webdriver()
            self.logger.info("[CASE_2-1] [INFO] 保留瀏覽器視窗，以便後續步驟使用")
            raise
        
        self.logger.info("✅ Case 2-1 完成：已進入 Nx Cloud")
        self.logger.info("[CASE_2-1] [INFO] 瀏覽器視窗已保留，可用於後續步驟")
        return self
    
    def run_review_recording_playback_step(self, **kwargs):
        """
        Case 2-2: 調閱一個錄影事件回放
        
        步驟：
        1. 點擊「查看」頁簽
        2. 點擊 server
        3. 點擊 usb-cam
        """
        self.logger.info("[CASE_2-2] 執行 Case 2-2: 調閱一個錄影事件回放")
        
        try:
            # 1. 初始化 Page Object (如果還沒有)
            if not self.nx_cloud_web_page:
                self.logger.info("[CASE_2-2] 開始初始化 NxCloudWebPage...")
                from pages.web.nx_cloud_web_page import NxCloudWebPage
                self.nx_cloud_web_page = NxCloudWebPage()
                self.logger.info("[CASE_2-2] 已初始化 NxCloudWebPage")
            else:
                self.logger.info("[CASE_2-2] NxCloudWebPage 已存在，跳過初始化")
            
            # 在開始連線前等待 2 秒，給系統時間釋放 Socket 資源
            self.logger.info("[CASE_2-2] 等待 2 秒，讓系統釋放 Socket 資源...")
            time.sleep(2)
            self.logger.info("[CASE_2-2] 等待完成，開始連線操作")
        except Exception as e:
            self.logger.error(f"[CASE_2-2] [ERROR] 初始化或等待階段發生異常: {e}")
            import traceback
            self.logger.error(f"[CASE_2-2] [ERROR] 錯誤詳情: {traceback.format_exc()}")
            raise
        
        # 2. 檢查 Driver 是否活著，如果死了就「重新連接」
        # 利用 Remote Debugging Port (9223) 的優勢：只要 Chrome 還開著，隨時都能連回去
        try:
            driver_exists = False
            try:
                driver_exists = self.nx_cloud_web_page.driver is not None
                self.logger.info(f"[CASE_2-2] Driver 狀態檢查: {'已連接' if driver_exists else '未連接'}")
            except Exception as e:
                self.logger.warning(f"[CASE_2-2] 檢查 driver 時發生異常: {e}，將嘗試重新連接")
                driver_exists = False
            
            if not driver_exists:
                self.logger.info("[CASE_2-2] Driver 未連接，嘗試重新連接到現有的 Debug Chrome (Port 9223)...")
                
                success = self.nx_cloud_web_page.attach_to_debug_chrome(port=9223)
                
                if not success:
                    self.logger.error("[CASE_2-2] ❌ 重新連接失敗！請確認 Chrome (Port 9223) 是否已開啟。")
                    raise AssertionError("[ERROR] WebDriver 重新連接失敗，請確認 Chrome (Port 9223) 是否已開啟")
                else:
                    self.logger.info("[CASE_2-2] ✅ 重新連接成功！繼續執行測試。")
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_2-2] [ERROR] 連接 Driver 時發生異常: {e}")
            import traceback
            self.logger.error(f"[CASE_2-2] [ERROR] 錯誤詳情: {traceback.format_exc()}")
            raise
        
        # 3. 確保現在是在正確的頁面（記錄當前 URL）
        try:
            current_url = self.nx_cloud_web_page.driver.current_url
            self.logger.info(f"[CASE_2-2] 當前網址: {current_url}")
        except Exception as e:
            self.logger.warning(f"[CASE_2-2] 無法獲取當前 URL: {e}")
        
        # 獲取 TestReporter（如果存在）
        reporter = None
        try:
            from base.desktop_app import DesktopApp
            reporter = DesktopApp.get_reporter()
        except Exception as e:
            self.logger.warning(f"[CASE_2-2] 無法獲取 TestReporter: {e}")
        
        try:
            step_no = 1
            
            # 步驟 1: 點擊「查看」頁簽
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 點擊「查看」頁簽...")
            if not self.nx_cloud_web_page.click_view_tab():
                error_msg = "點擊「查看」頁簽失敗"
                self.logger.error(f"[CASE_2-2] [ERROR] {error_msg}")
                if reporter:
                    verification_items = [
                        {"name": "查看頁簽"},
                        {"name": "頁面標籤區域"}
                    ]
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊「查看」頁簽",
                        status="fail",
                        message=error_msg,
                        verification_items=verification_items
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                verification_items = [
                    {"name": "查看頁簽"},
                    {"name": "頁面標籤區域"},
                    {"name": "頁面內容區域"}
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊「查看」頁簽",
                    status="pass",
                    message="成功點擊「查看」頁簽，頁面已切換",
                    verification_items=verification_items
                )
            step_no += 1
            
            # 等待頁面完全加載（在查詢操作前）
            wait_before_query = 3  # 等待 3 秒，確保頁面完全加載
            self.logger.info(f"[CASE_2-2] 等待 {wait_before_query} 秒，確保頁面完全加載後再進行查詢操作...")
            time.sleep(wait_before_query)
            self.logger.info(f"[CASE_2-2] [OK] 等待完成，開始查詢操作")
            
            # 步驟 2: 點擊 server
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 點擊 server...")
            if not self.nx_cloud_web_page.click_server():
                error_msg = "點擊 server 失敗"
                self.logger.error(f"[CASE_2-2] [ERROR] {error_msg}")
                if reporter:
                    verification_items = [
                        {"name": "Server 項目"},
                        {"name": "設備列表"}
                    ]
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊 server",
                        status="fail",
                        message=error_msg,
                        verification_items=verification_items
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                verification_items = [
                    {"name": "Server 項目"},
                    {"name": "設備列表"},
                    {"name": "展開的設備樹"}
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊 server",
                    status="pass",
                    message="成功點擊 server，設備列表已展開",
                    verification_items=verification_items
                )
            step_no += 1
            
            # 步驟 3: 點擊 usb-cam
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 點擊 usb-cam...")
            if not self.nx_cloud_web_page.click_usb_cam():
                error_msg = "點擊 usb-cam 失敗"
                self.logger.error(f"[CASE_2-2] [ERROR] {error_msg}")
                if reporter:
                    verification_items = [
                        {"name": "USB 攝影機項目"},
                        {"name": "設備列表"}
                    ]
                    reporter.add_step(
                        step_no=step_no,
                        step_name="點擊 usb-cam",
                        status="fail",
                        message=error_msg,
                        verification_items=verification_items
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                verification_items = [
                    {"name": "USB 攝影機項目"},
                    {"name": "設備列表"},
                    {"name": "視頻預覽區域"}
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊 usb-cam",
                    status="pass",
                    message="成功點擊 usb-cam，視頻預覽區域已顯示",
                    verification_items=verification_items
                )
            step_no += 1
            
            # 步驟 4: 驗證 video 播放狀態
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 驗證 video 播放狀態...")
            if not self.nx_cloud_web_page.verify_video_playback_status(timeout=20):
                error_msg = "驗證 video 播放狀態失敗"
                self.logger.error(f"[CASE_2-2] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="驗證 video 播放狀態",
                        status="fail",
                        message=error_msg
                    )
                raise AssertionError(f"[ERROR] {error_msg}")
            
            if reporter:
                verification_items = [
                    {"name": "Video 播放器"},
                    {"name": "播放控制按鈕"},
                    {"name": "視頻畫面區域"},
                    {"name": "播放狀態指示"}
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="驗證 video 播放狀態",
                    status="pass",
                    message="影片已載入完成且可播放，所有播放元素已驗證",
                    verification_items=verification_items
                )
            step_no += 1
            
            # 步驟 5: 等待影片播放 7 秒
            playback_wait_time = 7
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 等待影片播放 {playback_wait_time} 秒...")
            import time
            time.sleep(playback_wait_time)
            self.logger.info(f"[CASE_2-2] [OK] 已等待影片播放 {playback_wait_time} 秒")
            
            if reporter:
                verification_items = [
                    {"name": "Video 播放器"},
                    {"name": "播放進度"},
                    {"name": "播放時間顯示"},
                    {"name": "視頻畫面內容"}
                ]
                reporter.add_step(
                    step_no=step_no,
                    step_name="等待影片播放",
                    status="pass",
                    message=f"已等待影片播放 {playback_wait_time} 秒，播放狀態正常",
                    verification_items=verification_items
                )
            step_no += 1
            
            # 步驟 6: 關閉瀏覽器（Case 2-2 是最後一步，沒有後續步驟，需要關閉瀏覽器）
            self.logger.info(f"[CASE_2-2] 步驟 {step_no}: 關閉瀏覽器...")
            browser_closed = False
            try:
                # 🎯 使用 close_webdriver() 方法，它會執行系統級的 taskkill 來強制關閉 Chrome
                self.nx_cloud_web_page.close_webdriver()
                browser_closed = True
                self.logger.info("[CASE_2-2] [OK] 瀏覽器已關閉（通過 close_webdriver）")
                
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="關閉瀏覽器",
                        status="pass",
                        message="瀏覽器已成功關閉"
                    )
            except Exception as e:
                error_msg = f"關閉瀏覽器時發生錯誤: {e}"
                self.logger.error(f"[CASE_2-2] [ERROR] {error_msg}")
                if reporter:
                    reporter.add_step(
                        step_no=step_no,
                        step_name="關閉瀏覽器",
                        status="fail",
                        message=error_msg
                    )
                # 關閉瀏覽器失敗不影響測試結果，只記錄警告
                self.logger.warning("[CASE_2-2] [WARN] 關閉瀏覽器失敗，但測試繼續完成")
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_2-2] [ERROR] 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            # 即使失敗也嘗試關閉瀏覽器
            try:
                self.nx_cloud_web_page.close_webdriver()
            except:
                pass
            raise
        
        self.logger.info("✅ Case 2-2 完成：調閱一個錄影事件回放")
        return self