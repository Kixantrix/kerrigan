FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hello_cli/ ./hello_cli/
COPY setup.py .

# Copy README if it exists (optional for installation)
COPY README.md* ./

# Install the package
RUN pip install --no-cache-dir .

# Set the entrypoint
ENTRYPOINT ["hello"]
CMD ["--help"]
