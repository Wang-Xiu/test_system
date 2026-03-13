import subprocess
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from typing import Optional
from backend.scheduler.celery_app import celery_app
from backend.database import SessionLocal
from backend.model.models import TestCase, TestTask, TaskStatus


@celery_app.task(bind=True)
def run_test_cases_task(self, task_id: int, case_ids: list[int], environment_id: int = None):
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

            # Build pytest arguments - pass data dir via command line arg, not env var
            pytest_args = [
                str(engine_dir / "tests" / "test_runner.py"),
                "-v",
                "-s",
                f"--alluredir={allure_results_dir}",
                "--clean-alluredir",
                f"--test-data-dir={temp_dir_path}",
            ]

            # Pass environment config if environment_id is provided
            if environment_id:
                env_config = _build_env_config(db, environment_id)
                if env_config:
                    import json
                    env_config_path = temp_dir_path / "env_config.json"
                    with open(env_config_path, "w", encoding="utf-8") as f:
                        json.dump(env_config, f, ensure_ascii=False)
                    pytest_args.append(f"--env-config={env_config_path}")

            # Execute pytest
            exit_code = pytest.main(pytest_args)

            # Generate Allure HTML report using subprocess
            allure_report_dir = reports_dir / "allure-report" / str(task_id)
            allure_report_dir.parent.mkdir(parents=True, exist_ok=True)

            try:
                subprocess.run(
                    ["allure", "generate", str(allure_results_dir),
                     "-o", str(allure_report_dir), "--clean"],
                    capture_output=True,
                    timeout=120,
                    check=False,
                )
            except FileNotFoundError:
                task.error_msg = "allure command not found, report generation skipped"
            except subprocess.TimeoutExpired:
                task.error_msg = "allure report generation timed out"

            # Update task status
            task.status = TaskStatus.SUCCESS if exit_code == 0 else TaskStatus.FAILED
            task.report_path = f"/reports/{task_id}/index.html"
            task.finished_at = datetime.now()
            db.commit()

            # Send notifications
            try:
                from backend.notify import send_notification
                send_notification(db, task_id, task.status.value, task.project_id, task.report_path)
            except Exception:
                pass  # Don't fail the task if notification fails

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


def _build_env_config(db, environment_id: int) -> Optional[dict]:
    """Build environment configuration dict for test engine."""
    from backend.model.models import Environment, Variable

    env = db.query(Environment).filter(Environment.id == environment_id).first()
    if not env:
        return None

    config = {
        "base_url": env.base_url or "",
        "headers": env.headers or {},
        "auth_config": env.auth_config or {},
        "variables": {},
    }

    # Collect variables with priority: global < project < environment
    variables = {}

    # Global variables (project_id IS NULL)
    global_vars = db.query(Variable).filter(
        Variable.project_id.is_(None),
        Variable.environment_id.is_(None),
    ).all()
    for v in global_vars:
        variables[v.key] = v.value

    # Project variables
    if env.project_id:
        project_vars = db.query(Variable).filter(
            Variable.project_id == env.project_id,
            Variable.environment_id.is_(None),
        ).all()
        for v in project_vars:
            variables[v.key] = v.value

    # Environment variables (highest priority)
    env_vars = db.query(Variable).filter(
        Variable.environment_id == environment_id,
    ).all()
    for v in env_vars:
        variables[v.key] = v.value

    config["variables"] = variables
    return config
