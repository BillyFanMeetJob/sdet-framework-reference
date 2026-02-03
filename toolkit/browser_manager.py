# 相對路徑: toolkit/browser_manager.py
"""
瀏覽器管理器 - 實現「優先接管，失敗才啟動」策略

設計原則：
1. DIP (依賴反轉原則): Page Object 只依賴抽象接口，不依賴具體實現
2. 優先接管現有瀏覽器，失敗才啟動新實例
3. 使用 disconnect() 而非 close()，確保瀏覽器保持運行

Author: Senior SDET
Date: 2026-01-31
"""

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright
from typing import Optional, Tuple
import os
import time
import logging
import traceback


class BrowserManager:
    """
    瀏覽器管理器 - 封裝瀏覽器啟動和連接邏輯
    
    核心策略：
    1. 優先嘗試連接到 http://127.0.0.1:9222 (Attach Mode)
    2. 如果連接失敗，使用 launch_persistent_context 啟動新實例 (Launch Mode)
    3. 結束時使用 disconnect() 保持瀏覽器運行
    
    重要：
    - 禁止使用 Context Manager (with sync_playwright() as p:)
    - 手動管理 Playwright 生命週期
    - 使用類別變數 _pw_instance 確保持久化
    
    Note:
        使用 127.0.0.1 而非 localhost 避免 IPv6 解析問題
    """
    
    # CDP 端點配置
    CDP_ENDPOINT = "http://127.0.0.1:9222"
    USER_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '.chrome-user-data')
    
    # 🎯 類別變數：確保 Playwright 實例持久化（單例模式）
    _pw_instance: Optional[Playwright] = None
    _browser: Optional[Browser] = None  # 🎯 保持 Browser 實例
    _context: Optional[BrowserContext] = None  # 🎯 關鍵：保持 Context 實例（防止垃圾回收）
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化瀏覽器管理器
        
        Args:
            logger: 日誌記錄器，如果為 None 則使用默認 logger
        """
        self.logger = logger or logging.getLogger(__name__)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.mode: Optional[str] = None  # 'attach' 或 'launch'
    
    def get_active_page(self, url: Optional[str] = None) -> Optional[Page]:
        """
        獲取活動的瀏覽器頁面（優先接管，失敗才啟動）
        
        策略：
        1. 嘗試連接到現有瀏覽器 (CDP: http://127.0.0.1:9222)
        2. 如果連接失敗，啟動新的持久化瀏覽器實例
        3. 如果提供 URL，導航到該 URL
        
        Args:
            url: 可選的目標 URL，如果提供則導航到該 URL
            
        Returns:
            Page: Playwright Page 對象，失敗返回 None
            
        Note:
            使用 127.0.0.1 而非 localhost 是為了避免 Windows 上的 IPv6 解析問題。
            某些系統會將 localhost 解析為 ::1 (IPv6)，導致連接失敗。
        """
        try:
            # 優先嘗試接管現有瀏覽器
            page = self._try_attach_mode(url)
            if page:
                return page
            
            # 接管失敗，啟動新實例
            self.logger.info("[BROWSER] Attach 模式失敗，切換到 Launch 模式")
            page = self._try_launch_mode(url)
            return page
            
        except Exception as e:
            self.logger.error(f"[BROWSER] ❌ 獲取瀏覽器頁面失敗: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _try_attach_mode(self, url: Optional[str] = None) -> Optional[Page]:
        """
        嘗試連接到現有瀏覽器 (Attach Mode)
        
        Args:
            url: 可選的目標 URL
            
        Returns:
            Page: 成功返回 Page 對象，失敗返回 None
            
        Note:
            禁止使用 Context Manager，手動管理 Playwright 生命週期
        """
        try:
            self.logger.info(f"[BROWSER] 嘗試 Attach 模式: {self.CDP_ENDPOINT}")
            
            # 🎯 關鍵：手動啟動 Playwright（不使用 Context Manager）
            if not BrowserManager._pw_instance:
                BrowserManager._pw_instance = sync_playwright().start()
                self.logger.info("[BROWSER] Playwright 實例已啟動（類別變數）")
            
            # 🎯 關鍵：使用 no_viewport=True 避免縮放問題
            self.browser = BrowserManager._pw_instance.chromium.connect_over_cdp(
                self.CDP_ENDPOINT,
                timeout=30000
            )
            
            # 獲取現有 context 和 page
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                
                # 檢查是否已有 Nx Cloud 頁面
                if pages:
                    for page in pages:
                        if url and url in page.url:
                            self.logger.info(f"[BROWSER] ✅ Attach 成功，找到目標頁面: {page.url}")
                            self.page = page
                            self.mode = 'attach'
                            
                            # 🎯 強制同步視口尺寸到實際螢幕解析度
                            self._force_sync_viewport(page)
                            
                            return page
                    
                    # 沒有目標頁面，使用第一個頁面
                    self.page = pages[0]
                    if url:
                        self.logger.info(f"[BROWSER] 導航到目標 URL: {url}")
                        self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    
                    # 🎯 強制同步視口尺寸到實際螢幕解析度
                    self._force_sync_viewport(self.page)
                    
                    self.logger.info(f"[BROWSER] ✅ Attach 成功: {self.page.url}")
                    self.mode = 'attach'
                    return self.page
            
            # 沒有 context，創建新的
            self.context = self.browser.new_context(
                ignore_https_errors=True,
                no_viewport=True  # 🎯 關鍵：禁用固定視口，允許視窗調整大小
            )
            self.page = self.context.new_page()
            
            if url:
                self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # 🎯 強制同步視口尺寸到實際螢幕解析度
            self._force_sync_viewport(self.page)
            
            self.logger.info(f"[BROWSER] ✅ Attach 成功（新 context）")
            self.mode = 'attach'
            return self.page
            
        except Exception as e:
            # 連接失敗 (ECONNREFUSED)
            self.logger.debug(f"[BROWSER] Attach 模式失敗: {e}")
            
            # 🎯 關鍵：不要停止 Playwright 實例（保持持久化）
            # 不調用 pw.stop()
            
            return None
    
    def _try_launch_mode(self, url: Optional[str] = None) -> Optional[Page]:
        """
        啟動新的持久化瀏覽器實例 (Launch Mode)
        
        Args:
            url: 可選的目標 URL
            
        Returns:
            Page: 成功返回 Page 對象，失敗返回 None
            
        Note:
            禁止使用 Context Manager，手動管理 Playwright 生命週期
        """
        try:
            self.logger.info(f"[BROWSER] 嘗試 Launch 模式")
            
            # 清理 DevToolsActivePort 文件（避免端口佔用問題）
            self._cleanup_devtools_port()
            
            # 🎯 關鍵：手動啟動 Playwright（不使用 Context Manager）
            if not BrowserManager._pw_instance:
                BrowserManager._pw_instance = sync_playwright().start()
                self.logger.info("[BROWSER] Playwright 實例已啟動（類別變數）")
            
            # 🎯 使用 launch_persistent_context 啟動持久化瀏覽器
            # 🎯 關鍵：保存到類別變數，防止垃圾回收導致瀏覽器關閉
            BrowserManager._context = BrowserManager._pw_instance.chromium.launch_persistent_context(
                user_data_dir=self.USER_DATA_DIR,
                headless=False,
                args=[
                    '--remote-debugging-port=9222',
                    '--no-first-run',
                    '--no-default-browser-check',
                ],
                ignore_https_errors=True,
                no_viewport=True  # 🎯 關鍵：避免視口縮放問題
            )
            self.context = BrowserManager._context  # 同時保存到實例變數
            
            # 獲取或創建頁面
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = self.context.new_page()
            
            # 導航到目標 URL
            if url:
                self.logger.info(f"[BROWSER] 導航到目標 URL: {url}")
                self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # 最大化瀏覽器
            self._maximize_browser()
            
            # 🎯 強制同步視口尺寸到實際螢幕解析度
            self._force_sync_viewport(self.page)
            
            self.logger.info(f"[BROWSER] ✅ Launch 成功")
            self.mode = 'launch'
            return self.page
            
        except Exception as e:
            self.logger.error(f"[BROWSER] ❌ Launch 模式失敗: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _cleanup_devtools_port(self):
        """
        清理 DevToolsActivePort 文件
        
        該文件可能導致端口佔用問題，啟動前清理可以避免錯誤。
        """
        try:
            devtools_file = os.path.join(self.USER_DATA_DIR, 'DevToolsActivePort')
            if os.path.exists(devtools_file):
                os.remove(devtools_file)
                self.logger.debug(f"[BROWSER] 已清理 DevToolsActivePort 文件")
        except Exception as e:
            self.logger.debug(f"[BROWSER] 清理 DevToolsActivePort 失敗: {e}")
    
    def _maximize_browser(self):
        """
        最大化瀏覽器視窗
        
        使用 pygetwindow 直接操作視窗，確保瀏覽器完全最大化。
        """
        try:
            import pygetwindow as gw
            time.sleep(1)  # 等待視窗出現
            
            chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
            if chrome_windows:
                chrome_windows[0].maximize()
                self.logger.info("[BROWSER] ✅ 瀏覽器已最大化")
        except Exception as e:
            self.logger.warning(f"[BROWSER] 最大化失敗: {e}")
    
    def _force_sync_viewport(self, page: Page):
        """
        強制同步視口尺寸到實際螢幕解析度
        
        關鍵修復：
        1. 必須在 new_context 時設置 no_viewport=True
        2. 然後使用 set_viewport_size() 強制同步到實際螢幕解析度
        3. 這樣可以確保網頁內容自動填充整個視窗，無縮放、無留白
        
        Args:
            page: Playwright Page 對象
            
        Note:
            根據實際螢幕解析度動態設置，而非固定 1920x1080
        """
        try:
            # 🎯 獲取實際視窗尺寸
            import pygetwindow as gw
            chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
            
            if chrome_windows:
                win = chrome_windows[0]
                width = win.width if win.width > 0 else 1920
                height = win.height if win.height > 0 else 1080
            else:
                # 默認使用 Full HD
                width, height = 1920, 1080
            
            # 🎯 強制設置視口尺寸（確保內容填充整個視窗）
            page.set_viewport_size({"width": width, "height": height})
            self.logger.info(f"[BROWSER] ✅ 視口已強制同步: {width}x{height}")
            
        except Exception as e:
            # 如果失敗，使用默認尺寸
            self.logger.warning(f"[BROWSER] ⚠️ 同步視口失敗，使用默認尺寸: {e}")
            try:
                page.set_viewport_size({"width": 1920, "height": 1080})
                self.logger.info(f"[BROWSER] ✅ 視口已設置為默認: 1920x1080")
            except Exception as e2:
                self.logger.error(f"[BROWSER] ❌ 設置默認視口失敗: {e2}")
    
    def disconnect(self):
        """
        斷開瀏覽器連接（保持瀏覽器運行）
        
        ⚠️ 關鍵修復：
        1. 絕對不調用 pw.stop() - 會終止 Playwright 進程
        2. 絕對不調用 browser.close() - 即使是 CDP 連接也可能導致問題
        3. 只清理實例引用，讓 _pw_instance 和 _browser 保持存活
        4. 確保 Case 2-2 可以重新連接到同一個瀏覽器
        
        Note:
            使用單例模式的類別變數 _pw_instance 和 _browser 確保跨測試持久化
        """
        try:
            if self.mode == 'attach':
                self.logger.info("[BROWSER] Attach 模式：釋放連接（瀏覽器保持運行）")
                # 🎯 關鍵：不調用 browser.close()
                # 只清理實例引用
                
            elif self.mode == 'launch':
                self.logger.info("[BROWSER] Launch 模式：釋放連接（瀏覽器保持運行）")
                # 🎯 關鍵：不調用任何關閉方法
                # 因為使用了 launch_persistent_context，瀏覽器會保持運行
            
            # 🎯 關鍵：只清理實例引用，不調用任何 stop() 或 close()
            self.page = None
            self.context = None
            self.browser = None
            
            # 🎯 關鍵：保持類別變數存活（單例模式）
            # BrowserManager._pw_instance 保持運行
            # BrowserManager._context 保持運行（防止垃圾回收關閉瀏覽器）
            # BrowserManager._browser 保持運行（如果有的話）
            
            self.logger.info("[BROWSER] ✅ 已釋放連接，瀏覽器保持運行")
            self.logger.info("[BROWSER] 💡 類別變數 _pw_instance 和 _context 保持存活")
            
        except Exception as e:
            self.logger.warning(f"[BROWSER] ⚠️ 釋放連接時發生錯誤: {e}")
    
    def get_page_info(self) -> dict:
        """
        獲取當前頁面信息（用於調試）
        
        Returns:
            dict: 包含 mode, url, title 等信息
        """
        if not self.page:
            return {"status": "no_page"}
        
        try:
            return {
                "status": "active",
                "mode": self.mode,
                "url": self.page.url,
                "title": self.page.title(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
