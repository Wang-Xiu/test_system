"""
Debug runner - executes a single test case synchronously and returns structured results.
Used by the /api/debug/run endpoint for online debugging.
"""

import time
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from core.yaml_parser import YamlParser, ApiTestCaseModel
from core.http_client import HttpClient, http_client
from core.variable_engine import VariableEngine
from core.validator import Validator
from core.logger import logger


def run_single_case(
    yaml_content: str,
    env_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a single test case from YAML content and return structured results.
    Does NOT go through Celery - runs synchronously.
    """
    result = {
        "status": "pass",
        "request": {},
        "response": {},
        "validations": [],
        "extracted_vars": {},
        "error": None,
    }

    try:
        # Parse YAML
        import yaml
        import tempfile
        import os

        # Write to temp file for parser
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            cases = YamlParser.parse(temp_path)
        finally:
            os.unlink(temp_path)

        if not cases:
            result["status"] = "error"
            result["error"] = "No test cases found in YAML"
            return result

        case = cases[0]  # Debug only runs the first case

        # Setup variable engine
        ve = VariableEngine()
        if env_config:
            ve.load_variables(global_vars=env_config.get("variables", {}))

        # Setup HTTP client
        if env_config:
            client = HttpClient(base_url=env_config.get("base_url", ""))
            headers = env_config.get("headers", {})
            if headers:
                client.session.headers.update(headers)
        else:
            client = http_client

        # Resolve variables
        resolved_url = ve.resolve(case.request.url)
        resolved_headers = ve.resolve(case.request.headers) if case.request.headers else {}
        resolved_params = ve.resolve(case.request.params) if case.request.params else {}
        resolved_json = ve.resolve(case.request.json_data) if case.request.json_data else {}
        resolved_data = ve.resolve(case.request.data) if case.request.data else {}

        # Build request kwargs
        req_kwargs = {}
        if resolved_headers:
            req_kwargs["headers"] = resolved_headers
        if resolved_params:
            req_kwargs["params"] = resolved_params
        if resolved_json:
            req_kwargs["json"] = resolved_json
        if resolved_data:
            req_kwargs["data"] = resolved_data

        result["request"] = {
            "method": case.request.method.upper(),
            "url": resolved_url,
            "headers": resolved_headers,
            "params": resolved_params,
            "body": resolved_json or resolved_data or None,
        }

        # Send request
        start = time.time()
        response = client.request(method=case.request.method, url=resolved_url, **req_kwargs)
        elapsed_ms = round((time.time() - start) * 1000, 2)

        # Build response info
        try:
            resp_body = response.json()
        except ValueError:
            resp_body = response.text

        result["response"] = {
            "status_code": response.status_code,
            "body": resp_body,
            "headers": dict(response.headers),
            "elapsed_ms": elapsed_ms,
        }

        # Extract variables
        if case.extractions:
            ve.extract(response, case.extractions)
            result["extracted_vars"] = {
                k: v for ext in case.extractions for k in ext
                if (v := ve.get(k)) is not None
            }

        # Validate
        if case.validations:
            resolved_validations = ve.resolve(case.validations)
            for validation in resolved_validations:
                for operator, expected in validation.items():
                    for field, expected_value in expected.items():
                        actual_value = Validator._get_actual_value(response, field)
                        try:
                            if operator == "eq":
                                assert actual_value == expected_value
                            elif operator == "contains":
                                if isinstance(actual_value, str):
                                    assert str(expected_value) in actual_value
                                else:
                                    assert str(expected_value) in json.dumps(actual_value, ensure_ascii=False)
                            elif operator == "in":
                                assert actual_value in expected_value
                            result["validations"].append({
                                "rule": f"{operator} {field} {expected_value}",
                                "result": "pass",
                            })
                        except AssertionError:
                            result["validations"].append({
                                "rule": f"{operator} {field} {expected_value}",
                                "result": "fail",
                                "actual": str(actual_value),
                            })
                            result["status"] = "fail"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Debug run error: {e}")

    return result
