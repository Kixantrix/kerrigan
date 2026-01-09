"""Hello API - Simple REST API service."""

import logging
from flask import Flask, request
from config import load_config
from handlers import health_check, greet, echo


def create_app():
    """
    Application factory function.

    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    config = load_config()

    # Configure logging
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Register routes
    app.add_url_rule('/health', 'health', health_check, methods=['GET'])
    app.add_url_rule('/greet', 'greet', greet, methods=['GET'])
    app.add_url_rule('/echo', 'echo', echo, methods=['POST'])

    # Add request logging
    @app.after_request
    def log_request(response):
        logging.info(f"{request.method} {request.path} -> {response.status_code}")
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {"error": "Method not allowed"}, 405

    return app


def main():
    """Main entry point for running the service."""
    config = load_config()
    app = create_app()

    logging.info(f"Starting Hello API on port {config.PORT}")
    logging.info(f"Environment: {config.ENVIRONMENT}")

    app.run(host='0.0.0.0', port=config.PORT, debug=(config.ENVIRONMENT == 'development'))


if __name__ == '__main__':
    main()
