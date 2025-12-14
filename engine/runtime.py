# engine/runtime.py
from __future__ import annotations
from contextvars import ContextVar
from typing import Optional
from toolkit.datatable import DataTable
from engine.run_context import RunContext
from config import EnvConfig
_ctx_var: ContextVar[Optional[RunContext]] = ContextVar("run_ctx", default=None)

def set_ctx(ctx: RunContext) -> None:
    _ctx_var.set(ctx)

def get_ctx() -> RunContext:
    ctx = _ctx_var.get()
    if ctx is None:
        raise RuntimeError("RunContext 尚未初始化：請先呼叫 set_ctx(ctx)")
    return ctx

def get_datatable() -> DataTable:
    return get_ctx().dt

def get_config()->EnvConfig:
    return get_ctx().config
