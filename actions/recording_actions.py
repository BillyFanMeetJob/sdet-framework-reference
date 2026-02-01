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
        """執行調閱錄影事件回放流程（Case 2-2）
        
        此方法委託給 CloudActions 執行，使用 Selenium + Nx Cloud OAuth 登錄。
        
        流程：
        1. 啟動 Chrome（帶 debugging port）
        2. 通過 Nx Cloud OAuth 登錄 Web Admin
        3. 點擊「瀏覽」分頁
        4. 點擊 Server 選項卡
        5. 點擊攝影機項目
        6. 點擊錄影進度條
        7. 等待影片播放
        
        Args:
            **kwargs: 可選參數
                playback_duration (int|float): 播放持續時間（秒），預設 7 秒
                skip_login (bool): 是否跳過登錄步驟，預設 False
        
        Returns:
            RecordingActions: 返回自身，支持鏈式調用
        """
        self.logger.info("[RECORDING] 執行 Case 2-2: 調閱錄影事件回放")
        self.logger.info("[RECORDING] 委託 CloudActions 執行...")
        
        from actions.cloud_actions import CloudActions
        
        cloud_actions = CloudActions(self.browser_context)
        cloud_actions.run_playback_recording_step(**kwargs)
        
        return self
    
    def run_review_recording_playback_step(self, **kwargs) -> 'RecordingActions':
        """執行調閱錄影事件回放流程（Case 2-2）- 別名方法
        
        此方法是 run_playback_recording_step 的別名，保持向後兼容。
        
        Args:
            **kwargs: 可選參數
                playback_duration (int|float): 播放持續時間（秒），預設 7 秒
        
        Returns:
            RecordingActions: 返回自身，支持鏈式調用
        """
        return self.run_playback_recording_step(**kwargs)
