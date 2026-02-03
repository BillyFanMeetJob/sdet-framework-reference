# -*- coding: utf-8 -*-
"""
設置相關動作模組

負責處理系統設置相關的操作，包括語言切換、外觀設置等。

Author: SDET Team
Date: 2026-01-26
"""

from base.base_action import BaseAction
import time
from typing import Optional


class SettingsActions(BaseAction):
    """設置動作類
    
    負責處理所有與系統設置相關的操作。
    
    Attributes:
        main_page: 主頁面實例
        settings_page: 設置頁面實例
    """
    
    def __init__(self, browser_context: Optional[object] = None):
        """初始化設置動作類
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__(browser=browser_context)
        
        from pages.desktop.main_page import MainPage
        from pages.desktop.settings_page import SettingsPage
        
        self.main_page = MainPage()
        self.settings_page = SettingsPage()
    
    def run_change_language_step(self, **kwargs) -> 'SettingsActions':
        """執行語言切換流程
        
        從主選單進入本地設置，切換到外觀分頁，修改語言設置。
        
        Args:
            **kwargs: 可選參數
                language (str): 目標語言，預設為"繁體中文"
                    可選值: "繁體中文", "简体中文", "English"
        
        Returns:
            SettingsActions: 返回自身，支持鏈式調用
            
        Raises:
            AssertionError: 當任何步驟失敗時拋出
            
        Example:
            >>> settings = SettingsActions()
            >>> settings.run_change_language_step(language="繁體中文")
        """
        lang = kwargs.get("language", "繁體中文")
        self.logger.info(f"⚙️ 修改語系為: {lang}")
        
        # 步驟 1: 開啟主選單
        if not self.main_page.open_main_menu():
            error_msg = "開啟主選單失敗：無法點擊左上角菜單圖標"
            self.logger.error(f"[ERROR] {error_msg}")
            raise AssertionError(error_msg)
        
        # 步驟 2: 點擊本地設置
        self.logger.info("[DEBUG] 準備點擊本地設置...")
        local_settings_result = self.main_page.select_local_settings()
        self.logger.info(f"[DEBUG] select_local_settings 返回: {local_settings_result}")
        
        if not local_settings_result:
            error_msg = "點擊本地設置失敗：無法找到或點擊本地設置選項"
            self.logger.error(f"[ERROR] {error_msg}")
            raise AssertionError(error_msg)
        
        # 給設置視窗足夠時間完全載入
        self.logger.info("[DEBUG] 本地設置點擊成功，等待視窗載入...")
        time.sleep(1)
        
        # 步驟 3: 切換到外觀分頁
        self.logger.info("[DEBUG] 準備切換到外觀分頁...")
        self.settings_page.switch_to_appearance_tab()
        
        # 步驟 4: 修改語言
        self.settings_page.change_language(language=lang)
        
        self.logger.info(f"✅ 語系切換流程完成")
        return self
