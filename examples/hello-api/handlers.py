"""Route handlers for Hello API endpoints."""

from flask import request
from validators import validate_name, validate_json_body


def health_check():
    """
    Health check endpoint.

    Returns:
        tuple: (response_dict, status_code)
    """
    return {"status": "ok"}, 200


def greet():
    """
    Greeting endpoint that returns personalized message.

    Query Parameters:
        name: Name to greet (required)

    Returns:
        tuple: (response_dict, status_code)
    """
    try:
        name = request.args.get('name')
        validated_name = validate_name(name)
        return {"message": f"Hello, {validated_name}!"}, 200
    except ValueError as e:
        return {"error": str(e)}, 400


def echo():
    """
    Echo endpoint that returns the JSON body sent in request.

    Returns:
        tuple: (response_dict, status_code)
    """
    try:
        data = validate_json_body(request)
        return data, 200
    except ValueError as e:
        return {"error": str(e)}, 400
