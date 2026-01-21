# -*- coding: utf-8 -*-
"""
測試報告生成模組

功能：
1. 生成 HTML 格式的測試報告（類似 UFT 報告格式）
2. 記錄每個步驟的檢核結果和截圖
3. 在截圖中標出檢核的物件（紅框）
"""

import os
import time
import pyautogui
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from config import EnvConfig


class TestReporter:
    """測試報告生成器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.end_time = None
        self.steps: List[Dict] = []
        
        # 建立報告目錄結構
        self.report_dir = self._create_report_directory()
        
        # 截圖目錄
        self.screenshot_dir = os.path.join(self.report_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 用於記錄自動截圖（每次辨識成功時保存）
        self.recognition_screenshots: List[Dict] = []
    
    def _create_report_directory(self) -> str:
        """
        建立報告目錄結構
        
        report/
        └── <TestName>/
            └── <YYYY-MM-DD_HH-MM-SS>/
        """
        project_root = EnvConfig.PROJECT_ROOT
        report_base = os.path.join(project_root, "report")
        
        # 使用測試名稱建立資料夾（清理特殊字元）
        safe_test_name = self.test_name.replace("/", "_").replace("\\", "_")
        test_dir = os.path.join(report_base, safe_test_name)
        
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
        # 截取全屏
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
        region: Tuple[int, int, int, int] = None
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
        # 截取全屏
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
        
        # 🎯 標記辨識到的物件（紅色實線矩形）
        rect = [x, y, x + width, y + height]
        draw.rectangle(rect, outline='red', width=3)
        
        # 標註物件名稱
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # 在框的上方顯示名稱
        text_bbox = draw.textbbox((x, y - 20), item_name, font=font)
        draw.rectangle(
            [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
            fill='red'
        )
        draw.text((x, y - 20), item_name, fill='white', font=font)
        
        # 標記物件座標
        coord_text = f"({x}, {y})"
        draw.text((x + width + 5, y), coord_text, fill='red', font=font)
        
        # 🎯 標記實際點擊座標（綠色實心圓點和十字準星）
        # 計算點擊座標（即實際執行 pyautogui.click 的位置，即傳入的 x, y）
        click_x = x
        click_y = y
        
        # 🎯 繪製綠色十字準星（兩條長度為 30 像素的綠色線段，交叉點位於 (x, y)）
        cross_size = 15  # 半長度 15 像素，總長度 30 像素
        # 水平線（長度 30px，從左到右）
        draw.line(
            [(click_x - cross_size, click_y), (click_x + cross_size, click_y)],
            fill='green',
            width=4
        )
        # 垂直線（長度 30px，從上到下）
        draw.line(
            [(click_x, click_y - cross_size), (click_x, click_y + cross_size)],
            fill='green',
            width=4
        )
        
        # 🎯 繪製綠色實心圓點（直徑 10 像素，半徑 5 像素）
        # 繪製在十字準星上方，確保清晰可見
        circle_radius = 5  # 半徑 5 像素，直徑 10 像素
        draw.ellipse(
            [
                click_x - circle_radius,
                click_y - circle_radius,
                click_x + circle_radius,
                click_y + circle_radius
            ],
            fill='green',  # 實心填充
            outline='darkgreen',  # 深綠色邊框，增強對比度
            width=2
        )
        
        # 🎯 加入座標文字：在十字準星旁，用綠色底、白色字標註 Click: (x, y)
        click_text = f"Click: ({click_x}, {click_y})"
        try:
            click_font = ImageFont.truetype("arial.ttf", 14)
        except:
            click_font = ImageFont.load_default()
        
        # 計算文字位置（在十字準星右側，稍微向上偏移）
        text_x = click_x + cross_size + 5
        text_y = click_y - 15
        
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
    
    def add_recognition_screenshot(
        self,
        item_name: str,
        x: int,
        y: int,
        width: int = 50,
        height: int = 50,
        method: str = "OK Script",
        region: Tuple[int, int, int, int] = None
    ):
        """
        添加辨識成功的截圖（在 smart_click 成功時調用）
        
        :param item_name: 辨識到的物件名稱
        :param x: 物件 X 座標
        :param y: 物件 Y 座標
        :param width: 物件寬度
        :param height: 物件高度
        :param method: 辨識方法（OK Script, OCR, VLM 等）
        :param region: 搜尋區域 (left, top, width, height)，用於在截圖上標記搜尋範圍
        """
        # 截圖並標註物件（使用特殊的步驟編號，避免與測試步驟衝突）
        screenshot_path = self._take_recognition_screenshot_with_region(
            step_no=10000 + len(self.recognition_screenshots) + 1,  # 使用大數字避免衝突
            item_name=f"{item_name} ({method})",
            x=x,
            y=y,
            width=width,
            height=height,
            region=region
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
            "region": region  # 記錄搜尋區域
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
                import shutil
                # 統一命名為 terminal_output.log
                report_log_path = os.path.join(self.report_dir, "terminal_output.log")
                
                # 複製文件
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
