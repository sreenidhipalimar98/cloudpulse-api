"""Tests for /alerts endpoint."""


def test_alerts_returns_empty_list(client):
    response = client.get("/alerts/")
    assert response.status_code == 200
    assert response.json() == {"alerts": []}
