from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum
from backend.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, comment="用例名称")
    description = Column(String(255), nullable=True, comment="用例描述")
    yaml_content = Column(Text, nullable=False, comment="YAML格式的用例内容")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

class TestTask(Base):
    __tablename__ = "test_tasks"

    id = Column(Integer, primary_key=True, index=True)
    case_ids = Column(String(255), nullable=False, comment="关联的用例IDs，逗号分隔")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    celery_task_id = Column(String(100), nullable=True, index=True, comment="Celery任务ID")
    report_path = Column(String(255), nullable=True, comment="Allure报告相对路径")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始执行时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="执行完成时间")
