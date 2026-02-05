# 相對路徑: actions/nx_mobile_actions.py
"""
Nx Witness 移動端自動化操作類

處理 Test Case 4-1 和 4-2 的移動端測試流程
支持兩種模式：
1. Appium/UiAutomator2 模式（原有方式）
2. ADB + 圖像識別模式（更穩定）

報告功能：
- 每個 Page 方法調用都會記錄檢核點
- 截圖中標記點擊位置（綠色十字準星）
- 匹配到的物件用紅框標出
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional
from base.base_action import BaseAction
from toolkit.logger import get_logger
from toolkit.adb_toolkit import AdbController, find_image_on_screen, find_color_region, BLUE_BUTTON
from config import EnvConfig


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
            driver: Appium WebDriver 實例（未使用，Android 測試使用 ADB 方式）
        """
        super().__init__(browser=None)  # 移動端不使用 browser
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)
    
    def set_driver(self, driver: object) -> 'NxMobileActions':
        """
        設置 Appium WebDriver 實例（未使用，Android 測試使用 ADB 方式）
        
        Args:
            driver: Appium WebDriver 實例
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        self.driver = driver
        return self
    
    def run_login_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-1: 登錄到 Nx Cloud (對應 Excel FlowName: login_mobile)
        
        使用 ADB + 圖像識別方式，繞過不穩定的 Appium/UiAutomator2
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數（此步驟無參數）
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
            
        Raises:
            AssertionError: 如果登錄失敗
        """
        # 直接調用 ADB 方式的登錄流程
        return self.run_login_step_adb(**kwargs)
    
    def run_login_step_adb(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-1: 使用 ADB + 圖像識別登錄
        
        業務流程（Action 層職責）：
        1. 檢測頁面狀態（已登錄則跳過）
        2. 點擊 Log In 按鈕
        3. 輸入 Email
        4. 點擊 Next
        5. 輸入密碼
        6. 點擊 Log In 完成登錄
        
        報告功能：
        - 每個步驟都記錄檢核點
        - 截圖標記點擊位置
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        from pages.mobile.adb_login_page import AdbLoginPage
        from base.desktop_app import DesktopApp
        
        start_time = time.time()
        
        # 獲取 Reporter（由 test_runner.py 創建並註冊）
        reporter = DesktopApp.get_reporter()
        # 獲取當前步驟編號基準
        step_no = len(reporter.steps) if reporter and hasattr(reporter, 'steps') else 0
        
        def log_step(msg: str):
            """輸出日誌並刷新"""
            print(f">>> [CASE_4-1] {msg}")
            sys.stdout.flush()
        
        log_step("=" * 50)
        log_step("開始執行登錄流程")
        log_step("=" * 50)
        
        # 初始化 Page Object
        adb = AdbController()
        login_page = AdbLoginPage(adb)
        
        if not adb.is_connected():
            raise AssertionError("[ERROR] 未找到已連接的 Android 設備")
        
        width, height = login_page.screen_size
        log_step(f"螢幕尺寸: {width} x {height}")
        
        email = EnvConfig.NX_CLOUD_EMAIL
        password = EnvConfig.NX_CLOUD_PASSWORD
        log_step(f"使用帳號: {email}")
        
        # 截圖目錄
        screenshot_dir = reporter.screenshot_dir if reporter else os.path.join(os.getcwd(), "report", "diagnostics")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        try:
            # ========== 步驟 1: 檢測頁面狀態 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 檢測頁面狀態...")
            
            screenshot_path = os.path.join(screenshot_dir, f"step_{step_no:03d}_detect_state.png")
            login_page.take_screenshot(screenshot_path)
            page_state = login_page.detect_page_state(screenshot_path)
            log_step(f"  當前頁面狀態: {page_state}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="檢測頁面狀態",
                    status="pass",
                    message=f"頁面狀態: {page_state}",
                    screenshot_path=screenshot_path
                )
            
            if page_state == 'logged_in':
                log_step("已經登錄，無需重複登錄")
                return self
            
            # ========== 步驟 2: 進入登錄流程 ==========
            # 策略：先嘗試找 Login 按鈕，找不到就點擊左上角人像圖標
            step_no += 1
            log_step(f"步驟 {step_no}: 進入登錄流程...")
            
            # 左上角人像圖標位置（備用入口）
            avatar_x, avatar_y = int(width * 0.10), int(height * 0.07)  # 約 (108, 168) for 1080x2400
            
            button = login_page.find_blue_button(screenshot_path)
            if button:
                # 找到 Login 按鈕，直接點擊
                click_x, click_y = button
                element_name = "Log In 按鈕"
                log_step(f"  找到 Log In 按鈕: ({click_x}, {click_y})")
            else:
                # 沒有 Login 按鈕，點擊左上角人像圖標
                click_x, click_y = avatar_x, avatar_y
                element_name = "左上角人像圖標"
                log_step(f"  未找到 Log In 按鈕，點擊人像圖標: ({click_x}, {click_y})")
            
            # 截圖並標記點擊位置
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_entry.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, element_name)
            
            adb.tap(click_x, click_y)
            log_step(f"  已點擊 {element_name} ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="進入登錄流程",
                    status="pass",
                    message=f"點擊 {element_name}: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # 等待頁面內容加載（等待藍色按鈕出現，表示頁面已加載完成）
            log_step("  等待頁面內容加載...")
            
            max_wait_content = 15  # 最多等待 15 秒
            content_loaded = False
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_content:
                time.sleep(1)
                temp_screenshot = os.path.join(screenshot_dir, "wait_content.png")
                adb.screenshot(temp_screenshot)
                
                # 檢查是否有藍色按鈕（主要判斷標準）
                check_button = login_page.find_blue_button(temp_screenshot)
                if check_button:
                    log_step(f"  找到按鈕 {check_button}，頁面已加載")
                    content_loaded = True
                    break
                
                # 只有在找不到按鈕時，才檢查頁面狀態
                # 這避免了空白頁面被誤判為 logged_in
                log_step(f"  等待中... ({time.time() - wait_start:.1f}s)")
            
            if not content_loaded:
                # 最後一次檢查是否已登錄（有搜索框且有內容）
                final_check = os.path.join(screenshot_dir, "final_content_check.png")
                adb.screenshot(final_check)
                final_state = login_page.detect_page_state(final_check)
                if final_state == 'logged_in':
                    final_button = login_page.find_blue_button(final_check)
                    if not final_button:  # 確認沒有登錄按鈕才認為真正已登錄
                        log_step(f"  已登錄（無登錄按鈕），無需繼續")
                        return self
                log_step("  [WARN] 等待頁面內容超時，繼續嘗試")
            
            # 如果點擊的是人像圖標，可能會出現選單，需要再找 Login 按鈕
            if not button:
                log_step("  檢查是否出現登錄選項...")
                menu_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_menu.png")
                adb.screenshot(menu_screenshot)
                
                menu_button = login_page.find_blue_button(menu_screenshot)
                if menu_button:
                    step_no += 1
                    click_x, click_y = menu_button
                    log_step(f"  找到 Log In 選項: ({click_x}, {click_y})")
                    
                    marked_screenshot2 = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_login.png")
                    self._take_marked_screenshot_adb(adb, marked_screenshot2, click_x, click_y, "Log In 選項")
                    
                    adb.tap(click_x, click_y)
                    log_step(f"  已點擊 Log In 選項")
                    
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="點擊 Log In 選項",
                            status="pass",
                            message=f"點擊座標: ({click_x}, {click_y})",
                            screenshot_path=marked_screenshot2
                        )
                    
                    # 再次等待頁面加載
                    time.sleep(2)
            
            # 智能等待 Email 頁面出現
            log_step("  智能等待 Email 頁面加載...")
            
            # 額外驗證：確認 Email 頁面已出現（檢測特徵）
            max_wait_email = 25  # 最多等待 25 秒
            email_page_ready = False
            wait_start = time.time()
            retry_count = 0
            
            while time.time() - wait_start < max_wait_email:
                check_screenshot = os.path.join(screenshot_dir, "check_email_page.png")
                adb.screenshot(check_screenshot)
                
                # 先檢查是否有藍色按鈕（基本加載標誌）
                check_button = login_page.find_blue_button(check_screenshot)
                if not check_button:
                    log_step(f"  頁面加載中（無按鈕）...")
                    time.sleep(1)
                    continue
                
                page_state = login_page.detect_page_state(check_screenshot)
                log_step(f"  檢測頁面狀態: {page_state}, 按鈕: {check_button}")
                
                if page_state == 'email_input':
                    email_page_ready = True
                    log_step(f"  Email 頁面已就緒")
                    break
                elif page_state == 'logged_in':
                    log_step(f"  已登錄，無需繼續")
                    return self
                elif page_state == 'login_page':
                    # 還在初始登錄頁，嘗試再點一次 Login 按鈕
                    retry_count += 1
                    if retry_count <= 3:
                        log_step(f"  仍在初始登錄頁，嘗試點擊 Log In (第 {retry_count} 次)...")
                        retry_button = login_page.find_blue_button(check_screenshot)
                        if retry_button:
                            adb.tap(retry_button[0], retry_button[1])
                            time.sleep(2)
                    else:
                        log_step(f"  [WARN] 多次重試後仍在登錄頁")
                
                time.sleep(1)
            
            if not email_page_ready:
                # 最後一次截圖記錄
                fail_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_timeout.png")
                adb.screenshot(fail_screenshot)
                if reporter:
                    reporter.add_step(
                        step_no=step_no + 1,
                        step_name="等待 Email 頁面超時",
                        status="fail",
                        message=f"等待 {max_wait_email} 秒後頁面仍未加載",
                        screenshot_path=fail_screenshot
                    )
                raise AssertionError(f"等待 Email 頁面超時（{max_wait_email}秒），頁面未正確加載")
            
            # ========== 步驟 3: 輸入 Email ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 輸入 Email...")
            log_step(f"  [DEBUG] Email 長度: {len(email)}")
            
            email_x, email_y = width // 2, int(height * 0.46)
            log_step(f"  [DEBUG] Email 輸入框座標: ({email_x}, {email_y})")
            
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_input_email.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, email_x, email_y, "Email 輸入框")
            
            # 點擊 Email 輸入框
            log_step(f"  [DEBUG] 點擊 Email 輸入框...")
            adb.tap(email_x, email_y, wait=0.5)
            
            # 按 ESC 關閉自動填寫推薦框（如果有）
            log_step(f"  [DEBUG] 按 ESC 關閉自動填寫框...")
            adb.run_cmd(['shell', 'input', 'keyevent', '111'], silent=True)  # KEYCODE_ESCAPE
            time.sleep(0.2)
            
            # 按返回鍵關閉鍵盤（如果有）
            log_step(f"  [DEBUG] 按返回鍵關閉鍵盤...")
            adb.run_cmd(['shell', 'input', 'keyevent', '4'], silent=True)  # KEYCODE_BACK
            time.sleep(0.3)
            
            # 再次點擊 Email 輸入框，確保焦點
            log_step(f"  [DEBUG] 再次點擊 Email 輸入框確保焦點...")
            adb.tap(email_x, email_y, wait=0.3)
            
            # 使用 ADB 強制清空並輸入 Email（避免自動填寫干擾）
            log_step(f"  [DEBUG] 清空 Email 輸入框...")
            for _ in range(30):  # Email 可能較長，多刪除幾次
                adb.run_cmd(['shell', 'input', 'keyevent', '67'], silent=True)  # KEYCODE_DEL
                time.sleep(0.02)
            
            log_step(f"  [DEBUG] 開始逐字符輸入 Email...")
            for i, char in enumerate(email):
                escaped_char = char.replace('\\', '\\\\').replace('"', '\\"')
                adb.run_cmd(['shell', 'input', 'text', escaped_char], silent=True)
                time.sleep(0.05)
                
                if (i + 1) % 10 == 0:  # 每 10 個字符記錄一次進度
                    log_step(f"  [DEBUG] 已輸入 {i+1}/{len(email)} 個字符")
            
            log_step(f"  [DEBUG] Email 輸入完成（共 {len(email)} 個字符）")
            log_step(f"  已輸入: {email}")
            time.sleep(0.5)
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="輸入 Email",
                    status="pass",
                    message=f"輸入: {email}",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 4: 點擊 Next ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊 Next 按鈕...")
            
            adb.tap(width // 2, int(height * 0.15), wait=0.5)  # 關閉鍵盤
            
            temp_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_temp.png")
            adb.screenshot(temp_screenshot)
            button = login_page.find_blue_button(temp_screenshot)
            
            if button:
                click_x, click_y = button
            else:
                click_x, click_y = int(width * 0.82), int(height * 0.61)
            
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_next.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "Next 按鈕")
            
            adb.tap(click_x, click_y)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊 Next 按鈕",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # 使用固定等待（智能等待在密碼頁面容易超時）
            log_step("  等待密碼頁面加載（3秒）...")
            time.sleep(3)
            log_step(f"  [DEBUG] 等待完成，準備輸入密碼")
            
            # ========== 步驟 5: 輸入密碼 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 輸入密碼...")
            log_step(f"  [DEBUG] 密碼長度: {len(password)}")
            
            password_x, password_y = width // 2, int(height * 0.47)
            log_step(f"  [DEBUG] 密碼輸入框座標: ({password_x}, {password_y})")
            
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_input_password.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, password_x, password_y, "密碼輸入框")
            log_step(f"  [DEBUG] 已保存標記截圖: {marked_screenshot}")
            
            # 點擊密碼輸入框
            log_step(f"  [DEBUG] 點擊密碼輸入框...")
            adb.tap(password_x, password_y, wait=0.5)
            
            # 按 ESC 鍵關閉自動填寫推薦框（如果有）
            log_step(f"  [DEBUG] 按 ESC 鍵關閉自動填寫推薦框...")
            adb.run_cmd(['shell', 'input', 'keyevent', '111'], silent=True)  # KEYCODE_ESCAPE
            time.sleep(0.3)
            
            # 按返回鍵關閉鍵盤（如果有）
            log_step(f"  [DEBUG] 按返回鍵關閉鍵盤...")
            adb.run_cmd(['shell', 'input', 'keyevent', '4'], silent=True)  # KEYCODE_BACK
            time.sleep(0.3)
            
            # 再次點擊密碼輸入框，確保焦點在輸入框
            log_step(f"  [DEBUG] 再次點擊密碼輸入框確保焦點...")
            adb.tap(password_x, password_y, wait=0.3)
            
            # 使用 ADB 強制輸入密碼（逐字符輸入，避免被自動填寫干擾）
            log_step(f"  [DEBUG] 使用 ADB 強制輸入密碼（逐字符）...")
            try:
                # 先清空可能存在的內容
                for _ in range(20):  # 最多刪除 20 個字符
                    adb.run_cmd(['shell', 'input', 'keyevent', '67'], silent=True)  # KEYCODE_DEL
                    time.sleep(0.02)
                
                log_step(f"  [DEBUG] 開始逐字符輸入密碼...")
                # 逐字符輸入密碼
                for i, char in enumerate(password):
                    # 使用 ADB 直接輸入字符（不會被自動填寫框干擾）
                    escaped_char = char.replace('\\', '\\\\').replace('"', '\\"')
                    adb.run_cmd(['shell', 'input', 'text', escaped_char], silent=True)
                    time.sleep(0.05)  # 每個字符之間稍微等待
                    
                    if (i + 1) % 5 == 0:  # 每 5 個字符記錄一次進度
                        log_step(f"  [DEBUG] 已輸入 {i+1}/{len(password)} 個字符")
                
                log_step(f"  [DEBUG] 密碼輸入完成（共 {len(password)} 個字符）")
            except Exception as e:
                log_step(f"  [ERROR] 密碼輸入失敗: {e}")
                import traceback
                log_step(f"  [ERROR] 詳細錯誤: {traceback.format_exc()}")
            
            log_step(f"  已輸入密碼")
            
            # 等待一下讓輸入生效
            time.sleep(0.5)
            
            # 使用 VLM 驗證是否成功輸入密碼（檢查是否還在密碼頁面）
            log_step(f"  [DEBUG] 使用 VLM 驗證密碼輸入狀態...")
            verify_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_verify_password.png")
            adb.screenshot(verify_screenshot)
            
            # 檢查是否還在密碼頁面（如果還在，說明密碼沒有成功輸入）
            still_on_password_page = self._check_still_on_password_page(verify_screenshot)
            
            if still_on_password_page:
                log_step(f"  [WARN] VLM 檢測到仍在密碼頁面，密碼可能未成功輸入，重試一次...")
                
                # 重試：再次點擊密碼輸入框並輸入密碼
                log_step(f"  [RETRY] 重新點擊密碼輸入框...")
                adb.tap(password_x, password_y, wait=0.3)
                
                # 再次關閉可能的干擾
                log_step(f"  [RETRY] 關閉自動填寫框和鍵盤...")
                adb.run_cmd(['shell', 'input', 'keyevent', '111'], silent=True)  # ESC
                time.sleep(0.2)
                adb.run_cmd(['shell', 'input', 'keyevent', '4'], silent=True)  # BACK
                time.sleep(0.3)
                adb.tap(password_x, password_y, wait=0.3)
                
                # 清空並重新輸入
                log_step(f"  [RETRY] 清空輸入框...")
                for _ in range(20):
                    adb.run_cmd(['shell', 'input', 'keyevent', '67'], silent=True)
                    time.sleep(0.02)
                
                log_step(f"  [RETRY] 重新輸入密碼...")
                for i, char in enumerate(password):
                    escaped_char = char.replace('\\', '\\\\').replace('"', '\\"')
                    adb.run_cmd(['shell', 'input', 'text', escaped_char], silent=True)
                    time.sleep(0.05)
                
                log_step(f"  [RETRY] 密碼重新輸入完成")
                time.sleep(0.5)
                
                # 再次驗證
                verify_screenshot2 = os.path.join(screenshot_dir, f"step_{step_no:03d}_verify_password_retry.png")
                adb.screenshot(verify_screenshot2)
                still_on_password_page2 = self._check_still_on_password_page(verify_screenshot2)
                
                if still_on_password_page2:
                    log_step(f"  [ERROR] 重試後仍在密碼頁面，密碼輸入失敗")
                    if reporter:
                        reporter.add_step(
                            step_no=step_no,
                            step_name="輸入密碼（失敗）",
                            status="fail",
                            message="兩次嘗試後仍無法輸入密碼",
                            screenshot_path=verify_screenshot2
                        )
                    raise Exception("密碼輸入失敗：兩次嘗試後仍在密碼頁面")
                else:
                    log_step(f"  [OK] 重試成功，已離開密碼頁面")
            else:
                log_step(f"  [OK] VLM 確認已離開密碼頁面，密碼輸入成功")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="輸入密碼",
                    status="pass",
                    message="密碼已輸入並驗證",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 6: 點擊 Log In ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊 Log In 登錄...")
            
            adb.tap(width // 2, int(height * 0.125), wait=1.0)  # 關閉鍵盤
            
            temp_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_temp.png")
            adb.screenshot(temp_screenshot)
            button = login_page.find_blue_button(temp_screenshot)
            
            if button:
                click_x, click_y = button
            else:
                click_x, click_y = int(width * 0.82), int(height * 0.61)
            
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_login_final.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "Log In 按鈕")
            
            adb.tap(click_x, click_y)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊 Log In 登錄",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            log_step("  智能等待登錄完成...")
            adb.wait_for_page_stable(timeout=15.0, check_interval=0.5, stability_threshold=0.98)
            
            # ========== 步驟 7: 驗證登錄結果 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 驗證登錄結果...")
            
            # 等待登錄完成
            time.sleep(3)
            
            final_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_login_result.png")
            adb.screenshot(final_screenshot)
            
            final_state = login_page.detect_page_state(final_screenshot)
            is_success = (final_state == 'logged_in')
            
            log_step(f"  登錄狀態: {final_state}, 成功: {is_success}")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="驗證登錄結果",
                    status="pass" if is_success else "fail",
                    message=f"登錄狀態: {final_state}" + ("" if is_success else " - 登錄失敗！"),
                    screenshot_path=final_screenshot
                )
            
            total_elapsed = time.time() - start_time
            log_step("=" * 50)
            
            if not is_success:
                log_step(f"[FAIL] 登錄失敗！最終狀態: {final_state}")
                log_step("=" * 50)
                raise AssertionError(f"登錄失敗！最終頁面狀態: {final_state}，預期: logged_in")
            
            log_step(f"[OK] 登錄成功 [總耗時: {total_elapsed:.2f}s]")
            log_step("=" * 50)
            
            return self
            
        except Exception as e:
            self.logger.error(f"[CASE_4-1] 執行失敗: {e}")
            if reporter:
                error_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_error.png")
                try:
                    adb.screenshot(error_screenshot)
                except:
                    pass
                reporter.add_step(
                    step_no=step_no,
                    step_name="執行失敗",
                    status="fail",
                    message=str(e),
                    screenshot_path=error_screenshot if os.path.exists(error_screenshot) else None
                )
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] ADB 登錄流程執行失敗: {e}")
    
    def _take_marked_screenshot_adb(
        self,
        adb: AdbController,
        save_path: str,
        click_x: int,
        click_y: int,
        element_name: str
    ):
        """
        使用 ADB 截圖並標記點擊位置
        
        Args:
            adb: ADB 控制器
            save_path: 保存路徑
            click_x: 點擊 X 座標
            click_y: 點擊 Y 座標
            element_name: 元素名稱
        """
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        
        try:
            temp_path = tempfile.mktemp(suffix='.png')
            adb.screenshot(temp_path)
            
            img = Image.open(temp_path)
            draw = ImageDraw.Draw(img)
            
            # 繪製十字準星
            cross_size = 25
            draw.line([(click_x - cross_size, click_y), (click_x + cross_size, click_y)], 
                      fill='lime', width=4)
            draw.line([(click_x, click_y - cross_size), (click_x, click_y + cross_size)], 
                      fill='lime', width=4)
            
            # 繪製圓點
            circle_radius = 10
            draw.ellipse(
                [click_x - circle_radius, click_y - circle_radius,
                 click_x + circle_radius, click_y + circle_radius],
                fill='lime', outline='green', width=2
            )
            
            # 標註文字
            try:
                font = ImageFont.truetype("arial.ttf", 28)
            except:
                font = ImageFont.load_default()
            
            label = f"{element_name} ({click_x}, {click_y})"
            text_bbox = draw.textbbox((click_x + 20, click_y - 40), label, font=font)
            draw.rectangle(
                [text_bbox[0] - 4, text_bbox[1] - 4, text_bbox[2] + 4, text_bbox[3] + 4],
                fill='lime'
            )
            draw.text((click_x + 20, click_y - 40), label, fill='black', font=font)
            
            img.save(save_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            # 如果標記失敗，至少保存原始截圖
            try:
                adb.screenshot(save_path)
            except:
                pass
    
    def run_select_server_and_camera_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 選擇服務器和攝像頭 (對應 Excel FlowName: select_server_and_camera)
        
        使用 SmartLocator 智能定位，優先圖像/亮度識別，Fallback 使用配置座標。
        
        步驟：
        1. 點擊 Server 卡片
        2. 等待連接
        3. 點擊影片縮圖（智能亮度檢測）
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        import sys
        from toolkit.adb_toolkit import SmartLocator
        
        print(f">>> [CASE_4-2] [智能定位] 執行選擇服務器和攝像頭...")
        sys.stdout.flush()
        
        try:
            from config import EnvConfig
            
            adb = AdbController()
            locator = SmartLocator(adb)
            
            # Fallback 座標
            server_fallback = EnvConfig.CASE4_2_SERVER_CLICK_COORDINATES
            thumbnail_fallback = EnvConfig.CASE4_2_THUMBNAIL_CLICK_COORDINATES
            gotit_fallback = EnvConfig.CASE4_2_FULLSCREEN_GOTIT_COORDINATES
            
            # 步驟 1: 點擊 Server 卡片
            print(f">>> [CASE_4-2] 步驟 1: 點擊 Server 卡片 {server_fallback}...")
            sys.stdout.flush()
            adb.tap(server_fallback[0], server_fallback[1], wait=1)
            
            # 步驟 2: 等待連接完成（Connecting... 結束，縮略圖出現）
            # 原理：Connecting 畫面是深色的，連接完成後會顯示亮色的縮略圖
            print(f">>> [CASE_4-2] 步驟 2: 等待連接完成（Connecting...）...")
            sys.stdout.flush()
            
            # 等待縮略圖區域出現亮色內容（超時 30 秒）
            adb.wait_for_thumbnail(
                region=(0, 200, 600, 400),  # 縮略圖大約在這個區域
                min_brightness=40,           # 亮度閾值
                timeout=30.0,                # 最長等待 30 秒
                check_interval=1.0           # 每秒檢查一次
            )
            
            # 額外等待，確保頁面穩定
            time.sleep(1)
            
            # 步驟 3: 點擊影片縮圖進入播放畫面
            print(f">>> [CASE_4-2] 步驟 3: 點擊影片縮圖 {thumbnail_fallback}...")
            sys.stdout.flush()
            adb.tap(thumbnail_fallback[0], thumbnail_fallback[1], wait=1)
            
            # 等待影片播放畫面加載
            print(f">>> [CASE_4-2] 智能等待影片播放畫面...")
            sys.stdout.flush()
            adb.wait_for_page_stable(timeout=8.0, check_interval=0.5, stability_threshold=0.98)
            
            # 處理可能的全屏提示 "Got it"
            print(f">>> [CASE_4-2] 處理全屏提示（如有）...")
            adb.tap(gotit_fallback[0], gotit_fallback[1], wait=1)
            
            print(f">>> [CASE_4-2] [OK] 選擇服務器和攝像頭完成")
            sys.stdout.flush()
            return self
            
        except Exception as e:
            print(f">>> [CASE_4-2] [FAIL] 選擇服務器和攝像頭失敗: {e}")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 選擇服務器和攝像頭失敗: {e}")
    
    def run_playback_with_calendar_step(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2 (部分): 使用日曆控件播放錄製的視頻
        
        對應 Excel FlowName: playback_with_calendar
        
        業務流程（Action 層職責）：
        1. 點擊日曆圖標 → 打開日曆視圖
        2. 點擊有錄影的日期 → 開始播放
        3. 等待播放 5 秒
        4. 點擊暫停按鈕 → 暫停播放
        
        原子操作委託給 Page 層 (AdbPlaybackPage)
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
        
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        import sys
        from pages.mobile.adb_playback_page import AdbPlaybackPage
        
        print(f">>> [CASE_4-2] 執行日曆播放流程...")
        sys.stdout.flush()
        
        start_time = time.time()
        
        try:
            # 初始化 Page Object（原子操作封裝在 Page 層）
            playback_page = AdbPlaybackPage()
            
            # === 步驟 1: 點擊日曆圖標 ===
            print(f">>> [CASE_4-2] 步驟 1: 點擊日曆圖標")
            sys.stdout.flush()
            if not playback_page.tap_calendar_icon(wait=2):
                raise Exception("點擊日曆圖標失敗")
            
            # === 步驟 2: 點擊有錄影的日期 ===
            print(f">>> [CASE_4-2] 步驟 2: 點擊有錄影日期")
            sys.stdout.flush()
            if not playback_page.tap_recording_date(wait=3):
                raise Exception("點擊日期失敗")
            
            # === 步驟 3: 播放錄影 ===
            print(f">>> [CASE_4-2] 步驟 3: 播放 5 秒...")
            sys.stdout.flush()
            time.sleep(5)
            
            # === 步驟 4: 暫停播放 ===
            print(f">>> [CASE_4-2] 步驟 4: 點擊暫停按鈕")
            sys.stdout.flush()
            if not playback_page.tap_pause_button(wait=1):
                raise Exception("點擊暫停按鈕失敗")
            
            # 保存結果截圖
            result_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report", "case_4_2_result.png")
            playback_page.take_screenshot(result_path)
            
            elapsed = time.time() - start_time
            print(f">>> [CASE_4-2] [總耗時: {elapsed:.2f}s] [OK] 完成")
            sys.stdout.flush()
            
            return self
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f">>> [CASE_4-2] [總耗時: {elapsed:.2f}s] [FAIL] {e}")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] 日曆播放流程失敗: {e}")
    
    def run_playback_step_adb(self, **kwargs) -> 'NxMobileActions':
        """
        Test Case 4-2: 使用 ADB + 圖像識別播放錄製視頻
        
        業務流程：
        1. 點擊 Server 選項卡
        2. 等待連接完成
        3. 點擊縮圖打開影片
        4. 點擊日曆圖標
        5. 點擊有綠線的日期
        6. 播放 5 秒後點暫停
        
        報告功能：
        - 每個步驟都記錄檢核點
        - 截圖標記點擊位置
        
        Args:
            **kwargs: 從 Excel TestPlan 傳入的參數
            
        Returns:
            NxMobileActions: 返回自身以支持鏈式調用
        """
        from pages.mobile.adb_playback_page import AdbPlaybackPage
        from base.desktop_app import DesktopApp
        
        start_time = time.time()
        
        # 獲取 Reporter（由 test_runner.py 創建並註冊）
        reporter = DesktopApp.get_reporter()
        # 獲取當前步驟編號基準
        step_no = len(reporter.steps) if reporter and hasattr(reporter, 'steps') else 0
        
        def log_step(msg: str):
            """輸出日誌並刷新"""
            print(f">>> [CASE_4-2] {msg}")
            sys.stdout.flush()
        
        log_step("=" * 50)
        log_step("開始執行播放流程")
        log_step("=" * 50)
        
        # 初始化 Page Object
        adb = AdbController()
        playback_page = AdbPlaybackPage(adb)
        width, height = adb.get_screen_size()
        log_step(f"螢幕尺寸: {width} x {height}")
        
        # 截圖目錄
        screenshot_dir = reporter.screenshot_dir if reporter else os.path.join(os.getcwd(), "report", "diagnostics")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # 從 config 讀取座標配置
        server_coords = EnvConfig.CASE4_2_SERVER_CLICK_COORDINATES
        thumbnail_coords = EnvConfig.CASE4_2_THUMBNAIL_CLICK_COORDINATES
        gotit_coords = EnvConfig.CASE4_2_FULLSCREEN_GOTIT_COORDINATES
        calendar_coords = EnvConfig.CASE4_2_CALENDAR_ICON_COORDINATES
        today_coords = EnvConfig.CASE4_2_TODAY_DATE_COORDINATES
        pause_coords = EnvConfig.CASE4_2_PAUSE_BUTTON_COORDINATES
        show_controls_coords = EnvConfig.CASE4_2_SHOW_CONTROLS_TAP
        
        try:
            # ========== 步驟 1: 點擊 Server 選項卡 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊 Server 選項卡...")
            
            click_x, click_y = server_coords
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_server.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "Server 選項卡")
            
            adb.tap(click_x, click_y, wait=1)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊 Server 選項卡",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 2: 等待連接完成 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 等待連接完成...")
            
            # 等待縮略圖出現
            adb.wait_for_thumbnail(
                region=(0, 200, 600, 400),
                min_brightness=40,
                timeout=30.0,
                check_interval=1.0
            )
            time.sleep(1)
            
            connect_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_connected.png")
            adb.screenshot(connect_screenshot)
            log_step(f"  連接完成")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="等待連接完成",
                    status="pass",
                    message="連接成功，縮略圖已顯示",
                    screenshot_path=connect_screenshot
                )
            
            # ========== 步驟 3: 點擊影片縮圖 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊影片縮圖...")
            
            click_x, click_y = thumbnail_coords
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_thumbnail.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "影片縮圖")
            
            adb.tap(click_x, click_y, wait=3)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            # 處理全屏提示
            time.sleep(1)
            adb.tap(gotit_coords[0], gotit_coords[1], wait=1)
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊影片縮圖",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 4: 顯示控制欄 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 顯示控制欄...")
            
            click_x, click_y = show_controls_coords
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_show_controls.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "顯示控制欄")
            
            adb.tap(click_x, click_y, wait=0.5)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="顯示控制欄",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 5: 點擊日曆圖標 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊日曆圖標...")
            
            click_x, click_y = calendar_coords
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_calendar.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "日曆圖標")
            
            adb.tap(click_x, click_y, wait=2)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊日曆圖標",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 6: 點擊有錄影的日期 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊有錄影的日期...")
            
            time.sleep(1)
            temp_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_temp.png")
            adb.screenshot(temp_screenshot)
            
            # 查找綠色日期
            green_date = playback_page.find_green_date_in_calendar(temp_screenshot)
            if green_date:
                click_x, click_y = green_date[0], green_date[1] - 20
                log_step(f"  找到綠色日期: {green_date}")
            else:
                click_x, click_y = today_coords
                log_step(f"  使用預設日期座標: ({click_x}, {click_y})")
            
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_date.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "錄影日期")
            
            adb.tap(click_x, click_y, wait=3)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊有錄影的日期",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y}), 綠色日期: {green_date if green_date else '未找到'}",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 7: 播放 5 秒 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 播放 5 秒...")
            
            play_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_playing.png")
            adb.screenshot(play_screenshot)
            
            time.sleep(5)
            log_step(f"  播放完成")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="播放 5 秒",
                    status="pass",
                    message="播放 5 秒完成",
                    screenshot_path=play_screenshot
                )
            
            # ========== 步驟 8: 顯示控制欄並暫停 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 點擊暫停按鈕...")
            
            # 先顯示控制欄
            adb.tap(show_controls_coords[0], show_controls_coords[1], wait=0.3)
            
            click_x, click_y = pause_coords
            marked_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_click_pause.png")
            self._take_marked_screenshot_adb(adb, marked_screenshot, click_x, click_y, "暫停按鈕")
            
            adb.tap(click_x, click_y, wait=1)
            log_step(f"  已點擊 ({click_x}, {click_y})")
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊暫停按鈕",
                    status="pass",
                    message=f"點擊座標: ({click_x}, {click_y})",
                    screenshot_path=marked_screenshot
                )
            
            # ========== 步驟 9: 驗證暫停結果 ==========
            step_no += 1
            log_step(f"步驟 {step_no}: 驗證暫停結果...")
            
            final_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_final_result.png")
            adb.screenshot(final_screenshot)
            
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="驗證暫停結果",
                    status="pass",
                    message="播放流程完成",
                    screenshot_path=final_screenshot
                )
            
            elapsed = time.time() - start_time
            log_step("=" * 50)
            log_step(f"播放流程完成 [總耗時: {elapsed:.2f}s]")
            log_step("=" * 50)
            
            return self
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[CASE_4-2] 執行失敗: {e}")
            
            if reporter:
                error_screenshot = os.path.join(screenshot_dir, f"step_{step_no:03d}_error.png")
                try:
                    adb.screenshot(error_screenshot)
                except:
                    pass
                reporter.add_step(
                    step_no=step_no,
                    step_name="執行失敗",
                    status="fail",
                    message=str(e),
                    screenshot_path=error_screenshot if os.path.exists(error_screenshot) else None
                )
            
            import traceback
            traceback.print_exc()
            raise AssertionError(f"[ERROR] Case 4-2 播放流程失敗: {e}")
    
    def _check_still_on_password_page(self, screenshot_path: str) -> bool:
        """
        使用 VLM 檢查是否還在密碼輸入頁面
        
        Args:
            screenshot_path: 截圖路徑
            
        Returns:
            bool: True 表示還在密碼頁面，False 表示已離開
        """
        try:
            from toolkit.vlm_engine import UnifiedVLM
            
            vlm = UnifiedVLM()
            
            # 構建 VLM 提示詞
            prompt = """請分析這個手機應用截圖，判斷當前是否在密碼輸入頁面。

判斷標準：
1. 如果畫面中有「Password」或「密碼」輸入框 → 回答 YES
2. 如果畫面中有「Enter password」或「輸入密碼」提示 → 回答 YES
3. 如果畫面顯示的是 Cloud 列表、Server 列表或其他頁面 → 回答 NO
4. 如果畫面顯示「Connecting」或「連接中」→ 回答 NO

請只回答 YES 或 NO，不需要其他說明。"""

            response = vlm.find_element_by_text(screenshot_path, "Password", prompt)
            
            if response and isinstance(response, dict):
                # 檢查回應中是否包含 YES
                answer = str(response.get('answer', '')).upper()
                self.logger.info(f"[VLM_VERIFY] VLM 回應: {answer}")
                return 'YES' in answer
            
            # 如果 VLM 失敗，保守策略：假設不在密碼頁面（避免無限重試）
            self.logger.warning(f"[VLM_VERIFY] VLM 驗證失敗，假設密碼已輸入")
            return False
            
        except Exception as e:
            self.logger.warning(f"[VLM_VERIFY] VLM 驗證時發生異常: {e}")
            # 異常時保守策略：假設不在密碼頁面
            return False
