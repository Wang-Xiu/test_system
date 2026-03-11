import json
from typing import Any, Dict, List
import requests
from .logger import logger

class Validator:
    @staticmethod
    def validate(response: requests.Response, validations: List[Dict[str, Any]]):
        """
        Execute validations against the response
        """
        if not validations:
            return
            
        for validation in validations:
            for operator, expected in validation.items():
                if operator == "eq":
                    Validator._assert_eq(response, expected)
                elif operator == "contains":
                    Validator._assert_contains(response, expected)
                elif operator == "in":
                    Validator._assert_in(response, expected)
                else:
                    logger.warning(f"Unsupported validation operator: {operator}")

    @staticmethod
    def _get_actual_value(response: requests.Response, field: str) -> Any:
        """
        Extract actual value from response based on field name
        """
        if field == "status_code":
            return response.status_code
        elif field == "body":
            try:
                return response.json()
            except ValueError:
                return response.text
        elif field.startswith("headers."):
            header_name = field.split(".", 1)[1]
            return response.headers.get(header_name)
        elif field.startswith("body."):
            # Simple json path extraction (e.g., body.data.id)
            try:
                data = response.json()
                keys = field.split(".")[1:]
                for key in keys:
                    data = data[key]
                return data
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Failed to extract {field} from response: {e}")
                return None
        return None

    @staticmethod
    def _assert_eq(response: requests.Response, expected: Dict[str, Any]):
        for field, expected_value in expected.items():
            actual_value = Validator._get_actual_value(response, field)
            assert actual_value == expected_value, \
                f"Assertion failed: {field} expected {expected_value}, but got {actual_value}"
            logger.info(f"Assertion passed: {field} == {expected_value}")

    @staticmethod
    def _assert_contains(response: requests.Response, expected: Dict[str, Any]):
        for field, expected_value in expected.items():
            actual_value = Validator._get_actual_value(response, field)
            
            if isinstance(actual_value, str):
                assert str(expected_value) in actual_value, \
                    f"Assertion failed: {field} ({actual_value}) does not contain {expected_value}"
            elif isinstance(actual_value, (list, dict)):
                # For dict/list, convert to string to check if it contains the substring
                assert str(expected_value) in json.dumps(actual_value, ensure_ascii=False), \
                    f"Assertion failed: {field} does not contain {expected_value}"
            else:
                assert False, f"Cannot perform 'contains' on type {type(actual_value)}"
                
            logger.info(f"Assertion passed: {field} contains {expected_value}")

    @staticmethod
    def _assert_in(response: requests.Response, expected: Dict[str, Any]):
        for field, expected_list in expected.items():
            actual_value = Validator._get_actual_value(response, field)
            assert isinstance(expected_list, list), f"Expected value for 'in' must be a list, got {type(expected_list)}"
            assert actual_value in expected_list, \
                f"Assertion failed: {field} ({actual_value}) is not in {expected_list}"
            logger.info(f"Assertion passed: {field} in {expected_list}")
