# -*- coding: utf-8 -*-
"""
測試案例啟動器 (Test Case Launcher)

功能：
1. 動態載入 Excel 測資中的測試案例清單
2. 提供勾選介面與執行控制
3. 多線程執行測試，保持 UI 響應
4. 即時顯示執行結果 (Pass/Fail)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
import threading
import time
import random
import os
import subprocess
import sys
import shutil
from typing import List, Dict, Optional
from config import EnvConfig


class TestCaseLauncher:
    """測試案例啟動器主類別"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("自動化測試啟動器")
        self.root.geometry("800x700")
        
        # 測試案例資料
        self.test_cases: List[Dict[str, str]] = []  # 改為字典列表，包含 'test_case' 和 'test_name'
        self.test_vars: Dict[str, tk.BooleanVar] = {}
        self.test_status_labels: Dict[str, tk.Label] = {}
        
        # 執行狀態
        self.is_running = False
        self.execution_thread: Optional[threading.Thread] = None
        
        # 載入測試清單
        self.load_test_cases()
        
        # 建立 UI
        self.build_ui()
    
    def load_test_cases(self):
        """
        動態載入測試案例清單
        
        從 Excel 文件讀取 TestDir 工作表的 Test case 和 TestName 欄位
        保持與 TestPlan 相同的順序
        """
        try:
            excel_path = EnvConfig.TEST_PLAN_PATH
            
            # 檢查檔案是否存在
            if not os.path.exists(excel_path):
                error_msg = f"測試計劃檔案不存在: {excel_path}"
                print(f"[ERROR] {error_msg}")
                messagebox.showerror("檔案錯誤", f"無法找到測試計劃檔案：\n{error_msg}")
                self.test_cases = []
                return
            
            print(f"[INFO] 正在讀取測試計劃檔案: {excel_path}")
            
            # 讀取 Excel 的 TestDir 工作表（如果不存在，嘗試 Sheet1）
            df = None
            try:
                df = pd.read_excel(excel_path, sheet_name='TestDir')
                print(f"[INFO] 成功讀取 TestDir 工作表，共 {len(df)} 行")
            except ValueError as sheet_error:
                # 如果找不到 TestDir，嘗試 Sheet1（某些 Excel 文件可能使用 Sheet1 作為 TestDir）
                print(f"[WARN] 找不到 'TestDir' 工作表，嘗試使用 'Sheet1'...")
                try:
                    xl_file = pd.ExcelFile(excel_path)
                    available_sheets = xl_file.sheet_names
                    print(f"[INFO] 可用工作表: {', '.join(available_sheets)}")
                    
                    # 嘗試使用 Sheet1
                    if 'Sheet1' in available_sheets:
                        df = pd.read_excel(excel_path, sheet_name='Sheet1')
                        print(f"[INFO] 成功讀取 Sheet1 工作表作為 TestDir，共 {len(df)} 行")
                    else:
                        # 如果也沒有 Sheet1，使用第一個工作表
                        if available_sheets:
                            first_sheet = available_sheets[0]
                            df = pd.read_excel(excel_path, sheet_name=first_sheet)
                            print(f"[INFO] 使用第一個工作表 '{first_sheet}' 作為 TestDir，共 {len(df)} 行")
                        else:
                            error_msg = "Excel 文件中沒有任何工作表"
                            print(f"[ERROR] {error_msg}")
                            messagebox.showerror("工作表錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
                            self.test_cases = []
                            return
                except Exception as e2:
                    error_msg = f"無法讀取 Excel 文件: {str(e2)}"
                    print(f"[ERROR] {error_msg}")
                    messagebox.showerror("讀取錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
                    self.test_cases = []
                    return
            
            if df is None or df.empty:
                error_msg = "無法讀取測試計劃數據"
                print(f"[ERROR] {error_msg}")
                messagebox.showerror("讀取錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
                self.test_cases = []
                return
            
            # 檢查 TestName 欄位是否存在
            print(f"[INFO] Excel 欄位: {df.columns.tolist()}")
            if 'TestName' not in df.columns:
                error_msg = f"Excel 文件中找不到 'TestName' 欄位。可用欄位: {', '.join(df.columns.tolist())}"
                print(f"[ERROR] {error_msg}")
                messagebox.showerror("資料錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
                self.test_cases = []
                return
            
            # 檢查 Test case 欄位是否存在（如果不存在，使用空字串）
            has_test_case = 'Test case' in df.columns
            print(f"[INFO] 找到 'Test case' 欄位: {has_test_case}")
            
            # 過濾空值並保持原始順序（不反轉）
            test_cases_list = []
            for idx, row in df.iterrows():
                test_name = row.get('TestName')
                if pd.notna(test_name) and str(test_name).strip():  # 過濾空值和空白字串
                    test_case = row.get('Test case', '') if has_test_case else ''
                    test_cases_list.append({
                        'test_case': str(test_case).strip() if pd.notna(test_case) else '',
                        'test_name': str(test_name).strip()
                    })
                    print(f"[DEBUG] 載入測試案例: {test_case} - {test_name}")
            
            if not test_cases_list:
                error_msg = f"未找到任何有效的測試案例（TestName 欄位為空或無效）。共檢查 {len(df)} 行"
                print(f"[ERROR] {error_msg}")
                messagebox.showerror("資料錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
                self.test_cases = []
                return
            
            # 保持原始順序（不反轉）
            self.test_cases = test_cases_list
            # 注意：不使用 emoji，避免 cp950 編碼錯誤
            print(f"[OK] 成功載入 {len(self.test_cases)} 個測試案例")
            
        except FileNotFoundError as e:
            error_msg = str(e)
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("檔案錯誤", f"無法找到測試計劃檔案：\n{error_msg}")
            self.test_cases = []
        
        except PermissionError as e:
            error_msg = str(e)
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("權限錯誤", f"無法讀取測試計劃檔案（可能正在被其他程式使用）：\n{error_msg}")
            self.test_cases = []
        
        except ValueError as e:
            error_msg = str(e)
            print(f"[ERROR] {error_msg}")
            messagebox.showerror("資料錯誤", f"讀取測試計劃時發生錯誤：\n{error_msg}")
            self.test_cases = []
        
        except Exception as e:
            error_msg = str(e)
            import traceback
            traceback_str = traceback.format_exc()
            print(f"[ERROR] 未預期的錯誤: {error_msg}")
            print(f"[ERROR] 詳細錯誤:\n{traceback_str}")
            messagebox.showerror("載入失敗", f"載入測試計劃時發生未預期的錯誤：\n{error_msg}\n\n詳細信息請查看終端輸出")
            self.test_cases = []
    
    def build_ui(self):
        """建立 UI 介面"""
        
        # === 標題區域 ===
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="自動化測試啟動器", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # === 控制按鈕區域（全選/全不選） ===
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        btn_select_all = ttk.Button(
            control_frame,
            text="全選",
            command=self.select_all
        )
        btn_select_all.pack(side=tk.LEFT, padx=5)
        
        btn_deselect_all = ttk.Button(
            control_frame,
            text="全不選",
            command=self.deselect_all
        )
        btn_deselect_all.pack(side=tk.LEFT, padx=5)
        
        # === 測試案例清單區域（可滾動） ===
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 建立滾動條和畫布
        canvas = tk.Canvas(list_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 建立測試案例複選框
        if not self.test_cases:
            no_test_label = ttk.Label(
                scrollable_frame,
                text="❌ 未載入任何測試案例",
                foreground="red"
            )
            no_test_label.pack(pady=10)
        else:
            for test_info in self.test_cases:
                # 建立每行的容器框架
                item_frame = ttk.Frame(scrollable_frame)
                item_frame.pack(fill=tk.X, padx=5, pady=2)
                
                # 提取 test_case 和 test_name
                test_case = test_info.get('test_case', '')
                test_name = test_info.get('test_name', '')
                
                # 建立複選框文本：如果有 Test case，顯示 "Test case - TestName"，否則只顯示 TestName
                if test_case:
                    checkbox_text = f"{test_case} - {test_name}"
                else:
                    checkbox_text = test_name
                
                # 建立複選框
                var = tk.BooleanVar(value=False)
                self.test_vars[test_name] = var  # 仍然使用 test_name 作為鍵
                
                checkbox = ttk.Checkbutton(
                    item_frame,
                    text=checkbox_text,
                    variable=var,
                    width=70  # 增加寬度以容納 Test case
                )
                checkbox.pack(side=tk.LEFT, anchor=tk.W)
                
                # 建立狀態標籤（預留顯示 Pass/Fail）
                status_label = ttk.Label(
                    item_frame,
                    text="",
                    width=10,
                    anchor=tk.CENTER
                )
                status_label.pack(side=tk.LEFT, padx=10)
                self.test_status_labels[test_name] = status_label  # 仍然使用 test_name 作為鍵
        
        # 配置滾動區域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 滑鼠滾輪支援（只綁定到 canvas 和 scrollable_frame，不要使用 bind_all）
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 只綁定到 canvas 和 scrollable_frame，避免影響其他區域（如 log 區域）
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # === 執行按鈕區域 ===
        run_frame = ttk.Frame(self.root, padding="10")
        run_frame.pack(fill=tk.X)
        
        self.btn_run = ttk.Button(
            run_frame,
            text="▶ Run",
            command=self.run_tests,
            state=tk.NORMAL if self.test_cases else tk.DISABLED
        )
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        btn_stop = ttk.Button(
            run_frame,
            text="⏹ Stop",
            command=self.stop_tests,
            state=tk.DISABLED
        )
        btn_stop.pack(side=tk.LEFT, padx=5)
        self.btn_stop = btn_stop
        
        # === Log 顯示區域 ===
        log_frame = ttk.LabelFrame(self.root, text="執行日誌", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化日誌
        self.log("=" * 60)
        self.log("測試案例啟動器已就緒")
        self.log(f"已載入 {len(self.test_cases)} 個測試案例")
        self.log("=" * 60)
    
    def select_all(self):
        """全選所有測試案例"""
        for var in self.test_vars.values():
            var.set(True)
        self.log("已全選所有測試案例")
    
    def deselect_all(self):
        """全不選所有測試案例"""
        for var in self.test_vars.values():
            var.set(False)
        # 清除所有狀態標籤
        for label in self.test_status_labels.values():
            label.config(text="", background="")
        self.log("已全不選所有測試案例")
    
    def log(self, message: str, level: str = "INFO"):
        """
        記錄日誌訊息
        
        :param message: 日誌內容
        :param level: 日誌級別 (INFO, ERROR, WARNING)
        """
        timestamp = time.strftime("%H:%M:%S")
        
        # 根據級別設定顏色
        color_map = {
            "INFO": "black",
            "ERROR": "red",
            "WARNING": "orange"
        }
        color = color_map.get(level, "black")
        
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.tag_add(level, f"end-{len(log_entry)}c", tk.END)
        self.log_text.tag_config(level, foreground=color)
        self.log_text.see(tk.END)
        
        # 同時輸出到控制台（移除 emoji 避免 cp950 編碼錯誤）
        try:
            # 將 emoji 替換為 ASCII 字符，避免編碼錯誤
            safe_message = message.replace("✓", "[PASS]").replace("✗", "[FAIL]").replace("⚠️", "[WARN]").replace("⏳", "[RUN]")
            safe_log_entry = f"[{timestamp}] [{level}] {safe_message}"
            print(safe_log_entry)
        except UnicodeEncodeError:
            # 如果仍然有編碼錯誤，使用 ASCII 安全模式
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            safe_log_entry = f"[{timestamp}] [{level}] {safe_message}"
            print(safe_log_entry)
    
    def update_status(self, test_name: str, status: str):
        """
        更新測試案例的執行狀態顯示
        
        :param test_name: 測試案例名稱
        :param status: 狀態 ('pass', 'fail', 'running', '')
        """
        if test_name not in self.test_status_labels:
            return
        
        label = self.test_status_labels[test_name]
        
        if status == "pass":
            label.config(text="✓ Pass", foreground="green", font=("Arial", 9, "bold"))
        elif status == "fail":
            label.config(text="✗ Fail", foreground="red", font=("Arial", 9, "bold"))
        elif status == "running":
            label.config(text="⏳ Running...", foreground="blue")
        else:
            label.config(text="", foreground="black")
        
        # 強制更新 UI
        self.root.update_idletasks()
    
    def run_tests(self):
        """啟動測試執行（使用多線程）"""
        
        # 檢查是否有選中的測試
        selected_tests = [
            name for name, var in self.test_vars.items() 
            if var.get()
        ]
        
        if not selected_tests:
            messagebox.showwarning("提示", "請至少選擇一個測試案例")
            return
        
        if self.is_running:
            messagebox.showinfo("提示", "測試正在執行中，請等待完成或點擊 Stop")
            return
        
        # 清除之前的狀態
        for test_name in selected_tests:
            self.update_status(test_name, "")
        
        # 更新按鈕狀態
        self.btn_run.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.is_running = True
        
        # 在背景線程中執行測試
        self.execution_thread = threading.Thread(
            target=self._execute_tests_worker,
            args=(selected_tests,),
            daemon=True
        )
        self.execution_thread.start()
    
    def _execute_tests_worker(self, test_names: List[str]):
        """
        測試執行工作函數（在背景線程中執行）
        
        :param test_names: 要執行的測試案例列表
        """
        total = len(test_names)
        
        self.log(f"開始執行 {total} 個測試案例...", "INFO")
        
        for idx, test_name in enumerate(test_names, 1):
            if not self.is_running:
                self.log("測試執行已中斷", "WARNING")
                break
            
            # 更新狀態為執行中
            self.root.after(0, self.update_status, test_name, "running")
            self.log(f"[{idx}/{total}] 執行測試: {test_name}", "INFO")
            
            try:
                # 執行測試邏輯（模擬）
                result = self.execute_test_logic(test_name)
                
                # 更新狀態顯示
                if result:
                    self.root.after(0, self.update_status, test_name, "pass")
                    self.log(f"✓ {test_name} - Pass", "INFO")
                else:
                    self.root.after(0, self.update_status, test_name, "fail")
                    self.log(f"✗ {test_name} - Fail", "ERROR")
            
            except Exception as e:
                self.root.after(0, self.update_status, test_name, "fail")
                self.log(f"✗ {test_name} - 執行時發生錯誤: {str(e)}", "ERROR")
        
        # 執行完成
        self.is_running = False
        self.root.after(0, self._execution_completed)
        
        self.log("=" * 60)
        self.log("所有測試執行完成", "INFO")
    
    def execute_test_logic(self, test_name: str) -> bool:
        """
        執行測試邏輯
        
        可以選擇：
        1. 模擬模式：隨機產生 Pass/Fail（用於演示）
        2. 真實模式：調用 pytest 執行實際測試（使用 subprocess）
        
        :param test_name: 測試案例名稱
        :return: True (Pass) / False (Fail)
        """
        # ===== 模式選擇 =====
        # True = 模擬模式（快速演示）
        # False = 真實模式（實際執行 pytest）
        USE_MOCK_MODE = False  # 預設使用真實測試執行
        
        if USE_MOCK_MODE:
            # ===== 選項 1：模擬模式（用於演示和快速測試 UI）=====
            # 模擬執行時間（1-3 秒隨機）
            execution_time = random.uniform(1.0, 3.0)
            time.sleep(execution_time)
            
            # 模擬隨機結果（90% 通過率）
            result = random.random() < 0.9
            return result
        
        else:
            # ===== 選項 2：真實模式（使用 subprocess 執行 pytest）=====
            try:
                # 取得專案根目錄（用於確定測試文件路徑）
                project_root = EnvConfig.PROJECT_ROOT
                test_file = os.path.join(project_root, "tests", "test_runner.py")
                
                # 檢查測試文件是否存在
                if not os.path.exists(test_file):
                    self.log(f"⚠️ 找不到測試文件: {test_file}", "WARNING")
                    return False
                
                # 確定 Python 解釋器路徑
                # 如果是在打包的 EXE 環境中，sys.executable 指向 EXE 檔案
                # 需要找到真正的 Python 解釋器
                if getattr(sys, 'frozen', False):
                    # 打包環境：嘗試找到 Python 解釋器
                    # 方法 1: 使用 shutil.which 查找 python 命令（在 PATH 中）
                    python_exe = shutil.which("python") or shutil.which("python.exe")
                    
                    # 方法 2: 如果找不到，檢查常見的 Python 安裝位置
                    if not python_exe:
                        possible_python_paths = [
                            r"C:\Python314\python.exe",
                            r"C:\Python313\python.exe",
                            r"C:\Python312\python.exe",
                            r"C:\Users\usert\AppData\Local\Programs\Python\Python314\python.exe",
                            r"C:\Users\usert\AppData\Local\Programs\Python\Python313\python.exe",
                            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python314\python.exe"),
                            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python313\python.exe"),
                        ]
                        
                        for path in possible_python_paths:
                            if os.path.exists(path):
                                python_exe = path
                                break
                    
                    # 方法 3: 如果還是找不到，使用 "python" 命令（假設在 PATH 中）
                    if not python_exe:
                        python_exe = "python"
                        self.log(f"⚠️ 使用 PATH 中的 'python' 命令", "WARNING")
                    else:
                        self.log(f"找到 Python 解釋器: {python_exe}", "INFO")
                else:
                    # 正常運行：使用當前 Python 解釋器
                    python_exe = sys.executable
                    self.log(f"使用當前 Python 解釋器: {python_exe}", "INFO")
                
                # 構建 pytest 命令
                # 注意：test_runner.py 期望 --test_name 參數格式為：--test_name <值>（空格分隔，不是等號）
                cmd = [
                    python_exe,
                    "-m", "pytest",
                    test_file,
                    "--test_name", test_name,  # 使用空格分隔，而不是 --test_name=值
                    "-v",
                    "-s",
                    "--tb=short"  # 簡短的錯誤追蹤
                ]
                
                # 記錄執行信息（包括工作目錄）
                self.log(f"執行命令: {' '.join(cmd)}", "INFO")
                self.log(f"工作目錄: {project_root}", "INFO")
                
                # 驗證工作目錄是否存在
                if not os.path.exists(project_root):
                    self.log(f"錯誤: 工作目錄不存在: {project_root}", "ERROR")
                    return False
                
                # 【重要】先創建臨時 log 文件，在 subprocess 執行前設置環境變數
                # 這樣 subprocess 才能讀取到正確的 log 文件路徑
                import tempfile
                import datetime
                temp_log_file = None
                try:
                    # 創建臨時文件（在 subprocess 執行前）
                    temp_dir = tempfile.gettempdir()
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    temp_log_file = os.path.join(temp_dir, f"test_terminal_{timestamp}.log")
                    
                    # 先創建文件並寫入標題信息
                    with open(temp_log_file, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write("=" * 80 + "\n")
                        f.write(f"測試案例: {test_name}\n")
                        f.write(f"執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"執行命令: {' '.join(cmd)}\n")
                        f.write(f"工作目錄: {project_root}\n")
                        f.write("=" * 80 + "\n\n")
                    
                    self.log(f"Terminal log 文件已創建: {temp_log_file}", "INFO")
                except Exception as e:
                    self.log(f"創建 Terminal log 文件失敗: {e}", "WARNING")
                    temp_log_file = None
                
                # 準備環境變數（確保模組可以被找到）
                env = os.environ.copy()
                # 添加專案根目錄到 PYTHONPATH
                pythonpath = env.get('PYTHONPATH', '')
                if pythonpath:
                    env['PYTHONPATH'] = f"{project_root}{os.pathsep}{pythonpath}"
                else:
                    env['PYTHONPATH'] = project_root
                
                # 【重要】在 subprocess 執行前設置 TEST_TERMINAL_LOG 環境變數
                # 這樣 test_runner.py 才能讀取到正確的 log 文件路徑
                if temp_log_file:
                    env['TEST_TERMINAL_LOG'] = temp_log_file
                
                self.log(f"PYTHONPATH: {env['PYTHONPATH']}", "INFO")
                if temp_log_file:
                    self.log(f"TEST_TERMINAL_LOG: {temp_log_file}", "INFO")
                
                # 使用 subprocess 執行 pytest
                # 將 stdout 和 stderr 直接重定向到文件，確保捕獲所有輸出（包括 pytest -s 的輸出）
                result = None
                if temp_log_file:
                    try:
                        # 打開文件用於實時寫入 stdout 和 stderr
                        with open(temp_log_file, 'a', encoding='utf-8', errors='ignore', buffering=1) as log_file:
                            # 執行 subprocess，將 stdout 和 stderr 直接寫入文件（buffering=1 表示行緩衝）
                            result = subprocess.run(
                                cmd,
                                cwd=project_root,  # 設置工作目錄為專案根目錄
                                env=env,  # 使用修改後的環境變數（包含 TEST_TERMINAL_LOG）
                                stdout=log_file,  # 直接寫入文件
                                stderr=subprocess.STDOUT,  # 將 stderr 也合併到 stdout
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                timeout=300  # 5 分鐘超時
                            )
                            
                            # 寫入結尾信息
                            log_file.write("\n" + "=" * 80 + "\n")
                            log_file.write(f"退出碼: {result.returncode}\n")
                            log_file.write(f"執行結果: {'成功' if result.returncode == 0 else '失敗'}\n")
                            log_file.write("=" * 80 + "\n")
                        
                        # 執行完成後，讀取文件內容用於 UI 顯示
                        try:
                            with open(temp_log_file, 'r', encoding='utf-8', errors='ignore') as log_file_read:
                                log_content = log_file_read.read()
                                # 提取測試輸出部分（跳過標題，從 "=" 分隔符之後開始）
                                if "退出碼:" in log_content:
                                    # 提取退出碼之前的內容作為輸出
                                    parts = log_content.split("退出碼:")
                                    if len(parts) > 0:
                                        stdout_content = parts[0].split("=" * 80 + "\n", 1)[-1] if "=" * 80 in parts[0] else parts[0]
                                    else:
                                        stdout_content = log_content
                                else:
                                    stdout_content = log_content.split("=" * 80 + "\n", 1)[-1] if "=" * 80 in log_content else log_content
                                
                                # 用於 UI 顯示的預覽
                                if stdout_content.strip():
                                    output_preview = stdout_content[:2000] if len(stdout_content) > 2000 else stdout_content
                                    self.log(f"測試輸出:\n{output_preview}", "INFO")
                        except Exception as read_e:
                            self.log(f"讀取 Terminal log 失敗: {read_e}", "WARNING")
                        
                        self.log(f"Terminal log 已保存: {temp_log_file}", "INFO")
                    except Exception as e:
                        self.log(f"執行測試或保存 Terminal log 失敗: {e}", "WARNING")
                        import traceback
                        self.log(f"錯誤詳情: {traceback.format_exc()[:500]}", "ERROR")
                        # 如果失敗，回退到 capture_output 模式
                        result = subprocess.run(
                            cmd,
                            cwd=project_root,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            timeout=300
                        )
                        # 如果失敗但仍需要保存 log
                        if temp_log_file and result:
                            try:
                                with open(temp_log_file, 'a', encoding='utf-8', errors='ignore') as f:
                                    if result.stdout:
                                        f.write("[STDOUT]\n")
                                        f.write("-" * 80 + "\n")
                                        f.write(result.stdout)
                                    if result.stderr:
                                        f.write("\n[STDERR]\n")
                                        f.write("-" * 80 + "\n")
                                        f.write(result.stderr)
                                    f.write(f"\n退出碼: {result.returncode}\n")
                            except:
                                pass
                else:
                    # 如果沒有 temp_log_file，使用 capture_output
                    result = subprocess.run(
                        cmd,
                        cwd=project_root,
                        env=env,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        timeout=300
                    )
                
                # 記錄輸出（限制長度，用於 UI 顯示）
                # 如果使用文件重定向，result.stdout 和 result.stderr 會是 None，需要從文件讀取
                if result and not temp_log_file:
                    # 只有在使用 capture_output 時才會有 result.stdout/stderr
                    if result.stdout:
                        output_preview = result.stdout[:2000]  # 增加長度到 2000 字元
                        self.log(f"測試輸出:\n{output_preview}", "INFO")
                    
                    if result.stderr:
                        error_preview = result.stderr[:1000]  # 增加長度到 1000 字元
                        # 記錄所有 stderr 輸出（不只是 ERROR/FAILED）
                        self.log(f"測試錯誤輸出:\n{error_preview}", "ERROR")
                
                # 檢查退出碼：0=成功，非0=失敗
                success = (result.returncode == 0) if result else False
                
                if success:
                    self.log(f"✓ pytest 執行成功 (退出碼: {result.returncode})", "INFO")
                else:
                    self.log(f"✗ pytest 執行失敗 (退出碼: {result.returncode})", "ERROR")
                
                return success
                
            except subprocess.TimeoutExpired:
                self.log(f"✗ 測試執行超時（超過 5 分鐘）", "ERROR")
                return False
            except FileNotFoundError:
                self.log(f"⚠️ 找不到 Python 解釋器或 pytest: {python_exe}", "WARNING")
                return False
            except Exception as e:
                self.log(f"✗ 執行測試時發生錯誤: {str(e)}", "ERROR")
                import traceback
                self.log(f"錯誤詳情:\n{traceback.format_exc()[:500]}", "ERROR")
                return False
    
    def stop_tests(self):
        """停止測試執行"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.log("正在停止測試執行...", "WARNING")
        
        # 等待執行線程結束（最多等待 2 秒）
        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=2.0)
    
    def _execution_completed(self):
        """執行完成後的回調（在主線程中執行）"""
        self.btn_run.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)


def main():
    """主函數：啟動測試案例啟動器"""
    root = tk.Tk()
    app = TestCaseLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
