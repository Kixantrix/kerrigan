"""Request validation functions for Hello API."""


def validate_name(name):
    """
    Validate name parameter for greeting endpoint.

    Args:
        name: Name string from query parameter

    Returns:
        str: Validated name

    Raises:
        ValueError: If name is None, empty, or too long
    """
    if name is None or name == '':
        raise ValueError("Name parameter is required")

    if len(name) > 1000:
        raise ValueError("Name parameter is too long (max 1000 characters)")

    return name


def validate_json_body(request):
    """
    Validate and parse JSON body from request.

    Args:
        request: Flask Request object

    Returns:
        dict: Parsed JSON data

    Raises:
        ValueError: If JSON is invalid or missing
    """
    if not request.is_json:
        raise ValueError("Content-Type must be application/json")

    try:
        data = request.get_json()
    except Exception:
        raise ValueError("Invalid JSON body")

    if data is None or data == {}:
        raise ValueError("Request body cannot be empty")

    return data
