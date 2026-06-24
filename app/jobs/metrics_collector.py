"""Background job that collects metrics periodically and stores them in RDS."""
import logging
from datetime import datetime
from app.db.connection import get_session_factory
from app.db.models import MetricSnapshot
from app.services.aws_client import AWSClient

logger = logging.getLogger(__name__)


def collect_and_store_metrics():
    """Called every 5 minutes by APScheduler. Snapshots current state into RDS."""
    try:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        client = AWSClient()
        now = datetime.utcnow()

        # ECS metrics
        try:
            ecs_data = client.describe_ecs_services()
            for svc in ecs_data.get("services", []):
                session.add(MetricSnapshot(
                    timestamp=now,
                    resource_type="ecs",
                    resource_id=svc["name"],
                    metric_name="running_count",
                    metric_value=float(svc.get("running_count", 0)),
                    unit="tasks",
                ))
        except Exception as e:
            logger.warning(f"ECS metric collection failed: {e}")

        # RDS metrics
        try:
            rds_data = client.describe_rds_instances()
            for db in rds_data.get("instances", []):
                session.add(MetricSnapshot(
                    timestamp=now,
                    resource_type="rds",
                    resource_id=db["id"],
                    metric_name="status",
                    metric_value=1.0 if db.get("status") == "healthy" else 0.0,
                    unit="boolean",
                ))
        except Exception as e:
            logger.warning(f"RDS metric collection failed: {e}")

        # EC2 metrics
        try:
            ec2_data = client.describe_ec2_instances()
            session.add(MetricSnapshot(
                timestamp=now,
                resource_type="ec2",
                resource_id="all",
                metric_name="instance_count",
                metric_value=float(len(ec2_data.get("instances", []))),
                unit="instances",
            ))
        except Exception as e:
            logger.warning(f"EC2 metric collection failed: {e}")

        session.commit()
        logger.info(f"Metrics snapshot stored at {now.isoformat()}")

    except Exception as e:
        logger.error(f"Metric collection job failed: {e}")
    finally:
        if 'session' in locals():
            session.close()
