#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR 初始化速度測試腳本

用途：測試 OCR 引擎初始化時間
使用方法：python test_ocr_speed.py
"""

import time
import sys

def test_ocr_init_speed():
    """測試 OCR 引擎初始化速度"""
    
    print("=" * 60)
    print("🧪 OCR 初始化速度測試")
    print("=" * 60)
    print()
    
    # 測試 1: 導入 PaddleOCR
    print("📦 步驟 1: 導入 PaddleOCR 模組...")
    start = time.time()
    try:
        from paddleocr import PaddleOCR
        import logging
        import os
        elapsed = time.time() - start
        print(f"   ✅ 導入成功，耗時: {elapsed:.2f} 秒")
    except ImportError as e:
        print(f"   ❌ 導入失敗: {e}")
        sys.exit(1)
    
    print()
    
    # 測試 2: 初始化 OCR 引擎（優化配置）
    print("⚙️  步驟 2: 初始化 OCR 引擎（優化配置）...")
    print("   配置: use_angle_cls=False, DISABLE_MODEL_SOURCE_CHECK=True")
    
    # 禁用模型源檢查
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    logging.getLogger("ppocr").setLevel(logging.ERROR)
    
    start = time.time()
    try:
        ocr = PaddleOCR(
            use_angle_cls=False,  # 關閉角度分類器
            lang="ch"
        )
        elapsed = time.time() - start
        print(f"   ✅ 初始化成功，耗時: {elapsed:.2f} 秒")
        
        # 顯示時間評估
        if elapsed < 3:
            grade = "🚀 極快"
        elif elapsed < 6:
            grade = "⚡ 快"
        elif elapsed < 10:
            grade = "✅ 正常"
        else:
            grade = "⏰ 較慢"
        
        print(f"   評級: {grade}")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ 初始化失敗: {e}")
        print(f"   耗時: {elapsed:.2f} 秒")
        sys.exit(1)
    
    print()
    
    # 測試 3: 執行 OCR 識別（驗證功能）
    print("🔍 步驟 3: 測試 OCR 識別功能...")
    start = time.time()
    try:
        # 創建測試圖片（簡單的文字）
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 創建白底黑字圖片
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # 使用默認字體繪製文字
        try:
            # 嘗試使用系統字體
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            # 如果沒有，使用默認字體
            font = ImageFont.load_default()
        
        draw.text((10, 10), "測試文字", fill='black', font=font)
        
        # 轉換為 numpy 數組
        img_array = np.array(img)
        
        # 執行 OCR
        result = ocr.ocr(img_array, cls=False)
        
        elapsed = time.time() - start
        
        if result and result[0]:
            detected_text = " ".join([line[1][0] for line in result[0]])
            print(f"   ✅ 識別成功，耗時: {elapsed:.2f} 秒")
            print(f"   識別結果: {detected_text}")
        else:
            print(f"   ⚠️  未識別到文字，耗時: {elapsed:.2f} 秒")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ⚠️  測試執行異常: {e}")
        print(f"   耗時: {elapsed:.2f} 秒")
    
    print()
    print("=" * 60)
    print("🎉 測試完成！")
    print("=" * 60)
    print()
    print("📊 優化建議：")
    print("   - 如果初始化時間 > 10 秒，請確認:")
    print("     1. use_angle_cls=False 是否已設置")
    print("     2. DISABLE_MODEL_SOURCE_CHECK 環境變量是否已設置")
    print("     3. 模型文件是否已下載（第二次應該更快）")
    print("   - 如果初始化時間 < 6 秒，恭喜！優化成功！")
    print()

if __name__ == "__main__":
    test_ocr_init_speed()
