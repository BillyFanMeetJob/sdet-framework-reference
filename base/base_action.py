# base/base_action.py 
from __future__ import annotations
from toolkit.logger import get_logger
from engine.runtime import get_config
class BaseAction:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()

