# -*- coding: utf-8 -*-
"""
更新 TestPlan.xlsx - 填入 Case 1-3 的完整配置
"""
import pandas as pd
from openpyxl import load_workbook

file_path = 'DemoData/TestPlan.xlsx'

# 讀取現有數據
df_testdir = pd.read_excel(file_path, sheet_name='TestDir')
df_case1 = pd.read_excel(file_path, sheet_name='Case1')
df_translate = pd.read_excel(file_path, sheet_name='Translate')

print("=== 更新前的 Case1 Sheet ===")
print(df_case1.to_string())
print()

# === 更新 Case1 Sheet ===
# 找到 Case 1-3 的行索引
case13_mask = df_case1['Test case'] == 'Test case 1-3'
case13_idx = df_case1[case13_mask].index[0] if case13_mask.any() else None

if case13_idx is not None:
    # 更新 Case 1-3 的第一步（確保登入）
    df_case1.loc[case13_idx, 'FlowName'] = 'ensure_login'
    df_case1.loc[case13_idx, 'Params'] = 'server_name=LAPTOP-QRJN5735'
    df_case1.loc[case13_idx, 'Description'] = '檢查並確保已登入系統'

# 檢查是否已有 Case 1-3 Step 2
case13_step2_exists = ((df_case1['Test case'] == 'Test case 1-3') & (df_case1['StepNo'] == 2)).any()

if not case13_step2_exists:
    # 獲取 Case 1-3 的 TestName
    test_name = df_case1[df_case1['Test case'] == 'Test case 1-3']['TestName'].iloc[0]
    
    # 新增 Case 1-3 的第二步（啟用免費授權）
    new_row = pd.DataFrame([{
        'Test case': 'Test case 1-3',
        'TestName': test_name,
        'StepNo': 2,
        'FlowName': 'activate_free_license',
        'Params': 'use_menu=False',
        'Description': '開啟系統管理並啟用免費授權'
    }])
    df_case1 = pd.concat([df_case1, new_row], ignore_index=True)

# === 更新 Translate Sheet ===
# 檢查 activate_free_license 是否已存在
if 'activate_free_license' not in df_translate['FlowName'].values:
    new_translate = pd.DataFrame([{
        'FlowName': 'activate_free_license',
        'ActionKey': 'nx_poc',
        'ActionMethod': 'run_activate_free_license_step',
        'Parameter': 'use_menu',
        'Parameter Description': '是否使用選單開啟',
        'Description': '啟用免費錄製授權'
    }])
    df_translate = pd.concat([df_translate, new_translate], ignore_index=True)

# 同時補完 USB 攝影機的 Translate 條目（如果缺失參數）
usb_mask = df_translate['FlowName'].str.contains('USB', na=False)
if usb_mask.any():
    usb_idx = df_translate[usb_mask].index[0]
    if pd.isna(df_translate.loc[usb_idx, 'Parameter']):
        df_translate.loc[usb_idx, 'Parameter'] = 'camera_name'
        df_translate.loc[usb_idx, 'Parameter Description'] = 'USB攝影機名稱'
        df_translate.loc[usb_idx, 'Description'] = '啟用USB攝影機自動偵測'

# 寫入 Excel
with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
    df_testdir.to_excel(writer, sheet_name='TestDir', index=False)
    df_case1.to_excel(writer, sheet_name='Case1', index=False)
    df_translate.to_excel(writer, sheet_name='Translate', index=False)

print("=== 更新後的 Case1 Sheet ===")
print(df_case1.to_string())
print()
print("=== 更新後的 Translate Sheet ===")
print(df_translate.to_string())
print()
print("✅ TestPlan.xlsx 已更新完成！")
