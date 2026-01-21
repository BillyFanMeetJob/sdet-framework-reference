# engine/testplan_loader.py
from __future__ import annotations
from toolkit.types import Step, StepList
from toolkit.funlib import normalize
from engine.runtime import get_datatable, get_config
from typing import Any

def _infer_type(value: str) -> Any:
    v = normalize(value)
    if v == "":
        return ""

    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("none", "null"):
        return None

    # int
    if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
        try:
            return int(v)
        except ValueError:
            pass

    # float
    try:
        if "." in v:
            return float(v)
    except ValueError:
        pass

    return v

def parse_params(param_str: str | None) -> dict[str, Any]:
    param_str = normalize(param_str)
    if not param_str:
        return {}

    result: dict[str, Any] = {}
    for part in param_str.split(";"):
        part = normalize(part)
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[normalize(key)] = _infer_type(value)
    return result

def load_testplan_dir(test_name: str) -> str:
    C = get_config()
    dt = get_datatable()

    # TestDir 只需要載一次即可
    if not dt.has_sheet("TestDir"):
        dt.add_sheet_from_excel("TestDir", C.TEST_PLAN_PATH, "TestDir")

    sheet = dt.get_sheet("TestDir")

    for row in sheet.rows:
        if normalize(row.get("TestName")) != test_name:
            continue

        fc = normalize(row.get("FunctionalClassification"))
        if not fc:
            raise ValueError(f"TestDir FunctionalClassification 為空，TestName='{test_name}'")
        return fc

    raise ValueError(f"TestDir 找不到 TestName='{test_name}'")

def load_test_plan(test_name: str) -> StepList:
    C = get_config()
    dt = get_datatable()

    sheet_name = load_testplan_dir(test_name)

    # 關鍵：FunctionalClassification 不同就不能共用同一個 alias
    alias = f"TestPlan:{sheet_name}"
    if not dt.has_sheet(alias):
        dt.add_sheet_from_excel(alias, C.TEST_PLAN_PATH, sheet_name)

    sheet = dt.get_sheet(alias)

    steps: StepList = []
    for row in sheet.rows:
        if normalize(row.get("TestName")) != test_name:
            continue

        flow_name = normalize(row.get("FlowName"))
        if not flow_name:
            continue

        step: Step = {
            "TestName": test_name,
            "StepNo": int(row.get("StepNo") or 0),
            "FlowName": flow_name,
            "Params": parse_params(row.get("Params")),
        }
        steps.append(step)

    steps.sort(key=lambda s: s["StepNo"])
    return steps
