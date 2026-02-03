# -*- coding: utf-8 -*-
"""
Chrome UI 自動化工具

當 Playwright 無法接管 Chrome 時（例如 Nx App 開啟的視窗），
使用 PyAutoGUI 進行螢幕級別的 UI 自動化。

元件定位方式：
1. 圖像識別：準備元件截圖，在螢幕上找到它
2. OCR 文字識別：找到特定文字的位置
3. VLM 視覺模型：用 AI 描述要點擊的元件（如「點擊登入按鈕」）
4. 座標比例：根據視窗比例計算位置

Author: SDET Team
Date: 2026-02-01
"""

import time
import os
import pyautogui
import pygetwindow as gw
from typing import Optional, Tuple, List, Union
import logging
from PIL import Image


class ChromeUIAutomation:
    """
    Chrome UI 自動化類
    
    支援多種元件定位方式：
    - click_image(): 點擊圖片匹配的位置
    - click_text(): 點擊 OCR 識別的文字
    - click_by_description(): 用 VLM 描述要點擊的元件
    - click_at_ratio(): 按視窗比例點擊
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化 Chrome UI 自動化
        
        Args:
            logger: 日誌記錄器
        """
        self.logger = logger or logging.getLogger(__name__)
        self.window: Optional[gw.Win32Window] = None
        
        # PyAutoGUI 安全設置
        pyautogui.FAILSAFE = True  # 移動滑鼠到左上角可中斷
        pyautogui.PAUSE = 0.1  # 每個操作後短暫暫停
    
    # ========================================================================
    # 視窗管理
    # ========================================================================
    
    def find_chrome_window(self, title_contains: Optional[str] = None) -> Optional[gw.Win32Window]:
        """
        查找 Chrome 視窗
        
        Args:
            title_contains: 視窗標題需包含的文字（可選）
            
        Returns:
            找到的視窗，否則返回 None
        """
        try:
            all_windows = gw.getAllWindows()
            chrome_windows = [
                w for w in all_windows 
                if 'chrome' in w.title.lower() and w.visible and w.width > 400
            ]
            
            if not chrome_windows:
                self.logger.warning("[CHROME_UI] 未找到 Chrome 視窗")
                return None
            
            # 如果指定了標題關鍵字，進一步過濾
            if title_contains:
                filtered = [w for w in chrome_windows if title_contains.lower() in w.title.lower()]
                if filtered:
                    chrome_windows = filtered
            
            self.window = chrome_windows[0]
            self.logger.info(f"[CHROME_UI] 找到 Chrome 視窗: {self.window.title}")
            
            return self.window
            
        except Exception as e:
            self.logger.error(f"[CHROME_UI] 查找視窗失敗: {e}")
            return None
    
    def activate_window(self) -> bool:
        """激活並置頂 Chrome 視窗"""
        if not self.window:
            return False
        
        try:
            if self.window.isMinimized:
                self.window.restore()
                time.sleep(0.3)
            
            self.window.activate()
            time.sleep(0.3)
            return True
            
        except Exception as e:
            self.logger.error(f"[CHROME_UI] 激活視窗失敗: {e}")
            return False
    
    def get_window_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        獲取視窗區域 (left, top, width, height)
        """
        if not self.window:
            return None
        return (self.window.left, self.window.top, self.window.width, self.window.height)
    
    # ========================================================================
    # 方式 1: 圖像識別定位
    # ========================================================================
    
    def click_image(
        self, 
        image_path: str, 
        confidence: float = 0.8,
        timeout: int = 10,
        clicks: int = 1
    ) -> bool:
        """
        點擊圖片匹配的位置
        
        準備一張元件的截圖（如按鈕截圖），此方法會在螢幕上找到它並點擊。
        
        Args:
            image_path: 元件截圖的路徑
            confidence: 匹配信心度 (0.0-1.0)，需要 opencv-python
            timeout: 超時時間（秒）
            clicks: 點擊次數
            
        Returns:
            是否成功
            
        Example:
            # 準備一張「登入」按鈕的截圖，保存為 login_btn.png
            chrome.click_image("res/web/login_btn.png")
        """
        if not os.path.exists(image_path):
            self.logger.error(f"[CHROME_UI] 圖片不存在: {image_path}")
            return False
        
        self.activate_window()
        
        self.logger.info(f"[CHROME_UI] 尋找圖片: {image_path}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 在視窗區域內搜索（更快）
                region = self.get_window_region()
                
                location = pyautogui.locateOnScreen(
                    image_path, 
                    confidence=confidence,
                    region=region
                )
                
                if location:
                    # 獲取中心點
                    center = pyautogui.center(location)
                    self.logger.info(f"[CHROME_UI] ✅ 找到圖片，位置: {center}")
                    
                    pyautogui.click(center.x, center.y, clicks=clicks)
                    return True
                    
            except Exception as e:
                self.logger.debug(f"[CHROME_UI] 搜索中... {e}")
            
            time.sleep(0.5)
        
        self.logger.error(f"[CHROME_UI] ❌ 超時未找到圖片: {image_path}")
        return False
    
    def find_all_images(
        self, 
        image_path: str, 
        confidence: float = 0.8
    ) -> List[Tuple[int, int]]:
        """
        找到所有匹配圖片的位置
        
        Args:
            image_path: 元件截圖的路徑
            confidence: 匹配信心度
            
        Returns:
            座標列表 [(x, y), ...]
        """
        if not os.path.exists(image_path):
            return []
        
        self.activate_window()
        region = self.get_window_region()
        
        try:
            locations = list(pyautogui.locateAllOnScreen(
                image_path, 
                confidence=confidence,
                region=region
            ))
            
            centers = [pyautogui.center(loc) for loc in locations]
            return [(c.x, c.y) for c in centers]
            
        except Exception as e:
            self.logger.error(f"[CHROME_UI] 搜索圖片失敗: {e}")
            return []
    
    # ========================================================================
    # 方式 2: OCR 文字識別定位
    # ========================================================================
    
    def click_text(
        self, 
        text: str, 
        timeout: int = 10,
        clicks: int = 1,
        lang: str = "chi_tra+eng"
    ) -> bool:
        """
        點擊包含特定文字的位置
        
        使用 OCR（pytesseract）識別螢幕上的文字，找到後點擊。
        
        Args:
            text: 要找的文字（部分匹配）
            timeout: 超時時間（秒）
            clicks: 點擊次數
            lang: OCR 語言（chi_tra=繁體中文, eng=英文）
            
        Returns:
            是否成功
            
        Example:
            chrome.click_text("登入")
            chrome.click_text("Submit")
            
        Note:
            需要安裝: pip install pytesseract
            以及 Tesseract OCR: https://github.com/tesseract-ocr/tesseract
        """
        try:
            import pytesseract
        except ImportError:
            self.logger.error("[CHROME_UI] 需要安裝 pytesseract: pip install pytesseract")
            return False
        
        self.activate_window()
        
        self.logger.info(f"[CHROME_UI] 尋找文字: {text}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 截取視窗區域
                region = self.get_window_region()
                if not region:
                    continue
                
                screenshot = pyautogui.screenshot(region=region)
                
                # OCR 識別（獲取文字和位置）
                data = pytesseract.image_to_data(
                    screenshot, 
                    lang=lang, 
                    output_type=pytesseract.Output.DICT
                )
                
                # 搜索文字
                for i, word in enumerate(data['text']):
                    if text.lower() in str(word).lower():
                        # 計算文字中心位置
                        x = region[0] + data['left'][i] + data['width'][i] // 2
                        y = region[1] + data['top'][i] + data['height'][i] // 2
                        
                        self.logger.info(f"[CHROME_UI] ✅ 找到文字 '{word}'，位置: ({x}, {y})")
                        pyautogui.click(x, y, clicks=clicks)
                        return True
                        
            except Exception as e:
                self.logger.debug(f"[CHROME_UI] OCR 搜索中... {e}")
            
            time.sleep(0.5)
        
        self.logger.error(f"[CHROME_UI] ❌ 超時未找到文字: {text}")
        return False
    
    def find_text_position(self, text: str, lang: str = "chi_tra+eng") -> Optional[Tuple[int, int]]:
        """
        找到文字的位置（不點擊）
        
        Args:
            text: 要找的文字
            lang: OCR 語言
            
        Returns:
            座標 (x, y)，未找到返回 None
        """
        try:
            import pytesseract
        except ImportError:
            return None
        
        self.activate_window()
        region = self.get_window_region()
        if not region:
            return None
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            data = pytesseract.image_to_data(
                screenshot, 
                lang=lang, 
                output_type=pytesseract.Output.DICT
            )
            
            for i, word in enumerate(data['text']):
                if text.lower() in str(word).lower():
                    x = region[0] + data['left'][i] + data['width'][i] // 2
                    y = region[1] + data['top'][i] + data['height'][i] // 2
                    return (x, y)
                    
        except Exception as e:
            self.logger.error(f"[CHROME_UI] OCR 失敗: {e}")
        
        return None
    
    # ========================================================================
    # 方式 3: VLM 視覺模型定位（最智能）
    # ========================================================================
    
    def click_by_description(
        self, 
        description: str,
        timeout: int = 15,
        clicks: int = 1
    ) -> bool:
        """
        用自然語言描述要點擊的元件，VLM 模型會回傳座標
        
        這是最智能的方式，可以處理：
        - "點擊登入按鈕"
        - "點擊藍色的提交按鈕"
        - "點擊第二個輸入框"
        
        Args:
            description: 元件描述（自然語言）
            timeout: 超時時間（秒）
            clicks: 點擊次數
            
        Returns:
            是否成功
            
        Example:
            chrome.click_by_description("點擊登入按鈕")
            chrome.click_by_description("Click the blue Submit button")
            
        Note:
            需要 VLM 引擎（Ollama + llava 或 Gemini）
        """
        self.activate_window()
        
        self.logger.info(f"[CHROME_UI] VLM 定位: {description}")
        
        try:
            # 截取視窗
            region = self.get_window_region()
            if not region:
                return False
            
            screenshot = pyautogui.screenshot(region=region)
            
            # 保存臨時截圖
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), "chrome_vlm_temp.png")
            screenshot.save(temp_path)
            
            # 調用 VLM 引擎
            from toolkit.vlm_engine import UnifiedVLM
            
            vlm = UnifiedVLM()
            
            # 構建提示詞
            prompt = f"""請找到以下元件的位置並回傳座標：

描述：{description}

請只回傳一個座標，格式為 (x, y)，其中 x 和 y 是相對於圖片左上角的像素值。
如果找不到，回傳 None。

只回傳座標，不要其他文字。"""
            
            # 調用 VLM
            result = vlm.analyze_image(temp_path, prompt)
            
            if result and result != "None":
                # 解析座標
                import re
                match = re.search(r'\((\d+),\s*(\d+)\)', result)
                if match:
                    rel_x, rel_y = int(match.group(1)), int(match.group(2))
                    
                    # 轉換為螢幕座標
                    abs_x = region[0] + rel_x
                    abs_y = region[1] + rel_y
                    
                    self.logger.info(f"[CHROME_UI] ✅ VLM 找到元件，位置: ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y, clicks=clicks)
                    return True
            
            self.logger.error(f"[CHROME_UI] ❌ VLM 未找到元件: {description}")
            return False
            
        except ImportError:
            self.logger.error("[CHROME_UI] VLM 引擎不可用，請確認 toolkit/vlm_engine.py 存在")
            return False
        except Exception as e:
            self.logger.error(f"[CHROME_UI] VLM 定位失敗: {e}")
            return False
    
    # ========================================================================
    # 方式 4: 座標比例定位
    # ========================================================================
    
    def click_at_ratio(self, x_ratio: float, y_ratio: float, clicks: int = 1) -> bool:
        """
        在視窗內按比例點擊
        
        Args:
            x_ratio: X 座標比例 (0.0 - 1.0)
            y_ratio: Y 座標比例 (0.0 - 1.0)
            clicks: 點擊次數
            
        Example:
            chrome.click_at_ratio(0.5, 0.3)  # 點擊視窗中央偏上
        """
        if not self.window:
            return False
        
        self.activate_window()
        
        x = self.window.left + int(self.window.width * x_ratio)
        y = self.window.top + int(self.window.height * y_ratio)
        
        self.logger.info(f"[CHROME_UI] 點擊座標: ({x}, {y}) [比例: {x_ratio:.2f}, {y_ratio:.2f}]")
        pyautogui.click(x, y, clicks=clicks)
        
        return True
    
    def click_at_offset(self, x_offset: int, y_offset: int, clicks: int = 1) -> bool:
        """
        在視窗內按偏移點擊
        
        Args:
            x_offset: 相對於視窗左上角的 X 偏移（像素）
            y_offset: 相對於視窗左上角的 Y 偏移（像素）
            clicks: 點擊次數
        """
        if not self.window:
            return False
        
        self.activate_window()
        
        x = self.window.left + x_offset
        y = self.window.top + y_offset
        
        self.logger.info(f"[CHROME_UI] 點擊座標: ({x}, {y}) [偏移: {x_offset}, {y_offset}]")
        pyautogui.click(x, y, clicks=clicks)
        
        return True
    
    # ========================================================================
    # 輸入操作
    # ========================================================================
    
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        輸入英文/數字文字
        
        Args:
            text: 要輸入的文字
            interval: 每個字元之間的間隔（秒）
        """
        self.logger.info(f"[CHROME_UI] 輸入文字: {text[:20]}...")
        pyautogui.typewrite(text, interval=interval)
        return True
    
    def type_chinese(self, text: str) -> bool:
        """
        輸入中文文字（使用剪貼簿）
        
        Args:
            text: 要輸入的文字
        """
        try:
            import pyperclip
            
            self.logger.info(f"[CHROME_UI] 輸入中文: {text[:20]}...")
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            return True
            
        except Exception as e:
            self.logger.error(f"[CHROME_UI] 中文輸入失敗: {e}")
            return False
    
    def type_in_field(
        self, 
        field_identifier: Union[str, Tuple[float, float]], 
        text: str,
        clear_first: bool = True
    ) -> bool:
        """
        在指定欄位輸入文字
        
        Args:
            field_identifier: 欄位識別方式
                - str: 圖片路徑或文字（會自動判斷）
                - Tuple[float, float]: 座標比例 (x_ratio, y_ratio)
            text: 要輸入的文字
            clear_first: 是否先清空欄位
            
        Example:
            # 方式 1: 用圖片找到輸入框
            chrome.type_in_field("res/web/email_input.png", "user@example.com")
            
            # 方式 2: 用座標比例
            chrome.type_in_field((0.5, 0.3), "user@example.com")
            
            # 方式 3: 用文字標籤
            chrome.type_in_field("Email:", "user@example.com")
        """
        # 先點擊欄位
        clicked = False
        
        if isinstance(field_identifier, tuple):
            # 座標比例
            clicked = self.click_at_ratio(field_identifier[0], field_identifier[1])
        elif isinstance(field_identifier, str):
            if os.path.exists(field_identifier):
                # 圖片路徑
                clicked = self.click_image(field_identifier)
            else:
                # 文字標籤
                clicked = self.click_text(field_identifier)
        
        if not clicked:
            return False
        
        time.sleep(0.3)
        
        # 清空欄位
        if clear_first:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
        
        # 輸入文字
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            # 包含中文
            return self.type_chinese(text)
        else:
            return self.type_text(text)
    
    # ========================================================================
    # 其他操作
    # ========================================================================
    
    def press_key(self, key: str) -> bool:
        """按下鍵盤按鍵"""
        self.logger.info(f"[CHROME_UI] 按下按鍵: {key}")
        pyautogui.press(key)
        return True
    
    def hotkey(self, *keys) -> bool:
        """按下組合鍵"""
        self.logger.info(f"[CHROME_UI] 組合鍵: {'+'.join(keys)}")
        pyautogui.hotkey(*keys)
        return True
    
    def scroll(self, clicks: int, x_ratio: float = 0.5, y_ratio: float = 0.5) -> bool:
        """滾動頁面"""
        if not self.window:
            return False
        
        x = self.window.left + int(self.window.width * x_ratio)
        y = self.window.top + int(self.window.height * y_ratio)
        
        pyautogui.moveTo(x, y)
        time.sleep(0.1)
        pyautogui.scroll(clicks)
        
        return True
    
    def take_screenshot(self, filename: str = "chrome_screenshot.png") -> Optional[str]:
        """截取視窗截圖"""
        if not self.window:
            return None
        
        try:
            from config import EnvConfig
            screenshot_dir = os.path.join(EnvConfig.PROJECT_ROOT, "report", "screenshots")
        except:
            screenshot_dir = "screenshots"
        
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        region = (self.window.left, self.window.top, self.window.width, self.window.height)
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(filepath)
        
        self.logger.info(f"[CHROME_UI] ✅ 截圖已保存: {filepath}")
        return filepath
    
    def wait(self, seconds: float) -> None:
        """等待指定秒數"""
        time.sleep(seconds)


# ============================================================================
# 使用範例
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    chrome = ChromeUIAutomation()
    
    # 找到 Chrome 視窗
    if chrome.find_chrome_window("Nx Cloud"):
        print("找到 Nx Cloud 視窗!")
        
        # 方式 1: 圖像識別
        # chrome.click_image("res/web/login_btn.png")
        
        # 方式 2: OCR 文字識別
        # chrome.click_text("登入")
        
        # 方式 3: VLM 描述
        # chrome.click_by_description("點擊藍色的登入按鈕")
        
        # 方式 4: 座標比例
        chrome.click_at_ratio(0.5, 0.5)
        
        # 輸入文字
        # chrome.type_in_field("Email:", "user@example.com")
        
        # 截圖
        chrome.take_screenshot("test.png")
    else:
        print("未找到 Chrome 視窗")
