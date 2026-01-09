# Acceptance Tests: Hello API

This document defines the acceptance tests for the Hello API project in human-readable format.

## Test Scenarios

### 1. Health Check Endpoint

**Scenario: Service health check returns success**
- **Given**: The API service is running
- **When**: I send GET request to /health
- **Then**: I receive HTTP 200 status code
- **And**: Response body contains `{"status": "ok"}`
- **And**: Response Content-Type is "application/json"

**Scenario: Health check works without authentication**
- **Given**: The API service is running
- **When**: I send GET request to /health without any authentication
- **Then**: I receive HTTP 200 status code

### 2. Greeting Endpoint

**Scenario: Greet user with provided name**
- **Given**: The API service is running
- **When**: I send GET request to /greet?name=Alice
- **Then**: I receive HTTP 200 status code
- **And**: Response body contains `{"message": "Hello, Alice!"}`

**Scenario: Greet with special characters in name**
- **Given**: The API service is running
- **When**: I send GET request to /greet?name=José
- **Then**: I receive HTTP 200 status code
- **And**: Response body contains `{"message": "Hello, José!"}`

**Scenario: Greet without name parameter**
- **Given**: The API service is running
- **When**: I send GET request to /greet without name parameter
- **Then**: I receive HTTP 400 status code
- **And**: Response body contains error message explaining missing parameter

**Scenario: Greet with empty name**
- **Given**: The API service is running
- **When**: I send GET request to /greet?name=
- **Then**: I receive HTTP 400 status code
- **And**: Response body contains error message

### 3. Echo Endpoint

**Scenario: Echo simple JSON object**
- **Given**: The API service is running
- **When**: I send POST request to /echo with body `{"test": "value"}`
- **Then**: I receive HTTP 200 status code
- **And**: Response body is `{"test": "value"}`

**Scenario: Echo nested JSON object**
- **Given**: The API service is running
- **When**: I send POST request to /echo with body `{"user": {"name": "Alice", "age": 30}}`
- **Then**: I receive HTTP 200 status code
- **And**: Response body is `{"user": {"name": "Alice", "age": 30}}`

**Scenario: Echo with invalid JSON**
- **Given**: The API service is running
- **When**: I send POST request to /echo with malformed JSON body
- **Then**: I receive HTTP 400 status code
- **And**: Response body contains error message about invalid JSON

**Scenario: Echo with empty body**
- **Given**: The API service is running
- **When**: I send POST request to /echo with empty body
- **Then**: I receive HTTP 400 status code
- **And**: Response body contains error message

### 4. Error Handling

**Scenario: Request to non-existent endpoint**
- **Given**: The API service is running
- **When**: I send GET request to /nonexistent
- **Then**: I receive HTTP 404 status code
- **And**: Response contains error message

**Scenario: Unsupported HTTP method**
- **Given**: The API service is running
- **When**: I send POST request to /health (which only supports GET)
- **Then**: I receive HTTP 405 status code
- **And**: Response contains "Method Not Allowed" message

### 5. Configuration

**Scenario: Service starts on custom port**
- **Given**: Environment variable PORT is set to 8080
- **When**: I start the API service
- **Then**: Service listens on port 8080
- **And**: Health check succeeds at http://localhost:8080/health

**Scenario: Service starts with default port**
- **Given**: No PORT environment variable is set
- **When**: I start the API service
- **Then**: Service listens on default port (e.g., 5000 or 3000)
- **And**: Health check succeeds

### 6. Logging

**Scenario: Request logging**
- **Given**: The API service is running with INFO log level
- **When**: I send any request to the API
- **Then**: A log entry is written containing:
  - HTTP method
  - Request path
  - Response status code
  - Timestamp

### 7. Containerization

**Scenario: Docker build succeeds**
- **Given**: Dockerfile exists in project root
- **When**: I run `docker build -t hello-api .`
- **Then**: Build completes successfully with exit code 0
- **And**: Docker image hello-api is created

**Scenario: Service runs in Docker container**
- **Given**: Docker image hello-api exists
- **When**: I run `docker run -p 5000:5000 hello-api`
- **Then**: Container starts successfully
- **And**: Health check succeeds at http://localhost:5000/health

## Edge Cases & Failure Modes

### Edge Cases
1. **Very long names** (> 1000 characters) should be handled gracefully
2. **Unicode characters** in all fields should work correctly
3. **Large JSON payloads** (up to reasonable limit) should echo correctly
4. **Concurrent requests** should not interfere with each other

### Failure Modes
1. **Service crash**: If service crashes, container should exit with non-zero code
2. **Out of memory**: Service should handle gracefully or fail fast
3. **Port already in use**: Service should report clear error message
4. **Missing dependencies**: Build should fail with clear error messages

## Manual Verification Checklist

Before marking this project complete, manually verify:

- [ ] Run `curl http://localhost:PORT/health` and see valid JSON response
- [ ] Run `curl "http://localhost:PORT/greet?name=TestUser"` and see greeting
- [ ] Run `curl -X POST http://localhost:PORT/echo -H "Content-Type: application/json" -d '{"test":"data"}'` and see echo
- [ ] Check logs show request information
- [ ] Build and run Docker container successfully
- [ ] Run automated test suite and see all tests pass
- [ ] Run linter and see no errors
- [ ] CI pipeline is green
