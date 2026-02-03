# -*- coding: utf-8 -*-
"""
Session 轉移工具

實現從 Nx App 開啟的 Chrome 接管 session，用 Playwright 控制。

策略：
1. 關閉 Nx App 開啟的 Chrome（釋放 user-data-dir）
2. 用 Playwright 啟動新的 Chrome，使用相同的系統 user-data-dir
3. Session/Cookies 會被繼承，不會顯示 "Site is offline"
4. 支援完整的 DOM 控制

Author: SDET Team
Date: 2026-02-01
"""

import os
import time
import logging
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright


class SessionTransfer:
    """
    Session 轉移工具
    
    用於從 Nx App 開啟的 Chrome 接管 session，
    然後用 Playwright 進行完整的 DOM 控制。
    """
    
    # 系統 Chrome 的 user-data-dir
    SYSTEM_CHROME_PROFILE = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def get_current_chrome_url(self) -> Optional[str]:
        """
        獲取當前 Chrome 視窗的 URL（用於後續導航）
        
        Returns:
            當前 URL，失敗返回 None
        """
        try:
            import pygetwindow as gw
            
            # 找到 Chrome 視窗
            chrome_windows = [w for w in gw.getAllWindows() 
                           if 'chrome' in w.title.lower() and w.visible]
            
            if not chrome_windows:
                self.logger.warning("[SESSION] 未找到 Chrome 視窗")
                return None
            
            # 從視窗標題嘗試獲取資訊
            title = chrome_windows[0].title
            self.logger.info(f"[SESSION] Chrome 視窗標題: {title}")
            
            # 對於 Nx Cloud，URL 通常是固定的
            # 可以從 config 讀取
            try:
                from config import EnvConfig
                return EnvConfig.BASE_URL
            except:
                return None
                
        except Exception as e:
            self.logger.error(f"[SESSION] 獲取 URL 失敗: {e}")
            return None
    
    def close_existing_chrome(self) -> bool:
        """
        關閉所有 Chrome 進程（釋放 user-data-dir）
        
        Returns:
            是否成功
        """
        self.logger.info("[SESSION] 關閉現有 Chrome 進程...")
        
        try:
            import subprocess
            # 使用 taskkill 強制關閉所有 Chrome
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                capture_output=True,
                text=True
            )
            
            # 等待進程完全關閉
            time.sleep(2)
            
            # 確認已關閉
            import psutil
            chrome_procs = [p for p in psutil.process_iter(['name']) 
                          if p.info['name'] == 'chrome.exe']
            
            if chrome_procs:
                self.logger.warning(f"[SESSION] 仍有 {len(chrome_procs)} 個 Chrome 進程")
                return False
            
            self.logger.info("[SESSION] ✅ Chrome 已關閉")
            return True
            
        except Exception as e:
            self.logger.error(f"[SESSION] 關閉 Chrome 失敗: {e}")
            return False
    
    def launch_with_session(self, url: Optional[str] = None) -> Optional[Page]:
        """
        啟動帶有原始 session 的 Chrome
        
        使用系統預設的 user-data-dir，繼承 Nx App 的 session/cookies。
        
        Args:
            url: 要導航的 URL（如果為 None，使用 config 中的 BASE_URL）
            
        Returns:
            Playwright Page 對象，失敗返回 None
        """
        if url is None:
            try:
                from config import EnvConfig
                url = EnvConfig.BASE_URL
            except:
                url = "about:blank"
        
        self.logger.info(f"[SESSION] 啟動 Chrome（使用系統 Profile）")
        self.logger.info(f"[SESSION] User Data Dir: {self.SYSTEM_CHROME_PROFILE}")
        self.logger.info(f"[SESSION] 目標 URL: {url}")
        
        try:
            # 啟動 Playwright
            self.playwright = sync_playwright().start()
            
            # 使用 launch_persistent_context 啟動 Chrome
            # 使用系統的 user-data-dir，繼承 session
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.SYSTEM_CHROME_PROFILE,
                headless=False,
                channel="chrome",  # 使用系統 Chrome
                args=[
                    '--remote-debugging-port=9222',
                    '--no-first-run',
                    '--no-default-browser-check',
                ],
                ignore_https_errors=True,
            )
            
            # 獲取或創建頁面
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = self.context.new_page()
            
            # 導航到 URL
            self.logger.info(f"[SESSION] 導航到: {url}")
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待頁面載入
            time.sleep(2)
            
            # 最大化視窗
            self._maximize_window()
            
            self.logger.info(f"[SESSION] ✅ Chrome 已啟動，當前 URL: {self.page.url}")
            self.logger.info("[SESSION] ✅ Session 已繼承，可以進行 DOM 控制")
            
            return self.page
            
        except Exception as e:
            self.logger.error(f"[SESSION] 啟動失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _maximize_window(self):
        """最大化瀏覽器視窗"""
        try:
            import pygetwindow as gw
            time.sleep(1)
            chrome_windows = [w for w in gw.getAllWindows() 
                           if 'chrome' in w.title.lower()]
            if chrome_windows:
                chrome_windows[0].maximize()
                self.logger.info("[SESSION] ✅ 視窗已最大化")
        except Exception as e:
            self.logger.warning(f"[SESSION] 最大化失敗: {e}")
    
    def takeover_nx_chrome(self, url: Optional[str] = None) -> Optional[Page]:
        """
        一鍵接管 Nx App 開啟的 Chrome
        
        完整流程：
        1. 獲取當前 URL
        2. 關閉 Nx App 的 Chrome
        3. 用 Playwright 啟動新的 Chrome（繼承 session）
        4. 導航到相同的 URL
        
        Args:
            url: 目標 URL（如果為 None，使用 config 中的 BASE_URL）
            
        Returns:
            Playwright Page 對象，失敗返回 None
        """
        self.logger.info("[SESSION] === 開始接管 Nx App 的 Chrome ===")
        
        # 1. 關閉現有 Chrome
        if not self.close_existing_chrome():
            self.logger.error("[SESSION] ❌ 無法關閉現有 Chrome")
            return None
        
        # 2. 啟動帶有 session 的新 Chrome
        page = self.launch_with_session(url)
        if not page:
            self.logger.error("[SESSION] ❌ 無法啟動新 Chrome")
            return None
        
        self.logger.info("[SESSION] === ✅ 接管成功 ===")
        return page
    
    def get_page(self) -> Optional[Page]:
        """獲取當前 Page 對象"""
        return self.page
    
    def close(self):
        """關閉 Playwright（瀏覽器會保持運行）"""
        self.logger.info("[SESSION] 釋放 Playwright 控制...")
        
        # 不調用 context.close()，讓瀏覽器保持運行
        self.page = None
        self.context = None
        
        if self.playwright:
            # 也不調用 playwright.stop()
            self.playwright = None
        
        self.logger.info("[SESSION] ✅ 已釋放控制，瀏覽器保持運行")


# ============================================================================
# 使用範例
# ============================================================================

def example_case_2_2():
    """
    Case 2-2 範例：接管 Nx App 開啟的 Chrome，進行 DOM 控制
    """
    logging.basicConfig(level=logging.INFO)
    
    transfer = SessionTransfer()
    
    # 一鍵接管 Nx App 的 Chrome
    page = transfer.takeover_nx_chrome("http://localhost:7001")
    
    if page:
        print(f"✅ 成功接管 Chrome，當前 URL: {page.url}")
        
        # 現在可以用 Playwright 進行 DOM 控制
        # ============================================
        
        # 點擊元素
        # page.click("button#submit")
        
        # 輸入文字
        # page.fill("input#email", "user@example.com")
        
        # 獲取元素文字
        # text = page.text_content(".title")
        
        # 等待元素
        # page.wait_for_selector(".loading", state="hidden")
        
        # XPath 選擇器
        # page.click("//div[@class='menu']//a[text()='查看']")
        
        # 截圖
        # page.screenshot(path="screenshot.png")
        
        # ============================================
        
        print("按 Enter 結束...")
        input()
        
        transfer.close()
    else:
        print("❌ 接管失敗")


if __name__ == "__main__":
    example_case_2_2()
