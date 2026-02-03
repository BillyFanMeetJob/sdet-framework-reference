# base/base_page.py 
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import os
import logging
import toolkit.web_toolkit as tool
from toolkit.types import Locator
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException

if TYPE_CHECKING:
    from base.browser import Browser  # 避免循環 import 問題

# 配置日誌
logger = logging.getLogger(__name__)


class BasePage:
    """
    所有 Page Object 的基底類別。
    
    封裝：
    - browser / driver / wait
    - 常用 Selenium 動作（click/type/get_text/...）
    - VLM 自癒機制（當元素定位失敗時自動觸發 AI 觀測）
    
    Attributes:
        browser: Browser 實例
        driver: WebDriver 實例
        wait: WebDriverWait 實例
        _vlm_enabled: 是否啟用 VLM 學習模式
        _ai_helper: AI Vision Helper 實例（延遲載入）
    """

    def __init__(self, browser: "Browser"):
        self.browser = browser
        self.driver = browser.driver
        self.wait = browser.wait
        
        # VLM 相關屬性（延遲初始化）
        self._vlm_enabled: Optional[bool] = None
        self._ai_helper = None
    
    @property
    def vlm_enabled(self) -> bool:
        """
        檢查是否啟用 VLM 學習模式
        
        Returns:
            是否啟用 VLM
        """
        if self._vlm_enabled is None:
            # 從配置或環境變數讀取
            try:
                from config import DevConfig
                self._vlm_enabled = getattr(DevConfig, "ENABLE_VLM_LEARNING", False)
            except Exception:
                self._vlm_enabled = os.getenv("ENABLE_VLM_LEARNING", "false").lower() == "true"
        
        return self._vlm_enabled
    
    @property
    def ai_helper(self):
        """
        獲取 AI Vision Helper 實例（延遲載入）
        
        Returns:
            AIVisionHelper 實例
        """
        if self._ai_helper is None and self.vlm_enabled:
            try:
                from utils.ai_vision_helper import get_ai_helper
                self._ai_helper = get_ai_helper()
                logger.debug("[BASE_PAGE] AI Vision Helper 已初始化")
            except Exception as e:
                logger.warning(f"[BASE_PAGE] 無法初始化 AI Vision Helper: {e}")
                self._ai_helper = None
        
        return self._ai_helper
    
    def _trigger_vlm_observation(
        self, 
        target_element: str, 
        exception: Exception,
        context: Optional[dict] = None
    ) -> None:
        """
        觸發 VLM 觀測機制（內部方法）
        
        當元素定位失敗時，自動截圖並調用 VLM 進行畫面分析。
        
        Args:
            target_element: 目標元素描述（如 ActionKey 或 locator 字符串）
            exception: 原始異常對象
            context: 額外上下文信息
        """
        if not self.vlm_enabled or not self.ai_helper:
            return
        
        try:
            # 截圖
            screenshot_dir = "logs/ai_intelligence/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                screenshot_dir, 
                f"failure_{target_element}_{timestamp}.png"
            )
            
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"[VLM-TRIGGER] 已截圖: {screenshot_path}")
            
            # 調用 AI 分析
            analysis_result = self.ai_helper.analyze_failure(
                screenshot_path=screenshot_path,
                target_element=target_element,
                context={
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception),
                    **(context or {})
                }
            )
            
            # 記錄 VLM 洞察
            if analysis_result.get("status") == "success":
                vlm_analysis = analysis_result.get("vlm_analysis", {})
                logger.error(
                    f"[VLM-INSIGHT] 目標元素: {target_element}\n"
                    f"  觀測狀態: {vlm_analysis.get('target_element_status')}\n"
                    f"  潛在變化: {vlm_analysis.get('potential_changes')}\n"
                    f"  建議 ActionKey: {vlm_analysis.get('recommended_action_key')}\n"
                    f"  建議定位器: {vlm_analysis.get('recommended_locator')}"
                )
            else:
                logger.warning(f"[VLM-INSIGHT] AI 分析失敗: {analysis_result.get('error')}")
        
        except Exception as e:
            # VLM 調用失敗不應影響原始錯誤拋出
            logger.warning(f"[VLM-TRIGGER] VLM 觀測失敗（不影響測試）: {e}")
    
    def _safe_operation(
        self, 
        operation_func, 
        target_element: str,
        *args, 
        **kwargs
    ):
        """
        安全執行操作，失敗時觸發 VLM 觀測
        
        Args:
            operation_func: 要執行的操作函數
            target_element: 目標元素描述
            *args: 傳遞給操作函數的位置參數
            **kwargs: 傳遞給操作函數的關鍵字參數
            
        Returns:
            操作函數的返回值
            
        Raises:
            原始異常（在觸發 VLM 觀測後）
        """
        try:
            return operation_func(*args, **kwargs)
        except (TimeoutException, NoSuchElementException) as e:
            # 觸發 VLM 觀測
            self._trigger_vlm_observation(
                target_element=target_element,
                exception=e,
                context={"operation": operation_func.__name__}
            )
            # 重新拋出原始異常
            raise

    # === 基本操作封裝（帶 VLM 自癒機制）===

    def type(self, locator: Locator, text: str, clear: bool = True):
        """
        在指定 locator 上輸入文字，預設會先清空。
        
        失敗時自動觸發 VLM 觀測機制。
        
        Args:
            locator: 元素定位器
            text: 要輸入的文字
            clear: 是否先清空
        """
        return self._safe_operation(
            tool.type_text,
            target_element=str(locator),
            wait=self.wait,
            locator=locator,
            text=text,
            clear=clear
        )

    def click(self, locator: Locator):
        """
        等待元素可點擊後執行 click。
        
        失敗時自動觸發 VLM 觀測機制。
        
        Args:
            locator: 元素定位器
        """
        return self._safe_operation(
            tool.click_when_clickable,
            target_element=str(locator),
            wait=self.wait,
            locator=locator
        )

    def get_text(self, locator: Locator) -> str:
        """
        等待元素可見後回傳文字。
        
        失敗時自動觸發 VLM 觀測機制。
        
        Args:
            locator: 元素定位器
            
        Returns:
            元素文字內容
        """
        return self._safe_operation(
            tool.get_text_when_visible,
            target_element=str(locator),
            wait=self.wait,
            locator=locator
        )

    def is_visible(self, locator: Locator) -> bool:
        """
        檢查元素是否可見，不拋例外，回傳 True/False。
        
        注意：此方法不會觸發 VLM 觀測（因為不拋出異常）
        
        Args:
            locator: 元素定位器
            
        Returns:
            元素是否可見
        """
        return tool.is_element_visible(self.wait, locator)

    def wait_for_url(self, expected: str, timeout: int = 10, partial: bool = True) -> bool:
        """
        等待 URL 符合預期（部分比對或完整比對）。
        """
        return tool.wait_for_url(self.driver, expected, timeout=timeout, partial=partial)
    
    def find_all(self, locator: Locator) -> List[WebElement]:
        """
        等待並回傳所有可見元素（List[WebElement]）。
        """
        return tool.find_all_visible_elements(self.wait, locator)

    def get_all_texts(self, items_locator:Locator, text_locator=None) -> List[str]:
        """
        取得一組元素（例如列表列、卡片）的文字清單。
        - items_locator: 外層列表元素的 locator
        - text_locator: 若指定，則在每個 item 內再找子元素取 text
        """
        return tool.get_all_item_texts(self.wait, items_locator, text_locator)

    def elements_count(self,locator: Locator) -> int:
        """
        取得可見元素數量。
        """
        return tool.count_visible_elements(self.wait, locator)
    
    def find_element(self,parent_elem,locator: Locator) -> WebElement:
        """
        在指定父元素底下尋找子元素。
        """
        return tool.find_child_element(parent_elem, locator)