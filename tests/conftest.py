"""Shared test fixtures and configuration."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_boto():
    """Mock all boto3 clients used across the app."""
    with patch("app.services.aws_client.boto3.client") as mock:
        instance = MagicMock()
        mock.return_value = instance

        # Default responses for all AWS services
        instance.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{
                    "InstanceId": "i-abc123",
                    "State": {"Name": "running"},
                    "InstanceType": "t3.micro",
                    "Placement": {"AvailabilityZone": "ap-south-1a"},
                    "Tags": [{"Key": "Name", "Value": "test-instance"}],
                }]}
            ]
        }
        instance.list_clusters.return_value = {
            "clusterArns": ["arn:aws:ecs:ap-south-1:123456:cluster/test-cluster"]
        }
        instance.list_services.return_value = {
            "serviceArns": ["arn:aws:ecs:ap-south-1:123456:service/test-cluster/test-svc"]
        }
        instance.describe_services.return_value = {
            "services": [{
                "serviceArn": "arn:aws:ecs:ap-south-1:123456:service/test-cluster/test-svc",
                "serviceName": "test-svc",
                "status": "ACTIVE",
                "runningCount": 1,
                "desiredCount": 1,
            }]
        }
        instance.describe_db_instances.return_value = {
            "DBInstances": [{
                "DBInstanceIdentifier": "test-db",
                "DBInstanceStatus": "available",
                "Engine": "postgres",
                "EngineVersion": "16.14",
                "DBInstanceClass": "db.t4g.micro",
            }]
        }

        yield instance


@pytest.fixture
def client(mock_boto):
    """Create a test client with all boto3 calls mocked."""
    from app.main import app
    return TestClient(app)
