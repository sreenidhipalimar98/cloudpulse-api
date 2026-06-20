from fastapi import APIRouter
from app.services.aws_client import AWSClient

router = APIRouter(tags=["infrastructure"])


@router.get("/ec2")
def list_ec2_instances():
    return AWSClient().describe_ec2_instances()


@router.get("/ecs")
def list_ecs_services():
    return AWSClient().describe_ecs_services()


@router.get("/rds")
def list_rds_instances():
    return AWSClient().describe_rds_instances()
