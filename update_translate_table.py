# -*- coding: utf-8 -*-
"""
更新 TestPlan.xlsx 的 Translate 表

將原本映射到 nx_poc 的 ActionKey 更新為對應的新 Action 類。

Author: SDET Team
Date: 2026-01-26
"""

import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime


def backup_testplan(testplan_path: Path) -> Path:
    """備份 TestPlan.xlsx
    
    Args:
        testplan_path: TestPlan.xlsx 路徑
        
    Returns:
        Path: 備份文件路徑
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = testplan_path.parent / f"TestPlan_backup_{timestamp}.xlsx"
    shutil.copy2(testplan_path, backup_path)
    print(f"✅ 已備份 TestPlan.xlsx 到: {backup_path}")
    return backup_path


def update_translate_table():
    """更新 Translate 表的 ActionKey 映射"""
    
    testplan_path = Path("DemoData/TestPlan.xlsx")
    
    if not testplan_path.exists():
        print(f"❌ 找不到文件: {testplan_path}")
        return False
    
    try:
        # 備份原文件
        backup_testplan(testplan_path)
        
        # 讀取 Translate 表
        df = pd.read_excel(testplan_path, sheet_name='Translate')
        
        print("\n" + "=" * 60)
        print("原 Translate 表內容：")
        print("=" * 60)
        print(df.to_string(index=False))
        
        # 新的映射關係
        new_mapping = {
            'ensure_login': 'login',           # 登錄 -> LoginActions (保留 login_actions_refactored.py)
            'change_language': 'settings',     # 語言 -> SettingsActions
            'enable_usb_webcam': 'camera',     # 攝影機 -> CameraActions
            'activate_free_license': 'license', # 授權 -> LicenseActions
            'enable_recording': 'recording',    # 錄影 -> RecordingActions
            'playback_recording': 'recording',  # 回放 -> RecordingActions
            'login_nx_cloud_web': 'cloud',      # Cloud -> CloudActions
            'review_recording_playback': 'recording', # 調閱回放 -> RecordingActions
            # Mobile 相關保持不變
            'login_mobile': 'nx_mobile',
            'select_server_and_camera': 'nx_mobile',
            'playback_with_calendar': 'nx_mobile',
        }
        
        # 更新 ActionKey
        for flow_name, new_action_key in new_mapping.items():
            mask = df['FlowName'] == flow_name
            if mask.any():
                df.loc[mask, 'ActionKey'] = new_action_key
                print(f"✅ 更新 {flow_name}: nx_poc -> {new_action_key}")
        
        print("\n" + "=" * 60)
        print("新 Translate 表內容：")
        print("=" * 60)
        print(df.to_string(index=False))
        
        # 將更新後的 Translate 表寫回 Excel
        with pd.ExcelWriter(testplan_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name='Translate', index=False)
        
        print("\n" + "=" * 60)
        print("✅ TestPlan.xlsx Translate 表已成功更新！")
        print("=" * 60)
        
        # 驗證更新
        df_verify = pd.read_excel(testplan_path, sheet_name='Translate')
        print("\n驗證更新後的內容：")
        print(df_verify.to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("開始更新 TestPlan.xlsx Translate 表...")
    print("\n新的 ActionKey 映射：")
    print("  - ensure_login -> login (LoginActions)")
    print("  - change_language -> settings (SettingsActions)")
    print("  - enable_usb_webcam -> camera (CameraActions)")
    print("  - activate_free_license -> license (LicenseActions)")
    print("  - enable_recording -> recording (RecordingActions)")
    print("  - playback_recording -> recording (RecordingActions)")
    print("  - login_nx_cloud_web -> cloud (CloudActions)")
    print("  - review_recording_playback -> recording (RecordingActions)")
    print("  - Mobile 相關保持 nx_mobile 不變")
    print()
    
    success = update_translate_table()
    
    if success:
        print("\n🎉 更新完成！")
        print("\n對應的 Action 類文件：")
        print("  - actions/login_actions_refactored.py (LoginActions)")
        print("  - actions/settings_actions.py (SettingsActions)")
        print("  - actions/camera_actions.py (CameraActions)")
        print("  - actions/license_actions.py (LicenseActions)")
        print("  - actions/recording_actions.py (RecordingActions)")
        print("  - actions/cloud_actions.py (CloudActions)")
        print("  - actions/nx_mobile_actions.py (NxMobileActions)")
    else:
        print("\n❌ 更新失敗，請檢查錯誤訊息")
