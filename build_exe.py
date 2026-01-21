# -*- coding: utf-8 -*-
"""
打包測試案例啟動器為 EXE 檔案

使用 PyInstaller 將 test_case_launcher.py 打包成可執行檔案
"""

import os
import subprocess
import sys


def build_exe():
    """打包成 EXE 檔案"""
    
    print("=" * 60)
    print("測試案例啟動器 - EXE 打包工具")
    print("=" * 60)
    
    # 檢查 PyInstaller 是否已安裝
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安裝 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("❌ PyInstaller 未安裝")
        print("正在安裝 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 安裝完成")
    
    # PyInstaller 命令（使用 python -m 方式確保能找到 PyInstaller）
    script_path = "test_case_launcher.py"
    exe_name = "TestCaseLauncher"
    
    # 打包參數（使用 python -m PyInstaller 而不是直接調用 pyinstaller）
    cmd = [
        sys.executable,  # 使用當前的 Python 解釋器
        "-m", "PyInstaller",
        "--name", exe_name,  # 輸出檔案名稱
        "--onefile",  # 打包成單一執行檔
        "--windowed",  # 不顯示控制台視窗（GUI 應用）
        "--noconfirm",  # 覆蓋已存在的檔案
        "--clean",  # 清理暫存檔
        # 如需自訂圖示，添加: "--icon", "icon.ico",
        
        # 隱藏的匯入（確保所有依賴都被包含）
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",  # pandas 讀取 Excel 需要
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.scrolledtext",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "config",
        
        # 注意：不使用 --add-data 打包 DemoData
        # 這樣 EXE 每次執行時會自動從 EXE 所在目錄讀取 TestPlan.xlsx
        # 更新 TestPlan.xlsx 時，只需替換檔案，無需重新打包 EXE
        
        script_path
    ]
    
    print(f"\n📦 開始打包: {script_path}")
    print(f"📝 輸出檔案: {exe_name}.exe")
    print("\n執行命令:")
    print(" ".join(cmd))
    print("\n" + "=" * 60 + "\n")
    
    try:
        # 執行打包
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        print("\n" + "=" * 60)
        print("✅ 打包完成！")
        print("=" * 60)
        print(f"\n📁 EXE 檔案位置: dist\\{exe_name}.exe")
        print(f"📁 暫存檔案位置: build\\ (可刪除)")
        print(f"📁 規格檔案: {exe_name}.spec (可保留用於進階設定)")
        print("\n💡 重要提示:")
        print(f"   - EXE 檔案需要與 DemoData 資料夾在同一目錄下")
        print(f"   - 建議將 dist\\{exe_name}.exe 放在專案根目錄 (D:\\nxwitness-demo\\)")
        print(f"   - 或者將 {exe_name}.exe 和 DemoData 資料夾一起複製到其他位置")
        print(f"   - 更新 TestPlan.xlsx 時，只需替換檔案，無需重新打包 EXE")
        print(f"   - 首次運行時可能較慢（解壓縮過程）")
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ 打包失敗！")
        print("=" * 60)
        print(f"\n錯誤輸出:\n{e.stderr}")
        print(f"\n標準輸出:\n{e.stdout}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
