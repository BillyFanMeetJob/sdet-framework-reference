# -*- coding: utf-8 -*-
"""
攝影機相關動作模組

負責處理攝影機相關的操作，包括 USB 攝影機啟用、攝影機設置等。

Author: SDET Team
Date: 2026-01-26
"""

from base.base_action import BaseAction
import time
from typing import Optional


class CameraActions(BaseAction):
    """攝影機動作類
    
    負責處理所有與攝影機相關的操作。
    
    Attributes:
        server_settings_page: 伺服器設置頁面實例
    """
    
    def __init__(self, browser_context: Optional[object] = None):
        """初始化攝影機動作類
        
        Args:
            browser_context: 瀏覽器上下文（可選）
        """
        super().__init__(browser=browser_context)
        
        from pages.desktop.server_settings_page import ServerSettingsPage
        
        self.server_settings_page = ServerSettingsPage()
    
    def run_enable_usb_webcam_step(self, **kwargs) -> 'CameraActions':
        """執行啟用 USB 攝影機流程
        
        流程：
        1. 在左上 Server 點右鍵 -> 伺服器設定
        2. 勾選自動偵測 USB 攝影機 -> 套用
        3. 左鍵點擊 Server 圖示 -> 展開攝影機列表
        4. 雙擊 USB 攝影機
        
        Args:
            **kwargs: 可選參數
                camera_name (str): 攝影機名稱，預設為"usb_cam"
        
        Returns:
            CameraActions: 返回自身，支持鏈式調用
            
        Raises:
            AssertionError: 當關鍵步驟失敗時拋出
            
        Example:
            >>> camera = CameraActions()
            >>> camera.run_enable_usb_webcam_step(camera_name="usb_cam")
        """
        self.logger.info("🎬 執行 Case 1-2: 啟用 USB 攝影機自動偵測")
        
        # 獲取 TestReporter（如果存在）
        from base.desktop_app import DesktopApp
        reporter = DesktopApp.get_reporter()
        step_no = 1
        
        # 步驟 1: 右鍵點擊 Server 圖示
        if not self._right_click_server_icon(reporter, step_no):
            raise AssertionError("❌ 右鍵點擊 Server 圖示失敗")
        step_no += 1
        
        # 步驟 2: 點擊伺服器設定選單
        if not self._click_server_settings_menu(reporter, step_no):
            raise AssertionError("❌ 點擊伺服器設定選單失敗")
        step_no += 1
        
        # 步驟 3: 勾選 USB 攝影機選項
        if not self._enable_usb_detection(reporter, step_no):
            raise AssertionError("❌ 勾選 USB 選項失敗")
        step_no += 1
        
        # 步驟 4: 套用設置
        if not self._apply_settings(reporter, step_no):
            self.logger.warning("⚠️ 套用設定可能失敗")
        step_no += 1
        
        self.logger.info("✅ USB 攝影機自動偵測已啟用")
        
        # 步驟 5 & 6: 智能尋找並雙擊 USB 攝影機
        # 新邏輯：先找 usb_cam，找到就點擊，找不到才展開 Server
        camera_name = kwargs.get("camera_name", "usb_cam")
        camera_found, expanded_server = self._smart_find_and_click_camera(camera_name, reporter, step_no)
        
        if not camera_found:
            self.logger.warning(f"⚠️ 嘗試多次後仍未找到攝影機 {camera_name}（未使用保底坐標）")
        
        return self
    
    # ==================== 私有輔助方法 ====================
    
    def _right_click_server_icon(self, reporter, step_no: int) -> bool:
        """右鍵點擊 Server 圖示
        
        Args:
            reporter: 測試報告器
            step_no: 步驟編號
            
        Returns:
            bool: 是否成功
        """
        if not self.server_settings_page.right_click_server_icon():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="右鍵點擊 Server 圖示",
                    status="fail",
                    message="右鍵點擊 Server 圖示失敗",
                    verification_items=[self.server_settings_page.create_verification_item("Server 圖示")]
                )
            return False
        
        # 驗證選單出現
        time.sleep(0.8)
        menu_verified = self._verify_context_menu()
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="右鍵點擊 Server 圖示",
                status="pass" if menu_verified else "warning",
                message="成功右鍵點擊 Server 圖示" + ("，選單已驗證" if menu_verified else "，選單驗證未通過但繼續執行"),
                verification_items=[
                    self.server_settings_page.create_verification_item("Server 圖示"),
                    self.server_settings_page.create_verification_item("右鍵選單")
                ]
            )
        
        return True
    
    def _verify_context_menu(self) -> bool:
        """驗證右鍵選單是否出現
        
        Returns:
            bool: 選單是否出現
        """
        try:
            # 先嘗試圖片驗證
            try:
                self.server_settings_page.verify_element_exists(
                    image_path="desktop_settings/system_admin_menu.png",
                    timeout=2,
                    raise_on_failure=False,
                    error_message="圖片驗證失敗"
                )
                self.logger.info("✅ 選單驗證成功（圖片匹配）")
                return True
            except AssertionError:
                # 嘗試文字驗證
                self.logger.debug("圖片驗證失敗，嘗試文字驗證...")
                self.server_settings_page.verify_element_exists(
                    target_text="站點管理",
                    timeout=2,
                    raise_on_failure=True,
                    error_message="右鍵選單未出現"
                )
                self.logger.info("✅ 選單驗證成功（文字匹配）")
                return True
        except AssertionError:
            self.logger.warning("⚠️ 選單驗證失敗，但繼續執行")
            return False
    
    def _click_server_settings_menu(self, reporter, step_no: int) -> bool:
        """點擊伺服器設定選單
        
        Args:
            reporter: 測試報告器
            step_no: 步驟編號
            
        Returns:
            bool: 是否成功
        """
        if not self.server_settings_page.click_server_settings_menu():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊伺服器設定選單",
                    status="fail",
                    message="點擊伺服器設定選單失敗",
                    verification_items=[self.server_settings_page.create_verification_item("伺服器設定選單")]
                )
            return False
        
        # 驗證視窗開啟
        time.sleep(1)
        window_verified = self._verify_settings_window()
        
        if not window_verified:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊伺服器設定選單",
                    status="fail",
                    message="伺服器設定視窗未開啟",
                    verification_items=[self.server_settings_page.create_verification_item("伺服器設定視窗")]
                )
            return False
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="點擊伺服器設定選單",
                status="pass",
                message="成功點擊伺服器設定選單，視窗已開啟",
                verification_items=[self.server_settings_page.create_verification_item("伺服器設定視窗")]
            )
        
        return True
    
    def _verify_settings_window(self) -> bool:
        """驗證伺服器設定視窗是否開啟
        
        Returns:
            bool: 視窗是否開啟
        """
        try:
            self.server_settings_page.verify_element_exists(
                window_titles=["伺服器設定", "Server Settings"],
                timeout=3,
                raise_on_failure=True,
                error_message="伺服器設定視窗未開啟"
            )
            return True
        except AssertionError as e:
            self.logger.error(f"❌ {str(e)}")
            return False
    
    def _enable_usb_detection(self, reporter, step_no: int) -> bool:
        """勾選 USB 攝影機選項
        
        Args:
            reporter: 測試報告器
            step_no: 步驟編號
            
        Returns:
            bool: 是否成功
        """
        success, was_already_checked = self.server_settings_page.enable_usb_detection()
        
        if not success:
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="勾選 USB 攝影機選項",
                    status="fail",
                    message="檢查或勾選 USB 選項失敗",
                    verification_items=[self.server_settings_page.create_verification_item("USB 攝影機 checkbox")]
                )
            return False
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="勾選 USB 攝影機選項",
                status="pass",
                message=f"USB 選項已勾選{'（原本已勾選）' if was_already_checked else '（新勾選）'}",
                verification_items=[self.server_settings_page.create_verification_item("USB 攝影機 checkbox")]
            )
        
        return True
    
    def _apply_settings(self, reporter, step_no: int) -> bool:
        """套用設置
        
        Args:
            reporter: 測試報告器
            step_no: 步驟編號
            
        Returns:
            bool: 是否成功
        """
        if not self.server_settings_page.apply_settings():
            if reporter:
                reporter.add_step(
                    step_no=step_no,
                    step_name="點擊套用/確定按鈕",
                    status="fail",
                    message="點擊套用/確定按鈕失敗",
                    verification_items=[self.server_settings_page.create_verification_item("套用/確定按鈕")]
                )
            return False
        
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="點擊套用/確定按鈕",
                status="pass",
                message="成功點擊套用/確定按鈕",
                verification_items=[self.server_settings_page.create_verification_item("套用/確定按鈕")]
            )
        
        return True
    
    def _smart_find_and_click_camera(self, camera_name: str, reporter, step_no: int) -> tuple:
        """智能尋找並雙擊 USB 攝影機
        
        新邏輯（解決 usb_cam 已顯示時仍雙擊 Server 的問題）：
        1. 先等待 2 秒讓系統偵測
        2. 嘗試找 usb_cam（只找不點）
           - 找到 → 雙擊（嚴格模式，不用保底坐標）
           - 沒找到 → 雙擊 Server 展開列表（只展開一次）
        3. 循環直到找到並成功點擊，或達到最大嘗試次數
        
        Args:
            camera_name: 攝影機名稱
            reporter: 測試報告器
            step_no: 步驟編號
            
        Returns:
            tuple: (camera_found: bool, expanded_server: bool)
        """
        self.logger.info("⏳ 等待設定生效並偵測 USB 攝影機...")
        
        max_attempts = 8
        camera_found = False
        expanded_server = False
        need_expand = True  # 是否需要展開 Server（只展開一次）
        
        for attempt in range(max_attempts):
            self.logger.info(f">>> [SMART_CAMERA] 第 {attempt + 1}/{max_attempts} 次嘗試尋找 USB 攝影機...")
            
            # 等待 2 秒，讓系統有時間偵測
            time.sleep(2)
            
            # 先嘗試找 usb_cam（只找不點）
            self.logger.debug(f">>> [SMART_CAMERA] 調用 find_usb_camera({camera_name})...")
            if self.server_settings_page.find_usb_camera(camera_name):
                self.logger.info(f">>> [SMART_CAMERA] ✅ 找到 USB 攝影機，準備雙擊（嚴格模式）...")
                
                # 找到了，使用嚴格模式雙擊（不用保底坐標）
                if self.server_settings_page.double_click_usb_camera_strict(camera_name):
                    camera_found = True
                    self.logger.info(f">>> [SMART_CAMERA] ✅ 成功雙擊 USB 攝影機")
                    break
                else:
                    # 找到但點擊失敗，繼續重試找
                    self.logger.warning(f">>> [SMART_CAMERA] ⚠️ 找到攝影機但雙擊失敗，繼續重試...")
                    need_expand = False  # 已經找到過，不需要再展開
                    continue
            
            # 沒找到 usb_cam
            self.logger.debug(f">>> [SMART_CAMERA] 未找到攝影機，need_expand={need_expand}")
            
            if need_expand:
                # 嘗試雙擊 Server 展開列表（只展開一次）
                self.logger.info(f">>> [SMART_CAMERA] ⚠️ 未找到攝影機，嘗試雙擊 Server 展開列表...")
                if self.server_settings_page.double_click_server_icon():
                    expanded_server = True
                    need_expand = False  # 已展開，下次不再展開
                    # 等待列表展開動畫
                    time.sleep(1.0)
                else:
                    self.logger.warning(f">>> [SMART_CAMERA] ⚠️ 雙擊 Server 圖示失敗")
            else:
                self.logger.debug(f">>> [SMART_CAMERA] ⚠️ 攝影機尚未出現或匹配失敗，繼續等待...")
        
        # 報告步驟 5: 展開列表
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="尋找 USB 攝影機",
                status="pass" if camera_found else ("warning" if expanded_server else "fail"),
                message=f"{'成功找到攝影機' if camera_found else '展開列表後尋找' if expanded_server else '攝影機可能已自動展開'}",
                verification_items=[self.server_settings_page.create_verification_item("Server 圖示")]
            )
        step_no += 1
        
        # 報告步驟 6: 雙擊 USB 攝影機
        if reporter:
            reporter.add_step(
                step_no=step_no,
                step_name="雙擊 USB 攝影機",
                status="pass" if camera_found else "fail",
                message=f"{'成功找到並雙擊 USB 攝影機（嚴格模式）' if camera_found else f'嘗試 {max_attempts} 次後仍未找到攝影機（未使用保底坐標）'}",
                verification_items=[self.server_settings_page.create_verification_item(f"USB 攝影機 ({camera_name})")]
            )
        
        if camera_found:
            self.logger.info(f">>> [SMART_CAMERA] ✅ Case 1-2 完成：已開啟攝影機 {camera_name}")
        
        return (camera_found, expanded_server)
