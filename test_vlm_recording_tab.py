#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 VLM/OCR 是否能識別「錄影」文字

使用方法：
1. 確保攝影機設定視窗已打開，並且可以看見「錄影」頁籤
2. 運行: python test_vlm_recording_tab.py
3. 程序會截取當前屏幕並嘗試識別「錄影」文字
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pyautogui
import time
from base.desktop_app import DesktopApp
from base.vlm_recognizer import get_vlm_recognizer
from config import EnvConfig

def test_vlm_recognition():
    """測試 VLM 是否能識別「錄影」文字"""
    print("=" * 60)
    print("測試 VLM/OCR 識別「錄影」文字")
    print("=" * 60)
    print()
    
    # 初始化 DesktopApp 以獲取視窗信息
    app = DesktopApp()
    
    # 獲取視窗
    print("[1] 獲取 Nx Witness 視窗...")
    win = app.get_nx_window()
    if not win:
        print("  [錯誤] 未找到 Nx Witness 視窗")
        print("  請確保 Nx Witness 已打開並且視窗可見")
        return
    
    print(f"  [OK] 找到視窗: 尺寸={win.width}x{win.height}, 位置=({win.left}, {win.top})")
    print()
    
    # 定義搜索區域（視窗區域）
    region = (win.left, win.top, win.width, win.height)
    print(f"[2] 搜索區域: {region}")
    
    # 頁籤區域通常在上方，可以縮小搜索範圍
    # 頁籤通常在視窗頂部 50-150 像素範圍內
    tab_region = (win.left, win.top + 50, win.width, 150)
    print(f"[3] 頁籤搜索區域（縮小範圍）: {tab_region}")
    print()
    
    # 測試目標文字
    target_texts = ["錄影", "錄製", "Recording"]
    
    # 測試 1: VLM 識別
    print("=" * 60)
    print("測試 1: VLM (視覺語言模型) 識別")
    print("=" * 60)
    
    vlm_enabled = getattr(EnvConfig, 'VLM_ENABLED', False)
    vlm_backend = getattr(EnvConfig, 'VLM_BACKEND', 'ollama')
    vlm_model = getattr(EnvConfig, 'VLM_MODEL', 'llava')
    
    print(f"VLM 配置: enabled={vlm_enabled}, backend={vlm_backend}, model={vlm_model}")
    
    if vlm_enabled:
        try:
            vlm = get_vlm_recognizer(backend=vlm_backend, model=vlm_model)
            if vlm:
                print("  [OK] VLM 引擎初始化成功")
                print()
                
                for target_text in target_texts:
                    print(f"  搜索文字: '{target_text}'")
                    print(f"  {'-' * 50}")
                    
                    # 先在全區域搜索，再在頁籤區域搜索
                    for search_name, search_region in [("全視窗", region), ("頁籤區域", tab_region)]:
                        print(f"    搜索範圍: {search_name}")
                        try:
                            start_time = time.perf_counter()
                            result = vlm.find_element(target_text, region=search_region)
                            elapsed_ms = (time.perf_counter() - start_time) * 1000
                            
                            if result and result.success:
                                print(f"      [成功] 找到 '{target_text}'")
                                print(f"      位置: ({result.x}, {result.y})")
                                
                                # 計算相對位置
                                relative_x = result.x - win.left
                                relative_y = result.y - win.top
                                ratio_x = relative_x / win.width
                                ratio_y = relative_y / win.height
                                print(f"      相對位置: x_ratio={ratio_x:.4f}, y_ratio={ratio_y:.4f}")
                                
                                print(f"      信心度: {result.confidence:.2f}")
                                print(f"      耗時: {elapsed_ms:.1f}ms")
                                if result.description:
                                    print(f"      描述: {result.description}")
                                if hasattr(result, 'raw_response') and result.raw_response:
                                    print(f"      [DEBUG] VLM 原始響應: {result.raw_response[:300]}")
                                
                                # 只顯示第一次成功結果
                                if search_name == "全視窗":
                                    break
                            else:
                                print(f"      [失敗] 未找到 '{target_text}'")
                                if result:
                                    print(f"      信心度: {result.confidence:.2f}")
                                print(f"      耗時: {elapsed_ms:.1f}ms")
                        except Exception as e:
                            print(f"      [錯誤] VLM 識別異常: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    print()
            else:
                print("  [失敗] VLM 引擎初始化失敗")
        except Exception as e:
            print(f"  [錯誤] VLM 初始化異常: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  [跳過] VLM 未啟用")
    
    print()
    
    # 測試 2: OCR 識別
    print("=" * 60)
    print("測試 2: OCR 識別")
    print("=" * 60)
    
    ocr_engine = app._get_ocr_engine()
    if ocr_engine:
        print("  [OK] OCR 引擎已初始化")
        print()
        
        for target_text in target_texts:
            print(f"  搜索文字: '{target_text}'")
            print(f"  {'-' * 50}")
            
            try:
                start_time = time.perf_counter()
                
                # 使用 OCR 引擎直接識別，找到所有匹配項
                screenshot = pyautogui.screenshot(region=region)
                import numpy as np
                img_array = np.array(screenshot)
                
                ocr_result = ocr_engine.ocr(img_array, cls=True)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                if ocr_result and ocr_result[0]:
                    # 找到所有匹配項
                    matches = []
                    for line in ocr_result[0]:
                        text = line[1][0]
                        confidence = line[1][1]
                        box = line[0]
                        
                        # 模糊匹配（包含即可）
                        if target_text in text and confidence > 0.5:
                            # 計算文字中心點
                            center_x = region[0] + (box[0][0] + box[2][0]) / 2
                            center_y = region[1] + (box[0][1] + box[2][1]) / 2
                            
                            relative_x = center_x - win.left
                            relative_y = center_y - win.top
                            ratio_x = relative_x / win.width
                            ratio_y = relative_y / win.height
                            
                            matches.append({
                                'text': text,
                                'confidence': confidence,
                                'x': int(center_x),
                                'y': int(center_y),
                                'x_ratio': ratio_x,
                                'y_ratio': ratio_y
                            })
                    
                    if matches:
                        print(f"    [成功] 找到 {len(matches)} 個 '{target_text}' 匹配項:")
                        for i, match in enumerate(matches, 1):
                            print(f"      匹配項 {i}:")
                            print(f"        完整文字: '{match['text']}'")
                            print(f"        位置: ({match['x']}, {match['y']})")
                            print(f"        相對位置: x_ratio={match['x_ratio']:.4f}, y_ratio={match['y_ratio']:.4f}")
                            print(f"        信心度: {match['confidence']:.2f}")
                    else:
                        print(f"    [失敗] 未找到 '{target_text}'")
                    
                    print(f"    耗時: {elapsed_ms:.1f}ms")
                else:
                    print(f"    [失敗] OCR 未返回結果")
                    print(f"    耗時: {elapsed_ms:.1f}ms")
            except Exception as e:
                print(f"    [錯誤] OCR 識別異常: {e}")
                import traceback
                traceback.print_exc()
            
            print()
    else:
        print("  [失敗] OCR 引擎未初始化")
    
    print()
    
    # 測試 3: 截取並保存截圖供人工檢查
    print("=" * 60)
    print("測試 3: 保存截圖供人工檢查")
    print("=" * 60)
    
    try:
        screenshot = pyautogui.screenshot(region=region)
        screenshot_path = "logs/test_recording_tab_screenshot.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        screenshot.save(screenshot_path)
        print(f"  [OK] 截圖已保存: {screenshot_path}")
        print(f"  請手動檢查截圖中是否包含「錄影」頁籤")
    except Exception as e:
        print(f"  [錯誤] 保存截圖失敗: {e}")
    
    print()
    print("=" * 60)
    print("測試完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        time.sleep(2)
        test_vlm_recognition()
    except KeyboardInterrupt:
        print("\n\n[中斷] 用戶中斷測試")
    except Exception as e:
        print(f"\n\n[錯誤] 測試過程中發生異常: {e}")
        import traceback
        traceback.print_exc()
