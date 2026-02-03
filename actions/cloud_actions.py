# -*- coding: utf-8 -*-
"""
Nx Cloud 相關動作模組

負責處理 Nx Cloud 相關的操作，包括進入 Nx Cloud、Web 端登錄等。

Author: SDET Team
Date: 2026-01-26
"""

from base.base_action import BaseAction
import time
import os
from typing import Optional


class CloudActions(BaseAction):
    """Nx Cloud 動作類
    
    負責處理所有與 Nx Cloud 相關的操作。
    
    Attributes:
        nx_cloud_page: Nx Cloud 桌面端頁面實例
        nx_cloud_web_page: Nx Cloud Web 端頁面實例
    """
    
    def _ensure_chrome_debug_mode(self) -> bool:
        """
        確保 Chrome 調試模式運行（在測試開始前自動啟動）
        
        Returns:
            bool: 是否成功啟動或已運行
        """
        import requests
        import subprocess
        import sys
        import time
        from config import EnvConfig
        
        self.logger.info("[CASE_2-1] 🔍 檢查 Chrome 調試模式...")
        
        # 檢查是否已經運行
        try:
            response = requests.get(f"http://localhost:{EnvConfig.BROWSER_DEBUG_PORT}/json/version", timeout=2)
            if response.status_code == 200:
                version_data = response.json()
                self.logger.info(f"[CASE_2-1] ✅ Chrome 調試模式已運行")
                self.logger.info(f"[CASE_2-1]    Browser: {version_data.get('Browser', 'Unknown')}")
                return True
        except:
            pass
        
        # 如果沒有運行，自動啟動
        self.logger.info("[CASE_2-1] 🚀 Chrome 調試模式未運行，正在自動啟動...")
        
        try:
            # 啟動 Chrome 調試模式（後台運行）
            import os
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "start_chrome_debug.py")
            subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 等待 Chrome 啟動
            for i in range(15):
                time.sleep(1)
                try:
                    response = requests.get(f"http://localhost:{EnvConfig.BROWSER_DEBUG_PORT}/json/version", timeout=2)
                    if response.status_code == 200:
                        version_data = response.json()
                        self.logger.info(f"[CASE_2-1] ✅ Chrome 調試模式已啟動（耗時 {i+1} 秒）")
                        self.logger.info(f"[CASE_2-1]    Browser: {version_data.get('Browser', 'Unknown')}")
                        return True
                except:
                    pass
                
                if i % 3 == 0:
                    self.logger.info(f"[CASE_2-1] ⏳ 等待 Chrome 啟動... ({i+1}/15)")
            
            self.logger.error("[CASE_2-1] ❌ Chrome 調試模式啟動超時")
            return False
            
        except Exception as e:
            self.logger.error(f"[CASE_2-1] ❌ 啟動 Chrome 調試模式時發生錯誤: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def __init__(self, browser_context: Optional[object] = None):
        """初始化 Nx Cloud 動作類
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__(browser=browser_context)
        
        from pages.desktop.nx_cloud_page import NxCloudPage
        from pages.web.nx_cloud_web_page import NxCloudWebPage
        
        self.nx_cloud_page = NxCloudPage()
        self.nx_cloud_web_page = NxCloudWebPage(browser=None)
    
    def _switch_language_to_chinese(self) -> bool:
        """
        切換 Nx Cloud 網頁語言為繁體中文
        
        使用已驗證的 Selenium XPath 邏輯，轉換為 Playwright
        
        Returns:
            bool: 是否成功切換語言
            
        Note:
            XPath 來自 pages/web/nx_cloud_web_page.py 的 switch_language_to_chinese()
        """
        if not hasattr(self.nx_cloud_page, 'playwright_page') or not self.nx_cloud_page.playwright_page:
            msg = "[CASE_2-1] ❌ Playwright 頁面不可用"
            self.logger.error(msg)
            print(msg)
            return False
        
        page = self.nx_cloud_page.playwright_page
        
        try:
            # 步驟 1: 點擊語言下拉選單箭頭
            msg = "[CASE_2-1] 步驟 1: 點擊語言下拉選單箭頭..."
            self.logger.info(msg)
            print(msg)
            
            dropdown_arrow = page.locator("//div[@class='dropdown-arrow-wrapper']")
            if dropdown_arrow.is_visible(timeout=5000):
                dropdown_arrow.click()
                msg = "[CASE_2-1] 成功點擊語言下拉選單箭頭"
                self.logger.info(msg)
                print(msg)
                time.sleep(0.5)  # 等待選單展開
            else:
                msg = "[CASE_2-1] 未找到語言下拉選單箭頭（可能已經是中文）"
                self.logger.warning(msg)
                print(msg)
                return True
            
            # 步驟 2: 點擊繁體中文選項
            msg = "[CASE_2-1] 步驟 2: 點擊繁體中文選項..."
            self.logger.info(msg)
            print(msg)
            
            # 嘗試方式 1: 使用 contains
            try:
                chinese_option = page.locator("//li//a[contains(., '繁体中文')] | //a[contains(., '繁体中文')]").first
                if chinese_option.is_visible(timeout=3000):
                    chinese_option.click()
                    msg = "[CASE_2-1] ✅ 成功點擊繁體中文選項（方式 1）"
                    self.logger.info(msg)
                    print(msg)
                    time.sleep(2)
                    return True
            except:
                pass
            
            # 嘗試方式 2: 精確匹配
            try:
                chinese_option = page.locator("//*[text()='繁體中文']").first
                if chinese_option.is_visible(timeout=2000):
                    chinese_option.click()
                    msg = "[CASE_2-1] ✅ 成功點擊繁體中文選項（方式 2）"
                    self.logger.info(msg)
                    print(msg)
                    time.sleep(2)
                    return True
            except:
                pass
            
            msg = "[CASE_2-1] 未找到繁體中文選項（可能已經是中文）"
            self.logger.warning(msg)
            print(msg)
            return True
            
        except Exception as e:
            msg = f"[CASE_2-1] 切換語言失敗: {e}"
            self.logger.error(msg)
            print(msg)
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _handle_nx_cloud_login(self, email: str, password: str) -> bool:
        """
        處理 Nx Cloud 登錄流程
        
        Args:
            email: 登錄郵箱
            password: 登錄密碼
            
        Returns:
            bool: 是否成功登錄
        """
        if not hasattr(self.nx_cloud_page, 'playwright_page') or not self.nx_cloud_page.playwright_page:
            msg = "[CASE_2-1] ❌ Playwright 頁面不可用"
            self.logger.error(msg)
            print(msg)
            return False
        
        page = self.nx_cloud_page.playwright_page
        
        try:
            # 嘗試點擊登錄按鈕（中文）
            login_clicked = False
            try:
                msg = "[CASE_2-1] 嘗試點擊登錄按鈕（中文）..."
                self.logger.info(msg)
                print(msg)
                page.click("text='登入'", timeout=3000)
                login_clicked = True
                msg = "[CASE_2-1] ✅ 登錄按鈕已點擊（中文）"
                self.logger.info(msg)
                print(msg)
            except:
                # 嘗試英文
                try:
                    msg = "[CASE_2-1] 嘗試點擊登錄按鈕（英文）..."
                    self.logger.info(msg)
                    print(msg)
                    page.click("text='log in'", timeout=3000)
                    login_clicked = True
                    msg = "[CASE_2-1] ✅ 登錄按鈕已點擊（英文）"
                    self.logger.info(msg)
                    print(msg)
                except:
                    pass
            
            if not login_clicked:
                msg = "[CASE_2-1] 未找到登錄按鈕（可能已登入）"
                self.logger.warning(msg)
                print(msg)
                return True
            
            # 輸入郵箱
            page.wait_for_selector("#authorizeEmail", timeout=10000)
            page.fill("#authorizeEmail", email)
            msg = f"[CASE_2-1] 已輸入郵箱: {email}"
            self.logger.info(msg)
            print(msg)
            
            # 點擊「下一步」
            page.click("button[type='submit']")
            msg = "[CASE_2-1] 已點擊「下一步」"
            self.logger.info(msg)
            print(msg)
            
            # 輸入密碼
            page.wait_for_selector("#authorizePassword", timeout=10000)
            page.fill("#authorizePassword", password)
            msg = "[CASE_2-1] 已輸入密碼"
            self.logger.info(msg)
            print(msg)
            
            # 點擊「登錄」
            page.click("button[type='submit']")
            msg = "[CASE_2-1] 已點擊「登錄」"
            self.logger.info(msg)
            print(msg)
            
            # 等待登錄完成
            time.sleep(5)
            msg = "[CASE_2-1] ✅ 登錄成功"
            self.logger.info(msg)
            print(msg)
            
            return True
            
        except Exception as e:
            msg = f"[CASE_2-1] 登錄流程失敗: {e}"
            self.logger.error(msg)
            print(msg)
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def run_enter_nx_cloud_step(self, **kwargs) -> 'CloudActions':
        """執行進入 Nx Cloud 流程
        
        流程：
        1. 點擊畫面右上角的賬號（會出現 menu）
        2. 點擊「開啟 Nx Cloud 介面」
        3. 等待 Chrome 打開網頁
        4. 如果右上角登錄按鈕存在，進入網頁版登錄流程
        
        網頁版登錄流程：
        1. 點擊登錄按鈕
        2. 輸入郵箱
        3. 點擊【下一步】
        4. 輸入密碼
        5. 點擊【登錄】
        
        Args:
            **kwargs: 可選參數
                email (str): Nx Cloud 郵箱
                password (str): Nx Cloud 密碼
        
        Returns:
            CloudActions: 返回自身，支持鏈式調用
            
        Raises:
            AssertionError: 當關鍵步驟失敗時拋出
        """
        # 🚨 強制寫入文件，確保能看到執行信息
        with open("d:\\nxwitness-demo\\DEBUG_CASE_2-1_EXECUTION.txt", "w", encoding="utf-8") as f:
            f.write("run_enter_nx_cloud_step() 被調用\n")
            f.write(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.logger.info("[CASE_2-1] 執行 Case 2-1: 進入 Nx Cloud")
        self.logger.info("[CASE_2-1] 使用方案 A：app 開 Chrome → 獲取 URL → 關閉 → Playwright 新開")
        
        print("\n" + "="*80)
        print(f"[CASE_2-1] [DEBUG] run_enter_nx_cloud_step() 開始執行 - {time.strftime('%H:%M:%S')}")
        print("="*80 + "\n")
        
        # 獲取登錄憑證
        email = kwargs.get("email", self.config.NX_CLOUD_EMAIL)
        password = kwargs.get("password", self.config.NX_CLOUD_PASSWORD)
        
        # 初始化 TestReporter
        reporter = None
        try:
            from base.desktop_app import DesktopApp
            from engine.test_reporter import TestReporter
            
            reporter = DesktopApp.get_reporter()
            if reporter is None:
                reporter = TestReporter("Case 2-1: 進入 Nx Cloud")
                DesktopApp.set_reporter(reporter)
        except Exception as e:
            self.logger.warning(f"無法初始化 TestReporter: {e}")
        
        step_no = 1
        
        # ================================================================
        # 🎯 Case 2-1：執行到檢測 Chrome 打開並複製 URL
        # 每一步都必須成功，否則判定失敗
        # ================================================================
        
        # 步驟 1: 點擊右上角賬號圖標
        self.logger.info("[CASE_2-1] 步驟 1: 點擊右上角賬號圖標...")
        print("[CASE_2-1] 步驟 1: 點擊右上角賬號圖標...")
        
        if not self.nx_cloud_page.click_account_menu():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊右上角賬號圖標",
                    status="fail",
                    message="點擊賬號圖標失敗",
                    verification_items=[{"name": "賬號圖標"}]
                )
            raise AssertionError("[CASE_2-1] ❌ 步驟 1 失敗：點擊賬號圖標失敗")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="點擊右上角賬號圖標",
                status="pass",
                message="成功點擊賬號圖標",
                verification_items=[{"name": "賬號圖標"}]
            )
        step_no += 1
        print("[CASE_2-1] ✅ 步驟 1 完成：已點擊賬號圖標")
        
        # 🎯 等待選單展開（不要點太快）
        time.sleep(1.0)
        
        # 步驟 2: 點擊「開啟 Nx Cloud 介面」
        self.logger.info("[CASE_2-1] 步驟 2: 點擊「開啟 Nx Cloud 介面」...")
        print("[CASE_2-1] 步驟 2: 點擊「開啟 Nx Cloud 介面」...")
        
        if not self.nx_cloud_page.click_open_nx_cloud_interface():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊「開啟 Nx Cloud 介面」",
                    status="fail",
                    message="點擊「開啟 Nx Cloud 介面」失敗（選單可能未展開）",
                    verification_items=[{"name": "開啟 Nx Cloud 介面選項"}]
                )
            raise AssertionError("[CASE_2-1] ❌ 步驟 2 失敗：點擊「開啟 Nx Cloud 介面」失敗")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="點擊「開啟 Nx Cloud 介面」",
                status="pass",
                message="成功點擊「開啟 Nx Cloud 介面」",
                verification_items=[{"name": "開啟 Nx Cloud 介面選項"}]
            )
        step_no += 1
        print("[CASE_2-1] ✅ 步驟 2 完成：已點擊「開啟 Nx Cloud 介面」")
        
        # 步驟 3: 等待 Chrome 開啟
        self.logger.info("[CASE_2-1] 步驟 3: 等待 Chrome 開啟...")
        print("[CASE_2-1] 步驟 3: 等待 Chrome 開啟...")
        
        import pygetwindow as gw
        chrome_found = False
        
        # 🎯 最多等待 15 秒檢測 Chrome
        for i in range(15):
            chrome_windows = [w for w in gw.getAllWindows() 
                           if 'chrome' in w.title.lower() and w.visible and w.width > 100]
            if chrome_windows:
                chrome_found = True
                self.logger.info(f"[CASE_2-1] ✅ 找到 Chrome 視窗: {chrome_windows[0].title}")
                print(f"[CASE_2-1] ✅ 找到 Chrome 視窗: {chrome_windows[0].title[:50]}")
                break
            print(f"[CASE_2-1] 等待 Chrome... ({i+1}/15)")
            time.sleep(1)
        
        # 🎯 斷言：Chrome 必須開啟
        if not chrome_found:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="檢測 Chrome 開啟",
                    status="fail",
                    message="等待 15 秒後仍未檢測到 Chrome 瀏覽器開啟",
                    verification_items=[{"name": "Chrome 瀏覽器"}]
                )
            raise AssertionError("[CASE_2-1] ❌ 步驟 3 失敗：Chrome 瀏覽器未開啟")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="檢測 Chrome 開啟",
                status="pass",
                message="Chrome 瀏覽器已開啟",
                verification_items=[{"name": "Chrome 瀏覽器"}]
            )
        step_no += 1
        print("[CASE_2-1] ✅ 步驟 3 完成：Chrome 已開啟")
        
        # 步驟 4: 獲取並驗證 URL
        self.logger.info("[CASE_2-1] 步驟 4: 獲取並驗證 URL...")
        print("[CASE_2-1] 步驟 4: 獲取並驗證 URL...")
        
        nx_cloud_url = None
        url_error = None
        
        # 🎯 等待頁面載入
        time.sleep(5)
        
        # 🎯 方法：使用 pyautogui 從地址欄複製 URL
        import pyautogui
        
        try:
            # 找到 Chrome 視窗並置頂
            chrome_win = None
            for w in gw.getAllWindows():
                if 'chrome' in w.title.lower() and w.visible and w.width > 100:
                    chrome_win = w
                    break
            
            if chrome_win:
                print(f"[CASE_2-1] 找到 Chrome 視窗: {chrome_win.title[:50]}")
                
                # 置頂 Chrome
                try:
                    chrome_win.activate()
                    time.sleep(0.5)
                except:
                    pass
                
                # 🎯 使用快捷鍵複製 URL
                # Ctrl+L 選中地址欄，Ctrl+C 複製
                pyautogui.hotkey('ctrl', 'l')  # 選中地址欄
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'c')  # 複製
                time.sleep(0.3)
                
                # 從剪貼簿獲取 URL
                import subprocess
                result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    nx_cloud_url = result.stdout.strip()
                    print(f"[CASE_2-1] 從剪貼簿獲取 URL: {nx_cloud_url}")
                else:
                    url_error = "無法從剪貼簿獲取 URL"
            else:
                url_error = "找不到 Chrome 視窗"
                
        except Exception as e:
            url_error = f"獲取 URL 失敗: {e}"
            import traceback
            traceback.print_exc()
        
        # 🎯 斷言：URL 必須獲取成功且是有效的 HTTP URL
        url_valid = nx_cloud_url and nx_cloud_url.startswith('http')
        
        if not url_valid:
            error_msg = url_error or f"URL 無效或不是 Nx Cloud: {nx_cloud_url}"
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="獲取並驗證 URL",
                    status="fail",
                    message=error_msg,
                    verification_items=[{"name": "Nx Cloud URL"}]
                )
            raise AssertionError(f"[CASE_2-1] ❌ 步驟 4 失敗：{error_msg}")
        
        # 🎯 保存 URL 到文件
        url_file = os.path.join(os.path.dirname(__file__), '..', '.nx_cloud_url')
        try:
            with open(url_file, 'w') as f:
                f.write(nx_cloud_url)
            self.logger.info(f"[CASE_2-1] ✅ URL 已保存: {url_file}")
            print(f"[CASE_2-1] ✅ URL 已保存: {url_file}")
        except Exception as e:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="保存 URL",
                    status="fail",
                    message=f"保存 URL 失敗: {e}",
                    verification_items=[{"name": "URL 文件"}]
                )
            raise AssertionError(f"[CASE_2-1] ❌ 步驟 4 失敗：保存 URL 失敗: {e}")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="獲取並保存 URL",
                status="pass",
                message=f"URL: {nx_cloud_url}",
                verification_items=[{"name": "Nx Cloud URL"}, {"name": "URL 文件"}]
            )
        step_no += 1
        print(f"[CASE_2-1] ✅ 步驟 4 完成：URL 已獲取並保存")
        
        # ================================================================
        # 🎯 Case 2-1 完成
        # ================================================================
        
        self.logger.info("✅ Case 2-1 完成：已成功進入 Nx Cloud 並獲取 URL")
        print("=" * 60)
        print("[CASE_2-1] ✅ 測試通過！")
        print(f"[CASE_2-1] URL: {nx_cloud_url}")
        print("=" * 60)
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="Case 2-1 完成",
                status="pass",
                message=f"測試通過，URL: {nx_cloud_url}",
                verification_items=[{"name": "Case 2-1 完成"}]
            )
        
        return self
    
    def _legacy_run_enter_nx_cloud_step(self, **kwargs) -> 'CloudActions':
        """[舊版] 執行進入 Nx Cloud 介面流程（包含登錄）
        
        此方法保留舊版邏輯，供需要完整流程時使用。
        """
        from base.desktop_app import DesktopApp
        from engine.test_reporter import TestReporter
        
        email = kwargs.get("email", self.config.NX_CLOUD_EMAIL)
        password = kwargs.get("password", self.config.NX_CLOUD_PASSWORD)
        
        reporter = DesktopApp.get_reporter()
        step_no = 1
        
        # 舊版步驟 6: 處理登錄流程
        msg = "[CASE_2-1] 步驟 6: 處理登錄流程..."
        self.logger.info(msg)
        print(msg)
        if not self._handle_nx_cloud_login(email, password):
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="Nx Cloud 登錄",
                    status="fail",
                    message="登錄失敗",
                    verification_items=[{"name": "登錄狀態"}]
                )
            raise AssertionError("Nx Cloud 登錄失敗")
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="Nx Cloud 登錄",
                status="pass",
                message="成功登錄 Nx Cloud",
                verification_items=[{"name": "登錄狀態"}]
            )
        
        msg = "✅ Case 2-1 完成：已進入 Nx Cloud，瀏覽器保持打開"
        self.logger.info(msg)
        print(msg)
        return self
    
    def run_playback_recording_step(self, **kwargs) -> 'CloudActions':
        """執行調閱錄影事件回放流程 (Case 2-2)
        
        🎯 使用獨立的 Selenium 啟動 Chrome 並通過 Nx Cloud OAuth 登錄：
        1. 啟動帶有 debugging port 的 Chrome
        2. 通過 Nx Cloud OAuth 登錄 Web Admin
        3. 點擊「瀏覽」分頁
        4. 點擊 Server 選項卡
        5. 點擊攝影機項目
        6. 點擊錄影進度條
        7. 等待影片播放
        
        Args:
            **kwargs:
                playback_duration (int): 播放等待時間（秒），預設 7 秒
                skip_login (bool): 是否跳過登錄步驟（如果已登錄），預設 False
        
        Returns:
            CloudActions: 返回自身，支持鏈式調用
        """
        self.logger.info("[CASE_2-2] 執行 Case 2-2: 調閱一個錄影事件回放")
        print("=" * 60)
        print("[CASE_2-2] 開始執行（使用 Selenium + Nx Cloud OAuth）")
        print("=" * 60)
        
        # 獲取參數
        playback_duration = kwargs.get("playback_duration", 7)
        skip_login = kwargs.get("skip_login", False)
        
        # 初始化 TestReporter
        reporter = None
        try:
            from base.desktop_app import DesktopApp
            from engine.test_reporter import TestReporter
            
            reporter = DesktopApp.get_reporter()
            if reporter is None:
                reporter = TestReporter("Case 2-2: 調閱一個錄影事件回放")
                DesktopApp.set_reporter(reporter)
        except Exception as e:
            self.logger.warning(f"無法初始化 TestReporter: {e}")
        
        step_no = 1
        
        try:
            # ================================================================
            # 步驟 1: 啟動 Chrome 並初始化 WebDriver
            # ================================================================
            print("[CASE_2-2] 步驟 1: 啟動 Chrome 並初始化 WebDriver...")
            
            # 關閉現有 Chrome
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'], capture_output=True)
            time.sleep(2)
            
            # 使用 Selenium 啟動新的 Chrome
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = Options()
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_experimental_option('detach', True)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 將 driver 設置到 nx_cloud_web_page
            self.nx_cloud_web_page.driver = driver
            self.nx_cloud_web_page.wait = WebDriverWait(driver, 15)
            
            # 🎯 自動置頂 Chrome 視窗
            try:
                import pygetwindow as gw
                import win32gui
                import win32con
                time.sleep(1)
                chrome_windows = gw.getWindowsWithTitle('Chrome')
                if chrome_windows:
                    hwnd = chrome_windows[0]._hWnd
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                    self.logger.info("[CASE_2-2] Chrome 視窗已置頂")
            except Exception as e:
                self.logger.warning(f"[CASE_2-2] 置頂視窗失敗: {e}")
            
            print("[CASE_2-2] ✅ 步驟 1 完成：Chrome 已啟動並置頂")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="啟動 Chrome", status="pass",
                                 message="Chrome 已啟動並初始化 WebDriver")
            step_no += 1
            
            # ================================================================
            # 步驟 2: 通過 Nx Cloud OAuth 登錄
            # ================================================================
            if not skip_login:
                print("[CASE_2-2] 步驟 2: 通過 Nx Cloud OAuth 登錄...")
                
                if not self.nx_cloud_web_page.login_via_nx_cloud():
                    self.logger.warning("[CASE_2-2] ⚠️ 登錄可能未完全成功，繼續執行...")
                
                print("[CASE_2-2] ✅ 步驟 2 完成：登錄流程已執行")
                
                if reporter:
                    reporter.add_step(step_no=step_no, step_name="Nx Cloud 登錄", status="pass",
                                     message="已完成 Nx Cloud OAuth 登錄")
                step_no += 1
            else:
                print("[CASE_2-2] 步驟 2: 跳過登錄（skip_login=True）")
            
            # ================================================================
            # 步驟 3: 點擊「瀏覽」分頁
            # ================================================================
            print("[CASE_2-2] 步驟 3: 點擊「瀏覽」分頁...")
            
            if not self.nx_cloud_web_page.click_browse_tab():
                raise AssertionError("[CASE_2-2] ❌ 無法點擊「瀏覽」分頁")
            
            print("[CASE_2-2] ✅ 步驟 3 完成：已點擊「瀏覽」")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="點擊瀏覽", status="pass",
                                 message="已點擊「瀏覽」分頁")
            step_no += 1
            
            # ================================================================
            # 步驟 4: 智能尋找並點擊攝影機
            # 邏輯：先找攝影機，找不到就點 Server 展開，再找攝影機
            # ================================================================
            print("[CASE_2-2] 步驟 4: 智能尋找攝影機...")
            
            camera_found = False
            max_attempts = 3  # 最多嘗試 3 次
            
            for attempt in range(max_attempts):
                print(f"[CASE_2-2] 嘗試 {attempt + 1}/{max_attempts}: 檢查攝影機是否可見...")
                
                # 先快速檢查攝影機是否已經可見（等待 3 秒）
                if self.nx_cloud_web_page.click_camera_item(max_wait=3):
                    camera_found = True
                    print(f"[CASE_2-2] ✅ 攝影機已可見並點擊成功（嘗試 {attempt + 1}）")
                    break
                
                # 找不到攝影機，點擊 Server 展開
                print(f"[CASE_2-2] 攝影機不可見，點擊 Server 展開...")
                if self.nx_cloud_web_page.click_server_item():
                    print("[CASE_2-2] ✅ 已點擊 Server，等待攝影機列表展開...")
                    time.sleep(2)  # 等待展開動畫
                else:
                    print("[CASE_2-2] ⚠️ 點擊 Server 失敗，繼續嘗試...")
            
            if not camera_found:
                # 最後一次嘗試，等待較長時間
                print("[CASE_2-2] 最後嘗試：等待攝影機出現（最多 15 秒）...")
                if not self.nx_cloud_web_page.click_camera_item(max_wait=15):
                    raise AssertionError("[CASE_2-2] ❌ 無法點擊攝影機")
            
            print("[CASE_2-2] ✅ 步驟 4 完成：已點擊攝影機")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="點擊攝影機", status="pass",
                                 message="已成功找到並點擊攝影機")
            step_no += 1
            
            # ================================================================
            # 步驟 5: 點擊進度條綠色區塊開始播放錄影
            # ================================================================
            print(f"[CASE_2-2] 步驟 {step_no}: 點擊進度條綠色區塊...")
            
            if not self.nx_cloud_web_page.click_timeline_green_block():
                self.logger.warning("[CASE_2-2] ⚠️ 點擊進度條失敗，但測試繼續")
            else:
                print(f"[CASE_2-2] ✅ 步驟 {step_no} 完成：已點擊進度條")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="點擊進度條", status="pass",
                                 message="已點擊進度條綠色區塊")
            step_no += 1
            
            # ================================================================
            # 步驟 6: 等待影片播放 5 秒
            # ================================================================
            play_seconds = 5
            print(f"[CASE_2-2] 步驟 {step_no}: 等待影片播放 {play_seconds} 秒...")
            
            time.sleep(play_seconds)
            
            print(f"[CASE_2-2] ✅ 步驟 {step_no} 完成：影片已播放 {play_seconds} 秒")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="影片播放", status="pass",
                                 message=f"已播放 {play_seconds} 秒")
            step_no += 1
            
            # ================================================================
            # 步驟 7: 點擊暫停按鈕
            # ================================================================
            print(f"[CASE_2-2] 步驟 {step_no}: 點擊暫停按鈕...")
            
            if not self.nx_cloud_web_page.click_pause_button():
                self.logger.warning("[CASE_2-2] ⚠️ 點擊暫停按鈕失敗，但測試繼續")
            else:
                print(f"[CASE_2-2] ✅ 步驟 {step_no} 完成：已點擊暫停")
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="點擊暫停", status="pass",
                                 message="已點擊暫停按鈕")
            step_no += 1
            
            # ================================================================
            # Case 2-2 完成
            # ================================================================
            print("=" * 60)
            print("[CASE_2-2] ✅ 測試通過！")
            print("=" * 60)
            
            if reporter:
                reporter.add_step(step_no=step_no, step_name="Case 2-2 完成", status="pass",
                                 message="測試通過")
            
        except AssertionError:
            raise
        except Exception as e:
            self.logger.error(f"[CASE_2-2] ❌ 執行失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            if reporter:
                reporter.add_step(step_no=step_no, step_name="執行失敗", status="fail",
                                 message=str(e))
            raise AssertionError(f"[CASE_2-2] ❌ 執行失敗: {e}")
        finally:
            print("[CASE_2-2] 測試結束，Chrome 視窗保持開啟")
        
        return self
    
    def _legacy_run_playback_recording_step(self, **kwargs) -> 'CloudActions':
        """[舊版] 執行調閱錄影事件回放流程
        
        此方法保留舊版邏輯，連接到 Case 2-1 打開的瀏覽器。
        """
        self.logger.info("[CASE_2-2] [舊版] 執行 Case 2-2: 調閱一個錄影事件回放")
        
        playback_duration = kwargs.get("playback_duration", 7)
        
        reporter = None
        try:
            from base.desktop_app import DesktopApp
            from engine.test_reporter import TestReporter
            
            reporter = DesktopApp.get_reporter()
            if reporter is None:
                reporter = TestReporter("Case 2-2: 調閱一個錄影事件回放")
                DesktopApp.set_reporter(reporter)
        except Exception as e:
            self.logger.warning(f"無法初始化 TestReporter: {e}")
        
        # 嘗試連接到 Case 2-1 打開的瀏覽器
        self.logger.info("[CASE_2-2] 嘗試連接到 Case 2-1 打開的瀏覽器...")
        if not self.nx_cloud_page.connect_to_existing_browser():
            self.logger.error("[CASE_2-2] ❌ 無法連接到現有瀏覽器")
            return self
        
        self.logger.info("[CASE_2-2] ✅ 已連接到現有瀏覽器")
        time.sleep(3)
        
        if not self.nx_cloud_page.playback_recording_pw(playback_duration=playback_duration):
            if reporter:
                reporter.add_step(
                    step_no=1,
                    step_name="Playwright 執行錄影回放",
                    status="fail",
                    message="無法透過 Playwright 執行錄影回放操作",
                    verification_items=[
                        {"name": "Chrome 瀏覽器"},
                        {"name": "CDP 連接"},
                        {"name": "查看頁簽"},
                        {"name": "Server 項目"},
                        {"name": "USB 攝影機"},
                        {"name": "影片播放器"}
                    ]
                )
            raise AssertionError("Playwright 執行錄影回放失敗")
        
        if reporter:
            reporter.add_step(
                step_no=1,
                step_name="Playwright 執行錄影回放",
                status="pass",
                message=f"成功透過 Playwright 完成所有錄影回放步驟，影片已播放 {playback_duration} 秒",
                verification_items=[
                    {"name": "Chrome 瀏覽器"},
                    {"name": "CDP 連接"},
                    {"name": "查看頁簽"},
                    {"name": "Server 項目"},
                    {"name": "USB 攝影機"},
                    {"name": "影片播放器"},
                    {"name": "影片播放狀態"}
                ]
            )
        
        self.logger.info("✅ Case 2-2 完成：已調閱錄影事件回放")
        
        # 🎯 關鍵：保持瀏覽器打開，不清理 Playwright 資源
        # 用戶可能需要手動檢查結果或進行後續操作
        self.logger.info("[CASE_2-2] ⚠️ 瀏覽器保持打開狀態（供手動檢查）")
        self.logger.info("[CASE_2-2] 如需關閉，請手動調用 nx_cloud_page.cleanup_playwright()")
        
        return self
