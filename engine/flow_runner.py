# engine/flow_runner.py
from base.browser import Browser
from engine.runtime import set_ctx
from engine.run_context import RunContext
from engine.testplan_loader import load_test_plan
from engine.step_translator import StepTranslator
from toolkit.logger import get_logger
from toolkit.funlib import normalize
from toolkit.types import Step
from toolkit.datatable import DataTable
import config

logger = get_logger(__name__)

def execute_step(step: Step, translator: StepTranslator) -> None:
    flow_name = normalize(step.get("FlowName"))
    if not flow_name:
        raise ValueError("TestPlan異常,FlowName不可為空")
    params = step.get("Params") or {}
    step_no = step.get("StepNo")
    test_name = step.get("TestName")
    logger.info(f"TestName: {test_name}; StepNo: {step_no}; FlowName: {flow_name};")
    logger.info(f"Params: {params}")
    logger.info("Start execution")

    func = translator.get_action(flow_name)

    try:
        func(**params)
    except Exception:
        logger.exception("Step execution failed")
        raise

def run_test_flow(test_name: str, browser: Browser) -> None:
    # 建立執行期 Context（dt/config）
    ctx = RunContext(dt=DataTable(), config=config.ACTIVE_CONFIG)
    set_ctx(ctx)

    steps = load_test_plan(test_name)
    translator = StepTranslator(browser)

    for step in steps:
        execute_step(step, translator)
