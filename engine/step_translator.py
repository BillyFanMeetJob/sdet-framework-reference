# 相對路徑: engine/step_translator.py
# 
# 🎯 StepTranslator 的核心職責：
# 1. 從 Excel 的 "Translate" sheet 讀取 FlowName → ActionKey + ActionMethod 的映射表
# 2. 根據 ActionKey 找到對應的 Action 實例（如 LoginActions, SettingsActions 等）
# 3. 動態呼叫該實例的指定方法，並傳入參數
#
# 📊 Excel 結構範例（Translate sheet）：
# | FlowName          | ActionKey | ActionMethod              |
# |-------------------|-----------|---------------------------|
# | 強制登錄          | login     | run_server_login_step     |
# | 智能檢查登錄      | login     | run_ensure_login_step     |
# | 切換語系          | settings  | run_change_language_step  |
#
# 🔗 整合方式：
# - TestRunner 呼叫 StepTranslator.execute(flow_name, params)
# - StepTranslator 查表找到對應的 Action 類別和方法
# - 動態執行該方法，返回結果給 TestRunner
# - 所有 Action 類別繼承自 BaseAction，確保統一的日誌和配置管理
#
# 🧩 擴展性：
# - 新增功能只需：1) 在 actions/ 下新增 Action 類別  2) 在 action_map 註冊  3) 在 Excel 新增映射
# - 無需修改 TestRunner 或其他核心邏輯

from actions.nx_poc_actions import NxPocActions
from actions.nx_mobile_actions import NxMobileActions
from actions.login_actions_refactored import LoginActions
from actions.settings_actions import SettingsActions
from actions.camera_actions import CameraActions
from actions.license_actions import LicenseActions
from actions.recording_actions import RecordingActions
from actions.cloud_actions import CloudActions

class StepTranslator:
    def __init__(self, browser_context=None, mobile_driver=None):
        """
        初始化 StepTranslator
        
        Args:
            browser_context: Web 瀏覽器上下文（用於桌面/網頁端測試）
            mobile_driver: Appium WebDriver 實例（用於移動端測試）
        """
        # 透過 config 拿 TestPlan 路徑
        from config import EnvConfig
        import pandas as pd
        self.translate_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="Translate")
        
        # 🎯 註冊 Action 實例
        # 新的模組化結構：
        # - login: 登錄相關操作
        # - settings: 設置相關操作
        # - camera: 攝影機相關操作
        # - license: 授權相關操作
        # - recording: 錄影相關操作
        # - cloud: Nx Cloud 相關操作
        # - nx_mobile: 移動端操作
        # - nx_poc: 舊版本（向後兼容）
        self.action_map = {}
        
        # 註冊桌面/網頁端 Action（新模組化結構）
        if browser_context is not None:
            self.action_map["login"] = LoginActions(browser_context)
            self.action_map["settings"] = SettingsActions(browser_context)
            self.action_map["camera"] = CameraActions(browser_context)
            self.action_map["license"] = LicenseActions(browser_context)
            self.action_map["recording"] = RecordingActions(browser_context)
            self.action_map["cloud"] = CloudActions(browser_context)
            # 保留舊版本以向後兼容
            self.action_map["nx_poc"] = NxPocActions(browser_context)
        else:
            # 🎯 即使沒有 browser_context，也註冊可以獨立運行的 Action
            # Case 2-2 (playback_recording) 會自己啟動 Chrome，不需要外部 browser_context
            self.action_map["recording"] = RecordingActions(None)
            self.action_map["cloud"] = CloudActions(None)
        
        # 註冊移動端 Action（即使 driver 為 None 也創建，使用 ADB 方式）
        # NxMobileActions.run_login_step 現在使用 ADB 方式，不需要 Appium driver
        self.action_map["nx_mobile"] = NxMobileActions(mobile_driver)

    def execute(self, flow_name, injected_params=None):
        """
        根據 FlowName 執行對應的 Action 方法
        
        Args:
            flow_name: Excel 中定義的流程名稱（如 "強制登錄"）
            injected_params: 從 TestRunner 傳入的動態參數（如 {"language": "繁體中文"}）
        
        Returns:
            Action 方法的返回值（通常是 self，支援鏈式呼叫）
        """
        row = self.translate_df[self.translate_df['FlowName'] == flow_name]
        if row.empty:
            raise ValueError(f"[StepTranslator] FlowName '{flow_name}' 在 Translate 表中找不到")
        
        # 從 Excel 取得 ActionKey（如 "login"）和 ActionMethod（如 "run_server_login_step"）
        action_key = row.iloc[0]['ActionKey']
        method_name = row.iloc[0]['ActionMethod']
        
        target_obj = self.action_map.get(action_key)
        if target_obj is None:
            raise ValueError(f"[StepTranslator] ActionKey '{action_key}' 未在 action_map 中註冊")
        
        method = getattr(target_obj, method_name, None)
        if method is None:
            raise ValueError(f"[StepTranslator] 方法 '{method_name}' 在 {type(target_obj).__name__} 中不存在")
        
        return method(**(injected_params or {}))