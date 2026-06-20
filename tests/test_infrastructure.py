from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_list_ec2_instances_returns_200():
    with patch("app.services.aws_client.boto3.client") as mock_boto:
        mock_instance = MagicMock()
        mock_boto.return_value = mock_instance
        mock_instance.describe_instances.return_value = {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-123", "State": {"Name": "running"}, "InstanceType": "t3.micro"}]}
            ]
        }
        mock_instance.list_clusters.return_value = {"clusterArns": []}
        mock_instance.describe_db_instances.return_value = {"DBInstances": []}

        from app.main import app
        client = TestClient(app)
        response = client.get("/infrastructure/ec2")
    assert response.status_code == 200
