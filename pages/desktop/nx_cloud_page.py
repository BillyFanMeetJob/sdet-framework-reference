# 相對路徑: pages/desktop/nx_cloud_page.py

from base.desktop_app import DesktopApp
from config import EnvConfig
import time
import pygetwindow as gw
import pyautogui


class NxCloudPage(DesktopApp):
    """
    Nx Cloud 桌面端操作頁面處理類
    
    處理 Case 2-1 的桌面端操作：
    1. 點擊畫面右上角的賬號（會出現 menu）
    2. 點擊「開啟 Nx Cloud 介面」
    3. 等待 Chrome 視窗出現
    """
    
    def __init__(self):
        super().__init__()
    
    def click_account_menu(self) -> bool:
        """
        點擊畫面右上角的賬號（會出現 menu）
        
        策略：
        直接使用座標點擊（根據截圖量出的位置：x_ratio=0.85, y_ratio=0.02）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD] [CLICK] 點擊右上角賬號（使用座標）...")
        
        # 獲取視窗以計算座標
        win = self.get_nx_window()
        if not win:
            self.logger.error("[NX_CLOUD] [ERROR] 無法找到 Nx Witness 視窗")
            return False
        
        # 🎯 直接使用座標點擊（根據截圖量出的位置）
        # 禁用所有辨識方法，直接使用座標保底
        success = self.smart_click(
            x_ratio=0.85,  # 🎯 根據截圖量出的賬號位置
            y_ratio=0.02,  # 🎯 根據截圖量出的賬號位置
            target_text=None,  # 不使用文字辨識
            image_path=None,  # 不使用圖片
            timeout=1,  # 短超時，快速跳過辨識直接使用座標
            use_vlm=False,  # 禁用 VLM
            use_ok_script=False  # 禁用圖像辨識
        )
        
        if success:
            self.logger.info("[NX_CLOUD] [OK] 成功點擊賬號，等待選單展開...")
            time.sleep(1.0)  # 等待選單展開
        else:
            self.logger.error("[NX_CLOUD] [ERROR] 點擊賬號失敗")
        
        return success
    
    def click_open_nx_cloud_interface(self) -> bool:
        """
        點擊「開啟 Nx Cloud 介面」選單項目
        
        策略：
        1. 優先使用 OK Script 圖像辨識（需要先截圖選單項目的圖片）
        2. 如果圖像辨識失敗，使用座標保底（選單通常在賬號下方，中央偏右）
        
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info("[NX_CLOUD] [CLICK] 點擊「開啟 Nx Cloud 介面」...")
        
        # 獲取視窗以計算選單區域
        win = self.get_nx_window()
        if not win:
            self.logger.error("[NX_CLOUD] [ERROR] 無法找到 Nx Witness 視窗")
            return False
        
        # 🎯 根據截圖，選單在賬號下方，定義選單搜尋區域
        # 選單通常在頂部中央偏右，高度約為 200-300px
        screen_w, screen_h = pyautogui.size()
        region_left = int(screen_w * 0.40)  # 從螢幕中央 40% 開始
        region_top = int(screen_h * 0.05)  # 從頂部 5% 開始（選單在賬號下方）
        region_width = int(screen_w * 0.40)  # 寬度為螢幕的 40%
        region_height = int(screen_h * 0.25)  # 高度為螢幕的 25%（覆蓋選單區域）
        region = (region_left, region_top, region_width, region_height)
        
        self.logger.info(f"[NX_CLOUD] [ROI] 選單搜尋區域: left={region_left}, top={region_top}, width={region_width}, height={region_height}")
        
        # 🎯 優先使用 OK Script 圖像辨識，禁用 VLM（避免 VLM 給出錯誤座標）
        # 注意：如果圖片不存在，會回退到座標保底
        success = self.smart_click(
            x_ratio=0.85,  # 🎯 根據截圖調整：選單中央偏右（與賬號位置對齊）
            y_ratio=0.05,  # 🎯 選單第一項通常在賬號下方約 8% 的位置（根據截圖調整）
            target_text=None,  # 🎯 不使用文字辨識（避免 VLM 給出錯誤座標）
            image_path="desktop_settings/open_nx_web.png",  # 嘗試使用圖片（如果存在）
            timeout=5,  # 超時時間
            use_vlm=False,  # 🎯 禁用 VLM，優先使用圖像辨識
            use_ok_script=True,  # 🎯 優先使用 OK Script 圖像辨識
            region=region  # 🎯 限制搜尋區域在選單區域
        )
        
        if success:
            self.logger.info("[NX_CLOUD] [OK] 成功點擊「開啟 Nx Cloud 介面」，Chrome 會自動打開並跳轉...")
            # 🎯 不需要額外等待，Chrome 會自動打開並跳轉
            # 等待時間由 wait_for_chrome_window 處理
        else:
            self.logger.error("[NX_CLOUD] [ERROR] 點擊「開啟 Nx Cloud 介面」失敗")
        
        return success
    
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
        while time.time() - start_time < timeout:
            try:
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
                
                if unique_wins:
                    # 選擇最大的 Chrome 視窗
                    chrome_win = max(unique_wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                    self.logger.info(f"[NX_CLOUD] [OK] 找到 Chrome 視窗: '{chrome_win.title}' ({chrome_win.width}x{chrome_win.height})")
                    return True
                
                time.sleep(0.5)
            except Exception as e:
                self.logger.debug(f"[NX_CLOUD] 檢查 Chrome 視窗時發生異常: {e}")
                time.sleep(0.5)
        
        self.logger.error(f"[NX_CLOUD] [ERROR] 等待 Chrome 視窗超時（{timeout} 秒）")
        return False
