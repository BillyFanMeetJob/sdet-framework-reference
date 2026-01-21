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
    safe_message = message.replace("🔍", "[DEBUG]").replace("🤖", "[VLM]").replace("📝", "[OCR]").replace("🎯", "[OK]").replace("📸", "[IMG]").replace("📊", "[STAT]").replace("❌", "[ERROR]").replace("✅", "[OK]").replace("⚠️", "[WARN]").replace("⏳", "[WAIT]").replace("🚀", "[START]").replace("💡", "[TIP]").replace("🖱️", "[CLICK]").replace("⌨️", "[KEY]").replace("🎬", "[CASE]").replace("🔄", "[SWITCH]")
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


def get_logger(name):
    # 封鎖所有第三方庫日誌與環境警告
    for lib in ["ppocr", "paddle", "cv2", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.CRITICAL)
    
    # 嘗試屏蔽 OpenCV 的 C 語言層級警告
    os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        # 使用安全的 Formatter 自動清理 emoji
        console.setFormatter(SafeFormatter('>>> %(message)s'))
        console.setLevel(logging.INFO)
        logger.addHandler(console)
        logger.setLevel(logging.INFO)
    return logger