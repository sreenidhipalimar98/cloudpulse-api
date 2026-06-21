from fastapi import APIRouter
import boto3
import logging
from datetime import datetime, timedelta
from app.core.config import settings

router = APIRouter(tags=["diagnostics"])
logger = logging.getLogger(__name__)


@router.get("/ecs/{service_name}")
def diagnose_ecs_service(service_name: str):
    """Get diagnostics for an ECS service: recent events, stopped tasks, and error logs."""
    try:
        ecs = boto3.client("ecs", region_name=settings.aws_region)
        logs = boto3.client("logs", region_name=settings.aws_region)

        # Find the cluster
        clusters = ecs.list_clusters().get("clusterArns", [])
        cluster_arn = None
        service_detail = None

        for cluster in clusters:
            try:
                resp = ecs.describe_services(cluster=cluster, services=[service_name])
                if resp.get("services"):
                    cluster_arn = cluster
                    service_detail = resp["services"][0]
                    break
            except Exception:
                continue

        if not service_detail:
            return {"error": f"Service '{service_name}' not found", "events": [], "stopped_tasks": [], "recent_errors": []}

        # 1. Recent service events (deployments, task failures)
        events = []
        for event in service_detail.get("events", [])[:10]:
            events.append({
                "timestamp": event["createdAt"].isoformat(),
                "message": event["message"],
            })

        # 2. Recently stopped tasks with stop reasons
        stopped_tasks = []
        stopped_task_arns = ecs.list_tasks(
            cluster=cluster_arn,
            serviceName=service_name,
            desiredStatus="STOPPED",
            maxResults=5,
        ).get("taskArns", [])

        if stopped_task_arns:
            task_details = ecs.describe_tasks(cluster=cluster_arn, tasks=stopped_task_arns)
            for task in task_details.get("tasks", []):
                stopped_tasks.append({
                    "task_id": task["taskArn"].split("/")[-1],
                    "stopped_at": task.get("stoppedAt", "").isoformat() if task.get("stoppedAt") else None,
                    "stop_reason": task.get("stoppedReason", "Unknown"),
                    "stop_code": task.get("stopCode", "Unknown"),
                    "exit_code": _get_exit_code(task),
                })

        # 3. Recent error logs from CloudWatch
        recent_errors = []
        log_group = f"/ecs/cloudpulse-{settings.app_env if hasattr(settings, 'app_env') else 'dev'}"
        try:
            now = int(datetime.utcnow().timestamp() * 1000)
            one_hour_ago = int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000)

            log_resp = logs.filter_log_events(
                logGroupName=log_group,
                startTime=one_hour_ago,
                endTime=now,
                filterPattern="?ERROR ?error ?Error ?Exception ?Traceback ?CRITICAL",
                limit=20,
            )

            for event in log_resp.get("events", []):
                recent_errors.append({
                    "timestamp": datetime.fromtimestamp(event["timestamp"] / 1000).isoformat(),
                    "message": event["message"].strip(),
                    "stream": event.get("logStreamName", ""),
                })
        except Exception as e:
            logger.warning(f"Could not fetch logs: {e}")

        return {
            "service_name": service_name,
            "status": service_detail.get("status", "UNKNOWN"),
            "running_count": service_detail.get("runningCount", 0),
            "desired_count": service_detail.get("desiredCount", 0),
            "events": events,
            "stopped_tasks": stopped_tasks,
            "recent_errors": recent_errors,
        }

    except Exception as e:
        logger.error(f"ECS diagnostics failed: {e}")
        return {"error": str(e), "events": [], "stopped_tasks": [], "recent_errors": []}


@router.get("/rds/{instance_id}")
def diagnose_rds_instance(instance_id: str):
    """Get diagnostics for an RDS instance: recent events and key metrics."""
    try:
        rds = boto3.client("rds", region_name=settings.aws_region)
        cw = boto3.client("cloudwatch", region_name=settings.aws_region)

        # RDS events from last 24 hours
        events_resp = rds.describe_events(
            SourceIdentifier=instance_id,
            SourceType="db-instance",
            Duration=1440,  # last 24 hours in minutes
        )

        events = []
        for event in events_resp.get("Events", [])[:15]:
            events.append({
                "timestamp": event["Date"].isoformat(),
                "message": event["Message"],
                "category": event.get("EventCategories", ["unknown"])[0],
            })

        # Key metrics: CPU, connections, free storage
        now = datetime.utcnow()
        metrics = {}
        for metric_name, stat in [("CPUUtilization", "Average"), ("DatabaseConnections", "Sum"), ("FreeStorageSpace", "Average")]:
            try:
                resp = cw.get_metric_statistics(
                    Namespace="AWS/RDS",
                    MetricName=metric_name,
                    Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
                    StartTime=now - timedelta(minutes=30),
                    EndTime=now,
                    Period=300,
                    Statistics=[stat],
                )
                datapoints = sorted(resp.get("Datapoints", []), key=lambda x: x["Timestamp"], reverse=True)
                if datapoints:
                    metrics[metric_name] = round(datapoints[0][stat], 2)
            except Exception:
                pass

        return {
            "instance_id": instance_id,
            "events": events,
            "metrics": {
                "cpu_percent": metrics.get("CPUUtilization", None),
                "connections": metrics.get("DatabaseConnections", None),
                "free_storage_gb": round(metrics.get("FreeStorageSpace", 0) / (1024 ** 3), 2) if metrics.get("FreeStorageSpace") else None,
            },
        }

    except Exception as e:
        logger.error(f"RDS diagnostics failed: {e}")
        return {"error": str(e), "events": [], "metrics": {}}


def _get_exit_code(task):
    """Extract exit code from the first essential container."""
    for container in task.get("containers", []):
        if container.get("exitCode") is not None:
            return container["exitCode"]
    return None
