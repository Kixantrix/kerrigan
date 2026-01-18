"""
Hello Multi-App API

A simple FastAPI application demonstrating multi-repo coordination.
Provides health and version endpoints for the frontend to consume.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hello Multi-App API",
    description="API service for multi-repo coordination example",
    version="1.0.0"
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    logger.info("Health check requested")
    return {
        "status": "ok",
        "service": "hello-multiapp-api"
    }


@app.get("/version")
async def version():
    """Returns version information about the API."""
    logger.info("Version requested")
    return {
        "version": "1.0.0",
        "service": "hello-multiapp-api",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "message": "Hello Multi-App API",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting Hello Multi-App API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
