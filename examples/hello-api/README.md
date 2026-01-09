# Hello API

A simple, well-structured REST API service demonstrating best practices for API development.

## Overview

Hello API is a minimal REST service with three endpoints:
- `/health` - Health check endpoint
- `/greet` - Personalized greeting endpoint
- `/echo` - JSON echo endpoint

Built with Python and Flask as a reference implementation for the Kerrigan agent workflow.

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the service**:
   ```bash
   python app.py
   ```

3. **Test the endpoints**:
   ```bash
   # Health check
   curl http://localhost:5000/health
   
   # Greeting
   curl "http://localhost:5000/greet?name=Alice"
   
   # Echo
   curl -X POST http://localhost:5000/echo \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, World!"}'
   ```

### Docker

1. **Build the image**:
   ```bash
   docker build -t hello-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 5000:5000 hello-api
   ```

3. **Test**:
   ```bash
   curl http://localhost:5000/health
   ```

## API Documentation

### GET /health

Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "ok"
}
```

### GET /greet

Returns a personalized greeting.

**Query Parameters**:
- `name` (required): Name to greet

**Example**:
```bash
curl "http://localhost:5000/greet?name=Alice"
```

**Response**:
```json
{
  "message": "Hello, Alice!"
}
```

**Error Response** (400):
```json
{
  "error": "Name parameter is required"
}
```

### POST /echo

Echoes back the JSON body sent in the request.

**Headers**:
- `Content-Type: application/json` (required)

**Example**:
```bash
curl -X POST http://localhost:5000/echo \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

**Response**:
```json
{
  "key": "value"
}
```

**Error Response** (400):
```json
{
  "error": "Invalid JSON body"
}
```

## Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Port to listen on |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | development | Environment name |

**Example**:
```bash
export PORT=8080
export LOG_LEVEL=DEBUG
python app.py
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Code Quality

```bash
# Linting
flake8 .

# Formatting (if using black)
black --check .
```

## Project Structure

```
hello-api/
├── app.py              # Application entry point
├── handlers.py         # Route handler functions
├── config.py           # Configuration management
├── validators.py       # Request validation
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── .dockerignore       # Docker build exclusions
├── .gitignore          # Git exclusions
├── README.md           # This file
└── tests/              # Test suite
    ├── __init__.py
    ├── conftest.py     # Test fixtures
    ├── test_health.py  # Health endpoint tests
    ├── test_greet.py   # Greet endpoint tests
    └── test_echo.py    # Echo endpoint tests
```

## Documentation

For complete project documentation, see:
- **Specification**: `../../specs/projects/hello-api/spec.md`
- **Architecture**: `../../specs/projects/hello-api/architecture.md`
- **Deployment**: `../../specs/projects/hello-api/runbook.md`
- **Testing**: `../../specs/projects/hello-api/test-plan.md`

## License

MIT (see root LICENSE file)
