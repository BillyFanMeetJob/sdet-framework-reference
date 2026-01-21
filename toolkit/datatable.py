from toolkit.logger import get_logger

class DataTable:
    def __init__(self):
        self._data = {}
        self.logger = get_logger("DataTable")

    def set(self, key: str, value):
        self.logger.info(f"DataTable 存入數據: {key} = {value}")
        self._data[key] = value

    def get(self, key: str, default=None):
        value = self._data.get(key, default)
        self.logger.info(f"DataTable 讀取數據: {key} = {value}")
        return value

    def clear(self):
        self._data.clear()

# 全域單例
shared_dt = DataTable()