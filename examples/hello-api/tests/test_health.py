"""Tests for the health check endpoint."""

import json


def test_health_check_success(client):
    """Test health check returns success."""
    response = client.get('/health')

    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = json.loads(response.data)
    assert data == {"status": "ok"}


def test_health_check_no_auth_required(client):
    """Test health check works without authentication."""
    response = client.get('/health')
    assert response.status_code == 200


def test_health_check_wrong_method(client):
    """Test health check with POST returns method not allowed."""
    response = client.post('/health')
    assert response.status_code == 405
