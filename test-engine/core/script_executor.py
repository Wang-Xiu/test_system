"""
Script executor for setup/teardown actions in test cases.
Supports: set_variable, sleep, log, python (sandboxed).
"""

import time
from typing import List
from core.yaml_parser import ScriptAction
from core.variable_engine import VariableEngine
from core.logger import logger


class ScriptExecutor:
    """Execute setup/teardown script actions."""

    def __init__(self, variable_engine: VariableEngine):
        self.ve = variable_engine

    def execute(self, actions: List[ScriptAction], label: str = "script"):
        """Execute a list of script actions."""
        for action in actions:
            try:
                self._execute_one(action, label)
            except Exception as e:
                logger.error(f"[{label}] Action {action.type} failed: {e}")
                raise

    def _execute_one(self, action: ScriptAction, label: str):
        if action.type == "set_variable":
            value = self.ve.resolve(action.value or "")
            self.ve.set(action.key, value)
            logger.info(f"[{label}] set_variable: {action.key} = {value}")

        elif action.type == "sleep":
            seconds = action.seconds or 1
            logger.info(f"[{label}] sleep: {seconds}s")
            time.sleep(seconds)

        elif action.type == "log":
            msg = self.ve.resolve(action.message or "")
            logger.info(f"[{label}] log: {msg}")

        elif action.type == "python":
            self._run_python(action.code or "", label)

        else:
            logger.warning(f"[{label}] Unknown action type: {action.type}")

    def _run_python(self, code: str, label: str):
        """Execute Python code in a restricted sandbox."""
        # Provide limited builtins for safety
        safe_builtins = {
            "len": len, "str": str, "int": int, "float": float,
            "list": list, "dict": dict, "bool": bool,
            "range": range, "enumerate": enumerate,
            "print": lambda *args: logger.info(f"[{label}] print: {' '.join(str(a) for a in args)}"),
        }

        sandbox_globals = {
            "__builtins__": safe_builtins,
            "variables": self.ve.get_all(),
            "set_var": self.ve.set,
            "get_var": self.ve.get,
        }

        try:
            exec(code, sandbox_globals)
        except Exception as e:
            logger.error(f"[{label}] Python script error: {e}")
            raise
