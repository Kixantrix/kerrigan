# Architecture: Hello API

## Overview

Implement a simple REST API service using **Python with Flask framework** for the following reasons:
- Minimal boilerplate for small APIs
- Wide familiarity among developers
- Excellent testing support with pytest
- Easy containerization with standard Python Docker images
- Built-in development server for quick iteration

The service will follow a layered architecture with clear separation of concerns:
1. **HTTP layer**: Route definitions and request/response handling
2. **Handler layer**: Business logic (validation, processing)
3. **Configuration layer**: Environment-based settings
4. **Utilities layer**: Logging and common functions

## Components & interfaces

### 1. Application Entry Point (`app.py`)
- Flask application initialization
- Configuration loading
- Logging setup
- Route registration
- Server startup

**Interfaces**:
- `create_app() -> Flask`: Factory function returning configured Flask app
- `main()`: Entry point for running the service

### 2. Route Handlers (`handlers.py`)
- `health_check()`: Returns service status
- `greet(name: str)`: Returns personalized greeting
- `echo(data: dict)`: Returns received JSON

**Interfaces**:
- All handlers return `(dict, int)` tuple (response body, status code)
- Input validation raises appropriate HTTP exceptions
- All handlers are stateless

### 3. Configuration (`config.py`)
- Port configuration (default: 5000)
- Environment detection (dev/prod)
- Log level configuration

**Interfaces**:
- `Config` class with attributes: `PORT`, `LOG_LEVEL`, `ENVIRONMENT`
- `load_config() -> Config`: Loads from environment variables

### 4. Request Validation (`validators.py`)
- Name parameter validation (non-empty, reasonable length)
- JSON body validation
- Error message generation

**Interfaces**:
- `validate_name(name: Optional[str]) -> str`: Returns validated name or raises ValueError
- `validate_json_body(request: Request) -> dict`: Returns parsed JSON or raises ValueError

### 5. Testing (`tests/`)
- `test_health.py`: Health endpoint tests
- `test_greet.py`: Greeting endpoint tests
- `test_echo.py`: Echo endpoint tests
- `test_integration.py`: Full request/response cycle tests
- `conftest.py`: Pytest fixtures (test client)

## Data Flows

### Flow 1: Health Check
```
Client → GET /health → app.py routes → handlers.health_check() → JSON response → Client
```
No validation needed, always returns success.

### Flow 2: Greeting
```
Client → GET /greet?name=X → app.py routes → validators.validate_name() 
  → handlers.greet() → JSON response → Client
```
If validation fails, returns 400 error immediately.

### Flow 3: Echo
```
Client → POST /echo → app.py routes → validators.validate_json_body()
  → handlers.echo() → JSON response → Client
```
If JSON parsing fails, returns 400 error immediately.

### Flow 4: Error Handling
```
Any request → Flask exception handlers → formatted JSON error → Client
```
All errors return consistent JSON format: `{"error": "message"}`

## Project Structure
```
examples/hello-api/
├── app.py              # Main application entry point
├── handlers.py         # Route handler functions
├── config.py           # Configuration management
├── validators.py       # Request validation logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── README.md           # Setup and usage instructions
├── .gitignore          # Exclude venv, __pycache__, etc.
└── tests/
    ├── __init__.py
    ├── conftest.py     # Pytest fixtures
    ├── test_health.py
    ├── test_greet.py
    ├── test_echo.py
    └── test_integration.py
```

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: Flask 3.0+
- **Testing**: pytest, pytest-flask
- **WSGI Server**: Built-in development server (development), gunicorn (production)
- **Containerization**: Docker with python:3.11-slim base image
- **Dependencies**: Minimal (Flask, pytest, gunicorn)

## Tradeoffs

### Why Flask over FastAPI?
- **Pro Flask**: Simpler for this scope, less boilerplate, more familiar to broader audience
- **Con Flask**: No automatic API documentation, no type validation via Pydantic
- **Decision**: Flask is sufficient for this example; FastAPI would be overkill

### Why Python over Go/Node?
- **Pro Python**: Faster to write, excellent testing ecosystem, clear for examples
- **Con Python**: Slower startup time, larger container images than Go
- **Decision**: Python's clarity and accessibility outweigh performance for this example

### Validation approach (custom vs. library)
- **Pro custom**: No extra dependencies, clear control, easy to understand
- **Con custom**: Less robust than marshmallow/pydantic
- **Decision**: Custom validation for this simple case; keeps example focused

### Synchronous vs. Async
- **Pro sync**: Simpler code, easier to understand, sufficient for example
- **Con sync**: Not optimal for I/O-bound workloads
- **Decision**: Synchronous Flask; async would complicate the example unnecessarily

## Security & privacy notes

- **Input validation**: All user inputs validated to prevent injection attacks
- **Error handling**: No stack traces or sensitive info exposed in production errors
- **Dependencies**: Pin exact versions in requirements.txt; scan for CVEs in CI
- **Container**: Run as non-root user in Docker container
- **CORS**: Not enabled by default; can be added if needed
- **Rate limiting**: Not implemented (out of scope for example)
- **Secrets**: No secrets in this stateless API; document pattern in runbook

## Scalability Considerations

For this example:
- Stateless design enables horizontal scaling
- No database means no connection pool management
- Each request is independent and can be load-balanced
- Docker containerization enables easy deployment to orchestration platforms

Limitations (acceptable for example):
- Built-in Flask dev server is single-threaded (use gunicorn for production)
- No caching layer (not needed for this scope)
- No circuit breakers or retries (no external dependencies)

## Monitoring & Observability

- **Logging**: Structured logs to stdout (JSON format for production)
- **Metrics**: Not implemented (out of scope)
- **Tracing**: Not implemented (out of scope)
- **Health check**: `/health` endpoint for container orchestration platforms

## Rollout Strategy

Single milestone deployment:
1. Implement all endpoints
2. Add tests
3. Add Dockerfile
4. Document in README
5. Verify CI passes
6. Merge to main

No phased rollout needed for this example.
