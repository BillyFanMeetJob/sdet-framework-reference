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

class StepTranslator:
    def __init__(self, browser_context):
        # 透過 config 拿 TestPlan 路徑
        from config import EnvConfig
        import pandas as pd
        self.translate_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="Translate")
        
        # 🎯 註冊 nx_poc 實例，傳入瀏覽器實體
        # 未來可擴展：
        # "login": LoginActions(browser_context),
        # "settings": SettingsActions(browser_context),
        self.action_map = {
            "nx_poc": NxPocActions(browser_context)
        }

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
        if row.empty: return
        
        # 從 Excel 取得 ActionKey（如 "login"）和 ActionMethod（如 "run_server_login_step"）
        target_obj = self.action_map.get(row.iloc[0]['ActionKey'])
        method_name = row.iloc[0]['ActionMethod']
        method = getattr(target_obj, method_name, None)
        if method:
            return method(**(injected_params or {}))