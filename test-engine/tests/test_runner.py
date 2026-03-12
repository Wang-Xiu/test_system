import json
import time
import pytest
import allure
from pathlib import Path
from core.yaml_parser import YamlParser, ApiTestCaseModel
from core.http_client import HttpClient, http_client
from core.validator import Validator
from core.logger import logger
from core.variable_engine import VariableEngine


def get_yaml_test_cases(config):
    """
    Find all YAML files in the data directory and parse them into test cases.
    Reads data dir from pytest command line option --test-data-dir.
    """
    data_dir_option = config.getoption("--test-data-dir", default=None)
    if data_dir_option:
        data_dir = Path(data_dir_option)
    else:
        data_dir = Path(__file__).parent.parent / "data"

    test_cases = []

    if not data_dir.exists():
        return test_cases

    for yaml_file in sorted(data_dir.rglob("*.yaml")):
        try:
            cases = YamlParser.parse(str(yaml_file))
            for case in cases:
                test_cases.append((case, str(yaml_file)))
        except Exception as e:
            logger.error(f"Failed to parse {yaml_file}: {e}")

    return test_cases


def pytest_generate_tests(metafunc):
    """Dynamically parametrize test_api_from_yaml with YAML test cases."""
    if "test_case_data" in metafunc.fixturenames:
        cases = get_yaml_test_cases(metafunc.config)
        ids = []
        for case, file_path in cases:
            file_name = Path(file_path).name
            ids.append(f"{file_name}-{case.name}")
        metafunc.parametrize("test_case_data", cases, ids=ids)


def _get_http_client(config) -> HttpClient:
    """Get or create an HTTP client configured from env-config."""
    env_config_path = config.getoption("--env-config", default=None)
    if env_config_path and Path(env_config_path).exists():
        return HttpClient.from_config(env_config_path)
    return http_client


def _execute_scripts(actions, variable_engine, label: str):
    """Execute setup/teardown script actions."""
    if not actions:
        return
    for action in actions:
        action_type = action.type
        if action_type == "set_variable":
            resolved_value = variable_engine.resolve(action.value or "")
            variable_engine.set(action.key, resolved_value)
            logger.info(f"[{label}] set_variable: {action.key} = {resolved_value}")
        elif action_type == "sleep":
            seconds = action.seconds or 1
            logger.info(f"[{label}] sleep: {seconds}s")
            time.sleep(seconds)
        elif action_type == "log":
            msg = variable_engine.resolve(action.message or "")
            logger.info(f"[{label}] log: {msg}")
        elif action_type == "python":
            # Restricted sandbox execution
            code = action.code or ""
            sandbox_globals = {
                "variables": variable_engine.get_all(),
                "set_var": variable_engine.set,
            }
            try:
                exec(code, {"__builtins__": {}}, sandbox_globals)
            except Exception as e:
                logger.error(f"[{label}] python script error: {e}")
        else:
            logger.warning(f"[{label}] Unknown script type: {action_type}")


def test_api_from_yaml(test_case_data, request, variable_engine):
    case, file_path = test_case_data
    client = _get_http_client(request.config)

    allure.dynamic.title(case.name)
    allure.dynamic.description(f"Source file: {file_path}")

    # 0. Execute setup scripts
    if case.setup:
        with allure.step("Setup"):
            _execute_scripts(case.setup, variable_engine, "setup")

    # 1. Resolve variables in request
    resolved_url = variable_engine.resolve(case.request.url)
    resolved_headers = variable_engine.resolve(case.request.headers) if case.request.headers else {}
    resolved_params = variable_engine.resolve(case.request.params) if case.request.params else {}
    resolved_json = variable_engine.resolve(case.request.json_data) if case.request.json_data else {}
    resolved_data = variable_engine.resolve(case.request.data) if case.request.data else {}

    # 2. Send Request
    with allure.step(f"Request: {case.request.method.upper()} {resolved_url}"):
        req_kwargs = {}
        if resolved_headers:
            req_kwargs["headers"] = resolved_headers
        if resolved_params:
            req_kwargs["params"] = resolved_params
        if resolved_json:
            req_kwargs["json"] = resolved_json
        if resolved_data:
            req_kwargs["data"] = resolved_data

        allure.attach(
            json.dumps(req_kwargs, ensure_ascii=False, default=str),
            name="Request Parameters",
            attachment_type=allure.attachment_type.JSON
        )

        response = client.request(
            method=case.request.method,
            url=resolved_url,
            **req_kwargs
        )

        allure.attach(
            str(response.status_code),
            name="Response Status Code",
            attachment_type=allure.attachment_type.TEXT
        )

        try:
            response.json()
            allure.attach(
                response.text,
                name="Response Body",
                attachment_type=allure.attachment_type.JSON
            )
        except ValueError:
            allure.attach(
                response.text,
                name="Response Body",
                attachment_type=allure.attachment_type.TEXT
            )

    # 3. Extract variables from response
    if case.extractions:
        with allure.step("Extract Variables"):
            variable_engine.extract(response, case.extractions)
            allure.attach(
                json.dumps(
                    {k: str(v) for ext in case.extractions for k, v in ext.items()},
                    ensure_ascii=False,
                ),
                name="Extraction Rules",
                attachment_type=allure.attachment_type.JSON,
            )

    # 4. Validate Response (resolve expected values too)
    if case.validations:
        with allure.step("Validate Response"):
            resolved_validations = variable_engine.resolve(case.validations)
            allure.attach(
                json.dumps(resolved_validations, ensure_ascii=False, default=str),
                name="Validation Rules",
                attachment_type=allure.attachment_type.JSON
            )
            Validator.validate(response, resolved_validations)

    # 5. Execute teardown scripts
    if case.teardown:
        with allure.step("Teardown"):
            _execute_scripts(case.teardown, variable_engine, "teardown")
