# -*- coding: utf-8 -*-
"""
授權相關動作模組

負責處理授權相關的操作，包括啟用免費授權等。

Author: SDET Team
Date: 2026-01-26
"""

from base.base_action import BaseAction
from typing import Optional


class LicenseActions(BaseAction):
    """授權動作類
    
    負責處理所有與授權相關的操作。
    
    Attributes:
        license_settings_page: 授權設置頁面實例
    """
    
    def __init__(self, browser_context: Optional[object] = None):
        """初始化授權動作類
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__(browser=browser_context)
        
        from pages.desktop.license_settings_page import LicenseSettingsPage
        
        self.license_settings_page = LicenseSettingsPage()
    
    def run_activate_free_license_step(self, **kwargs) -> 'LicenseActions':
        """執行啟用免費授權流程
        
        流程：
        1. 在左側 Server 上右鍵 -> 站點管理 (系統管理)
        2. 進入「站點管理」視窗（預設在「一般」頁籤）
        3. 切換到「授權」頁籤
        4. 嘗試點擊「啟用免費授權」按鈕（如果存在）
        5. 如果找到按鈕，確認授權成功彈窗
        6. 關閉站點管理視窗
        
        注意：如果授權已經啟用過，啟用按鈕將不存在，直接關閉視窗。
        
        Args:
            **kwargs: 可選參數
                use_menu (bool|str): 是否通過主選單進入，預設 False
                    可以是布爾值或字符串 'True'/'False'
        
        Returns:
            LicenseActions: 返回自身，支持鏈式調用
            
        Example:
            >>> license = LicenseActions()
            >>> license.run_activate_free_license_step(use_menu=False)
        """
        self.logger.info("🎬 執行 Case 1-3: 啟用免費錄製授權")
        
        # 處理 use_menu 參數（可能是字符串 'False' 或布爾值 False）
        use_menu_raw = kwargs.get("use_menu", False)
        if isinstance(use_menu_raw, str):
            use_menu = use_menu_raw.lower() == 'true'
        else:
            use_menu = bool(use_menu_raw)
        
        # 步驟 1: 開啟站點管理視窗
        if not self.license_settings_page.open_system_administration(via_menu=use_menu):
            self.logger.error("[ERROR] 開啟站點管理視窗失敗")
            return self
        
        # 步驟 2: 切換到授權分頁
        if not self.license_settings_page.switch_to_license_tab():
            self.logger.error("[ERROR] 切換到授權分頁失敗")
            self.license_settings_page.close_system_administration()
            return self
        
        # 步驟 3: 嘗試點擊啟用免費授權按鈕
        if self.license_settings_page.click_activate_free_license():
            self.logger.info("✅ 正在啟用免費授權...")
            
            # 步驟 4: 確認授權啟動成功彈窗
            if self.license_settings_page.confirm_license_activation():
                self.logger.info("✅ 授權啟動成功")
            else:
                self.logger.warning("⚠️ 未檢測到授權確認彈窗")
        else:
            self.logger.info("ℹ️ 授權已存在或按鈕不可用，直接關閉視窗")
        
        # 步驟 5: 關閉站點管理視窗
        if self.license_settings_page.close_system_administration():
            self.logger.info("✅ Case 1-3 完成")
        else:
            self.logger.warning("⚠️ 站點管理視窗可能未正確關閉")
        
        return self
