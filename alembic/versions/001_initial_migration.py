"""initial migration with all tables

Revision ID: 001
Revises:
Create Date: 2026-03-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("webhook_secret", sa.String(255), nullable=True),
        sa.Column("notification_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Environments ---
    op.create_table(
        "environments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("auth_config", sa.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "name", name="uq_env_project_name"),
    )

    # --- Variables ---
    op.create_table(
        "variables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("environment_id", sa.Integer(), sa.ForeignKey("environments.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("var_type", sa.String(50), default="string"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "environment_id", "key", name="uq_var_scope_key"),
    )

    # --- Test Suites ---
    op.create_table(
        "test_suites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Add project_id, environment_id, suite_id to test_cases and test_tasks ---
    # test_cases: add project_id
    op.add_column("test_cases", sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True))

    # test_tasks: add project_id, environment_id, suite_id
    op.add_column("test_tasks", sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True))
    op.add_column("test_tasks", sa.Column("environment_id", sa.Integer(), sa.ForeignKey("environments.id", ondelete="SET NULL"), nullable=True, index=True))
    op.add_column("test_tasks", sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id", ondelete="SET NULL"), nullable=True, index=True))

    # --- Task-Case association table ---
    op.create_table(
        "task_case_association",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order", sa.Integer(), nullable=False, default=0),
    )

    # --- Suite-Case association table ---
    op.create_table(
        "suite_case_association",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order", sa.Integer(), nullable=False, default=0),
    )

    # --- Scheduled Jobs ---
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("environment_id", sa.Integer(), sa.ForeignKey("environments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suite_id", sa.Integer(), sa.ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Migrate existing task case_ids to association table ---
    # This is a data migration: parse comma-separated case_ids into rows
    conn = op.get_bind()
    tasks = conn.execute(sa.text("SELECT id, case_ids FROM test_tasks WHERE case_ids IS NOT NULL AND case_ids != ''"))
    for task_row in tasks:
        task_id = task_row[0]
        case_ids_str = task_row[1]
        if case_ids_str:
            for order, cid_str in enumerate(case_ids_str.split(",")):
                cid_str = cid_str.strip()
                if cid_str.isdigit():
                    conn.execute(
                        sa.text("INSERT INTO task_case_association (task_id, case_id, `order`) VALUES (:tid, :cid, :ord)"),
                        {"tid": task_id, "cid": int(cid_str), "ord": order},
                    )


def downgrade() -> None:
    op.drop_table("scheduled_jobs")
    op.drop_table("suite_case_association")
    op.drop_table("task_case_association")
    op.drop_column("test_tasks", "suite_id")
    op.drop_column("test_tasks", "environment_id")
    op.drop_column("test_tasks", "project_id")
    op.drop_column("test_cases", "project_id")
    op.drop_table("test_suites")
    op.drop_table("variables")
    op.drop_table("environments")
    op.drop_table("projects")
