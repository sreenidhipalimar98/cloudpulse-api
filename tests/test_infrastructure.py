from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_ec2_instances_returns_200():
    mock_response = {
        "Reservations": [
            {"Instances": [{"InstanceId": "i-123", "State": {"Name": "running"}, "InstanceType": "t3.micro"}]}
        ]
    }
    with patch("app.services.aws_client.boto3.client") as mock_boto:
        mock_boto.return_value.describe_instances.return_value = mock_response
        response = client.get("/infrastructure/ec2")
    assert response.status_code == 200
