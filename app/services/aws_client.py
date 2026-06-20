import boto3
from app.core.config import settings

class AWSClient:
    def __init__(self):
        self.region = settings.aws_region
        self.ec2 = boto3.client("ec2", region_name=self.region)
        self.ecs = boto3.client("ecs", region_name=self.region)
        self.rds = boto3.client("rds", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)

    def describe_ec2_instances(self):
        response = self.ec2.describe_instances()
        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "id": instance["InstanceId"],
                    "state": instance["State"]["Name"],
                    "type": instance["InstanceType"],
                })
        return {"instances": instances}

    def describe_ecs_services(self):
        clusters = self.ecs.list_clusters().get("clusterArns", [])
        services = []
        for cluster in clusters:
            service_arns = self.ecs.list_services(cluster=cluster).get("serviceArns", [])
            if service_arns:
                details = self.ecs.describe_services(cluster=cluster, services=service_arns)
                for svc in details.get("services", []):
                    services.append({
                        "name": svc["serviceName"],
                        "status": svc["status"],
                        "running": svc["runningCount"],
                        "desired": svc["desiredCount"],
                    })
        return {"services": services}

    def describe_rds_instances(self):
        response = self.rds.describe_db_instances()
        instances = []
        for db in response.get("DBInstances", []):
            instances.append({
                "id": db["DBInstanceIdentifier"],
                "status": db["DBInstanceStatus"],
                "engine": db["Engine"],
                "class": db["DBInstanceClass"],
            })
        return {"instances": instances}
