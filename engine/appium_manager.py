# -*- coding: utf-8 -*-
"""
Appium Server 管理器

負責 Appium Server 的啟動、停止和狀態檢查。

Author: SDET Team
Date: 2026-01-26
"""

import os
import sys
import subprocess
import time
import socket
import platform
import shutil
import io
from typing import Optional, Callable


class AppiumManager:
    """Appium Server 管理器。
    
    此類負責：
    - 檢查 Appium Server 運行狀態
    - 啟動 Appium Server
    - 停止 Appium Server
    - 自動檢測 Android SDK
    
    Attributes:
        appium_process: Appium 進程對象
        appium_port (int): Appium Server 端口號
        log_callback: 日誌回調函數
        is_running (bool): Appium 是否運行
        log_file: 日誌文件句柄
    """
    
    # 預設配置
    DEFAULT_PORT = 4723
    DEFAULT_ADDRESS = "127.0.0.1"
    DEFAULT_BASE_PATH = "/wd/hub"
    
    # 超時配置
    STARTUP_MAX_WAIT = 10  # 啟動最大等待時間（秒）
    STARTUP_WAIT_INTERVAL = 0.5  # 啟動檢查間隔（秒）
    STOP_TIMEOUT = 5  # 停止超時時間（秒）
    STOP_WAIT_TIME = 2  # 停止後等待時間（秒）
    
    # Appium 可能的安裝路徑
    POSSIBLE_APPIUM_PATHS = [
        r"C:\Users\usert\AppData\Roaming\npm\appium.cmd",
        r"C:\Users\usert\AppData\Local\npm\appium.cmd",
    ]
    
    # Android SDK 可能的路徑
    POSSIBLE_SDK_PATHS = [
        r"C:\Users\usert\AppData\Local\Android\Sdk",
        r"C:\Android\Sdk",
    ]
    
    def __init__(self, port: int = DEFAULT_PORT, log_callback: Optional[Callable] = None):
        """初始化 Appium 管理器。
        
        Args:
            port: Appium Server 端口號
            log_callback: 日誌回調函數 (message: str, level: str) -> None
        """
        self.appium_process: Optional[subprocess.Popen] = None
        self.appium_port = port
        self.log_callback = log_callback
        self.is_running = False
        self.log_file: Optional[io.TextIOWrapper] = None
    
    def log(self, message: str, level: str = "INFO") -> None:
        """輸出日誌。
        
        Args:
            message: 日誌訊息
            level: 日誌級別 (INFO, WARNING, ERROR, DEBUG)
        """
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    
    def check_port_in_use(self, port: int) -> bool:
        """檢查指定端口是否被佔用。
        
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
        """檢查 Appium Server 是否正在運行。
        
        Returns:
            bool: True 表示 Appium 正在運行，False 表示未運行
        """
        return self.check_port_in_use(self.appium_port)
    
    def find_appium_command(self) -> Optional[str]:
        """查找 Appium 命令路徑。
        
        Returns:
            Optional[str]: Appium 命令路徑，如果未找到則返回 None
        """
        # 首先嘗試從 PATH 中查找
        appium_cmd = shutil.which("appium")
        if appium_cmd:
            return appium_cmd
        
        # 嘗試常見的安裝位置
        for path in self.POSSIBLE_APPIUM_PATHS:
            # 支持 ~ 展開
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return None
    
    def find_android_sdk(self) -> Optional[str]:
        """查找 Android SDK 路徑。
        
        Returns:
            Optional[str]: Android SDK 路徑，如果未找到則返回 None
        """
        # 首先檢查環境變數
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if android_home and os.path.exists(android_home):
            return android_home
        
        # 嘗試常見的安裝位置
        search_paths = [
            os.path.expanduser(r"~\AppData\Local\Android\Sdk"),
            os.path.expanduser(r"~\Android\Sdk"),
            *self.POSSIBLE_SDK_PATHS,
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk'),
        ]
        
        for sdk_path in search_paths:
            if os.path.exists(sdk_path) and os.path.isdir(sdk_path):
                # 驗證是否是有效的 SDK（檢查 platform-tools）
                platform_tools = os.path.join(sdk_path, 'platform-tools')
                if os.path.exists(platform_tools):
                    return sdk_path
        
        return None
    
    def start_appium(self) -> bool:
        """啟動 Appium Server。
        
        執行流程：
        1. 檢查 Appium 是否已運行
        2. 查找 Appium 命令
        3. 設置 Android SDK 環境變數
        4. 啟動 Appium 進程
        5. 等待並驗證啟動成功
        
        Returns:
            bool: 啟動是否成功
        """
        # 檢查是否已運行
        if self.is_appium_running():
            self.log("Appium Server 已經在運行中", "INFO")
            self.is_running = True
            return True
        
        try:
            # 查找 Appium 命令
            appium_cmd = self.find_appium_command()
            if not appium_cmd:
                self.log("找不到 Appium 命令，請確認 Appium 已安裝", "ERROR")
                return False
            
            self.log(f"啟動 Appium Server: {appium_cmd}", "INFO")
            
            # 設置環境變數
            env = self._prepare_environment()
            
            # 準備日誌文件
            log_file_path = self._prepare_log_file()
            
            # 啟動 Appium
            cmd_args = [
                appium_cmd,
                "--address", self.DEFAULT_ADDRESS,
                "--port", str(self.appium_port),
                "--base-path", self.DEFAULT_BASE_PATH
            ]
            
            self.log(f"[診斷] 啟動命令: {' '.join(cmd_args)}", "INFO")
            
            self.appium_process = subprocess.Popen(
                cmd_args,
                stdout=self.log_file,
                stderr=self.log_file,
                text=True,
                encoding='utf-8',
                errors='ignore',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            # 等待啟動完成
            return self._wait_for_startup(log_file_path)
            
        except Exception as e:
            self.log(f"啟動 Appium Server 時發生錯誤: {e}", "ERROR")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()[:300]}", "ERROR")
            return False
    
    def stop_appium(self) -> bool:
        """停止 Appium Server。
        
        Returns:
            bool: 停止是否成功
        """
        try:
            # 嘗試終止進程
            if self.appium_process and self.appium_process.poll() is None:
                self.log("正在終止 Appium 進程...", "INFO")
                self.appium_process.terminate()
                
                try:
                    self.appium_process.wait(timeout=self.STOP_TIMEOUT)
                    self.log("Appium 進程已終止", "INFO")
                except subprocess.TimeoutExpired:
                    self.log("進程未響應 terminate，強制終止...", "WARNING")
                    self.appium_process.kill()
                    self.appium_process.wait()
                
                self.appium_process = None
                self.is_running = False
                self._close_log_file()
                return True
            
            # 嘗試終止所有 Appium/Node 進程
            self._kill_all_appium_processes()
            
            # 等待並檢查
            time.sleep(self.STOP_WAIT_TIME)
            if not self.is_appium_running():
                self.is_running = False
                self._close_log_file()
                self.log("Appium Server 已停止", "INFO")
                return True
            else:
                self.log("警告：Appium Server 可能仍在運行", "WARNING")
                self._close_log_file()
                return False
                
        except Exception as e:
            self.log(f"停止 Appium Server 時發生錯誤: {e}", "ERROR")
            self._close_log_file()
            return False
    
    # ==================== 私有輔助方法 ====================
    
    def _prepare_environment(self) -> dict:
        """準備環境變數。
        
        Returns:
            dict: 包含必要環境變數的字典
        """
        env = os.environ.copy()
        
        # 檢查並設置 Android SDK
        android_home = env.get('ANDROID_HOME') or env.get('ANDROID_SDK_ROOT')
        
        if not android_home:
            android_home = self.find_android_sdk()
            if android_home:
                env['ANDROID_HOME'] = android_home
                env['ANDROID_SDK_ROOT'] = android_home
                self.log(f"[診斷] 已設置 ANDROID_HOME={android_home}", "INFO")
            else:
                self.log("[WARN] 無法找到 Android SDK，Appium 可能無法正常工作", "WARNING")
        else:
            self.log(f"[診斷] 使用現有的 Android SDK: {android_home}", "INFO")
        
        return env
    
    def _prepare_log_file(self) -> str:
        """準備日誌文件。
        
        Returns:
            str: 日誌文件路徑
        """
        log_file_path = os.path.join(os.getcwd(), "appium_server_output.log")
        self.log_file = open(log_file_path, "w", encoding="utf-8")
        self.log(f"Appium Server 日誌將寫入: {log_file_path}", "INFO")
        return log_file_path
    
    def _wait_for_startup(self, log_file_path: str) -> bool:
        """等待 Appium 啟動完成。
        
        Args:
            log_file_path: 日誌文件路徑
            
        Returns:
            bool: 是否啟動成功
        """
        waited = 0
        
        while waited < self.STARTUP_MAX_WAIT:
            time.sleep(self.STARTUP_WAIT_INTERVAL)
            waited += self.STARTUP_WAIT_INTERVAL
            
            # 檢查端口是否就緒
            if self.is_appium_running():
                self.is_running = True
                self.log(f"Appium Server 啟動成功（等待 {waited:.1f} 秒）", "INFO")
                return True
            
            # 檢查進程是否已結束
            if self.appium_process.poll() is not None:
                self._handle_startup_failure(log_file_path)
                return False
        
        # 超時處理
        if self.appium_process.poll() is None:
            self.log("Appium Server 正在啟動中（進程運行中，但端口尚未就緒）", "WARNING")
            self.is_running = True
            return True
        else:
            self.log("Appium Server 啟動超時", "ERROR")
            return False
    
    def _handle_startup_failure(self, log_file_path: str) -> None:
        """處理啟動失敗。
        
        Args:
            log_file_path: 日誌文件路徑
        """
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
    
    def _kill_all_appium_processes(self) -> None:
        """終止所有 Appium/Node 進程"""
        self.log("嘗試終止所有 Appium/Node 進程...", "INFO")
        
        if platform.system() == 'Windows':
            # Windows: 使用 taskkill 命令
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'node.exe'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                self.log("已終止所有 Node.exe 進程", "INFO")
            except Exception as e:
                self.log(f"終止 Node.exe 進程時發生錯誤: {e}", "WARNING")
            
            # 嘗試終止 appium.exe
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'appium.exe'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
            except:
                pass
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
    
    def _close_log_file(self) -> None:
        """關閉日誌文件"""
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None
