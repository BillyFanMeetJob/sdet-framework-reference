# 相對路徑: config.py
import os
import sys

def get_project_root():
    """
    取得專案根目錄
    
    支援兩種模式：
    1. 正常運行：使用當前檔案（config.py）所在目錄
    2. 打包成 EXE：使用 EXE 檔案所在目錄
    
    注意：EXE 執行時，會從 EXE 所在目錄查找 DemoData\TestPlan.xlsx
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
    
    # VLM (視覺語言模型) 設定
    VLM_ENABLED = True  # 是否啟用 VLM 辨識
    VLM_BACKEND = "ollama"  # 後端: 'ollama' (本地), 'openai', 'anthropic'
    VLM_MODEL = "llava"  # 模型名稱: 'llava', 'bakllava', 'gpt-4o', 'claude-3-5-sonnet-20241022'
    VLM_PRIORITY = 2  # VLM 在辨識優先級中的位置 (1=最高, 2=OK Script後, 3=OCR後)

def get_current_config():
    return DevConfig()

EnvConfig = get_current_config()