# 相對路徑: toolkit/mobile_toolkit.py
"""
移動端自動化工具類

提供 Appium WebDriver 的初始化和管理功能。
"""

from typing import Optional, Tuple
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from config import EnvConfig
from toolkit.logger import get_logger


logger = get_logger(__name__)


def find_main_activity(package_name: str) -> Optional[str]:
    """
    使用 adb 命令查找 App 的主 Activity
    
    Args:
        package_name: App 的包名
        
    Returns:
        主 Activity 名稱，如果找不到則返回 None
    """
    import subprocess
    try:
        # 使用 adb 命令查找主 Activity
        # adb shell pm dump <package> | grep -A 1 "android.intent.action.MAIN"
        cmd = ['adb', 'shell', 'pm', 'dump', package_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            output = result.stdout
            # 檢查 output 是否為 None 或空
            if not output:
                logger.debug("[MOBILE_TOOLKIT] adb 命令返回空輸出")
                return None
            
            # 查找包含 MAIN action 的 Activity
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'android.intent.action.MAIN' in line:
                    # 在接下來的幾行中查找 Activity 名稱
                    for j in range(i, min(i + 10, len(lines))):
                        if j < len(lines) and lines[j] and 'Activity' in lines[j] and package_name in lines[j]:
                            # 提取 Activity 名稱
                            activity_line = lines[j]
                            if activity_line and '/' in activity_line:
                                try:
                                    # 提取 / 後面的部分
                                    activity_part = activity_line.split('/')[-1].strip()
                                    # 去除額外的文本（如 "filter 2dc86f"），只保留類名
                                    # Activity 類名通常只包含字母、數字、點和底線
                                    activity = activity_part.split()[0] if activity_part else None
                                    if activity and not activity.startswith('(') and '.' in activity:
                                        logger.info(f"[MOBILE_TOOLKIT] 找到主 Activity: {activity}")
                                        return activity
                                except Exception as e:
                                    logger.debug(f"[MOBILE_TOOLKIT] 解析 Activity 行失敗: {e}")
                                    continue
        return None
    except Exception as e:
        logger.warning(f"[MOBILE_TOOLKIT] 無法查找主 Activity: {e}")
        return None


def create_appium_driver(timeout: Optional[int] = None) -> Tuple[webdriver.Remote, WebDriverWait]:
    """
    創建 Appium WebDriver 實例
    
    根據 config.py 中的配置創建並返回 Appium WebDriver 和 WebDriverWait 實例。
    
    Args:
        timeout: 顯式等待超時時間（秒），如果為 None 則使用配置中的默認值
        
    Returns:
        Tuple[webdriver.Remote, WebDriverWait]: Appium WebDriver 和 WebDriverWait 實例
        
    Raises:
        Exception: 如果創建 WebDriver 失敗
    """
    import time
    init_start = time.time()
    logger.info(f"[MOBILE_TOOLKIT] [時間戳: {time.strftime('%H:%M:%S')}] 開始初始化 Appium WebDriver...")
    
    # 構建 Appium capabilities
    options = UiAutomator2Options()
    options.platform_name = "Android"
    # 如果未指定平台版本，讓 Appium 自動使用第一個可用設備的版本
    if EnvConfig.ANDROID_PLATFORM_VERSION:
        options.platform_version = EnvConfig.ANDROID_PLATFORM_VERSION
        logger.info(f"[MOBILE_TOOLKIT] 使用指定的 Android 版本: {EnvConfig.ANDROID_PLATFORM_VERSION}")
    else:
        logger.info("[MOBILE_TOOLKIT] 未指定 Android 版本，將使用第一個可用設備的版本")
    options.device_name = EnvConfig.ANDROID_DEVICE_NAME
    options.automation_name = EnvConfig.ANDROID_AUTOMATION_NAME
    
    # App 配置
    if EnvConfig.ANDROID_APP_PATH:
        # 如果提供了 APK 路徑，使用它
        options.app = EnvConfig.ANDROID_APP_PATH
        logger.info(f"[MOBILE_TOOLKIT] 使用 APK 路徑: {EnvConfig.ANDROID_APP_PATH}")
    else:
        # 否則使用已安裝的 App
        options.app_package = EnvConfig.ANDROID_APP_PACKAGE
        
        # 如果指定了 Activity，使用它；否則嘗試自動查找主 Activity
        if EnvConfig.ANDROID_APP_ACTIVITY:
            options.app_activity = EnvConfig.ANDROID_APP_ACTIVITY
            logger.info(f"[MOBILE_TOOLKIT] 使用已安裝的 App: {EnvConfig.ANDROID_APP_PACKAGE}/{EnvConfig.ANDROID_APP_ACTIVITY}")
        else:
            # 嘗試使用 adb 查找主 Activity
            activity_find_start = time.time()
            logger.info(f"[MOBILE_TOOLKIT] [時間戳: {time.strftime('%H:%M:%S')}] 未指定 Activity，嘗試自動查找主 Activity...")
            main_activity = find_main_activity(EnvConfig.ANDROID_APP_PACKAGE)
            activity_find_elapsed = time.time() - activity_find_start
            if main_activity:
                # 如果找到主 Activity，使用它
                options.app_activity = main_activity
                logger.info(f"[MOBILE_TOOLKIT] [耗時: {activity_find_elapsed:.2f}s] 使用已安裝的 App: {EnvConfig.ANDROID_APP_PACKAGE}/{main_activity}")
            else:
                # 如果找不到，不指定 Activity，讓 Appium 自動處理
                logger.info(f"[MOBILE_TOOLKIT] [耗時: {activity_find_elapsed:.2f}s] 無法自動查找 Activity，讓 Appium 自動處理: {EnvConfig.ANDROID_APP_PACKAGE}")
        
        # 設置等待 Activity（如果 App 已經在運行，等待它啟動）
        # 使用通配符 * 來匹配任何 Activity，避免 Activity 名稱不匹配的問題
        options.app_wait_activity = "*"
        options.app_wait_package = EnvConfig.ANDROID_APP_PACKAGE
    
    # 如果指定了 UDID，則使用它
    if EnvConfig.ANDROID_UDID:
        options.udid = EnvConfig.ANDROID_UDID
        logger.info(f"[MOBILE_TOOLKIT] 使用設備 UDID: {EnvConfig.ANDROID_UDID}")
    
    # 其他配置
    options.no_reset = True  # 不重置 App（保留 App 狀態，避免退出）
    options.full_reset = False  # 不完整重置（保留數據）
    # 如果 App 已經在運行，不要強制停止它
    # 使用 set_capability 設置一些特殊的選項
    try:
        # 防止 App 在 session 結束時被停止
        options.set_capability("appium:dontStopAppOnReset", True)
        logger.info("[MOBILE_TOOLKIT] 已設置 dontStopAppOnReset=True，防止 App 被停止")
    except Exception as e:
        logger.warning(f"[MOBILE_TOOLKIT] 無法設置 dontStopAppOnReset: {e}")
    
    # 如果 App 已經在運行，嘗試附加到現有實例而不是重新啟動
    try:
        options.set_capability("appium:autoLaunch", True)  # 如果未運行則自動啟動
        logger.info("[MOBILE_TOOLKIT] 已設置 autoLaunch=True")
    except Exception as e:
        logger.warning(f"[MOBILE_TOOLKIT] 無法設置 autoLaunch: {e}")
    
    try:
        # 先檢查 Appium Server 是否可用
        import socket
        from urllib.parse import urlparse
        
        server_url = EnvConfig.APPIUM_SERVER_URL
        parsed_url = urlparse(server_url)
        server_host = parsed_url.hostname or 'localhost'
        server_port = parsed_url.port or 4723
        
        # 初始化 server_url_with_path（默認使用原始 URL）
        server_url_with_path = server_url
        
        # 檢查是否需要添加 /wd/hub 路徑（Appium 3.x 可能需要）
        # 如果 URL 中沒有路徑，嘗試添加 /wd/hub
        if not parsed_url.path or parsed_url.path == '/':
            # 嘗試使用 /wd/hub 路徑（Appium 3.x 默認路徑）
            base_path = "/wd/hub"
            server_url_with_path = f"{parsed_url.scheme}://{server_host}:{server_port}{base_path}"
            logger.info(f"[MOBILE_TOOLKIT] [診斷] 原始 URL: {server_url}")
            logger.info(f"[MOBILE_TOOLKIT] [診斷] 嘗試使用路徑: {server_url_with_path}")
        else:
            server_url_with_path = server_url
            logger.info(f"[MOBILE_TOOLKIT] [診斷] 使用配置的 URL: {server_url_with_path}")
        
        logger.info(f"[MOBILE_TOOLKIT] [時間戳: {time.strftime('%H:%M:%S')}] 檢查 Appium Server 是否可用: {server_host}:{server_port}")
        
        # 方法 1: 使用 socket 檢查端口是否開放
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 秒超時
            result = sock.connect_ex((server_host, server_port))
            sock.close()
            if result != 0:
                raise Exception(f"無法連接到 Appium Server 端口 {server_port}（端口未開放）")
            logger.info(f"[MOBILE_TOOLKIT] [OK] 端口 {server_port} 已開放")
        except socket.timeout:
            raise Exception(f"連接 Appium Server 端口 {server_port} 超時（2 秒）")
        except Exception as e:
            raise Exception(f"檢查 Appium Server 端口時發生錯誤: {e}")
        
        # 方法 2: 使用 HTTP 請求檢查 Appium Server 狀態（可選，如果 requests 可用）
        try:
            import requests
            # 嘗試多個路徑來檢查 Appium Server 狀態
            status_paths = ["/status", "/wd/hub/status", "/"]
            status_checked = False
            
            for path in status_paths:
                status_url = f"http://{server_host}:{server_port}{path}"
                try:
                    logger.info(f"[MOBILE_TOOLKIT] [診斷] 嘗試檢查 Appium Server 狀態: {status_url}")
                    response = requests.get(status_url, timeout=5)
                    logger.info(f"[MOBILE_TOOLKIT] [診斷] 狀態碼: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"[MOBILE_TOOLKIT] [OK] Appium Server 狀態正常 (路徑: {path})")
                        status_checked = True
                        # 嘗試解析狀態信息
                        try:
                            status_data = response.json()
                            version = status_data.get('value', {}).get('build', {}).get('version', 'N/A')
                            logger.info(f"[MOBILE_TOOLKIT] Appium Server 版本: {version}")
                            
                            # 如果成功使用 /wd/hub/status，更新 server_url_with_path
                            if path == "/wd/hub/status" and (not parsed_url.path or parsed_url.path == '/'):
                                server_url_with_path = f"{parsed_url.scheme}://{server_host}:{server_port}/wd/hub"
                                logger.info(f"[MOBILE_TOOLKIT] [診斷] 檢測到 Appium 使用 /wd/hub 路徑，更新連接 URL: {server_url_with_path}")
                        except:
                            pass
                        break
                    elif response.status_code == 404:
                        logger.debug(f"[MOBILE_TOOLKIT] [診斷] 路徑 {path} 返回 404，嘗試下一個路徑")
                        continue
                    else:
                        logger.warning(f"[MOBILE_TOOLKIT] [WARN] Appium Server 返回狀態碼: {response.status_code} (路徑: {path})")
                        break
                except requests.exceptions.RequestException as e:
                    logger.debug(f"[MOBILE_TOOLKIT] [診斷] 路徑 {path} 檢查失敗: {type(e).__name__}")
                    continue
            
            if not status_checked:
                logger.warning(f"[MOBILE_TOOLKIT] [WARN] 無法通過任何路徑檢查 Appium Server 狀態")
                logger.warning(f"[MOBILE_TOOLKIT] [診斷] 嘗試的路徑: {status_paths}")
                logger.warning(f"[MOBILE_TOOLKIT] [診斷] 這可能表示 Appium Server 未正確啟動或路徑配置不正確")
            
            # 額外檢查：檢查是否有現有 session（使用正確的路徑）
            try:
                # 根據前面檢測到的路徑來決定使用哪個 session 路徑
                session_base_path = "/wd/hub" if status_checked and "/wd/hub" in str(server_url_with_path) else ""
                sessions_paths = [f"{session_base_path}/sessions", "/sessions", "/wd/hub/sessions"]
                
                for path in sessions_paths:
                    sessions_url = f"http://{server_host}:{server_port}{path}"
                    try:
                        logger.debug(f"[MOBILE_TOOLKIT] [診斷] 嘗試檢查 session: {sessions_url}")
                        sessions_response = requests.get(sessions_url, timeout=3)
                        if sessions_response.status_code == 200:
                            sessions_data = sessions_response.json()
                            active_sessions = sessions_data.get('value', [])
                            if active_sessions:
                                logger.warning(f"[MOBILE_TOOLKIT] [WARN] 檢測到 {len(active_sessions)} 個活躍的 Appium session，這可能導致連接失敗")
                                for session in active_sessions:
                                    logger.warning(f"[MOBILE_TOOLKIT]   - Session ID: {session.get('id', 'N/A')}")
                            break
                    except Exception as e:
                        logger.debug(f"[MOBILE_TOOLKIT] [診斷] 路徑 {path} 檢查失敗: {type(e).__name__}")
                        continue
            except:
                pass  # 忽略 sessions 檢查錯誤
                
        except ImportError:
            # 如果 requests 不可用，跳過 HTTP 檢查
            logger.debug("[MOBILE_TOOLKIT] requests 模組不可用，跳過 HTTP 狀態檢查")
        except requests.exceptions.Timeout:
            raise Exception(f"檢查 Appium Server 狀態超時（5 秒），請確認 Appium Server 是否正常運行")
        except requests.exceptions.ConnectionError:
            raise Exception(f"無法連接到 Appium Server，請確認 Appium Server 是否已啟動")
        except Exception as e:
            logger.warning(f"[MOBILE_TOOLKIT] [WARN] 檢查 Appium Server 狀態時發生錯誤（繼續嘗試連接）: {e}")
        
        # 在連接前，先檢查 adb devices 是否連接
        try:
            import subprocess
            logger.info("[MOBILE_TOOLKIT] 檢查 Android 設備連接狀態...")
            adb_result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
            if adb_result.returncode == 0:
                devices_output = adb_result.stdout.strip()
                # 檢查是否有設備連接（排除 "List of devices attached" 標題行）
                device_lines = [line for line in devices_output.split('\n') if line.strip() and 'List of devices' not in line]
                connected_devices = [line for line in device_lines if 'device' in line and 'offline' not in line]
                if connected_devices:
                    logger.info(f"[MOBILE_TOOLKIT] [OK] 找到 {len(connected_devices)} 個已連接的設備")
                    for device in connected_devices:
                        logger.info(f"[MOBILE_TOOLKIT]   - {device.strip()}")
                else:
                    logger.warning("[MOBILE_TOOLKIT] [WARN] 未找到已連接的 Android 設備")
                    logger.warning("[MOBILE_TOOLKIT] 請確認：1. 設備已通過 USB 連接  2. 已啟用 USB 調試  3. 設備已解鎖")
            else:
                logger.warning(f"[MOBILE_TOOLKIT] [WARN] 無法執行 adb devices 命令: {adb_result.stderr}")
        except FileNotFoundError:
            logger.warning("[MOBILE_TOOLKIT] [WARN] 找不到 adb 命令，跳過設備檢查")
        except Exception as e:
            logger.warning(f"[MOBILE_TOOLKIT] [WARN] 檢查設備連接時發生錯誤: {e}")
        
        # 創建 WebDriver 實例（使用 threading 和 timeout 來限制連接時間）
        driver_connect_start = time.time()
        logger.info(f"[MOBILE_TOOLKIT] [時間戳: {time.strftime('%H:%M:%S')}] 正在連接到 Appium Server")
        logger.info(f"[MOBILE_TOOLKIT] [診斷] 連接 URL: {server_url_with_path}")
        logger.info(f"[MOBILE_TOOLKIT] [診斷] 原始配置 URL: {server_url}")
        
        # 等待 driver 創建完成，但設置超時
        # 優先使用 config 中的值，如果不存在則使用 120 秒默認值
        connection_timeout = 120  # 默認值
        if hasattr(EnvConfig, 'APPIUM_COMMAND_TIMEOUT'):
            connection_timeout = EnvConfig.APPIUM_COMMAND_TIMEOUT
        logger.info(f"[MOBILE_TOOLKIT] 設置連接超時: {connection_timeout} 秒 (從 config: {hasattr(EnvConfig, 'APPIUM_COMMAND_TIMEOUT')})")
        
        # 使用 threading 來實現超時控制
        import threading
        driver_result = [None]
        driver_exception = [None]
        
        def _create_driver():
            try:
                logger.info("[MOBILE_TOOLKIT] [背景線程] 開始創建 WebDriver 實例...")
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] 連接 URL: {server_url_with_path}")
                
                # 記錄 Capabilities 詳情
                caps_info = {
                    'platform': options.platform_name,
                    'package': getattr(options, 'app_package', 'N/A'),
                    'activity': getattr(options, 'app_activity', 'N/A'),
                    'device_name': getattr(options, 'device_name', 'N/A'),
                    'automation_name': getattr(options, 'automation_name', 'N/A'),
                }
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] Capabilities: {caps_info}")
                
                # 在創建前檢查是否有現有 session
                try:
                    import requests
                    # 嘗試多個路徑檢查 session
                    session_paths = ["/sessions", "/wd/hub/sessions"]
                    for path in session_paths:
                        sessions_url = f"http://{server_host}:{server_port}{path}"
                        try:
                            logger.debug(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 嘗試檢查 session: {sessions_url}")
                            sessions_response = requests.get(sessions_url, timeout=3)
                            if sessions_response.status_code == 200:
                                sessions_data = sessions_response.json()
                                active_sessions = sessions_data.get('value', [])
                                if active_sessions:
                                    logger.warning(f"[MOBILE_TOOLKIT] [背景線程] 檢測到 {len(active_sessions)} 個現有 session，這可能導致連接失敗")
                                    for session in active_sessions:
                                        logger.warning(f"[MOBILE_TOOLKIT] [背景線程]   - Session ID: {session.get('id', 'N/A')}")
                                else:
                                    logger.debug(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 沒有現有 session")
                                break
                        except Exception as e:
                            logger.debug(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 路徑 {path} 檢查失敗: {type(e).__name__}")
                            continue
                except Exception as e:
                    logger.debug(f"[MOBILE_TOOLKIT] [背景線程] 無法檢查現有 session: {e}")
                
                # 記錄開始時間
                create_start = time.time()
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] 調用 webdriver.Remote()...")
                
                # 嘗試創建 WebDriver（這裡可能會卡住）
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 使用連接 URL: {server_url_with_path}")
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] [診斷] Capabilities 完整信息: {options.to_capabilities()}")
                
                driver_result[0] = webdriver.Remote(
                    command_executor=server_url_with_path,  # 使用帶路徑的 URL
                    options=options
                )
                
                create_elapsed = time.time() - create_start
                logger.info(f"[MOBILE_TOOLKIT] [背景線程] WebDriver 實例創建成功 (耗時: {create_elapsed:.2f}s)")
            except Exception as e:
                create_elapsed = time.time() - create_start if 'create_start' in locals() else 0
                error_type = type(e).__name__
                error_msg = str(e)
                
                logger.error(f"[MOBILE_TOOLKIT] [背景線程] WebDriver 創建失敗 (耗時: {create_elapsed:.2f}s)")
                logger.error(f"[MOBILE_TOOLKIT] [背景線程] 錯誤類型: {error_type}")
                logger.error(f"[MOBILE_TOOLKIT] [背景線程] 錯誤訊息: {error_msg}")
                
                # 提供診斷建議
                if "ANDROID_HOME" in error_msg or "ANDROID_SDK_ROOT" in error_msg:
                    logger.error("[MOBILE_TOOLKIT] [背景線程] [診斷] Android SDK 環境變數未設置")
                    logger.error("  這是導致連接失敗的主要原因！")
                    logger.error("  解決方法：")
                    logger.error("  1. 設置 ANDROID_HOME 或 ANDROID_SDK_ROOT 環境變數")
                    logger.error("  2. 常見位置: %LOCALAPPDATA%\\Android\\Sdk")
                    logger.error("  3. 或在啟動 Appium Server 前設置環境變數")
                    logger.error("  4. 檢查 appium_server_output.log 查看詳細錯誤")
                    
                    # 嘗試檢測 Android SDK
                    import os
                    possible_sdk_paths = [
                        os.path.expanduser(r"~\AppData\Local\Android\Sdk"),
                        os.path.expanduser(r"~\Android\Sdk"),
                        r"C:\Users\usert\AppData\Local\Android\Sdk",
                        r"C:\Android\Sdk",
                    ]
                    logger.info("[MOBILE_TOOLKIT] [背景線程] [診斷] 嘗試檢測 Android SDK 位置...")
                    for sdk_path in possible_sdk_paths:
                        if os.path.exists(sdk_path):
                            logger.info(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 找到可能的 SDK 位置: {sdk_path}")
                            logger.info(f"[MOBILE_TOOLKIT] [背景線程] [診斷] 建議設置: set ANDROID_HOME={sdk_path}")
                    
                elif "Connection" in error_type or "timeout" in error_msg.lower() or "ConnectionError" in error_type or "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning("[MOBILE_TOOLKIT] [背景線程] [診斷] 這可能是連接問題，請檢查：")
                    logger.warning(f"  1. 使用的連接 URL: {server_url_with_path}")
                    logger.warning(f"  2. 原始配置 URL: {server_url}")
                    logger.warning("  3. Appium Server 是否正常運行（查看 appium_server_output.log）")
                    logger.warning("  4. 設備是否已連接且已解鎖（使用 'adb devices' 檢查）")
                    logger.warning("  5. 是否有其他 Appium session 正在使用設備")
                    logger.warning("  6. 設備是否允許 USB 調試")
                    logger.warning("  7. 嘗試重啟 Appium Server")
                    logger.warning("  8. 檢查 Appium Server 是否使用 /wd/hub 路徑（查看啟動參數）")
                else:
                    logger.warning("[MOBILE_TOOLKIT] [背景線程] [診斷] 其他錯誤，請檢查：")
                    logger.warning(f"  1. 錯誤類型: {error_type}")
                    logger.warning(f"  2. 錯誤訊息: {error_msg[:200]}")
                    logger.warning("  3. 查看 appium_server_output.log 獲取詳細信息")
                
                import traceback
                logger.error(f"[MOBILE_TOOLKIT] [背景線程] 錯誤詳情: {traceback.format_exc()[:500]}")
                driver_exception[0] = e
        
        # 在背景線程中創建 driver
        driver_thread = threading.Thread(target=_create_driver, daemon=True)
        driver_thread.start()
        logger.info("[MOBILE_TOOLKIT] 已啟動背景線程創建 WebDriver，開始等待連接...")
        
        # 定期檢查連接進度
        check_interval = 3  # 每 3 秒檢查一次（更頻繁的檢查）
        elapsed = 0
        last_log_time = 0
        
        while driver_thread.is_alive() and elapsed < connection_timeout:
            driver_thread.join(timeout=check_interval)
            elapsed += check_interval
            
            if driver_thread.is_alive():
                # 每 3 秒記錄一次進度（而不是每 5 秒）
                if elapsed - last_log_time >= 3:
                    logger.info(f"[MOBILE_TOOLKIT] [等待中...] 已等待 {elapsed} 秒，還剩 {connection_timeout - elapsed} 秒...")
                    last_log_time = elapsed
                
                # 每 6 秒檢查一次設備狀態和 Appium Server 狀態
                if elapsed % 6 == 0:
                    # 檢查設備狀態
                    try:
                        adb_result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=2, encoding='utf-8', errors='ignore')
                        if adb_result.returncode == 0:
                            device_lines = [line for line in adb_result.stdout.strip().split('\n') 
                                          if line.strip() and 'List of devices' not in line]
                            connected_devices = [line for line in device_lines if 'device' in line and 'offline' not in line]
                            if not connected_devices:
                                logger.warning("[MOBILE_TOOLKIT] [WARN] 檢測到設備未連接，這可能是連接失敗的原因")
                            else:
                                logger.info(f"[MOBILE_TOOLKIT] [狀態檢查] 設備仍連接: {len(connected_devices)} 個設備")
                    except:
                        pass
                    
                    # 檢查 Appium Server 是否還在運行
                    try:
                        import requests
                        status_response = requests.get(f"http://{server_host}:{server_port}/status", timeout=2)
                        if status_response.status_code == 200:
                            logger.debug("[MOBILE_TOOLKIT] [狀態檢查] Appium Server 仍在運行")
                        else:
                            logger.warning(f"[MOBILE_TOOLKIT] [WARN] Appium Server 狀態異常: {status_response.status_code}")
                    except requests.exceptions.ConnectionError:
                        logger.error("[MOBILE_TOOLKIT] [ERROR] 無法連接到 Appium Server，Server 可能已停止")
                    except requests.exceptions.Timeout:
                        logger.warning("[MOBILE_TOOLKIT] [WARN] 檢查 Appium Server 狀態超時")
                    except Exception as e:
                        logger.warning(f"[MOBILE_TOOLKIT] [WARN] 無法檢查 Appium Server 狀態: {type(e).__name__}")
        
        if driver_thread.is_alive():
            # 如果線程還在運行，說明超時了
            error_msg = f"連接 Appium Server 超時（{connection_timeout} 秒），請檢查：\n" \
                       f"  1. Appium Server 是否正常運行（檢查 Appium Server 日誌）\n" \
                       f"  2. Android 設備/模擬器是否已連接（使用 'adb devices' 檢查）\n" \
                       f"  3. 設備是否已解鎖且允許 USB 調試\n" \
                       f"  4. 設備是否正在被其他 Appium session 使用\n" \
                       f"  5. 檢查 Appium Server 日誌是否有錯誤訊息"
            logger.error(f"[MOBILE_TOOLKIT] [ERROR] {error_msg}")
            raise Exception(error_msg)
        
        if driver_exception[0]:
            raise driver_exception[0]
        
        if driver_result[0] is None:
            raise Exception("創建 WebDriver 失敗（未知錯誤）")
        
        driver = driver_result[0]
        driver_connect_elapsed = time.time() - driver_connect_start
        logger.info(f"[MOBILE_TOOLKIT] [耗時: {driver_connect_elapsed:.2f}s] WebDriver 連接成功")
        
        # 設置隱式等待
        driver.implicitly_wait(EnvConfig.ANDROID_IMPLICIT_WAIT)
        
        # 創建 WebDriverWait 實例
        if timeout is None:
            timeout = getattr(EnvConfig, 'ANDROID_DEFAULT_TIMEOUT', 10)
        wait = WebDriverWait(driver, timeout)
        
        total_init_elapsed = time.time() - init_start
        logger.info(f"[MOBILE_TOOLKIT] [總耗時: {total_init_elapsed:.2f}s] ✅ Appium WebDriver 初始化成功")
        return driver, wait
        
    except Exception as e:
        logger.error(f"[MOBILE_TOOLKIT] ❌ 初始化 Appium WebDriver 失敗: {e}")
        logger.warning("[MOBILE_TOOLKIT] 💡 請確認:")
        logger.warning("  1. Appium Server 已啟動 (通常運行在 http://localhost:4723)")
        logger.warning("  2. Android 設備/模擬器已連接 (使用 'adb devices' 檢查)")
        logger.warning("  3. APP_PACKAGE 和 APP_ACTIVITY 配置正確")
        logger.warning("  4. 設備已解鎖且允許 USB 調試")
        raise
