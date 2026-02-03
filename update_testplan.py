# -*- coding: utf-8 -*-
"""
更新 TestPlan.xlsx 以反映新的程式架構

此腳本會更新 TestPlan.xlsx 中的 action 映射，
將舊的 NxPocActions 映射更新為新的重構模組。

執行方式：
python update_testplan.py
"""

import openpyxl
from pathlib import Path

def update_testplan():
    """更新 TestPlan.xlsx 的 action 映射"""
    
    # TestPlan.xlsx 路徑
    testplan_path = Path("DemoData/TestPlan.xlsx")
    
    if not testplan_path.exists():
        print(f"❌ 找不到文件: {testplan_path}")
        return False
    
    try:
        # 打開 Excel 文件
        wb = openpyxl.load_workbook(testplan_path)
        
        # 假設測試用例在第一個工作表
        ws = wb.active
        
        # 新的 action 映射（如果使用重構版本）
        action_mapping = {
            "自動登入伺服器": "login_actions_refactored.LoginActions.run_server_login_step",
            "自動登入伺服器並切換繁體中文": "nx_poc_actions.NxPocActions",  # 保持舊的
            "切換繁體中文": "settings_actions_refactored.SettingsActions.run_change_language_step",
            "新增Webcam攝影機": "nx_poc_actions.NxPocActions",  # 保持舊的
            "啟用免費一個月的錄製授權": "nx_poc_actions.NxPocActions",  # 保持舊的
            "開啟錄影功能": "nx_poc_actions.NxPocActions",  # 保持舊的
            "回放錄影事件後停止": "nx_poc_actions.NxPocActions",  # 保持舊的
            "進入 Nx Cloud": "nx_poc_actions.NxPocActions",  # 保持舊的
            "調閱一個錄影事件回放": "nx_poc_actions.NxPocActions",  # 保持舊的
        }
        
        # 打印當前內容（用於調試）
        print("=" * 60)
        print("TestPlan.xlsx 當前內容：")
        print("=" * 60)
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), 1):
            print(f"Row {row_idx}: {row}")
        
        print("\n" + "=" * 60)
        print("注意：此腳本需要根據實際的 Excel 結構進行調整")
        print("請檢查 TestPlan.xlsx 的結構，確定需要更新的列")
        print("=" * 60)
        
        # 保存文件（暫時註釋，等確認結構後再啟用）
        # wb.save(testplan_path)
        # print(f"✅ TestPlan.xlsx 已更新")
        
        wb.close()
        return True
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("開始更新 TestPlan.xlsx...")
    success = update_testplan()
    
    if success:
        print("\n✅ 檢查完成")
        print("\n請按照以下步驟手動更新 TestPlan.xlsx：")
        print("1. 打開 DemoData/TestPlan.xlsx")
        print("2. 找到 action 映射列")
        print("3. 根據新的模組結構更新")
        print("4. 參考 FINAL_REFACTORING_SUMMARY.md 中的映射表")
    else:
        print("\n❌ 檢查失敗")
