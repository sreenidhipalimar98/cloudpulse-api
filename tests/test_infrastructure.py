"""Tests for /infrastructure endpoints."""


def test_ec2_returns_instances(client):
    response = client.get("/infrastructure/ec2")
    assert response.status_code == 200
    data = response.json()
    assert "instances" in data
    assert len(data["instances"]) == 1
    assert data["instances"][0]["id"] == "i-abc123"
    assert data["instances"][0]["status"] == "healthy"


def test_ec2_returns_empty_when_no_instances(client, mock_boto):
    mock_boto.describe_instances.return_value = {"Reservations": []}
    response = client.get("/infrastructure/ec2")
    assert response.status_code == 200
    assert response.json() == {"instances": []}


def test_ecs_returns_services(client):
    response = client.get("/infrastructure/ecs")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert len(data["services"]) == 1
    assert data["services"][0]["name"] == "test-svc"
    assert data["services"][0]["status"] == "healthy"


def test_ecs_returns_empty_when_no_clusters(client, mock_boto):
    mock_boto.list_clusters.return_value = {"clusterArns": []}
    response = client.get("/infrastructure/ecs")
    assert response.status_code == 200
    assert response.json() == {"services": []}


def test_rds_returns_instances(client):
    response = client.get("/infrastructure/rds")
    assert response.status_code == 200
    data = response.json()
    assert "instances" in data
    assert len(data["instances"]) == 1
    assert data["instances"][0]["id"] == "test-db"
    assert data["instances"][0]["status"] == "healthy"


def test_rds_returns_empty_when_no_instances(client, mock_boto):
    mock_boto.describe_db_instances.return_value = {"DBInstances": []}
    response = client.get("/infrastructure/rds")
    assert response.status_code == 200
    assert response.json() == {"instances": []}
