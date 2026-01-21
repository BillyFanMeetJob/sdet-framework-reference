# 相對路徑: pages/desktop/license_settings_page.py

from base.desktop_app import DesktopApp
import time

class LicenseSettingsPage(DesktopApp):
    """
    授權設定頁面
    處理 Case 1-3: 啟用免費錄製授權
    """
    
    def __init__(self):
        super().__init__()
    
    def open_system_administration(self, via_menu=False):
        """
        🎯 開啟系統管理視窗
        方法 1: 在左側 Server 上右鍵 -> 系統管理
        方法 2: 點擊左上角三條線選單 -> 系統管理
        
        Args:
            via_menu: True 使用左上角選單，False 使用 Server 右鍵（預設）
        """
        if via_menu:
            self.logger.info("🖱️ 透過左上角選單開啟系統管理...")
            
            # 點擊左上角三條線選單
            if not self.smart_click(
                x_ratio=0.02,
                y_ratio=0.02,
                image_path="desktop_main/menu_icon.png",
                timeout=3
            ):
                self.logger.error("❌ 點擊選單圖示失敗")
                return False
            
            time.sleep(0.5)
            
            # 點擊「系統管理」選項
            success = self.smart_click(
                x_ratio=0.1,
                y_ratio=0.2,
                target_text="系統管理",
                timeout=2
            )
        else:
            self.logger.info("🖱️ 在 LAPTOP 上右鍵開啟站點管理...")
            
            # 在 LAPTOP-QRJN5735 上點擊右鍵（admin 上方的那個，不是 Server）
            # 從截圖看，LAPTOP 位置約在 y_ratio=0.10
            if not self.smart_click(
                x_ratio=0.08,
                y_ratio=0.10,
                target_text="LAPTOP",
                click_type='right',
                timeout=3
            ):
                self.logger.error("❌ 右鍵點擊 LAPTOP 圖示失敗")
                return False
            
            # 等待右鍵選單出現
            time.sleep(0.8)
            
            # 點擊右鍵選單中的「站點管理」（第 3 項）
            # 右鍵選單：1.開啟網頁用戶端 2.合併站點 3.站點管理
            # 每項約 32px 高度，第三項相對於點擊位置約 +64px
            # 使用 OCR 優先找 "站點管理" 文字
            success = self.smart_click(
                x_ratio=0.12,
                y_ratio=0.16,  # 相對於視窗，第三項約在這個位置
                target_text="站點管理",
                image_path="desktop_settings/system_admin_menu.png",
                timeout=3
            )
        
        if success:
            self.logger.info("✅ 成功點擊系統管理選項")
            # 等待系統管理視窗開啟
            time.sleep(1.5)
            found_window = self.wait_for_window(
                window_titles=["系統管理", "站點管理", "System Administration", "Nx Witness Client"],
                timeout=3
            )
            if found_window:
                self.logger.info(f"✅ 系統管理視窗已開啟: {found_window.title}")
                return True
            else:
                self.logger.warning("⚠️ 未檢測到系統管理視窗")
        
        return success
    
    def switch_to_license_tab(self):
        """
        🎯 切換到「授權」分頁
        從「一般」分頁切換到「授權」分頁
        """
        self.logger.info("🖱️ 點擊「授權」分頁...")
        
        # 分頁通常在視窗上方，水平排列
        # 根據截圖：一般、使用者管理、更新、授權、Email、安全性...
        # 授權是第 4 個分頁，約在 x_ratio=0.25 的位置
        success = self.smart_click(
            x_ratio=0.28,
            y_ratio=0.08,
            target_text="授權",
            image_path="desktop_settings/license_tab.png",
            timeout=2
        )
        
        if success:
            self.logger.info("✅ 成功切換到授權分頁")
            time.sleep(0.5)  # 等待分頁內容載入
        else:
            self.logger.warning("⚠️ 可能未成功切換到授權分頁")
        
        return success
    
    def click_activate_free_license(self):
        """
        🎯 嘗試點擊「啟用免費授權」按鈕
        在授權分頁中，點擊「線上啟動」標籤下的「啟動試用授權」按鈕
        
        注意：如果授權已經啟用過，此按鈕可能不存在
        Returns:
            True: 成功點擊按鈕
            False: 按鈕不存在（可能已經啟用過授權）
        """
        self.logger.info("🖱️ 嘗試尋找「啟用免費授權」按鈕...")
        
        # 從截圖看，按鈕在「線上啟動」標籤下方中間位置
        # 按鈕文字：「啟動試用授權」或「Activate Free License」
        # 使用較短的 timeout，因為按鈕可能不存在
        success = self.smart_click(
            x_ratio=0.2,
            y_ratio=0.35,
            target_text="啟動試用授權",
            image_path="desktop_settings/activate_free_license_btn.png",
            timeout=2
        )
        
        if success:
            self.logger.info("✅ 成功點擊啟用免費授權按鈕")
            # 等待授權啟動處理
            time.sleep(2)
        else:
            # 按鈕不存在，可能授權已經啟用過
            self.logger.info("ℹ️ 未找到啟用免費授權按鈕（授權可能已啟用）")
        
        return success
    
    def confirm_license_activation(self):
        """
        🎯 確認授權啟動成功
        點擊彈窗中的「確認」按鈕
        """
        self.logger.info("🖱️ 確認授權啟動...")
        
        # 尋找並點擊「確認」或「OK」按鈕
        # 彈窗按鈕通常在底部中間或右側
        success = self.smart_click(
            x_ratio=0.65,
            y_ratio=0.85,
            target_text="確認",
            timeout=2
        )
        
        if success:
            self.logger.info("✅ 已確認授權啟動")
            time.sleep(0.5)
        else:
            # 嘗試尋找 OK 按鈕
            self.logger.info("🔄 嘗試尋找 OK 按鈕...")
            success = self.smart_click(
                x_ratio=0.65,
                y_ratio=0.85,
                target_text="OK",
                timeout=2
            )
        
        return success
    
    def close_system_administration(self):
        """
        🎯 關閉系統管理視窗
        點擊「確認」或「OK」按鈕關閉視窗
        """
        self.logger.info("🖱️ 關閉系統管理視窗...")
        
        # 系統管理視窗的確認按鈕通常在右下角
        success = self.smart_click(
            x_ratio=0.72,
            y_ratio=0.95,
            target_text="確認",
            timeout=2
        )
        
        if success:
            self.logger.info("✅ 成功關閉系統管理視窗")
            # 等待視窗關閉
            self.wait_for_window_close(
                window_titles=["系統管理", "站點管理", "System Administration"],
                timeout=2
            )
        else:
            self.logger.warning("⚠️ 可能未成功關閉系統管理視窗")
        
        return success
