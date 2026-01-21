# 相對路徑: pages/desktop_login_page.py

from base.desktop_app import DesktopApp
import time

class DesktopLoginPage(DesktopApp):
    def __init__(self):
        super().__init__()

    def select_server_and_auto_login(self, server_name):
        """ 點擊伺服器入口 """
        self.logger.info(f"🖱️ 正在登錄伺服器: {server_name}")
        
        # 使用真實記錄的座標：x_ratio=0.4995, y_ratio=0.6375 (來自 1920x1200 視窗)
        self.smart_click(
            x_ratio=0.4995, 
            y_ratio=0.6375, 
            timeout=3,
            target_text=server_name, 
            image_path="desktop_login/server_tile.png"
        )
        
        # 登錄後的加載動畫較長，請給予足夠時間
        time.sleep(1.5) 
        return self