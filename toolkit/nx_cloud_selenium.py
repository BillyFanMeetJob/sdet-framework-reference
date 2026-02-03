# -*- coding: utf-8 -*-
"""
Nx Cloud Selenium 自動化工具

由於無法直接繼承 Nx App 的 Chrome session，
此工具使用 Selenium 啟動獨立的 Chrome 並自動登錄。

使用方法：
1. Case 2-1 使用 Nx App 開啟 Chrome（確認 Nx Cloud 可正常訪問）
2. Case 2-2 使用此工具啟動新的 Chrome 並自動登錄
3. 登錄後即可進行 DOM 控制測試

Author: SDET Team
Date: 2026-02-01
"""

import os
import sys
import time
import subprocess
import logging
from typing import Optional

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class NxCloudSelenium:
    """
    Nx Cloud Selenium 自動化類
    
    提供完整的 DOM 控制能力，包括：
    - 自動啟動 Chrome（帶 debugging port）
    - 自動登錄 Nx Cloud
    - 完整的 DOM 操作方法
    """
    
    # Chrome profile 路徑
    CHROME_PROFILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   '.chrome-nx-cloud')
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化
        
        Args:
            logger: 日誌記錄器
        """
        self.logger = logger or logging.getLogger(__name__)
        self.driver: Optional[webdriver.Chrome] = None
        self.chrome_process = None
        
    def _ensure_chrome_closed(self):
        """確保所有 Chrome 進程都已關閉"""
        self.logger.info("[NX_SELENIUM] 關閉現有 Chrome 進程...")
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], 
                       capture_output=True, text=True)
        subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'], 
                       capture_output=True, text=True)
        time.sleep(2)
        
    def _start_chrome_with_debug_port(self, port: int = 9222) -> bool:
        """
        啟動帶 debugging port 的 Chrome
        
        Args:
            port: Debugging port (預設 9222)
            
        Returns:
            是否成功
        """
        self._ensure_chrome_closed()
        
        self.logger.info(f"[NX_SELENIUM] 啟動 Chrome (debugging port: {port})...")
        
        # 找到 Chrome 路徑
        chrome_paths = [
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        ]
        chrome_path = None
        for p in chrome_paths:
            if os.path.exists(p):
                chrome_path = p
                break
                
        if not chrome_path:
            self.logger.error("[NX_SELENIUM] 找不到 Chrome")
            return False
            
        # 創建 profile 目錄
        os.makedirs(self.CHROME_PROFILE, exist_ok=True)
        
        # 啟動 Chrome
        cmd = [
            chrome_path,
            f'--remote-debugging-port={port}',
            f'--user-data-dir={self.CHROME_PROFILE}',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        
        self.chrome_process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        self.logger.info(f"[NX_SELENIUM] Chrome PID: {self.chrome_process.pid}")
        time.sleep(3)
        
        # 驗證 debugging port
        import requests
        try:
            r = requests.get(f'http://127.0.0.1:{port}/json/version', timeout=5)
            self.logger.info(f"[NX_SELENIUM] ✅ Chrome 已啟動: {r.json().get('Browser')}")
            return True
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] ❌ Debugging port 不可用: {e}")
            return False
            
    def connect(self, port: int = 9222) -> bool:
        """
        連接到帶 debugging port 的 Chrome
        
        如果 Chrome 未運行，會自動啟動。
        
        Args:
            port: Debugging port
            
        Returns:
            是否成功
        """
        # 檢查是否已經有 debugging port
        import requests
        try:
            requests.get(f'http://127.0.0.1:{port}/json/version', timeout=2)
            self.logger.info(f"[NX_SELENIUM] 找到現有的 Chrome (port {port})")
        except:
            # 啟動新的 Chrome
            if not self._start_chrome_with_debug_port(port):
                return False
                
        # 連接 Selenium
        self.logger.info("[NX_SELENIUM] 連接 Selenium...")
        options = Options()
        options.add_experimental_option('debuggerAddress', f'127.0.0.1:{port}')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.logger.info("[NX_SELENIUM] ✅ Selenium 已連接")
            return True
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] ❌ Selenium 連接失敗: {e}")
            return False
            
    def login(self, url: str = None, email: str = None, password: str = None) -> bool:
        """
        自動登錄 Nx Cloud
        
        Args:
            url: Nx Cloud URL（如果為 None，使用預設）
            email: 郵箱（如果為 None，從 config 讀取）
            password: 密碼（如果為 None，從 config 讀取）
            
        Returns:
            是否成功
        """
        if not self.driver:
            self.logger.error("[NX_SELENIUM] 請先調用 connect()")
            return False
            
        # 讀取配置
        try:
            from config import EnvConfig
            url = url or EnvConfig.BASE_URL or 'https://nx-cn.nxvms.cloud'
            email = email or EnvConfig.NX_CLOUD_EMAIL
            password = password or EnvConfig.NX_CLOUD_PASSWORD
        except:
            url = url or 'https://nx-cn.nxvms.cloud'
            
        if not email or not password:
            self.logger.error("[NX_SELENIUM] 缺少登錄憑證")
            return False
            
        self.logger.info(f"[NX_SELENIUM] 導航到: {url}")
        self.driver.get(url)
        time.sleep(3)
        
        # 檢查是否已經登錄
        body_text = self.driver.find_element(By.TAG_NAME, 'body').text
        if '登录' not in body_text and 'login' not in body_text.lower():
            self.logger.info("[NX_SELENIUM] ✅ 已經登錄")
            return True
            
        self.logger.info("[NX_SELENIUM] 開始登錄流程...")
        
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # 點擊登錄按鈕
            self.logger.info("[NX_SELENIUM] 點擊登錄按鈕...")
            login_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '登录') or contains(text(), 'Sign In') or contains(text(), 'Login')]")
            ))
            login_btn.click()
            time.sleep(2)
            
            # 輸入郵箱
            self.logger.info("[NX_SELENIUM] 輸入郵箱...")
            email_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@type='email' or @name='email' or @placeholder='Email']")
            ))
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)
            
            # 點擊下一步
            next_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '下一步') or contains(text(), 'Next') or contains(text(), '繼續')]")
            ))
            next_btn.click()
            time.sleep(2)
            
            # 輸入密碼
            self.logger.info("[NX_SELENIUM] 輸入密碼...")
            pwd_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@type='password' or @name='password']")
            ))
            pwd_input.clear()
            pwd_input.send_keys(password)
            time.sleep(1)
            
            # 點擊登錄
            submit_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '登录') or contains(text(), 'Sign In') or contains(text(), 'Log In') or @type='submit']")
            ))
            submit_btn.click()
            time.sleep(5)
            
            # 驗證登錄結果
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            if '登录' in body_text or 'login' in body_text.lower():
                self.logger.warning("[NX_SELENIUM] ⚠️ 登錄可能失敗")
                return False
                
            self.logger.info("[NX_SELENIUM] ✅ 登錄成功！")
            return True
            
        except TimeoutException as e:
            self.logger.error(f"[NX_SELENIUM] ❌ 登錄超時: {e}")
            return False
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] ❌ 登錄失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
            
    def navigate(self, url: str):
        """導航到指定 URL"""
        if self.driver:
            self.driver.get(url)
            
    def click(self, xpath: str, timeout: int = 10) -> bool:
        """
        點擊元素
        
        Args:
            xpath: XPath 選擇器
            timeout: 超時秒數
            
        Returns:
            是否成功
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] 點擊失敗: {e}")
            return False
            
    def fill(self, xpath: str, text: str, timeout: int = 10) -> bool:
        """
        填寫輸入框
        
        Args:
            xpath: XPath 選擇器
            text: 要輸入的文字
            timeout: 超時秒數
            
        Returns:
            是否成功
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] 填寫失敗: {e}")
            return False
            
    def get_text(self, xpath: str, timeout: int = 10) -> Optional[str]:
        """
        獲取元素文字
        
        Args:
            xpath: XPath 選擇器
            timeout: 超時秒數
            
        Returns:
            元素文字，失敗返回 None
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element.text
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] 獲取文字失敗: {e}")
            return None
            
    def wait_for(self, xpath: str, timeout: int = 30) -> bool:
        """
        等待元素出現
        
        Args:
            xpath: XPath 選擇器
            timeout: 超時秒數
            
        Returns:
            元素是否出現
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            return True
        except:
            return False
            
    def screenshot(self, filename: str = None) -> Optional[str]:
        """
        截圖
        
        Args:
            filename: 檔案名（如果為 None，自動生成）
            
        Returns:
            截圖路徑
        """
        if not self.driver:
            return None
            
        if not filename:
            filename = f"selenium_{int(time.time())}.png"
            
        try:
            screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          'report', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            self.logger.info(f"[NX_SELENIUM] ✅ 截圖: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"[NX_SELENIUM] ❌ 截圖失敗: {e}")
            return None
            
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """獲取 WebDriver 實例"""
        return self.driver
        
    def close(self):
        """關閉（保持 Chrome 運行）"""
        self.driver = None
        self.logger.info("[NX_SELENIUM] ✅ 已釋放 Selenium 控制")
        
    def quit(self):
        """完全退出（關閉 Chrome）"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        self.logger.info("[NX_SELENIUM] ✅ Chrome 已關閉")


# ============================================================================
# 測試
# ============================================================================

def test():
    """測試 NxCloudSelenium"""
    logging.basicConfig(level=logging.INFO)
    
    nx = NxCloudSelenium()
    
    print("="*60)
    print("NxCloudSelenium Test")
    print("="*60)
    
    # 連接
    if not nx.connect():
        print("Failed to connect!")
        return
        
    # 導航
    nx.navigate('https://nx-cn.nxvms.cloud/?from=client&context=menu')
    time.sleep(3)
    
    # 獲取頁面內容
    driver = nx.get_driver()
    body = driver.find_element(By.TAG_NAME, 'body')
    print(f"Title: {driver.title}")
    print(f"Body length: {len(body.text)} chars")
    print(f"First 500 chars:\n{body.text[:500]}")
    
    # 截圖
    nx.screenshot("test.png")
    
    print("\n✅ Test completed!")
    print("Chrome stays open for inspection...")
    
    # 保持運行
    input("Press Enter to quit...")
    nx.quit()


if __name__ == "__main__":
    test()
