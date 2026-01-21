import pandas as pd
import os

def load_test_cases(file_path):
    """
    設計師邏輯：
    1. 讀取 TestDir 找出需要執行的分頁
    2. 遍歷分頁，將 TestName 下的所有步驟封裝成 pytest 參數
    """
    # 讀取 TestDir (目前環境讀取 CSV 版本)
    dir_df = pd.read_csv('TestPlan.xlsx - TestDir.csv')
    
    all_test_data = []
    
    # 從 TestDir 獲取要執行的分頁名稱
    target_sheets = dir_df['FunctionalClassification'].unique()
    
    for sheet_name in target_sheets:
        # 實務上從 Excel 讀取特定分頁，這裡讀取對應的 CSV
        csv_file = f"TestPlan.xlsx - {sheet_name}.csv"
        if not os.path.exists(csv_file):
            continue
            
        case_df = pd.read_csv(csv_file)
        
        # 依照 TestName 分群，將同一個測試的所有步驟打包
        for test_name, group in case_df.groupby('TestName'):
            steps = []
            for _, row in group.sort_values('StepNo').iterrows():
                steps.append({
                    "step_no": row['StepNo'],
                    "flow_name": row['FlowName'],
                    "params": parse_params(row['Params']) # 注入點
                })
            all_test_data.append((test_name, steps))
            
    return all_test_data

def parse_params(param_str):
    """ 解析 Params 字串: key1=val1;key2=val2 """
    if pd.isna(param_str) or not param_str:
        return {}
    pairs = [p.split('=') for p in str(param_str).split(';') if '=' in p]
    return {k.strip(): v.strip() for k, v in pairs}