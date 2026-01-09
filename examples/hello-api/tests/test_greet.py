"""Tests for the greet endpoint."""

import json


def test_greet_with_name(client):
    """Test greet with provided name."""
    response = client.get('/greet?name=Alice')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == {"message": "Hello, Alice!"}


def test_greet_with_special_characters(client):
    """Test greet with special characters in name."""
    response = client.get('/greet?name=José')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == {"message": "Hello, José!"}


def test_greet_with_unicode(client):
    """Test greet with unicode characters."""
    response = client.get('/greet?name=测试')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == {"message": "Hello, 测试!"}


def test_greet_without_name(client):
    """Test greet without name parameter returns error."""
    response = client.get('/greet')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "required" in data["error"].lower()


def test_greet_with_empty_name(client):
    """Test greet with empty name returns error."""
    response = client.get('/greet?name=')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_greet_with_long_name(client):
    """Test greet with very long name (edge case)."""
    long_name = "A" * 500
    response = client.get(f'/greet?name={long_name}')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["message"] == f"Hello, {long_name}!"


def test_greet_with_too_long_name(client):
    """Test greet with name exceeding max length."""
    too_long_name = "A" * 1001
    response = client.get(f'/greet?name={too_long_name}')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "too long" in data["error"].lower()


def test_greet_wrong_method(client):
    """Test greet with POST returns method not allowed."""
    response = client.post('/greet?name=Alice')
    assert response.status_code == 405
