import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ScriptAction(BaseModel):
    type: str
    key: Optional[str] = None
    value: Optional[str] = None
    seconds: Optional[float] = None
    message: Optional[str] = None
    code: Optional[str] = None


class RequestModel(BaseModel):
    method: str
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    json_data: Dict[str, Any] = Field(default_factory=dict, alias="json")
    data: Dict[str, Any] = Field(default_factory=dict)


class ApiTestCaseModel(BaseModel):
    name: str
    request: RequestModel
    validations: List[Dict[str, Any]] = Field(default_factory=list, alias="validate")
    extractions: List[Dict[str, str]] = Field(default_factory=list, alias="extract")
    setup: List[ScriptAction] = Field(default_factory=list)
    teardown: List[ScriptAction] = Field(default_factory=list)


class YamlParser:
    @staticmethod
    def parse(file_path: str) -> List[ApiTestCaseModel]:
        """
        Parse YAML file and return a list of ApiTestCaseModel.
        Supports multi-document YAML (separated by ---).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        test_cases = []
        with open(path, "r", encoding="utf-8") as f:
            for data in yaml.safe_load_all(f):
                if not data:
                    continue

                # Handle both single test case (dict) and multiple test cases (list)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    test_cases.append(ApiTestCaseModel(**item))

        return test_cases
