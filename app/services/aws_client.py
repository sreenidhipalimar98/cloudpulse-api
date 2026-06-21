import boto3
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Map AWS-native statuses to UI-friendly statuses
STATUS_MAP = {
    # EC2
    "running": "healthy",
    "stopped": "critical",
    "stopping": "degraded",
    "pending": "degraded",
    "terminated": "critical",
    # ECS
    "ACTIVE": "healthy",
    "DRAINING": "degraded",
    "INACTIVE": "critical",
    # RDS
    "available": "healthy",
    "backing-up": "healthy",
    "creating": "degraded",
    "deleting": "critical",
    "failed": "critical",
    "maintenance": "degraded",
    "modifying": "degraded",
    "rebooting": "degraded",
    "starting": "degraded",
    "stopped": "critical",
    "stopping": "degraded",
    "storage-optimization": "degraded",
}


def normalize_status(aws_status):
    return STATUS_MAP.get(aws_status, STATUS_MAP.get(aws_status.lower(), "unknown"))


class AWSClient:
    def __init__(self):
        self.region = settings.aws_region
        self.ec2 = boto3.client("ec2", region_name=self.region)
        self.ecs = boto3.client("ecs", region_name=self.region)
        self.rds = boto3.client("rds", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)

    def describe_ec2_instances(self):
        try:
            response = self.ec2.describe_instances()
            instances = []
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "id": instance["InstanceId"],
                        "name": next((t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"), instance["InstanceId"]),
                        "instance_type": instance["InstanceType"],
                        "availability_zone": instance["Placement"]["AvailabilityZone"],
                        "status": normalize_status(instance["State"]["Name"]),
                    })
            return {"instances": instances}
        except Exception as e:
            logger.error(f"EC2 describe failed: {e}")
            return {"instances": []}

    def describe_ecs_services(self):
        try:
            clusters = self.ecs.list_clusters().get("clusterArns", [])
            services = []
            for cluster in clusters:
                cluster_name = cluster.split("/")[-1]
                service_arns = self.ecs.list_services(cluster=cluster).get("serviceArns", [])
                if service_arns:
                    details = self.ecs.describe_services(cluster=cluster, services=service_arns)
                    for svc in details.get("services", []):
                        services.append({
                            "id": svc["serviceArn"],
                            "name": svc["serviceName"],
                            "cluster": cluster_name,
                            "running_count": svc["runningCount"],
                            "desired_count": svc["desiredCount"],
                            "status": normalize_status(svc["status"]),
                        })
            return {"services": services}
        except Exception as e:
            logger.error(f"ECS describe failed: {e}")
            return {"services": []}

    def describe_rds_instances(self):
        try:
            response = self.rds.describe_db_instances()
            instances = []
            for db in response.get("DBInstances", []):
                instances.append({
                    "id": db["DBInstanceIdentifier"],
                    "name": db["DBInstanceIdentifier"],
                    "engine": f"{db['Engine']} {db.get('EngineVersion', '')}",
                    "instance_class": db["DBInstanceClass"],
                    "status": normalize_status(db["DBInstanceStatus"]),
                })
            return {"instances": instances}
        except Exception as e:
            logger.error(f"RDS describe failed: {e}")
            return {"instances": []}
