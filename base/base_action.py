# base/base_action.py 
from __future__ import annotations
from toolkit.logger import get_logger
import config

class BaseAction:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = config.ACTIVE_CONFIG
