"""Tests for /pipelines endpoint."""
from unittest.mock import patch, MagicMock


def test_pipelines_returns_workflow_runs(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_runs": [{
            "id": 12345,
            "name": "CI/CD",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc12345def67890",
            "head_branch": "develop",
            "head_commit": {
                "author": {"name": "Test User"},
                "message": "feat: something",
            },
            "run_started_at": "2026-06-21T10:00:00Z",
            "updated_at": "2026-06-21T10:02:30Z",
            "html_url": "https://github.com/test/repo/actions/runs/12345",
        }]
    }

    with patch("app.routers.pipelines.httpx.get", return_value=mock_response):
        response = client.get("/pipelines/")

    assert response.status_code == 200
    data = response.json()
    assert len(data["pipelines"]) >= 1
    run = data["pipelines"][0]
    assert run["status"] == "healthy"
    assert run["commit"] == "abc12345"
    assert run["duration_seconds"] == 150


def test_pipelines_returns_empty_on_error(client):
    with patch("app.routers.pipelines.httpx.get", side_effect=Exception("timeout")):
        response = client.get("/pipelines/")

    assert response.status_code == 200
    assert response.json() == {"pipelines": []}


def test_pipelines_maps_failure_to_critical(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_runs": [{
            "id": 99,
            "name": "CI/CD",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "deadbeef12345678",
            "head_branch": "develop",
            "head_commit": {
                "author": {"name": "Dev"},
                "message": "broke stuff",
            },
            "run_started_at": "2026-06-21T10:00:00Z",
            "updated_at": "2026-06-21T10:01:00Z",
            "html_url": "https://github.com/test/actions/runs/99",
        }]
    }

    with patch("app.routers.pipelines.httpx.get", return_value=mock_response):
        response = client.get("/pipelines/")

    assert response.json()["pipelines"][0]["status"] == "critical"
