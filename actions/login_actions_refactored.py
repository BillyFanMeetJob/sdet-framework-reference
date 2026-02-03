# -*- coding: utf-8 -*-
"""
登錄相關動作模組（重構版）

此模組包含所有與登錄相關的測試動作，遵循以下原則：
1. 單一職責：只處理登錄相關邏輯
2. 參數統一：所有參數從 config.py 讀取
3. 類型提示：所有方法使用 Type Hints
4. 文檔完整：使用 Google-style Docstrings

Author: SDET Team
Date: 2026-01-26
"""

import time
from typing import Optional, List
import pygetwindow as gw

from base.base_action import BaseAction
from config import EnvConfig
from pages.desktop.desktop_login_page import DesktopLoginPage
from pages.desktop.main_page import MainPage


class LoginActions(BaseAction):
    """登錄動作類，處理所有登錄相關的測試流程。
    
    此類負責：
    - 伺服器登錄流程
    - 登錄狀態檢查
    - 登錄驗證
    
    Attributes:
        login_page (DesktopLoginPage): 登錄頁面操作對象
        main_page (MainPage): 主頁面操作對象
        login_config: 登錄相關配置
    """
    
    def __init__(self, browser_context=None):
        """初始化登錄動作類。
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__(browser=browser_context)
        
        # 使用統一配置
        self.login_config = EnvConfig.LOGIN_CONFIG
        
        # 初始化頁面對象
        self.login_page = DesktopLoginPage()
        self.main_page = MainPage()
    
    def run_server_login_step(self, **kwargs) -> 'LoginActions':
        """執行伺服器登錄流程。
        
        登錄流程：
        1. 啟動應用程式
        2. 優先點擊伺服器卡片
        3. 如失敗，點擊「連接服務器」並輸入密碼
        4. 驗證登錄成功
        
        Args:
            **kwargs: 可選參數
                server_name (str): 伺服器名稱，默認從 config 讀取
                password (str): 登錄密碼，默認從 config 讀取
                
        Returns:
            LoginActions: 返回自身，支持鏈式調用
            
        Raises:
            AssertionError: 登錄失敗時拋出
            
        Example:
            >>> actions = LoginActions()
            >>> actions.run_server_login_step(server_name="MyServer")
        """
        self.logger.info("[CASE_1-1] 執行 Case 1-1 登錄流程")
        
        # 從 kwargs 或 config 獲取參數
        server_name = kwargs.get("server_name", self.config.DEFAULT_SERVER_NAME)
        password = kwargs.get("password", self.config.ADMIN_PASSWORD)
        
        # 啟動應用程式
        self.login_page.launch_app(self.config.NX_EXE_PATH)
        
        # 嘗試點擊伺服器卡片
        success = self._try_click_server_tile(server_name)
        
        # 驗證是否誤點擊「連接服務器」
        if success:
            success = self._verify_not_connect_dialog()
        
        # 如失敗，嘗試「連接服務器」流程
        if not success:
            self._handle_connect_to_server(server_name, password)
            success = True
        
        # 驗證登錄成功
        if success:
            self._verify_login_success()
        else:
            raise AssertionError("登錄失敗：無法點擊伺服器卡片或連接服務器")
        
        return self
    
    def run_ensure_login_step(self, **kwargs) -> 'LoginActions':
        """智能登錄檢查：檢查是否已登錄，未登錄則執行登錄。
        
        此方法用於需要在已登錄狀態下執行的測試用例（如 Case 1-2）。
        會自動檢測當前狀態並決定是否需要執行登錄流程。
        
        Args:
            **kwargs: 傳遞給 run_server_login_step 的參數
            
        Returns:
            LoginActions: 返回自身，支持鏈式調用
            
        Example:
            >>> actions = LoginActions()
            >>> actions.run_ensure_login_step()
        """
        server_name = kwargs.get("server_name", self.config.DEFAULT_SERVER_NAME)
        self.logger.info(f"🔍 檢查登錄狀態（目標伺服器: {server_name}）")
        
        # 等待應用程式啟動
        if self._wait_for_app_startup():
            # 檢查是否已在主頁面
            if self._is_on_main_page():
                self.logger.info("✅ 已在主畫面，無需重新登錄")
                return self
        
        # 未登錄，執行登錄流程
        self.logger.info("⚠️ 未檢測到主畫面，執行登錄...")
        return self.run_server_login_step(**kwargs)
    
    # ==================== 私有輔助方法 ====================
    
    def _try_click_server_tile(self, server_name: str) -> bool:
        """嘗試點擊伺服器卡片。
        
        Args:
            server_name: 伺服器名稱
            
        Returns:
            bool: 點擊是否成功
        """
        self.logger.info(f"[LOGIN] 嘗試點擊伺服器卡片: {server_name}")
        
        cfg = self.login_config
        success = self.login_page.smart_click_priority_image(
            x_ratio=cfg.SERVER_TILE_X_RATIO,
            y_ratio=cfg.SERVER_TILE_Y_RATIO,
            target_text=server_name,
            image_path=cfg.SERVER_TILE_IMAGE,
            timeout=cfg.SERVER_CLICK_TIMEOUT
        )
        
        self.logger.info(f"[DEBUG] 點擊結果: {success}")
        return success
    
    def _verify_not_connect_dialog(self) -> bool:
        """驗證是否誤點擊了「連接服務器」。
        
        如果出現連接服務器對話框，說明點擊了錯誤的位置。
        
        Returns:
            bool: True 表示未誤點擊，False 表示誤點擊了
        """
        self.logger.info("[VERIFY] 驗證點擊結果...")
        time.sleep(self.login_config.DIALOG_WAIT_TIME)
        
        cfg = self.login_config
        for check_round in range(cfg.DIALOG_CHECK_ROUNDS):
            if self._is_connect_dialog_open():
                self.logger.warning(
                    f"[WARN] 檢測到連接服務器對話框（檢查輪次: {check_round+1}），"
                    "表示點擊了「連接服務器」而非伺服器卡片"
                )
                return False
            
            if check_round < cfg.DIALOG_CHECK_ROUNDS - 1:
                time.sleep(cfg.DIALOG_CHECK_INTERVAL)
        
        self.logger.info("[OK] 未檢測到連接服務器對話框，確認成功點擊了伺服器卡片")
        return True
    
    def _is_connect_dialog_open(self) -> bool:
        """檢查連接服務器對話框是否打開。
        
        Returns:
            bool: 對話框是否打開
        """
        for title in self.login_config.CONNECT_DIALOG_TITLES:
            try:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    return True
            except Exception as e:
                self.logger.debug(f"檢查對話框標題 '{title}' 時發生異常: {e}")
        return False
    
    def _handle_connect_to_server(self, server_name: str, password: str) -> None:
        """處理「連接服務器」流程。
        
        Args:
            server_name: 伺服器名稱
            password: 登錄密碼
            
        Raises:
            AssertionError: 連接失敗時拋出
        """
        self.logger.info("[WARN] 未找到伺服器卡片，嘗試點擊「連接服務器」...")
        
        # 點擊「連接服務器」按鈕
        cfg = self.login_config
        success = self.login_page.smart_click_priority_text(
            x_ratio=cfg.CONNECT_BTN_X_RATIO,
            y_ratio=cfg.CONNECT_BTN_Y_RATIO,
            target_text="連接服務器",
            timeout=cfg.SERVER_CLICK_TIMEOUT
        )
        
        if not success:
            raise AssertionError("無法點擊「連接服務器」按鈕")
        
        self.logger.info("[OK] 已點擊「連接服務器」，等待對話框出現...")
        time.sleep(cfg.DIALOG_WAIT_TIME)
        
        # 輸入密碼
        self._input_password(password)
        
        # 驗證登錄成功（對話框應該關閉）
        self._verify_dialog_closed()
    
    def _input_password(self, password: str) -> None:
        """輸入密碼。
        
        Args:
            password: 密碼字符串
        """
        self.logger.info("🖱️ 點擊密碼輸入框...")
        
        cfg = self.login_config
        password_clicked = self.login_page.smart_click(
            x_ratio=cfg.PASSWORD_INPUT_X_RATIO,
            y_ratio=cfg.PASSWORD_INPUT_Y_RATIO,
            target_text="密码",
            timeout=cfg.PASSWORD_INPUT_TIMEOUT
        )
        
        if not password_clicked:
            self.logger.warning("⚠️ 密碼框點擊失敗，嘗試直接輸入...")
        
        # 輸入密碼
        self.logger.info(f"⌨️ 輸入密碼（長度: {len(password)} 字元）...")
        self.login_page.type_text(password)
        time.sleep(0.5)
        
        # 按 Enter 確認
        self.logger.info("⌨️ 按 Enter 確認登錄...")
        self.login_page.press_key('enter')
        time.sleep(self.login_config.LOGIN_PROCESS_WAIT)
    
    def _verify_dialog_closed(self) -> None:
        """驗證連接服務器對話框已關閉。
        
        Raises:
            AssertionError: 對話框仍然打開時拋出
        """
        self.logger.info("⏳ 等待登錄處理...")
        
        max_check = 4
        for i in range(max_check):
            time.sleep(1)
            if self._is_connect_dialog_open():
                self.logger.warning(
                    f"⚠️ 連接服務器對話框仍存在（嘗試 {i+1}/{max_check}）"
                )
                if i == max_check - 1:
                    raise AssertionError(
                        "登錄失敗：連接服務器對話框仍然存在，可能是密碼錯誤"
                    )
            else:
                break
        
        self.logger.info("✅ 連接服務器對話框已關閉")
        time.sleep(self.login_config.LOGIN_PROCESS_WAIT)
    
    def _verify_login_success(self) -> None:
        """驗證登錄成功。
        
        檢查項目：
        1. 主頁面視窗存在
        2. 不在登錄頁面
        3. 主頁面元素可見
        
        Raises:
            AssertionError: 登錄驗證失敗時拋出
        """
        self.logger.info("✅ 等待系統載入...")
        time.sleep(self.login_config.LOGIN_BUFFER_TIME)
        
        # 檢查主頁面視窗
        win = self.main_page.get_nx_window()
        if not win:
            raise AssertionError("登錄驗證失敗：未找到主畫面視窗")
        
        self.logger.info("✅ 找到主畫面視窗，繼續驗證...")
        
        # 檢查是否還在登錄頁面
        if self._is_on_login_page():
            if not self._is_on_main_page():
                raise AssertionError("登錄驗證失敗：仍在登錄畫面")
            else:
                self.logger.warning("⚠️ 檢測到登錄畫面元素，但主畫面元素也存在，可能是誤判")
        
        # 驗證主頁面元素
        try:
            cfg = self.login_config
            self.main_page.verify_element_exists(
                image_path=cfg.MAIN_PAGE_INDICATOR,
                window_titles=["Nx Witness Client"],
                timeout=cfg.MAIN_PAGE_VERIFY_TIMEOUT,
                raise_on_failure=False
            )
            self.logger.info("✅ 登錄驗證成功：找到主畫面圖示")
        except Exception as e:
            self.logger.warning(f"⚠️ 圖片驗證失敗: {e}")
        
        self.logger.info("✅ 登錄驗證成功：已進入主畫面")
    
    def _wait_for_app_startup(self) -> bool:
        """等待應用程式啟動。
        
        Returns:
            bool: 應用程式是否成功啟動
        """
        cfg = self.login_config
        max_wait = cfg.STARTUP_MAX_WAIT
        wait_interval = cfg.STARTUP_WAIT_INTERVAL
        waited = 0
        
        while waited < max_wait:
            main_windows = gw.getWindowsWithTitle("Nx Witness Client")
            
            if main_windows:
                for w in main_windows:
                    if w.visible:
                        try:
                            _ = w.left, w.top, w.width, w.height
                            if w.width > 0 and w.height > 0:
                                return True
                        except Exception:
                            continue
            
            if waited == 0:
                self.logger.info("⏳ 等待軟件啟動...")
            time.sleep(wait_interval)
            waited += wait_interval
        
        return False
    
    def _is_on_main_page(self) -> bool:
        """檢查是否在主頁面。
        
        Returns:
            bool: 是否在主頁面
        """
        try:
            cfg = self.login_config
            return self.main_page.verify_element_exists(
                image_path=cfg.MAIN_PAGE_INDICATOR,
                timeout=2,
                raise_on_failure=False
            )
        except Exception:
            return False
    
    def _is_on_login_page(self) -> bool:
        """檢查是否在登錄頁面。
        
        Returns:
            bool: 是否在登錄頁面
        """
        try:
            for indicator in self.login_config.LOGIN_INDICATOR_IMAGES:
                if self.login_page.verify_element_exists(
                    image_path=indicator,
                    timeout=1,
                    raise_on_failure=False
                ):
                    return True
            return False
        except Exception:
            return False
