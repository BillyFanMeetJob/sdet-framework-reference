import pytest
import pandas as pd
import os
import sys
from engine.step_translator import StepTranslator
from config import EnvConfig

# 設置 UTF-8 編碼，避免 Windows cp950 編碼錯誤
if sys.platform == 'win32':
    try:
        # 嘗試設置 stdout 和 stderr 為 UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # 如果設置失敗，使用環境變數
        os.environ['PYTHONIOENCODING'] = 'utf-8'

def get_test_data():
    # 🎯 抓取命令行 --test_name 參數
    target_test = None
    for i, arg in enumerate(sys.argv):
        if arg == "--test_name" and i + 1 < len(sys.argv):
            target_test = sys.argv[i+1]

    test_data = []
    if not os.path.exists(EnvConfig.TEST_PLAN_PATH): return []

    # 🎯 讀取 Excel 的 TestDir 工作表（如果不存在，嘗試 Sheet1）
    dir_df = None
    try:
        dir_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="TestDir")
    except ValueError:
        # 如果找不到 TestDir，嘗試 Sheet1（某些 Excel 文件可能使用 Sheet1 作為 TestDir）
        try:
            xl_file = pd.ExcelFile(EnvConfig.TEST_PLAN_PATH)
            available_sheets = xl_file.sheet_names
            if 'Sheet1' in available_sheets:
                dir_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name='Sheet1')
            elif available_sheets:
                # 使用第一個工作表
                dir_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name=available_sheets[0])
            else:
                print(f"[ERROR] Excel 文件中沒有任何工作表")
                return []
        except Exception as e:
            print(f"[ERROR] 無法讀取 Excel 文件: {e}")
            return []
    
    if dir_df is None or dir_df.empty:
        print(f"[ERROR] 無法讀取測試計劃數據")
        return []
    
    for _, row in dir_df.iterrows():
        test_name = row['TestName']
        
        # 🎯 過濾邏輯
        if target_test and target_test != test_name: continue
        
        # 🎯 讀取對應的功能分類工作表（如 Case1）
        functional_class = row.get('FunctionalClassification')
        if pd.isna(functional_class) or not str(functional_class).strip():
            print(f"[WARN] 測試案例 '{test_name}' 沒有 FunctionalClassification，跳過")
            continue
            
        try:
            case_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name=str(functional_class))
        except ValueError as e:
            print(f"[WARN] 無法讀取工作表 '{functional_class}'，跳過測試案例 '{test_name}': {e}")
            continue
        
        steps_df = case_df[case_df['TestName'] == test_name].sort_values(by='StepNo')
        
        steps = []
        for _, s_row in steps_df.iterrows():
            params = {}
            if pd.notna(s_row['Params']):
                for p in str(s_row['Params']).split(";"):
                    if "=" in p:
                        k, v = p.split("=", 1)
                        params[k.strip()] = v.strip()
            steps.append({"flow_name": s_row['FlowName'], "params": params})
        if steps: test_data.append((test_name, steps))
    return test_data

@pytest.mark.parametrize("test_name, steps", get_test_data())
def test_main_flow(test_name, steps, browser_context):
    """
    執行測試流程並驗證結果
    
    驗證規則：
    1. 連續三個需要圖像辨識的物件，沒有使用圖像辨識成功，就判定Fail
    2. 保底座標使用率不應過高（> 50% 視為失敗）
    
    Args:
        test_name: 測試名稱
        steps: 測試步驟列表
        browser_context: Web 瀏覽器上下文（用於桌面/網頁端測試）
    """
    from engine.test_reporter import TestReporter
    from base.ok_script_recognizer import get_recognizer
    
    html_path = None  # 用於保存報告路徑
    overall_status = "pass"  # 預設為通過
    mobile_driver = None  # 移動端 driver（按需初始化）
    reporter = None  # 初始化為 None，確保 finally 中可以檢查
    
    try:
        # 🎯 檢測是否需要移動端測試（通過檢查步驟中的 ActionKey）
        needs_mobile = False
        try:
            translate_df = pd.read_excel(EnvConfig.TEST_PLAN_PATH, sheet_name="Translate")
            for step in steps:
                flow_name = step.get('flow_name', '')
                row = translate_df[translate_df['FlowName'] == flow_name]
                if not row.empty and row.iloc[0]['ActionKey'] == 'nx_mobile':
                    needs_mobile = True
                    break
        except Exception as e:
            print(f"[WARN] 檢測移動端需求時發生錯誤: {e}")
        
        # 🎯 先初始化測試報告生成器（確保即使後續步驟失敗也能記錄）
        reporter = TestReporter(test_name, mobile_driver=None)
        
        # 如果需要移動端，初始化 Appium WebDriver
        if needs_mobile:
            import time
            mobile_init_start = time.time()
            try:
                print(f"\n[系統] [時間戳: {time.strftime('%H:%M:%S')}] 偵測到移動端測試需求，啟動 Appium WebDriver...")
            except UnicodeEncodeError:
                print(f"\n[系統] [時間戳: {time.strftime('%H:%M:%S')}] 偵測到移動端測試需求，啟動 Appium WebDriver...")
            
            try:
                from toolkit.mobile_toolkit import create_appium_driver
                mobile_driver, wait = create_appium_driver()
                mobile_init_elapsed = time.time() - mobile_init_start
                try:
                    print(f"[系統] [耗時: {mobile_init_elapsed:.2f}s] [OK] Appium WebDriver 初始化成功")
                except UnicodeEncodeError:
                    print(f"[系統] [耗時: {mobile_init_elapsed:.2f}s] [OK] Appium WebDriver 初始化成功")
                # 更新 reporter 的 mobile_driver 引用（用於截圖）
                reporter.mobile_driver = mobile_driver
            except Exception as e:
                error_msg = f"Appium WebDriver 初始化失敗: {str(e)}"
                try:
                    print(f"[系統] [ERROR] {error_msg}")
                except UnicodeEncodeError:
                    print(f"[系統] [ERROR] Appium WebDriver 初始化失敗")
                import sys
                try:
                    sys.stdout.flush()  # 確保日誌立即輸出
                except:
                    pass
                # 記錄錯誤到報告
                try:
                    reporter.add_step(
                        step_no=0,
                        step_name="Appium WebDriver 初始化",
                        status="fail",
                        message=error_msg
                    )
                except Exception as report_error:
                    # 如果記錄報告也失敗，至少記錄到日誌
                    try:
                        print(f"[ERROR] 記錄錯誤到報告失敗: {report_error}")
                    except:
                        pass
                overall_status = "fail"
                # 設置 mobile_driver 為 None，後續步驟會因為缺少 driver 而失敗
                mobile_driver = None
                # 不重新拋出異常，讓測試繼續執行以便生成完整報告
                # 但由於缺少 mobile_driver，後續步驟無法執行，所以直接跳過所有步驟
                try:
                    print("[系統] [WARN] 由於 Appium WebDriver 初始化失敗，跳過所有測試步驟")
                    sys.stdout.flush()
                except:
                    pass
                # 跳過後續步驟，直接執行 finally 塊生成報告
                # 通過設置一個標記來跳過步驟執行循環
        
        # 註冊 reporter 到 DesktopApp（用於自動截圖，僅桌面端需要）
        if browser_context is not None:
            from base.desktop_app import DesktopApp
            DesktopApp.set_reporter(reporter)
        
        # 初始化 StepTranslator（支持桌面端和移動端）
        translator = StepTranslator(browser_context=browser_context, mobile_driver=mobile_driver)
        
        # 執行前記錄初始統計
        recognizer = get_recognizer()
        recognizer.reset_consecutive_failures()  # 重置連續失敗計數
        initial_coordinate_hits = recognizer.stats.coordinate_hits
        initial_total_attempts = recognizer.stats.total_attempts
        
        # 執行所有步驟（只有在 Appium 初始化成功或不需要 mobile 時才執行）
        step_no = 1
        skip_steps = (needs_mobile and mobile_driver is None)  # 如果需要 mobile 但初始化失敗，跳過步驟
        
        if skip_steps:
            print("[系統] [WARN] 跳過所有測試步驟（Appium WebDriver 未初始化）")
            import sys
            sys.stdout.flush()
        
        for step in steps:
            # 如果需要 mobile 但初始化失敗，跳過所有步驟
            if skip_steps:
                break
            flow_name = step['flow_name']
            
            # 檢查連續失敗次數（在執行前檢查）
            consecutive_failures = recognizer.get_consecutive_image_recognition_failures()
            if consecutive_failures >= 3:
                error_msg = (
                    f"測試失敗：連續 {consecutive_failures} 次圖像辨識失敗！\n"
                    f"這表示無法找到正確的 UI 元素，可能是：\n"
                    f"- UI 元素未出現或位置改變\n"
                    f"- 圖片辨識資源不正確\n"
                    f"- 測試步驟順序錯誤\n"
                    f"請檢查測試執行過程和日誌。"
                )
                
                # 添加失敗步驟到報告
                reporter.add_step(
                    step_no=step_no,
                    step_name=flow_name,
                    status="fail",
                    message=error_msg
                )
                
                print(f"\n[ERROR] {error_msg}")
                overall_status = "fail"
                break  # 立即停止測試
            
            # 執行步驟
            try:
                translator.execute(flow_name, injected_params=step['params'])
                
                # 檢查執行後的連續失敗次數
                consecutive_failures = recognizer.get_consecutive_image_recognition_failures()
                
                if consecutive_failures >= 3:
                    # 連續失敗達到閾值，標記為失敗
                    reporter.add_step(
                        step_no=step_no,
                        step_name=flow_name,
                        status="fail",
                        message=f"連續 {consecutive_failures} 次圖像辨識失敗"
                    )
                    overall_status = "fail"
                    break
                else:
                    # 步驟執行成功
                    reporter.add_step(
                        step_no=step_no,
                        step_name=flow_name,
                        status="pass",
                        message=f"步驟執行成功（連續失敗: {consecutive_failures}）"
                    )
            except Exception as e:
                # 步驟執行出錯
                error_msg = f"步驟執行時發生異常: {str(e)}"
                reporter.add_step(
                    step_no=step_no,
                    step_name=flow_name,
                    status="fail",
                    message=error_msg
                )
                overall_status = "fail"
                print(f"\n[ERROR] {error_msg}")
                break
            
            step_no += 1
        
        # 測試結束後取得統計
        recognizer.save_stats()
        stats_summary = recognizer.get_stats_summary()
        print("\n" + stats_summary)
        
        # 計算測試期間的統計
        final_coordinate_hits = recognizer.stats.coordinate_hits
        final_total_attempts = recognizer.stats.total_attempts
        
        test_coordinate_hits = final_coordinate_hits - initial_coordinate_hits
        test_total_attempts = final_total_attempts - initial_total_attempts
        
        # 驗證規則 1: 連續圖像辨識失敗（已在執行過程中檢查）
        
        # 驗證規則 2: 保底座標使用率不應過高
        # 調整閾值為 50%（如果使用率超過 50%，視為失敗）
        if test_total_attempts > 0:
            coordinate_rate = (test_coordinate_hits / test_total_attempts) * 100
            
            # 如果保底座標使用率 > 50%，視為測試失敗
            if coordinate_rate > 50.0:
                error_msg = (
                    f"測試失敗：保底座標使用率過高 ({coordinate_rate:.1f}%)！\n"
                    f"這表示大部分操作無法找到正確的 UI 元素。\n"
                    f"當前閾值: 50%"
                )
                print(f"\n[ERROR] {error_msg}")
                overall_status = "fail"
            else:
                # 如果使用率在 30%-50% 之間，發出警告但不失敗
                if coordinate_rate > 30.0:
                    warning_msg = f"[WARN] 警告：保底座標使用率較高 ({coordinate_rate:.1f}%)，建議檢查圖片辨識資源"
                    print(f"\n{warning_msg}")
    
    finally:
        # 清理移動端 driver（如果已初始化）
        if mobile_driver is not None:
            print("\n[系統] 關閉 Appium WebDriver...")
            try:
                mobile_driver.quit()
                print("[系統] [OK] Appium WebDriver 已關閉")
            except Exception as e:
                print(f"[系統] [WARN] 關閉 Appium WebDriver 失敗: {e}")
        
        # 確保總是生成報告（無論測試是否失敗）
        try:
            # 如果 reporter 未初始化（例如測試在 collection 階段失敗），嘗試創建一個最小化的報告
            if reporter is None:
                print("\n[WARN] TestReporter 未初始化，嘗試創建最小化報告...")
                try:
                    reporter = TestReporter(test_name, mobile_driver=None)
                    # 添加一個失敗步驟說明測試未執行
                    reporter.add_step(
                        step_no=0,
                        step_name="測試初始化失敗",
                        status="fail",
                        message="測試在初始化階段失敗，可能是因為缺少依賴（如 appium 模組）或配置錯誤。請檢查錯誤日誌。"
                    )
                    overall_status = "fail"
                except Exception as e:
                    print(f"[ERROR] 無法創建 TestReporter: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 優先使用 Terminal log（從環境變數獲取）
            log_file_path = None
            if 'TEST_TERMINAL_LOG' in os.environ:
                terminal_log = os.environ.get('TEST_TERMINAL_LOG')
                print(f"[REPORT] 從環境變數獲取 Terminal log: {terminal_log}")
                if os.path.exists(terminal_log):
                    log_file_path = terminal_log
                    file_size = os.path.getsize(terminal_log)
                    print(f"[REPORT] Terminal log 文件存在，大小: {file_size} bytes")
                else:
                    print(f"[WARNING] Terminal log 文件不存在: {terminal_log}")
                # 清除環境變數，避免影響下一個測試
                del os.environ['TEST_TERMINAL_LOG']
            
            # 如果沒有 Terminal log，嘗試從預設位置獲取 automation.log
            if not log_file_path:
                automation_log = os.path.join(EnvConfig.PROJECT_ROOT, "logs", "automation.log")
                print(f"[REPORT] 嘗試使用預設 automation.log: {automation_log}")
                if os.path.exists(automation_log):
                    log_file_path = automation_log
                    file_size = os.path.getsize(automation_log)
                    print(f"[REPORT] automation.log 文件存在，大小: {file_size} bytes")
                else:
                    print(f"[WARNING] automation.log 文件不存在: {automation_log}")
            
            # 只有在 reporter 存在時才調用 finish
            if reporter is not None:
                try:
                    print(f"[REPORT] 開始生成報告，log_file_path: {log_file_path}")
                    html_path = reporter.finish(overall_status, log_file_path=log_file_path)
                except Exception as finish_error:
                    print(f"[ERROR] 生成報告時發生錯誤: {finish_error}")
                    import traceback
                    try:
                        traceback.print_exc()
                    except:
                        pass
                    html_path = None
            else:
                print("[ERROR] 無法生成報告：TestReporter 未初始化")
                # 即使 reporter 不存在，也嘗試手動保存 log（如果有的話）
                if log_file_path and os.path.exists(log_file_path):
                    try:
                        import shutil
                        from datetime import datetime
                        # 創建一個基本的報告目錄
                        safe_test_name = test_name.replace("/", "_").replace("\\", "_")
                        report_base = os.path.join(EnvConfig.PROJECT_ROOT, "report")
                        test_dir = os.path.join(report_base, safe_test_name)
                        time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        report_dir = os.path.join(test_dir, time_str)
                        os.makedirs(report_dir, exist_ok=True)
                        
                        # 複製 log 文件
                        report_log_path = os.path.join(report_dir, "terminal_output.log")
                        shutil.copy2(log_file_path, report_log_path)
                        print(f"[REPORT] Log 已手動保存到: {report_log_path}")
                    except Exception as e:
                        print(f"[ERROR] 手動保存 log 失敗: {e}")
                        import traceback
                        traceback.print_exc()
            # 🎯 Demo 友好結束：打印完整的報告路徑，方便點擊開啟
            if html_path and os.path.exists(html_path):
                # 轉換為絕對路徑並標準化
                abs_path = os.path.abspath(html_path).replace("\\", "/")
                print(f"\n{'='*80}")
                print(f"[REPORT] 測試報告已生成！")
                print(f"[REPORT] 報告路徑: {abs_path}")
                print(f"[REPORT] 您可以直接在瀏覽器中打開此文件查看詳細報告")
                print(f"{'='*80}\n")
            else:
                # 使用 ASCII 字符避免編碼問題
                print(f"\n[REPORT] 測試報告已生成: {html_path}")
        except Exception as e:
            print(f"\n[ERROR] 生成測試報告時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            # 即使報告生成失敗，也要繼續
            html_path = None
    
    # 如果測試失敗，拋出異常
    if overall_status == "fail":
        fail_msg = "測試執行失敗，請查看測試報告了解詳情"
        if html_path:
            fail_msg += f"\n報告位置: {html_path}"
        pytest.fail(fail_msg)
