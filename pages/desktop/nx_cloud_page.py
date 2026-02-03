# 相對路徑: pages/desktop/nx_cloud_page.py

from base.desktop_app import DesktopApp
from config import EnvConfig
from toolkit.browser_manager import BrowserManager
import time
import os
import atexit
import pygetwindow as gw
import pyautogui
import pyperclip
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from typing import Optional

# 🎯 全局變量：保持 BrowserManager 實例（防止被垃圾回收）
_GLOBAL_BROWSER_MANAGER: Optional[BrowserManager] = None


class NxCloudPage(DesktopApp):
    """
    Nx Cloud 桌面端操作頁面處理類
    
    處理 Case 2-1 的桌面端操作：
    1. 點擊畫面右上角的賬號（會出現 menu）
    2. 點擊「開啟 Nx Cloud 介面」
    3. 等待 Chrome 視窗出現
    
    持久化策略（比照 Selenium）：
    - 使用類別屬性保存 Playwright 實例
    - 防止函數結束時被垃圾回收
    - 確保瀏覽器在測試結束後保持運行
    """
    
    # ============================================================================
    # 🎯 類別屬性：持久化 Playwright 實例（比照 Selenium 的 WebDriver 管理）
    # ============================================================================
    # 
    # 教學說明：為什麼使用類別屬性？
    # 
    # Selenium 的 detach 模式：
    #   options = ChromeOptions()
    #   options.add_experimental_option("detach", True)
    #   driver = webdriver.Chrome(options=options)
    #   # 測試結束後，driver 進程不會被關閉
    # 
    # Playwright 的對應實現：
    #   1. 使用類別屬性保存 Playwright 實例（_global_pw）
    #   2. 類別屬性的生命週期 = 類別的生命週期 = 程序運行期間
    #   3. Python 垃圾回收器不會回收類別屬性引用的對象
    #   4. 因此 Playwright 進程和瀏覽器進程都不會被關閉
    # 
    # 關鍵原理：
    #   - 局部變數：函數結束 → 引用計數 = 0 → 垃圾回收 → 進程終止
    #   - 類別屬性：程序結束才清理 → 引用計數 > 0 → 不會被垃圾回收 → 進程保持運行
    # 
    # 這就是為什麼「持有實例」+ 「不調用 stop()」= Selenium 的 detach 功能
    # ============================================================================
    
    _global_pw = None        # Playwright 實例（對應 Selenium 的 WebDriver）
    _browser = None          # Browser 實例（CDP 連接）- 🎯 關鍵：必須保存到類別變數
    _global_context = None   # BrowserContext 實例（持久化會話）
    _global_page = None      # Page 實例（當前頁面）
    _browser_detached = False  # 標記瀏覽器是否已脫離控制
    _atexit_registered = False  # 標記是否已註冊 atexit 處理函數
    
    @classmethod
    def _prevent_browser_cleanup(cls):
        """
        防止 Python 退出時關閉瀏覽器（atexit 處理函數）
        
        ========================================================================
        教學說明：為什麼需要 atexit？
        ========================================================================
        
        問題：
        - Python 程序退出時會調用所有對象的 __del__() 方法
        - BrowserContext.__del__() 會關閉瀏覽器進程
        - 即使我們保存了類別屬性，程序退出時仍然會清理
        
        解決方案：
        - 使用 atexit 註冊清理函數
        - 在 Python 清理對象前執行
        - 通過保持引用來阻止瀏覽器被關閉
        
        關鍵：
        - 這個函數在程序退出時自動執行
        - 不需要手動調用
        - 保持對 context 的引用，防止被垃圾回收
        ========================================================================
        """
        if cls._browser_detached and cls._global_context:
            print("\n" + "=" * 80)
            print("[ATEXIT] 🔒 Python 程序即將退出")
            print("[ATEXIT] 💡 瀏覽器已脫離控制，將保持運行")
            print(f"[ATEXIT] 💡 Context 引用仍然存在: {cls._global_context is not None}")
            print("[ATEXIT] 💡 這等同於 Selenium 的 detach=True 功能")
            print("=" * 80 + "\n")
            
            # 🎯 關鍵：保持引用，阻止垃圾回收
            # 不要設為 None，保持對 context 的引用
            # 這樣 __del__() 就不會被調用
    
    def __init__(self):
        super().__init__()
    
    def click_account_menu(self) -> bool:
        """
        點擊畫面右上角的賬號（會出現 menu）
        
        Returns:
            bool: 點擊是否成功
        """
        import pyautogui
        import pygetwindow as gw
        
        print("=" * 50)
        print("[STEP 1] 點擊賬號圖標 - 開始")
        print("=" * 50)
        
        # 🎯 直接查找視窗（不調用 get_nx_window 避免重複置頂）
        win = None
        for title in ["Nx Witness Client", "Nx Witness"]:
            try:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible and w.width > 800]
                if wins:
                    win = wins[0]
                    break
            except:
                continue
        
        if not win:
            print("[STEP 1] ❌ 無法找到 Nx Witness 視窗")
            return False
        
        print(f"[STEP 1] 找到視窗: {win.title}")
        print(f"[STEP 1] 視窗位置: left={win.left}, top={win.top}")
        print(f"[STEP 1] 視窗大小: {win.width}x{win.height}")
        
        # 🎯 置頂視窗
        self._force_window_to_front(win)
        time.sleep(0.5)
        
        # 🎯 計算賬號圖標座標
        x = win.left + int(win.width * 0.85)
        y = win.top + int(win.height * 0.02)
        
        print(f"[STEP 1] 賬號圖標座標: ({x}, {y})")
        print(f"[STEP 1] >>> 執行點擊 <<<")
        
        # 🎯 點擊
        pyautogui.click(x, y, clicks=1)
        
        print(f"[STEP 1] ✅ 點擊完成")
        print("=" * 50)
        
        # 保存窗口信息供下一步使用
        self._cached_window = win
        
        time.sleep(1.5)  # 等待選單展開
        return True
    
    def _force_window_to_front(self, win) -> int:
        """
        強力將視窗置頂（繞過 Windows 的前台限制）
        
        Args:
            win: pygetwindow 視窗對象
            
        Returns:
            int: 視窗句柄 (hwnd)，失敗返回 0
        """
        try:
            import win32gui
            import win32con
            import win32api
            import ctypes
            
            # 獲取視窗句柄
            hwnd = win32gui.FindWindow(None, win.title)
            if not hwnd:
                print(f"[NX_CLOUD] [WARN] 找不到視窗句柄: {win.title}")
                return 0
            
            print(f"[NX_CLOUD] [DEBUG] 視窗句柄: {hwnd}")
            
            # 如果最小化，先還原
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)
            
            # 🎯 方法 1: 使用 SetWindowPos 設為 TOPMOST
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            
            # 🎯 方法 2: 使用 keybd_event 模擬 Alt 鍵（繞過前台限制）
            ALT = 0x12
            KEYEVENTF_EXTENDEDKEY = 0x0001
            KEYEVENTF_KEYUP = 0x0002
            
            ctypes.windll.user32.keybd_event(ALT, 0, KEYEVENTF_EXTENDEDKEY, 0)
            win32gui.SetForegroundWindow(hwnd)
            ctypes.windll.user32.keybd_event(ALT, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            
            # 🎯 方法 3: BringWindowToTop
            win32gui.BringWindowToTop(hwnd)
            
            # 🎯 方法 4: 取消 TOPMOST（避免永久置頂）
            time.sleep(0.1)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_NOTOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
            
            print("[NX_CLOUD] [OK] 視窗已強力置頂")
            return hwnd
            
        except ImportError as e:
            print(f"[NX_CLOUD] [WARN] 缺少 win32gui 模組: {e}")
            try:
                win.activate()
                print("[NX_CLOUD] [OK] 使用 pygetwindow 激活")
            except:
                pass
            return 0
        except Exception as e:
            print(f"[NX_CLOUD] [WARN] 強力置頂失敗: {e}")
            return 0
    
    def click_open_nx_cloud_interface(self) -> bool:
        """
        點擊「開啟 Nx Cloud 介面」選單項目
        
        Returns:
            bool: 點擊是否成功
        """
        import pyautogui
        import pygetwindow as gw
        
        print("=" * 50)
        print("[STEP 2] 點擊選單項目 - 開始")
        print("=" * 50)
        
        # 🎯 使用緩存的視窗（避免調用 get_nx_window 觸發重複置頂）
        win = getattr(self, '_cached_window', None)
        if not win:
            print("[STEP 2] 緩存視窗不存在，重新查找...")
            for title in ["Nx Witness Client", "Nx Witness"]:
                try:
                    wins = [w for w in gw.getWindowsWithTitle(title) if w.visible and w.width > 800]
                    if wins:
                        win = wins[0]
                        break
                except:
                    continue
        
        if not win:
            print("[STEP 2] ❌ 無法找到視窗")
            return False
        
        print(f"[STEP 2] 視窗: {win.title}")
        print(f"[STEP 2] 視窗位置: left={win.left}, top={win.top}")
        print(f"[STEP 2] 視窗大小: {win.width}x{win.height}")
        
        # 🎯 計算選單項目座標
        # 選單第一項在賬號圖標下方約 40-50px
        account_y = win.top + int(win.height * 0.02)
        menu_x = win.left + int(win.width * 0.85)
        menu_y = account_y + 35  # 🎯 在賬號圖標下方 35px
        
        print(f"[STEP 2] 賬號圖標 Y: {account_y}")
        print(f"[STEP 2] 選單項目座標: ({menu_x}, {menu_y})")
        print(f"[STEP 2] Y 軸差距: {menu_y - account_y}px")
        print(f"[STEP 2] >>> 執行點擊 <<<")
        
        # 🎯 點擊
        pyautogui.click(menu_x, menu_y, clicks=1)
        
        print(f"[STEP 2] ✅ 點擊完成")
        print("=" * 50)
        
        return True
    
    def wait_for_chrome_window(self, timeout=15) -> bool:
        """
        等待 Chrome 視窗出現（點擊「開啟 Nx Cloud 介面」後會自動打開）
        
        Args:
            timeout: 超時時間（秒，預設 15 秒，給 Chrome 更多時間打開）
        
        Returns:
            bool: 是否找到 Chrome 視窗
        """
        self.logger.info(f"[NX_CLOUD] [WAIT] 等待 Chrome 視窗出現（點擊後會自動打開，超時: {timeout} 秒）...")
        
        start_time = time.time()
        check_count = 0
        while time.time() - start_time < timeout:
            try:
                check_count += 1
                # 查找 Chrome 視窗（使用多種標題匹配）
                chrome_wins = []
                
                # 嘗試多種 Chrome 視窗標題
                possible_titles = [
                    "Chrome",
                    "Google Chrome",
                    "Nx Cloud",
                    "Cloud Portal",
                    "新分頁",  # 新標籤頁（繁體中文）
                    "New Tab"  # 新標籤頁（英文）
                ]
                
                for title in possible_titles:
                    try:
                        wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                        chrome_wins.extend(wins)
                    except:
                        continue
                
                # 去重（根據視窗標題和位置）
                unique_wins = []
                seen = set()
                for win in chrome_wins:
                    try:
                        key = (win.title, win.left, win.top)
                        if key not in seen:
                            seen.add(key)
                            unique_wins.append(win)
                    except:
                        continue
                
                # 🔍 診斷：每 10 次檢查輸出一次狀態
                if check_count % 10 == 0:
                    elapsed = time.time() - start_time
                    self.logger.info(f"[NX_CLOUD] [WAIT] 檢查 Chrome 視窗中... (已等待 {elapsed:.1f}s, 找到 {len(unique_wins)} 個視窗)")
                    if unique_wins:
                        for idx, win in enumerate(unique_wins[:3]):  # 只顯示前 3 個
                            self.logger.info(f"[NX_CLOUD] [WAIT]   [{idx+1}] '{win.title}' ({win.width}x{win.height})")
                
                if unique_wins:
                    # 選擇最大的 Chrome 視窗
                    chrome_win = max(unique_wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                    self.logger.info(f"[NX_CLOUD] [OK] 找到 Chrome 視窗: '{chrome_win.title}' ({chrome_win.width}x{chrome_win.height})")
                    
                    # 🔍 診斷：檢查這個 Chrome 是否是我們啟動的（帶調試端口）
                    import requests
                    try:
                        response = requests.get(f"http://localhost:{EnvConfig.BROWSER_DEBUG_PORT}/json/version", timeout=2)
                        if response.status_code == 200:
                            self.logger.info(f"[NX_CLOUD] [OK] ✅ Chrome 調試端口 {EnvConfig.BROWSER_DEBUG_PORT} 可訪問")
                        else:
                            self.logger.warning(f"[NX_CLOUD] [WARN] ⚠️ Chrome 調試端口返回狀態碼: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        self.logger.error(f"[NX_CLOUD] [ERROR] ❌ Chrome 調試端口 {EnvConfig.BROWSER_DEBUG_PORT} 無法連接！")
                        self.logger.error(f"[NX_CLOUD] [ERROR] 這個 Chrome 可能不是我們啟動的（沒有調試端口）")
                        self.logger.error(f"[NX_CLOUD] [ERROR] 請先運行: python start_chrome_debug.py")
                    except Exception as e:
                        self.logger.warning(f"[NX_CLOUD] [WARN] 檢查調試端口時發生錯誤: {e}")
                    
                    return True
                
                time.sleep(0.5)
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD] 檢查 Chrome 視窗時發生異常: {e}")
                time.sleep(0.5)
        
        self.logger.error(f"[NX_CLOUD] [ERROR] 等待 Chrome 視窗超時（{timeout} 秒）")
        self.logger.error(f"[NX_CLOUD] [ERROR] 總共檢查了 {check_count} 次，未找到 Chrome 視窗")
        return False
    
    def get_current_browser_url(self, close_window: bool = False, max_retries: int = 5) -> str:
        """
        [Desktop] 從當前活動的瀏覽器視窗獲取 URL
        
        策略：
        1. 快速嘗試獲取 URL（不等待）
        2. 如果失敗，重試最多 max_retries 次
        3. 每次重試間隔 0.3 秒
        
        Args:
            close_window: 是否在獲取 URL 後關閉瀏覽器視窗，默認為 False
            max_retries: 最大重試次數，默認 5 次
        
        Returns:
            str: 獲取到的 URL，如果失敗則返回 None
        """
        self.logger.info("[NX_CLOUD] [GET_URL] 快速獲取瀏覽器 URL...")
        
        for attempt in range(max_retries):
            try:
                # 🎯 優化：減少等待時間，快速嘗試
                if attempt == 0:
                    time.sleep(0.5)  # 第一次只等 0.5 秒
                else:
                    time.sleep(0.3)  # 重試時等 0.3 秒
                
                # 模擬鍵盤操作：Ctrl+L (聚焦網址列)
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.2)
                
                # 模擬鍵盤操作：Ctrl+C (複製網址)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.2)
                
                # 從剪貼簿讀取
                url = pyperclip.paste()
                if url and "http" in url:
                    self.logger.info(f"[NX_CLOUD] [GET_URL] ✅ 成功獲取 URL (嘗試 {attempt + 1}/{max_retries}): {url}")
                    
                    # 關閉視窗（如果需要）
                    if close_window:
                        pyautogui.hotkey('ctrl', 'w')
                        time.sleep(0.5)
                    
                    return url
                else:
                    self.logger.debug(f"[NX_CLOUD] [GET_URL] 嘗試 {attempt + 1}/{max_retries} 失敗，剪貼簿內容: {url}")
                    
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD] [GET_URL] 嘗試 {attempt + 1}/{max_retries} 發生異常: {e}")
        
        self.logger.error(f"[NX_CLOUD] [GET_URL] ❌ 獲取 URL 失敗（已重試 {max_retries} 次）")
        return None
    
    def close_chrome_window(self) -> bool:
        """
        關閉 Chrome 視窗
        
        Returns:
            bool: 是否成功關閉
        """
        self.logger.info("[NX_CLOUD] [CLOSE] 關閉 Chrome 視窗...")
        
        try:
            import pygetwindow as gw
            
            # 查找 Chrome 窗口
            chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
            
            if not chrome_windows:
                self.logger.warning("[NX_CLOUD] [CLOSE] 沒有找到 Chrome 視窗")
                return True  # 沒有窗口也算成功
            
            # 關閉所有 Chrome 窗口
            for win in chrome_windows:
                try:
                    self.logger.info(f"[NX_CLOUD] [CLOSE] 關閉視窗: {win.title}")
                    win.close()
                except Exception as e:
                    self.logger.warning(f"[NX_CLOUD] [CLOSE] 關閉視窗失敗: {e}")
            
            self.logger.info(f"[NX_CLOUD] [CLOSE] ✅ 已關閉 {len(chrome_windows)} 個 Chrome 視窗")
            return True
            
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [CLOSE] 關閉 Chrome 視窗時發生錯誤: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def click_view_tab_pw(self, target_page) -> bool:
        """
        [Playwright] 點擊「查看」頁簽
        
        Args:
            target_page: Playwright Page 實例
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD] [PW] 點擊「查看」頁簽...")
        
        try:
            # 使用 Playwright 的文本選擇器,更簡潔
            view_tab = target_page.locator("div.menu-items div.outer-menu-item:has-text('查看') a.anchor")
            view_tab.click(timeout=10000)
            self.logger.info("[NX_CLOUD] [PW] ✅ 成功點擊「查看」頁簽")
            target_page.wait_for_timeout(1500)
            return True
        except PlaywrightTimeoutError:
            self.logger.error("[NX_CLOUD] [PW] ❌ 等待「查看」頁簽超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PW] ❌ 點擊「查看」頁簽失敗: {e}")
            return False
    
    def click_server_pw(self, target_page) -> bool:
        """
        [Playwright] 點擊 server 元素
        
        Args:
            target_page: Playwright Page 實例
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD] [PW] 點擊 server...")
        
        try:
            # 使用 CSS 選擇器
            server = target_page.locator("div.server.online")
            server.click(timeout=10000)
            self.logger.info("[NX_CLOUD] [PW] ✅ 成功點擊 server")
            target_page.wait_for_timeout(1500)
            return True
        except PlaywrightTimeoutError:
            self.logger.error("[NX_CLOUD] [PW] ❌ 等待 server 元素超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PW] ❌ 點擊 server 失敗: {e}")
            return False
    
    def click_usb_cam_pw(self, target_page) -> bool:
        """
        [Playwright] 點擊 usb-cam 元素
        
        Args:
            target_page: Playwright Page 實例
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD] [PW] 點擊 usb-cam...")
        
        try:
            # 使用文本選擇器,更靈活
            usb_cam = target_page.locator("span:has(nx-search-highlight:has-text('usb_cam'))")
            usb_cam.click(timeout=10000)
            self.logger.info("[NX_CLOUD] [PW] ✅ 成功點擊 usb-cam")
            target_page.wait_for_timeout(1500)
            return True
        except PlaywrightTimeoutError:
            self.logger.error("[NX_CLOUD] [PW] ❌ 等待 usb-cam 元素超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PW] ❌ 點擊 usb-cam 失敗: {e}")
            return False
    
    def verify_video_playback_pw(self, target_page, timeout: int = 20) -> bool:
        """
        [Playwright] 驗證頁面上的 <video> 元素是否載入完成且可播放
        
        Args:
            target_page: Playwright Page 實例
            timeout: 等待超時時間 (秒)
        
        Returns:
            bool: 影片是否載入成功且可播放
        """
        self.logger.info(f"[NX_CLOUD] [PW] 檢查影片載入狀態 (Timeout: {timeout}s)...")
        
        try:
            # 等待 video 元素出現
            video_locator = target_page.locator("video").first
            video_locator.wait_for(state="attached", timeout=timeout * 1000)
            
            # 使用 JavaScript 檢查影片狀態
            start_time = time.time()
            while time.time() - start_time < timeout:
                video_status = target_page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (!video) return null;
                        return {
                            readyState: video.readyState,
                            duration: video.duration,
                            error: video.error,
                            paused: video.paused,
                            currentTime: video.currentTime
                        };
                    }
                """)
                
                if not video_status:
                    self.logger.warning("[NX_CLOUD] [PW] video 元素不存在")
                    time.sleep(0.5)
                    continue
                
                # 檢查影片是否準備好
                ready_state = video_status.get('readyState', 0)
                duration = video_status.get('duration', 0)
                error = video_status.get('error')
                
                self.logger.info(f"[NX_CLOUD] [PW] Video 狀態: readyState={ready_state}, duration={duration}, error={error}")
                
                # readyState >= 3 且 duration > 0 且無錯誤
                if ready_state >= 3 and duration > 0 and not error:
                    self.logger.info("[NX_CLOUD] [PW] ✅ 影片已載入完成且可播放")
                    return True
                
                time.sleep(0.5)
            
            self.logger.error(f"[NX_CLOUD] [PW] ❌ 影片載入超時 ({timeout}s)")
            return False
            
        except PlaywrightTimeoutError:
            self.logger.error("[NX_CLOUD] [PW] ❌ 等待 video 元素超時")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PW] ❌ 驗證影片播放狀態失敗: {e}")
            return False
    
    def launch_independent_chrome_and_connect(self, url: str) -> tuple:
        """
        啟動獨立的 Chrome 進程並用 Playwright 連接
        
        這樣做的好處：
        1. Chrome 進程獨立運行，不會因為 Python 進程退出而被終止
        2. 可以跨測試共享同一個瀏覽器實例
        
        Args:
            url: 要訪問的 URL
            
        Returns:
            tuple: (playwright_instance, browser, context, page)
        """
        from playwright.sync_api import sync_playwright
        import subprocess
        import random
        import time
        
        self.logger.info(f"[PLAYWRIGHT] 啟動獨立 Chrome 並連接到 URL: {url}")
        
        try:
            # 1. 啟動獨立的 Chrome 進程（使用 DETACHED_PROCESS）
            debug_port = random.randint(9222, 9299)
            
            # 查找 Chrome 可執行文件
            import shutil
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                shutil.which("chrome"),
                shutil.which("google-chrome"),
            ]
            
            chrome_exe = None
            for path in chrome_paths:
                if path and os.path.exists(path):
                    chrome_exe = path
                    break
            
            if not chrome_exe:
                self.logger.error("[PLAYWRIGHT] ❌ 找不到 Chrome 可執行文件")
                return (None, None, None, None)
            
            self.logger.info(f"[PLAYWRIGHT] Chrome 路徑: {chrome_exe}")
            self.logger.info(f"[PLAYWRIGHT] CDP 端口: {debug_port}")
            
            # 啟動 Chrome（使用 DETACHED_PROCESS 讓它獨立運行）
            import sys
            if sys.platform == 'win32':
                # Windows: 使用 DETACHED_PROCESS
                DETACHED_PROCESS = 0x00000008
                chrome_process = subprocess.Popen(
                    [
                        chrome_exe,
                        f'--remote-debugging-port={debug_port}',
                        '--no-first-run',
                        '--no-default-browser-check',
                        url
                    ],
                    creationflags=DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Linux/Mac
                chrome_process = subprocess.Popen(
                    [
                        chrome_exe,
                        f'--remote-debugging-port={debug_port}',
                        '--no-first-run',
                        '--no-default-browser-check',
                        url
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            self.logger.info(f"[PLAYWRIGHT] Chrome 進程已啟動 (PID: {chrome_process.pid})")
            
            # 2. 等待 Chrome 啟動
            time.sleep(3)
            
            # 3. 用 Playwright 連接到 Chrome（保存到類別變數）
            if NxCloudPage._global_pw is None:
                NxCloudPage._global_pw = sync_playwright().start()
            
            NxCloudPage._browser = NxCloudPage._global_pw.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            
            # 4. 獲取 context 和 page
            contexts = NxCloudPage._browser.contexts
            if not contexts:
                # 創建新 context（使用 no_viewport=True）
                context = NxCloudPage._browser.new_context(ignore_https_errors=True, no_viewport=True)
                page = context.new_page()
                page.goto(url, timeout=30000)
            else:
                context = contexts[0]
                pages = context.pages
                if pages:
                    page = pages[0]
                else:
                    page = context.new_page()
                    page.goto(url, timeout=30000)
            
            # 保存到類別變數
            NxCloudPage._global_context = context
            NxCloudPage._global_page = page
            
            self.logger.info("[PLAYWRIGHT] ✅ 已連接到獨立 Chrome")
            self.logger.info("[PLAYWRIGHT] ✅ Browser 已保存到類別變數")
            
            # 5. 最大化瀏覽器
            try:
                import pygetwindow as gw
                time.sleep(1)
                chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
                if chrome_windows:
                    chrome_windows[0].maximize()
                    self.logger.info("[PLAYWRIGHT] ✅ 瀏覽器已最大化")
            except Exception as e:
                self.logger.warning(f"[PLAYWRIGHT] 最大化失敗: {e}")
            
            # 6. 保存 CDP endpoint
            cdp_file = os.path.join(os.path.dirname(__file__), '..', '..', '.playwright_cdp_endpoint')
            with open(cdp_file, 'w') as f:
                f.write(f"http://localhost:{debug_port}")
            self.logger.info(f"[PLAYWRIGHT] CDP endpoint 已保存")
            
            return (NxCloudPage._global_pw, NxCloudPage._browser, context, page)
            
        except Exception as e:
            self.logger.error(f"[PLAYWRIGHT] ❌ 啟動失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return (None, None, None, None)
    
    def launch_playwright_browser(self, url: str) -> tuple:
        """
        啟動 Playwright 瀏覽器並訪問指定 URL
        
        Args:
            url: 要訪問的 URL
            
        Returns:
            tuple: (playwright_instance, browser, context, page) 如果成功，否則 (None, None, None, None)
            
        Note:
            - 此方法只負責啟動瀏覽器和訪問 URL
            - 不包含業務邏輯（如登錄、切換語言）
            - 返回的實例需要保存到全局變量以防止垃圾回收
        """
        from playwright.sync_api import sync_playwright
        import time
        
        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 啟動瀏覽器並訪問 URL: {url}")
        
        try:
            # 啟動 Playwright（保存到類別變數）
            if NxCloudPage._global_pw is None:
                NxCloudPage._global_pw = sync_playwright().start()
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] Playwright 已啟動（類別變數）")
            else:
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 使用現有 Playwright 實例")
            
            # 🎯 啟動 Chrome 並開啟遠程調試端口
            # 這樣其他進程可以通過 CDP 連接到同一個瀏覽器
            import random
            debug_port = random.randint(9222, 9299)  # 隨機端口避免衝突
            
            # 🎯 關鍵：將 browser 保存到類別變數
            NxCloudPage._browser = NxCloudPage._global_pw.chromium.launch(
                headless=False,
                channel="chrome",  # 使用系統 Chrome
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    f'--remote-debugging-port={debug_port}'  # 開啟遠程調試
                ]
            )
            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] Chrome 已啟動（CDP 端口: {debug_port}）")
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ Browser 已保存到類別變數")
            
            # 🎯 保存 CDP endpoint 到文件，供 Case 2-2 使用
            import os
            cdp_file = os.path.join(os.path.dirname(__file__), '..', '..', '.playwright_cdp_endpoint')
            try:
                with open(cdp_file, 'w') as f:
                    f.write(f"http://localhost:{debug_port}")
                self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] CDP endpoint 已保存: {cdp_file}")
            except Exception as e:
                self.logger.warning(f"[NX_CLOUD] [PLAYWRIGHT] 保存 CDP endpoint 失敗: {e}")
            
            # 創建上下文（使用類別變數）
            context = NxCloudPage._browser.new_context(
                ignore_https_errors=True,
                no_viewport=True  # 🎯 關鍵：禁用固定視口
            )
            
            # 創建頁面
            page = context.new_page()
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 頁面已創建")
            
            # 訪問 URL
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(2)  # 等待頁面完全載入
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ 頁面載入完成")
            
            # 🎯 關鍵：最大化瀏覽器視窗（使用 pygetwindow）
            try:
                import pygetwindow as gw
                self.logger.info("[PLAYWRIGHT] 正在最大化瀏覽器視窗...")
                
                # 等待視窗出現
                time.sleep(1)
                
                # 查找 Chrome 視窗
                chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
                
                if chrome_windows:
                    # 最大化第一個 Chrome 視窗
                    chrome_windows[0].maximize()
                    self.logger.info("[PLAYWRIGHT] ✅ 瀏覽器已最大化")
                    time.sleep(1)  # 等待視窗調整
                else:
                    self.logger.warning("[PLAYWRIGHT] ⚠️ 未找到 Chrome 視窗，無法最大化")
                    
            except Exception as maximize_e:
                self.logger.warning(f"[PLAYWRIGHT] 最大化失敗: {maximize_e}")
            
            # 保存到類別變數
            NxCloudPage._global_context = context
            NxCloudPage._global_page = page
            
            return (NxCloudPage._global_pw, NxCloudPage._browser, context, page)
            
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ 啟動瀏覽器失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # 🎯 不清理資源，保留 browser 供調試
            # NxCloudPage._browser 仍然保持存活
            
            return (None, None, None, None)
    
    def connect_to_existing_browser(self) -> bool:
        """
        連接到現有的瀏覽器（用於 Case 2-2，比照 Selenium）
        
        使用類別屬性中保存的 Playwright 實例連接到現有瀏覽器。
        
        Returns:
            bool: 是否成功連接
            
        Note:
            比照 Selenium 的持久化邏輯，直接使用類別屬性中的實例
        """
        self.logger.info("[NX_CLOUD] 嘗試連接到現有瀏覽器（使用類別屬性）...")
        
        try:
            from playwright.sync_api import sync_playwright
            
            # 🎯 檢查類別屬性中是否已有 Playwright 實例
            if NxCloudPage._global_pw is None:
                self.logger.info("[NX_CLOUD] 初始化 Playwright 實例...")
                NxCloudPage._global_pw = sync_playwright().start()
            
            # 🎯 檢查是否已有 page
            if NxCloudPage._global_page:
                self.playwright_page = NxCloudPage._global_page
                self.logger.info(f"[NX_CLOUD] ✅ 使用現有頁面: {self.playwright_page.url}")
                return True
            
            # 🎯 嘗試連接到現有瀏覽器（保存到類別變數）
            self.logger.info("[NX_CLOUD] 嘗試連接到 CDP: http://127.0.0.1:9222")
            NxCloudPage._browser = NxCloudPage._global_pw.chromium.connect_over_cdp(
                "http://127.0.0.1:9222",
                timeout=10000
            )
            
            # 獲取現有 context 和 page
            contexts = NxCloudPage._browser.contexts
            if not contexts:
                self.logger.error("[NX_CLOUD] ❌ 沒有找到 context")
                return False
            
            context = contexts[0]
            pages = context.pages
            
            if not pages:
                self.logger.error("[NX_CLOUD] ❌ 沒有找到 page")
                return False
            
            # 🎯 保存到類別變數（防止垃圾回收）
            NxCloudPage._global_context = context
            NxCloudPage._global_page = pages[0]
            self.playwright_page = NxCloudPage._global_page
            
            self.logger.info(f"[NX_CLOUD] ✅ 已連接到現有瀏覽器")
            self.logger.info(f"[NX_CLOUD] ✅ Browser 已保存到類別變數（瀏覽器保持運行）")
            self.logger.info(f"[NX_CLOUD] 當前 URL: {self.playwright_page.url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] ❌ 連接失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def attach_and_manage_nx_cloud_v2(self) -> bool:
        """
        使用「優先接管，失敗才啟動」策略管理瀏覽器（比照 Selenium）
        
        策略：
        1. 等待 app 打開 Chrome
        2. 獲取 URL
        3. 關閉 app Chrome
        4. 使用類別屬性保存 Playwright 實例（防止垃圾回收）
        5. 優先接管現有瀏覽器，失敗才啟動新實例
        
        Returns:
            bool: 是否成功獲取瀏覽器頁面
            
        Note:
            比照 Selenium 的持久化邏輯，使用類別屬性保存 Playwright 實例
        """
        import time
        from playwright.sync_api import sync_playwright
        
        self.logger.info("[NX_CLOUD] 使用「優先接管，失敗才啟動」策略（比照 Selenium）")
        
        # 步驟 1: 等待 app 打開 Chrome
        msg = "[STEP_1] 等待 app 打開 Chrome..."
        self.logger.info(msg)
        print(msg)
        if not self.wait_for_chrome_window(timeout=10):
            msg = "[STEP_1] ❌ 等待 Chrome 窗口超時"
            self.logger.error(msg)
            print(msg)
            return False
        msg = "[STEP_1] ✅ Chrome 窗口已打開"
        self.logger.info(msg)
        print(msg)
        
        # 步驟 2: 快速獲取 URL
        msg = "[STEP_2] 快速獲取 URL..."
        self.logger.info(msg)
        print(msg)
        nx_url = self.get_current_browser_url(close_window=False, max_retries=10)
        
        if not nx_url or "nxvms.cloud" not in nx_url:
            msg = f"[STEP_2] ❌ 無法獲取有效 URL: {nx_url}"
            self.logger.error(msg)
            print(msg)
            return False
        msg = f"[STEP_2] ✅ 獲取到 URL: {nx_url}"
        self.logger.info(msg)
        print(msg)
        
        # 步驟 3: 關閉 app Chrome（避免多個 Chrome 實例）
        msg = "[STEP_3] 關閉 app Chrome..."
        self.logger.info(msg)
        print(msg)
        try:
            self.close_chrome_window()
            time.sleep(1)
        except Exception as e:
            msg = f"[STEP_3] ⚠️ 關閉 Chrome 時發生錯誤: {e}"
            self.logger.warning(msg)
            print(msg)
        
        # 步驟 4: 初始化 Playwright（比照 Selenium 的 WebDriver 管理）
        msg = "[STEP_4] 初始化 Playwright 實例（類別屬性）..."
        self.logger.info(msg)
        print(msg)
        
        try:
            # ========================================================================
            # 🎯 關鍵步驟 1：單例模式初始化 Playwright（比照 Selenium）
            # ========================================================================
            # 
            # 教學說明：為什麼這樣做等同於 Selenium 的 detach？
            # 
            # Selenium 的做法：
            #   if MyPage._driver is None:
            #       options = ChromeOptions()
            #       options.add_experimental_option("detach", True)
            #       MyPage._driver = webdriver.Chrome(options=options)
            # 
            # Playwright 的對應做法：
            #   if NxCloudPage._global_pw is None:
            #       NxCloudPage._global_pw = sync_playwright().start()
            # 
            # 為什麼不會被關閉？
            #   1. _global_pw 是類別屬性，不是局部變數
            #   2. 類別屬性在程序運行期間一直存在
            #   3. Python 垃圾回收器看到引用計數 > 0，不會回收
            #   4. Playwright 進程和瀏覽器進程都保持運行
            # 
            # 對比：如果使用局部變數（❌ 錯誤示範）
            #   pw = sync_playwright().start()  # 局部變數
            #   # 函數結束 → pw 被銷毀 → 引用計數 = 0 → 垃圾回收 → 進程終止
            # ========================================================================
            
            if NxCloudPage._global_pw is None:
                NxCloudPage._global_pw = sync_playwright().start()
                self.logger.info("[PLAYWRIGHT] ✅ Playwright 實例已啟動（類別屬性）")
                print("[PLAYWRIGHT] ✅ Playwright 實例已啟動（類別屬性）")
                print("[PLAYWRIGHT] 💡 使用類別屬性保存，等同於 Selenium 的 detach=True")
            else:
                self.logger.info("[PLAYWRIGHT] ℹ️ 使用現有 Playwright 實例")
                print("[PLAYWRIGHT] ℹ️ 使用現有 Playwright 實例")
            
            # 步驟 5: 優先嘗試接管現有瀏覽器
            msg = "[STEP_5] 嘗試接管現有瀏覽器（CDP: http://127.0.0.1:9222）..."
            self.logger.info(msg)
            print(msg)
            
            page = None
            try:
                # ================================================================
                # 🎯 關鍵：將 browser 保存到類別變數（不是局部變數）
                # ================================================================
                # 
                # 問題：browser = ... 是局部變數，函數結束後會被垃圾回收
                # 解決：NxCloudPage._browser = ... 保存到類別變數
                # ================================================================
                
                NxCloudPage._browser = NxCloudPage._global_pw.chromium.connect_over_cdp(
                    "http://127.0.0.1:9222",
                    timeout=5000
                )
                
                # 獲取現有 context 和 page
                contexts = NxCloudPage._browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    
                    if pages:
                        # 使用第一個頁面或創建新頁面
                        page = pages[0]
                        page.goto(nx_url, timeout=30000, wait_until="domcontentloaded")
                    else:
                        page = context.new_page()
                        page.goto(nx_url, timeout=30000, wait_until="domcontentloaded")
                else:
                    # 創建新 context（使用 no_viewport=True 解決畫面比例問題）
                    context = NxCloudPage._browser.new_context(
                        ignore_https_errors=True,
                        no_viewport=True  # 🎯 關鍵：禁用固定視口
                    )
                    page = context.new_page()
                    page.goto(nx_url, timeout=30000, wait_until="domcontentloaded")
                
                # 🎯 保存到類別變數（防止垃圾回收）
                NxCloudPage._global_context = context
                NxCloudPage._global_page = page
                
                self.logger.info("[PLAYWRIGHT] ✅ Attach 模式成功")
                self.logger.info("[PLAYWRIGHT] ✅ Browser 已保存到類別變數（瀏覽器保持運行）")
                print("[PLAYWRIGHT] ✅ Attach 模式成功")
                print("[PLAYWRIGHT] ✅ Browser 已保存到類別變數（瀏覽器保持運行）")
                print("[PLAYWRIGHT] 💡 這等同於 Selenium 的 detach=True 功能")
                
            except Exception as attach_error:
                self.logger.info(f"[PLAYWRIGHT] Attach 模式失敗: {attach_error}")
                print(f"[PLAYWRIGHT] Attach 模式失敗，切換到 Launch 模式")
                
                # 步驟 6: 啟動新的持久化瀏覽器
                msg = "[STEP_6] 啟動新的持久化瀏覽器..."
                self.logger.info(msg)
                print(msg)
                
                import os
                user_data_dir = os.path.join(os.path.dirname(__file__), '..', '..', '.chrome-user-data')
                
                # 清理 DevToolsActivePort
                devtools_file = os.path.join(user_data_dir, 'DevToolsActivePort')
                if os.path.exists(devtools_file):
                    try:
                        os.remove(devtools_file)
                    except:
                        pass
                
                # ================================================================
                # 🎯 關鍵步驟 3：啟動持久化瀏覽器並保存到類別屬性
                # ================================================================
                # 
                # 教學說明：launch_persistent_context 的作用
                # 
                # Selenium 的持久化：
                #   options.add_experimental_option("detach", True)
                #   options.add_argument("--user-data-dir=/path/to/profile")
                #   driver = webdriver.Chrome(options=options)
                # 
                # Playwright 的對應實現：
                #   context = pw.chromium.launch_persistent_context(
                #       user_data_dir=...,  # 持久化用戶數據
                #       args=['--remote-debugging-port=9222']  # 開啟 CDP 端口
                #   )
                # 
                # 為什麼使用 launch_persistent_context？
                #   1. 保存用戶數據（cookies, localStorage）
                #   2. 開啟 CDP 端口，允許後續測試連接
                #   3. 返回 BrowserContext，直接可用
                # 
                # 為什麼保存到類別屬性？
                #   - 防止 context 被垃圾回收
                #   - 確保瀏覽器進程保持運行
                #   - 等同於 Selenium 的 detach=True
                # ================================================================
                
                NxCloudPage._global_context = NxCloudPage._global_pw.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    args=[
                        '--remote-debugging-port=9222',  # 開啟 CDP 端口（供 Case 2-2 連接）
                        '--no-first-run',
                        '--no-default-browser-check',
                    ],
                    ignore_https_errors=True,
                    no_viewport=True  # 禁用固定視口（解決內容縮放問題）
                )
                
                # 獲取或創建頁面
                pages = NxCloudPage._global_context.pages
                if pages:
                    page = pages[0]
                else:
                    page = NxCloudPage._global_context.new_page()
                
                # 🎯 保存到類別屬性（防止垃圾回收）
                NxCloudPage._global_page = page
                
                # 導航到 URL
                page.goto(nx_url, timeout=30000, wait_until="domcontentloaded")
                
                # 最大化瀏覽器
                try:
                    import pygetwindow as gw
                    time.sleep(1)
                    chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
                    if chrome_windows:
                        chrome_windows[0].maximize()
                        self.logger.info("[PLAYWRIGHT] ✅ 瀏覽器已最大化")
                except Exception as e:
                    self.logger.warning(f"[PLAYWRIGHT] 最大化失敗: {e}")
                
                self.logger.info("[PLAYWRIGHT] ✅ Launch 模式成功")
                print("[PLAYWRIGHT] ✅ Launch 模式成功")
            
            # 強制同步視口尺寸
            if page:
                try:
                    import pygetwindow as gw
                    chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
                    if chrome_windows:
                        win = chrome_windows[0]
                        width = win.width if win.width > 0 else 1920
                        height = win.height if win.height > 0 else 1080
                    else:
                        width, height = 1920, 1080
                    
                    page.set_viewport_size({"width": width, "height": height})
                    self.logger.info(f"[PLAYWRIGHT] ✅ 視口已同步: {width}x{height}")
                except Exception as e:
                    self.logger.warning(f"[PLAYWRIGHT] 同步視口失敗: {e}")
            
            # 保存到實例變量
            self.playwright_page = page
            
            msg = f"[PLAYWRIGHT] 當前 URL: {page.url}"
            self.logger.info(msg)
            print(msg)
            
            msg = "[PLAYWRIGHT] ✅ 瀏覽器頁面已就緒（供 Case 2-2 使用）"
            self.logger.info(msg)
            print(msg)
            
            # ================================================================
            # 🎯 DEBUG 日誌：確認瀏覽器已脫離控制（Selenium Detach Style）
            # ================================================================
            print("\n" + "=" * 80)
            print("[DEBUG] 🔗 已釋放 Playwright 控制權，Chrome 進程已脫離")
            print("[DEBUG] 💡 瀏覽器將保持運行，您可以開始手動調試")
            print("[DEBUG] 💡 類別屬性保持存活：")
            print(f"[DEBUG]    - _global_pw: {NxCloudPage._global_pw is not None}")
            print(f"[DEBUG]    - _global_context: {NxCloudPage._global_context is not None}")
            print(f"[DEBUG]    - _global_page: {NxCloudPage._global_page is not None}")
            print("[DEBUG] 💡 這等同於 Selenium 的 detach=True 功能")
            print("=" * 80 + "\n")
            
            # ================================================================
            # 🎯 關鍵步驟 4：註冊 atexit 處理函數（最終保險）
            # ================================================================
            # 
            # 教學說明：為什麼需要 atexit？
            # 
            # 即使我們：
            #   1. 使用類別屬性保存 context
            #   2. 調用 browser.disconnect()
            # 
            # Python 程序退出時仍然可能清理 context 對象，導致瀏覽器關閉
            # 
            # 解決方案：
            #   - 註冊 atexit 處理函數
            #   - 在 Python 清理對象前執行
            #   - 標記瀏覽器已脫離，阻止清理
            # ================================================================
            
            if not NxCloudPage._atexit_registered:
                atexit.register(NxCloudPage._prevent_browser_cleanup)
                NxCloudPage._atexit_registered = True
                NxCloudPage._browser_detached = True
                self.logger.info("[PLAYWRIGHT] ✅ atexit 處理函數已註冊")
                print("[PLAYWRIGHT] ✅ atexit 處理函數已註冊（防止程序退出時關閉瀏覽器）")
            
            # ================================================================
            # 🎯 DEBUG_PAUSE：手動調試功能
            # ================================================================
            # 
            # 用法：設置環境變數 DEBUG_PAUSE=true 來啟用手動調試模式
            # 
            # 效果：
            #   - 測試會在此處暫停
            #   - 瀏覽器保持運行，您可以手動操作和調試
            #   - 按 Enter 鍵繼續測試
            # ================================================================
            
            # ================================================================
            # 🎯 關鍵：調用 browser.disconnect() 釋放 Playwright 對瀏覽器的控制
            # ================================================================
            # 
            # 為什麼需要 disconnect？
            #   - disconnect() 斷開 Playwright 與 Chrome 的 CDP 連接
            #   - 瀏覽器進程變成獨立進程，不再受 Playwright 控制
            #   - 當 Python 進程結束時，瀏覽器不會被關閉
            # 
            # 這是實現「Selenium detach=True」效果的關鍵步驟！
            # ================================================================
            
            if NxCloudPage._browser:
                NxCloudPage._browser.disconnect()
                self.logger.info("[PLAYWRIGHT] ✅ Browser 已斷開連接（瀏覽器變成獨立進程）")
                print("[PLAYWRIGHT] ✅ Browser 已斷開連接（瀏覽器變成獨立進程）")
            
            # ================================================================
            # 🎯 DEBUG_PAUSE 模式：按 Enter 繼續
            # ================================================================
            
            if os.getenv("DEBUG_PAUSE") == "true":
                print("\n" + "=" * 80)
                print("[DEBUG] 🔧 測試已暫停，瀏覽器已脫離控制")
                print("[DEBUG] 💡 您可以在瀏覽器中手動操作和調試")
                print("=" * 80)
                input("[DEBUG] 請在手動調試完成後，按 Enter 鍵繼續...")
                print("[DEBUG] ✅ 繼續測試...")
            
            # ================================================================
            # 🎯 KEEP_ALIVE 模式：物理阻斷 Python 進程退出
            # ================================================================
            # 
            # 邏輯說明：
            #   - 即使調用了 disconnect()，Python 進程結束時仍可能觸發清理
            #   - 使用 while True 死循環是保留窗口進行手動調試的物理手段
            #   - 這等同於 Selenium 的 detach=True + 手動阻塞
            # 
            # 用法（在終端機執行）：
            #   $env:KEEP_ALIVE="true"
            #   python TestCaseLauncher.exe
            # ================================================================
            
            if os.getenv("KEEP_ALIVE") == "true":
                print("\n" + "!" * 60)
                print(" [DEBUG] 💡 自動化操作已完成，現在進入「手動調試模式」。")
                print(" [DEBUG] 💡 瀏覽器窗口已脫離自動化控制，且 Python 進程已鎖定。")
                print(" [DEBUG] 💡 現在您可以隨意操作瀏覽器。")
                print(" [DEBUG] 💡 調試結束後，請在終端機按 Ctrl+C 或關閉終端機來結束。")
                print("!" * 60 + "\n")
                
                try:
                    # 使用死循環強行握住 Python 進程
                    # 這也是保留 Playwright 窗口的唯一物理手段
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n[DEBUG] 🛑 收到停止指令，正在釋放驅動...")
            
            return True
            
        except Exception as e:
            msg = f"[STEP_4] ❌ 發生異常: {e}"
            self.logger.error(msg)
            print(msg)
            
            import traceback
            self.logger.error(traceback.format_exc())
            
            return False
    def cleanup_playwright(self):
        """
        清理 Playwright 資源（比照 Selenium 的持久化邏輯）
        
        ========================================================================
        教學說明：為什麼這樣清理等同於 Selenium 的 detach？
        ========================================================================
        
        Selenium 的清理方式：
            def cleanup(self):
                # 不調用 driver.quit()
                # driver 保持運行，瀏覽器不關閉
                pass
        
        Playwright 的對應實現：
            def cleanup_playwright(self):
                # 只清理實例變量
                self.playwright_page = None
                
                # 不清理類別屬性（關鍵！）
                # NxCloudPage._global_pw 保持存活
                # NxCloudPage._global_context 保持存活
                # NxCloudPage._global_page 保持存活
        
        為什麼不清理類別屬性？
            1. 類別屬性的引用計數 > 0
            2. Python 垃圾回收器不會回收
            3. Playwright 進程和瀏覽器進程保持運行
            4. 等同於 Selenium 的 detach=True
        
        對比：如果清理類別屬性（❌ 錯誤示範）
            NxCloudPage._global_context = None  # 引用計數 = 0
            # → 垃圾回收 → context.__del__() → 瀏覽器關閉
        
        重要：
        - 不清理類別屬性（_global_pw, _global_context, _global_page）
        - 只清理實例變量
        - 確保瀏覽器保持運行供後續測試使用
        ========================================================================
        """
        self.logger.info("[NX_CLOUD] [CLEANUP] 清理實例變量（保持類別屬性）...")
        print("\n" + "="*80)
        print("[NX_CLOUD] [CLEANUP] 清理實例變量（保持類別屬性）...")
        print("="*80)
        
        try:
            # ====================================================================
            # 🎯 關鍵：只清理實例變量，不清理類別屬性
            # ====================================================================
            # 
            # 清理實例變量：
            self.playwright_page = None  # 清理實例引用
            
            # 不清理類別屬性（關鍵！）：
            # NxCloudPage._global_pw = None        # ❌ 絕對不要這樣做！
            # NxCloudPage._global_context = None   # ❌ 絕對不要這樣做！
            # NxCloudPage._global_page = None      # ❌ 絕對不要這樣做！
            # 
            # 為什麼？
            #   - 清理類別屬性 → 引用計數 = 0 → 垃圾回收 → 瀏覽器關閉
            #   - 保持類別屬性 → 引用計數 > 0 → 不會被回收 → 瀏覽器保持運行
            # ====================================================================
            
            self.logger.info("[NX_CLOUD] [CLEANUP] ✅ 實例變量已清理")
            self.logger.info("[NX_CLOUD] [CLEANUP] 💡 類別屬性保持存活（瀏覽器繼續運行）")
            print("[NX_CLOUD] [CLEANUP] ✅ 實例變量已清理")
            print("[NX_CLOUD] [CLEANUP] 💡 類別屬性保持存活（瀏覽器繼續運行）")
            print("[NX_CLOUD] [CLEANUP] 💡 這等同於 Selenium 的 detach=True 功能")
            print("="*80 + "\n")
            
        except Exception as e:
            self.logger.warning(f"[NX_CLOUD] [CLEANUP] ⚠️ 清理時發生錯誤: {e}")
            print(f"[NX_CLOUD] [CLEANUP] ⚠️ 清理時發生錯誤: {e}")
    
    def attach_and_manage_nx_cloud(self) -> bool:
        """
        使用 Playwright 接管 Chrome 瀏覽器並處理 Nx Cloud 登錄
        
        此方法會：
        1. 透過 CDP (Chrome DevTools Protocol) 連接到已打開的 Chrome
        2. 尋找 Nx Cloud 系統管理頁面
        3. 檢查登錄狀態並執行登錄（如果需要）
        
        Returns:
            bool: 操作是否成功
        
        Note:
            - Chrome 必須以 --remote-debugging-port 啟動
            - 預設連接到 http://localhost:7001
        """
        self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 嘗試透過 CDP 接管 Chrome 瀏覽器...")
        
        # ✅ 關鍵：必須在 sync_playwright() 之前設置環境變量
        import os
        import requests
        os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
        
        # 🔍 診斷：檢查 Chrome 調試端口是否運行
        cdp_url = f"http://localhost:{EnvConfig.BROWSER_DEBUG_PORT}"
        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 目標 CDP 端口: {EnvConfig.BROWSER_DEBUG_PORT}")
        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 目標 CDP URL: {cdp_url}")
        
        try:
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 🔍 診斷步驟 1: 檢查 CDP 端口是否可訪問...")
            response = requests.get(f"{cdp_url}/json/version", timeout=3)
            if response.status_code == 200:
                version_data = response.json()
                self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] ✅ CDP 端口可訪問")
                self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT]    Browser: {version_data.get('Browser', 'Unknown')}")
                self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT]    WebSocket: {version_data.get('webSocketDebuggerUrl', 'N/A')[:80]}...")
            else:
                self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ CDP 端口返回錯誤狀態碼: {response.status_code}")
                self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 請確保已運行: python start_chrome_debug.py")
                return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ 無法連接到 CDP 端口 {EnvConfig.BROWSER_DEBUG_PORT}")
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] Chrome 調試模式未運行！")
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 請先運行: python start_chrome_debug.py")
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 然後保持 Chrome 窗口運行，再重新執行測試")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ 檢查 CDP 端口時發生錯誤: {e}")
            return False
        
        try:
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 🔍 診斷步驟 2: 嘗試透過 Playwright 連接...")
            
            # ================================================================
            # 🎯 關鍵修改：不使用 with 語句，改用類別變數保持實例
            # ================================================================
            # 
            # 問題：with sync_playwright() as p: 會在塊結束時自動調用 p.stop()
            # 解決：使用類別變數 _global_pw 保持 Playwright 實例存活
            # ================================================================
            
            if NxCloudPage._global_pw is None:
                NxCloudPage._global_pw = sync_playwright().start()
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ Playwright 實例已啟動（類別變數）")
            
            # 🎯 關鍵：將 browser 保存到類別變數（不是局部變數）
            NxCloudPage._browser = NxCloudPage._global_pw.chromium.connect_over_cdp(cdp_url)
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 成功連接到 Chrome")
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ Browser 已保存到類別變數")
            
            # 🎯 關鍵：檢查所有 BrowserContext（可能有多個窗口）
            if not NxCloudPage._browser.contexts:
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT] 無可用的 BrowserContext")
                return False
            
            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 找到 {len(NxCloudPage._browser.contexts)} 個 BrowserContext")
            
            # 檢查所有 context 中的所有頁面
            all_pages = []
            for ctx_idx, ctx in enumerate(NxCloudPage._browser.contexts):
                self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] Context {ctx_idx}: {len(ctx.pages)} 個頁面")
                all_pages.extend(ctx.pages)
            
            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 總共找到 {len(all_pages)} 個頁面")
            
            # 🎯 關鍵改進：等待 Nx Cloud 頁面出現（最多等待 15 秒）
            target_page = None
            max_wait_time = 15  # 秒
            check_interval = 1  # 秒
            
            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 等待 Nx Cloud 頁面出現（最多 {max_wait_time} 秒）...")
            
            for attempt in range(max_wait_time):
                # 🎯 重新獲取所有 context 的所有頁面（可能有新窗口打開）
                all_pages = []
                for ctx in NxCloudPage._browser.contexts:
                    all_pages.extend(ctx.pages)
                
                for page in all_pages:
                    page_url = page.url
                    if attempt == 0 or attempt % 3 == 0:  # 每 3 秒輸出一次
                        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] [嘗試 {attempt+1}/{max_wait_time}] 檢查頁面: {page_url}")
                    
                    # 檢查是否是 Nx Cloud 系統管理頁面
                    if "nxvms.cloud/systems/" in page_url or "nx-cn.nxvms.cloud/systems/" in page_url:
                        target_page = page
                        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] ✅ 找到目標頁面: {page_url}")
                        break
                
                if target_page:
                    break
                
                # 如果還沒找到，等待一下再檢查
                if attempt < max_wait_time - 1:
                    time.sleep(check_interval)
            
            if not target_page:
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT] ❌ 等待超時，未找到 Nx Cloud 系統管理頁面")
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 最終頁面列表:")
                for idx, page in enumerate(NxCloudPage._browser.contexts[0].pages if NxCloudPage._browser.contexts else []):
                    self.logger.info(f"  [{idx}] {page.url}")
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT] 可能原因：")
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT]   1. Nx Witness 沒有成功打開 URL")
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT]   2. URL 在其他 Chrome 實例中打開")
                self.logger.error("[NX_CLOUD] [PLAYWRIGHT]   3. 網絡連接問題")
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 提取系統 UUID
            system_uuid = target_page.url.split('/')[-1]
            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 系統 UUID: {system_uuid}")
            
            # 等待頁面載入完成
            try:
                target_page.wait_for_load_state('networkidle', timeout=10000)
            except PlaywrightTimeoutError:
                self.logger.warning("[NX_CLOUD] [PLAYWRIGHT] 頁面載入超時，繼續執行...")
            
            # 檢查登錄狀態
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 檢查登錄狀態...")
            
            # 方式 1: 檢查登錄按鈕（未登錄時存在）
            login_button = target_page.locator("a:has-text('log in'), a:has-text('Log in'), a:has-text('登入')")
            
            try:
                if login_button.is_visible(timeout=3000):
                    self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 🔒 尚未登入，執行登入流程...")
                    
                    # 點擊登錄按鈕
                    login_button.click()
                    self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 已點擊登錄按鈕")
                    
                    # 等待登錄表單出現（使用正確的 ID 選擇器）
                    try:
                        # 優先使用 ID 選擇器（更精確）
                        target_page.wait_for_selector("#authorizeEmail", timeout=5000)
                        self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 登錄表單已出現（找到 #authorizeEmail）")
                    except PlaywrightTimeoutError:
                        self.logger.error("[NX_CLOUD] [PLAYWRIGHT] ❌ 等待登錄表單超時")
                        # 嘗試查找頁面上的所有 input 元素
                        all_inputs = target_page.locator("input").all()
                        self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 頁面上共有 {len(all_inputs)} 個 input 元素")
                        for idx, inp in enumerate(all_inputs[:5]):  # 只顯示前 5 個
                            try:
                                inp_type = inp.get_attribute("type")
                                inp_name = inp.get_attribute("name")
                                inp_id = inp.get_attribute("id")
                                self.logger.info(f"  Input {idx}: type={inp_type}, name={inp_name}, id={inp_id}")
                            except:
                                pass
                        # 🎯 不調用 disconnect，保留 browser 供調試
                        return False
                    
                    # 輸入郵箱（使用 ID 選擇器）
                    email_input = target_page.locator("#authorizeEmail")
                    email_input.fill(EnvConfig.NX_CLOUD_EMAIL)
                    self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 已輸入郵箱: {EnvConfig.NX_CLOUD_EMAIL}")
                    
                    # 檢查是否有「下一步」按鈕（某些登錄流程分兩步）
                    next_button = target_page.locator("button:has-text('Next'), button:has-text('下一步'), button:has-text('next')")
                    if next_button.is_visible(timeout=1000):
                        next_button.click()
                        self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 已點擊「下一步」")
                        time.sleep(1)
                    
                    # 輸入密碼（使用 ID 選擇器）
                    password_input = target_page.locator("#authorizePassword")
                    password_input.fill(EnvConfig.NX_CLOUD_PASSWORD)
                    self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 已輸入密碼")
                    
                    # 點擊登錄按鈕
                    submit_button = target_page.locator("button:has-text('Log in'), button:has-text('登入'), button[type='submit']").first
                    submit_button.click()
                    self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 已點擊登錄按鈕")
                    
                    # 等待登錄完成（檢查 URL 變化或用戶頭像出現）
                    try:
                        target_page.wait_for_load_state('networkidle', timeout=10000)
                        self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ 登錄成功")
                    except PlaywrightTimeoutError:
                        self.logger.warning("[NX_CLOUD] [PLAYWRIGHT] 登錄後頁面載入超時，但可能已成功")
                    
                else:
                    self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ 已登入，無需重複登錄")
                    
                    # 檢查用戶頭像或用戶名（驗證登錄狀態）
                    user_indicators = [
                        "img[alt*='avatar'], img[alt*='Avatar']",  # 用戶頭像
                        "[class*='user'], [class*='User']",  # 用戶相關元素
                        "button:has-text('Logout'), button:has-text('登出')",  # 登出按鈕
                    ]
                    
                    for indicator in user_indicators:
                        if target_page.locator(indicator).is_visible(timeout=2000):
                            self.logger.info(f"[NX_CLOUD] [PLAYWRIGHT] 驗證登錄狀態: 找到元素 '{indicator}'")
                            break
            
            except PlaywrightTimeoutError:
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ 未找到登錄按鈕，可能已登入")
            
            # 🎯 操作完成
            self.logger.info("[NX_CLOUD] [PLAYWRIGHT] 操作完成")
            
            # ================================================================
            # 🎯 關鍵：調用 browser.disconnect() 釋放 Playwright 對瀏覽器的控制
            # ================================================================
            # 
            # 為什麼需要 disconnect？
            #   - disconnect() 斷開 Playwright 與 Chrome 的 CDP 連接
            #   - 瀏覽器進程變成獨立進程，不再受 Playwright 控制
            #   - 當 Python 進程結束時，瀏覽器不會被關閉
            # 
            # 這是實現「Selenium detach=True」效果的關鍵步驟！
            # ================================================================
            
            if NxCloudPage._browser:
                NxCloudPage._browser.disconnect()
                self.logger.info("[NX_CLOUD] [PLAYWRIGHT] ✅ Browser 已斷開連接（瀏覽器變成獨立進程）")
                print("[NX_CLOUD] [PLAYWRIGHT] ✅ Browser 已斷開連接（瀏覽器變成獨立進程）")
            
            # ================================================================
            # 🎯 KEEP_ALIVE 模式：物理阻斷 Python 進程退出
            # ================================================================
            # 
            # 邏輯說明：
            #   - 即使調用了 disconnect()，Python 進程結束時仍可能觸發清理
            #   - 使用 while True 死循環是保留窗口進行手動調試的物理手段
            #   - 這等同於 Selenium 的 detach=True + 手動阻塞
            # 
            # 用法（在終端機執行）：
            #   $env:KEEP_ALIVE="true"
            #   python TestCaseLauncher.exe
            # ================================================================
            
            if os.getenv("KEEP_ALIVE") == "true":
                print("\n" + "!" * 60)
                print(" [DEBUG] 💡 自動化操作已完成，現在進入「手動調試模式」。")
                print(" [DEBUG] 💡 瀏覽器窗口已脫離自動化控制，且 Python 進程已鎖定。")
                print(" [DEBUG] 💡 現在您可以隨意操作瀏覽器。")
                print(" [DEBUG] 💡 調試結束後，請在終端機按 Ctrl+C 或關閉終端機來結束。")
                print("!" * 60 + "\n")
                
                try:
                    # 使用死循環強行握住 Python 進程
                    # 這也是保留 Playwright 窗口的唯一物理手段
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n[DEBUG] 🛑 收到停止指令，正在釋放驅動...")
            
            return True
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ Playwright 超時錯誤: {e}")
            import traceback
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 錯誤堆棧:\n{traceback.format_exc()}")
            return False
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] ❌ 操作失敗: {e}")
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 錯誤類型: {type(e).__name__}")
            import traceback
            self.logger.error(f"[NX_CLOUD] [PLAYWRIGHT] 錯誤堆棧:\n{traceback.format_exc()}")
            return False
    
    def playback_recording_pw(self, playback_duration: int = 7) -> bool:
        """
        [Playwright] 完整執行 Case 2-2: 調閱錄影事件回放
        
        此方法會：
        1. 透過 CDP 連接到已打開的 Chrome
        2. 尋找 Nx Cloud 系統管理頁面
        3. 點擊「查看」頁簽
        4. 點擊 server
        5. 點擊 usb-cam
        6. 驗證影片播放狀態
        7. 等待影片播放指定時間
        
        Args:
            playback_duration: 影片播放時間 (秒)，默認 7 秒
        
        Returns:
            bool: 操作是否成功
        """
        self.logger.info(f"[NX_CLOUD] [PW] [CASE_2-2] 開始調閱錄影事件回放 (播放 {playback_duration} 秒)...")
        
        try:
            # ================================================================
            # 🎯 關鍵修改：不使用 with 語句，改用類別變數保持實例
            # ================================================================
            # 
            # 問題：with sync_playwright() as p: 會在塊結束時自動調用 p.stop()
            # 解決：使用類別變數 _global_pw 保持 Playwright 實例存活
            # ================================================================
            
            if NxCloudPage._global_pw is None:
                NxCloudPage._global_pw = sync_playwright().start()
                self.logger.info("[NX_CLOUD] [PW] ✅ Playwright 實例已啟動（類別變數）")
            
            # 1. 連接到 Chrome（保存到類別變數）
            cdp_url = f"http://localhost:{EnvConfig.BROWSER_DEBUG_PORT}"
            self.logger.info(f"[NX_CLOUD] [PW] 連接 CDP: {cdp_url}")
            
            # 🎯 關鍵：將 browser 保存到類別變數（不是局部變數）
            NxCloudPage._browser = NxCloudPage._global_pw.chromium.connect_over_cdp(cdp_url)
            self.logger.info("[NX_CLOUD] [PW] 成功連接到 Chrome")
            self.logger.info("[NX_CLOUD] [PW] ✅ Browser 已保存到類別變數")
            
            if not NxCloudPage._browser.contexts:
                self.logger.error("[NX_CLOUD] [PW] 無可用的 BrowserContext")
                return False
            
            context = NxCloudPage._browser.contexts[0]
            self.logger.info(f"[NX_CLOUD] [PW] 找到 {len(context.pages)} 個頁面")
            
            # 2. 尋找 Nx Cloud 頁面
            target_page = None
            for page in context.pages:
                self.logger.info(f"[NX_CLOUD] [PW] 檢查頁面: {page.url}")
                if "nxvms.cloud/systems/" in page.url or "nx-cn.nxvms.cloud/systems/" in page.url:
                    target_page = page
                    self.logger.info(f"[NX_CLOUD] [PW] ✅ 找到目標頁面: {page.url}")
                    break
            
            if not target_page:
                self.logger.error("[NX_CLOUD] [PW] ❌ 未找到 Nx Cloud 系統管理頁面")
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 等待頁面穩定
            try:
                target_page.wait_for_load_state('networkidle', timeout=10000)
            except PlaywrightTimeoutError:
                self.logger.warning("[NX_CLOUD] [PW] 頁面載入超時，繼續執行...")
            
            # 3. 點擊「查看」頁簽
            self.logger.info("[NX_CLOUD] [PW] [步驟 1] 點擊「查看」頁簽...")
            if not self.click_view_tab_pw(target_page):
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 等待頁面完全加載
            time.sleep(3)
            
            # 4. 點擊 server
            self.logger.info("[NX_CLOUD] [PW] [步驟 2] 點擊 server...")
            if not self.click_server_pw(target_page):
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 5. 點擊 usb-cam
            self.logger.info("[NX_CLOUD] [PW] [步驟 3] 點擊 usb-cam...")
            if not self.click_usb_cam_pw(target_page):
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 6. 驗證影片播放狀態
            self.logger.info("[NX_CLOUD] [PW] [步驟 4] 驗證影片播放狀態...")
            if not self.verify_video_playback_pw(target_page, timeout=20):
                # 🎯 不調用 disconnect，保留 browser 供調試
                return False
            
            # 7. 等待影片播放
            self.logger.info(f"[NX_CLOUD] [PW] [步驟 5] 等待影片播放 {playback_duration} 秒...")
            time.sleep(playback_duration)
            self.logger.info(f"[NX_CLOUD] [PW] ✅ 已等待影片播放 {playback_duration} 秒")
            
            # 🎯 操作完成（瀏覽器保持運行，已保存到類別變數）
            self.logger.info("[NX_CLOUD] [PW] 操作完成（瀏覽器保持運行）")
            self.logger.info("[NX_CLOUD] [PW] ✅ Browser 已保存到類別變數，不會被關閉")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[NX_CLOUD] [PW] [CASE_2-2] 操作失敗: {e}")
            import traceback
            traceback.print_exc()
            return False