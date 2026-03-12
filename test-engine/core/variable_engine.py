"""
Variable Engine - handles variable resolution, extraction and built-in functions.

Variable priority (highest to lowest):
  1. Extracted from responses during test execution
  2. Environment variables
  3. Project variables
  4. Global variables
"""

import re
import time
import uuid
import random
import string
from typing import Any, Dict, List, Optional
from .logger import logger

# Pattern for ${variable} or ${__function(args)}
VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
FUNC_PATTERN = re.compile(r'^__(\w+)\((.*)\)$')


class VariableEngine:
    def __init__(self):
        self._variables: Dict[str, Any] = {}

    def load_variables(
        self,
        global_vars: Dict[str, Any] = None,
        project_vars: Dict[str, Any] = None,
        env_vars: Dict[str, Any] = None,
    ):
        """Load variables with priority: env > project > global."""
        if global_vars:
            self._variables.update(global_vars)
        if project_vars:
            self._variables.update(project_vars)
        if env_vars:
            self._variables.update(env_vars)
        logger.info(f"VariableEngine loaded {len(self._variables)} variables")

    def set(self, key: str, value: Any):
        """Set a single variable."""
        self._variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single variable."""
        return self._variables.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all variables."""
        return dict(self._variables)

    def resolve(self, value: Any) -> Any:
        """
        Recursively resolve ${var} references in a value.
        - If the entire value is "${var}", return the original type (int, dict, etc.)
        - If "${var}" is embedded in a string, substitute as string.
        - Supports nested dicts/lists.
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value

    def _resolve_string(self, text: str) -> Any:
        """Resolve a single string value."""
        # If the entire string is a single ${var}, return raw type
        match = VAR_PATTERN.fullmatch(text.strip())
        if match:
            key = match.group(1)
            result = self._evaluate(key)
            if result is not None:
                return result
            # Variable not found, return original
            return text

        # Otherwise, do string substitution for all ${var} occurrences
        def replacer(m):
            key = m.group(1)
            result = self._evaluate(key)
            if result is not None:
                return str(result)
            return m.group(0)  # Keep original if not found

        return VAR_PATTERN.sub(replacer, text)

    def _evaluate(self, key: str) -> Any:
        """Evaluate a variable key or built-in function."""
        # Check built-in functions
        func_match = FUNC_PATTERN.match(key)
        if func_match:
            func_name = func_match.group(1)
            func_args = func_match.group(2).strip()
            return self._call_builtin(func_name, func_args)

        # Simple variable lookup
        return self._variables.get(key)

    def _call_builtin(self, func_name: str, args_str: str) -> Any:
        """Execute a built-in function."""
        if func_name == "timestamp":
            return int(time.time())
        elif func_name == "uuid":
            return str(uuid.uuid4())
        elif func_name == "random_int":
            parts = [a.strip() for a in args_str.split(",")]
            low = int(parts[0]) if len(parts) > 0 and parts[0] else 1
            high = int(parts[1]) if len(parts) > 1 and parts[1] else 100
            return random.randint(low, high)
        elif func_name == "random_string":
            length = int(args_str) if args_str else 8
            return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        else:
            logger.warning(f"Unknown built-in function: __{func_name}")
            return None

    def extract(self, response, extractions: List[Dict[str, str]]):
        """
        Extract variables from HTTP response.

        extractions format:
          - token: body.data.token
          - user_id: body.data.id
          - status: status_code
          - header_val: headers.X-Request-Id
        """
        if not extractions:
            return

        for extraction in extractions:
            for var_name, path in extraction.items():
                value = self._extract_value(response, path)
                if value is not None:
                    self._variables[var_name] = value
                    logger.info(f"Extracted variable: {var_name} = {value}")
                else:
                    logger.warning(f"Failed to extract variable: {var_name} from path: {path}")

    def _extract_value(self, response, path: str) -> Any:
        """Extract a value from response using a dot-path."""
        if path == "status_code":
            return response.status_code

        if path.startswith("headers."):
            header_name = path[len("headers."):]
            return response.headers.get(header_name)

        if path == "body":
            try:
                return response.json()
            except ValueError:
                return response.text

        if path.startswith("body."):
            try:
                data = response.json()
                keys = path.split(".")[1:]
                for key in keys:
                    if isinstance(data, dict):
                        data = data[key]
                    elif isinstance(data, list) and key.isdigit():
                        data = data[int(key)]
                    else:
                        return None
                return data
            except (ValueError, KeyError, TypeError, IndexError):
                return None

        return None
