# 相對路徑: toolkit/logger.py

import logging
import sys
import os

def _safe_encode_message(message):
    """
    安全編碼日誌消息，自動清理 emoji 避免 cp950 編碼錯誤
    """
    if not isinstance(message, str):
        return message
    
    # 替換常見 emoji 為 ASCII 等效字符
    # 按使用頻率排序，確保所有 emoji 都被清理
    safe_message = message.replace("🟢", "[START]").replace("📸", "[IMG]").replace("🤖", "[VLM]").replace("📝", "[OCR]").replace("📍", "[LOC]").replace("✅", "[OK]").replace("⚠️", "[WARN]").replace("❌", "[ERROR]").replace("⏱️", "[TIMEOUT]").replace("💾", "[SAVE]").replace("⚙️", "[CFG]").replace("🖱️", "[CLICK]").replace("⌨️", "[KEY]").replace("🎬", "[CASE]").replace("🔄", "[SWITCH]").replace("🔍", "[DEBUG]").replace("🎯", "[OK]").replace("📊", "[STAT]").replace("⏳", "[WAIT]").replace("🚀", "[START]").replace("💡", "[TIP]")
    return safe_message


class SafeFormatter(logging.Formatter):
    """安全的 Formatter，自動清理 emoji"""
    def format(self, record):
        # 清理消息中的 emoji
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = _safe_encode_message(record.msg)
        # 清理參數中的 emoji
        if hasattr(record, 'args') and record.args:
            record.args = tuple(_safe_encode_message(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return super().format(record)


class FlushingStreamHandler(logging.StreamHandler):
    """
    自動刷新的 StreamHandler
    確保每條日誌都立即寫入文件（對 subprocess 重定向很重要）
    """
    def emit(self, record):
        super().emit(record)
        self.flush()  # 🎯 關鍵：每次輸出後立即刷新


def get_logger(name):
    # 封鎖所有第三方庫日誌與環境警告
    for lib in ["ppocr", "paddle", "cv2", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.CRITICAL)
    
    # 嘗試屏蔽 OpenCV 的 C 語言層級警告
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 🎯 檢查是否有環境變數指定日誌文件（test_case_launcher 會設置）
        log_file = os.environ.get('TEST_TERMINAL_LOG')
        
        if log_file:
            # 如果有指定日誌文件，直接寫入文件
            try:
                file_handler = FlushingStreamHandler(
                    open(log_file, 'a', encoding='utf-8', errors='ignore', buffering=1)
                )
                file_handler.setFormatter(SafeFormatter('>>> %(message)s'))
                file_handler.setLevel(logging.INFO)
                logger.addHandler(file_handler)
            except Exception as e:
                # 如果文件打開失敗，回退到 stdout
                print(f"[LOGGER] 無法打開日誌文件 {log_file}: {e}")
                console = FlushingStreamHandler(sys.stdout)
                console.setFormatter(SafeFormatter('>>> %(message)s'))
                console.setLevel(logging.INFO)
                logger.addHandler(console)
        else:
            # 沒有指定日誌文件，使用 stdout
            console = FlushingStreamHandler(sys.stdout)
            console.setFormatter(SafeFormatter('>>> %(message)s'))
            console.setLevel(logging.INFO)
            logger.addHandler(console)
        
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger