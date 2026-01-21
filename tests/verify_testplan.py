# -*- coding: utf-8 -*-
"""
驗證 TestPlan 引擎設計
確認能正確解析 Case 1-3: 啟用免費一個月的錄製授權
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from config import EnvConfig

def verify_testplan_flow(test_name):
    """驗證 TestPlan 流程"""
    print("=" * 60)
    print(f"Verifying TestPlan Flow for: {test_name}")
    print("=" * 60)
    
    # Step 1: 從 TestDir 找 FunctionalClassification
    print("\n[Step 1] Reading TestDir sheet...")
    dir_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="TestDir")
    
    match = dir_df[dir_df['TestName'] == test_name]
    if match.empty:
        print(f"  ERROR: TestName '{test_name}' not found in TestDir")
        return False
    
    fc = match.iloc[0]['FunctionalClassification']
    print(f"  Found: TestName='{test_name}' -> FunctionalClassification='{fc}'")
    
    # Step 2: 從對應 Sheet 找步驟
    print(f"\n[Step 2] Reading {fc} sheet...")
    case_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name=fc)
    steps_df = case_df[case_df['TestName'] == test_name].sort_values(by='StepNo')
    
    if steps_df.empty:
        print(f"  ERROR: No steps found for TestName '{test_name}' in {fc}")
        return False
    
    print(f"  Found {len(steps_df)} steps:")
    for _, row in steps_df.iterrows():
        print(f"    Step {row['StepNo']}: FlowName='{row['FlowName']}', Params='{row['Params']}'")
    
    # Step 3: 從 Translate 找 ActionMethod
    print(f"\n[Step 3] Reading Translate sheet...")
    trans_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="Translate")
    
    print("  Mapping FlowName -> ActionMethod:")
    for _, row in steps_df.iterrows():
        flow_name = row['FlowName']
        trans_match = trans_df[trans_df['FlowName'] == flow_name]
        
        if trans_match.empty:
            print(f"    WARNING: FlowName '{flow_name}' not found in Translate")
        else:
            action_key = trans_match.iloc[0]['ActionKey']
            action_method = trans_match.iloc[0]['ActionMethod']
            print(f"    '{flow_name}' -> {action_key}.{action_method}()")
    
    print("\n" + "=" * 60)
    print("Verification PASSED!")
    print("=" * 60)
    return True

def list_all_testcases():
    """列出所有測試案例"""
    print("\n" + "=" * 60)
    print("All Test Cases in TestPlan")
    print("=" * 60)
    
    dir_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="TestDir")
    
    for idx, row in dir_df.iterrows():
        print(f"  {idx + 1}. {row['TestName']}")
        print(f"     -> FunctionalClassification: {row['FunctionalClassification']}")
    
    print("=" * 60)

if __name__ == "__main__":
    # 列出所有測試案例
    list_all_testcases()
    
    # 驗證 Case 1-3
    print("\n")
    verify_testplan_flow("啟用免費一個月的錄製授權")
