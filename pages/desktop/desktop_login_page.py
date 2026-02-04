# 相對路徑: pages/desktop_login_page.py

from base.desktop_app import DesktopApp
import time

class DesktopLoginPage(DesktopApp):
    def __init__(self):
        super().__init__()

    def select_server_and_auto_login(self, server_name):
        """ 點擊伺服器入口 """
        self.logger.info(f"🖱️ 正在登錄伺服器: {server_name}")
        
        # 🎯 使用 UILocator：簡潔且易讀
        from config import EnvConfig
        locator_config = EnvConfig.LOCATOR_CONFIG
        
        # 方式 1：使用新的 UILocator（推薦）
        server_locator = locator_config.SERVER_TILE.with_text(server_name)
        self.click_with_locator(server_locator)
        
        # 方式 2：向後兼容的舊方式（仍然可用）
        # x_ratio = getattr(locator_config, 'SERVER_TILE_X_RATIO', 0.4995)
        # y_ratio = getattr(locator_config, 'SERVER_TILE_Y_RATIO', 0.6375)
        # image_path = getattr(locator_config, 'SERVER_TILE_IMAGE', "desktop_login/server_tile.png")
        # self.smart_click(x_ratio=x_ratio, y_ratio=y_ratio, timeout=3, target_text=server_name, image_path=image_path)
        
        # 登錄後的加載動畫較長，請給予足夠時間
        time.sleep(1.5) 
        return self