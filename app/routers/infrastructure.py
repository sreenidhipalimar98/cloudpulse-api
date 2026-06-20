from fastapi import APIRouter
from app.services.aws_client import AWSClient

router = APIRouter(tags=["infrastructure"])
client = AWSClient()

@router.get("/ec2")
def list_ec2_instances():
    return client.describe_ec2_instances()

@router.get("/ecs")
def list_ecs_services():
    return client.describe_ecs_services()

@router.get("/rds")
def list_rds_instances():
    return client.describe_rds_instances()
