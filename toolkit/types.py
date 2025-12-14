# toolkit/types.py
from typing import Tuple, List, Dict, Any, Callable
from selenium.webdriver.common.by import By

Locator = Tuple[By, str]

Step = Dict[str, Any]
StepList = List[Step]

# Action function 型別：某個可被呼叫的流程函式
ActionFunc = Callable[..., Any]
# Action 對照表：action_name → Action function
ActionMap = Dict[str, ActionFunc]
