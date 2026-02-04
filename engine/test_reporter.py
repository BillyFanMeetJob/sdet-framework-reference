# -*- coding: utf-8 -*-
"""
測試報告生成模組

功能：
1. 生成 HTML 格式的測試報告（類似 UFT 報告格式）
2. 記錄每個步驟的檢核結果和截圖
3. 在截圖中標出檢核的物件（紅框）
4. VLM 座標驗證與數據持久化
"""

import os
import time
import pyautogui
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from config import EnvConfig
from toolkit.types import Toolkit
from toolkit.coordinate_validator import CoordinateValidator


class TestReporter:
    """測試報告生成器"""
    
    def __init__(self, test_name: str, mobile_driver=None):
        """
        初始化測試報告生成器
        
        Args:
            test_name: 測試名稱
            mobile_driver: Appium WebDriver 實例（用於移動端測試截圖，可選）
        """
        self.test_name = test_name
        self.start_time = datetime.now()
        self.end_time = None
        self.steps: List[Dict] = []
        self.mobile_driver = mobile_driver  # 保存 mobile_driver 引用，用於截圖
        
        # 建立報告目錄結構
        self.report_dir = self._create_report_directory()
        
        # 截圖目錄
        self.screenshot_dir = os.path.join(self.report_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 用於記錄自動截圖（每次辨識成功時保存）
        self.recognition_screenshots: List[Dict] = []
        
        # 初始化 logger（用於調試日誌）
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化座標驗證器（用於 VLM 座標驗證）
        self.coordinate_validator = CoordinateValidator(
            threshold=15.0,  # 預設閾值 15 像素
            logger=self.logger
        )
    
    def _create_report_directory(self) -> str:
        """
        建立報告目錄結構
        
        report/
        └── <TestCaseID-TestName>/
            └── <YYYY-MM-DD_HH-MM-SS>/
        
        如果環境變數 TEST_REPORT_DIR 已設置，則使用該目錄（確保與 test_case_launcher 使用相同的目錄）
        """
        # 檢查環境變數，如果已設置則使用（由 test_case_launcher 傳遞）
        import os
        test_report_dir = os.environ.get('TEST_REPORT_DIR')
        if test_report_dir:
            # 確保目錄存在
            os.makedirs(test_report_dir, exist_ok=True)
            # 記錄使用的目錄（用於調試）
            import logging
            logger = logging.getLogger(self.__class__.__name__)
            logger.info(f"[TEST_REPORTER] 使用環境變數指定的報告目錄: {test_report_dir}")
            return test_report_dir
        
        # 否則使用原有邏輯創建目錄
        project_root = EnvConfig.PROJECT_ROOT
        report_base = os.path.join(project_root, "report")
        
        # 使用測試名稱建立資料夾（清理特殊字元）
        safe_test_name = self.test_name.replace("/", "_").replace("\\", "_")
        
        # 檢查是否有 test_case 序號（從環境變數獲取）
        test_case = os.environ.get('TEST_CASE_ID', '')
        if test_case:
            safe_test_case = test_case.lower().replace(" ", "")  # 轉小寫並移除空格
            folder_name = f"{safe_test_case}-{safe_test_name}"
        else:
            folder_name = safe_test_name
        
        test_dir = os.path.join(report_base, folder_name)
        
        # 使用執行時間建立資料夾
        time_str = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        report_dir = os.path.join(test_dir, time_str)
        
        os.makedirs(report_dir, exist_ok=True)
        return report_dir
    
    def add_step(
        self,
        step_no: int,
        step_name: str,
        status: str,  # 'pass', 'fail', 'warning'
        message: str = "",
        verification_items: List[Dict] = None,
        screenshot_path: str = None
    ):
        """
        添加測試步驟
        
        :param step_no: 步驟編號
        :param step_name: 步驟名稱
        :param status: 狀態 ('pass', 'fail', 'warning')
        :param message: 步驟訊息
        :param verification_items: 檢核項目列表 [{"name": "物件名稱", "x": x, "y": y, "width": w, "height": h}, ...]
        :param screenshot_path: 截圖路徑（如果不提供，會自動截圖）
        """
        # 如果沒有提供截圖，自動截圖
        if screenshot_path is None:
            screenshot_path = self._take_screenshot_with_annotations(
                step_no, verification_items or []
            )
        
        step = {
            "step_no": step_no,
            "step_name": step_name,
            "status": status,
            "message": message,
            "verification_items": verification_items or [],
            "screenshot_path": screenshot_path,
            "timestamp": datetime.now().isoformat()
        }
        self.steps.append(step)
    
    def _take_screenshot_with_annotations(
        self,
        step_no: int,
        verification_items: List[Dict]
    ) -> str:
        """
        截圖並在圖中標出檢核物件（紅框）
        
        :param step_no: 步驟編號
        :param verification_items: 檢核項目列表
        :return: 截圖檔案路徑
        """
        # 🎯 根據是否有 mobile_driver 決定截圖方式
        # - 如果有 mobile_driver：使用 Appium 截圖（只截取手機模擬器）
        # - 如果沒有 mobile_driver：使用 pyautogui 截圖（全屏）
        if self.mobile_driver:
            # Mobile 測試：使用 Appium 截圖
            try:
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # 使用 Appium 的 save_screenshot 方法截圖（只截取手機模擬器）
                self.mobile_driver.save_screenshot(temp_path)
                
                # 讀取截圖並轉換為 PIL Image
                from PIL import Image
                screenshot = Image.open(temp_path)
                
                # 刪除臨時文件
                try:
                    os.unlink(temp_path)
                except:
                    pass
            except Exception as e:
                # 如果 Appium 截圖失敗，回退到全屏截圖並記錄警告
                import logging
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning(f"[REPORTER] Mobile 截圖失敗，回退到全屏截圖: {e}")
                screenshot = pyautogui.screenshot()
        else:
            # Desktop/Web 測試：使用 pyautogui 截圖（全屏）
            screenshot = pyautogui.screenshot()
        
        # 轉換為 PIL Image
        img = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # 繪製紅框標出檢核物件
        for item in verification_items:
            x = item.get('x', 0)
            y = item.get('y', 0)
            width = item.get('width', 50)
            height = item.get('height', 50)
            
            # 繪製紅色矩形框
            rect = [x, y, x + width, y + height]
            draw.rectangle(rect, outline='red', width=3)
            
            # 標註物件名稱
            item_name = item.get('name', 'Object')
            try:
                # 嘗試使用系統字體
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                # 如果找不到字體，使用預設字體
                font = ImageFont.load_default()
            
            # 在框的上方顯示名稱
            text_bbox = draw.textbbox((x, y - 20), item_name, font=font)
            draw.rectangle(
                [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
                fill='red'
            )
            draw.text((x, y - 20), item_name, fill='white', font=font)
        
        # 保存截圖
        filename = f"step_{step_no:03d}_{int(time.time())}.png"
        screenshot_path = os.path.join(self.screenshot_dir, filename)
        img.save(screenshot_path)
        
        return screenshot_path
    
    def _take_recognition_screenshot_with_region(
        self,
        step_no: int,
        item_name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        region: Tuple[int, int, int, int] = None,
        vlm_box: Tuple[int, int, int, int] = None  # VLM 邊界框 (xmin, ymin, xmax, ymax)
    ) -> str:
        """
        截圖並在圖中標出辨識物件和搜尋範圍
        
        :param step_no: 步驟編號
        :param item_name: 物件名稱
        :param x: 物件 X 座標
        :param y: 物件 Y 座標
        :param width: 物件寬度
        :param height: 物件高度
        :param region: 搜尋區域 (left, top, width, height)
        :return: 截圖檔案路徑
        """
        # 🎯 根據是否有 mobile_driver 決定截圖方式
        if self.mobile_driver:
            # Mobile 測試：使用 Appium 截圖
            try:
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # 使用 Appium 的 save_screenshot 方法截圖（只截取手機模擬器）
                self.mobile_driver.save_screenshot(temp_path)
                
                # 讀取截圖並轉換為 PIL Image
                from PIL import Image
                screenshot = Image.open(temp_path)
                
                # 刪除臨時文件
                try:
                    os.unlink(temp_path)
                except:
                    pass
            except Exception as e:
                # 如果 Appium 截圖失敗，回退到全屏截圖並記錄警告
                import logging
                logger = logging.getLogger(self.__class__.__name__)
                logger.warning(f"[REPORTER] Mobile 截圖失敗，回退到全屏截圖: {e}")
                screenshot = pyautogui.screenshot()
        else:
            # Desktop/Web 測試：使用 pyautogui 截圖（全屏）
            screenshot = pyautogui.screenshot()
        
        # 轉換為 PIL Image
        img = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # 🎯 標記搜尋區域（黃色虛線矩形）
        if region:
            region_left, region_top, region_width, region_height = region
            region_right = region_left + region_width
            region_bottom = region_top + region_height
            
            # 繪製黃色虛線矩形框標記搜尋區域
            dash_length = 10
            gap_length = 5
            
            # 上邊界（虛線）
            x_pos = region_left
            while x_pos < region_right:
                draw.line([(x_pos, region_top), (min(x_pos + dash_length, region_right), region_top)], fill="yellow", width=3)
                x_pos += dash_length + gap_length
            
            # 下邊界（虛線）
            x_pos = region_left
            while x_pos < region_right:
                draw.line([(x_pos, region_bottom), (min(x_pos + dash_length, region_right), region_bottom)], fill="yellow", width=3)
                x_pos += dash_length + gap_length
            
            # 左邊界（虛線）
            y_pos = region_top
            while y_pos < region_bottom:
                draw.line([(region_left, y_pos), (region_left, min(y_pos + dash_length, region_bottom))], fill="yellow", width=3)
                y_pos += dash_length + gap_length
            
            # 右邊界（虛線）
            y_pos = region_top
            while y_pos < region_bottom:
                draw.line([(region_right, y_pos), (region_right, min(y_pos + dash_length, region_bottom))], fill="yellow", width=3)
                y_pos += dash_length + gap_length
            
            # 搜尋區域信息文字
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            region_info = f"Search Region: ({region_left}, {region_top}, {region_width}, {region_height})"
            draw.text((region_left + 5, region_top - 25), region_info, fill="yellow", font=font)
        
        # 🎯 獲取 DPI 縮放比例（修復高 DPI 螢幕下的座標偏移問題）
        # Windows 的 DPI 縮放會導致截圖的物理尺寸與 pyautogui 的邏輯尺寸不一致
        # 例如：150% DPI 縮放時，1920x1080 邏輯解析度對應 2880x1620 物理解析度
        # 重要：縮放比例只用於繪圖，不應用於點擊座標（pyautogui 會自動處理 OS 縮放）
        img_width, img_height = img.size  # 截圖的物理尺寸（實際像素）
        screen_w, screen_h = pyautogui.size()  # 螢幕的邏輯尺寸（pyautogui 座標系）
        scale_x = img_width / screen_w  # X 軸縮放比例
        scale_y = img_height / screen_h  # Y 軸縮放比例
        
        # 🎯 標記 VLM 邊界框（綠色實線矩形）- 優先繪製，確保在紅色框下方
        if vlm_box:
            box_xmin, box_ymin, box_xmax, box_ymax = vlm_box
            
            # 🎯 檢查是否為正規化座標（0.0-1.0），如果是則轉換為像素座標
            is_normalized = all(0.0 <= v <= 1.0 for v in vlm_box)
            
            if is_normalized:
                # 正規化座標：先轉換為邏輯像素座標，再應用 DPI 縮放（用於繪圖）
                box_xmin = int(box_xmin * screen_w * scale_x)
                box_ymin = int(box_ymin * screen_h * scale_y)
                box_xmax = int(box_xmax * screen_w * scale_x)
                box_ymax = int(box_ymax * screen_h * scale_y)
                self.logger.debug(f"[VLM_BOX] 檢測到正規化座標，轉換為像素座標（已應用 DPI 縮放）: ({box_xmin}, {box_ymin}, {box_xmax}, {box_ymax})")
            else:
                # 絕對座標：直接應用 DPI 縮放（因為座標來自 pyautogui 邏輯座標系，需要轉換為截圖物理座標系）
                box_xmin = int(box_xmin * scale_x)
                box_ymin = int(box_ymin * scale_y)
                box_xmax = int(box_xmax * scale_x)
                box_ymax = int(box_ymax * scale_y)
                self.logger.debug(f"[VLM_BOX] 絕對座標已應用 DPI 縮放: scale=({scale_x:.2f}, {scale_y:.2f}), 座標=({box_xmin}, {box_ymin}, {box_xmax}, {box_ymax})")
            
            vlm_rect = [box_xmin, box_ymin, box_xmax, box_ymax]
            draw.rectangle(vlm_rect, outline='green', width=2)
            
            # 標註 VLM 邊界框信息（在框的下方，避免與其他標籤重疊）
            try:
                vlm_font = ImageFont.truetype("arial.ttf", 12)
            except:
                vlm_font = ImageFont.load_default()
            
            vlm_label = f"VLM Box: ({box_xmin}, {box_ymin}, {box_xmax}, {box_ymax})"
            # 在框的下方顯示標籤
            label_y = box_ymax + 5
            draw.text((box_xmin, label_y), vlm_label, fill='green', font=vlm_font)
        
        # 🎯 標記辨識到的物件（紅色實線矩形）- 應用 DPI 縮放
        # 重要：(x, y) 是物件的中心點座標，需要轉換為左上角座標才能正確繪製矩形框
        # 
        # 座標轉換邏輯：
        # 1. (x, y) 是物件中心點的邏輯座標（pyautogui 座標系）
        # 2. (width, height) 是物件的寬高（邏輯座標）
        # 3. 左上角座標 = 中心點 - (寬度/2, 高度/2)
        # 4. 將邏輯座標轉換為物理像素座標（應用 DPI 縮放）用於繪圖
        
        # 計算左上角座標（邏輯座標）
        top_left_x, top_left_y = Toolkit.calculate_top_left_from_center(
            center=(x, y),
            width=width,
            height=height
        )
        
        # 轉換為物理像素座標（應用 DPI 縮放）
        rect_x = int(top_left_x * scale_x)
        rect_y = int(top_left_y * scale_y)
        rect_width = int(width * scale_x)
        rect_height = int(height * scale_y)
        rect = [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height]
        draw.rectangle(rect, outline='red', width=3)
        
        # 標註物件名稱
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # 在框的上方顯示名稱（使用縮放後的座標）
        text_bbox = draw.textbbox((rect_x, rect_y - 20), item_name, font=font)
        draw.rectangle(
            [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
            fill='red'
        )
        draw.text((rect_x, rect_y - 20), item_name, fill='white', font=font)
        
        # 標記物件座標（顯示原始邏輯座標，但使用縮放後的繪製位置）
        coord_text = f"({x}, {y})"
        draw.text((rect_x + rect_width + 5, rect_y), coord_text, fill='red', font=font)
        
        # 🎯 標記實際點擊座標（綠色實心圓點和十字準星）
        # 計算點擊座標（即實際執行 pyautogui.click 的位置，即傳入的 x, y）
        # 🎯 重要：x, y 是邏輯座標（pyautogui 使用的座標），需要在物理截圖上繪製時應用縮放
        # 獲取 DPI 縮放比例（如果尚未計算）
        if 'scale_x' not in locals() or 'scale_y' not in locals():
            img_width, img_height = img.size
            screen_w, screen_h = pyautogui.size()
            scale_x = img_width / screen_w
            scale_y = img_height / screen_h
        
        # 🎯 繪圖座標：將邏輯座標轉換為物理像素座標（僅用於繪圖）
        draw_x = int(x * scale_x)
        draw_y = int(y * scale_y)
        
        # 🎯 繪製綠色十字準星（兩條長度為 30 像素的綠色線段，交叉點位於 (draw_x, draw_y)）
        cross_size = 15  # 半長度 15 像素，總長度 30 像素
        # 水平線（長度 30px，從左到右）
        draw.line(
            [(draw_x - cross_size, draw_y), (draw_x + cross_size, draw_y)],
            fill='green',
            width=4
        )
        # 垂直線（長度 30px，從上到下）
        draw.line(
            [(draw_x, draw_y - cross_size), (draw_x, draw_y + cross_size)],
            fill='green',
            width=4
        )
        
        # 🎯 繪製綠色實心圓點（直徑 10 像素，半徑 5 像素）
        # 繪製在十字準星上方，確保清晰可見
        circle_radius = 5  # 半徑 5 像素，直徑 10 像素
        draw.ellipse(
            [
                draw_x - circle_radius,
                draw_y - circle_radius,
                draw_x + circle_radius,
                draw_y + circle_radius
            ],
            fill='green',  # 實心填充
            outline='darkgreen',  # 深綠色邊框，增強對比度
            width=2
        )
        
        # 🎯 加入座標文字：在十字準星旁，用綠色底、白色字標註 Click: (x, y)
        # 注意：顯示原始邏輯座標 (x, y)，但繪製位置使用縮放後的座標 (draw_x, draw_y)
        # 這樣可以清楚看到實際點擊的邏輯座標，同時在截圖上正確標記位置
        click_text = f"Click: ({x}, {y})"
        try:
            click_font = ImageFont.truetype("arial.ttf", 14)
        except:
            click_font = ImageFont.load_default()
        
        # 計算文字位置（在十字準星右側，稍微向上偏移）
        text_x = draw_x + cross_size + 5
        text_y = draw_y - 15
        
        # 計算文字邊界框
        text_bbox = draw.textbbox((text_x, text_y), click_text, font=click_font)
        
        # 繪製綠色背景矩形（綠色底）
        draw.rectangle(
            [text_bbox[0] - 3, text_bbox[1] - 3, text_bbox[2] + 3, text_bbox[3] + 3],
            fill='green',
            outline='darkgreen',
            width=1
        )
        
        # 繪製白色文字（白色字）
        draw.text((text_x, text_y), click_text, fill='white', font=click_font)
        
        # 保存截圖
        filename = f"recognition_{step_no:05d}_{int(time.time())}.png"
        screenshot_path = os.path.join(self.screenshot_dir, filename)
        img.save(screenshot_path)
        
        return screenshot_path
    
    def add_click_screenshot(
        self,
        click_x: int,
        click_y: int,
        click_action: str = "單擊"
    ):
        """
        添加點擊前的截圖（標記點擊位置）
        
        :param click_x: 點擊 X 座標
        :param click_y: 點擊 Y 座標
        :param click_action: 點擊動作（單擊、雙擊、右鍵）
        """
        try:
            # 🎯 根據是否有 mobile_driver 決定截圖方式
            if self.mobile_driver:
                # Mobile 測試：使用 Appium 截圖
                try:
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    # 使用 Appium 的 save_screenshot 方法截圖（只截取手機模擬器）
                    self.mobile_driver.save_screenshot(temp_path)
                    
                    # 讀取截圖並轉換為 PIL Image
                    from PIL import Image
                    screenshot = Image.open(temp_path)
                    
                    # 刪除臨時文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                except Exception as e:
                    # 如果 Appium 截圖失敗，回退到全屏截圖並記錄警告
                    import logging
                    logger = logging.getLogger(self.__class__.__name__)
                    logger.warning(f"[REPORTER] Mobile 截圖失敗，回退到全屏截圖: {e}")
                    screenshot = pyautogui.screenshot()
            else:
                # Desktop/Web 測試：使用 pyautogui 截圖（全屏）
                screenshot = pyautogui.screenshot()
            img = screenshot.convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 🎯 獲取 DPI 縮放比例
            img_width, img_height = img.size
            screen_w, screen_h = pyautogui.size()
            scale_x = img_width / screen_w
            scale_y = img_height / screen_h
            
            # 🎯 標記點擊位置（綠色實心圓點和十字準星）
            draw_x = int(click_x * scale_x)
            draw_y = int(click_y * scale_y)
            
            # 繪製十字準星（綠色）
            crosshair_size = 20
            draw.line([(draw_x - crosshair_size, draw_y), (draw_x + crosshair_size, draw_y)], fill='green', width=3)
            draw.line([(draw_x, draw_y - crosshair_size), (draw_x, draw_y + crosshair_size)], fill='green', width=3)
            
            # 繪製實心圓點（綠色）
            circle_radius = 8
            draw.ellipse(
                [draw_x - circle_radius, draw_y - circle_radius, draw_x + circle_radius, draw_y + circle_radius],
                fill='green',
                outline='green',
                width=2
            )
            
            # 標註點擊信息
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            click_label = f"Click: ({click_x}, {click_y}) [{click_action}]"
            # 在點擊位置上方顯示標籤
            label_y = draw_y - 30
            text_bbox = draw.textbbox((draw_x, label_y), click_label, font=font)
            draw.rectangle(
                [text_bbox[0] - 3, text_bbox[1] - 3, text_bbox[2] + 3, text_bbox[3] + 3],
                fill='green',
                outline='green'
            )
            draw.text((draw_x, label_y), click_label, fill='white', font=font)
            
            # 保存截圖
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            screenshot_filename = f"click_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_filename)
            img.save(screenshot_path)
            
            # 記錄到 recognition_screenshots（用於報告）
            self.recognition_screenshots.append({
                "timestamp": datetime.now().isoformat(),
                "item_name": f"點擊位置 [{click_action}]",
                "x": click_x,
                "y": click_y,
                "width": 20,
                "height": 20,
                "method": "座標點擊",
                "screenshot_path": screenshot_path
            })
            
        except Exception as e:
            self.logger.debug(f"添加點擊截圖失敗: {e}")
    
    def add_recognition_screenshot(
        self,
        item_name: str,
        x: int,
        y: int,
        width: int = 50,
        height: int = 50,
        method: str = "OK Script",
        region: Tuple[int, int, int, int] = None,
        vlm_box: Tuple[int, int, int, int] = None,  # VLM 邊界框 (xmin, ymin, xmax, ymax)
        vlm_coord: Tuple[int, int] = None  # VLM 識別的中心點座標 (x, y)
    ):
        """添加辨識成功的截圖（在 smart_click 成功時調用）。
        
        此方法會：
        1. 截圖並標註物件
        2. 如果提供了 VLM 座標，進行座標驗證並記錄到座標庫
        
        Args:
            item_name: 辨識到的物件名稱
            x: 物件中心點 X 座標（圖像辨識結果）
            y: 物件中心點 Y 座標（圖像辨識結果）
            width: 物件寬度
            height: 物件高度
            method: 辨識方法（OK Script, OCR, VLM 等）
            region: 搜尋區域 (left, top, width, height)，用於在截圖上標記搜尋範圍
            vlm_box: VLM 邊界框 (xmin, ymin, xmax, ymax)
            vlm_coord: VLM 識別的中心點座標 (x, y)，用於與圖像辨識座標比對
        """
        # 🎯 VLM 座標驗證與數據持久化
        # 如果提供了 VLM 座標，進行歐幾里得距離驗證
        if vlm_coord and method != "VLM":  # 只在非 VLM 方法時進行比對
            cv_coord = (x, y)  # 圖像辨識的中心點座標
            
            try:
                # 執行座標驗證並保存至座標庫
                comparison = self.coordinate_validator.validate_and_save(
                    element_name=item_name,
                    cv_coord=cv_coord,
                    vlm_coord=vlm_coord
                )
                
                # 在日誌中記錄驗證結果
                if comparison.is_discrepancy:
                    self.logger.warning(
                        f"[VLM_DISCREPANCY] 元素 '{item_name}' 座標差異: "
                        f"CV={cv_coord}, VLM={vlm_coord}, "
                        f"距離={comparison.distance:.2f}px (閾值={comparison.threshold}px)"
                    )
                else:
                    self.logger.info(
                        f"[VLM_VALIDATION_OK] 元素 '{item_name}' 座標驗證通過: "
                        f"距離={comparison.distance:.2f}px"
                    )
            except Exception as e:
                self.logger.error(f"[VLM_VALIDATION_ERROR] 座標驗證失敗: {e}")
        
        # 截圖並標註物件（使用特殊的步驟編號，避免與測試步驟衝突）
        screenshot_path = self._take_recognition_screenshot_with_region(
            step_no=10000 + len(self.recognition_screenshots) + 1,  # 使用大數字避免衝突
            item_name=f"{item_name} ({method})",
            x=x,
            y=y,
            width=width,
            height=height,
            region=region,
            vlm_box=vlm_box  # 傳入 VLM 邊界框
        )
        
        # 重命名檔案為 recognition_xxx.png
        import shutil
        rec_filename = f"recognition_{len(self.recognition_screenshots) + 1:03d}_{int(time.time())}.png"
        rec_screenshot_path = os.path.join(self.screenshot_dir, rec_filename)
        try:
            shutil.move(screenshot_path, rec_screenshot_path)
            screenshot_path = rec_screenshot_path
        except Exception as e:
            # 如果重命名失敗，使用原來的路徑
            pass
        
        # 記錄截圖資訊
        self.recognition_screenshots.append({
            "item_name": item_name,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "method": method,
            "screenshot_path": screenshot_path,
            "timestamp": datetime.now().isoformat(),
            "region": region,  # 記錄搜尋區域
            "vlm_coord": vlm_coord  # 記錄 VLM 座標（如果有）
        })
    
    def finish(self, overall_status: str, log_file_path: str = None):
        """
        完成報告生成
        
        :param overall_status: 整體狀態 ('pass', 'fail')
        :param log_file_path: 執行 log 檔案路徑（可選）
        """
        self.end_time = datetime.now()
        self.overall_status = overall_status
        
        # 只複製 Terminal log 檔案到報告目錄（不複製 automation.log）
        if log_file_path and os.path.exists(log_file_path):
            try:
                # 統一命名為 terminal_output.log
                report_log_path = os.path.join(self.report_dir, "terminal_output.log")
                
                # 複製並清理 NULL 字節（Windows subprocess 可能產生的緩衝區殘留）
                try:
                    with open(log_file_path, 'rb') as src:
                        content = src.read()
                    
                    # 移除 NULL 字節 (\x00)
                    clean_content = content.replace(b'\x00', b'')
                    
                    with open(report_log_path, 'wb') as dst:
                        dst.write(clean_content)
                    
                    print(f"[REPORT] 清理了 {len(content) - len(clean_content)} 個 NULL 字節")
                except Exception as copy_err:
                    print(f"[WARNING] 清理 log 失敗，使用原始複製: {copy_err}")
                    import shutil
                    shutil.copy2(log_file_path, report_log_path)
                
                self.log_file_path = report_log_path
                
                # 驗證複製是否成功
                if os.path.exists(report_log_path):
                    file_size = os.path.getsize(report_log_path)
                    print(f"[REPORT] Terminal log 已複製到報告目錄: {report_log_path} ({file_size} bytes)")
                else:
                    print(f"[WARNING] Terminal log 複製後文件不存在: {report_log_path}")
                    self.log_file_path = None
            except Exception as e:
                print(f"[WARNING] 複製 Terminal log 檔案失敗: {e}")
                import traceback
                traceback.print_exc()
                self.log_file_path = None
        else:
            if log_file_path:
                print(f"[WARNING] Terminal log 檔案不存在: {log_file_path}")
            self.log_file_path = None
        
        # 生成 HTML 報告
        html_path = os.path.join(self.report_dir, "report.html")
        self._generate_html_report(html_path)
        
        return html_path
    
    def _generate_html_report(self, output_path: str):
        """生成 HTML 格式的測試報告（類似 UFT 格式）"""
        
        duration = (self.end_time - self.start_time).total_seconds()
        passed_steps = sum(1 for s in self.steps if s['status'] == 'pass')
        failed_steps = sum(1 for s in self.steps if s['status'] == 'fail')
        warning_steps = sum(1 for s in self.steps if s['status'] == 'warning')
        
        # 取得相對路徑的截圖
        def get_relative_screenshot_path(absolute_path):
            return os.path.relpath(absolute_path, os.path.dirname(output_path)).replace("\\", "/")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>測試報告 - {self.test_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header-info {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            font-weight: normal;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .summary-card.passed .value {{ color: #4CAF50; }}
        .summary-card.failed .value {{ color: #f44336; }}
        .summary-card.warning .value {{ color: #FF9800; }}
        .summary-card.total .value {{ color: #2196F3; }}
        .steps {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .step {{
            border-bottom: 1px solid #e0e0e0;
            padding: 20px;
        }}
        .step:last-child {{
            border-bottom: none;
        }}
        .step-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }}
        .step-number {{
            background: #2196F3;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}
        .step-name {{
            font-size: 18px;
            font-weight: bold;
            flex: 1;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-pass {{
            background: #4CAF50;
            color: white;
        }}
        .status-fail {{
            background: #f44336;
            color: white;
        }}
        .status-warning {{
            background: #FF9800;
            color: white;
        }}
        .step-message {{
            color: #666;
            margin: 10px 0;
        }}
        .step-screenshot {{
            margin-top: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .step-screenshot img {{
            width: 100%;
            height: auto;
            display: block;
            transition: opacity 0.3s;
        }}
        .step-screenshot img:hover {{
            opacity: 0.8;
        }}
        .step-screenshot a {{
            display: block;
            text-decoration: none;
        }}
        .verification-items {{
            margin-top: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        .verification-items h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
        }}
        .verification-item {{
            display: inline-block;
            background: #e3f2fd;
            padding: 5px 10px;
            margin: 5px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .timestamp {{
            color: #999;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 測試報告</h1>
        <div>測試案例: {self.test_name}</div>
        <div class="header-info">
            <div>開始時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div>結束時間: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div>執行時長: {duration:.2f} 秒</div>
        </div>
    </div>
    
    <div class="summary">
        <div class="summary-card passed">
            <h3>通過步驟</h3>
            <div class="value">{passed_steps}</div>
        </div>
        <div class="summary-card failed">
            <h3>失敗步驟</h3>
            <div class="value">{failed_steps}</div>
        </div>
        <div class="summary-card warning">
            <h3>警告步驟</h3>
            <div class="value">{warning_steps}</div>
        </div>
        <div class="summary-card total">
            <h3>總步驟數</h3>
            <div class="value">{len(self.steps)}</div>
        </div>
    </div>
    
    <div class="steps">
        <h2 style="padding: 20px; margin: 0; border-bottom: 2px solid #667eea;">測試步驟詳情</h2>
"""
        
        # 生成每個步驟的 HTML
        for step in self.steps:
            status_class = f"status-{step['status']}"
            screenshot_rel_path = get_relative_screenshot_path(step['screenshot_path'])
            
            verification_html = ""
            if step['verification_items']:
                verification_html = '<div class="verification-items"><h4>檢核物件：</h4>'
                for item in step['verification_items']:
                    verification_html += f'<span class="verification-item">{item.get("name", "Unknown")}</span>'
                verification_html += '</div>'
            
            html_content += f"""
        <div class="step">
            <div class="step-header">
                <div class="step-number">{step['step_no']}</div>
                <div class="step-name">{step['step_name']}</div>
                <div class="status-badge {status_class}">{step['status'].upper()}</div>
            </div>
            <div class="step-message">{step['message']}</div>
            {verification_html}
            <div class="step-screenshot">
                <img src="{screenshot_rel_path}" alt="步驟 {step['step_no']} 截圖">
            </div>
            <div class="timestamp">執行時間: {step['timestamp']}</div>
        </div>
"""
        
        html_content += """
    </div>
"""
        
        # 添加辨識截圖區域（如果有的話）
        if self.recognition_screenshots:
            html_content += """
    <div class="steps" style="margin-top: 20px;">
        <h2 style="padding: 20px; margin: 0; border-bottom: 2px solid #667eea;">物件辨識截圖</h2>
"""
            for idx, rec_screenshot in enumerate(self.recognition_screenshots, 1):
                screenshot_rel_path = get_relative_screenshot_path(rec_screenshot['screenshot_path'])
                
                # 辨識方法的中文顯示
                method_display = {
                    "OK Script": "OK Script / OpenCV",
                    "pyautogui": "PyAutoGUI 圖片辨識",
                    "OCR": "OCR 文字辨識",
                    "VLM": "VLM (視覺語言模型)",
                    "Coordinate": "座標保底"
                }.get(rec_screenshot['method'], rec_screenshot['method'])
                
                # 格式化時間戳
                try:
                    timestamp_obj = datetime.fromisoformat(rec_screenshot['timestamp'])
                    time_display = timestamp_obj.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_display = rec_screenshot['timestamp']
                
                html_content += f"""
        <div class="step">
            <div class="step-header">
                <div class="step-number">{idx}</div>
                <div class="step-name">{rec_screenshot['item_name']}</div>
                <div class="status-badge status-pass">辨識成功</div>
            </div>
            <div class="step-message">
                <strong>辨識方式：</strong>{method_display}<br>
                <strong>物件位置：</strong>({rec_screenshot['x']}, {rec_screenshot['y']}) | 
                <strong>物件尺寸：</strong>{rec_screenshot['width']}x{rec_screenshot['height']} | 
                <strong>辨識時間：</strong>{time_display}
            </div>
            <div class="step-screenshot">
                <a href="{screenshot_rel_path}" target="_blank" title="點擊查看大圖">
                    <img src="{screenshot_rel_path}" alt="辨識截圖 {idx}" style="cursor: pointer;">
                </a>
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{screenshot_rel_path}" target="_blank" download="{os.path.basename(rec_screenshot['screenshot_path'])}" 
                       style="color: #2196F3; text-decoration: none; font-size: 12px;">
                        📥 下載截圖 ({os.path.basename(rec_screenshot['screenshot_path'])})
                    </a>
                </div>
            </div>
        </div>
"""
            html_content += """
    </div>
"""
        
        # 添加 log 檔案連結（如果有的話）
        if hasattr(self, 'log_file_path') and self.log_file_path and os.path.exists(self.log_file_path):
            log_rel_path = os.path.relpath(self.log_file_path, os.path.dirname(output_path)).replace("\\", "/")
            html_content += f"""
    <div class="steps" style="margin-top: 20px;">
        <h2 style="padding: 20px; margin: 0; border-bottom: 2px solid #667eea;">執行日誌</h2>
        <div class="step">
            <div class="step-message">
                <a href="{log_rel_path}" target="_blank" style="color: #2196F3; text-decoration: none; font-weight: bold;">
                    📄 查看完整執行日誌 ({os.path.basename(self.log_file_path)})
                </a>
            </div>
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        # 寫入 HTML 檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
