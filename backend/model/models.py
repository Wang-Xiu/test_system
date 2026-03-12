from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, Boolean, JSON,
    ForeignKey, Table, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


# ---------- Association tables ----------

task_case_association = Table(
    "task_case_association",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("task_id", Integer, ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("case_id", Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("order", Integer, nullable=False, default=0, comment="Execution order"),
)

suite_case_association = Table(
    "suite_case_association",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("suite_id", Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("case_id", Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("order", Integer, nullable=False, default=0, comment="Execution order"),
)


# ---------- Project & Environment ----------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="项目名称")
    description = Column(String(500), nullable=True, comment="项目描述")
    base_url = Column(String(500), nullable=True, comment="默认 Base URL")
    webhook_secret = Column(String(255), nullable=True, comment="Webhook 密钥")
    notification_config = Column(JSON, nullable=True, comment="通知配置")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    environments = relationship("Environment", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project")
    variables = relationship("Variable", back_populates="project",
                             foreign_keys="[Variable.project_id]",
                             cascade="all, delete-orphan")


class Environment(Base):
    __tablename__ = "environments"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_env_project_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), nullable=True, comment="环境 Base URL")
    headers = Column(JSON, nullable=True, comment="公共请求头")
    auth_config = Column(JSON, nullable=True, comment="认证配置")
    is_default = Column(Boolean, default=False, comment="是否默认环境")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="environments")
    variables = relationship("Variable", back_populates="environment", cascade="all, delete-orphan")


class Variable(Base):
    __tablename__ = "variables"
    __table_args__ = (
        UniqueConstraint("project_id", "environment_id", "key", name="uq_var_scope_key"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    environment_id = Column(Integer, ForeignKey("environments.id", ondelete="CASCADE"), nullable=True, index=True)
    key = Column(String(255), nullable=False, comment="变量名")
    value = Column(Text, nullable=False, comment="变量值")
    var_type = Column(String(50), default="string", comment="变量类型: string/integer/json/secret")
    description = Column(String(500), nullable=True, comment="变量描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="variables", foreign_keys=[project_id])
    environment = relationship("Environment", back_populates="variables")


# ---------- Test Case ----------

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, comment="用例名称")
    description = Column(String(255), nullable=True, comment="用例描述")
    yaml_content = Column(Text, nullable=False, comment="YAML格式的用例内容")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    project = relationship("Project", back_populates="test_cases")


# ---------- Test Task ----------

class TestTask(Base):
    __tablename__ = "test_tasks"

    id = Column(Integer, primary_key=True, index=True)
    case_ids = Column(String(255), nullable=True, comment="关联的用例IDs，逗号分隔（旧字段，保留兼容）")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    celery_task_id = Column(String(100), nullable=True, index=True, comment="Celery任务ID")
    report_path = Column(String(255), nullable=True, comment="Allure报告相对路径")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    environment_id = Column(Integer, ForeignKey("environments.id", ondelete="SET NULL"), nullable=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始执行时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="执行完成时间")

    cases = relationship("TestCase", secondary=task_case_association, order_by=task_case_association.c.order)
    project = relationship("Project")
    environment = relationship("Environment")
    suite = relationship("TestSuite")


# ---------- Test Suite ----------

class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="套件名称")
    description = Column(String(500), nullable=True, comment="套件描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project")
    cases = relationship("TestCase", secondary=suite_case_association, order_by=suite_case_association.c.order)


# ---------- Scheduled Job ----------

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id = Column(Integer, ForeignKey("environments.id", ondelete="CASCADE"), nullable=False)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="定时任务名称")
    cron_expression = Column(String(100), nullable=False, comment="Cron 表达式")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_run_at = Column(DateTime(timezone=True), nullable=True, comment="上次执行时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project")
    environment = relationship("Environment")
    suite = relationship("TestSuite")
