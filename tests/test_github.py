"""Tests for /github endpoints."""
from unittest.mock import patch, MagicMock


def test_commits_returns_data(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "sha": "abc12345def67890",
            "commit": {
                "message": "feat: add new feature\n\nDetailed description",
                "author": {"name": "Test User", "date": "2026-06-21T10:00:00Z"},
            },
            "html_url": "https://github.com/test/repo/commit/abc12345",
        }
    ]

    with patch("app.routers.github.httpx.get", return_value=mock_response):
        response = client.get("/github/commits")

    assert response.status_code == 200
    data = response.json()
    assert len(data["commits"]) >= 1
    assert data["commits"][0]["sha"] == "abc12345"
    assert data["commits"][0]["message"] == "feat: add new feature"
    assert data["commits"][0]["author"] == "Test User"


def test_commits_handles_rate_limit(client):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "API rate limit exceeded"

    with patch("app.routers.github.httpx.get", return_value=mock_response):
        response = client.get("/github/commits")

    assert response.status_code == 200
    data = response.json()
    assert data["commits"] == []
    assert "errors" in data


def test_commits_handles_network_error(client):
    with patch("app.routers.github.httpx.get", side_effect=Exception("Connection timeout")):
        response = client.get("/github/commits")

    assert response.status_code == 200
    data = response.json()
    assert data["commits"] == []
    assert "errors" in data
