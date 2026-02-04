# 相對路徑: pages/desktop_login_page.py

from base.desktop_app import DesktopApp
import time

class DesktopLoginPage(DesktopApp):
    def __init__(self):
        super().__init__()

    def select_server_and_auto_login(self, server_name):
        """ 點擊伺服器入口 """
        self.logger.info(f"🖱️ 正在登錄伺服器: {server_name}")
        
        # 🎯 從 LocatorConfig 獲取配置
        from config import EnvConfig
        locator = getattr(EnvConfig, 'LOCATOR_CONFIG', None)
        x_ratio = getattr(locator, 'SERVER_TILE_X_RATIO', 0.4995) if locator else 0.4995
        y_ratio = getattr(locator, 'SERVER_TILE_Y_RATIO', 0.6375) if locator else 0.6375
        image_path = getattr(locator, 'SERVER_TILE_IMAGE', "desktop_login/server_tile.png") if locator else "desktop_login/server_tile.png"
        
        self.smart_click(
            x_ratio=x_ratio, 
            y_ratio=y_ratio, 
            timeout=3,
            target_text=server_name, 
            image_path=image_path
        )
        
        # 登錄後的加載動畫較長，請給予足夠時間
        time.sleep(1.5) 
        return self