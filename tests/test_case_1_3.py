"""
Test Case 1-3: 啟用免費一個月的錄製授權
測試步驟 20-24
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.nx_poc_actions import NxPocActions
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_activate_free_license():
    """測試啟用免費授權流程"""
    print("\n" + "="*60)
    print("Test Case 1-3: 啟用免費錄製授權")
    print("="*60 + "\n")
    
    # 初始化 Actions
    actions = NxPocActions(browser_context=None)
    
    # 步驟 1: 確保已登入
    print("步驟 1: 確保已登入系統...")
    actions.run_ensure_login_step()
    
    # 步驟 2: 執行啟用免費授權流程
    print("\n步驟 2: 啟用免費授權...")
    print("-" * 60)
    print("步驟 20: 在 Server 上右鍵，點選「系統管理」")
    print("步驟 21: 進入「系統管理」視窗（預設在「一般」頁籤）")
    print("步驟 22: 切換到「授權」頁籤，點選「啟用免費授權」")
    print("步驟 23: 顯示已啟用授權，點選 OK")
    print("步驟 24: 回到「授權」頁籤，顯示授權碼，點選 OK")
    print("-" * 60)
    
    actions.run_activate_free_license_step(use_menu=False)
    
    print("\n" + "="*60)
    print("✅ Test Case 1-3 測試完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_activate_free_license()
