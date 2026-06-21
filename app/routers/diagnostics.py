from fastapi import APIRouter, Query
import boto3
import logging
from datetime import datetime, timedelta
from app.core.config import settings

router = APIRouter(tags=["diagnostics"])
logger = logging.getLogger(__name__)

LOG_GROUP = "/ecs/cloudpulse-dev"


@router.get("/ecs/{service_name}")
def diagnose_ecs_service(service_name: str):
    """Get diagnostics for an ECS service: recent events, stopped tasks, and error logs."""
    try:
        ecs = boto3.client("ecs", region_name=settings.aws_region)
        logs_client = boto3.client("logs", region_name=settings.aws_region)

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
            return {"error": f"Service '{service_name}' not found", "events": [], "stopped_tasks": [], "recent_errors": [], "recent_logs": []}

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

        # 3. Recent error logs (filtered for errors/exceptions)
        recent_errors = _fetch_logs(logs_client, LOG_GROUP, filter_pattern="?ERROR ?error ?Exception ?Traceback ?CRITICAL ?500", limit=30)

        # 4. Recent application logs (last 50 lines, unfiltered — the actual API output)
        recent_logs = _fetch_logs(logs_client, LOG_GROUP, filter_pattern=None, limit=50)

        return {
            "service_name": service_name,
            "status": service_detail.get("status", "UNKNOWN"),
            "running_count": service_detail.get("runningCount", 0),
            "desired_count": service_detail.get("desiredCount", 0),
            "events": events,
            "stopped_tasks": stopped_tasks,
            "recent_errors": recent_errors,
            "recent_logs": recent_logs,
        }

    except Exception as e:
        logger.error(f"ECS diagnostics failed: {e}")
        return {"error": str(e), "events": [], "stopped_tasks": [], "recent_errors": [], "recent_logs": []}


@router.get("/ecs/{service_name}/logs")
def get_ecs_logs(service_name: str, minutes: int = Query(default=30, le=360), filter: str = Query(default=None)):
    """Get raw application logs for an ECS service. Optional filter pattern."""
    try:
        logs_client = boto3.client("logs", region_name=settings.aws_region)
        results = _fetch_logs(logs_client, LOG_GROUP, filter_pattern=filter, limit=100, minutes_back=minutes)
        return {"logs": results, "log_group": LOG_GROUP, "minutes": minutes, "filter": filter}
    except Exception as e:
        logger.error(f"Log fetch failed: {e}")
        return {"logs": [], "error": str(e)}


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
            Duration=1440,
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


def _fetch_logs(logs_client, log_group, filter_pattern=None, limit=50, minutes_back=60):
    """Fetch recent logs from CloudWatch, optionally filtered."""
    try:
        now = int(datetime.utcnow().timestamp() * 1000)
        start = int((datetime.utcnow() - timedelta(minutes=minutes_back)).timestamp() * 1000)

        kwargs = {
            "logGroupName": log_group,
            "startTime": start,
            "endTime": now,
            "limit": limit,
            "interleaved": True,
        }
        if filter_pattern:
            kwargs["filterPattern"] = filter_pattern

        log_resp = logs_client.filter_log_events(**kwargs)

        results = []
        for event in log_resp.get("events", []):
            msg = event["message"].strip()
            level = "info"
            if any(kw in msg for kw in ["ERROR", "CRITICAL", "Traceback", "Exception"]):
                level = "error"
            elif any(kw in msg for kw in ["WARNING", "WARN"]):
                level = "warning"

            results.append({
                "timestamp": datetime.fromtimestamp(event["timestamp"] / 1000).isoformat(),
                "message": msg,
                "level": level,
                "stream": event.get("logStreamName", ""),
            })
        return results
    except Exception as e:
        logger.warning(f"Could not fetch logs from {log_group}: {e}")
        return []


def _get_exit_code(task):
    """Extract exit code from the first essential container."""
    for container in task.get("containers", []):
        if container.get("exitCode") is not None:
            return container["exitCode"]
    return None
