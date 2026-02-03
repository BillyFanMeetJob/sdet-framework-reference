# -*- coding: utf-8 -*-
"""
瀏覽器管理類 (Browser)

封裝 WebDriver 的初始化和生命週期管理。
整合反封號機制：User-Agent 隨機化、瀏覽器指紋隱藏。

Author: SDET Team
Date: 2026-01-27
"""

import os
import shutil
from typing import Optional
from toolkit.web_toolkit import create_driver, type_text, click_when_clickable, get_text_when_visible
from toolkit.types import Locator


class Browser:
    """
    瀏覽器管理類
    
    負責 WebDriver 的創建、配置和清理，內建反封號機制：
    - 自動隨機化 User-Agent（從 config 讀取）
    - 移除 Selenium 自動化標記
    - 隨機化瀏覽器視窗大小
    - 自動清理臨時 Profile
    
    Attributes:
        driver (WebDriver): Selenium WebDriver 實例
        wait (WebDriverWait): WebDriverWait 實例
        _profile_path (str): 臨時 Chrome Profile 路徑
    
    Example:
        >>> browser = Browser()
        >>> browser.open("https://example.com")
        >>> browser.quit()
    """
    
    def __init__(self, enable_anti_bot: Optional[bool] = None):
        """
        初始化瀏覽器
        
        Args:
            enable_anti_bot (bool, optional): 是否啟用反封號機制
                                            None 時從 config 讀取
        
        Note:
            - create_driver() 會根據 config 自動配置反封號選項
            - Profile 路徑會被記錄，用於 quit() 時清理
        """
        # create_driver 內部會根據 config 應用反封號配置
        # 包括：User-Agent 隨機化、指紋隱藏、視窗大小隨機化
        self.driver, self.wait = create_driver(enable_anti_bot=enable_anti_bot)
        self._profile_path = self.driver.capabilities.get("chrome", {}).get("userDataDir")

    def open(self, url: str) -> None:
        """
        開啟指定 URL
        
        Args:
            url (str): 目標 URL
        
        Example:
            >>> browser.open("https://example.com")
        """
        self.driver.get(url)

    def type(self, locator: Locator, text: str):
        """
        輸入文字（舊版兼容方法）
        
        注意：建議使用 WebBasePage.smart_type() 以獲得擬人化輸入
        
        Args:
            locator (Locator): Selenium 定位器
            text (str): 要輸入的文字
        
        Returns:
            WebElement: 輸入欄位元素
        """
        return type_text(self.wait, locator, text)

    def click(self, locator: Locator):
        """
        點擊元素（舊版兼容方法）
        
        注意：建議使用 WebBasePage.smart_click() 以獲得擬人化延遲
        
        Args:
            locator (Locator): Selenium 定位器
        
        Returns:
            WebElement: 被點擊的元素
        """
        return click_when_clickable(self.wait, locator)

    def quit(self) -> None:
        """
        關閉瀏覽器並清理臨時資源
        
        自動執行：
        1. 關閉 WebDriver
        2. 清理臨時 Chrome Profile（避免磁碟空間浪費）
        
        Note:
            - Profile 清理失敗不會中斷程式
            - 使用 ignore_errors=True 確保穩定性
        
        Example:
            >>> browser.quit()
        """
        self.driver.quit()
        
        # 優化點：自動清理暫存的 Chrome Profile
        # 避免磁碟累積大量臨時文件（每次執行約 50-100MB）
        if self._profile_path and os.path.exists(self._profile_path):
            try:
                shutil.rmtree(self._profile_path, ignore_errors=True)
            except:
                # 清理失敗不影響主流程（可能被其他進程佔用）
                pass