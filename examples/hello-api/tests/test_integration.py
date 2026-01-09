"""Integration tests for Hello API."""

import json


def test_nonexistent_endpoint(client):
    """Test request to non-existent endpoint returns 404."""
    response = client.get('/nonexistent')

    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


def test_multiple_requests_sequential(client):
    """Test multiple sequential requests work correctly."""
    # Health check
    response1 = client.get('/health')
    assert response1.status_code == 200

    # Greet
    response2 = client.get('/greet?name=Test')
    assert response2.status_code == 200

    # Echo
    response3 = client.post(
        '/echo',
        data=json.dumps({"key": "value"}),
        content_type='application/json'
    )
    assert response3.status_code == 200


def test_request_response_content_type(client):
    """Test all responses have correct Content-Type."""
    # Health
    response = client.get('/health')
    assert 'application/json' in response.content_type

    # Greet
    response = client.get('/greet?name=Test')
    assert 'application/json' in response.content_type

    # Echo
    response = client.post(
        '/echo',
        data=json.dumps({"test": "data"}),
        content_type='application/json'
    )
    assert 'application/json' in response.content_type

    # Error
    response = client.get('/nonexistent')
    assert 'application/json' in response.content_type
