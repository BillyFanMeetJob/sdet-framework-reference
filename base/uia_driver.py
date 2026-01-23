# base/uia_driver.py
from pywinauto import Application, Desktop
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper
import time

class UIADriver:
    """
    封裝 PyWinAuto 的基礎操作，負責處理 UIA 協定的元件定位
    """
    def __init__(self, app_path=None, process_name="NxWitness.exe"):
        self.app = None
        self.main_window = None
        self.process_name = process_name
        self.timeout = 10

    def launch_app(self, executable_path):
        """
        啟動 Nx Witness 應用程式
        
        Args:
            executable_path: 應用程式的完整路徑（例如：C:\\Program Files\\Nx Witness\\NxWitness.exe）
        """
        try:
            print(f"[UIA] 正在啟動應用程式: {executable_path}")
            # 使用 uia backend 啟動應用程式
            self.app = Application(backend="uia").start(executable_path)
            
            # 等待幾秒讓視窗出現
            time.sleep(3)
            
            # 嘗試定位主視窗
            # 根據 dump 文件，主視窗標題通常包含 "Nx Witness"
            self.main_window = self.app.window(title_re=".*Nx Witness.*")
            
            # 等待主視窗可見
            self.main_window.wait('visible', timeout=10)
            
            print(f"[UIA] 成功啟動應用程式並定位主視窗")
        except Exception as e:
            print(f"[UIA] 啟動應用程式失敗: {e}")
            raise
    
    def connect(self):
        """連接到現有的 Nx Witness 應用程式"""
        try:
            # 使用 uia backend 連接
            self.app = Application(backend="uia").connect(path=self.process_name)
            # 根據 dump 文件，主視窗標題通常包含 "Nx Witness"
            self.main_window = self.app.window(title_re=".*Nx Witness.*")
            print(f"[UIA] 成功連接到應用程式: {self.process_name}")
        except Exception as e:
            print(f"[UIA] 連接失敗: {e}")
            raise

    def find_element_by_id(self, automation_id, parent=None, timeout=5):
        """透過 AutomationId 尋找元件"""
        window = parent if parent else self.main_window
        return window.child_window(auto_id=automation_id).wait('visible', timeout=timeout)

    def find_element_by_name(self, name, control_type=None, parent=None, timeout=5):
        """透過 Name (顯示文字) 尋找元件，例如伺服器名稱"""
        window = parent if parent else self.main_window
        criteria = {"title": name}
        if control_type:
            criteria["control_type"] = control_type
        
        return window.child_window(**criteria).wait('visible', timeout=timeout)

    def click_menu_button(self):
        """專門點擊左上角的漢堡選單 (根據 Dump Line 9)"""
        # Line 9: "Main Menu" "Button" "mainMenuButton"
        self.find_element_by_id("mainMenuButton").click()
        print("[UIA] 點擊主選單按鈕")