# engine/run_context.py
from __future__ import annotations
from dataclasses import dataclass

from toolkit.datatable import DataTable
from config import EnvConfig


@dataclass(frozen=True)
class RunContext:
    dt: DataTable
    config: EnvConfig
