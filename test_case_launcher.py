# -*- coding: utf-8 -*-
"""
測試案例啟動器 (Test Case Launcher)

功能：
1. 動態載入 Excel 測資中的測試案例清單
2. 提供勾選介面與執行控制
3. 多線程執行測試，保持 UI 響應
4. 即時顯示執行結果 (Pass/Fail)
5. Appium Server 控制（啟動/停止）
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
import datetime
import socket
import platform
import io
from typing import List, Dict, Optional
from config import EnvConfig


class AppiumManager:
    """Appium Server 管理器"""
    
    def __init__(self, log_callback=None):
        """
        初始化 AppiumManager
        
        Args:
            log_callback: 日誌回調函數，用於輸出日誌訊息
        """
        self.appium_process: Optional[subprocess.Popen] = None
        self.appium_port = 4723
        self.log_callback = log_callback
        self.is_running = False
        self.log_file: Optional[io.TextIOWrapper] = None
    
    def log(self, message: str, level: str = "INFO"):
        """輸出日誌"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    
    def check_port_in_use(self, port: int) -> bool:
        """
        檢查指定端口是否被佔用
        
        Args:
            port: 要檢查的端口號
            
        Returns:
            bool: True 表示端口被佔用，False 表示端口可用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception as e:
            self.log(f"檢查端口 {port} 時發生錯誤: {e}", "WARNING")
            return False
    
    def is_appium_running(self) -> bool:
        """
        檢查 Appium Server 是否正在運行
        
        Returns:
            bool: True 表示 Appium 正在運行，False 表示未運行
        """
        return self.check_port_in_use(self.appium_port)
    
    def start_appium(self) -> bool:
        """
        啟動 Appium Server（在背景執行）
        
        Returns:
            bool: 啟動是否成功
        """
        if self.is_appium_running():
            self.log("Appium Server 已經在運行中", "INFO")
            self.is_running = True
            return True
        
        try:
            # 查找 appium 命令
            appium_cmd = shutil.which("appium")
            if not appium_cmd:
                # 嘗試常見的安裝位置
                possible_paths = [
                    r"C:\Users\usert\AppData\Roaming\npm\appium.cmd",
                    r"C:\Users\usert\AppData\Local\npm\appium.cmd",
                    os.path.expanduser(r"~\AppData\Roaming\npm\appium.cmd"),
                    os.path.expanduser(r"~\AppData\Local\npm\appium.cmd"),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        appium_cmd = path
                        break
            
            if not appium_cmd:
                self.log("找不到 Appium 命令，請確認 Appium 已安裝並在 PATH 中", "ERROR")
                return False
            
            self.log(f"啟動 Appium Server: {appium_cmd}", "INFO")
            
            # 1. 檢查並設置 Android SDK 環境變數
            env = os.environ.copy()
            android_home = env.get('ANDROID_HOME') or env.get('ANDROID_SDK_ROOT')
            
            if not android_home:
                # 嘗試自動查找 Android SDK
                possible_sdk_paths = [
                    os.path.expanduser(r"~\AppData\Local\Android\Sdk"),
                    os.path.expanduser(r"~\Android\Sdk"),
                    r"C:\Users\usert\AppData\Local\Android\Sdk",
                    r"C:\Android\Sdk",
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk'),
                ]
                
                for sdk_path in possible_sdk_paths:
                    if os.path.exists(sdk_path) and os.path.isdir(sdk_path):
                        # 檢查是否包含 platform-tools（確認是有效的 SDK）
                        platform_tools = os.path.join(sdk_path, 'platform-tools')
                        if os.path.exists(platform_tools):
                            android_home = sdk_path
                            self.log(f"[診斷] 自動檢測到 Android SDK: {android_home}", "INFO")
                            break
                
                if android_home:
                    env['ANDROID_HOME'] = android_home
                    env['ANDROID_SDK_ROOT'] = android_home
                    self.log(f"[診斷] 已設置 ANDROID_HOME={android_home}", "INFO")
                else:
                    self.log("[WARN] 無法找到 Android SDK，Appium 可能無法正常工作", "WARNING")
                    self.log("[診斷] 請設置 ANDROID_HOME 或 ANDROID_SDK_ROOT 環境變數", "WARNING")
                    self.log("[診斷] 常見位置: %LOCALAPPDATA%\\Android\\Sdk", "WARNING")
            else:
                self.log(f"[診斷] 使用現有的 Android SDK: {android_home}", "INFO")
            
            # 2. 準備一個 Log 檔案來接收輸出
            log_file_path = os.path.join(os.getcwd(), "appium_server_output.log")
            self.log_file = open(log_file_path, "w", encoding="utf-8")
            self.log(f"Appium Server 日誌將寫入: {log_file_path}", "INFO")
            
            # 3. 啟動 Appium，把輸出導向檔案 (這樣就不會卡死了)
            # 加上 --base-path /wd/hub 以確保相容性
            cmd_args = [appium_cmd, "--address", "127.0.0.1", "--port", str(self.appium_port), "--base-path", "/wd/hub"]
            
            self.log(f"[診斷] 啟動命令: {' '.join(cmd_args)}", "INFO")
            if android_home:
                self.log(f"[診斷] 環境變數: ANDROID_HOME={android_home}", "INFO")
            
            self.appium_process = subprocess.Popen(
                cmd_args,
                stdout=self.log_file,  # <--- 改成寫入檔案
                stderr=self.log_file,  # <--- 改成寫入檔案
                text=True,
                encoding='utf-8',
                errors='ignore',
                env=env,  # 傳遞環境變數
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            # 等待幾秒確認 Appium 是否成功啟動
            max_wait = 10  # 最多等待 10 秒
            wait_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_interval)
                waited += wait_interval
                
                if self.is_appium_running():
                    self.is_running = True
                    self.log(f"Appium Server 啟動成功（等待 {waited:.1f} 秒）", "INFO")
                    return True
                
                # 檢查進程是否還在運行
                if self.appium_process.poll() is not None:
                    # 進程已結束，讀取錯誤信息（從日誌文件）
                    if self.log_file:
                        self.log_file.flush()
                        try:
                            with open(log_file_path, "r", encoding="utf-8", errors='ignore') as f:
                                log_content = f.read()
                                if log_content:
                                    error_msg = log_content[-500:]  # 讀取最後 500 字符
                                    self.log(f"Appium Server 啟動失敗: {error_msg}", "ERROR")
                        except Exception:
                            self.log("Appium Server 啟動失敗（無法讀取日誌）", "ERROR")
                    else:
                        self.log("Appium Server 啟動失敗（進程已結束）", "ERROR")
                    return False
            
            # 如果等待超時但進程還在運行，可能正在啟動中
            if self.appium_process.poll() is None:
                self.log("Appium Server 正在啟動中（進程運行中，但端口尚未就緒）", "WARNING")
                self.is_running = True
                return True
            else:
                self.log("Appium Server 啟動超時", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"啟動 Appium Server 時發生錯誤: {e}", "ERROR")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()[:300]}", "ERROR")
            return False
    
    def stop_appium(self) -> bool:
        """
        停止 Appium Server
        
        Returns:
            bool: 停止是否成功
        """
        try:
            # 方法 1: 如果我們啟動了進程，先嘗試終止它
            if self.appium_process and self.appium_process.poll() is None:
                self.log("正在終止 Appium 進程...", "INFO")
                self.appium_process.terminate()
                try:
                    self.appium_process.wait(timeout=5)
                    self.log("Appium 進程已終止", "INFO")
                    self.appium_process = None
                    self.is_running = False
                    # 關閉日誌文件
                    if self.log_file:
                        try:
                            self.log_file.close()
                        except Exception:
                            pass
                        self.log_file = None
                    return True
                except subprocess.TimeoutExpired:
                    self.log("進程未響應 terminate，強制終止...", "WARNING")
                    self.appium_process.kill()
                    self.appium_process.wait()
                    self.appium_process = None
                    self.is_running = False
                    # 關閉日誌文件
                    if self.log_file:
                        try:
                            self.log_file.close()
                        except Exception:
                            pass
                        self.log_file = None
                    return True
            
            # 方法 2: 如果進程已經結束或我們沒有進程引用，嘗試殺掉所有 Node.exe/Appium 進程
            self.log("嘗試終止所有 Appium/Node 進程...", "INFO")
            
            if platform.system() == 'Windows':
                # Windows: 使用 taskkill 命令
                try:
                    # 殺掉所有 node.exe 進程（Appium 通常運行在 Node.js 中）
                    subprocess.run(
                        ['taskkill', '/F', '/IM', 'node.exe'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10
                    )
                    self.log("已終止所有 Node.exe 進程", "INFO")
                except Exception as e:
                    self.log(f"終止 Node.exe 進程時發生錯誤: {e}", "WARNING")
                
                # 也嘗試殺掉 appium 進程（如果有的話）
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/IM', 'appium.exe'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10
                    )
                except:
                    pass  # 如果沒有 appium.exe 進程，忽略錯誤
            else:
                # Linux/Mac: 使用 pkill 命令
                try:
                    subprocess.run(
                        ['pkill', '-f', 'appium'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10
                    )
                    self.log("已終止所有 Appium 進程", "INFO")
                except Exception as e:
                    self.log(f"終止 Appium 進程時發生錯誤: {e}", "WARNING")
            
            # 等待一下，然後檢查端口是否釋放
            time.sleep(2)
            if not self.is_appium_running():
                self.is_running = False
                # 關閉日誌文件
                if self.log_file:
                    try:
                        self.log_file.close()
                    except Exception:
                        pass
                    self.log_file = None
                self.log("Appium Server 已停止", "INFO")
                return True
            else:
                self.log("警告：Appium Server 可能仍在運行（端口仍被佔用）", "WARNING")
                # 即使端口仍被佔用，也嘗試關閉日誌文件
                if self.log_file:
                    try:
                        self.log_file.close()
                    except Exception:
                        pass
                    self.log_file = None
                return False
                
        except Exception as e:
            self.log(f"停止 Appium Server 時發生錯誤: {e}", "ERROR")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()[:300]}", "ERROR")
            # 發生錯誤時也嘗試關閉日誌文件
            if self.log_file:
                try:
                    self.log_file.close()
                except Exception:
                    pass
                self.log_file = None
            return False


class TestCaseLauncher:
    """測試案例啟動器主類別"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Nx Witness 自動化測試主控台")
        self.root.geometry("900x800")
        
        # 測試案例資料
        self.test_cases: List[Dict[str, str]] = []
        self.test_vars: Dict[str, tk.BooleanVar] = {}
        self.test_status_labels: Dict[str, tk.Label] = {}
        
        # 執行狀態
        self.is_running = False
        self.execution_thread: Optional[threading.Thread] = None
        
        # 追蹤當前執行的測試案例和 log 文件
        self.current_test_name: Optional[str] = None
        self.current_log_file: Optional[str] = None
        
        # 追蹤當前執行的 subprocess，用於強制終止
        self.current_process: Optional[subprocess.Popen] = None
        
        # Appium 管理器
        self.appium_manager = AppiumManager(log_callback=self.log)
        
        # 載入測試清單
        self.load_test_cases()
        
        # 建立 UI
        self.build_ui()
        
        # 啟動時檢查 Appium 狀態
        self.check_appium_status()
    
    def check_appium_status(self):
        """檢查 Appium 狀態並更新按鈕"""
        def _check():
            is_running = self.appium_manager.is_appium_running()
            self.appium_manager.is_running = is_running
            self.root.after(0, self._update_appium_button_state, is_running)
        
        # 在背景線程中檢查，避免凍結 UI
        threading.Thread(target=_check, daemon=True).start()
    
    def _update_appium_button_state(self, is_running: bool):
        """更新 Appium 按鈕狀態"""
        if is_running:
            self.btn_appium.config(
                text="停止 Appium",
                bg="#ff4444",  # 紅色
                fg="white",
                activebackground="#ff6666",  # 滑鼠懸停時的顏色
                activeforeground="white",
                state=tk.NORMAL
            )
            self.appium_status_label.config(
                text="[運行中]",
                foreground="green",
                font=("Arial", 10, "bold")
            )
        else:
            self.btn_appium.config(
                text="啟動 Appium",
                bg="#44ff44",  # 綠色
                fg="black",
                activebackground="#66ff66",  # 滑鼠懸停時的顏色
                activeforeground="black",
                state=tk.NORMAL
            )
            self.appium_status_label.config(
                text="[已停止]",
                foreground="red",
                font=("Arial", 10, "bold")
            )
    
    def toggle_appium(self):
        """切換 Appium Server 狀態"""
        def _toggle():
            # 先檢查當前實際狀態（而不是依賴緩存的 is_running）
            current_status = self.appium_manager.is_appium_running()
            
            if current_status:
                # 停止 Appium
                self.log("正在停止 Appium Server...", "INFO")
                self.root.after(0, lambda: self.btn_appium.config(state=tk.DISABLED))
                success = self.appium_manager.stop_appium()
                # 再次檢查實際狀態
                final_status = self.appium_manager.is_appium_running()
                self.root.after(0, self._update_appium_button_state, final_status)
                if success:
                    self.log("Appium Server 已停止", "INFO")
                else:
                    self.log("停止 Appium Server 失敗", "ERROR")
                self.root.after(0, lambda: self.btn_appium.config(state=tk.NORMAL))
            else:
                # 啟動 Appium
                self.log("正在啟動 Appium Server...", "INFO")
                self.root.after(0, lambda: self.btn_appium.config(state=tk.DISABLED))
                success = self.appium_manager.start_appium()
                # 再次檢查實際狀態
                final_status = self.appium_manager.is_appium_running()
                self.root.after(0, self._update_appium_button_state, final_status)
                if success:
                    self.log("Appium Server 已啟動", "INFO")
                else:
                    self.log("啟動 Appium Server 失敗", "ERROR")
                self.root.after(0, lambda: self.btn_appium.config(state=tk.NORMAL))
        
        # 在背景線程中執行，避免凍結 UI
        threading.Thread(target=_toggle, daemon=True).start()
    
    def check_test_needs_mobile(self, test_name: str) -> bool:
        """
        檢查測試是否需要 Mobile 測試（通過檢查 Excel 的 Translate 工作表）
        
        Args:
            test_name: 測試案例名稱
            
        Returns:
            bool: True 表示需要 Mobile 測試，False 表示不需要
        """
        try:
            excel_path = EnvConfig.TEST_PLAN_PATH
            if not os.path.exists(excel_path):
                return False
            
            # 讀取 TestDir 工作表，找到測試案例的 FunctionalClassification
            dir_df = pd.read_excel(excel_path, sheet_name="TestDir")
            test_row = dir_df[dir_df['TestName'] == test_name]
            
            if test_row.empty:
                return False
            
            functional_class = test_row.iloc[0].get('FunctionalClassification')
            if pd.isna(functional_class):
                return False
            
            # 讀取對應的功能分類工作表
            case_df = pd.read_excel(excel_path, sheet_name=str(functional_class))
            steps_df = case_df[case_df['TestName'] == test_name]
            
            # 讀取 Translate 工作表
            translate_df = pd.read_excel(excel_path, sheet_name="Translate")
            
            # 檢查是否有任何步驟使用 nx_mobile ActionKey
            for _, step_row in steps_df.iterrows():
                flow_name = step_row.get('FlowName')
                if pd.notna(flow_name):
                    translate_row = translate_df[translate_df['FlowName'] == flow_name]
                    if not translate_row.empty and translate_row.iloc[0].get('ActionKey') == 'nx_mobile':
                        return True
            
            return False
            
        except Exception as e:
            self.log(f"檢查測試是否需要 Mobile 時發生錯誤: {e}", "WARNING")
            return False
    
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
                # 如果找不到 TestDir，嘗試 Sheet1
                print(f"[WARN] 找不到 'TestDir' 工作表，嘗試使用 'Sheet1'...")
                try:
                    xl_file = pd.ExcelFile(excel_path)
                    available_sheets = xl_file.sheet_names
                    print(f"[INFO] 可用工作表: {', '.join(available_sheets)}")
                    
                    if 'Sheet1' in available_sheets:
                        df = pd.read_excel(excel_path, sheet_name='Sheet1')
                        print(f"[INFO] 成功讀取 Sheet1 工作表作為 TestDir，共 {len(df)} 行")
                    else:
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
            
            # 檢查 Test case 欄位是否存在
            has_test_case = 'Test case' in df.columns
            print(f"[INFO] 找到 'Test case' 欄位: {has_test_case}")
            
            # 過濾空值並保持原始順序
            test_cases_list = []
            for idx, row in df.iterrows():
                test_name = row.get('TestName')
                if pd.notna(test_name) and str(test_name).strip():
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
            
            self.test_cases = test_cases_list
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
            text="Nx Witness 自動化測試主控台", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # === Appium 控制區（上方） ===
        appium_frame = ttk.LabelFrame(self.root, text="Appium 控制區", padding="10")
        appium_frame.pack(fill=tk.X, padx=10, pady=5)
        
        appium_control_frame = ttk.Frame(appium_frame)
        appium_control_frame.pack(fill=tk.X)
        
        # Appium 控制按鈕（開關按鈕）
        # 使用 tk.Button 而不是 ttk.Button，以便更好地控制顏色
        self.btn_appium = tk.Button(
            appium_control_frame,
            text="啟動 Appium",
            command=self.toggle_appium,
            font=("Arial", 11, "bold"),
            bg="#44ff44",  # 綠色（未運行）
            fg="black",
            activebackground="#66ff66",  # 滑鼠懸停時的顏色
            activeforeground="black",
            relief=tk.RAISED,
            borderwidth=2,
            width=15,
            height=2,
            cursor="hand2"
        )
        self.btn_appium.pack(side=tk.LEFT, padx=5)
        
        # Appium 狀態標籤
        self.appium_status_label = ttk.Label(
            appium_control_frame,
            text="[檢查中...]",
            font=("Arial", 10),
            foreground="gray"
        )
        self.appium_status_label.pack(side=tk.LEFT, padx=10)
        
        # === 測試執行區（下方） ===
        test_frame = ttk.LabelFrame(self.root, text="測試執行區", padding="10")
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # === 控制按鈕區域（全選/全不選） ===
        control_frame = ttk.Frame(test_frame, padding="5")
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
        list_frame = ttk.Frame(test_frame, padding="5")
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
                text="[ERROR] 未載入任何測試案例",
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
                
                # 建立複選框文本
                if test_case:
                    checkbox_text = f"{test_case} - {test_name}"
                else:
                    checkbox_text = test_name
                
                # 建立複選框
                var = tk.BooleanVar(value=False)
                self.test_vars[test_name] = var
                
                checkbox = ttk.Checkbutton(
                    item_frame,
                    text=checkbox_text,
                    variable=var,
                    width=70
                )
                checkbox.pack(side=tk.LEFT, anchor=tk.W)
                
                # 建立狀態標籤
                status_label = ttk.Label(
                    item_frame,
                    text="",
                    width=10,
                    anchor=tk.CENTER
                )
                status_label.pack(side=tk.LEFT, padx=10)
                self.test_status_labels[test_name] = status_label
        
        # 配置滾動區域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 滑鼠滾輪支援
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # === 執行按鈕區域 ===
        run_frame = ttk.Frame(test_frame, padding="5")
        run_frame.pack(fill=tk.X)
        
        self.btn_run = ttk.Button(
            run_frame,
            text="開始執行測試",
            command=self.run_tests,
            state=tk.NORMAL if self.test_cases else tk.DISABLED
        )
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        btn_stop = ttk.Button(
            run_frame,
            text="停止測試",
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
            safe_message = message.replace("✓", "[PASS]").replace("✗", "[FAIL]").replace("⚠️", "[WARN]").replace("⏳", "[RUN]")
            safe_log_entry = f"[{timestamp}] [{level}] {safe_message}"
            print(safe_log_entry)
        except UnicodeEncodeError:
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
            label.config(text="[PASS]", foreground="green", font=("Arial", 9, "bold"))
        elif status == "fail":
            label.config(text="[FAIL]", foreground="red", font=("Arial", 9, "bold"))
        elif status == "running":
            label.config(text="[RUNNING...]", foreground="blue")
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
            messagebox.showinfo("提示", "測試正在執行中，請等待完成或點擊停止")
            return
        
        # 檢查是否需要 Mobile 測試，以及 Appium 是否運行
        needs_mobile = False
        for test_name in selected_tests:
            if self.check_test_needs_mobile(test_name):
                needs_mobile = True
                break
        
        if needs_mobile and not self.appium_manager.is_appium_running():
            # 彈出警告視窗
            result = messagebox.askyesno(
                "Appium 未運行",
                "檢測到您選擇的測試需要 Mobile 測試，但 Appium Server 未運行。\n\n"
                "是否要先啟動 Appium Server？\n\n"
                "點擊「是」將自動啟動 Appium，點擊「否」將繼續執行（可能會失敗）。"
            )
            
            if result:
                # 用戶選擇啟動 Appium
                self.log("用戶選擇啟動 Appium Server...", "INFO")
                self.btn_appium.config(state=tk.DISABLED)
                
                def _start_and_wait():
                    success = self.appium_manager.start_appium()
                    self.root.after(0, self._update_appium_button_state, success)
                    if success:
                        self.log("Appium Server 已啟動，開始執行測試...", "INFO")
                        self.root.after(0, self._start_tests_after_appium, selected_tests)
                    else:
                        self.log("Appium Server 啟動失敗，無法執行 Mobile 測試", "ERROR")
                        messagebox.showerror("錯誤", "Appium Server 啟動失敗，無法執行 Mobile 測試")
                        self.root.after(0, lambda: self.btn_appium.config(state=tk.NORMAL))
                
                threading.Thread(target=_start_and_wait, daemon=True).start()
                return
            else:
                # 用戶選擇繼續執行（可能會失敗）
                self.log("用戶選擇繼續執行（Appium 未運行，Mobile 測試可能會失敗）", "WARNING")
        
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
    
    def _start_tests_after_appium(self, selected_tests: List[str]):
        """在 Appium 啟動後開始執行測試"""
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
                if self.current_test_name:
                    self.root.after(0, self.update_status, self.current_test_name, "fail")
                    self._generate_report_for_stopped_test(self.current_test_name, "interrupted")
                break
            
            # 更新當前測試案例名稱
            self.current_test_name = test_name
            self.current_log_file = None
            
            # 更新狀態為執行中
            self.root.after(0, self.update_status, test_name, "running")
            self.log(f"[{idx}/{total}] 執行測試: {test_name}", "INFO")
            
            try:
                # 執行測試邏輯
                result = self.execute_test_logic(test_name)
                
                # 更新狀態顯示
                if result:
                    self.root.after(0, self.update_status, test_name, "pass")
                    self.log(f"[PASS] {test_name} - Pass", "INFO")
                else:
                    self.root.after(0, self.update_status, test_name, "fail")
                    self.log(f"[FAIL] {test_name} - Fail", "ERROR")
            
            except Exception as e:
                self.root.after(0, self.update_status, test_name, "fail")
                self.log(f"[FAIL] {test_name} - 執行時發生錯誤: {str(e)}", "ERROR")
            
            finally:
                # 清除進程引用
                self.current_process = None
                
                if not self.is_running:
                    pass
                else:
                    self.current_test_name = None
        
        # 執行完成
        self.is_running = False
        self.root.after(0, self._execution_completed)
        
        self.log("=" * 60)
        self.log("所有測試執行完成", "INFO")
    
    def execute_test_logic(self, test_name: str) -> bool:
        """
        執行測試邏輯
        
        :param test_name: 測試案例名稱
        :return: True (Pass) / False (Fail)
        """
        try:
            # 取得專案根目錄
            project_root = EnvConfig.PROJECT_ROOT
            test_file = os.path.join(project_root, "tests", "test_runner.py")
            
            # 檢查測試文件是否存在
            if not os.path.exists(test_file):
                self.log(f"[WARN] 找不到測試文件: {test_file}", "WARNING")
                return False
            
            # 確定 Python 解釋器路徑
            if getattr(sys, 'frozen', False):
                python_exe = shutil.which("python") or shutil.which("python.exe")
                
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
                
                if not python_exe:
                    python_exe = "python"
                    self.log(f"[WARN] 使用 PATH 中的 'python' 命令", "WARNING")
                else:
                    self.log(f"找到 Python 解釋器: {python_exe}", "INFO")
            else:
                python_exe = sys.executable
                self.log(f"使用當前 Python 解釋器: {python_exe}", "INFO")
            
            # 構建 pytest 命令
            cmd = [
                python_exe,
                "-m", "pytest",
                test_file,
                "--test_name", test_name,
                "-v",
                "-s",
                "--tb=short"
            ]
            
            # 記錄執行信息
            self.log(f"執行命令: {' '.join(cmd)}", "INFO")
            self.log(f"工作目錄: {project_root}", "INFO")
            
            # 驗證工作目錄是否存在
            if not os.path.exists(project_root):
                self.log(f"錯誤: 工作目錄不存在: {project_root}", "ERROR")
                return False
            
            # 創建 log 文件（保存在專案目錄下的 report/{測試名稱}/{時間戳}/ 資料夾）
            # 注意：為了確保與 TestReporter 使用相同的目錄，我們先創建目錄並通過環境變數傳遞
            log_file = None
            report_dir = None
            try:
                # 使用與報告相同的目錄結構（與 TestReporter._create_report_directory 邏輯一致）
                report_base = os.path.join(project_root, "report")
                
                # 清理測試名稱，移除不適合作為文件名的字符（與 TestReporter 一致）
                safe_test_name = test_name.replace("/", "_").replace("\\", "_")
                test_dir = os.path.join(report_base, safe_test_name)
                
                # 使用執行時間建立資料夾（與 TestReporter 相同的格式）
                # 注意：這裡使用一個固定的時間戳，確保與 TestReporter 使用相同的目錄
                test_start_time = datetime.datetime.now()
                time_str = test_start_time.strftime("%Y-%m-%d_%H-%M-%S")
                report_dir = os.path.join(test_dir, time_str)
                os.makedirs(report_dir, exist_ok=True)  # 確保資料夾存在
                
                # log 文件名
                log_file = os.path.join(report_dir, "terminal_output.log")
                
                # 先創建文件並寫入標題信息
                with open(log_file, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"測試案例: {test_name}\n")
                    f.write(f"執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"執行命令: {' '.join(cmd)}\n")
                    f.write(f"工作目錄: {project_root}\n")
                    f.write("=" * 80 + "\n\n")
                
                self.log(f"Terminal log 文件已創建: {log_file}", "INFO")
            except Exception as e:
                self.log(f"創建 Terminal log 文件失敗: {e}", "WARNING")
                log_file = None
            
            # 準備環境變數
            env = os.environ.copy()
            pythonpath = env.get('PYTHONPATH', '')
            if pythonpath:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{pythonpath}"
            else:
                env['PYTHONPATH'] = project_root
            
            # 設置環境變數
            if log_file:
                env['TEST_TERMINAL_LOG'] = log_file
            # 設置報告目錄環境變數，讓 TestReporter 使用相同的目錄
            if report_dir:
                env['TEST_REPORT_DIR'] = report_dir
            
            self.log(f"PYTHONPATH: {env['PYTHONPATH']}", "INFO")
            if log_file:
                self.log(f"TEST_TERMINAL_LOG: {log_file}", "INFO")
            
            # 使用 subprocess 執行 pytest
            result = None
            if log_file:
                log_file_path = log_file  # 保存文件路徑，避免被覆蓋
                try:
                    with open(log_file_path, 'a', encoding='utf-8', errors='ignore', buffering=1) as log_file_handle:
                        self.current_process = subprocess.Popen(
                            cmd,
                            cwd=project_root,
                            env=env,
                            stdout=log_file_handle,
                            stderr=subprocess.STDOUT,
                            text=True,
                            encoding='utf-8',
                            errors='ignore'
                        )
                        
                        # 等待進程完成，但定期檢查 is_running 狀態
                        try:
                            while self.current_process.poll() is None:
                                if not self.is_running:
                                    self.log("檢測到停止請求，正在終止測試進程...", "WARNING")
                                    
                                    if log_file_path:
                                        try:
                                            log_file_handle.flush()
                                            self.log(f"Log 文件已刷新: {log_file_path}", "INFO")
                                        except Exception as flush_e:
                                            self.log(f"刷新 log 文件時發生錯誤: {str(flush_e)}", "WARNING")
                                    
                                    self.current_process.terminate()
                                    try:
                                        self.current_process.wait(timeout=5)
                                    except subprocess.TimeoutExpired:
                                        self.log("進程未響應 terminate，強制終止...", "WARNING")
                                        self.current_process.kill()
                                        self.current_process.wait()
                                    
                                    if log_file_path:
                                        try:
                                            log_file_handle.write("\n" + "=" * 80 + "\n")
                                            log_file_handle.write("測試進程被用戶手動終止\n")
                                            log_file_handle.write(f"終止時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                            log_file_handle.write("=" * 80 + "\n")
                                            log_file_handle.flush()
                                            self.log(f"Log 文件已保存: {log_file_path}", "INFO")
                                        except Exception as save_e:
                                            self.log(f"保存 log 文件時發生錯誤: {str(save_e)}", "WARNING")
                                    
                                    break
                                time.sleep(0.5)
                            
                            # 獲取進程返回碼
                            returncode = self.current_process.returncode
                            
                            class ProcessResult:
                                def __init__(self, returncode):
                                    self.returncode = returncode
                                    self.stdout = None
                                    self.stderr = None
                            
                            result = ProcessResult(returncode)
                            
                        except KeyboardInterrupt:
                            self.log("收到中斷信號，正在終止測試進程...", "WARNING")
                            if self.current_process:
                                self.current_process.terminate()
                                try:
                                    self.current_process.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    self.current_process.kill()
                                    self.current_process.wait()
                            result = ProcessResult(-1)
                        
                        # 寫入結尾信息
                        log_file_handle.write("\n" + "=" * 80 + "\n")
                        log_file_handle.write(f"退出碼: {result.returncode}\n")
                        if result.returncode == 0:
                            log_file_handle.write(f"執行結果: 成功\n")
                        elif result.returncode == -1:
                            log_file_handle.write(f"執行結果: 被用戶中斷\n")
                        else:
                            log_file_handle.write(f"執行結果: 失敗或被中斷\n")
                        log_file_handle.write("=" * 80 + "\n")
                        log_file_handle.flush()
                        
                        # 保存 log 文件路徑
                        self.current_log_file = log_file_path
                    
                    # 執行完成後，讀取文件內容用於 UI 顯示
                    try:
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as log_file_read:
                            log_content = log_file_read.read()
                            if "退出碼:" in log_content:
                                parts = log_content.split("退出碼:")
                                if len(parts) > 0:
                                    stdout_content = parts[0].split("=" * 80 + "\n", 1)[-1] if "=" * 80 in parts[0] else parts[0]
                                else:
                                    stdout_content = log_content
                            else:
                                stdout_content = log_content.split("=" * 80 + "\n", 1)[-1] if "=" * 80 in log_content else log_content
                            
                            if stdout_content.strip():
                                output_preview = stdout_content[:2000] if len(stdout_content) > 2000 else stdout_content
                                self.log(f"測試輸出:\n{output_preview}", "INFO")
                    except Exception as read_e:
                        self.log(f"讀取 Terminal log 失敗: {read_e}", "WARNING")
                    
                    self.log(f"Terminal log 已保存: {log_file}", "INFO")
                    self.current_log_file = log_file
                    
                except Exception as e:
                    self.log(f"執行測試或保存 Terminal log 失敗: {e}", "WARNING")
                    import traceback
                    self.log(f"錯誤詳情: {traceback.format_exc()[:500]}", "ERROR")
                    return False
            
            # 檢查退出碼：0=成功，非0=失敗
            success = (result.returncode == 0) if result else False
            
            if success:
                self.log(f"[PASS] pytest 執行成功 (退出碼: {result.returncode})", "INFO")
            else:
                self.log(f"[FAIL] pytest 執行失敗 (退出碼: {result.returncode})", "ERROR")
            
            return success
                
        except FileNotFoundError:
            self.log(f"[WARN] 找不到 Python 解釋器或 pytest: {python_exe}", "WARNING")
            return False
        except Exception as e:
            self.log(f"[FAIL] 執行測試時發生錯誤: {str(e)}", "ERROR")
            import traceback
            self.log(f"錯誤詳情:\n{traceback.format_exc()[:500]}", "ERROR")
            return False
    
    def stop_tests(self):
        """
        停止測試執行
        
        功能：
        1. 停止執行程序（包括終止 subprocess）
        2. 保存 log
        3. 產生 HTML 報告
        4. 更新狀態顯示
        """
        if not self.is_running:
            return
        
        self.log("正在停止測試執行...", "WARNING")
        
        # 設置停止標誌
        self.is_running = False
        
        # 如果當前有正在運行的 subprocess，立即終止它
        if self.current_process and self.current_process.poll() is None:
            self.log("正在終止測試進程...", "WARNING")
            try:
                # 在終止進程前，確保 log 文件被保存
                if self.current_log_file and os.path.exists(self.current_log_file):
                    try:
                        with open(self.current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                        with open(self.current_log_file, 'a', encoding='utf-8', errors='ignore') as f:
                            f.write("\n" + "=" * 80 + "\n")
                            f.write("測試進程被用戶手動終止\n")
                            f.write(f"終止時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("=" * 80 + "\n")
                            f.flush()
                        self.log(f"Log 文件已保存: {self.current_log_file}", "INFO")
                    except Exception as log_e:
                        self.log(f"保存 log 文件時發生錯誤: {str(log_e)}", "WARNING")
                
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                    self.log("測試進程已終止", "INFO")
                except subprocess.TimeoutExpired:
                    self.log("進程未響應 terminate，強制終止...", "WARNING")
                    self.current_process.kill()
                    self.current_process.wait()
                    self.log("測試進程已強制終止", "INFO")
            except Exception as e:
                self.log(f"終止測試進程時發生錯誤: {str(e)}", "ERROR")
        
        # 如果當前有正在執行的測試，更新狀態並生成報告
        if self.current_test_name:
            self.root.after(0, self.update_status, self.current_test_name, "fail")
            self.log(f"正在為中斷的測試 '{self.current_test_name}' 生成報告...", "INFO")
            
            if self.current_log_file:
                self.log(f"[LOG] 當前 log 文件: {self.current_log_file}", "INFO")
                if os.path.exists(self.current_log_file):
                    file_size = os.path.getsize(self.current_log_file)
                    self.log(f"[LOG] Log 文件大小: {file_size} bytes", "INFO")
                else:
                    self.log(f"[WARNING] Log 文件不存在: {self.current_log_file}", "WARNING")
            else:
                if 'TEST_TERMINAL_LOG' in os.environ:
                    self.current_log_file = os.environ.get('TEST_TERMINAL_LOG')
                    self.log(f"[LOG] 從環境變數獲取 log 文件: {self.current_log_file}", "INFO")
            
            self._generate_report_for_stopped_test(self.current_test_name, "interrupted")
        
        # 等待執行線程結束（最多等待 2 秒）
        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=2.0)
        
        # 清除進程引用
        self.current_process = None
        
        self.log("測試執行已停止", "WARNING")
    
    def _execution_completed(self):
        """執行完成後的回調（在主線程中執行）"""
        self.btn_run.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
    
    def _generate_report_for_stopped_test(self, test_name: str, status: str):
        """
        為中斷或完成的測試生成報告
        
        :param test_name: 測試案例名稱
        :param status: 狀態 ('interrupted', 'completed')
        """
        import datetime
        try:
            from engine.test_reporter import TestReporter
            
            # 嘗試獲取 TestReporter 實例
            reporter = None
            try:
                from base.desktop_app import DesktopApp
                reporter = DesktopApp.get_reporter()
            except Exception as e:
                self.log(f"[WARNING] 無法從 DesktopApp 獲取 reporter: {str(e)}", "WARNING")
            
            # 確定 log 文件路徑
            log_file_path = self.current_log_file
            if not log_file_path:
                if 'TEST_TERMINAL_LOG' in os.environ:
                    log_file_path = os.environ.get('TEST_TERMINAL_LOG')
            
            # 確保 log 文件存在並記錄路徑
            if log_file_path:
                if os.path.exists(log_file_path):
                    file_size = os.path.getsize(log_file_path)
                    self.log(f"[LOG] 找到 log 文件: {log_file_path} ({file_size} bytes)", "INFO")
                else:
                    self.log(f"[WARNING] Log 文件不存在: {log_file_path}", "WARNING")
            else:
                self.log(f"[WARNING] 未找到 log 文件路徑", "WARNING")
            
            # 確定整體狀態
            overall_status = "fail" if status == "interrupted" else "pass"
            
            # 如果找到了對應的 reporter，使用它生成報告
            if reporter and hasattr(reporter, 'test_name') and reporter.test_name == test_name:
                self.log(f"[REPORT] 找到 TestReporter 實例，正在生成報告...", "INFO")
                
                try:
                    html_path = reporter.finish(overall_status, log_file_path=log_file_path)
                    if html_path and os.path.exists(html_path):
                        abs_path = os.path.abspath(html_path).replace("\\", "/")
                        self.log(f"[REPORT] [OK] 報告已生成: {abs_path}", "INFO")
                        self.log(f"[REPORT] 您可以直接在瀏覽器中打開此文件查看詳細報告", "INFO")
                        if log_file_path and os.path.exists(log_file_path):
                            self.log(f"[LOG] Log 文件位置: {log_file_path}", "INFO")
                    else:
                        self.log(f"[WARNING] 報告生成失敗: {html_path}", "WARNING")
                except Exception as e:
                    self.log(f"[ERROR] 生成報告時發生錯誤: {str(e)}", "ERROR")
                    import traceback
                    self.log(f"[ERROR] 錯誤詳情: {traceback.format_exc()[:500]}", "ERROR")
                    reporter = None
            
            # 如果沒有找到 reporter 或使用現有 reporter 失敗，創建一個新的並生成基本報告
            if not reporter:
                self.log(f"[REPORT] 未找到 TestReporter 實例，創建新的報告...", "INFO")
                
                try:
                    reporter = TestReporter(test_name)
                    
                    # 添加一個步驟說明測試被中斷
                    if status == "interrupted":
                        reporter.add_step(
                            step_no=1,
                            step_name="測試執行被中斷",
                            status="fail",
                            message=f"測試執行過程中被用戶手動停止（停止時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"
                        )
                    
                    # 生成報告
                    html_path = reporter.finish(overall_status, log_file_path=log_file_path)
                    if html_path and os.path.exists(html_path):
                        abs_path = os.path.abspath(html_path).replace("\\", "/")
                        self.log(f"[REPORT] [OK] 報告已生成: {abs_path}", "INFO")
                        self.log(f"[REPORT] 您可以直接在瀏覽器中打開此文件查看詳細報告", "INFO")
                        if log_file_path and os.path.exists(log_file_path):
                            self.log(f"[LOG] Log 文件位置: {log_file_path}", "INFO")
                    else:
                        self.log(f"[WARNING] 報告生成失敗: {html_path}", "WARNING")
                except Exception as e:
                    self.log(f"[ERROR] 創建新報告時發生錯誤: {str(e)}", "ERROR")
                    import traceback
                    self.log(f"[ERROR] 錯誤詳情: {traceback.format_exc()[:500]}", "ERROR")
                    
        except Exception as e:
            self.log(f"[ERROR] 生成報告時發生未預期的錯誤: {str(e)}", "ERROR")
            import traceback
            self.log(f"[ERROR] 錯誤詳情: {traceback.format_exc()[:500]}", "ERROR")


def main():
    """主函數：啟動測試案例啟動器"""
    root = tk.Tk()
    app = TestCaseLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
