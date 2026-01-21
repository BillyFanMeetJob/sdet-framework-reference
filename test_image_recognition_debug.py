# -*- coding: utf-8 -*-
"""
圖像辨識座標調試工具

功能：
1. 測試圖片辨識返回的座標是左上角還是中心點
2. 在截圖上標記辨識區域和座標
3. 對比不同辨識方法的座標差異
"""

import os
import sys
import pyautogui
import pygetwindow as gw
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import EnvConfig
import time

# 設置輸出編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_image_recognition(image_path, region=None):
    """
    測試圖片辨識並生成調試截圖
    
    :param image_path: 圖片路徑
    :param region: 搜尋區域 (left, top, width, height)
    """
    time.sleep(2)
    print("=" * 80)
    print(f"圖像辨識座標調試工具")
    print("=" * 80)
    
    if not os.path.exists(image_path):
        print(f"❌ 圖片不存在: {image_path}")
        return
    
    print(f"\n📸 測試圖片: {image_path}")
    print(f"🔍 搜尋區域: {region}")
    
    # 讀取圖片尺寸
    try:
        template_img = Image.open(image_path)
        template_width, template_height = template_img.size
        print(f"📏 圖片尺寸: {template_width}x{template_height}")
    except Exception as e:
        print(f"❌ 讀取圖片失敗: {e}")
        return
    
    # 方法 1: OK Script / OpenCV
    print("\n" + "=" * 80)
    print("方法 1: OK Script / OpenCV 辨識")
    print("=" * 80)
    
    ok_script_result = None
    try:
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        result = recognizer.locate_on_screen(image_path, region=region, confidence=0.7)
        
        if result and result.success:
            ok_script_result = {
                'x': result.x,
                'y': result.y,
                'width': result.width if hasattr(result, 'width') and result.width > 0 else template_width,
                'height': result.height if hasattr(result, 'height') and result.height > 0 else template_height,
                'method': result.method if hasattr(result, 'method') else 'ok_script',
                'confidence': result.confidence
            }
            print(f"✅ OK Script 辨識成功")
            print(f"   座標: ({ok_script_result['x']}, {ok_script_result['y']})")
            print(f"   尺寸: {ok_script_result['width']}x{ok_script_result['height']}")
            print(f"   方法: {ok_script_result['method']}")
            print(f"   信心度: {ok_script_result['confidence']:.2f}")
            
            # 計算可能的左上角座標（如果返回的是中心點）
            center_x = ok_script_result['x']
            center_y = ok_script_result['y']
            possible_left = center_x - ok_script_result['width'] // 2
            possible_top = center_y - ok_script_result['height'] // 2
            print(f"   如果返回的是中心點，左上角可能是: ({possible_left}, {possible_top})")
        else:
            print(f"❌ OK Script 辨識失敗")
    except Exception as e:
        print(f"❌ OK Script 辨識異常: {e}")
        import traceback
        traceback.print_exc()
    
    # 方法 2: PyAutoGUI
    print("\n" + "=" * 80)
    print("方法 2: PyAutoGUI 辨識")
    print("=" * 80)
    
    pyautogui_result = None
    try:
        loc = pyautogui.locateOnScreen(image_path, confidence=0.7, region=region)
        if loc:
            center = pyautogui.center(loc)
            pyautogui_result = {
                'x': center.x,
                'y': center.y,
                'left': loc.left,
                'top': loc.top,
                'width': loc.width,
                'height': loc.height,
                'method': 'pyautogui'
            }
            print(f"✅ PyAutoGUI 辨識成功")
            print(f"   中心點座標: ({pyautogui_result['x']}, {pyautogui_result['y']})")
            print(f"   左上角座標: ({pyautogui_result['left']}, {pyautogui_result['top']})")
            print(f"   尺寸: {pyautogui_result['width']}x{pyautogui_result['height']}")
        else:
            print(f"❌ PyAutoGUI 辨識失敗")
    except Exception as e:
        print(f"❌ PyAutoGUI 辨識異常: {e}")
    
    # 生成調試截圖
    print("\n" + "=" * 80)
    print("生成調試截圖")
    print("=" * 80)
    
    try:
        # 截取全屏
        screenshot = pyautogui.screenshot()
        img = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # 嘗試加載字體
        try:
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # 標記搜尋區域（如果提供）
        if region:
            region_left, region_top, region_width, region_height = region
            region_right = region_left + region_width
            region_bottom = region_top + region_height
            
            # 繪製黃色虛線矩形框
            dash_length = 10
            gap_length = 5
            
            # 上邊界
            x_pos = region_left
            while x_pos < region_right:
                draw.line([(x_pos, region_top), (min(x_pos + dash_length, region_right), region_top)], fill="yellow", width=3)
                x_pos += dash_length + gap_length
            
            # 下邊界
            x_pos = region_left
            while x_pos < region_right:
                draw.line([(x_pos, region_bottom), (min(x_pos + dash_length, region_right), region_bottom)], fill="yellow", width=3)
                x_pos += dash_length + gap_length
            
            # 左邊界
            y_pos = region_top
            while y_pos < region_bottom:
                draw.line([(region_left, y_pos), (region_left, min(y_pos + dash_length, region_bottom))], fill="yellow", width=3)
                y_pos += dash_length + gap_length
            
            # 右邊界
            y_pos = region_top
            while y_pos < region_bottom:
                draw.line([(region_right, y_pos), (region_right, min(y_pos + dash_length, region_bottom))], fill="yellow", width=3)
                y_pos += dash_length + gap_length
            
            # 標記搜尋區域信息
            region_info = f"Search Region: ({region_left}, {region_top}, {region_width}, {region_height})"
            draw.text((region_left + 5, region_top - 25), region_info, fill="yellow", font=font_small)
        
        # 標記 OK Script 結果
        if ok_script_result:
            x = ok_script_result['x']
            y = ok_script_result['y']
            width = ok_script_result['width']
            height = ok_script_result['height']
            
            # 繪製紅色實線矩形（假設返回的是左上角）
            rect_left = x
            rect_top = y
            rect_right = x + width
            rect_bottom = y + height
            draw.rectangle([(rect_left, rect_top), (rect_right, rect_bottom)], outline='red', width=3)
            
            # 標記座標
            label = f"OK Script: ({x}, {y}) [左上角假設]"
            draw.text((rect_left + 5, rect_top - 20), label, fill='red', font=font_small)
            
            # 繪製中心點（如果返回的是中心點）
            center_x = x
            center_y = y
            possible_left = center_x - width // 2
            possible_top = center_y - height // 2
            possible_right = possible_left + width
            possible_bottom = possible_top + height
            
            # 繪製藍色虛線矩形（中心點假設）
            dash_length = 8
            gap_length = 4
            x_pos = possible_left
            while x_pos < possible_right:
                draw.line([(x_pos, possible_top), (min(x_pos + dash_length, possible_right), possible_top)], fill="blue", width=2)
                x_pos += dash_length + gap_length
            x_pos = possible_left
            while x_pos < possible_right:
                draw.line([(x_pos, possible_bottom), (min(x_pos + dash_length, possible_right), possible_bottom)], fill="blue", width=2)
                x_pos += dash_length + gap_length
            y_pos = possible_top
            while y_pos < possible_bottom:
                draw.line([(possible_left, y_pos), (possible_left, min(y_pos + dash_length, possible_bottom))], fill="blue", width=2)
                y_pos += dash_length + gap_length
            y_pos = possible_top
            while y_pos < possible_bottom:
                draw.line([(possible_right, y_pos), (possible_right, min(y_pos + dash_length, possible_bottom))], fill="blue", width=2)
                y_pos += dash_length + gap_length
            
            label2 = f"OK Script: ({x}, {y}) [中心點假設] -> 左上角({possible_left}, {possible_top})"
            draw.text((possible_left + 5, possible_top - 40), label2, fill='blue', font=font_small)
            
            # 標記中心點
            draw.ellipse([(center_x - 5, center_y - 5), (center_x + 5, center_y + 5)], outline='red', width=2)
            draw.line([(center_x - 15, center_y), (center_x + 15, center_y)], fill='red', width=2)
            draw.line([(center_x, center_y - 15), (center_x, center_y + 15)], fill='red', width=2)
        
        # 標記 PyAutoGUI 結果
        if pyautogui_result:
            # 中心點
            center_x = pyautogui_result['x']
            center_y = pyautogui_result['y']
            # 左上角
            left = pyautogui_result['left']
            top = pyautogui_result['top']
            width = pyautogui_result['width']
            height = pyautogui_result['height']
            
            # 繪製綠色實線矩形（PyAutoGUI 返回的是左上角）
            draw.rectangle([(left, top), (left + width, top + height)], outline='green', width=3)
            
            # 標記中心點
            draw.ellipse([(center_x - 5, center_y - 5), (center_x + 5, center_y + 5)], outline='green', width=2)
            draw.line([(center_x - 15, center_y), (center_x + 15, center_y)], fill='green', width=2)
            draw.line([(center_x, center_y - 15), (center_x, center_y + 15)], fill='green', width=2)
            
            # 標記座標
            label = f"PyAutoGUI: 中心({center_x}, {center_y}), 左上({left}, {top})"
            draw.text((left + 5, top - 20), label, fill='green', font=font_small)
        
        # 保存截圖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = os.path.basename(image_path).replace('.png', '')
        debug_dir = os.path.join(EnvConfig.PROJECT_ROOT, "logs", "image_recognition_debug")
        os.makedirs(debug_dir, exist_ok=True)
        screenshot_path = os.path.join(debug_dir, f"{image_name}_debug_{timestamp}.png")
        img.save(screenshot_path)
        
        print(f"✅ 調試截圖已保存: {screenshot_path}")
        print(f"\n📊 座標對比:")
        if ok_script_result and pyautogui_result:
            print(f"   OK Script 座標: ({ok_script_result['x']}, {ok_script_result['y']})")
            print(f"   PyAutoGUI 中心點: ({pyautogui_result['x']}, {pyautogui_result['y']})")
            print(f"   PyAutoGUI 左上角: ({pyautogui_result['left']}, {pyautogui_result['top']})")
            print(f"   座標差異: X={abs(ok_script_result['x'] - pyautogui_result['x'])}, Y={abs(ok_script_result['y'] - pyautogui_result['y'])}")
            
            # 判斷 OK Script 返回的是左上角還是中心點
            center_diff = abs(ok_script_result['x'] - pyautogui_result['x']) + abs(ok_script_result['y'] - pyautogui_result['y'])
            left_top_diff = abs(ok_script_result['x'] - pyautogui_result['left']) + abs(ok_script_result['y'] - pyautogui_result['top'])
            
            if center_diff < left_top_diff:
                print(f"   ✅ OK Script 返回的可能是中心點（與 PyAutoGUI 中心點更接近）")
            else:
                print(f"   ✅ OK Script 返回的可能是左上角（與 PyAutoGUI 左上角更接近）")
        
    except Exception as e:
        print(f"❌ 生成調試截圖失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # 允許通過命令行參數指定圖片路徑
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 默認測試 schedule_grid_corner.png
        image_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings", "schedule_grid_corner.png")
    
    # 允許通過命令行參數指定區域
    region = None
    if len(sys.argv) > 5:
        try:
            region = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
            print(f"使用命令行指定的搜尋區域: {region}")
        except:
            pass
    
    if not region:
        # 獲取 Nx Witness 窗口
        win = None
        window_titles = ["攝影機設定", "Camera Settings", "攝影機設定 - Nx Witness Client", "Camera Settings - Nx Witness Client", "Nx Witness Client"]
        for title in window_titles:
            try:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    win = max(wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                    if win.width > 800 and win.height > 600:
                        break
            except Exception:
                continue
        
        if win:
            print(f"\n🪟 找到窗口: {win.title}")
            print(f"   位置: ({win.left}, {win.top})")
            print(f"   尺寸: {win.width}x{win.height}")
            
            # 檢查窗口是否在屏幕上（位置不應該是負數或過大）
            screen_width, screen_height = pyautogui.size()
            if win.left < -1000 or win.top < -1000 or win.left > screen_width or win.top > screen_height:
                print(f"⚠️ 窗口位置異常，可能被最小化或不在屏幕上")
                print(f"   嘗試激活窗口...")
                try:
                    win.activate()
                    import time
                    time.sleep(1.0)
                    # 重新獲取窗口位置
                    wins = [w for w in gw.getWindowsWithTitle(win.title) if w.visible]
                    if wins:
                        win = max(wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                        print(f"   激活後位置: ({win.left}, {win.top})")
                        print(f"   激活後尺寸: {win.width}x{win.height}")
                except Exception as e:
                    print(f"   ⚠️ 激活窗口失敗: {e}")
            
            # 如果窗口位置仍然異常，使用全屏
            if win.left < -1000 or win.top < -1000 or win.left > screen_width or win.top > screen_height:
                print(f"\n⚠️ 窗口位置仍然異常，使用全屏搜尋")
                region = None
            else:
                # 定義搜尋區域（窗口的 15%-85% 寬度，10%-65% 高度）
                search_region_left = win.left + int(win.width * 0.15)
                search_region_top = win.top + int(win.height * 0.10)
                search_region_width = int(win.width * 0.70)
                search_region_height = int(win.height * 0.55)
                region = (search_region_left, search_region_top, search_region_width, search_region_height)
                
                print(f"\n🔍 搜尋區域: {region}")
        else:
            print("\n⚠️ 未找到 Nx Witness 窗口，使用全屏搜尋")
            region = None
    
    # 執行測試
    test_image_recognition(image_path, region)
    
    print("\n" + "=" * 80)
    print("調試完成！請查看生成的截圖文件。")
    print("=" * 80)
