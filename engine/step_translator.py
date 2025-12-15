# engine/step_translator.py
from __future__ import annotations
from typing import Callable
from toolkit.types import ActionFunc
from base.browser import Browser
from actions.login_actions import LoginActions
from actions.inventory_actions import InventoryActions
from toolkit.types import ActionMap
from toolkit.funlib import normalize
from engine.runtime import get_datatable, get_config

class StepTranslator:
    def __init__(self, browser: Browser):
        self.actions = {
            "login": LoginActions(browser),
            "inventory": InventoryActions(browser),
        }
        C = get_config()
        self._mapping: ActionMap = self._build_action_map_from_excel(C.TESTPLANPATH)

    def _build_action_map_from_excel(self, filepath: str) -> ActionMap:
        dt = get_datatable()

        if not dt.has_sheet("Translate"):
            dt.add_sheet_from_excel("Translate", filepath, "Translate")

        sheet = dt.get_sheet("Translate")

        mapping: ActionMap = {}
        for row in sheet.rows:
            flow_name = normalize(row.get("FlowName"))
            action_key = normalize(row.get("ActionKey"))
            method_name = normalize(row.get("ActionMethod"))

            if not flow_name:
                continue

            if action_key not in self.actions:
                raise ValueError(f"Translate sheet 錯誤：ActionKey='{action_key}' 不存在於 StepTranslator.actions")

            obj = self.actions[action_key]
            if not hasattr(obj, method_name):
                raise ValueError(f"Translate sheet 錯誤：{action_key} 物件不存在方法 '{method_name}'")

            method: Callable = getattr(obj, method_name)
            mapping[flow_name] = method

        return mapping

    def get_action(self, flow_name: str)->ActionFunc:
        flow_name = normalize(flow_name)
        if flow_name not in self._mapping:
            raise ValueError(f"未知的流程名稱：{flow_name}")
        return self._mapping[flow_name]
