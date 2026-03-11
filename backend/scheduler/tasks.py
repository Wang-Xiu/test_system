import os
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from backend.scheduler.celery_app import celery_app
from backend.database import SessionLocal
from backend.model.models import TestCase, TestTask, TaskStatus

@celery_app.task(bind=True)
def run_test_cases_task(self, task_id: int, case_ids: list[int]):
    db = SessionLocal()
    try:
        # Update task status to RUNNING
        task = db.query(TestTask).filter(TestTask.id == task_id).first()
        if not task:
            return {"error": f"Task {task_id} not found"}
            
        task.status = TaskStatus.RUNNING
        task.celery_task_id = self.request.id
        task.started_at = datetime.now()
        db.commit()

        # Fetch test cases
        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        if not cases:
            task.status = TaskStatus.FAILED
            task.error_msg = "No valid test cases found"
            task.finished_at = datetime.now()
            db.commit()
            return {"error": "No valid test cases found"}

        # Create temporary directory for YAML files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Write YAML content to temp files
            for case in cases:
                file_path = temp_dir_path / f"case_{case.id}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(case.yaml_content)

            # Setup paths for execution
            project_root = Path(__file__).parent.parent.parent
            engine_dir = project_root / "test-engine"
            reports_dir = project_root / "reports"
            allure_results_dir = reports_dir / "allure-results" / str(task_id)
            
            allure_results_dir.mkdir(parents=True, exist_ok=True)

            # Build pytest arguments
            # We need to tell pytest to run the test_runner.py but point it to our temp dir for data
            # Since our current test_runner.py hardcodes the data dir, we'll pass it via env var
            os.environ["TEST_DATA_DIR"] = str(temp_dir_path)
            
            pytest_args = [
                str(engine_dir / "tests" / "test_runner.py"),
                "-v",
                "-s",
                f"--alluredir={allure_results_dir}",
                "--clean-alluredir"
            ]

            # Execute pytest
            exit_code = pytest.main(pytest_args)

            # Generate Allure HTML report
            allure_report_dir = reports_dir / "allure-report" / str(task_id)
            allure_report_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Use allure command line to generate report
            os.system(f"allure generate {allure_results_dir} -o {allure_report_dir} --clean")

            # Update task status
            task.status = TaskStatus.SUCCESS if exit_code == 0 else TaskStatus.FAILED
            task.report_path = f"/reports/{task_id}/index.html"
            task.finished_at = datetime.now()
            db.commit()

            return {
                "task_id": task_id,
                "status": task.status,
                "exit_code": exit_code,
                "report_path": task.report_path
            }

    except Exception as e:
        task = db.query(TestTask).filter(TestTask.id == task_id).first()
        if task:
            task.status = TaskStatus.ERROR
            task.error_msg = str(e)
            task.finished_at = datetime.now()
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()
