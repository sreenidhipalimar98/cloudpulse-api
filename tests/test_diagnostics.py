"""Tests for /diagnostics endpoints."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def test_ecs_diagnostics_returns_service_info(client, mock_boto):
    mock_boto.list_tasks.return_value = {"taskArns": []}

    with patch("app.routers.diagnostics.boto3.client") as mock_diag_boto:
        mock_ecs = MagicMock()
        mock_logs = MagicMock()

        def client_factory(service, **kwargs):
            if service == "ecs":
                return mock_ecs
            return mock_logs

        mock_diag_boto.side_effect = client_factory

        mock_ecs.list_clusters.return_value = {
            "clusterArns": ["arn:aws:ecs:ap-south-1:123:cluster/test"]
        }
        mock_ecs.describe_services.return_value = {
            "services": [{
                "serviceName": "test-svc",
                "status": "ACTIVE",
                "runningCount": 1,
                "desiredCount": 1,
                "events": [{
                    "createdAt": datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc),
                    "message": "service has reached a steady state.",
                }],
            }]
        }
        mock_ecs.list_tasks.return_value = {"taskArns": []}
        mock_logs.filter_log_events.return_value = {"events": []}

        response = client.get("/diagnostics/ecs/test-svc")

    assert response.status_code == 200
    data = response.json()
    assert data["service_name"] == "test-svc"
    assert data["running_count"] == 1
    assert len(data["events"]) == 1
    assert data["stopped_tasks"] == []


def test_ecs_diagnostics_service_not_found(client, mock_boto):
    with patch("app.routers.diagnostics.boto3.client") as mock_diag_boto:
        mock_ecs = MagicMock()
        mock_diag_boto.return_value = mock_ecs
        mock_ecs.list_clusters.return_value = {"clusterArns": []}

        response = client.get("/diagnostics/ecs/nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_rds_diagnostics_returns_metrics(client, mock_boto):
    with patch("app.routers.diagnostics.boto3.client") as mock_diag_boto:
        mock_rds = MagicMock()
        mock_cw = MagicMock()

        def client_factory(service, **kwargs):
            if service == "rds":
                return mock_rds
            return mock_cw

        mock_diag_boto.side_effect = client_factory

        mock_rds.describe_events.return_value = {"Events": []}
        mock_cw.get_metric_statistics.return_value = {
            "Datapoints": [{
                "Timestamp": datetime(2026, 6, 21, 10, 0, 0, tzinfo=timezone.utc),
                "Average": 25.5,
                "Sum": 3,
            }]
        }

        response = client.get("/diagnostics/rds/test-db")

    assert response.status_code == 200
    data = response.json()
    assert data["instance_id"] == "test-db"
    assert "metrics" in data
