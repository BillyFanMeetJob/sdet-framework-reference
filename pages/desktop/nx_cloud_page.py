# 相對路徑: pages/desktop/nx_cloud_page.py

from base.desktop_app import DesktopApp
from config import EnvConfig
import time
import pygetwindow as gw
import pyautogui
import pyperclip


class NxCloudPage(DesktopApp):
    """
    Nx Cloud 桌面端操作頁面處理類
    
    處理 Case 2-1 的桌面端操作：
    1. 點擊畫面右上角的賬號（會出現 menu）
    2. 點擊「開啟 Nx Cloud 介面」
    3. 等待 Chrome 視窗出現
    
    Note:
        - Case 2-2 已改用 Selenium (pages/web/nx_cloud_web_page.py)
        - 此類別僅保留 Case 2-1 需要的桌面端操作方法
        - 所有 Playwright 相關方法已移除
    """
    
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

