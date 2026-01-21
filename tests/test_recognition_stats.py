# -*- coding: utf-8 -*-
"""
測試圖像辨識統計功能

這個腳本展示如何：
1. 使用 OK Script / OpenCV 進行圖像辨識
2. 統計命中率和所需時間
3. 生成統計報告
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from base.ok_script_recognizer import get_recognizer, OKScriptRecognizer
from base.desktop_app import DesktopApp
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_recognizer_stats():
    """測試辨識器統計功能"""
    print("\n" + "=" * 60)
    print("圖像辨識統計功能測試")
    print("=" * 60 + "\n")
    
    # 取得辨識器實例
    recognizer = get_recognizer()
    
    # 設置日誌
    logger = logging.getLogger("TestRecognizer")
    recognizer.set_logger(logger)
    
    print("當前統計狀態：")
    print(recognizer.get_stats_summary())
    print()

def test_with_desktop_app():
    """使用 DesktopApp 測試統計功能"""
    print("\n" + "=" * 60)
    print("使用 DesktopApp 測試統計功能")
    print("=" * 60 + "\n")
    
    app = DesktopApp()
    
    # 顯示當前統計
    print("當前辨識統計：")
    print(app.get_recognition_stats())
    print()
    
    print("提示：")
    print("  1. 執行實際測試案例（如 Case 1-2, 1-3）來收集統計數據")
    print("  2. 使用 app.save_recognition_stats() 保存統計")
    print("  3. 使用 app.reset_recognition_stats() 重置統計")
    print()

def show_available_images():
    """顯示可用的圖片資源"""
    print("\n" + "=" * 60)
    print("可用的圖片資源")
    print("=" * 60 + "\n")
    
    res_path = os.path.join(os.path.dirname(__file__), '..', 'res')
    
    if not os.path.exists(res_path):
        print(f"資源目錄不存在: {res_path}")
        return
    
    total_images = 0
    for root, dirs, files in os.walk(res_path):
        png_files = [f for f in files if f.endswith('.png')]
        if png_files:
            rel_path = os.path.relpath(root, res_path)
            print(f"\n{rel_path}/")
            for f in sorted(png_files):
                full_path = os.path.join(root, f)
                size = os.path.getsize(full_path)
                print(f"  - {f} ({size} bytes)")
                total_images += 1
    
    print(f"\n總計: {total_images} 張圖片")
    print()

def show_usage_guide():
    """顯示使用指南"""
    print("\n" + "=" * 60)
    print("OK Script 辨識器使用指南")
    print("=" * 60 + "\n")
    
    print("""
【優先級順序】
1. OK Script / OpenCV Template Matching（如果啟用）
2. pyautogui 圖片辨識（作為備用）
3. OCR 文字辨識
4. 座標保底

【統計指標】
- 命中率 (Hit Rate): 各方法成功辨識的比例
- 平均時間: 各方法的平均辨識時間（毫秒）
- 各圖片統計: 每張圖片的辨識成功率

【配置選項】
- use_ok_script=True/False: 是否啟用 OK Script（smart_click 參數）
- confidence: 信心閾值（預設 0.85）

【統計命令】
- app.get_recognition_stats()  # 取得統計報告
- app.save_recognition_stats() # 保存統計到文件
- app.reset_recognition_stats() # 重置統計

【統計文件】
- logs/recognition_stats.json

【使用範例】
```python
from base.desktop_app import DesktopApp

app = DesktopApp()

# 執行點擊（會自動記錄統計）
app.smart_click(0.5, 0.5, image_path="desktop_main/server_icon.png")

# 查看統計
print(app.get_recognition_stats())

# 保存統計
app.save_recognition_stats()
```
""")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OK Script Image Recognition Stats Test")
    print("=" * 60)
    
    # 顯示可用圖片
    show_available_images()
    
    # 測試辨識器統計
    test_recognizer_stats()
    
    # 使用 DesktopApp 測試
    test_with_desktop_app()
    
    # 顯示使用指南
    show_usage_guide()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
