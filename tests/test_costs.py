"""Tests for /costs endpoints."""
from unittest.mock import patch, MagicMock


def test_cost_summary_returns_data(client):
    with patch("app.routers.costs.boto3.client") as mock_ce:
        mock_client = MagicMock()
        mock_ce.return_value = mock_client
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "Total": {"UnblendedCost": {"Amount": "42.50"}}
            }]
        }
        response = client.get("/costs/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == 42.5
    assert data["currency"] == "USD"
    assert data["status"] == "healthy"  # under $50


def test_cost_summary_degraded_over_50(client):
    with patch("app.routers.costs.boto3.client") as mock_ce:
        mock_client = MagicMock()
        mock_ce.return_value = mock_client
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "Total": {"UnblendedCost": {"Amount": "75.00"}}
            }]
        }
        response = client.get("/costs/summary")

    assert response.json()["status"] == "degraded"


def test_cost_summary_critical_over_100(client):
    with patch("app.routers.costs.boto3.client") as mock_ce:
        mock_client = MagicMock()
        mock_ce.return_value = mock_client
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "Total": {"UnblendedCost": {"Amount": "150.00"}}
            }]
        }
        response = client.get("/costs/summary")

    assert response.json()["status"] == "critical"


def test_cost_by_service_returns_breakdown(client):
    with patch("app.routers.costs.boto3.client") as mock_ce:
        mock_client = MagicMock()
        mock_ce.return_value = mock_client
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "Groups": [
                    {"Keys": ["Amazon ECS"], "Metrics": {"UnblendedCost": {"Amount": "9.50"}}},
                    {"Keys": ["Amazon RDS"], "Metrics": {"UnblendedCost": {"Amount": "13.20"}}},
                ]
            }]
        }
        response = client.get("/costs/by-service")

    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert len(data["services"]) == 2
    assert data["services"][0]["name"] == "Amazon RDS"  # sorted by cost desc
    assert data["services"][0]["cost"] == 13.2


def test_cost_by_service_handles_error(client):
    with patch("app.routers.costs.boto3.client") as mock_ce:
        mock_ce.return_value.get_cost_and_usage.side_effect = Exception("Access denied")
        response = client.get("/costs/by-service")

    assert response.status_code == 200
    data = response.json()
    assert data["services"] == []
    assert "error" in data
