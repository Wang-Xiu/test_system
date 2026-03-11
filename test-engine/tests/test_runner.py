import os
import pytest
import allure
from pathlib import Path
from core.yaml_parser import YamlParser, ApiTestCaseModel
from core.http_client import http_client
from core.validator import Validator
from core.logger import logger

def get_yaml_test_cases():
    """
    Find all YAML files in the data directory and parse them into test cases
    """
    # Check if TEST_DATA_DIR env var is set (used by Celery task)
    env_data_dir = os.environ.get("TEST_DATA_DIR")
    if env_data_dir:
        data_dir = Path(env_data_dir)
    else:
        data_dir = Path(__file__).parent.parent / "data"
        
    test_cases = []
    
    if not data_dir.exists():
        return test_cases
        
    for yaml_file in data_dir.rglob("*.yaml"):
        try:
            cases = YamlParser.parse(str(yaml_file))
            for case in cases:
                # Store the file path for reference
                test_cases.append((case, str(yaml_file)))
        except Exception as e:
            logger.error(f"Failed to parse {yaml_file}: {e}")
            
    return test_cases

# Generate test IDs for better pytest output
def generate_test_id(val):
    if isinstance(val, tuple) and isinstance(val[0], ApiTestCaseModel):
        case, file_path = val
        file_name = Path(file_path).name
        return f"{file_name}-{case.name}"
    return str(val)

# Parametrize the test function with all found YAML test cases
@pytest.mark.parametrize("test_case_data", get_yaml_test_cases(), ids=generate_test_id)
def test_api_from_yaml(test_case_data):
    case, file_path = test_case_data
    
    allure.dynamic.title(case.name)
    allure.dynamic.description(f"Source file: {file_path}")
    
    # 1. Send Request
    with allure.step(f"Request: {case.request.method.upper()} {case.request.url}"):
        req_kwargs = {}
        if case.request.headers:
            req_kwargs["headers"] = case.request.headers
        if case.request.params:
            req_kwargs["params"] = case.request.params
        if case.request.json_data:
            req_kwargs["json"] = case.request.json_data
        if case.request.data:
            req_kwargs["data"] = case.request.data
            
        allure.attach(
            str(req_kwargs),
            name="Request Parameters",
            attachment_type=allure.attachment_type.JSON
        )
        
        response = http_client.request(
            method=case.request.method,
            url=case.request.url,
            **req_kwargs
        )
        
        allure.attach(
            str(response.status_code),
            name="Response Status Code",
            attachment_type=allure.attachment_type.TEXT
        )
        
        try:
            resp_body = response.json()
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
            
    # 2. Validate Response
    if case.validations:
        with allure.step("Validate Response"):
            allure.attach(
                str(case.validations),
                name="Validation Rules",
                attachment_type=allure.attachment_type.JSON
            )
            Validator.validate(response, case.validations)
