#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI 樹狀結構傾倒腳本 (UI Tree Dumper)
使用 pywinauto 導出 Nx Witness 應用程式的 UI 元件結構

使用方法:
    python scripts/dump_ui_tree.py
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from pywinauto import Application
except ImportError:
    print("錯誤: 未安裝 pywinauto")
    print("請執行: pip install pywinauto")
    sys.exit(1)


def find_nx_witness_window():
    """尋找標題包含 'Nx Witness' 的應用程式視窗"""
    try:
        # 嘗試使用 uia backend 連接
        app = Application(backend="uia").connect(title_re=".*Nx Witness.*")
        return app
    except Exception as e:
        print(f"使用 uia backend 連接失敗: {e}")
        print("嘗試使用 win32 backend...")
        try:
            app = Application(backend="win32").connect(title_re=".*Nx Witness.*")
            return app
        except Exception as e2:
            print(f"使用 win32 backend 連接也失敗: {e2}")
            return None


def dump_ui_tree():
    """導出 UI 樹狀結構到檔案"""
    print("=" * 60)
    print("UI 樹狀結構傾倒腳本 (UI Tree Dumper)")
    print("=" * 60)
    print()
    
    # 尋找 Nx Witness 應用程式
    print("正在尋找 Nx Witness 應用程式...")
    app = find_nx_witness_window()
    
    if app is None:
        print("\n❌ 錯誤: 找不到標題包含 'Nx Witness' 的應用程式視窗")
        print("\n請確認:")
        print("  1. Nx Witness 應用程式已經啟動")
        print("  2. 應用程式視窗標題包含 'Nx Witness'")
        print("  3. 嘗試手動檢查視窗標題:")
        print("     - 在 Windows 中，可以查看工作管理員或使用 Alt+Tab")
        return False
    
    # 列出所有視窗，幫助用戶確認
    print("\n找到應用程式，正在列出所有視窗...")
    try:
        windows = app.windows()
        print(f"找到 {len(windows)} 個視窗:")
        for i, window in enumerate(windows, 1):
            try:
                title = window.window_text()
                print(f"  {i}. {title}")
            except:
                print(f"  {i}. (無法取得標題)")
    except Exception as e:
        print(f"無法列出視窗: {e}")
    
    # 尋找主視窗（通常是最大的視窗或第一個視窗）
    print("\n正在尋找主視窗...")
    try:
        # 嘗試獲取主視窗
        if hasattr(app, 'top_window'):
            main_window = app.top_window()
        else:
            # 如果沒有 top_window，使用第一個視窗
            windows = app.windows()
            if windows:
                main_window = windows[0]
            else:
                print("❌ 錯誤: 找不到任何視窗")
                return False
        
        # 獲取視窗標題
        try:
            window_title = main_window.window_text()
            print(f"主視窗標題: {window_title}")
        except:
            print("主視窗: (無法取得標題)")
        
        # 導出 UI 樹狀結構
        output_file = project_root / "nx_tree_dump.txt"
        print(f"\n正在導出 UI 樹狀結構到: {output_file}")
        print("深度: 10 層")
        print("這可能需要幾秒鐘...")
        
        # 使用 dump_tree 導出
        main_window.dump_tree(depth=10, filename=str(output_file))
        
        print(f"\n✅ 成功! UI 樹狀結構已導出到: {output_file}")
        print(f"檔案大小: {os.path.getsize(output_file)} 位元組")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: 導出 UI 樹狀結構時發生錯誤")
        print(f"錯誤訊息: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    try:
        success = dump_ui_tree()
        if success:
            print("\n" + "=" * 60)
            print("下一步:")
            print("  1. 檢查 nx_tree_dump.txt 檔案")
            print("  2. 將檔案提供給 AI 進行分析")
            print("  3. AI 將分析「日曆 (Calendar)」和「日期按鈕 (Date Button)」的屬性")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("請檢查錯誤訊息並重試")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n使用者中斷執行")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
