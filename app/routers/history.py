"""API router for historical metrics from RDS."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional
from app.db.connection import get_db
from app.db.models import MetricSnapshot, AlertHistory, DeploymentHistory

router = APIRouter(tags=["history"])


@router.get("/metrics")
def get_metric_history(
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type: ec2, ecs, rds"),
    resource_id: Optional[str] = Query(default=None),
    metric_name: Optional[str] = Query(default=None),
    hours: int = Query(default=24, le=168, description="Hours of history to retrieve"),
    db: Session = Depends(get_db),
):
    """Get historical metric snapshots for time-series display."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(MetricSnapshot).filter(MetricSnapshot.timestamp >= since)

    if resource_type:
        query = query.filter(MetricSnapshot.resource_type == resource_type)
    if resource_id:
        query = query.filter(MetricSnapshot.resource_id == resource_id)
    if metric_name:
        query = query.filter(MetricSnapshot.metric_name == metric_name)

    results = query.order_by(MetricSnapshot.timestamp).limit(500).all()

    return {
        "metrics": [
            {
                "timestamp": r.timestamp.isoformat(),
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "metric_name": r.metric_name,
                "value": r.metric_value,
                "unit": r.unit,
            }
            for r in results
        ],
        "count": len(results),
        "hours": hours,
    }


@router.get("/alerts")
def get_alert_history(
    hours: int = Query(default=72, le=720),
    severity: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get historical alerts."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(AlertHistory).filter(AlertHistory.timestamp >= since)

    if severity:
        query = query.filter(AlertHistory.severity == severity)

    results = query.order_by(desc(AlertHistory.timestamp)).limit(100).all()

    return {
        "alerts": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "severity": r.severity,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "title": r.title,
                "message": r.message,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in results
        ],
        "count": len(results),
    }


@router.get("/deployments")
def get_deployment_history(
    hours: int = Query(default=168, le=720),
    repo: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get deployment history for correlation with incidents."""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(DeploymentHistory).filter(DeploymentHistory.timestamp >= since)

    if repo:
        query = query.filter(DeploymentHistory.repo == repo)

    results = query.order_by(desc(DeploymentHistory.timestamp)).limit(50).all()

    return {
        "deployments": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "repo": r.repo,
                "commit_sha": r.commit_sha,
                "commit_message": r.commit_message,
                "author": r.author,
                "status": r.status,
                "duration_seconds": r.duration_seconds,
                "workflow_url": r.workflow_url,
            }
            for r in results
        ],
        "count": len(results),
    }
