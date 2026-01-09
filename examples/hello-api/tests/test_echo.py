"""Tests for the echo endpoint."""

import json


def test_echo_simple_json(client):
    """Test echo with simple JSON object."""
    payload = {"test": "value"}
    response = client.post(
        '/echo',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == payload


def test_echo_nested_json(client):
    """Test echo with nested JSON object."""
    payload = {
        "user": {
            "name": "Alice",
            "age": 30,
            "tags": ["developer", "python"]
        }
    }
    response = client.post(
        '/echo',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == payload


def test_echo_array(client):
    """Test echo with JSON array."""
    payload = [1, 2, 3, "four", {"five": 5}]
    response = client.post(
        '/echo',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == payload


def test_echo_with_unicode(client):
    """Test echo with unicode characters."""
    payload = {"message": "Hello 世界 🌍"}
    response = client.post(
        '/echo',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == payload


def test_echo_with_invalid_json(client):
    """Test echo with malformed JSON returns error."""
    response = client.post(
        '/echo',
        data='invalid json',
        content_type='application/json'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "invalid" in data["error"].lower() or "json" in data["error"].lower()


def test_echo_with_empty_body(client):
    """Test echo with empty body returns error."""
    response = client.post(
        '/echo',
        data='',
        content_type='application/json'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_echo_with_empty_object(client):
    """Test echo with empty JSON object returns error."""
    response = client.post(
        '/echo',
        data='{}',
        content_type='application/json'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "empty" in data["error"].lower()


def test_echo_without_content_type(client):
    """Test echo without Content-Type header returns error."""
    response = client.post(
        '/echo',
        data='{"test": "value"}'
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_echo_wrong_method(client):
    """Test echo with GET returns method not allowed."""
    response = client.get('/echo')
    assert response.status_code == 405
