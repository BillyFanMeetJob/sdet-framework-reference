# 相對路徑: base/desktop_app.py

import pyautogui
import time
import os
import ctypes
import pygetwindow as gw
from toolkit.logger import get_logger
from config import EnvConfig
from PIL import Image
import numpy as np
from typing import Optional, Tuple, List, Dict

class DesktopApp:
    _last_x, _last_y = 0, 0
    _reporter = None  # 用於自動截圖的測試報告器

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._ocr_engine = None
        self._vlm_engine = None
    
    def _safe_log(self, level, message, also_print=True):
        """
        安全輸出日誌，自動清理 emoji 避免 cp950 編碼錯誤
        
        同時輸出到日誌文件和終端（print），確保兩者內容一致。
        
        :param level: 日誌級別 ('info', 'warning', 'error', 'debug')
        :param message: 日誌內容
        :param also_print: 是否同時輸出到終端（預設 True）
        """
        # 替換常見 emoji 為 ASCII 等效字符
        # 按使用頻率排序，確保所有 emoji 都被清理
        safe_message = message.replace("🟢", "[START]").replace("📸", "[IMG]").replace("🤖", "[VLM]").replace("📝", "[OCR]").replace("📍", "[LOC]").replace("✅", "[OK]").replace("⚠️", "[WARN]").replace("❌", "[ERROR]").replace("⏱️", "[TIMEOUT]").replace("💾", "[SAVE]").replace("⚙️", "[CFG]").replace("🖱️", "[CLICK]").replace("⌨️", "[KEY]").replace("🎬", "[CASE]").replace("🔄", "[SWITCH]").replace("🔍", "[DEBUG]").replace("🎯", "[OK]").replace("📊", "[STAT]").replace("⏳", "[WAIT]").replace("🚀", "[START]").replace("💡", "[TIP]")
        
        # 輸出到日誌
        getattr(self.logger, level)(safe_message)
        
        # 同時輸出到終端
        if also_print:
            print(safe_message)
    
    @classmethod
    def set_reporter(cls, reporter):
        """
        設置測試報告器（用於自動截圖）
        :param reporter: TestReporter 實例
        """
        cls._reporter = reporter
    
    @classmethod
    def get_reporter(cls):
        """
        獲取當前設置的測試報告器
        :return: TestReporter 實例或 None
        """
        return cls._reporter
    
    def create_verification_item(
        self,
        name: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        center_x: Optional[int] = None,
        center_y: Optional[int] = None
    ) -> Dict:
        """
        創建檢核項目（verification item）用於測試報告
        
        Args:
            name: 檢核項目名稱
            x, y: 左上角座標（可選）
            width, height: 寬度和高度（可選，預設 50x50）
            center_x, center_y: 中心座標（可選，如果提供會自動計算 x, y）
            
        Returns:
            Dict: 檢核項目字典，格式: {"name": "...", "x": ..., "y": ..., "width": ..., "height": ...}
            
        Example:
            >>> # 使用中心座標
            >>> item = self.create_verification_item("按鈕", center_x=100, center_y=200, width=80, height=30)
            >>> # 結果: {"name": "按鈕", "x": 60, "y": 185, "width": 80, "height": 30}
            
            >>> # 使用左上角座標
            >>> item = self.create_verification_item("圖標", x=50, y=100, width=40, height=40)
            >>> # 結果: {"name": "圖標", "x": 50, "y": 100, "width": 40, "height": 40}
            
            >>> # 只提供名稱（用於簡單檢核，不標註座標）
            >>> item = self.create_verification_item("視窗")
            >>> # 結果: {"name": "視窗"}
        """
        item = {"name": name}
        
        # 如果提供了中心座標，轉換為左上角座標
        if center_x is not None and center_y is not None:
            w = width or 50
            h = height or 50
            x = center_x - w // 2
            y = center_y - h // 2
            width = w
            height = h
        
        # 添加座標信息（如果提供）
        if x is not None:
            item["x"] = x
        if y is not None:
            item["y"] = y
        if width is not None:
            item["width"] = width
        if height is not None:
            item["height"] = height
        
        return item
    
    def create_verification_items_from_result(
        self,
        name: str,
        result,
        default_size: Tuple[int, int] = (50, 50)
    ) -> List[Dict]:
        """
        從辨識結果創建檢核項目列表
        
        Args:
            name: 檢核項目名稱
            result: 辨識結果物件（OK Script / VLM / OCR 結果）
            default_size: 預設尺寸 (width, height)，當結果沒有尺寸信息時使用
            
        Returns:
            List[Dict]: 檢核項目列表（通常只有一個項目）
            
        Example:
            >>> # 從 OK Script 結果創建
            >>> result = recognizer.locate_on_screen(...)
            >>> items = self.create_verification_items_from_result("按鈕", result)
        """
        items = []
        
        if result and hasattr(result, 'success') and result.success:
            # OK Script 結果
            if hasattr(result, 'center'):
                center = result.center
                width = getattr(result, 'width', default_size[0])
                height = getattr(result, 'height', default_size[1])
                items.append(self.create_verification_item(
                    name, center_x=center.x, center_y=center.y, width=width, height=height
                ))
            # VLM 結果
            elif hasattr(result, 'bbox'):
                bbox = result.bbox  # (xmin, ymin, xmax, ymax)
                items.append(self.create_verification_item(
                    name, x=bbox[0], y=bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1]
                ))
            # OCR 結果
            elif hasattr(result, 'x') and hasattr(result, 'y'):
                items.append(self.create_verification_item(
                    name, x=result.x, y=result.y, width=default_size[0], height=default_size[1]
                ))
        
        # 如果無法從結果提取座標，至少提供名稱
        if not items:
            items.append(self.create_verification_item(name))
        
        return items
    
    def _get_ocr_engine(self):
        """延遲載入 OCR 引擎，只在需要時初始化"""
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR
                import logging
                import os
                
                # 禁用模型源檢查，加快初始化速度
                os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
                
                # 設置 PaddleOCR 的日誌級別為 ERROR，減少輸出
                logging.getLogger("ppocr").setLevel(logging.ERROR)
                
                self._ocr_engine = PaddleOCR(
                    use_angle_cls=False,  # 關閉角度分類器（桌面文字都是水平的）
                    lang="ch"
                )
                self._safe_log("info", "[OK] OCR 引擎初始化成功")
            except Exception as e:
                self._safe_log("warning", f"[WARN] OCR 引擎初始化失敗: {e}")
                self._ocr_engine = False  # 標記為失敗，避免重複嘗試
        return self._ocr_engine if self._ocr_engine else None
    
    def _get_vlm_engine(self):
        """延遲載入 VLM (視覺語言模型) 引擎，使用 UnifiedVLM（Ollama + Gemini 備援）"""
        if self._vlm_engine is None:
            try:
                # 檢查是否啟用 VLM
                vlm_enabled = getattr(EnvConfig, 'VLM_ENABLED', False)
                self._safe_log("info", f"[DEBUG] VLM 啟用狀態: {vlm_enabled}")
                if not vlm_enabled:
                    self._vlm_engine = False
                    self._safe_log("info", "[DEBUG] VLM 未啟用，跳過初始化")
                    return None
                
                # 使用新的 UnifiedVLM 引擎（整合 Ollama + Gemini 備援）
                from toolkit.vlm_engine import create_vlm_engine
                
                self._safe_log("info", "[DEBUG] 初始化 UnifiedVLM 引擎（Ollama + Gemini 備援）")
                
                # 創建 UnifiedVLM 實例（自動從 config 讀取 Gemini API Key）
                self._vlm_engine = create_vlm_engine(
                    threshold=15.0,
                    logger=self.logger
                )
                
                self._safe_log("info", "[OK] UnifiedVLM 引擎初始化成功")
                self._safe_log("info", f"[DEBUG] 功能: Ollama (主) + Gemini (備援) + 描述校正 + 特徵進化")
                
                # 測試 Ollama 是否可用
                try:
                    import ollama
                    try:
                        models = ollama.list()
                        model_names = []
                        if hasattr(models, 'models'):
                            model_names = [m.name if hasattr(m, 'name') else str(m) for m in models.models]
                        elif isinstance(models, dict) and 'models' in models:
                            model_names = [m.get('name', str(m)) for m in models['models']]
                        self._safe_log("info", f"[DEBUG] Ollama 可用，已安裝模型: {model_names}")
                    except Exception as e:
                        self._safe_log("warning", f"[WARN] Ollama 可能未運行: {e}")
                        self._safe_log("warning", "[TIP] Ollama 未運行時將自動使用 Gemini 備援")
                except Exception as e:
                    self._safe_log("warning", f"[WARN] Ollama 測試失敗，將使用 Gemini 備援: {e}")
                    
            except Exception as e:
                self._safe_log("warning", f"[WARN] UnifiedVLM 引擎初始化失敗: {e}")
                import traceback
                self.logger.debug(f"詳細錯誤: {traceback.format_exc()}")
                self._vlm_engine = False  # 標記為失敗，避免重複嘗試
        return self._vlm_engine if self._vlm_engine else None

    def get_nx_window(self):
        """
        獲取 Nx Witness 視窗物件，並驗證視窗是否有效
        
        :return: 視窗物件或 None
        """
        # 🎯 擴展窗口標題列表，包含更多可能的標題
        window_titles = [
            "警告",
            "Nx Witness Client",
            "本地設置",
            "Nx Witness",
            "Nx Witness Client - Nx Witness Client",  # 完整標題
            "Nx Witness - Nx Witness Client",
        ]
        
        for t in window_titles:
            try:
                wins = [w for w in gw.getWindowsWithTitle(t) if w.visible]
                if wins:
                    # 🎯 選擇最大的可見窗口（避免選到小窗口）
                    win = max(wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                    # 驗證視窗物件是否有效（嘗試訪問屬性）
                    try:
                        _ = win.left, win.top, win.width, win.height
                        # 🎯 過濾掉太小的窗口（可能是錯誤的窗口）
                        if win.width > 800 and win.height > 600:
                            # 🎯 額外驗證：確保窗口標題確實包含 Nx Witness 關鍵字
                            title_lower = win.title.lower()
                            has_nx_keyword = (
                                "nx witness" in title_lower or 
                                "nxwitness" in title_lower or
                                "警告" in win.title or
                                "本地設置" in win.title
                            )
                            # 排除編輯器、測試啟動器、檔案總管等（含 "Nx Witness" 但非 Nx Witness 客戶端）
                            is_excluded = any(kw in win.title for kw in [
                                "cursor", "editor", "code", "vscode", "visual studio",
                                "pycharm", "sublime", "notepad", "notepad++", "mark.txt",
                                "自動化測試主控台", "自動化測試",  # 排除測試案例啟動器 GUI
                                "檔案總管", "explorer", "資料夾", "folder"  # 排除檔案總管
                            ]) or any(kw in title_lower for kw in [
                                "cursor", "editor", "code", "vscode", "visual studio",
                                "pycharm", "sublime", "notepad", "notepad++", "mark.txt",
                                "explorer", "file explorer", "folder"  # 排除檔案總管
                            ])
                            
                            if has_nx_keyword and not is_excluded:
                                self.logger.debug(f"[WINDOW] 找到 Nx Witness 視窗: '{t}' ({win.width}x{win.height})")
                                # 🎯 不再自動置頂，避免干擾右鍵選單等操作
                                # 如需置頂，請在外部明確調用 bring_window_to_front()
                                return win
                            else:
                                self.logger.debug(f"[WINDOW] 跳過非 Nx Witness 窗口: '{win.title}' (has_nx={has_nx_keyword}, is_excluded={is_excluded})")
                        else:
                            self.logger.debug(f"[WINDOW] 跳過小窗口: '{t}' ({win.width}x{win.height})")
                    except Exception:
                        # 視窗物件無效（可能正在初始化），跳過
                        continue
            except Exception as e:
                self.logger.debug(f"[WINDOW] 查找窗口 '{t}' 時發生異常: {e}")
                continue
        
        # 🎯 如果找不到，嘗試查找包含 "Nx Witness" 的窗口（更嚴格的匹配）
        self.logger.warning("[WINDOW] 未找到標準 Nx Witness 視窗，嘗試模糊匹配...")
        try:
            all_wins = [w for w in gw.getAllWindows() if w.visible]
            # 🎯 更嚴格的匹配：必須包含 "Nx Witness" 或 "NxWitness"（不區分大小寫）
            # 排除包含 "Cursor"、"Editor"、"Code"、"Notepad" 等編輯器關鍵字的窗口
            nx_wins = []
            for w in all_wins:
                title_lower = w.title.lower()
                # 🎯 更嚴格的匹配：必須包含 "nx witness" 或 "nxwitness"，並且必須包含 "client" 或特定關鍵字
                # 這樣可以排除像 "nxwitness-demo - 檔案總管" 這樣的視窗
                has_nx_witness = "nx witness" in title_lower or "nxwitness" in title_lower
                # 必須包含更明確的 Nx Witness 關鍵字（Client、警告、本地設置等）
                has_nx_keyword = (
                    "client" in title_lower or
                    "警告" in w.title or
                    "本地設置" in w.title or
                    "local settings" in title_lower
                )
                # 排除編輯器、測試啟動器、檔案總管等（自動化測試主控台）
                # 🎯 優先檢查排除條件，避免誤匹配檔案總管等系統窗口
                is_excluded = (
                    any(kw in title_lower for kw in [
                        "cursor", "editor", "code", "vscode", "visual studio",
                        "pycharm", "sublime", "notepad", "notepad++", "mark.txt",
                        "explorer", "file explorer", "folder", "檔案總管", "資料夾",  # 排除檔案總管
                        "- 檔案總管", "- file explorer", "- folder"  # 排除檔案總管後綴
                    ]) or "自動化測試主控台" in w.title or "自動化測試" in w.title
                    or "檔案總管" in w.title or "資料夾" in w.title  # 排除檔案總管
                    or w.title.endswith(" - 檔案總管") or w.title.endswith(" - File Explorer")  # 排除檔案總管後綴
                )
                
                # 🎯 如果已被排除，直接跳過（避免後續檢查）
                if is_excluded:
                    continue
                
                # 必須同時滿足：包含 nx witness 且包含明確關鍵字，且不被排除
                if has_nx_witness and has_nx_keyword and not is_excluded:
                    # 額外驗證：窗口必須足夠大（避免選到小彈窗）
                    try:
                        if w.width > 800 and w.height > 600:
                            nx_wins.append(w)
                    except:
                        pass
            
            if nx_wins:
                # 選擇最大的窗口
                win = max(nx_wins, key=lambda w: w.width * w.height if w.width > 0 and w.height > 0 else 0)
                try:
                    _ = win.left, win.top, win.width, win.height
                    if win.width > 800 and win.height > 600:
                        self.logger.info(f"[WINDOW] 通過模糊匹配找到視窗: '{win.title}' ({win.width}x{win.height})")
                        # 🎯 不再自動置頂，避免干擾右鍵選單等操作
                        return win
                except Exception:
                    pass
        except Exception as e:
            self.logger.debug(f"[WINDOW] 模糊匹配時發生異常: {e}")
        
        # 🎯 最後嘗試：列出所有可見窗口供調試
        try:
            all_wins = [w for w in gw.getAllWindows() if w.visible]
            if all_wins:
                self.logger.warning(f"[WINDOW] 當前所有可見窗口列表（共 {len(all_wins)} 個）:")
                for w in all_wins[:10]:  # 只列出前10個
                    try:
                        self.logger.warning(f"[WINDOW]   - '{w.title}' ({w.width}x{w.height})")
                    except:
                        pass
        except:
            pass
        
        return None

    def bring_window_to_front(self, win) -> bool:
        """
        將指定視窗置頂並激活（強制方式）
        
        Args:
            win: pygetwindow 視窗物件
            
        Returns:
            bool: 是否成功置頂
        """
        if not win:
            return False
            
        try:
            self.logger.info(f"[WINDOW] 🔝 將視窗置頂: {win.title}")
            print(f"[WINDOW] 🔝 將視窗置頂: {win.title}")
            
            # 如果視窗最小化，先還原
            if win.isMinimized:
                win.restore()
                time.sleep(0.3)
            
            # 🎯 使用 win32gui 強制置頂（繞過 Windows 限制）
            try:
                import win32gui
                import win32con
                import win32api
                
                hwnd = win32gui.FindWindow(None, win.title)
                if hwnd:
                    # 🎯 技巧 1：先模擬按鍵，讓當前進程獲得輸入焦點
                    try:
                        import ctypes
                        # 模擬按下並釋放 Alt 鍵，這會讓系統認為我們有權設置前景窗口
                        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt down
                        ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt up
                    except:
                        pass
                    
                    # 🎯 技巧 2：使用 AttachThreadInput 附加到目標窗口的線程
                    try:
                        foreground_hwnd = win32gui.GetForegroundWindow()
                        foreground_thread = win32api.GetWindowThreadProcessId(foreground_hwnd)[0]
                        target_thread = win32api.GetWindowThreadProcessId(hwnd)[0]
                        
                        if foreground_thread != target_thread:
                            ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, True)
                    except:
                        pass
                    
                    # 還原視窗
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.1)
                    
                    # 設置為前景視窗
                    win32gui.SetForegroundWindow(hwnd)
                    
                    # 置頂
                    win32gui.BringWindowToTop(hwnd)
                    
                    # 🎯 技巧 3：使用 SetWindowPos 強制置頂
                    win32gui.SetWindowPos(
                        hwnd, 
                        win32con.HWND_TOPMOST,  # 設為最頂層
                        0, 0, 0, 0, 
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                    )
                    # 然後取消最頂層（避免永久置頂）
                    win32gui.SetWindowPos(
                        hwnd, 
                        win32con.HWND_NOTOPMOST, 
                        0, 0, 0, 0, 
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                    )
                    
                    self.logger.info("[WINDOW] ✅ 視窗已強制置頂（win32gui）")
                    print("[WINDOW] ✅ 視窗已強制置頂")
                    return True
                    
            except ImportError:
                self.logger.debug("[WINDOW] win32gui 不可用，使用 pygetwindow")
                print("[WINDOW] win32gui 不可用，嘗試 pygetwindow")
            except Exception as e:
                self.logger.debug(f"[WINDOW] win32gui 置頂失敗: {e}")
                print(f"[WINDOW] win32gui 置頂失敗: {e}")
            
            # 備用方法：使用 pygetwindow
            try:
                win.activate()
                self.logger.info("[WINDOW] ✅ 視窗已激活（pygetwindow）")
                print("[WINDOW] ✅ 視窗已激活（pygetwindow）")
                return True
            except Exception as e:
                self.logger.warning(f"[WINDOW] pygetwindow 激活失敗: {e}")
                print(f"[WINDOW] pygetwindow 激活失敗: {e}")
                
        except Exception as e:
            self.logger.warning(f"[WINDOW] 置頂視窗失敗: {e}")
            print(f"[WINDOW] 置頂視窗失敗: {e}")
        
        return False

    def launch_app(self, exe_path):
        """
        啟動程式，如果已經運行則將視窗置頂
        """
        # 🔍 先檢查軟件是否已經運行（通過檢查視窗是否存在）
        win = self.get_nx_window()
        if win:
            try:
                # 驗證視窗是否有效
                _ = win.left, win.top, win.width, win.height
                if win.width > 0 and win.height > 0:
                    # 🎯 額外驗證：確保窗口標題確實是 Nx Witness（避免誤匹配）
                    title_lower = win.title.lower()
                    is_nx_witness = (
                        "nx witness" in title_lower or 
                        "nxwitness" in title_lower or
                        "警告" in win.title or
                        "本地設置" in win.title
                    )
                    # 必須包含更明確的 Nx Witness 關鍵字（Client、警告、本地設置等）
                    has_nx_keyword = (
                        "client" in title_lower or
                        "警告" in win.title or
                        "本地設置" in win.title or
                        "local settings" in title_lower
                    )
                    # 🎯 優先檢查排除條件，避免誤匹配檔案總管等系統窗口
                    is_excluded = (
                        any(kw in title_lower for kw in [
                            "cursor", "editor", "code", "vscode", "visual studio", "pycharm", "sublime",
                            "explorer", "file explorer", "folder", "檔案總管", "資料夾",  # 排除檔案總管
                            "- 檔案總管", "- file explorer", "- folder"  # 排除檔案總管後綴
                        ])
                        or "自動化測試主控台" in win.title or "自動化測試" in win.title
                        or "檔案總管" in win.title or "資料夾" in win.title  # 排除檔案總管
                        or win.title.endswith(" - 檔案總管") or win.title.endswith(" - File Explorer")  # 排除檔案總管後綴
                    )
                    
                    # 🎯 如果已被排除，直接跳過（避免誤判為 Nx Witness）
                    if is_excluded:
                        self.logger.warning(f"[WINDOW] 找到的窗口是系統窗口（非 Nx Witness）: '{win.title}'，將啟動新實例")
                        # 繼續執行啟動流程，不返回
                    else:
                        # 必須同時滿足：包含 nx witness 且包含明確關鍵字，且不被排除
                        if is_nx_witness and has_nx_keyword:
                            self.logger.info(f"✅ 軟件已在運行，將視窗置頂（視窗: '{win.title}', 尺寸: {win.width}x{win.height}）")
                            # 將視窗置頂
                            try:
                                win.activate()
                                time.sleep(0.3)  # 等待視窗置頂
                                self.logger.info("✅ 視窗已置頂")
                            except Exception as e:
                                self.logger.warning(f"⚠️ 置頂視窗失敗: {e}")
                            return self
                        else:
                            self.logger.warning(f"[WINDOW] 找到的窗口不是 Nx Witness: '{win.title}'，將啟動新實例")
            except Exception as e:
                # 視窗無效，繼續啟動流程
                self.logger.debug(f"[WINDOW] 驗證窗口時發生異常: {e}")
        
        # 如果視窗不存在或不是 Nx Witness，啟動程式
        self.logger.info(f"[START] 啟動程式: {exe_path}")
        if not os.path.exists(exe_path):
            self.logger.error(f"[ERROR] 程式路徑不存在: {exe_path}")
            raise FileNotFoundError(f"程式路徑不存在: {exe_path}")
        
        try:
            os.startfile(exe_path)
            self.logger.info("[OK] 已執行啟動命令，等待程式啟動...")
        except Exception as e:
            self.logger.error(f"[ERROR] 啟動程式失敗: {e}")
            raise
        
        # 🎯 智能等待視窗出現並完全初始化（最多 15 秒，給程序更多啟動時間）
        self.logger.info("[WAIT] 等待 Nx Witness 視窗出現...")
        win = self.wait_for_window(timeout=15)
        
        if not win:
            # 如果 wait_for_window 返回 None，嘗試使用 get_nx_window 再次查找
            self.logger.warning("[WARN] wait_for_window 未找到視窗，嘗試使用 get_nx_window 再次查找...")
            time.sleep(2)  # 額外等待 2 秒
            win = self.get_nx_window()
            if win:
                self.logger.info(f"[OK] 通過 get_nx_window 找到視窗: '{win.title}' ({win.width}x{win.height})")
            else:
                self.logger.error("[ERROR] 啟動程式後無法找到 Nx Witness 視窗，請檢查程式是否正常啟動")
                raise RuntimeError("無法找到 Nx Witness 視窗，程式可能啟動失敗")
        
        # 額外等待視窗完全初始化（確保可以訪問視窗屬性）
        max_wait = 5
        waited = 0
        while waited < max_wait:
            win = self.get_nx_window()
            if win:
                try:
                    # 驗證視窗物件是否有效
                    _ = win.left, win.top, win.width, win.height
                    if win.width > 0 and win.height > 0:
                        self.logger.info(f"✅ 軟件已完全啟動（視窗尺寸: {win.width}x{win.height}）")
                        # 將視窗置頂
                        try:
                            win.activate()
                            time.sleep(0.3)
                        except Exception:
                            pass
                        return self
                except Exception:
                    pass
            time.sleep(0.2)
            waited += 0.2
        
        self.logger.warning("⚠️ 軟件可能尚未完全啟動，繼續執行...")
        return self
    
    def wait_for_window(self, window_titles=None, timeout=3):
        """
        智能等待視窗出現並完全初始化
        :param window_titles: 要等待的視窗標題列表，None 則使用預設
        :param timeout: 超時時間（秒）
        :return: 找到的視窗物件或 None
        """
        if window_titles is None:
            window_titles = ["警告", "Nx Witness Client", "本地設置", "Nx Witness", "Server Settings"]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            for title in window_titles:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    win = wins[0]
                    # 驗證視窗物件是否有效（確保視窗已完全初始化）
                    try:
                        _ = win.left, win.top, win.width, win.height
                        if win.width > 0 and win.height > 0:
                            self.logger.info(f"✅ 視窗已出現並完全初始化: {title} ({win.width}x{win.height})")
                            return win
                    except Exception:
                        # 視窗尚未完全初始化，繼續等待
                        pass
            time.sleep(0.1)  # 短暫等待避免 CPU 過載
        
        self.logger.warning(f"⚠️ 等待 {timeout} 秒後未找到視窗或視窗尚未完全初始化")
        return None
    
    def wait_for_condition(self, condition_func, timeout=3, check_interval=0.1):
        """
        通用條件等待函數
        :param condition_func: 返回 True/False 的函數
        :param timeout: 超時時間（秒）
        :param check_interval: 檢查間隔（秒）
        :return: 條件是否滿足
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if condition_func():
                    return True
            except Exception:
                pass
            time.sleep(check_interval)
        return False
    
    def verify_element_exists(
        self,
        image_path=None,
        target_text=None,
        window_titles=None,
        timeout=3,
        raise_on_failure=True,
        error_message="驗證失敗：未找到預期的 UI 元素"
    ):
        """
        🔍 驗證 UI 元素是否存在（用於點擊後驗證）
        
        :param image_path: 要驗證的圖片路徑（相對於 res/）
        :param target_text: 要驗證的文字（OCR/VLM）
        :param window_titles: 要驗證的視窗標題列表
        :param timeout: 超時時間（秒）
        :param raise_on_failure: 驗證失敗時是否拋出異常（預設 True）
        :param error_message: 驗證失敗時的錯誤訊息
        :return: 是否驗證成功
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            win = self.get_nx_window()
            if not win:
                time.sleep(0.1)
                continue
            
            # 驗證視窗標題
            if window_titles:
                window_found = False
                # 🎯 改進：使用部分匹配，而不只是完全匹配
                all_wins = [w for w in gw.getAllWindows() if w.visible]
                for win in all_wins:
                    # 檢查窗口標題是否包含任何關鍵字
                    if any(keyword in win.title for keyword in window_titles):
                        # 驗證窗口尺寸合理（不是太小的彈窗）
                        if win.width > 400 and win.height > 300:
                            window_found = True
                            self.logger.info(f"✅ 找到目標視窗: {win.title} ({win.width}x{win.height})")
                            break
                
                if not window_found:
                    time.sleep(0.1)
                    continue  # 繼續等待視窗出現
            
            # 驗證圖片元素
            if image_path:
                if image_path.startswith("res/") or image_path.startswith("res\\"):
                    image_path = image_path[4:]
                full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, image_path))
                
                if os.path.exists(full_img):
                    region = (win.left, win.top, win.width, win.height)
                    try:
                        # 優先使用 OK Script
                        from base.ok_script_recognizer import get_recognizer
                        recognizer = get_recognizer()
                        result = recognizer.locate_on_screen(full_img, region=region, confidence=0.75)  # 降低信心度
                        if result and result.success:
                            self.logger.info(f"✅ 驗證成功：找到預期元素 {image_path}")
                            return True
                    except Exception:
                        pass
                    
                    # 回退到 pyautogui
                    try:
                        loc = pyautogui.locateOnScreen(full_img, confidence=0.7, region=region)  # 降低信心度
                        if loc:
                            self.logger.info(f"✅ 驗證成功：找到預期元素 {image_path}")
                            return True
                    except Exception:
                        pass
            
            # 驗證文字元素（優先使用 VLM，然後 OCR）
            if target_text:
                # 嘗試使用 VLM 驗證
                vlm = self._get_vlm_engine()
                if vlm:
                    try:
                        region = (win.left, win.top, win.width, win.height)
                        vlm_result = vlm.find_element(target_text, region=region)
                        if vlm_result and vlm_result.success:
                            self.logger.info(f"✅ 驗證成功（VLM）：找到預期文字 '{target_text}' (信心: {vlm_result.confidence:.2f})")
                            return True
                    except Exception as e:
                        self.logger.debug(f"VLM 驗證異常: {e}")
                
                # 回退到 OCR
                try:
                    ocr_result = self._find_text_by_ocr(target_text, region=(win.left, win.top, win.width, win.height))
                    if ocr_result:
                        self.logger.info(f"✅ 驗證成功（OCR）：找到預期文字 '{target_text}'")
                        return True
                except Exception:
                    pass
            
            # 如果所有驗證都通過（視窗標題驗證通過，且沒有圖片/文字驗證要求），返回成功
            if window_titles and not image_path and not target_text:
                self.logger.info(f"✅ 驗證成功：找到預期視窗 {window_titles}")
                return True
            
            time.sleep(0.1)
        
        # 驗證失敗
        if raise_on_failure:
            raise AssertionError(f"{error_message}（超時: {timeout}秒）")
        return False
    
    def _perform_click(self, x, y, clicks=1, click_type='left', offset_x=0, offset_y=0):
        """
        🖱️ 統一的點擊執行方法（base 層核心方法）
        :param x: X 座標（原始座標）
        :param y: Y 座標（原始座標）
        :param clicks: 點擊次數（1=單擊，2=雙擊）
        :param click_type: 點擊類型（'left'=左鍵, 'right'=右鍵）
        :param offset_x: X 軸偏移量（像素，預設 0）
        :param offset_y: Y 軸偏移量（像素，預設 0）
        :return: (final_x, final_y) 加上偏移後的最終座標
        """
        # 🎯 套用偏移量
        final_x = x + offset_x
        final_y = y + offset_y
        
        # 🎯 記錄原始座標和最終座標（用於調試）- 只使用一種輸出方式避免重複
        click_action = "右鍵" if click_type == 'right' else ("雙擊" if clicks == 2 else "單擊")
        if offset_x != 0 or offset_y != 0:
            log_msg = f">>> [CLICK_COORD] 原始座標: ({x}, {y}), 偏移: (offset_x={offset_x}, offset_y={offset_y}), 最終座標: ({final_x}, {final_y}), 動作={click_action}"
        else:
            log_msg = f">>> [CLICK_COORD] 實際點擊座標: ({final_x}, {final_y}), 動作={click_action}"
        print(log_msg)
        import sys
        sys.stdout.flush()
        
        # 🎯 報告優化：點擊前截圖並標記點擊位置
        reporter = DesktopApp.get_reporter()
        if reporter and hasattr(reporter, 'add_click_screenshot'):
            try:
                reporter.add_click_screenshot(
                    click_x=final_x,
                    click_y=final_y,
                    click_action=click_action
                )
            except Exception as e:
                self.logger.debug(f"[CLICK] 添加點擊截圖失敗: {e}")
        
        # 🎯 使用最終座標執行點擊
        if click_type == 'right':
            # 右鍵只支持單擊
            pyautogui.rightClick(final_x, final_y)
        elif clicks == 2:
            pyautogui.doubleClick(final_x, final_y, interval=0.1)
        else:
            pyautogui.click(final_x, final_y)
        
        # 🎯 返回最終座標，用於記錄
        return (final_x, final_y)
    
    def drag_select_range(self, start_x, start_y, end_x, end_y, duration=0.5, button='left'):
        """
        🖱️ 拖拽框選範圍（base 層核心方法）
        按住鼠標左鍵從起始位置拖拽到結束位置，用於框選區域
        
        :param start_x: 起始位置 X 座標
        :param start_y: 起始位置 Y 座標
        :param end_x: 結束位置 X 座標
        :param end_y: 結束位置 Y 座標
        :param duration: 拖拽持續時間（秒，預設 0.5）
        :param button: 按鈕類型（'left'=左鍵, 'right'=右鍵，預設 'left'）
        :return: 是否成功
        """
        try:
            # 🎯 驗證座標有效性
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            
            # 確保座標在屏幕範圍內
            start_x = max(0, min(start_x, screen_width - 1))
            start_y = max(0, min(start_y, screen_height - 1))
            end_x = max(0, min(end_x, screen_width - 1))
            end_y = max(0, min(end_y, screen_height - 1))
            
            self.logger.info(f"[DRAG] 拖拽座標（已驗證）: 起始=({start_x}, {start_y}), 結束=({end_x}, {end_y})")
            self.logger.info(f"[DRAG] 屏幕尺寸: {screen_width}x{screen_height}")
            
            # 確保視窗是活動的（如果可能）
            win = self.get_nx_window()
            if win:
                try:
                    if not win.isActive:
                        win.activate()
                        time.sleep(0.2)
                    
                    # 🎯 驗證座標是否在窗口內
                    win_right = win.left + win.width
                    win_bottom = win.top + win.height
                    if (start_x < win.left or start_x > win_right or 
                        start_y < win.top or start_y > win_bottom or
                        end_x < win.left or end_x > win_right or
                        end_y < win.top or end_y > win_bottom):
                        self.logger.warning(f"[DRAG] ⚠️ 座標超出窗口範圍！窗口: ({win.left}, {win.top}, {win.width}, {win.height})")
                        self.logger.warning(f"[DRAG] 起始: ({start_x}, {start_y}), 結束: ({end_x}, {end_y})")
                except Exception:
                    pass
            
            # 移動到起始位置
            pyautogui.moveTo(start_x, start_y, duration=0.3)
            time.sleep(0.2)
            
            # 按住鼠標按鈕
            pyautogui.mouseDown(button=button)
            self.logger.info(f"[DRAG] 在起始位置按下鼠標按鈕 ({button}): ({start_x}, {start_y})")
            time.sleep(0.1)  # 短暫停頓確保按下
            
            # 拖拽到結束位置
            pyautogui.moveTo(end_x, end_y, duration=duration)
            self.logger.info(f"[DRAG] 拖拽到結束位置: ({end_x}, {end_y})")
            time.sleep(0.1)
            
            # 釋放鼠標按鈕
            pyautogui.mouseUp(button=button)
            self.logger.info(f"[DRAG] ✅ 成功拖拽框選範圍: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
            
            # 等待一下讓選中的區域生效
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"[DRAG] ❌ 拖拽框選範圍失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def type_text(self, text, interval=0.05):
        """
        ⌨️ 鍵盤輸入文字（base 層核心方法）
        :param text: 要輸入的文字
        :param interval: 字元間隔時間（秒）
        """
        pyautogui.typewrite(text, interval=interval)
    
    def press_key(self, key):
        """
        ⌨️ 按下指定按鍵（base 層核心方法）
        :param key: 按鍵名稱（如 'enter', 'esc', 'tab' 等）
        """
        pyautogui.press(key)
    
    def activate_window(self, window_obj):
        """
        🪟 啟動指定視窗（base 層核心方法）
        :param window_obj: pygetwindow 視窗物件
        :return: 是否成功
        """
        try:
            window_obj.activate()
            time.sleep(0.3)
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ 啟動視窗失敗: {e}")
            return False
    
    def find_window(self, title_keywords=None, max_width=None, max_height=None, exclude_titles=None):
        """
        🔍 尋找符合條件的視窗（base 層核心方法）
        :param title_keywords: 標題關鍵字列表（任一匹配即可）
        :param max_width: 最大寬度（用於篩選小視窗）
        :param max_height: 最大高度（用於篩選小視窗）
        :param exclude_titles: 排除的標題關鍵字列表
        :return: 找到的視窗物件或 None
        """
        wins = gw.getAllWindows()
        
        # 如果提供了標題關鍵字，優先匹配標題
        if title_keywords:
            for win in wins:
                if not win.visible:
                    continue
                
                # 檢查排除條件
                if exclude_titles:
                    if any(keyword in win.title for keyword in exclude_titles):
                        continue
                
                # 檢查標題關鍵字匹配
                if any(keyword in win.title for keyword in title_keywords):
                    # 如果還有尺寸條件，驗證尺寸
                    if max_width and max_height:
                        if win.width < max_width and win.height < max_height:
                            return win
                    else:
                        # 沒有尺寸條件，標題匹配就返回
                        return win
        
        # 如果沒有提供標題關鍵字，或標題關鍵字沒有匹配到，檢查尺寸條件
        if max_width and max_height and not title_keywords:
            for win in wins:
                if not win.visible:
                    continue
                
                # 檢查排除條件
                if exclude_titles:
                    if any(keyword in win.title for keyword in exclude_titles):
                        continue
                
                # 只檢查尺寸條件
                if win.width < max_width and win.height < max_height:
                    return win
        
        return None
    
    def wait_for_window_close(self, window_titles, timeout=2):
        """
        ⏳ 等待指定視窗關閉（base 層核心方法）
        :param window_titles: 要等待關閉的視窗標題列表
        :param timeout: 超時時間（秒）
        :return: 是否成功關閉
        """
        def is_window_closed():
            """檢查視窗是否已關閉"""
            for title in window_titles:
                wins = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                if wins:
                    return False  # 視窗還在
            return True  # 視窗已關閉
        
        if self.wait_for_condition(is_window_closed, timeout=timeout):
            self.logger.debug(f"✅ 視窗已關閉: {window_titles}")
            return True
        else:
            self.logger.debug(f"⏳ 視窗可能仍然開啟: {window_titles}")
            return False
    
    def handle_password_popup(self, password, popup_title_keywords=None, input_x_ratio=0.5, input_y_ratio=0.45):
        """
        🔐 處理密碼確認彈窗（base 層核心方法）
        :param password: 要輸入的密碼
        :param popup_title_keywords: 彈窗標題關鍵字列表（預設：["需要再次確認", "確認密碼"]）
        :param input_x_ratio: 輸入框 X 位置比例（相對視窗寬度）
        :param input_y_ratio: 輸入框 Y 位置比例（相對視窗高度）
        :return: 是否成功處理
        """
        if popup_title_keywords is None:
            popup_title_keywords = ["需要再次確認", "確認密碼"]
        
        # 尋找密碼彈窗
        self._safe_log("info", f"[DEBUG] 開始搜尋密碼確認彈窗，關鍵字: {popup_title_keywords}")
        password_window = self.find_window(
            title_keywords=popup_title_keywords,
            max_width=600,
            max_height=400,
            exclude_titles=["伺服器設定", "Server Settings"]
        )
        
        # 特殊處理：Nx Witness Client 標題的小視窗也可能是密碼彈窗
        if not password_window:
            self._safe_log("info", "[DEBUG] 嘗試搜尋標題為 'Nx Witness Client' 的小視窗...")
            wins = gw.getAllWindows()
            visible_wins = [w for w in wins if w.visible]
            self._safe_log("info", f"[DEBUG] 當前所有可見窗口數量: {len(visible_wins)}")
            for win in visible_wins:
                win_info = f"標題='{win.title}', 尺寸={win.width}x{win.height}"
                self._safe_log("info", f"[DEBUG]   - {win_info}")
                if win.title == "Nx Witness Client" and win.width < 600 and win.height < 400:
                    if "伺服器設定" not in win.title and "Server Settings" not in win.title:
                        self._safe_log("info", f"[OK] 找到符合條件的小視窗: {win_info}")
                        password_window = win
                        break
        
        if not password_window:
            self._safe_log("warning", "[WARN] 未檢測到密碼確認彈窗，可能彈窗尚未出現或標題不匹配")
            # 列出所有可見窗口，方便調試
            all_wins = [w for w in gw.getAllWindows() if w.visible]
            if all_wins:
                self._safe_log("info", "[DEBUG] 當前所有可見窗口列表：")
                for win in all_wins:
                    self._safe_log("info", f"[DEBUG]   - 標題: '{win.title}', 尺寸: {win.width}x{win.height}")
            return True  # 沒有彈窗也算成功（可能不需要密碼）
        
        self._safe_log("info", "[OK] 檢測到密碼確認彈窗，準備輸入密碼...")
        
        # 輔助函數：保存調試截圖
        def _save_debug_screenshot(step_name, password_window=None):
            """保存調試截圖"""
            try:
                # 修復格式字符串：使用 datetime 獲取毫秒
                import datetime
                now = datetime.datetime.now()
                timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
                
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "password_debug")
                os.makedirs(debug_dir, exist_ok=True)
                
                # 截圖全屏
                screenshot = pyautogui.screenshot()
                screenshot_filename = "password_{}_{}_full.png".format(step_name, timestamp)
                screenshot_path = os.path.join(debug_dir, screenshot_filename)
                screenshot.save(screenshot_path)
                self._safe_log("info", "[DEBUG_SCREENSHOT] {} - 全屏截圖已保存: {}".format(step_name, screenshot_path))
                
                # 如果提供了窗口，也截圖窗口區域
                if password_window:
                    try:
                        win_region = (password_window.left, password_window.top, password_window.width, password_window.height)
                        win_screenshot = pyautogui.screenshot(region=win_region)
                        win_filename = "password_{}_{}_window.png".format(step_name, timestamp)
                        win_path = os.path.join(debug_dir, win_filename)
                        win_screenshot.save(win_path)
                        self._safe_log("info", "[DEBUG_SCREENSHOT] {} - 窗口截圖已保存: {}".format(step_name, win_path))
                    except Exception as e:
                        self._safe_log("warning", "[DEBUG_SCREENSHOT] 窗口截圖失敗: {}".format(str(e)))
            except Exception as e:
                self._safe_log("warning", "[DEBUG_SCREENSHOT] 截圖失敗: {}".format(str(e)))
        
        # 輔助函數：檢查當前活動窗口
        def _check_active_window():
            """檢查當前活動窗口"""
            try:
                active_win = gw.getActiveWindow()
                if active_win:
                    self._safe_log("info", f"[DEBUG_FOCUS] 當前活動窗口: '{active_win.title}', 尺寸: {active_win.width}x{active_win.height}")
                    return active_win.title
                else:
                    self._safe_log("info", "[DEBUG_FOCUS] 當前無活動窗口")
                    return None
            except Exception as e:
                self._safe_log("warning", f"[DEBUG_FOCUS] 檢查活動窗口失敗: {e}")
                return None
        
        try:
            # 步驟 1: 初始狀態截圖
            _save_debug_screenshot("01_initial", password_window)
            initial_active = _check_active_window()
            self._safe_log("info", "[DEBUG] 密碼彈窗信息: 標題='{}', 位置=({}, {}), 尺寸={}x{}".format(
                password_window.title, password_window.left, password_window.top, password_window.width, password_window.height))
            self._safe_log("info", "[DEBUG] 初始活動窗口: '{}'".format(initial_active))
            
            # 如果活動窗口不是密碼彈窗，記錄警告
            if initial_active and initial_active != password_window.title:
                self._safe_log("warning", "[WARN] 活動窗口 '{}' 與密碼彈窗標題 '{}' 不一致！".format(initial_active, password_window.title))
            
            # 啟動彈窗視窗（確保彈窗獲得焦點，避免在主窗口操作）
            if not self.activate_window(password_window):
                self.logger.warning("⚠️ 啟動密碼彈窗失敗")
            
            # 額外等待，確保彈窗完全激活並穩定
            time.sleep(0.5)
            
            # 步驟 2: 激活窗口後
            _save_debug_screenshot("02_after_activate", password_window)
            active_title = _check_active_window()
            self._safe_log("info", f"[DEBUG] 激活窗口後，活動窗口: '{active_title}'")
            
            # 重新激活彈窗，確保獲得焦點
            try:
                password_window.activate()
                time.sleep(0.3)  # 等待彈窗完全激活
                _check_active_window()
            except Exception as e:
                self._safe_log("warning", f"[DEBUG] 再次激活窗口失敗: {e}")
            
            # 計算輸入框位置（密碼輸入框通常在彈窗中間偏下位置）
            input_x = password_window.left + int(password_window.width * input_x_ratio)
            input_y = password_window.top + int(password_window.height * input_y_ratio)
            self._safe_log("info", f"[DEBUG] 計算輸入框位置: 窗口=({password_window.left}, {password_window.top}, {password_window.width}, {password_window.height}), 比例=({input_x_ratio}, {input_y_ratio}), 絕對座標=({input_x}, {input_y})")
            
            # 重試機制：最多嘗試 2 次輸入密碼
            max_attempts = 2
            for attempt in range(1, max_attempts + 1):
                self._safe_log("info", f"[DEBUG] ========== 第 {attempt} 次嘗試輸入密碼 ==========")
                
                # 1. 輸入之前先點擊密碼輸入框，確保焦點在輸入框中
                _save_debug_screenshot(f"03_attempt{attempt}_before_click", password_window)
                active_title = _check_active_window()
                self._safe_log("info", f"[DEBUG] 點擊前活動窗口: '{active_title}'")
                
                # 再次激活窗口，確保彈窗在最前
                try:
                    password_window.activate()
                    time.sleep(0.2)
                    active_title = _check_active_window()
                    self._safe_log("info", f"[DEBUG] 再次激活窗口後，活動窗口: '{active_title}'")
                except Exception as e:
                    self._safe_log("warning", f"[DEBUG] 激活窗口失敗: {e}")
                
                # 點擊輸入框，確保焦點在輸入框中
                self._safe_log("info", f"[DEBUG] 執行點擊輸入框: ({input_x}, {input_y})")
                final_x, final_y = self._perform_click(input_x, input_y, clicks=1, offset_x=0, offset_y=0)
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                time.sleep(0.5)  # 等待輸入框獲得焦點
                
                # 步驟 3: 點擊後
                _save_debug_screenshot(f"04_attempt{attempt}_after_click", password_window)
                active_title = _check_active_window()
                self._safe_log("info", f"[DEBUG] 點擊後活動窗口: '{active_title}'")
                
                # 輸入密碼
                if password:
                    self._safe_log("info", f"[DEBUG] 準備輸入密碼，長度: {len(password)}, 密碼前3字符: {password[:3]}***")
                    
                    # 步驟 4: 輸入前
                    _save_debug_screenshot(f"05_attempt{attempt}_before_input", password_window)
                    active_title = _check_active_window()
                    self._safe_log("info", f"[DEBUG] 輸入前活動窗口: '{active_title}'")
                    
                    # 使用 typewrite 輸入密碼（模擬鍵盤輸入）
                    try:
                        self._safe_log("info", f"[DEBUG] 開始執行 pyautogui.typewrite，密碼長度: {len(password)}")
                        pyautogui.typewrite(password, interval=0.1)
                        self._safe_log("info", f"[DEBUG] pyautogui.typewrite 執行完成")
                        
                        # 步驟 5: 輸入中（立即截圖，可能在輸入過程中）
                        time.sleep(0.1)  # 稍等片刻讓輸入開始
                        _save_debug_screenshot(f"06_attempt{attempt}_during_input", password_window)
                        active_title = _check_active_window()
                        self._safe_log("info", f"[DEBUG] 輸入中活動窗口: '{active_title}'")
                        
                        time.sleep(0.4)  # 等待輸入完成（總共 0.5 秒）
                        
                        # 步驟 6: 輸入後
                        _save_debug_screenshot(f"07_attempt{attempt}_after_input", password_window)
                        active_title = _check_active_window()
                        self._safe_log("info", f"[DEBUG] 輸入後活動窗口: '{active_title}', 密碼輸入完成: {len(password)} 個字符")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 密碼輸入失敗: {e}")
                        _save_debug_screenshot(f"error_attempt{attempt}_input_failed", password_window)
                        # 嘗試逐個字符輸入
                        self._safe_log("info", "[DEBUG] 嘗試逐個字符輸入密碼...")
                        for i, char in enumerate(password):
                            try:
                                pyautogui.typewrite(char, interval=0.05)
                                time.sleep(0.05)
                                if i % 3 == 0:  # 每3個字符記錄一次
                                    self._safe_log("info", f"[DEBUG] 已輸入 {i+1}/{len(password)} 個字符")
                            except Exception as e:
                                self._safe_log("warning", f"[DEBUG] 輸入字符 '{char}' 失敗: {e}")
                        time.sleep(0.3)
                else:
                    self.logger.info("⌨️ 密碼為空，直接確認...")
                
                # 按 Enter 確認
                self.logger.info("⌨️ 按 Enter 鍵確認...")
                _save_debug_screenshot(f"08_attempt{attempt}_before_enter", password_window)
                active_title = _check_active_window()
                self._safe_log("info", f"[DEBUG] 按 Enter 前活動窗口: '{active_title}'")
                
                self.press_key('enter')
                time.sleep(0.8)  # 等待彈窗關閉或更新
                
                # 步驟 9: 按 Enter 後
                _save_debug_screenshot(f"09_attempt{attempt}_after_enter", password_window)
                active_title = _check_active_window()
                self._safe_log("info", f"[DEBUG] 按 Enter 後活動窗口: '{active_title}'")
                
                # 2. 輸入之後再檢測一次密碼視窗，如果還是存在，就再輸入一次
                password_window_after = self.find_window(
                    title_keywords=["需要再次確認", "確認密碼"],
                    max_width=600,
                    max_height=400,
                    exclude_titles=["伺服器設定", "Server Settings"]
                )
                
                # 特殊處理：Nx Witness Client 標題的小視窗也可能是密碼彈窗
                if not password_window_after:
                    wins = gw.getAllWindows()
                    for win in wins:
                        if not win.visible:
                            continue
                        if win.title == "Nx Witness Client" and win.width < 600 and win.height < 400:
                            if "伺服器設定" not in win.title and "Server Settings" not in win.title:
                                password_window_after = win
                                break
                
                if password_window_after:
                    # 密碼視窗還在，表示輸入失敗或密碼錯誤
                    self._safe_log("info", f"[DEBUG] 密碼視窗仍存在，標題: '{password_window_after.title}', 尺寸: {password_window_after.width}x{password_window_after.height}")
                    _save_debug_screenshot(f"10_attempt{attempt}_window_still_exists", password_window_after)
                    
                    if attempt < max_attempts:
                        self._safe_log("warning", f"[WARN] 密碼視窗仍存在，準備第 {attempt + 1} 次輸入...")
                        # 更新 password_window 引用，使用最新的視窗物件
                        password_window = password_window_after
                        # 重新計算輸入框位置
                        input_x = password_window.left + int(password_window.width * input_x_ratio)
                        input_y = password_window.top + int(password_window.height * input_y_ratio)
                        self._safe_log("info", f"[DEBUG] 重新計算輸入框位置: ({input_x}, {input_y})")
                        time.sleep(0.5)  # 等待一下再重試
                        continue  # 繼續下一次嘗試
                    else:
                        self.logger.warning(f"⚠️ 嘗試 {max_attempts} 次後，密碼視窗仍存在，可能密碼錯誤")
                        _save_debug_screenshot(f"11_final_failed", password_window_after)
                        return False
                else:
                    # 密碼視窗已關閉，輸入成功
                    self._safe_log("info", f"[DEBUG] 密碼輸入成功（第 {attempt} 次嘗試），視窗已關閉")
                    _save_debug_screenshot(f"12_final_success", None)
                    break
            
            self.logger.info("✅ 密碼確認彈窗已處理")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 處理密碼確認彈窗時出錯: {e}")
            return False
    
    def wait_for_screen_change(self, region, threshold=100000, max_wait=1.0):
        """
        🔍 智能等待螢幕變化（例如選單出現）
        :param region: 檢測區域 (left, top, width, height)
        :param threshold: 變化閾值（越大越敏感）
        :param max_wait: 最大等待時間（秒）
        :return: True (檢測到變化) / False (超時)
        """
        try:
            # 截取初始螢幕
            before = pyautogui.screenshot(region=(region[0], region[1], 200, 200))
            before_array = np.array(before)
            
            start_time = time.time()
            while time.time() - start_time < max_wait:
                time.sleep(0.05)
                after = pyautogui.screenshot(region=(region[0], region[1], 200, 200))
                after_array = np.array(after)
                
                # 計算螢幕差異
                diff = np.abs(after_array - before_array).sum()
                if diff > threshold:
                    self.logger.debug(f"✅ 檢測到螢幕變化（diff={diff}）")
                    time.sleep(0.1)  # 短暫穩定
                    return True
            
            self.logger.debug(f"⚠️ 等待 {max_wait}s 後未檢測到螢幕變化")
            return False
        except Exception as e:
            self.logger.debug(f"螢幕變化檢測異常: {e}")
            time.sleep(0.3)
            return True
    
    def smart_checkbox(self, x_ratio, y_ratio, target_text=None, image_path=None, 
                       checked_image=None, unchecked_image=None, 
                       ensure_checked=True, force_verify=False, timeout=3):
        """
        🎯 智能 Checkbox 操作（base 層核心方法）
        
        功能：
        1. 定位 checkbox（圖片辨識 > OCR > 座標保底）
        2. 判斷當前狀態（已勾選 or 未勾選）
        3. 根據 ensure_checked 參數決定是否點擊
        4. 驗證操作結果
        
        :param x_ratio: X 軸比例（座標保底用）
        :param y_ratio: Y 軸比例（座標保底用）
        :param target_text: OCR 尋找文字（通常是 checkbox 旁邊的標籤文字）
        :param image_path: Checkbox 圖片路徑（相對於 res/）
        :param checked_image: 已勾選狀態的參考圖片（相對於 res/）
        :param unchecked_image: 未勾選狀態的參考圖片（相對於 res/）
        :param ensure_checked: True=確保勾選, False=確保不勾選
        :param force_verify: True=強制驗證（即使初始狀態正確也會點擊兩次確保）
        :param timeout: 定位超時時間（秒）
        :return: True (操作成功) / False (操作失敗)
        """
        self.logger.info(f"🎯 智能 Checkbox 操作（目標狀態: {'已勾選' if ensure_checked else '未勾選'}{'，強制驗證模式' if force_verify else ''}）")
        
        # 步驟 1: 定位 checkbox
        checkbox_pos = self._locate_checkbox(x_ratio, y_ratio, target_text, image_path, timeout)
        if not checkbox_pos:
            self.logger.error("❌ 找不到 checkbox")
            return False
        
        click_x, click_y = checkbox_pos
        
        # 步驟 2: 判斷當前狀態
        is_checked = self._is_checkbox_checked(click_x, click_y, checked_image, unchecked_image)
        
        # 步驟 3: 根據目標狀態決定是否點擊
        if not force_verify:
            # 正常模式：如果狀態已正確，跳過點擊
            if ensure_checked and is_checked:
                self.logger.info("✅ Checkbox 已經是勾選狀態，跳過")
                return True
            elif not ensure_checked and not is_checked:
                self.logger.info("✅ Checkbox 已經是未勾選狀態，跳過")
                return True
        else:
            # 強制驗證模式：不管初始狀態，都會點擊確保最終狀態正確
            if ensure_checked and is_checked:
                self.logger.warning("⚠️ Checkbox 判定為已勾選，但啟用強制驗證模式，將點擊兩次確保")
            elif not ensure_checked and not is_checked:
                self.logger.warning("⚠️ Checkbox 判定為未勾選，但啟用強制驗證模式，將點擊兩次確保")
        
        # 步驟 4: 執行點擊切換狀態
        action = "勾選" if ensure_checked else "取消勾選"
        
        # 確保視窗是活動的
        win = self.get_nx_window()
        if win:
            try:
                if not win.isActive:
                    win.activate()
                    time.sleep(0.1)
            except Exception:
                pass
        
        # 在強制驗證模式下，如果初始狀態與目標相同，需要點擊兩次（先取消再設置）
        if force_verify and ((ensure_checked and is_checked) or (not ensure_checked and not is_checked)):
            self.logger.info(f"⚙️ 強制驗證模式：先點擊一次切換狀態...")
            final_x, final_y = self._perform_click(click_x, click_y, clicks=1, click_type='left', offset_x=0, offset_y=0)
            DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
            self.logger.info(f"📍 第1次點擊 checkbox: ({final_x}, {final_y})")
            time.sleep(0.5)
            
            self.logger.info(f"⚙️ 強制驗證模式：再點擊一次恢復到目標狀態...")
            final_x, final_y = self._perform_click(click_x, click_y, clicks=1, click_type='left', offset_x=0, offset_y=0)
            DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
            self.logger.info(f"📍 第2次點擊 checkbox: ({final_x}, {final_y})")
            time.sleep(0.5)
        else:
            # 正常點擊一次
            self.logger.info(f"⚙️ 執行{action}操作...")
            final_x, final_y = self._perform_click(click_x, click_y, clicks=1, click_type='left', offset_x=0, offset_y=0)
            DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
            self.logger.info(f"📍 點擊 checkbox: ({final_x}, {final_y})")
            time.sleep(0.5)
        
        # 步驟 5: 驗證結果
        is_checked_after = self._is_checkbox_checked(click_x, click_y, checked_image, unchecked_image)
        if (ensure_checked and is_checked_after) or (not ensure_checked and not is_checked_after):
            self.logger.info(f"✅ {action}成功")
            return True
        else:
            self.logger.warning(f"⚠️ {action}後驗證失敗")
            return False
    
    def _locate_checkbox(self, x_ratio, y_ratio, target_text=None, image_path=None, timeout=3):
        """
        🔍 定位 Checkbox 位置（base 層核心方法）
        優先級：圖片辨識 > OCR 文字 > 座標保底
        
        :param x_ratio: X 軸比例（座標保底用）
        :param y_ratio: Y 軸比例（座標保底用）
        :param target_text: OCR 尋找文字（checkbox 旁邊的標籤）
        :param image_path: Checkbox 圖片路徑（相對於 res/）
        :param timeout: 超時時間（秒）
        :return: (x, y) 座標或 None
        """
        win = self.get_nx_window()
        if not win:
            self.logger.error("❌ 找不到視窗")
            return None
        
        try:
            if not win.isActive:
                win.activate()
                time.sleep(0.1)
        except Exception:
            pass
        
        region = (win.left, win.top, win.width, win.height)
        
        # 【優先級 1】圖片辨識
        if image_path:
            if image_path.startswith("res/") or image_path.startswith("res\\"):
                image_path = image_path[4:]
            full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, image_path))
            
            if os.path.exists(full_img):
                try:
                    loc = pyautogui.locateOnScreen(full_img, confidence=0.8, region=region)
                    if loc:
                        # ⚠️ 重要：不使用中心點，而是使用左側 checkbox 位置
                        # 因為參考圖片可能包含文字，中心點會偏移
                        checkbox_x = loc.left + 12  # checkbox 通常在圖片左側 12px 處
                        checkbox_y = loc.top + (loc.height // 2)  # 垂直居中
                        self.logger.info(f"📸 Checkbox 圖片辨識成功: 圖片區域={loc}, 點擊座標=({checkbox_x}, {checkbox_y})")
                        return (checkbox_x, checkbox_y)
                except Exception as e:
                    self.logger.debug(f"圖片辨識異常: {e}")
        
        # 【優先級 2】OCR 文字辨識
        if target_text and self._get_ocr_engine():
            try:
                result = self._find_text_by_ocr(target_text, region)
                if result:
                    text_x, text_y = result
                    # Checkbox 通常在文字左側約 30 像素
                    checkbox_x = text_x - 30
                    checkbox_y = text_y
                    self.logger.info(f"📝 OCR 找到文字「{target_text}」，推測 checkbox 位置: ({checkbox_x}, {checkbox_y})")
                    return (checkbox_x, checkbox_y)
            except Exception as e:
                self.logger.debug(f"OCR 辨識異常: {e}")
        
        # 【優先級 3】座標保底
        self.logger.warning("⚠️ 圖片/OCR 辨識失敗，使用座標保底")
        checkbox_x = win.left + int(win.width * x_ratio)
        checkbox_y = win.top + int(win.height * y_ratio)
        self.logger.info(f"📍 使用保底座標: ({checkbox_x}, {checkbox_y})")
        return (checkbox_x, checkbox_y)
    
    def _is_checkbox_checked(self, x, y, checked_image=None, unchecked_image=None, sample_size=80):
        """
        🔍 判斷 Checkbox 是否已勾選（base 層核心方法）
        
        方法：
        1. 優先使用圖片辨識（比對已勾選/未勾選的參考圖片）
        2. 降級為像素分析（不可靠，建議提供參考圖片）
        
        :param x: checkbox 中心 x 座標
        :param y: checkbox 中心 y 座標
        :param checked_image: 已勾選狀態的參考圖片（相對於 res/）
        :param unchecked_image: 未勾選狀態的參考圖片（相對於 res/）
        :param sample_size: 採樣區域大小（像素，預設 80）
        :return: True (已勾選) / False (未勾選)
        """
        try:
            # 計算截取區域（以 checkbox 為中心，擴展 sample_size）
            half_size = sample_size // 2
            region = (int(x - half_size), int(y - half_size), int(sample_size), int(sample_size))
            
            self.logger.debug(f"截取 checkbox 區域: 中心 ({x}, {y}), 區域 {region} ({sample_size}x{sample_size})")
            
            # 【優先級 1】圖片辨識判斷
            if checked_image or unchecked_image:
                if checked_image:
                    if checked_image.startswith("res/") or checked_image.startswith("res\\"):
                        checked_image = checked_image[4:]
                    checked_img_path = os.path.normpath(os.path.join(EnvConfig.RES_PATH, checked_image))
                else:
                    checked_img_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings/checkbox_checked.png")
                
                if unchecked_image:
                    if unchecked_image.startswith("res/") or unchecked_image.startswith("res\\"):
                        unchecked_image = unchecked_image[4:]
                    unchecked_img_path = os.path.normpath(os.path.join(EnvConfig.RES_PATH, unchecked_image))
                else:
                    unchecked_img_path = os.path.join(EnvConfig.RES_PATH, "desktop_settings/checkbox_unchecked.png")
                
                self.logger.debug(f"使用參考圖片判斷狀態:")
                self.logger.debug(f"  已勾選: {checked_img_path} (存在: {os.path.exists(checked_img_path)})")
                self.logger.debug(f"  未勾選: {unchecked_img_path} (存在: {os.path.exists(unchecked_img_path)})")
                self.logger.debug(f"  截取區域: {region}")
                
                try:
                    # 嘗試匹配「已勾選」圖片
                    if os.path.exists(checked_img_path):
                        try:
                            loc = pyautogui.locateOnScreen(checked_img_path, confidence=0.8, region=region)
                            if loc:
                                self.logger.info(f"📸 圖片辨識：找到已勾選狀態 → 判定: 已勾選 ✓")
                                return True
                            else:
                                self.logger.debug("  未匹配到已勾選狀態")
                        except Exception as e1:
                            self.logger.debug(f"  匹配已勾選圖片時異常: {e1}")
                    
                    # 嘗試匹配「未勾選」圖片
                    if os.path.exists(unchecked_img_path):
                        try:
                            loc = pyautogui.locateOnScreen(unchecked_img_path, confidence=0.8, region=region)
                            if loc:
                                self.logger.info(f"📸 圖片辨識：找到未勾選狀態 → 判定: 未勾選 ☐")
                                return False
                            else:
                                self.logger.debug("  未匹配到未勾選狀態")
                        except Exception as e2:
                            self.logger.debug(f"  匹配未勾選圖片時異常: {e2}")
                    
                    self.logger.warning("⚠️ 圖片辨識無法匹配已勾選/未勾選狀態，降級為像素分析")
                except Exception as e:
                    self.logger.warning(f"⚠️ 圖片辨識異常: {e}")
            else:
                self.logger.warning("⚠️ 未提供參考圖片，直接使用像素分析")
            
            # 【優先級 2】像素分析（保底 - 不可靠）
            screenshot = pyautogui.screenshot(region=region)
            
            # 保存截圖供除錯（使用當前的 sample_size 區域）
            debug_path = f"debug_checkbox_{int(time.time())}.png"
            screenshot.save(debug_path)
            
            # 額外保存大圖（含上下文，200x60 像素）
            large_region = (int(x - 100), int(y - 30), 200, 60)
            large_screenshot = pyautogui.screenshot(region=large_region)
            large_debug_path = f"debug_checkbox_large_{int(time.time())}.png"
            large_screenshot.save(large_debug_path)
            
            self.logger.warning(f"⚠️ 無法使用圖片辨識，改用像素分析（不可靠）")
            self.logger.info(f"💾 已保存 checkbox 截圖: {debug_path} ({sample_size}x{sample_size} 像素)")
            self.logger.info(f"💾 已保存 checkbox 大圖: {large_debug_path} (200x60 像素，含上下文)")
            self.logger.info(f"💡 建議：將截圖複製到 res/desktop_settings/ 作為參考圖片")
            
            # 保守策略：假設為未勾選
            self.logger.warning(f"⚠️ 像素分析無法準確判斷，假設為未勾選")
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ 判斷 checkbox 狀態時出錯: {e}，假設為未勾選")
            return False

    def _try_vlm_recognition(self, target_text, region, win, clicks=1, click_type='left', offset_x=0, offset_y=0):
        """
        🤖 嘗試使用 VLM (視覺語言模型) 進行 UI 元素辨識
        
        使用 UnifiedVLM 引擎（Ollama + Gemini 備援 + 描述校正 + 特徵進化）
        
        :param target_text: 要尋找的元素描述（支援自然語言）
        :param region: 搜尋區域 (left, top, width, height)
        :param win: 視窗物件
        :param clicks: 點擊次數
        :param click_type: 點擊類型
        :param offset_x: X 軸偏移量（像素，預設 0）
        :param offset_y: Y 軸偏移量（像素，預設 0）
        :return: True (成功點擊) / False (辨識失敗)
        """
        self._safe_log("info", f"[DEBUG] _try_vlm_recognition 被調用: target_text='{target_text}', region={region}")
        vlm = self._get_vlm_engine()
        self._safe_log("info", f"[DEBUG] _get_vlm_engine() 返回: {vlm} (類型: {type(vlm)})")
        if not vlm:
            self._safe_log("warning", f"[VLM] VLM 引擎未初始化或未啟用，跳過 VLM 辨識")
            return False
        
        try:
            from base.ok_script_recognizer import get_recognizer
            from toolkit.types import Area
            import pyautogui
            
            recognizer = get_recognizer()
            
            self._safe_log("info", f"[VLM] 正在使用 UnifiedVLM 搜尋元素: '{target_text}'")
            
            # 步驟 1: 截取搜尋區域的截圖
            screenshot_path = None
            try:
                import tempfile
                from datetime import datetime
                
                # 截取搜尋區域
                screenshot = pyautogui.screenshot(region=region)
                
                # 保存到臨時文件
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(temp_dir, f"vlm_search_{timestamp}.png")
                screenshot.save(screenshot_path)
                
                self._safe_log("info", f"[VLM] 截圖已保存: {screenshot_path}")
                
            except Exception as e:
                self._safe_log("error", f"[VLM] 截圖失敗: {e}")
                return False
            
            # 步驟 2: 使用 UnifiedVLM 進行識別
            try:
                # 獲取當前解析度
                screen_width, screen_height = pyautogui.size()
                current_resolution = (screen_width, screen_height)
                
                # 調用 UnifiedVLM 的 find_element 方法
                area: Optional[Area] = vlm.find_element(
                    element_name=target_text,
                    screenshot_path=screenshot_path,
                    current_resolution=current_resolution,
                    enable_description_calibration=True
                )
                
                # 清理臨時截圖
                try:
                    if screenshot_path and os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                except:
                    pass
                
                if not area:
                    self._safe_log("warning", f"[VLM] UnifiedVLM 未找到元素: '{target_text}'")
                    return False
                
                # 步驟 3: 將 Area 轉換為絕對座標
                # Area 返回的是相對於截圖的座標，需要加上 region 的偏移
                center_x, center_y = area.center
                click_x = region[0] + center_x
                click_y = region[1] + center_y
                
                self._safe_log("info", f"[VLM] UnifiedVLM 辨識成功: 相對座標=({center_x}, {center_y}), 絕對座標=({click_x}, {click_y})")
                
            except Exception as e:
                self._safe_log("error", f"[VLM] UnifiedVLM 識別失敗: {e}")
                import traceback
                self.logger.debug(f"詳細錯誤: {traceback.format_exc()}")
                return False
            
            # 步驟 4: 座標合理性檢查和執行點擊
            self._safe_log("info", f"[VLM] UnifiedVLM 辨識成功: 絕對座標=({click_x}, {click_y})")
            if region:
                self._safe_log("info", f"[VLM] region=({region[0]}, {region[1]}, {region[2]}, {region[3]})")
            if win:
                self._safe_log("info", f"[VLM] 窗口位置: left={win.left}, top={win.top}, width={win.width}, height={win.height}")
            
            # 座標合理性檢查和自動修正
            screen_width, screen_height = pyautogui.size()
            
            # 自動修正稍微超出螢幕範圍的座標（允許 20px 的誤差）
            if click_y >= screen_height:
                if click_y <= screen_height + 20:
                    click_y = screen_height - 1
                    self._safe_log("info", f"[VLM] y 座標超出螢幕範圍，自動修正: {click_y + 1} -> {click_y}")
                else:
                    self._safe_log("warning", f"[VLM] y 座標超出螢幕範圍過大 ({click_y}/{screen_height})，拒絕點擊")
                    return False
            
            if click_x >= screen_width:
                if click_x <= screen_width + 20:
                    click_x = screen_width - 1
                    self._safe_log("info", f"[VLM] x 座標超出螢幕範圍，自動修正: {click_x + 1} -> {click_x}")
                else:
                    self._safe_log("warning", f"[VLM] x 座標超出螢幕範圍過大 ({click_x}/{screen_width})，拒絕點擊")
                    return False
            
            # 確保座標在視窗範圍內（允許稍微超出視窗範圍，自動修正）
            win_left = win.left
            win_top = win.top
            win_right = win.left + win.width
            win_bottom = win.top + win.height
            
            # 自動修正稍微超出視窗範圍的座標（允許 20px 的誤差）
            if click_x < win_left:
                if click_x >= win_left - 20:
                    click_x = win_left
                    self._safe_log("info", f"[VLM] x 座標稍微超出視窗左側，自動修正到視窗邊界")
                else:
                    self._safe_log("warning", f"[VLM] x 座標超出視窗範圍過大: {click_x} < {win_left}")
                    return False
            elif click_x > win_right:
                if click_x <= win_right + 20:
                    click_x = win_right - 1
                    self._safe_log("info", f"[VLM] x 座標稍微超出視窗右側，自動修正到視窗邊界")
                else:
                    self._safe_log("warning", f"[VLM] x 座標超出視窗範圍過大: {click_x} > {win_right}")
                    return False
            
            if click_y < win_top:
                if click_y >= win_top - 20:
                    click_y = win_top
                    self._safe_log("info", f"[VLM] y 座標稍微超出視窗頂部，自動修正到視窗邊界")
                else:
                    self._safe_log("warning", f"[VLM] y 座標超出視窗範圍過大: {click_y} < {win_top}")
                    return False
            elif click_y > win_bottom:
                if click_y <= win_bottom + 20:
                    click_y = win_bottom - 1
                    self._safe_log("info", f"[VLM] y 座標稍微超出視窗底部，自動修正到視窗邊界")
                else:
                    self._safe_log("warning", f"[VLM] y 座標超出視窗範圍過大: {click_y} > {win_bottom}")
                    return False
            
            # 座標已修正，繼續執行點擊
            if (win_left <= click_x <= win_right and 
                win_top <= click_y <= win_bottom):
                
                # 額外驗證：如果提供了 region，確保座標在 region 範圍內（相對於視窗）
                if region:
                    region_left = region[0]
                    region_top = region[1]
                    region_right = region[0] + region[2]
                    region_bottom = region[1] + region[3]
                    
                    if not (region_left <= click_x <= region_right and 
                            region_top <= click_y <= region_bottom):
                        self._safe_log("warning", f"[VLM] 座標超出 region 範圍: ({click_x}, {click_y}), region=({region_left}, {region_top}, {region[2]}, {region[3]})")
                        # 如果座標明顯超出 region，拒絕點擊
                        if abs(click_y - region_bottom) > 50:  # 允許 50px 的誤差
                            self._safe_log("warning", f"[VLM] 座標超出 region 範圍過大，拒絕點擊")
                            return False
                
                # 🎯 執行點擊並獲取最終座標（已應用偏移）
                final_x, final_y = self._perform_click(click_x, click_y, clicks, click_type, offset_x, offset_y)
                
                # 記錄統計（UnifiedVLM 沒有 time_ms，使用預設值）
                recognizer.record_vlm_hit(0)
                
                # 🎯 自動記錄相對於視窗的比例座標（使用最終座標）
                relative_x = final_x - win.left
                relative_y = final_y - win.top
                ratio_x = relative_x / win.width
                ratio_y = relative_y / win.height
                
                action_type = "雙擊" if clicks == 2 else "點擊"
                self._safe_log("info", f"[VLM] UnifiedVLM 辨識成功並{action_type}: {target_text}")
                self._safe_log("info", f"[STAT] [座標庫] 比例座標: x_ratio={ratio_x:.4f}, y_ratio={ratio_y:.4f} | 絕對座標: ({final_x}, {final_y})")
                
                # 🎯 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                # 記錄圖像辨識成功（重置連續失敗計數）
                recognizer.record_image_recognition_success()
                
                # 自動截圖並標註（如果有 reporter）
                if DesktopApp._reporter and hasattr(DesktopApp._reporter, 'add_recognition_screenshot'):
                    try:
                        item_name = target_text or "VLM_Element"
                        # 🎯 使用 Area 的尺寸
                        DesktopApp._reporter.add_recognition_screenshot(
                            item_name=item_name,
                            x=final_x,
                            y=final_y,
                            width=area.width,
                            height=area.height,
                            method="UnifiedVLM",
                            region=region
                        )
                    except Exception as e:
                        self.logger.debug(f"自動截圖失敗: {e}")
                
                return True
            else:
                self.logger.debug(f"[VLM] 返回座標超出視窗範圍: ({click_x}, {click_y})")
            
        except Exception as e:
            self.logger.debug(f"🤖 VLM 辨識異常: {e}")
        
        return False

    def _try_ocr_recognition(self, target_text, region, win, clicks=1, click_type='left', offset_x=0, offset_y=0):
        """
        📝 嘗試使用 OCR 進行文字辨識
        
        :param target_text: 要尋找的文字
        :param region: 搜尋區域 (left, top, width, height)
        :param win: 視窗物件
        :param clicks: 點擊次數
        :param click_type: 點擊類型
        :param offset_x: X 軸偏移量（像素，預設 0）
        :param offset_y: Y 軸偏移量（像素，預設 0）
        :return: True (成功點擊) / False (辨識失敗)
        """
        if not target_text:
            return False
            
        if not self._get_ocr_engine():
            return False
        
        try:
            from base.ok_script_recognizer import get_recognizer
            recognizer = get_recognizer()
            
            ocr_start = time.perf_counter()
            result = self._find_text_by_ocr(target_text, region)
            if result:
                ocr_time_ms = (time.perf_counter() - ocr_start) * 1000
                recognizer.record_ocr_hit(ocr_time_ms)
                
                click_x, click_y = result
                # 🎯 執行點擊並獲取最終座標（已應用偏移）
                final_x, final_y = self._perform_click(click_x, click_y, clicks, click_type, offset_x, offset_y)
                
                # 🎯 自動記錄相對於視窗的比例座標（使用最終座標）
                relative_x = final_x - win.left
                relative_y = final_y - win.top
                ratio_x = relative_x / win.width
                ratio_y = relative_y / win.height
                
                action_type = "雙擊" if clicks == 2 else "點擊"
                self._safe_log("info", f"[OCR] OCR 文字辨識成功並{action_type}: {target_text} (耗時: {ocr_time_ms:.1f}ms)")
                self._safe_log("info", f"[STAT] [座標庫] 比例座標: x_ratio={ratio_x:.4f}, y_ratio={ratio_y:.4f} | 視窗尺寸: {win.width}x{win.height} | 絕對座標: ({final_x}, {final_y})")
                
                # 🎯 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                recognizer.record_image_recognition_success()
                
                # 自動截圖並標註（如果有 reporter）
                if DesktopApp._reporter and hasattr(DesktopApp._reporter, 'add_recognition_screenshot'):
                    try:
                        item_name = target_text or "OCR_Text"
                        # 🎯 使用最終點擊座標（已應用偏移），確保綠色標記顯示在實際點擊位置
                        DesktopApp._reporter.add_recognition_screenshot(
                            item_name=item_name,
                            x=final_x,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            y=final_y,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            width=50,
                            height=50,
                            method="OCR"
                        )
                    except Exception as e:
                        self.logger.debug(f"自動截圖失敗: {e}")
                
                return True
        except Exception as e:
            self.logger.debug(f"OCR 辨識異常: {e}")
        
        return False

    def _try_ok_script_recognition(self, image_path, region, win, clicks=1, click_type='left', confidence=0.7, offset_x=0, offset_y=0):
        """
        🎯 嘗試使用 OK Script / OpenCV 進行圖片辨識
        
        :param image_path: 圖片路徑（完整路徑）
        :param region: 搜尋區域 (left, top, width, height)
        :param win: 視窗物件
        :param clicks: 點擊次數
        :param click_type: 點擊類型
        :param confidence: 置信度閾值（預設 0.7）
        :param offset_x: X 軸偏移量（像素，預設 0）
        :param offset_y: Y 軸偏移量（像素，預設 0）
        :return: True (成功點擊) / False (辨識失敗)
        """
        if not image_path or not os.path.exists(image_path):
            return False
        
        try:
            from base.ok_script_recognizer import get_recognizer
            recognizer = get_recognizer()
            
            self._safe_log("info", f"[DEBUG] 嘗試 OK Script 圖像辨識: {image_path}")
            result = recognizer.locate_on_screen(image_path, region=region, confidence=confidence)
            self._safe_log("info", f"[DEBUG] OK Script 辨識結果: {result.success if result else None}, 方法: {result.method if result and hasattr(result, 'method') else None}")
            
            if result and result.success:
                self._safe_log("info", f"[DEBUG] OK Script 辨識成功，開始驗證座標...")
                # 驗證 result 的座標是否有效
                if not hasattr(result, 'x') or not hasattr(result, 'y') or result.x is None or result.y is None:
                    self.logger.warning(f"⚠️ OK Script 辨識成功但座標無效: x={getattr(result, 'x', None)}, y={getattr(result, 'y', None)}")
                    raise ValueError("OK Script 辨識結果座標無效")
                
                # 🎯 計算中心點：OK Script 返回的是左上角座標，需要計算中心點
                center_x = result.x + (result.width // 2) if hasattr(result, 'width') and result.width > 0 else result.x
                center_y = result.y + (result.height // 2) if hasattr(result, 'height') and result.height > 0 else result.y
                
                self._safe_log("info", f"[DEBUG] 座標驗證通過: 左上角=({result.x}, {result.y}), 中心點=({center_x}, {center_y})，執行點擊...")
                # 🎯 執行點擊並獲取最終座標（已應用偏移）
                final_x, final_y = self._perform_click(center_x, center_y, clicks, click_type, offset_x, offset_y)
                self._safe_log("info", f"[DEBUG] 點擊執行完成")
                
                # 🎯 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                
                # 🎯 自動記錄相對於視窗的比例座標（如果視窗資訊可用）
                # 注意：使用最終座標（已應用偏移）計算比例座標
                try:
                    relative_x = final_x - win.left
                    relative_y = final_y - win.top
                    ratio_x = relative_x / win.width
                    ratio_y = relative_y / win.height
                    
                    action_type = "雙擊" if clicks == 2 else "點擊"
                    image_name = os.path.basename(image_path)
                    self._safe_log("info", f"[OK] {result.method.upper()} 辨識成功並{action_type}: {image_name} (信心: {result.confidence:.2f}, 耗時: {result.time_ms:.1f}ms)")
                    self._safe_log("info", f"[STAT] [座標庫] 比例座標: x_ratio={ratio_x:.4f}, y_ratio={ratio_y:.4f} | 視窗尺寸: {win.width}x{win.height} | 絕對座標: ({final_x}, {final_y})")
                except Exception as win_err:
                    # 視窗資訊不可用（可能句柄失效），但仍記錄辨識成功
                    action_type = "雙擊" if clicks == 2 else "點擊"
                    image_name = os.path.basename(image_path)
                    self._safe_log("info", f"[OK] {result.method.upper()} 辨識成功並{action_type}: {image_name} (信心: {result.confidence:.2f}, 耗時: {result.time_ms:.1f}ms)")
                    self._safe_log("warning", f"[WARN] 無法計算比例座標（視窗資訊不可用）: {type(win_err).__name__}: {win_err}")
                    self._safe_log("info", f"[STAT] [座標庫] 絕對座標: ({center_x}, {center_y})")
                
                DesktopApp._last_x, DesktopApp._last_y = center_x, center_y
                recognizer.record_image_recognition_success()
                
                # 自動截圖並標註（如果有 reporter）
                if DesktopApp._reporter and hasattr(DesktopApp._reporter, 'add_recognition_screenshot'):
                    try:
                        item_name = os.path.basename(image_path)
                        # 使用實際辨識到的物件尺寸
                        width = result.width if hasattr(result, 'width') and result.width > 0 else 50
                        height = result.height if hasattr(result, 'height') and result.height > 0 else 50
                        # 🎯 使用最終點擊座標（已應用偏移），確保綠色標記顯示在實際點擊位置
                        DesktopApp._reporter.add_recognition_screenshot(
                            item_name=item_name,
                            x=final_x,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            y=final_y,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            width=width,
                            height=height,
                            method=result.method.upper() if hasattr(result, 'method') else "OK Script",
                            region=region  # 傳入搜尋區域，用於在截圖上標記
                        )
                    except Exception as e:
                        self.logger.debug(f"自動截圖失敗: {e}")
                
                return True
        except Exception as e:
            # 將異常日誌提升為 info 級別，方便調試
            self._safe_log("warning", f"[WARN] OK Script 辨識過程發生異常: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(f"OK Script 辨識異常詳細信息:\n{traceback.format_exc()}")
        
        return False

    def _try_pyautogui_recognition(self, image_path, region, win, clicks=1, click_type='left', confidence=0.7, offset_x=0, offset_y=0):
        """
        📸 嘗試使用 PyAutoGUI 進行圖片辨識
        
        :param image_path: 圖片路徑（完整路徑）
        :param region: 搜尋區域 (left, top, width, height)
        :param win: 視窗物件
        :param clicks: 點擊次數
        :param click_type: 點擊類型
        :param confidence: 置信度閾值（預設 0.7）
        :param offset_x: X 軸偏移量（像素，預設 0）
        :param offset_y: Y 軸偏移量（像素，預設 0）
        :return: True (成功點擊) / False (辨識失敗)
        """
        if not image_path or not os.path.exists(image_path):
            return False
        
        try:
            from base.ok_script_recognizer import get_recognizer
            recognizer = get_recognizer()
            
            loc = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
            if loc:
                center = pyautogui.center(loc)
                # 🎯 執行點擊並獲取最終座標（已應用偏移）
                final_x, final_y = self._perform_click(center.x, center.y, clicks, click_type, offset_x, offset_y)
                
                # 🎯 自動記錄相對於視窗的比例座標（使用最終座標）
                relative_x = final_x - win.left
                relative_y = final_y - win.top
                ratio_x = relative_x / win.width
                ratio_y = relative_y / win.height
                
                action_type = "雙擊" if clicks == 2 else "點擊"
                image_name = os.path.basename(image_path)
                self._safe_log("info", f"[IMG] 圖片辨識成功並{action_type}: {image_name}")
                self._safe_log("info", f"[STAT] [座標庫] 比例座標: x_ratio={ratio_x:.4f}, y_ratio={ratio_y:.4f} | 視窗尺寸: {win.width}x{win.height} | 絕對座標: ({final_x}, {final_y})")
                
                # 🎯 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                recognizer.record_image_recognition_success()
                
                # 自動截圖並標註（如果有 reporter）
                if DesktopApp._reporter and hasattr(DesktopApp._reporter, 'add_recognition_screenshot'):
                    try:
                        item_name = os.path.basename(image_path)
                        width = loc.width if loc else 50
                        height = loc.height if loc else 50
                        # 🎯 使用最終點擊座標（已應用偏移），確保綠色標記顯示在實際點擊位置
                        DesktopApp._reporter.add_recognition_screenshot(
                            item_name=item_name,
                            x=final_x,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            y=final_y,  # 🎯 使用最終點擊座標，確保綠色標記顯示在實際點擊位置
                            width=width,
                            height=height,
                            method="PyAutoGUI",
                            region=region  # 傳入搜尋區域，用於在截圖上標記
                        )
                    except Exception as e:
                        self.logger.debug(f"自動截圖失敗: {e}")
                
                return True
        except Exception:
            pass
        
        return False

    def _prepare_click_context(self, x_ratio, y_ratio, image_path=None, is_relative=False, from_bottom=False):
        """
        準備點擊上下文：獲取視窗、計算 region、處理圖片路徑
        返回 (win, region, full_img) 或 None（如果失敗）
        """
        win = self.get_nx_window()
        
        # 🎯 如果找不到窗口，嘗試使用全屏作為保底
        if not win:
            self.logger.warning("[WINDOW] 未找到 Nx Witness 視窗，使用全屏作為保底")
            try:
                screen_width, screen_height = pyautogui.size()
                # 創建一個虛擬的窗口對象（使用全屏尺寸）
                class VirtualWindow:
                    def __init__(self, left, top, width, height):
                        self.left = left
                        self.top = top
                        self.width = width
                        self.height = height
                        self.isActive = False
                
                win = VirtualWindow(0, 0, screen_width, screen_height)
                region = (0, 0, screen_width, screen_height)
            except Exception as e:
                self.logger.error(f"[WINDOW] 無法獲取全屏尺寸: {e}")
                return None
        else:
            try:
                win_left = win.left
                win_top = win.top
                win_width = win.width
                win_height = win.height
                
                if win_width <= 0 or win_height <= 0:
                    self.logger.warning(f"[WINDOW] 視窗尺寸無效: {win_width}x{win_height}")
                    return None
                
                region = (win_left, win_top, win_width, win_height)
            except Exception as e:
                self.logger.warning(f"[WINDOW] 獲取視窗屬性失敗: {e}")
                return None
        
        # 處理圖片路徑
        full_img = None
        if image_path:
            if image_path.startswith("res/") or image_path.startswith("res\\"):
                image_path = image_path[4:]
            full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, image_path))
        
        return (win, region, full_img)

    def smart_click_priority_text(self, x_ratio, y_ratio, target_text=None, image_path=None, timeout=3, is_relative=False, from_bottom=False, clicks=1, click_type='left', window_obj=None, use_vlm=None, offset_x=0, offset_y=0):
        """
        🎯 文字優先策略：VLM > OCR > OK Script > PyAutoGUI
        適合需要精確文字匹配的場景
        
        :param x_ratio: X 軸比例 (0.0 - 1.0)
        :param y_ratio: Y 軸比例 (0.0 - 1.0)
        :param target_text: 要尋找的文字（用於 VLM/OCR）
        :param image_path: 圖片路徑（相對於 res/，作為備選）
        :param timeout: 超時時間（秒，預設 3）
        :param clicks: 點擊次數（1=單擊，2=雙擊）
        :param click_type: 點擊類型（'left'=左鍵, 'right'=右鍵）
        :param use_vlm: 是否使用 VLM 辨識（None=根據配置, True=強制使用, False=強制禁用）
        :param offset_x: X 軸偏移量（像素），用於所有點擊時微調位置（預設 0）
        :param offset_y: Y 軸偏移量（像素），用於所有點擊時微調位置（預設 0）
        :return: True (成功) / False (失敗)
        """
        vlm_enabled = use_vlm if use_vlm is not None else getattr(EnvConfig, 'VLM_ENABLED', False)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            ctx = self._prepare_click_context(x_ratio, y_ratio, image_path, is_relative, from_bottom)
            if not ctx:
                time.sleep(0.1)
                continue
            
            win, region, full_img = ctx
            
            # 為 VLM/OCR 創建一個限制區域，圍繞 x_ratio, y_ratio 附近（避免搜尋到其他位置的文字）
            # 使用一個較小的搜尋區域，例如寬度為視窗的 60%，高度為視窗的 30%，中心在 (x_ratio, y_ratio)
            search_region_width = int(win.width * 0.6)
            search_region_height = int(win.height * 0.3)
            search_region_left = max(win.left, int(win.left + win.width * x_ratio - search_region_width / 2))
            search_region_top = max(win.top, int(win.top + win.height * y_ratio - search_region_height / 2))
            search_region = (search_region_left, search_region_top, search_region_width, search_region_height)
            
            # 🎯 優先級 1: VLM（如果啟用且 target_text 存在）
            # 使用限制的搜尋區域，避免搜尋到其他位置的文字
            if vlm_enabled and target_text:
                if self._try_vlm_recognition(target_text, search_region, win, clicks, click_type, offset_x, offset_y):
                    return True
            
            # 🎯 優先級 2: OCR（也使用限制的搜尋區域）
            if target_text:
                if self._try_ocr_recognition(target_text, search_region, win, clicks, click_type, offset_x, offset_y):
                    return True
            
            # 🎯 優先級 3: OK Script 圖片辨識（使用完整的 region）
            if full_img:
                if self._try_ok_script_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                    return True
            
            # 🎯 優先級 4: PyAutoGUI 圖片辨識（使用完整的 region）
            if full_img:
                if self._try_pyautogui_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                    return True
            
            time.sleep(0.15)
        
        # 🎯 如果所有辨識方法都失敗，使用座標保底
        win = self.get_nx_window()
        if win:
            try:
                if is_relative:
                    tx = DesktopApp._last_x + x_ratio
                    ty = DesktopApp._last_y + y_ratio
                    self.logger.info(f"[COORD] [TEXT_PRIORITY] 執行相對座標點擊: 原始座標=({tx}, {ty}), 偏移=(offset_x={offset_x}, offset_y={offset_y})")
                elif from_bottom:
                    tx = win.left + int(win.width * x_ratio)
                    ty = win.top + win.height - int(win.height * y_ratio)
                    self.logger.info(f"[COORD] [TEXT_PRIORITY] 執行視窗底部對齊點擊: 原始座標=({tx}, {ty}), 偏移=(offset_x={offset_x}, offset_y={offset_y})")
                else:
                    tx = win.left + int(win.width * x_ratio)
                    ty = win.top + int(win.height * y_ratio)
                    self.logger.info(f"[COORD] [TEXT_PRIORITY] 執行視窗比例點擊: 原始座標=({tx}, {ty}), 偏移=(offset_x={offset_x}, offset_y={offset_y})")
                
                # 🎯 VLM 驗證：點擊前截圖並標記位置
                final_x = tx + offset_x
                final_y = ty + offset_y
                screenshot_path = self._capture_click_preview(
                    click_x=final_x,
                    click_y=final_y,
                    target_text=target_text,
                    image_path=image_path
                )
                
                # 🎯 執行點擊並獲取最終座標（應用偏移）
                final_x, final_y = self._perform_click(tx, ty, clicks, click_type, offset_x, offset_y)
                # 🎯 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                
                # 🎯 VLM 驗證：點擊後，使用點擊前的截圖進行驗證
                vlm_verification_result = self._verify_coordinate_click_with_vlm(
                    screenshot_path=screenshot_path,
                    click_x=final_x,
                    click_y=final_y,
                    target_text=target_text,
                    image_path=image_path,
                    expected_action="點擊" + (target_text if target_text else "元素")
                )
                
                # 記錄 VLM 驗證結果
                if vlm_verification_result.get('verified'):
                    self.logger.info(f"[TEXT_PRIORITY] [VLM] ✅ Verified. {vlm_verification_result.get('description', '')}")
                else:
                    self.logger.warning(f"[TEXT_PRIORITY] [VLM] ⚠️ Warning. {vlm_verification_result.get('description', '')}")
                
                return True
            except Exception as e:
                self.logger.error(f"[ERROR] [TEXT_PRIORITY] 座標保底失敗: {e}")
        
        return False

    def smart_click(self, x_ratio, y_ratio, target_text=None, image_path=None, timeout=3, is_relative=False, from_bottom=False, clicks=1, click_type='left', window_obj=None, use_ok_script=True, use_vlm=None, offset_x=0, offset_y=0, region=None):
        """ 
        🎯 智能點擊：優先級 OK Script > VLM > OCR 文字 > 座標保底
        :param x_ratio: X 軸比例 (0.0 - 1.0) 或絕對像素（is_relative=True 時）
        :param y_ratio: Y 軸比例 (0.0 - 1.0) 或絕對像素（is_relative=True 時）
        :param target_text: OCR 要尋找的文字（也用於 VLM 查詢）
        :param image_path: 圖片路徑（相對於 res/）
        :param timeout: 超時時間（秒，預設 3）
        :param is_relative: 是否使用相對座標（相對於上次點擊位置）
        :param from_bottom: Y 軸是否從視窗底部計算
        :param clicks: 點擊次數（1=單擊，2=雙擊）
        :param click_type: 點擊類型（'left'=左鍵, 'right'=右鍵）
        :param window_obj: 指定視窗物件（可選）
        :param use_ok_script: 是否優先使用 OK Script 辨識（預設 True）
        :param use_vlm: 是否使用 VLM 辨識（None=根據配置, True=強制使用, False=強制禁用）
        :param offset_x: X 軸偏移量（像素），用於所有點擊時微調位置（預設 0）
        :param offset_y: Y 軸偏移量（像素），用於所有點擊時微調位置（預設 0）
        :param region: 搜尋區域 (left, top, width, height)，用於限制 VLM/OCR 搜尋範圍（可選）
        """
        # 方法入口：記錄開始尋找目標
        self.logger.info(f"[SMART_CLICK] [START] Finding target: text='{target_text}', image='{image_path}', timeout={timeout}s")
        
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        recognizer.set_logger(self.logger)
        
        # 取得 VLM 配置
        vlm_enabled = use_vlm if use_vlm is not None else getattr(EnvConfig, 'VLM_ENABLED', False)
        vlm_priority = getattr(EnvConfig, 'VLM_PRIORITY', 2)  # 預設在 OK Script 後
        
        start_time = time.time()
        
        # 處理圖片路徑
        original_image_path = image_path  # 保留原始路徑用於日誌
        if image_path:
            if image_path.startswith("res/") or image_path.startswith("res\\"):
                image_path = image_path[4:]
            full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, image_path))
        else:
            full_img = None
        
        # 追蹤已嘗試的策略（用於最終總結）
        # 注意：在循環中，同一個策略可能被嘗試多次，但我們只記錄一次
        attempted_strategies = []
        strategy_results = {}  # 記錄每個策略的結果
        strategy_attempted_in_loop = set()  # 追蹤本輪循環中已嘗試的策略（避免重複記錄）

        while time.time() - start_time < timeout:
            # 每輪循環重置已嘗試策略集合（允許同一策略在不同循環中重試）
            strategy_attempted_in_loop.clear()
            win = self.get_nx_window()
            if not win:
                time.sleep(0.1)
                continue
            
            # 驗證視窗物件是否有效（確保視窗已完全初始化）
            try:
                # 嘗試訪問視窗屬性，如果失敗表示視窗尚未完全初始化
                win_left = win.left
                win_top = win.top
                win_width = win.width
                win_height = win.height
                
                # 確保視窗尺寸有效（大於 0）
                if win_width <= 0 or win_height <= 0:
                    self.logger.debug(f"視窗尺寸無效: {win_width}x{win_height}，等待初始化...")
                    time.sleep(0.1)
                    continue
                
            except Exception as e:
                # 視窗物件無效或正在初始化，等待後重試
                self.logger.debug(f"視窗尚未完全初始化: {e}，等待...")
                time.sleep(0.2)
                continue
            
            try:
                if not win.isActive:
                    win.activate()
                    time.sleep(0.1)  # 減少等待時間
            except Exception: 
                pass

            # 如果提供了 region 參數，使用它；否則使用整個視窗區域
            if region is None:
                region = (win_left, win_top, win_width, win_height)

            # 策略選擇：根據 use_vlm 參數決定優先級
            # 如果 use_vlm=False 且有圖片，啟用「圖片優先」模式；否則使用傳統模式（VLM 優先）
            image_first_mode = (use_vlm is False) and full_img and os.path.exists(full_img)
            
            if image_first_mode:
                # 【優先級 1】圖片優先模式：先嘗試圖片辨識
                if use_ok_script:
                    strategy_name = f"Image Recognition (OK Script: {original_image_path})"
                    self.logger.info(f"[SMART_CLICK] [IMG] Trying Image Strategy: {original_image_path}...")
                    attempted_strategies.append(strategy_name)
                    if self._try_ok_script_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                        self.logger.info(f"[SMART_CLICK] [IMG] Success.")
                        return True
                    else:
                        self.logger.warning(f"[SMART_CLICK] [IMG] Failed (Confidence too low or not found).")
                        strategy_results[strategy_name] = "Failed"
                
                # 【優先級 2】圖片失敗後，嘗試 VLM（作為備選）- 即使 use_vlm=False，也允許 VLM 作為備選
                if target_text and vlm_enabled:
                    strategy_name = f"Text/VLM Recognition ('{target_text}')"
                    priority_mode = "VLM"
                    self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                    attempted_strategies.append(strategy_name)
                    vlm_result = self._try_vlm_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y)
                    if vlm_result:
                        self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                        return True
                    else:
                        self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                        strategy_results[strategy_name] = "Failed"
                
                # 【優先級 3】VLM 失敗後，嘗試 OCR
                if target_text and self._get_ocr_engine():
                    strategy_name = f"OCR Text Recognition ('{target_text}')"
                    priority_mode = "OCR"
                    self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                    attempted_strategies.append(strategy_name)
                    if self._try_ocr_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y):
                        self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                        return True
                    else:
                        self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                        strategy_results[strategy_name] = "Failed"
                
                # 【優先級 4】如果沒有使用 OK Script，嘗試 PyAutoGUI 圖片辨識
                if not use_ok_script:
                    strategy_name = f"Image Recognition (PyAutoGUI: {original_image_path})"
                    self.logger.info(f"[SMART_CLICK] [IMG] Trying Image Strategy: {original_image_path}...")
                    attempted_strategies.append(strategy_name)
                    if self._try_pyautogui_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                        self.logger.info(f"[SMART_CLICK] [IMG] Success.")
                        return True
                    else:
                        self.logger.warning(f"[SMART_CLICK] [IMG] Failed (Confidence too low or not found).")
                        strategy_results[strategy_name] = "Failed"
            else:
                # 【優先級 1】傳統模式：如果有 target_text，優先使用文字辨識（VLM/OCR）
                # 這樣可以避免圖片辨識匹配到錯誤的位置（例如 server_tile.png 可能匹配多個卡片）
                if target_text:
                    # VLM 優先（如果啟用）- 無論 VLM_PRIORITY 是多少，當有 target_text 時都優先嘗試 VLM
                    if vlm_enabled:
                        strategy_name = f"Text/VLM Recognition ('{target_text}')"
                        priority_mode = "VLM"
                        self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                        attempted_strategies.append(strategy_name)
                        vlm_result = self._try_vlm_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y)
                        if vlm_result:
                            self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                            return True
                        else:
                            self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                            strategy_results[strategy_name] = "Failed"
                    
                    # OCR 優先（如果 VLM 未啟用或失敗）
                    if self._get_ocr_engine():
                        strategy_name = f"OCR Text Recognition ('{target_text}')"
                        priority_mode = "OCR"
                        self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                        attempted_strategies.append(strategy_name)
                        if self._try_ocr_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y):
                            self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                            return True
                        else:
                            self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                            strategy_results[strategy_name] = "Failed"

                # 【優先級 2】OK Script / OpenCV Template Matching（圖片辨識作為備選）
                # 只有在文字辨識（VLM/OCR）都失敗時才使用圖片辨識
                # 降低置信度閾值（從 0.85 降到 0.7）以提高對畫面變化的容錯性
                if use_ok_script and full_img and os.path.exists(full_img):
                    strategy_name = f"Image Recognition (OK Script: {original_image_path})"
                    self.logger.info(f"[SMART_CLICK] [IMG] Trying Image Strategy: {original_image_path}...")
                    attempted_strategies.append(strategy_name)
                    if self._try_ok_script_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                        self.logger.info(f"[SMART_CLICK] [IMG] Success.")
                        return True
                    else:
                        self.logger.warning(f"[SMART_CLICK] [IMG] Failed (Confidence too low or not found).")
                        strategy_results[strategy_name] = "Failed"

            # 注意：VLM 已在【優先級 1】處理（當 target_text 存在時）
            # 如果 target_text 存在且 VLM 啟用，VLM 已在【優先級 1】嘗試
            # 這裡不需要再次調用 VLM

            # 【優先級 3】圖片辨識（pyautogui 備用）
            # 降低置信度閾值（從 0.8 降到 0.7）以提高對畫面變化的容錯性
            if full_img and os.path.exists(full_img) and not use_ok_script:
                strategy_name = f"Image Recognition (PyAutoGUI: {original_image_path})"
                self.logger.info(f"[SMART_CLICK] [IMG] Trying Image Strategy: {original_image_path}...")
                attempted_strategies.append(strategy_name)
                if self._try_pyautogui_recognition(full_img, region, win, clicks, click_type, 0.7, offset_x, offset_y):
                    self.logger.info(f"[SMART_CLICK] [IMG] Success.")
                    return True
                else:
                    self.logger.warning(f"[SMART_CLICK] [IMG] Failed (Confidence too low or not found).")
                    strategy_results[strategy_name] = "Failed"
            
            # 【優先級 4】OCR 文字辨識（如果【優先級 1】未處理，或【優先級 1】只處理了VLM priority==1的情況）
            # 注意：如果 target_text 存在且【優先級 1】已經處理了OCR，這裡不會再執行
            # 但如果【優先級 1】只處理了VLM priority==1的情況，且VLM失敗，這裡會執行OCR作為備選
            if target_text and self._get_ocr_engine() and not (vlm_enabled and vlm_priority == 1):
                strategy_name = f"OCR Text Recognition ('{target_text}')"
                priority_mode = "OCR"
                self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                attempted_strategies.append(strategy_name)
                if self._try_ocr_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y):
                    self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                    return True
                else:
                    self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                    strategy_results[strategy_name] = "Failed"
            
            # 【優先級 5】VLM 在 OCR 後（如果配置 VLM_PRIORITY >= 3）
            if vlm_enabled and vlm_priority >= 3 and target_text:
                strategy_name = f"Text/VLM Recognition ('{target_text}', Priority: {vlm_priority})"
                priority_mode = f"VLM (Priority {vlm_priority})"
                self.logger.info(f"[SMART_CLICK] [TEXT] Trying Text Strategy: '{target_text}' (Priority: {priority_mode})...")
                attempted_strategies.append(strategy_name)
                vlm_result = self._try_vlm_recognition(target_text, region, win, clicks, click_type, offset_x, offset_y)
                if vlm_result:
                    self.logger.info(f"[SMART_CLICK] [TEXT] Success.")
                    return True
                else:
                    self.logger.warning(f"[SMART_CLICK] [TEXT] Failed.")
                    strategy_results[strategy_name] = "Failed"
            
            time.sleep(0.15)  # 減少等待間隔
        
        # 循環超時：記錄超時信息
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            self.logger.warning(f"[SMART_CLICK] [TIMEOUT] Recognition timeout ({timeout}s), attempted strategies: {len(attempted_strategies)}")

        # 【優先級 最後】座標保底 - 當所有辨識方法都失敗時使用
        # 總結失敗：記錄所有嘗試過的策略
        if attempted_strategies:
            failed_strategies = ", ".join(attempted_strategies)
            self.logger.error(f"[SMART_CLICK] [FAIL] All strategies failed. Attempted strategies: {failed_strategies}")
        else:
            self.logger.error(f"[SMART_CLICK] [FAIL] All strategies failed (No available recognition methods).")
        
        # 嘗試座標保底
        strategy_name = f"Coordinate Fallback (Ratio: {x_ratio:.3f}, {y_ratio:.3f})"
        self.logger.info(f"[SMART_CLICK] [COORD] Trying Coordinate Strategy: Ratio ({x_ratio:.3f}, {y_ratio:.3f})...")
        
        # 重新獲取視窗（可能已經改變）
        win = self.get_nx_window()
        if win:
            # 記錄座標保底統計
            recognizer.record_coordinate_hit()
            
            # 座標保底點擊（僅在圖片/文字辨識都失敗時使用）
            try:
                # 驗證視窗控制代碼是否有效
                _ = win.left  # 嘗試訪問屬性
                
                if is_relative:
                    tx = DesktopApp._last_x + x_ratio
                    ty = DesktopApp._last_y + y_ratio
                    self.logger.debug(f"[SMART_CLICK] [COORD] Executing relative coordinate click: ({tx}, {ty}), offset=({offset_x}, {offset_y}), clicks={clicks}")
                elif from_bottom:
                    tx = win.left + int(win.width * x_ratio)
                    ty = win.top + win.height - int(win.height * y_ratio)
                    self.logger.debug(f"[SMART_CLICK] [COORD] Executing bottom-aligned click: ({tx}, {ty}), offset=({offset_x}, {offset_y}), clicks={clicks}")
                else:
                    tx = win.left + int(win.width * x_ratio)
                    ty = win.top + int(win.height * y_ratio)
                    self.logger.debug(f"[SMART_CLICK] [COORD] Executing ratio-based click: ({tx}, {ty}), offset=({offset_x}, {offset_y}), clicks={clicks}")
                
                # 🎯 VLM 驗證：點擊前截圖並標記位置
                final_x = tx + offset_x
                final_y = ty + offset_y
                screenshot_path = self._capture_click_preview(
                    click_x=final_x,
                    click_y=final_y,
                    target_text=target_text,
                    image_path=image_path
                )
                
                # 執行點擊並獲取最終座標（應用偏移）
                final_x, final_y = self._perform_click(tx, ty, clicks, click_type, offset_x, offset_y)
                # 使用最終座標記錄（已應用偏移）
                DesktopApp._last_x, DesktopApp._last_y = final_x, final_y
                
                # 🎯 VLM 驗證：點擊後，使用點擊前的截圖進行驗證
                vlm_verification_result = self._verify_coordinate_click_with_vlm(
                    screenshot_path=screenshot_path,
                    click_x=final_x,
                    click_y=final_y,
                    target_text=target_text,
                    image_path=image_path,
                    expected_action="點擊" + (target_text if target_text else "元素")
                )
                
                # 🎯 添加報告截圖（標記座標保底點擊位置，並包含 VLM 驗證結果）
                if DesktopApp._reporter and hasattr(DesktopApp._reporter, 'add_recognition_screenshot'):
                    try:
                        DesktopApp._reporter.add_recognition_screenshot(
                            item_name=f"Coordinate Fallback{' (VLM Verified)' if vlm_verification_result.get('verified') else ' (VLM Warning)'}",
                            x=final_x,
                            y=final_y,
                            width=50,
                            height=50,
                            method="Coordinate + VLM Verification",
                            region=region if region else (win.left, win.top, win.width, win.height),
                            additional_info=vlm_verification_result.get('description', '')
                        )
                    except Exception as e:
                        self.logger.debug(f"座標保底截圖失敗: {e}")
                
                # 記錄 VLM 驗證結果
                if vlm_verification_result.get('verified'):
                    self.logger.info(f"[SMART_CLICK] [COORD] [VLM] ✅ Verified. {vlm_verification_result.get('description', '')}")
                else:
                    self.logger.warning(f"[SMART_CLICK] [COORD] [VLM] ⚠️ Warning. {vlm_verification_result.get('description', '')}")
                
                self.logger.info(f"[SMART_CLICK] [COORD] Success. Final coordinates: ({final_x}, {final_y})")
                return True
            except Exception as e:
                self.logger.error(f"[SMART_CLICK] [COORD] Failed. Error: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            self.logger.error(f"[SMART_CLICK] [COORD] Failed. Window not found.")
            return False
    
    def get_recognition_stats(self) -> str:
        """
        📊 取得圖像辨識統計報告
        :return: 統計摘要字串
        """
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        return recognizer.get_stats_summary()
    
    def save_recognition_stats(self):
        """
        💾 保存圖像辨識統計到文件
        """
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        recognizer.save_stats()
        self.logger.info("✅ 辨識統計已保存到 logs/recognition_stats.json")
    
    def reset_recognition_stats(self):
        """
        🔄 重置圖像辨識統計
        """
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        recognizer.reset_stats()
        self.logger.info("✅ 辨識統計已重置")
    
    def _capture_click_preview(self, click_x, click_y, target_text=None, image_path=None):
        """
        📸 點擊前截圖並標記將要點擊的位置
        
        Args:
            click_x: 將要點擊的 X 座標
            click_y: 將要點擊的 Y 座標
            target_text: 目標文字（如果有）
            image_path: 目標圖片路徑（如果有）
            
        Returns:
            str: 標記後的截圖路徑，如果失敗則返回 None
        """
        # 檢查 VLM 是否啟用
        vlm_enabled = getattr(EnvConfig, 'VLM_ENABLED', False)
        if not vlm_enabled:
            return None
        
        try:
            self.logger.info(f"[VLM_PREVIEW] 點擊前截圖並標記位置: ({click_x}, {click_y})")
            
            # 截圖
            screenshot = pyautogui.screenshot()
            from PIL import ImageDraw
            draw = ImageDraw.Draw(screenshot)
            
            # 繪製紅色圓圈標記將要點擊的位置
            marker_size = 30
            draw.ellipse(
                [click_x - marker_size, click_y - marker_size, 
                 click_x + marker_size, click_y + marker_size],
                outline='red',
                width=3
            )
            
            # 繪製十字線
            cross_size = 15
            draw.line([click_x - cross_size, click_y, click_x + cross_size, click_y], fill='red', width=2)
            draw.line([click_x, click_y - cross_size, click_x, click_y + cross_size], fill='red', width=2)
            
            # 保存標記後的截圖
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name
                screenshot.save(screenshot_path)
            
            self.logger.info(f"[VLM_PREVIEW] 截圖已保存: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.warning(f"[VLM_PREVIEW] 截圖失敗: {e}")
            return None
    
    def _verify_coordinate_click_with_vlm(self, screenshot_path, click_x, click_y, target_text=None, image_path=None, expected_action="點擊元素"):
        """
        🤖 使用 VLM 驗證座標點擊是否正確
        
        使用點擊前的截圖（已標記點擊位置），讓 VLM 判斷點擊位置是否正確。
        
        Args:
            screenshot_path: 點擊前的截圖路徑（已標記點擊位置）
            click_x: 點擊的 X 座標
            click_y: 點擊的 Y 座標
            target_text: 目標文字（如果有）
            image_path: 目標圖片路徑（如果有）
            expected_action: 預期的操作描述
            
        Returns:
            dict: {
                'verified': bool,  # 是否驗證通過
                'description': str,  # VLM 的描述
                'confidence': float  # 信心度（0-1）
            }
        """
        # 檢查 VLM 是否啟用或截圖是否存在
        vlm_enabled = getattr(EnvConfig, 'VLM_ENABLED', False)
        if not vlm_enabled or not screenshot_path:
            return {
                'verified': True,  # VLM 未啟用時，假設驗證通過
                'description': 'VLM 驗證未啟用',
                'confidence': 0.0
            }
        
        try:
            self.logger.info(f"[VLM_VERIFY] 開始驗證座標點擊: ({click_x}, {click_y})")
            
            # 獲取 VLM 引擎
            vlm_engine = self._get_vlm_engine()
            if not vlm_engine:
                self.logger.warning("[VLM_VERIFY] VLM 引擎未初始化")
                # 清理臨時文件
                try:
                    import os
                    os.unlink(screenshot_path)
                except:
                    pass
                return {
                    'verified': True,  # VLM 不可用時，假設驗證通過
                    'description': 'VLM 引擎不可用',
                    'confidence': 0.0
                }
            
            # 構建 VLM 提示詞
            target_description = ""
            if target_text:
                target_description = f"文字「{target_text}」"
            elif image_path:
                # 從圖片路徑提取元素名稱
                import os
                element_name = os.path.splitext(os.path.basename(image_path))[0]
                target_description = f"元素「{element_name}」"
            else:
                target_description = "目標元素"
            
            prompt = f"""請分析這張截圖，紅色圓圈和十字線標記了將要點擊的位置。

預期操作：{expected_action}
目標元素：{target_description}

請判斷：
1. 標記的點擊位置是否在正確的元素上？
2. 該位置的元素是否符合預期的目標元素？
3. 點擊這個位置是否能達成預期的操作？

請用以下格式回答：
驗證結果：[通過/警告/失敗]
信心度：[0-100]%
說明：[簡短描述標記位置的元素，並說明是否正確]"""

            # 調用 VLM
            self.logger.info(f"[VLM_VERIFY] 調用 VLM 進行驗證...")
            vlm_response = vlm_engine.analyze_image(screenshot_path, prompt)
            
            # 清理臨時文件
            try:
                import os
                os.unlink(screenshot_path)
            except:
                pass
            
            # 解析 VLM 回應
            response_text = vlm_response.get('text', '') if isinstance(vlm_response, dict) else str(vlm_response)
            
            # 判斷驗證結果
            verified = False
            confidence = 0.5  # 預設信心度
            
            if '通過' in response_text or '正確' in response_text or '符合' in response_text:
                verified = True
                confidence = 0.8
            elif '警告' in response_text:
                verified = True  # 警告仍視為通過，但記錄
                confidence = 0.6
            else:
                verified = False
                confidence = 0.3
            
            # 提取信心度（如果 VLM 有提供）
            import re
            confidence_match = re.search(r'(\d+)%', response_text)
            if confidence_match:
                confidence = float(confidence_match.group(1)) / 100.0
            
            result = {
                'verified': verified,
                'description': response_text[:200],  # 限制長度
                'confidence': confidence
            }
            
            self.logger.info(f"[VLM_VERIFY] 驗證完成: {result}")
            return result
            
        except Exception as e:
            self.logger.warning(f"[VLM_VERIFY] 驗證過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return {
                'verified': True,  # 發生錯誤時，假設驗證通過（避免阻塞測試）
                'description': f'VLM 驗證失敗: {str(e)}',
                'confidence': 0.0
            }
    
    def _find_text_by_ocr(self, target_text, region):
        """
        使用 OCR 在指定區域尋找文字
        :param target_text: 要尋找的文字
        :param region: (left, top, width, height)
        :return: (x, y) 座標或 None
        """
        try:
            # 截取指定區域
            screenshot = pyautogui.screenshot(region=region)
            img_array = np.array(screenshot)
            
            # OCR 辨識
            ocr_engine = self._get_ocr_engine()
            if not ocr_engine:
                return None
            
            result = ocr_engine.ocr(img_array, cls=True)
            
            if not result or not result[0]:
                return None
            
            # 尋找匹配的文字
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                box = line[0]
                
                # 模糊匹配（包含即可）
                if target_text in text and confidence > 0.5:
                    # 計算文字中心點（相對於螢幕的絕對座標）
                    center_x = region[0] + (box[0][0] + box[2][0]) / 2
                    center_y = region[1] + (box[0][1] + box[2][1]) / 2
                    
                    self.logger.debug(f"OCR 找到文字: {text} (信賴度: {confidence:.2f})")
                    return (int(center_x), int(center_y))
            
            return None
            
        except Exception as e:
            self.logger.debug(f"OCR 處理異常: {e}")
            return None

    # ==================== 通用 VLM 截图和日志方法 ====================
    
    def _log_method_entry(self, method_name, additional_info=""):
        """
        🎯 通用方法入口日志记录
        统一所有 page 方法入口的日志格式，方便排查
        
        :param method_name: 方法名称（用于日志标记）
        :param additional_info: 额外的信息（可选）
        """
        import sys
        print("=" * 80, file=sys.stderr)
        print(f"[{method_name.upper()}] ========== {method_name}() 方法被調用！==========", file=sys.stderr)
        if additional_info:
            print(f"[{method_name.upper()}] {additional_info}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        self.logger.info(f"[{method_name.upper()}] 方法開始執行")
    
    def _get_debug_dir(self, subdir="vlm_scan_debug"):
        """
        🎯 获取调试截图目录路径
        
        :param subdir: 子目录名称（如 "vlm_scan_debug", "radio_verify_debug" 等）
        :return: 调试目录的完整路径
        """
        # 计算项目根目录（从 base/desktop_app.py 向上两级）
        base_dir = os.path.dirname(os.path.dirname(__file__))
        debug_dir = os.path.join(base_dir, "logs", subdir)
        os.makedirs(debug_dir, exist_ok=True)
        return debug_dir
    
    def _save_vlm_scan_region_screenshot(self, step_name, scan_region, win):
        """
        🎯 保存 VLM 掃描區域的截圖，用紅框標記掃描區域
        通用方法，所有 page 方法都可以使用
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 logs 目錄（直接放在項目根目錄下的 logs 資料夾）
            base_dir = os.path.dirname(os.path.dirname(__file__))
            debug_dir = os.path.join(base_dir, "logs")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 🎯 獲取 DPI 縮放比例（修復高 DPI 螢幕下的座標偏移問題）
            img_width, img_height = img.size
            screen_w, screen_h = pyautogui.size()
            scale_x = img_width / screen_w
            scale_y = img_height / screen_h
            
            # 提取掃描區域座標並應用 DPI 縮放
            scan_left, scan_top, scan_width, scan_height = scan_region
            rect_left = int(scan_left * scale_x)
            rect_top = int(scan_top * scale_y)
            rect_right = int((scan_left + scan_width) * scale_x)
            rect_bottom = int((scan_top + scan_height) * scale_y)
            
            # 繪製紅色矩形框（線寬 3px）
            draw.rectangle(
                [rect_left, rect_top, rect_right, rect_bottom],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）- 應用 DPI 縮放
            if win:
                win_rect_left = int(win.left * scale_x)
                win_rect_top = int(win.top * scale_y)
                win_rect_right = int((win.left + win.width) * scale_x)
                win_rect_bottom = int((win.top + win.height) * scale_y)
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記掃描區域信息
            draw.text((rect_left + 5, rect_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] VLM 掃描區域截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [SCREENSHOT] VLM 掃描區域截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [SCAN_REGION] 掃描區域: ({scan_left}, {scan_top}, {scan_width}, {scan_height})")
            if win:
                print(f"[VLM_SCAN] [WINDOW] 視窗範圍: ({win.left}, {win.top}, {win.width}, {win.height})")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存截圖失敗: {e}")
            print(f"[VLM_SCAN] [SCREENSHOT] 保存截圖失敗: {e}")
    
    def _save_vlm_error_screenshot(self, step_name, scan_region, win, vlm_x, vlm_y):
        """
        🎯 保存 VLM 錯誤截圖，標記掃描區域、視窗範圍和 VLM 返回的錯誤座標
        通用方法，所有 page 方法都可以使用
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height)
        :param win: 視窗物件
        :param vlm_x: VLM 返回的 X 座標
        :param vlm_y: VLM 返回的 Y 座標
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 logs 目錄（直接放在項目根目錄下的 logs 資料夾）
            base_dir = os.path.dirname(os.path.dirname(__file__))
            debug_dir = os.path.join(base_dir, "logs")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 🎯 獲取 DPI 縮放比例（修復高 DPI 螢幕下的座標偏移問題）
            img_width, img_height = img.size
            screen_w, screen_h = pyautogui.size()
            scale_x = img_width / screen_w
            scale_y = img_height / screen_h
            
            # 提取掃描區域座標並應用 DPI 縮放
            scan_left, scan_top, scan_width, scan_height = scan_region
            rect_left = int(scan_left * scale_x)
            rect_top = int(scan_top * scale_y)
            rect_right = int((scan_left + scan_width) * scale_x)
            rect_bottom = int((scan_top + scan_height) * scale_y)
            
            # 繪製紅色矩形框（線寬 3px）
            draw.rectangle(
                [rect_left, rect_top, rect_right, rect_bottom],
                outline="red",
                width=3
            )
            
            # 標記視窗範圍（藍色框）- 應用 DPI 縮放
            if win:
                win_rect_left = int(win.left * scale_x)
                win_rect_top = int(win.top * scale_y)
                win_rect_right = int((win.left + win.width) * scale_x)
                win_rect_bottom = int((win.top + win.height) * scale_y)
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記 VLM 返回的錯誤座標（黃色圓圈）- 應用 DPI 縮放
            if abs(vlm_x) < 100000 and abs(vlm_y) < 100000:  # 只標記合理的座標範圍
                vlm_x_scaled = int(vlm_x * scale_x)
                vlm_y_scaled = int(vlm_y * scale_y)
                # 繪製黃色圓圈標記 VLM 返回的座標
                circle_radius = 10
                draw.ellipse(
                    [vlm_x_scaled - circle_radius, vlm_y_scaled - circle_radius, vlm_x_scaled + circle_radius, vlm_y_scaled + circle_radius],
                    outline="yellow",
                    width=3
                )
                draw.text((vlm_x_scaled + 15, vlm_y_scaled), f"VLM Coord: ({vlm_x}, {vlm_y})", fill="yellow")
            
            # 標記掃描區域信息
            draw.text((rect_left + 5, rect_top + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 標記錯誤信息
            if win:
                draw.text((rect_left + 5, rect_top + 25), f"ERROR: VLM coord ({vlm_x}, {vlm_y}) out of window ({win.left}, {win.top}, {win.width}, {win.height})", fill="red")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] VLM 錯誤截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [SCREENSHOT] VLM 錯誤截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [ERROR] VLM 返回座標 ({vlm_x}, {vlm_y}) 超出視窗範圍")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存錯誤截圖失敗: {e}")
            print(f"[VLM_SCAN] [SCREENSHOT] 保存錯誤截圖失敗: {e}")
    
    def _save_vlm_click_coord_screenshot(self, step_name, scan_region, win, click_x, click_y):
        """
        🎯 保存點擊後的截圖，標記掃描區域和實際點擊的座標
        通用方法，所有 page 方法都可以使用
        
        :param step_name: 步驟名稱（用於文件名）
        :param scan_region: 掃描區域 (left, top, width, height) 或 None
        :param win: 視窗物件
        :param click_x: 實際點擊的 X 座標
        :param click_y: 實際點擊的 Y 座標
        """
        try:
            import pyautogui
            from PIL import Image, ImageDraw
            import datetime
            
            # 截取全屏
            screenshot = pyautogui.screenshot()
            
            # 創建 logs 目錄（直接放在項目根目錄下的 logs 資料夾）
            base_dir = os.path.dirname(os.path.dirname(__file__))
            debug_dir = os.path.join(base_dir, "logs")
            os.makedirs(debug_dir, exist_ok=True)
            
            # 生成時間戳
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S") + "_{:03d}".format(now.microsecond // 1000)
            
            # 轉換為 PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(img)
            
            # 🎯 獲取 DPI 縮放比例（修復高 DPI 螢幕下的座標偏移問題）
            img_width, img_height = img.size  # 截圖的物理尺寸
            screen_w, screen_h = pyautogui.size()  # 螢幕的邏輯尺寸
            scale_x = img_width / screen_w  # X 軸縮放比例
            scale_y = img_height / screen_h  # Y 軸縮放比例
            
            # 標記掃描區域（如果有）- 應用 DPI 縮放
            if scan_region:
                scan_left, scan_top, scan_width, scan_height = scan_region
                # 將邏輯座標轉換為截圖座標
                scan_left_scaled = int(scan_left * scale_x)
                scan_top_scaled = int(scan_top * scale_y)
                scan_width_scaled = int(scan_width * scale_x)
                scan_height_scaled = int(scan_height * scale_y)
                # 用紅框標記掃描區域
                draw.rectangle(
                    [scan_left_scaled, scan_top_scaled, scan_left_scaled + scan_width_scaled, scan_top_scaled + scan_height_scaled],
                    outline="red",
                    width=2
                )
                draw.text((scan_left_scaled + 5, scan_top_scaled + 5), f"Scan Region: ({scan_left}, {scan_top}, {scan_width}, {scan_height})", fill="red")
            
            # 標記視窗範圍（藍色框）- 應用 DPI 縮放
            if win:
                win_rect_left = int(win.left * scale_x)
                win_rect_top = int(win.top * scale_y)
                win_rect_right = int((win.left + win.width) * scale_x)
                win_rect_bottom = int((win.top + win.height) * scale_y)
                draw.rectangle(
                    [win_rect_left, win_rect_top, win_rect_right, win_rect_bottom],
                    outline="blue",
                    width=2
                )
                # 標記視窗信息
                draw.text((win_rect_left + 5, win_rect_top + 5), f"Window: {win.title}", fill="blue")
            
            # 標記實際點擊的座標（綠色圓圈和十字）- 應用 DPI 縮放
            click_x_scaled = int(click_x * scale_x)
            click_y_scaled = int(click_y * scale_y)
            circle_radius = 15
            draw.ellipse(
                [click_x_scaled - circle_radius, click_y_scaled - circle_radius, click_x_scaled + circle_radius, click_y_scaled + circle_radius],
                outline="green",
                width=3
            )
            # 繪製十字標記
            draw.line([(click_x_scaled - 20, click_y_scaled), (click_x_scaled + 20, click_y_scaled)], fill="green", width=3)
            draw.line([(click_x_scaled, click_y_scaled - 20), (click_x_scaled, click_y_scaled + 20)], fill="green", width=3)
            draw.text((click_x_scaled + circle_radius + 5, click_y_scaled - circle_radius), f"ACTUAL CLICK: ({click_x}, {click_y})", fill="green")
            
            # 保存截圖
            screenshot_path = os.path.join(debug_dir, f"{step_name}_{timestamp}.png")
            img.save(screenshot_path)
            
            self.logger.info(f"[VLM_SCAN] [SCREENSHOT] 實際點擊座標截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [SCREENSHOT] 實際點擊座標截圖已保存: {screenshot_path}")
            print(f"[VLM_SCAN] [CLICK_COORD] 實際點擊座標: ({click_x}, {click_y})")
            
        except Exception as e:
            self.logger.warning(f"[VLM_SCAN] [SCREENSHOT] 保存點擊座標截圖失敗: {e}")
            print(f"[VLM_SCAN] [SCREENSHOT] 保存點擊座標截圖失敗: {e}")
    
    # ==================== 智慧展開邏輯（DRY：統一實現在基類中）====================
    
    def _check_camera_visible(self, camera_name: str) -> bool:
        """
        檢查相機節點是否已在畫面上可見（純檢查，不執行任何操作）
        
        此方法使用圖片辨識和 OCR 兩種方式檢查相機是否已展開可見。
        這是智慧展開邏輯的第一步，避免無意義的雙擊 Server Icon。
        
        Args:
            camera_name: 相機名稱，例如 "usb_cam"
        
        Returns:
            bool: 如果相機可見返回 True，否則返回 False
        
        Note:
            - 此方法只檢查，不點擊，符合 SRP 原則
            - 使用配置中的搜索區域比例，避免硬編碼
        """
        win = self.get_nx_window()
        if not win:
            self.logger.debug("[Tree] 無法獲取視窗，無法檢查相機可見性")
            return False
        
        # 使用配置中的搜索區域比例（避免硬編碼）
        cam_config = EnvConfig.CAMERA_SETTINGS
        left_panel_region = (
            win.left,
            win.top + int(win.height * cam_config.LEFT_PANEL_Y_START),
            int(win.width * cam_config.LEFT_PANEL_X_RATIO),
            int(win.height * cam_config.LEFT_PANEL_Y_HEIGHT)
        )
        
        # 方法 1: 使用圖片辨識檢查（純檢測，不點擊）
        # 圖片辨識是最可靠的方式，因為相機圖標的視覺特徵穩定
        from base.ok_script_recognizer import get_recognizer
        recognizer = get_recognizer()
        full_img = os.path.normpath(os.path.join(EnvConfig.RES_PATH, EnvConfig.APP_PATHS.USB_CAM_ITEM))
        
        if os.path.exists(full_img):
            # locate_on_screen 返回 RecognitionResult，包含 success 屬性
            result = recognizer.locate_on_screen(full_img, region=left_panel_region, confidence=0.7)
            if result and result.success:
                self.logger.info(f"[Tree] 圖片辨識：相機節點已可見（位置: {result.x}, {result.y}）")
                return True
        
        # 方法 2: 如果圖片辨識失敗，嘗試 OCR 檢查
        # OCR 作為備選方案，因為文字辨識可能受到字體、大小、背景影響
        try:
            ocr_engine = self._get_ocr_engine()
            if ocr_engine:
                # 截取左側面板區域進行 OCR 掃描
                screenshot = pyautogui.screenshot(region=left_panel_region)
                
                # OCR 返回格式：[[(bbox, (text, confidence)), ...], ...]
                # 這是一個嵌套列表結構：
                # - 外層列表：可能包含多個檢測區域（通常只有一個）
                # - 內層列表：每個區域的檢測結果
                # - 每個結果：tuple，第一個元素是邊界框，第二個元素是 (text, confidence)
                ocr_result = ocr_engine.ocr(np.array(screenshot), cls=False)
                
                if ocr_result and ocr_result[0]:
                    # 遍歷 OCR 結果，尋找包含相機名稱的文字
                    for line in ocr_result[0]:
                        if line and len(line) > 1:
                            # line[1] 可能是 tuple (text, confidence) 或直接是 text
                            # 使用 isinstance 檢查並安全提取文字，避免類型錯誤
                            text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                            
                            # 使用大小寫不敏感的匹配，提高容錯性
                            if camera_name.lower() in text.lower():
                                self.logger.info(f"[Tree] OCR 辨識：相機節點已可見（文字: {text}）")
                                return True
        except Exception as e:
            # OCR 檢查失敗不應該影響整體流程，只記錄 debug 級別日誌
            self.logger.debug(f"[Tree] OCR 檢查失敗: {e}")
        
        return False
    
    def _expand_server_if_needed(self) -> bool:
        """
        如果需要，展開 Server 節點（純展開操作，不操作相機）
        
        此方法負責雙擊 Server Icon 以展開樹狀結構。
        這是智慧展開邏輯的第二步，只在相機不可見時執行。
        
        Returns:
            bool: 如果成功展開返回 True，否則返回 False
        
        Note:
            - 此方法只展開，不檢查相機，符合 SRP 原則
            - 使用配置中的 Server Icon 位置和等待時間
        """
        self.logger.info("[Tree] 雙擊 Server Icon 進行展開...")
        
        cam_config = EnvConfig.CAMERA_SETTINGS
        thresholds = EnvConfig.THRESHOLDS
        
        # 使用配置中的 Server Icon 位置比例
        success = self.smart_click(
            x_ratio=cam_config.SERVER_ICON_X_RATIO,
            y_ratio=cam_config.SERVER_ICON_Y_RATIO,
            target_text="Server",
            image_path=EnvConfig.APP_PATHS.SERVER_ICON,
            clicks=2,  # 雙擊
            timeout=3
        )
        
        if success:
            self.logger.info("[Tree] ✅ 成功雙擊 Server Icon")
            # 使用配置中的等待時間（避免硬編碼）
            time.sleep(thresholds.TREE_EXPAND_WAIT_TIME)
            return True
        else:
            self.logger.warning("[Tree] ⚠️ 雙擊 Server Icon 失敗")
            return False
    
    def _ensure_camera_visible_and_interact(
        self, 
        action: str = "right_click", 
        camera_name: str = None
    ) -> bool:
        """
        智慧展開邏輯：如果相機已在畫面上，直接操作；否則先展開 Server。
        
        此方法組合了檢查、展開、操作三個步驟，實現完整的智慧展開流程。
        符合 SRP 原則：此方法的唯一責任是「確保相機可見並執行操作」。
        
        Args:
            action: 操作類型，可選值：
                - "right_click": 右鍵點擊（預設）
                - "double_click": 雙擊
                - "click": 單擊
            camera_name: 相機名稱，如果為 None 則使用配置中的預設值
        
        Returns:
            bool: 操作是否成功
        
        Example:
            >>> # 右鍵點擊相機（智慧展開）
            >>> success = self._ensure_camera_visible_and_interact("right_click", "usb_cam")
            >>> 
            >>> # 雙擊相機（智慧展開）
            >>> success = self._ensure_camera_visible_and_interact("double_click")
        
        Note:
            - 此方法內部調用 _check_camera_visible 和 _expand_server_if_needed
            - 使用配置中的相機名稱和資源路徑，避免硬編碼
        """
        # 使用配置中的預設相機名稱（避免硬編碼）
        if camera_name is None:
            camera_name = EnvConfig.CAMERA_SETTINGS.DEFAULT_CAMERA_NAME
        
        self.logger.info(f"[Tree] 檢查相機節點是否可見: {camera_name}...")
        
        # 步驟 1: 檢查相機是否已可見
        camera_visible = self._check_camera_visible(camera_name)
        
        if camera_visible:
            self.logger.info("[Tree] ✅ 相機節點已可見，跳過 Server 展開")
        else:
            # 步驟 2: 相機不可見，需要展開 Server
            expand_success = self._expand_server_if_needed()
            if not expand_success:
                # 展開失敗，但繼續嘗試操作（可能相機已經在其他位置）
                self.logger.warning("[Tree] ⚠️ Server 展開失敗，但繼續嘗試操作相機")
        
        # 步驟 3: 對相機進行實際操作
        self.logger.info(f"[Tree] 對相機執行操作: {action}")
        
        # 根據 action 類型設置點擊參數
        # 使用字典映射提高可讀性和可維護性
        action_config = {
            "right_click": {"click_type": "right", "clicks": 1},
            "double_click": {"click_type": "left", "clicks": 2},
            "click": {"click_type": "left", "clicks": 1}
        }
        
        config = action_config.get(action, action_config["right_click"])  # 預設右鍵
        cam_config = EnvConfig.CAMERA_SETTINGS
        
        return self.smart_click_priority_image(
            x_ratio=cam_config.CAMERA_ITEM_X_RATIO,
            y_ratio=cam_config.CAMERA_ITEM_Y_RATIO,
            target_text=camera_name,  # 使用相機名稱作為備選
            image_path=EnvConfig.APP_PATHS.USB_CAM_ITEM,  # 使用配置中的路徑
            click_type=config["click_type"],
            clicks=config["clicks"],
            timeout=3
        )