"""
錄影相關操作模組 - RecordingActions

此模組包含錄影事件回放相關的操作，主要用於 Case 2-2。
"""
import os
import time
from base.base_action import BaseAction
from toolkit.logger import get_logger


class RecordingActions(BaseAction):
    """錄影相關操作類"""
    
    def __init__(self, browser_context=None):
        """
        初始化 RecordingActions
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__()
        self.browser_context = browser_context
        self.logger = get_logger(self.__class__.__name__)
        
        # 導入配置
        from config import EnvConfig
        self.config = EnvConfig
    
    def run_playback_recording_step(self, **kwargs) -> 'RecordingActions':
        """執行 Case 1-5: 桌面版回放錄影事件後停止
        
        此方法委託給 NxPocActions 執行，使用桌面版 Nx Witness Client。
        
        流程：
        1. 選擇攝影機
        2. 點擊日曆圖標
        3. 選擇有錄影的日期
        4. 播放指定時間後暫停
        
        Args:
            **kwargs: 可選參數
                camera_name (str): 攝影機名稱，預設 "usb_cam"
                playback_duration (int|float): 播放持續時間（秒），預設 7 秒
        
        Returns:
            RecordingActions: 返回自身，支持鏈式調用
        """
        self.logger.info("[RECORDING] 執行 Case 1-5: 回放錄影事件後停止（桌面版）")
        self.logger.info("[RECORDING] 委託 NxPocActions 執行...")
        
        from actions.nx_poc_actions import NxPocActions
        
        poc_actions = NxPocActions(self.browser_context)
        poc_actions.run_playback_recording_step(**kwargs)
        
        return self
    
    def run_review_recording_playback_step(self, **kwargs) -> 'RecordingActions':
        """執行 Case 2-2: Web 版調閱錄影事件回放
        
        此方法委託給 CloudActions 執行，使用 Selenium + Nx Cloud OAuth 登錄。
        
        流程：
        1. 啟動 Chrome（帶 debugging port）
        2. 通過 Nx Cloud OAuth 登錄 Web Admin
        3. 點擊「瀏覽」分頁
        4. 點擊 Server 選項卡
        5. 點擊攝影機項目
        
        Args:
            **kwargs: 可選參數
                skip_login (bool): 是否跳過登錄步驟，預設 False
        
        Returns:
            RecordingActions: 返回自身，支持鏈式調用
        """
        self.logger.info("[RECORDING] 執行 Case 2-2: 調閱錄影事件回放（Web 版）")
        self.logger.info("[RECORDING] 委託 CloudActions 執行...")
        
        from actions.cloud_actions import CloudActions
        
        cloud_actions = CloudActions(self.browser_context)
        cloud_actions.run_playback_recording_step(**kwargs)
        
        return self
    
    def run_enable_recording_step(self, **kwargs) -> 'RecordingActions':
        """執行開啟錄影功能流程（Case 1-4）
        
        此方法委託給 NxPocActions 執行，保持代碼一致性。
        
        流程：
        1. 找到要開啟錄製功能的攝影機，右鍵點選「攝影機設定」
        2. 進入「攝影機設定」視窗，點選「錄製」頁籤
        3. 開啟左上角「錄製」開關，點選 OK，就會開始錄影
        
        Args:
            **kwargs: 可選參數
                camera_name (str): 攝影機名稱，預設 "usb_cam"
        
        Returns:
            RecordingActions: 返回自身，支持鏈式調用
        """
        self.logger.info("[RECORDING] 執行 Case 1-4: 開啟錄影功能")
        self.logger.info("[RECORDING] 委託 NxPocActions 執行...")
        
        from actions.nx_poc_actions import NxPocActions
        
        poc_actions = NxPocActions(self.browser_context)
        poc_actions.run_enable_recording_step(**kwargs)
        
        return self
