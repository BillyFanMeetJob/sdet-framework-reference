# 相對路徑: config.py
import os
import sys

def get_project_root():
    """
    取得專案根目錄
    
    支援兩種模式：
    1. 正常運行：使用當前檔案（config.py）所在目錄
    2. 打包成 EXE：使用 EXE 檔案所在目錄
    
    注意：EXE 執行時，會從 EXE 所在目錄查找 DemoData\\TestPlan.xlsx
    因此需要確保 EXE 和 DemoData 資料夾在同一目錄下，或放在專案根目錄
    """
    # 檢查是否在打包後的環境中運行（PyInstaller）
    if getattr(sys, 'frozen', False):
        # 打包後的環境：使用 EXE 檔案所在目錄
        # sys.executable 在打包後指向 EXE 檔案路徑
        # 這樣每次執行時，EXE 會自動從 EXE 所在目錄讀取 TestPlan.xlsx
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return exe_dir
    else:
        # 正常運行：使用當前檔案（config.py）所在目錄
        project_root = os.path.dirname(os.path.abspath(__file__))
        return project_root

class BaseConfig:
    PROJECT_ROOT = get_project_root()
    # 🎯 指向您的 DemoData
    TEST_PLAN_PATH = os.path.join(PROJECT_ROOT, "DemoData", "TestPlan.xlsx")
    RES_PATH = os.path.join(PROJECT_ROOT, "res") 
    LOG_PATH = os.path.join(PROJECT_ROOT, "logs")
    OCR_FONT_PATH = os.path.join(PROJECT_ROOT, "assets", "simhei.ttf")
    BASE_WINDOW_SIZE = (1920, 1200)

class DevConfig(BaseConfig):
    BASE_URL = "http://localhost:7001"
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "LAPTOP-QRJN5735"
    # 管理員密碼（用於伺服器設定確認彈窗）
    ADMIN_PASSWORD = "1q2w!Q@W"  # 預設空密碼，如有密碼請在此設置
    
    # Nx Cloud 登錄資訊
    NX_CLOUD_EMAIL = "billy.19920917@gmail.com"  # Nx Cloud 登錄郵箱
    NX_CLOUD_PASSWORD = "1q2w!Q@W"  # Nx Cloud 登錄密碼（預設與管理員密碼相同）
    
    # ==================== Android Mobile App 配置 ====================
    # Appium Server 配置
    APPIUM_SERVER_URL = "http://localhost:4723"  # Appium Server 地址
    APPIUM_COMMAND_TIMEOUT = 120  # Appium 命令超時時間（秒）
    
    # Android 設備配置
    ANDROID_PLATFORM_VERSION = None  # Android 版本（如果為 None，則自動使用第一個可用設備的版本）
    ANDROID_DEVICE_NAME = "Android Device"  # 設備名稱
    ANDROID_UDID = None  # 設備 UDID（如果為 None，則使用第一個連接的設備）
    ANDROID_AUTOMATION_NAME = "UiAutomator2"  # 自動化引擎
    
    # Nx Witness App 配置
    ANDROID_APP_PACKAGE = "com.networkoptix.nxwitness"  # App Package Name（實際的 Package）
    ANDROID_APP_ACTIVITY = None  # 啟動 Activity（如果為 None，則讓 Appium 自動找到主 Activity）
    ANDROID_APP_PATH = None  # APK 文件路徑（如果為 None，則使用已安裝的 App）
    
    # 登錄頁面特殊配置
    LOGIN_SURFACEVIEW_TAP_COORDINATES = (550, 1500)  # 破解黑盒子 (SurfaceView) 的座標點擊位置
    LOGIN_ANIMATION_WAIT_TIME = 3  # 等待動畫轉場時間（秒）
    
    # Case 4-2 主頁面點擊服務器座標（第一步點擊 server）
    CASE4_2_SERVER_CLICK_COORDINATES = (550, 500)
    
    # Case 4-2 主頁面點擊攝像頭座標（選擇攝像頭，當 SurfaceView 無法定位時使用）
    # 如果為 None，則嘗試元素定位；如果提供了座標，則優先使用座標點擊
    CASE4_2_CAMERA_CLICK_COORDINATES = (540, 800)  # 攝像頭列表中的第一個攝像頭位置（可根據實際情況調整）
    
    # Android 等待超時配置
    ANDROID_DEFAULT_TIMEOUT = 10  # 默認等待超時時間（秒）
    ANDROID_IMPLICIT_WAIT = 5  # 隱式等待時間（秒）
    
    # VLM (視覺語言模型) 設定
    VLM_ENABLED = True  # 是否啟用 VLM 辨識
    VLM_BACKEND = "ollama"  # 後端: 'ollama' (本地), 'openai', 'anthropic'
    VLM_MODEL = "llava"  # 模型名稱: 'llava', 'bakllava', 'gpt-4o', 'claude-3-5-sonnet-20241022'
    VLM_PRIORITY = 2  # VLM 在辨識優先級中的位置 (1=最高, 2=OK Script後, 3=OCR後)

def get_current_config():
    return DevConfig()

EnvConfig = get_current_config()


# ==================== 新增配置類（追加模式，不覆蓋現有內容）====================

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Thresholds:
    """
    視覺辨識閾值配置
    
    用於像素顏色判定、等待時間等可配置的閾值參數。
    所有硬編碼的魔法數字都應該移到這裡。
    """
    # 黑色像素判定閾值（RGB 值低於此值視為黑色）
    BLACK_PIXEL_THRESHOLD: int = 10
    
    # 黑色像素比例閾值（超過此比例認為日曆未打開）
    BLACK_RATIO_THRESHOLD: float = 0.95
    
    # 樹狀結構展開動畫等待時間（秒）
    TREE_EXPAND_WAIT_TIME: float = 1.0
    
    # 綠色像素判定閾值（用於日曆錄影標記識別）
    GREEN_THRESHOLD_MIN: int = 100  # G > 100
    RED_THRESHOLD_MAX: int = 100    # R < 100
    BLUE_THRESHOLD_MAX: int = 100   # B < 100
    
    # 點擊後等待時間（秒）
    CLICK_WAIT_TIME: float = 0.3
    MENU_WAIT_TIME: float = 0.8
    SETTINGS_WAIT_TIME: float = 1.0


@dataclass
class AppPaths:
    """
    應用程式資源路徑配置
    
    所有圖片路徑、資源路徑都應該在這裡定義，避免硬編碼。
    """
    # 主頁面資源路徑
    USB_CAM_ITEM: str = "desktop_main/usb_cam_item.png"
    SERVER_ICON: str = "desktop_main/server_icon.png"
    MENU_ICON: str = "desktop_main/menu_icon.png"
    LOCAL_SETTINGS: str = "desktop_main/local_settings.png"
    ADD_CAMERA_MENU: str = "desktop_main/add_camera_menu.png"
    CAMERA_SETTINGS_MENU: str = "desktop_main/camera_settings_menu.png"
    
    # 時間軸相關資源
    TIMELINE_PAUSE: str = "desktop_main/timeline_pause.png"
    TIMELINE_PLAY: str = "desktop_main/timeline_play.png"
    
    # 設定頁面資源
    APPEARANCE_TAB: str = "desktop_settings/appearance_tab.png"
    LANGUAGE_DROPDOWN: str = "desktop_settings/language_dropdown.png"
    TRADITIONAL_CHINESE: str = "desktop_settings/traditional_chinese.png"
    APPLY_BTN: str = "desktop_settings/apply_btn.png"
    RESTART_NOW: str = "desktop_settings/restart_now.png"
    RESTART_NOW_BTN: str = "desktop_settings/restart_now_btn.png"


@dataclass
class CameraSettings:
    """
    攝影機相關配置
    
    攝影機名稱、預設設定等可配置參數。
    """
    # 預設攝影機名稱
    DEFAULT_CAMERA_NAME: str = "usb_cam"
    
    # 攝影機列表搜索區域比例（相對於視窗）
    LEFT_PANEL_X_RATIO: float = 0.3      # 左側面板寬度比例
    LEFT_PANEL_Y_START: float = 0.10     # 搜索區域起始 Y 比例（Server 下方）
    LEFT_PANEL_Y_HEIGHT: float = 0.20    # 搜索區域高度比例
    
    # Server Icon 位置比例
    SERVER_ICON_X_RATIO: float = 0.08
    SERVER_ICON_Y_RATIO: float = 0.08
    
    # Camera Item 位置比例
    CAMERA_ITEM_X_RATIO: float = 0.10
    CAMERA_ITEM_Y_RATIO: float = 0.18


@dataclass
class TimelineSettings:
    """
    時間軸相關配置
    
    時間軸位置、點擊區域等幾何配置。
    """
    # 時間軸位置（相對於視窗底部）
    TIMELINE_Y_RATIO: float = 0.90  # 底部 10% 位置
    
    # 時間軸水平位置比例
    TIMELINE_CENTER_X_RATIO: float = 0.5   # 中央
    TIMELINE_LEFT_X_RATIO: float = 0.15   # 左側 1/4
    TIMELINE_RIGHT_X_RATIO: float = 0.85   # 右側 3/4
    
    # 時間軸掃描區域
    TIMELINE_SCAN_LEFT_RATIO: float = 0.15  # 左側邊界
    TIMELINE_SCAN_RIGHT_RATIO: float = 0.80  # 右側邊界（嚴格限制，避免抓到 Live 錄影段）


@dataclass
class CalendarSettings:
    """
    日曆相關配置（已更新為 Anchor 優先策略）
    
    注意：這些靜態比例僅作為 Fallback，優先使用圖像錨點定位。
    """
    # [DEPRECATED] 舊的靜態比例僅作為 Fallback
    # 優先使用 _get_calendar_region_by_anchor() 動態計算日曆區域
    # 這些值僅在錨點定位失敗時使用
    CALENDAR_LEFT_RATIO: float = 0.70   # 左側邊界（稍微靠右一點）
    CALENDAR_RIGHT_RATIO: float = 1.0   # [關鍵修正] 必須是 1.0 (螢幕最右邊)，確保覆蓋到最右側
    CALENDAR_TOP_RATIO: float = 0.20    # 頂部邊界
    CALENDAR_BOTTOM_RATIO: float = 0.80 # 底部邊界（擴大下方搜尋範圍）
    
    # 日期點擊偏移（相對於綠色標記）
    DATE_CLICK_OFFSET_Y: int = 15  # 向上偏移像素（點擊日期文字而非綠線）
    
    # [UPDATED] 顏色判定閾值（用於區分亮綠色與白色文字）
    # 綠色亮度門檻 (排除過暗的像素)
    GREEN_MIN_BRIGHTNESS: int = 140  # G 通道必須大於此值
    
    # 綠色主導門檻 (Green Dominance)
    # G 必須比 R 和 B 高出這個數值，才能被視為綠色
    # 這能有效排除白色 (G ~= R) 和灰色 (G ~= R)
    GREEN_DOMINANCE_OFFSET: int = 40  # G > R + offset AND G > B + offset
    
    # 日曆區域高度（從標題上邊緣向下延伸的像素數）
    CALENDAR_REGION_HEIGHT: int = 370  # 向下延伸 370px，不延伸到最下面


@dataclass
class LocatorConfig:
    """
    定位器配置（Locator Configuration）
    
    收納所有在 MainPage 和 CameraPage 中硬編碼的比例（x_ratio, y_ratio）與偏移量（offset）。
    使用具備業務意義的變數命名，例如 RECORDING_TAB_REGION 或 CALENDAR_OPEN_BTN。
    
    注意：所有 image_path 都應該相對於 RES_PATH，在 Page 層統一拼接。
    """
    
    # ==================== MainPage 定位器 ====================
    
    # 主選單圖標（左上角）
    MENU_ICON_X_RATIO: float = 0.02
    MENU_ICON_Y_RATIO: float = 0.03
    MENU_ICON_IMAGE: str = "desktop_main/menu_icon.png"
    
    # 本地設置選單項目
    LOCAL_SETTINGS_X_RATIO: float = 0.1
    LOCAL_SETTINGS_Y_RATIO: float = 0.32
    # 注意：LOCAL_SETTINGS_IMAGE 已在 AppPaths 中定義，這裡不重複
    
    # 日曆圖標（右下角）
    CALENDAR_ICON_X_RATIO: float = 0.92  # 視窗寬度 92% 處
    CALENDAR_ICON_Y_RATIO: float = 0.04  # 視窗底部向上 4% 處
    CALENDAR_ICON_OFFSET_X: int = 0  # 向右偏移（從原本的 -10 改為 0）
    CALENDAR_ICON_OFFSET_Y: int = 0  # Y 軸不需要偏移
    CALENDAR_ICON_IMAGE: str = "desktop_main/calendar_icon.png"
    
    # 日期點擊偏移（補償 VLM 常見的偏左上誤差）
    DATE_CLICK_OFFSET_X: int = 5   # 向右偏移 5 像素，補償 VLM 常見的偏左誤差
    DATE_CLICK_OFFSET_Y: int = 15  # 向下偏移 15 像素，補償 VLM 常見的偏上誤差
    
    # 日期備選點擊偏移（fallback 時使用）
    DATE_FALLBACK_OFFSET_X: int = 0
    DATE_FALLBACK_OFFSET_Y: int = 0
    
    # ==================== CameraPage 定位器 ====================
    
    # 伺服器節點（右鍵點擊以打開添加攝影機對話框）
    SERVER_NODE_X_RATIO: float = 0.05
    SERVER_NODE_Y_RATIO: float = 0.15
    SERVER_NODE_IMAGE: str = "desktop_main/server_node.png"
    
    # 添加攝影機選單項目（右鍵選單中）
    ADD_CAMERA_MENU_X_RATIO: float = 0.1
    ADD_CAMERA_MENU_Y_RATIO: float = 0.2
    ADD_CAMERA_MENU_IMAGE: str = "desktop_main/add_camera_menu.png"
    
    # 攝影機設定選單項目（右鍵選單中）
    CAMERA_SETTINGS_MENU_X_RATIO: float = 0.22
    CAMERA_SETTINGS_MENU_Y_RATIO: float = 0.38
    CAMERA_SETTINGS_MENU_IMAGE: str = "desktop_main/camera_settings_menu.png"
    
    # 錄影分頁簽（攝影機設定視窗中）
    RECORDING_TAB_X_RATIO: float = 0.25
    RECORDING_TAB_Y_RATIOS: List[float] = field(default_factory=lambda: [0.10, 0.12, 0.15, 0.08])  # 嘗試多個垂直位置
    RECORDING_TAB_IMAGE: str = "desktop_settings/recording_tab.png"
    
    # Radio Button 'Y' 位置（錄影分頁簽中的啟用錄影選項）
    RADIO_Y_X_RATIO: float = 0.10  # 左上角偏左一點
    RADIO_Y_Y_RATIO: float = 0.15  # 分頁簽下方


# 創建全局配置實例（追加到現有配置）
_thresholds = Thresholds()
_app_paths = AppPaths()
_camera_settings = CameraSettings()
_timeline_settings = TimelineSettings()
_calendar_settings = CalendarSettings()
_locator_config = LocatorConfig()

# 將新配置添加到 EnvConfig（通過擴展類的方式）
class ExtendedConfig(DevConfig):
    """擴展配置類，包含所有新增的配置"""
    THRESHOLDS = _thresholds
    APP_PATHS = _app_paths
    CAMERA_SETTINGS = _camera_settings
    TIMELINE_SETTINGS = _timeline_settings
    CALENDAR_SETTINGS = _calendar_settings
    LOCATOR_CONFIG = _locator_config

# 更新全局配置實例
EnvConfig = ExtendedConfig()