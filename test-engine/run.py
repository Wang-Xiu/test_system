import os
import sys
import pytest
from pathlib import Path

def main():
    # Setup paths
    engine_dir = Path(__file__).parent
    reports_dir = engine_dir.parent / "reports"
    allure_results_dir = reports_dir / "allure-results"
    
    # Ensure directories exist
    allure_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Build pytest arguments
    pytest_args = [
        str(engine_dir / "tests"),
        "-v",
        "-s",
        f"--alluredir={allure_results_dir}",
        "--clean-alluredir"
    ]
    
    print(f"Starting tests with args: {' '.join(pytest_args)}")
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    
    print(f"Tests finished with exit code: {exit_code}")
    print(f"\nTo generate and view the Allure report, run:")
    print(f"allure serve {allure_results_dir}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
