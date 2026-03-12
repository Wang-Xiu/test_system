import os
import sys
import json
import pytest
from pathlib import Path

# Add the test-engine directory to the Python path
engine_dir = Path(__file__).parent.parent
sys.path.insert(0, str(engine_dir))


def pytest_addoption(parser):
    """Register custom command line options."""
    parser.addoption(
        "--test-data-dir",
        action="store",
        default=None,
        help="Directory containing YAML test case files",
    )
    parser.addoption(
        "--env-config",
        action="store",
        default=None,
        help="Path to environment configuration JSON file",
    )


@pytest.fixture(scope="session")
def variable_engine(request):
    """Session-scoped VariableEngine that persists across all test cases."""
    from core.variable_engine import VariableEngine

    engine = VariableEngine()

    env_config_path = request.config.getoption("--env-config", default=None)
    if env_config_path and Path(env_config_path).exists():
        with open(env_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        variables = config.get("variables", {})
        engine.load_variables(global_vars=variables)

    return engine
