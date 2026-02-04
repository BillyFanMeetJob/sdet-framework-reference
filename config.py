# 相對路徑: config.py
import os
import sys
from enum import Enum
from typing import Optional


class PlatformType(Enum):
    """平台類型枚舉"""
    DESKTOP = "desktop"
    WEB = "web"
    ANDROID = "android"


class ConfigManager:
    """配置管理器 - 管理當前運行平台"""
    
    _current_platform: Optional[PlatformType] = None
    
    @classmethod
    def set_platform(cls, platform: PlatformType) -> None:
        """設置當前平台"""
        cls._current_platform = platform
    
    @classmethod
    def get_current_platform(cls) -> PlatformType:
        """獲取當前平台，默認為 DESKTOP"""
        if cls._current_platform is None:
            # 從環境變數讀取，默認為 DESKTOP
            platform_str = os.getenv("TEST_PLATFORM", "desktop").lower()
            try:
                cls._current_platform = PlatformType(platform_str)
            except ValueError:
                cls._current_platform = PlatformType.DESKTOP
        return cls._current_platform


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
    # config.py 建議配置
    # ⚠️ Chrome 調試端口必須與 Nx Cloud Web 服務器端口不同
    BROWSER_DEBUG_PORT = 9222  # Chrome 默認調試端口
    # 啟動 Nx 測試前，先確保環境中所有瀏覽器都帶有調試端口
    BROWSER_ARGUMENTS = [f"--remote-debugging-port={BROWSER_DEBUG_PORT}", "--no-first-run"]

    BASE_URL = "http://localhost:7001"  # Nx Cloud Web 服務器端口
    NX_EXE_PATH = r"C:\Program Files\Network Optix\Nx Witness\Client\6.1.0.42176\Nx Witness Chinese Launcher.exe"
    DEFAULT_SERVER_NAME = "LAPTOP-QRJN5735"
    # 管理員密碼（用於伺服器設定確認彈窗）
    ADMIN_PASSWORD = "1q2w!Q@W"  # 預設空密碼，如有密碼請在此設置
    
    # ================================================================
    # AI Vision Learning Mode (VLM 自癒機制)
    # ================================================================
    # 是否啟用 VLM 學習模式（用於 UI 變動觀測與自動修復建議）
    ENABLE_VLM_LEARNING: bool = False  # 預設關閉，避免消耗 API Token
    
    # VLM API 配置（根據使用的模型選擇）
    VLM_PROVIDER: str = "gemini"  # 可選: "gemini", "ollama", "openai"
    VLM_API_KEY: str = os.getenv("GEMINI_API_KEY", "")  # 從環境變數讀取
    VLM_MODEL: str = "gemini-pro-vision"  # 或 "gpt-4-vision-preview"
    
    # 隨機掃描頻率（當 ENABLE_VLM_LEARNING=True 時）
    # 即使操作成功，也會在每 N 次操作中隨機執行一次 VLM 掃描
    VLM_RANDOM_SCAN_FREQUENCY: int = 10  # 每 10 次操作掃描 1 次
    
    # AI 分析結果存放路徑
    AI_INTELLIGENCE_LOG_DIR: str = os.path.join(BaseConfig.LOG_PATH, "ai_intelligence")
    
    # Nx Cloud 登錄資訊
    NX_CLOUD_EMAIL = "fanzhenglun2@gmail.com"  # Nx Cloud 登錄郵箱
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
    
    # ==================== Case 4-1/4-2 Mobile ADB 模式座標配置 ====================
    # 螢幕基準尺寸（用於座標比例計算）
    MOBILE_SCREEN_SIZE = (1080, 2400)
    
    # Case 4-1: 登錄流程座標（ADB 模式）
    CASE4_1_LOGIN_BUTTON_Y_PERCENT = 0.625  # Log In 按鈕 Y 位置（相對於螢幕高度）
    CASE4_1_EMAIL_INPUT_Y_PERCENT = 0.46  # Email 輸入框 Y 位置
    CASE4_1_NEXT_BUTTON_Y_PERCENT = 0.606  # Next 按鈕 Y 位置
    CASE4_1_PASSWORD_INPUT_Y_PERCENT = 0.47  # 密碼輸入框 Y 位置
    CASE4_1_FINAL_LOGIN_BUTTON_Y_PERCENT = 0.606  # 最終 Log In 按鈕 Y 位置
    
    # Case 4-2: 播放流程座標（ADB 模式，基於 1080x2400 螢幕）
    CASE4_2_SERVER_CLICK_COORDINATES = (540, 570)  # Server 卡片位置（精確測量）
    CASE4_2_THUMBNAIL_CLICK_COORDINATES = (273, 400)  # 影片縮圖位置（精確測量）
    CASE4_2_FULLSCREEN_GOTIT_COORDINATES = (392, 270)  # 全屏提示 "Got it" 按鈕
    CASE4_2_CALENDAR_ICON_COORDINATES = (35, 2256)  # 日曆圖標位置（精確測量）
    CASE4_2_TODAY_DATE_COORDINATES = (99, 1527)  # 今天日期位置（精確測量）
    CASE4_2_PAUSE_BUTTON_COORDINATES = (542, 1889)  # 暫停按鈕位置（精確測量）
    CASE4_2_SHOW_CONTROLS_TAP = (540, 1200)  # 點擊顯示控制的位置
    
    # Case 4-2 舊配置（Appium 模式，保留兼容）
    CASE4_2_CAMERA_CLICK_COORDINATES = (540, 800)  # 攝像頭列表中的第一個攝像頭位置
    
    # Android 等待超時配置
    ANDROID_DEFAULT_TIMEOUT = 10  # 默認等待超時時間（秒）
    ANDROID_IMPLICIT_WAIT = 5  # 隱式等待時間（秒）
    
    # VLM (視覺語言模型) 設定
    VLM_ENABLED = True  # 是否啟用 VLM 辨識
    VLM_MODEL = "llava"  # Ollama 模型名稱: 'llava' (預設), 'bakllava', 'llava:13b'
    VLM_PRIORITY = 2  # VLM 在辨識優先級中的位置 (1=最高, 2=OK Script後, 3=OCR後)
    
    # Gemini API 配置（用於 UnifiedVLM 備援策略）
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Gemini API 金鑰（從環境變數讀取）
    
    # ==================== Web 自動化配置 (Anti-Bot Detection) ====================
    
    # WebDriver 反封號配置
    ENABLE_ANTI_BOT = True  # 啟用反封號機制（User-Agent 隨機化、指紋隱藏）
    ENABLE_HUMAN_DELAY = True  # 啟用擬人化延遲（點擊前隨機停頓）
    
    # 擬人化延遲範圍（秒）
    MIN_HUMAN_DELAY = 0.5  # 最小延遲：模擬快速反應的使用者
    MAX_HUMAN_DELAY = 2.0  # 最大延遲：模擬謹慎思考的使用者
    MIN_TYPING_DELAY = 0.05  # 打字最小延遲（秒/字元）
    MAX_TYPING_DELAY = 0.15  # 打字最大延遲（秒/字元）
    
    # User-Agent 隨機化配置
    ENABLE_RANDOM_USER_AGENT = True  # 啟用 User-Agent 隨機化
    USER_AGENT_POOL = [
        # Chrome 120+ (Windows 10/11)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        
        # Edge (Chromium)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        
        # macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # Accept-Language 隨機化配置
    ACCEPT_LANGUAGE_POOL = [
        "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",  # 繁體中文優先
        "zh-TW,zh;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",  # 簡體中文優先
        "en-US,en;q=0.9,zh-TW;q=0.8",  # 英文優先
        "en-US,en;q=0.9",
    ]
    
    # 其他反偵測配置
    DISABLE_AUTOMATION_CONTROLLED = True  # 移除 navigator.webdriver 標記
    ENABLE_RANDOM_VIEWPORT = True  # 啟用隨機視窗大小
    VIEWPORT_SIZE_POOL = [
        (1920, 1080),  # Full HD
        (1366, 768),   # 常見筆電解析度
        (1536, 864),   # 1.5x 縮放
        (1280, 720),   # HD
    ]
    
    # ==================== Playwright 配置 (Modern Web Automation) ====================
    
    # Playwright 引擎配置
    USE_PLAYWRIGHT = True  # 啟用 Playwright（False 則使用 Selenium）
    PLAYWRIGHT_BROWSER = "chromium"  # 瀏覽器類型：chromium, firefox, webkit
    PLAYWRIGHT_HEADLESS = False  # 無頭模式
    PLAYWRIGHT_SLOW_MO = 0  # 慢動作模式（ms）：用於 Debug，0 表示正常速度
    PLAYWRIGHT_DEBUG_PAUSE = False  # 調試暫停模式：每個步驟後暫停等待用戶確認
    PLAYWRIGHT_DEBUG_PAUSE_SECONDS = 30  # 調試暫停時間（秒）
    
    # Playwright 反封號增強配置
    PLAYWRIGHT_VIEWPORT_JITTER = 10  # 視窗大小隨機擾動（像素）：±5-10px
    PLAYWRIGHT_IGNORE_HTTPS_ERRORS = True  # 忽略 HTTPS 錯誤
    PLAYWRIGHT_DEVICE_SCALE_FACTOR = 1.0  # 設備縮放比例
    
    # Playwright 超時配置（毫秒）
    PLAYWRIGHT_DEFAULT_TIMEOUT = 30000  # 預設超時：30 秒
    PLAYWRIGHT_NAVIGATION_TIMEOUT = 60000  # 導航超時：60 秒
    
    # Playwright 點擊延遲配置（毫秒）
    PLAYWRIGHT_CLICK_DELAY_MIN = 50  # 點擊最小延遲
    PLAYWRIGHT_CLICK_DELAY_MAX = 200  # 點擊最大延遲
    
    # Playwright 滑鼠軌跡模擬配置
    PLAYWRIGHT_ENABLE_HOVER_BEFORE_CLICK = True  # 點擊前先 hover
    PLAYWRIGHT_HOVER_OFFSET_MAX = 5  # hover 隨機偏移（像素）

def get_current_config():
    return DevConfig()

EnvConfig = get_current_config()


# ==================== 新增配置類（追加模式，不覆蓋現有內容）====================

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class UILocator:
    """
    UI 元素定位器
    
    封裝 UI 元素的所有定位相關屬性，包括座標比例、偏移量、圖片路徑等。
    使用此類可以避免在方法中傳入大量參數，提高代碼可讀性。
    
    Attributes:
        x_ratio: X 軸座標比例 (0.0 - 1.0)
        y_ratio: Y 軸座標比例 (0.0 - 1.0)
        image_path: 圖片路徑（相對於 RES_PATH）
        offset_x: X 軸偏移量（像素）
        offset_y: Y 軸偏移量（像素）
        target_text: 目標文字（用於 OCR/VLM）
        is_relative: 是否使用相對座標
        from_bottom: 是否從底部計算 Y 座標
        timeout: 超時時間（秒）
        use_ok_script: 是否使用 OK Script 圖片識別
        use_vlm: 是否使用 VLM 識別
        click_type: 點擊類型（'left', 'right'）
        clicks: 點擊次數（1=單擊, 2=雙擊）
        
    Example:
        # 創建定位器
        menu_locator = UILocator(
            x_ratio=0.02,
            y_ratio=0.03,
            image_path="desktop_main/menu_icon.png",
            timeout=3
        )
        
        # 使用定位器
        self.click_with_locator(menu_locator)
    """
    x_ratio: float
    y_ratio: float
    image_path: Optional[str] = None
    offset_x: int = 0
    offset_y: int = 0
    target_text: Optional[str] = None
    is_relative: bool = False
    from_bottom: bool = False
    timeout: float = 3.0
    use_ok_script: bool = True
    use_vlm: Optional[bool] = None
    click_type: str = 'left'
    clicks: int = 1
    
    def to_smart_click_kwargs(self) -> dict:
        """
        轉換為 smart_click 方法的參數字典
        
        Returns:
            dict: 包含所有 smart_click 參數的字典
        """
        return {
            'x_ratio': self.x_ratio,
            'y_ratio': self.y_ratio,
            'image_path': self.image_path,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'target_text': self.target_text,
            'is_relative': self.is_relative,
            'from_bottom': self.from_bottom,
            'timeout': self.timeout,
            'use_ok_script': self.use_ok_script,
            'use_vlm': self.use_vlm,
            'click_type': self.click_type,
            'clicks': self.clicks
        }
    
    def with_offset(self, offset_x: int = 0, offset_y: int = 0) -> 'UILocator':
        """
        創建一個帶有額外偏移的新定位器
        
        Args:
            offset_x: 額外的 X 軸偏移
            offset_y: 額外的 Y 軸偏移
            
        Returns:
            UILocator: 新的定位器實例
        """
        from copy import copy
        new_locator = copy(self)
        new_locator.offset_x += offset_x
        new_locator.offset_y += offset_y
        return new_locator
    
    def with_text(self, target_text: str) -> 'UILocator':
        """
        創建一個帶有目標文字的新定位器
        
        Args:
            target_text: 目標文字
            
        Returns:
            UILocator: 新的定位器實例
        """
        from copy import copy
        new_locator = copy(self)
        new_locator.target_text = target_text
        return new_locator
    
    def as_relative(self) -> 'UILocator':
        """
        創建一個使用相對座標的新定位器
        
        Returns:
            UILocator: 新的定位器實例
        """
        from copy import copy
        new_locator = copy(self)
        new_locator.is_relative = True
        return new_locator


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
    
    使用 UILocator 類封裝所有 UI 元素的定位信息。
    提供更好的可讀性和可維護性。
    
    注意：所有 image_path 都應該相對於 RES_PATH。
    """
    
    # ==================== LoginPage 定位器 ====================
    
    # 伺服器入口（Server Tile）
    # 使用真實記錄的座標：x_ratio=0.4995, y_ratio=0.6375 (來自 1920x1200 視窗)
    SERVER_TILE: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.4995,
        y_ratio=0.6375,
        image_path="desktop_login/server_tile.png",
        timeout=3
    ))
    
    # 向後兼容：保留舊的屬性名稱
    SERVER_TILE_X_RATIO: float = 0.4995
    SERVER_TILE_Y_RATIO: float = 0.6375
    SERVER_TILE_IMAGE: str = "desktop_login/server_tile.png"
    
    # ==================== SettingsPage 定位器 ====================
    
    # 語言下拉選單
    # 使用真實記錄的座標：x_ratio=0.5793, y_ratio=0.1936 (來自 706x847 視窗)
    LANGUAGE_DROPDOWN: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.5793,
        y_ratio=0.1936,
        image_path="desktop_settings/language_dropdown.png",
        timeout=1.5
    ))
    
    # 向後兼容
    LANGUAGE_DROPDOWN_X_RATIO: float = 0.5793
    LANGUAGE_DROPDOWN_Y_RATIO: float = 0.1936
    LANGUAGE_DROPDOWN_IMAGE: str = "desktop_settings/language_dropdown.png"
    
    # 繁體中文選項（相對於語言下拉選單）
    TRADITIONAL_CHINESE: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0,
        y_ratio=40,
        image_path="desktop_settings/traditional_chinese.png",
        is_relative=True,
        use_ok_script=True,
        use_vlm=False,
        timeout=2
    ))
    
    # 向後兼容
    TRADITIONAL_CHINESE_OFFSET_X: int = 0
    TRADITIONAL_CHINESE_OFFSET_Y: int = 40
    TRADITIONAL_CHINESE_IMAGE: str = "desktop_settings/traditional_chinese.png"
    
    # 套用按鈕
    # 使用真實記錄的座標：x_ratio=0.7351, y_ratio=0.9445 (來自 706x847 視窗)
    APPLY_BTN: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.7351,
        y_ratio=0.9445,
        image_path="desktop_settings/apply_btn.png",
        timeout=1.5
    ))
    
    # 向後兼容
    APPLY_BTN_X_RATIO: float = 0.7351
    APPLY_BTN_Y_RATIO: float = 0.9445
    APPLY_BTN_IMAGE: str = "desktop_settings/apply_btn.png"
    
    # ==================== MainPage 定位器 ====================
    
    # 主選單圖標（左上角）
    MENU_ICON: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.02,
        y_ratio=0.03,
        image_path="desktop_main/menu_icon.png",
        timeout=3
    ))
    
    # 向後兼容
    MENU_ICON_X_RATIO: float = 0.02
    MENU_ICON_Y_RATIO: float = 0.03
    MENU_ICON_IMAGE: str = "desktop_main/menu_icon.png"
    
    # 本地設置選單項目
    LOCAL_SETTINGS: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.1,
        y_ratio=0.32,
        image_path="desktop_main/local_settings.png",
        is_relative=True,
        timeout=3
    ))
    
    # 向後兼容
    LOCAL_SETTINGS_X_RATIO: float = 0.1
    LOCAL_SETTINGS_Y_RATIO: float = 0.32
    
    # 日曆圖標（右下角）
    CALENDAR_ICON: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.92,
        y_ratio=0.04,
        image_path="desktop_main/calendar_icon.png",
        offset_x=0,
        offset_y=0,
        from_bottom=True,
        use_ok_script=False,
        use_vlm=False,
        timeout=3
    ))
    
    # 向後兼容
    CALENDAR_ICON_X_RATIO: float = 0.92
    CALENDAR_ICON_Y_RATIO: float = 0.04
    CALENDAR_ICON_OFFSET_X: int = 0
    CALENDAR_ICON_OFFSET_Y: int = 0
    CALENDAR_ICON_IMAGE: str = "desktop_main/calendar_icon.png"
    
    # 日期點擊偏移（補償 VLM 常見的偏左上誤差）
    DATE_CLICK_OFFSET_X: int = 5   # 向右偏移 5 像素，補償 VLM 常見的偏左誤差
    DATE_CLICK_OFFSET_Y: int = 15  # 向下偏移 15 像素，補償 VLM 常見的偏上誤差
    
    # 日期備選點擊偏移（fallback 時使用）
    DATE_FALLBACK_OFFSET_X: int = 0
    DATE_FALLBACK_OFFSET_Y: int = 0
    
    # 暫停按鈕（時間軸控制）
    PAUSE_BUTTON: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.5,  # 時間軸中心
        y_ratio=0.95,  # 時間軸位置
        image_path="desktop_main/timeline_pause.png",
        use_ok_script=True,
        use_vlm=False,
        timeout=2
    ))
    
    # 播放按鈕（時間軸控制）
    PLAY_BUTTON: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.5,  # 時間軸中心
        y_ratio=0.95,  # 時間軸位置
        image_path="desktop_main/timeline_play.png",
        use_ok_script=True,
        use_vlm=False,
        timeout=2
    ))
    
    # ==================== SettingsPage 定位器 ====================
    
    # 外觀分頁簽
    APPEARANCE_TAB: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.1686,
        y_ratio=0.0720,
        image_path="desktop_settings/appearance_tab.png",
        use_ok_script=True,
        use_vlm=False,
        timeout=3
    ))
    
    # ==================== CameraPage 定位器 ====================
    
    # 伺服器節點（右鍵點擊以打開添加攝影機對話框）
    SERVER_NODE: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.05,
        y_ratio=0.15,
        image_path="desktop_main/server_node.png",
        click_type='right',
        timeout=3
    ))
    
    # 向後兼容
    SERVER_NODE_X_RATIO: float = 0.05
    SERVER_NODE_Y_RATIO: float = 0.15
    SERVER_NODE_IMAGE: str = "desktop_main/server_node.png"
    
    # 添加攝影機選單項目（右鍵選單中）
    ADD_CAMERA_MENU: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.1,
        y_ratio=0.2,
        image_path="desktop_main/add_camera_menu.png",
        is_relative=True,
        timeout=3
    ))
    
    # 向後兼容
    ADD_CAMERA_MENU_X_RATIO: float = 0.1
    ADD_CAMERA_MENU_Y_RATIO: float = 0.2
    ADD_CAMERA_MENU_IMAGE: str = "desktop_main/add_camera_menu.png"
    
    # 攝影機設定選單項目（右鍵選單中）
    CAMERA_SETTINGS_MENU: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.22,
        y_ratio=0.38,
        image_path="desktop_main/camera_settings_menu.png",
        timeout=3
    ))
    
    # 向後兼容
    CAMERA_SETTINGS_MENU_X_RATIO: float = 0.22
    CAMERA_SETTINGS_MENU_Y_RATIO: float = 0.38
    CAMERA_SETTINGS_MENU_IMAGE: str = "desktop_main/camera_settings_menu.png"
    
    # 錄影分頁簽（攝影機設定視窗中）
    RECORDING_TAB_X_RATIO: float = 0.25
    RECORDING_TAB_Y_RATIOS: List[float] = field(default_factory=lambda: [0.10, 0.12, 0.15, 0.08])  # 嘗試多個垂直位置
    RECORDING_TAB_IMAGE: str = "desktop_settings/recording_tab.png"
    
    # ==================== LicenseSettingsPage 定位器 ====================
    
    # 系統管理選單項目
    SYSTEM_ADMIN_MENU: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.12,
        y_ratio=0.16,
        timeout=2
    ))
    
    # 授權分頁簽
    LICENSE_TAB: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.28,
        y_ratio=0.08,
        image_path="desktop_settings/license_tab.png",
        timeout=3
    ))
    
    # 啟動試用授權按鈕
    ACTIVATE_FREE_LICENSE_BTN: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.2,
        y_ratio=0.35,
        timeout=2
    ))
    
    # 確認按鈕（彈窗）
    CONFIRM_BTN: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.65,
        y_ratio=0.85,
        image_path="desktop_settings/ok_btn.png",
        timeout=2
    ))
    
    # 系統管理視窗確認按鈕
    SYSTEM_ADMIN_OK_BTN: UILocator = field(default_factory=lambda: UILocator(
        x_ratio=0.72,
        y_ratio=0.95,
        image_path="desktop_settings/ok_btn.png",
        timeout=2
    ))
    
    # Radio Button 'Y' 位置（錄影分頁簽中的啟用錄影選項）
    RADIO_Y_X_RATIO: float = 0.10  # 左上角偏左一點
    RADIO_Y_Y_RATIO: float = 0.15  # 分頁簽下方
    
    # ==================== Web Admin 定位器 (Case 2-2) ====================
    # 用於 https://localhost:7001 Web Admin 頁面
    
    # 「View / 瀏覽 / 查看」分頁 Tab（Nx Cloud 網頁）
    # 使用 href 包含 /view 來定位，不依賴語言
    WEB_BROWSE_TAB_XPATH: str = "//div[@class='menu-items']//a[contains(@href, '/view')]"
    WEB_BROWSE_TAB_FALLBACK_XPATH: str = "//a[contains(text(), '瀏覽') or contains(text(), 'Browse') or contains(text(), 'View') or contains(text(), '查看')]"
    
    # Server 選項卡（左側 Server 列表項目）
    # DOM: <div class="server-name"><span class="name Online">
    WEB_SERVER_XPATH: str = "//div[@class='server-name']/span[contains(@class, 'name')]"
    WEB_SERVER_FALLBACK_XPATH: str = "//div[contains(@class, 'server-name')]//span[contains(@class, 'name')]"
    WEB_SERVER_TEXT_XPATH: str = "//*[contains(text(), 'LAPTOP') or contains(text(), 'Server')]"
    
    # 語言選擇器（Nx Cloud 網頁）
    WEB_LANGUAGE_DROPDOWN_XPATH: str = "//button[contains(@class, 'language') or contains(@class, 'locale')]"
    WEB_LANGUAGE_CHINESE_XPATH: str = "//*[contains(text(), '繁體中文') or contains(text(), 'Traditional Chinese')]"
    
    # 攝影機項目
    # DOM: <div class="cameras ng-star-inserted"><div class="preview">
    WEB_CAMERA_XPATH: str = "//div[@class='cameras ng-star-inserted']/div[@class='preview']"
    WEB_CAMERA_FALLBACK_XPATH: str = "//div[contains(@class, 'cameras')]//div[contains(@class, 'preview')]"
    WEB_CAMERA_TEXT_XPATH: str = "//a[contains(text(), 'cam') or contains(text(), 'USB') or contains(text(), 'Camera')]"
    
    # 錄影進度條 (Timeline Canvas)
    WEB_TIMELINE_XPATH: str = "/html/body/nx-app/div[2]/div/nx-system-view-index-page/nx-system-view-camera-page/div[2]/div[2]/div[2]/nx-timeline/div/canvas"
    WEB_TIMELINE_FALLBACK_XPATH: str = "//nx-timeline//canvas"
    
    # Nx Cloud 登錄相關
    # 右上角「登入」按鈕：<a class="login nx-button--primary" href="/authorize">登入</a>
    WEB_NX_CLOUD_LOGIN_BTN_XPATH: str = "//a[@href='/authorize']"
    WEB_NX_CLOUD_LOGIN_BTN_FALLBACK_XPATH: str = "//a[contains(@class, 'login') and contains(@class, 'nx-button')]"
    WEB_ACCEPT_RISK_BTN_XPATH: str = "//button[contains(., '接受') or contains(., '风险')]"
    WEB_EMAIL_INPUT_XPATH: str = "//input[@type='email' or @type='text']"
    WEB_NEXT_BTN_XPATH: str = "//button[contains(., '下一') or contains(., 'Next')]"
    WEB_PASSWORD_INPUT_XPATH: str = "//input[@type='password']"
    WEB_LOGIN_SUBMIT_BTN_XPATH: str = "//button[contains(., '登录') or contains(., '登入') or @type='submit']"
    
    # 語言切換相關
    # 語言下拉按鈕：<button id="dropdownMenuButton">
    WEB_LANGUAGE_DROPDOWN_XPATHS: List[str] = field(default_factory=lambda: [
        "//button[@id='dropdownMenuButton']",
        "//button[contains(@class, 'btn-dropdown-toggle')]",
        "//button[contains(@class, 'legacy-btn') and contains(@class, 'dropdown')]",
        "//div[contains(@class, 'language')]//button",
        "//*[contains(@class, 'locale-selector')]",
    ])
    
    # 繁體中文選項：<ul aria-labelledby="dropdownMenuButton"><a><span>繁体中文</span></a></ul>
    WEB_CHINESE_OPTION_XPATHS: List[str] = field(default_factory=lambda: [
        "//ul[@aria-labelledby='dropdownMenuButton']//span[contains(text(), '繁体中文')]",
        "//ul[@aria-labelledby='dropdownMenuButton']//span[contains(text(), '繁體中文')]",
        "//ul[@aria-labelledby='dropdownMenuButton']//a[contains(@class, 'dropdown-item')]//span[contains(text(), '繁')]",
        "//a[contains(@class, 'dropdown-item')]//span[contains(text(), '繁体中文')]",
        "//a[contains(@class, 'dropdown-item')]//span[contains(text(), '繁體中文')]",
        "//*[contains(text(), '繁體中文')]",
        "//*[contains(text(), '繁体中文')]",
        "//*[contains(text(), 'Traditional Chinese')]",
    ])


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


# ==================== 登錄相關配置 ====================

@dataclass
class LoginConfig:
    """登錄流程相關配置"""
    # 伺服器卡片位置
    SERVER_TILE_X_RATIO: float = 0.25
    SERVER_TILE_Y_RATIO: float = 0.65
    SERVER_TILE_IMAGE: str = "desktop_login/server_tile.png"
    
    # 連接服務器按鈕位置
    CONNECT_BTN_X_RATIO: float = 0.75
    CONNECT_BTN_Y_RATIO: float = 0.65
    
    # 密碼輸入框位置
    PASSWORD_INPUT_X_RATIO: float = 0.5
    PASSWORD_INPUT_Y_RATIO: float = 0.55
    
    # 超時配置
    SERVER_CLICK_TIMEOUT: int = 5
    PASSWORD_INPUT_TIMEOUT: int = 2
    DIALOG_WAIT_TIME: float = 2.0
    DIALOG_CHECK_INTERVAL: float = 0.5
    DIALOG_CHECK_ROUNDS: int = 3
    LOGIN_PROCESS_WAIT: float = 1.0
    LOGIN_BUFFER_TIME: float = 1.5
    
    # 對話框標題列表
    CONNECT_DIALOG_TITLES: List[str] = field(default_factory=lambda: [
        "连接到服务器",
        "Connect to server",
        "连接到服务器...",
        "连接到服务器... - Nx Witness Client",
        "連線至伺服器",
        "連線至伺服器...",
        "連線至伺服器... - Nx Witness Client"
    ])
    
    # 登錄驗證配置
    LOGIN_INDICATOR_IMAGES: List[str] = field(default_factory=lambda: [
        "desktop_login/server_tile.png",
        "desktop_login/login_indicator.png"
    ])
    
    MAIN_PAGE_INDICATOR: str = "desktop_main/server_icon.png"
    MAIN_PAGE_VERIFY_TIMEOUT: int = 3
    
    # 智能登錄檢查配置
    STARTUP_MAX_WAIT: int = 10
    STARTUP_WAIT_INTERVAL: float = 0.5


# 將登錄配置添加到 ExtendedConfig
class ExtendedConfig(DevConfig):
    """擴展配置類，包含所有新增的配置"""
    THRESHOLDS = _thresholds
    APP_PATHS = _app_paths
    CAMERA_SETTINGS = _camera_settings
    TIMELINE_SETTINGS = _timeline_settings
    CALENDAR_SETTINGS = _calendar_settings
    LOCATOR_CONFIG = _locator_config
    LOGIN_CONFIG = LoginConfig()
    
    @classmethod
    def validate(cls) -> None:
        """驗證配置的完整性。
        
        檢查必要的配置項目是否正確設置，若有問題則打印警告或錯誤。
        """
        # 檢查 Gemini API Key（警告但不中斷）
        if not cls.GEMINI_API_KEY:
            print("⚠️ 警告: GEMINI_API_KEY 未設置")
            print("   UnifiedVLM 將僅使用 Ollama，無法使用 Gemini 備援功能")
            print("   若需啟用 Gemini 備援，請設置環境變數: GEMINI_API_KEY")
        else:
            print(f"✅ Gemini API Key 已設置: {cls.GEMINI_API_KEY[:10]}...")
        
        # 檢查 NX 執行檔路徑
        if not os.path.exists(cls.NX_EXE_PATH):
            print(f"⚠️ 警告: NX 執行檔不存在: {cls.NX_EXE_PATH}")
        
        # 檢查資源路徑
        if not os.path.exists(cls.RES_PATH):
            print(f"⚠️ 警告: 資源路徑不存在: {cls.RES_PATH}")

# 更新全局配置實例
EnvConfig = ExtendedConfig()

