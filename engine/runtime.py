import sys
import os

# 確保能找到根目錄與各資料夾
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import EnvConfig
from toolkit.datatable import shared_dt

def get_config():
    """ 統一獲取 EnvConfig 實例 """
    return EnvConfig

def get_datatable():
    """ 獲取位於 toolkit 的共享數據容器 """
    return shared_dt

def set_ctx(ctx):
    pass