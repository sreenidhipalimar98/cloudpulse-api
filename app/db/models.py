from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.connection import Base


class MetricSnapshot(Base):
    """Periodic snapshot of infrastructure metrics for time-series display."""
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # ec2, ecs, rds
    resource_id = Column(String(200), nullable=False)
    metric_name = Column(String(100), nullable=False)  # cpu, memory, connections, cost
    metric_value = Column(Float, nullable=False)
    unit = Column(String(50), default="")
    metadata_ = Column("metadata", JSON, default=dict)


class AlertHistory(Base):
    """Historical record of alerts for audit and trend analysis."""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    severity = Column(String(20), nullable=False)  # critical, degraded, healthy
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, default="")
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class DeploymentHistory(Base):
    """Record of deployments for correlation with incidents."""
    __tablename__ = "deployment_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    repo = Column(String(100), nullable=False)
    commit_sha = Column(String(40), nullable=False)
    commit_message = Column(String(500), default="")
    author = Column(String(100), default="")
    status = Column(String(20), nullable=False)  # success, failure, in_progress
    duration_seconds = Column(Integer, nullable=True)
    workflow_url = Column(String(500), default="")
