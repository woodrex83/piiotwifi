#!/usr/bin/env python3
"""
IOT WiFi Management - Python version with Bottle API server.
Manages WiFi AP and Station modes on Raspberry Pi.
"""
import json
import logging
import os
import sys
from typing import Dict, Any

from bottle import Bottle, request, response, run, abort
from pydantic import ValidationError

from models import (
    ApiResponse, WpaCredentials, WpaConnection, SetupConfig
)
from wifi_manager import WiFiManager
from utils import setup_logging


# Global variables
wifi_manager: WiFiManager = None
logger: logging.Logger = None
app = Bottle()


def load_config(config_path: str) -> SetupConfig:
    """Load configuration from JSON file or URL."""
    try:
        if config_path.startswith(('http://', 'https://')):
            import urllib.request
            with urllib.request.urlopen(config_path) as response:
                config_data = json.loads(response.read().decode())
        else:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        
        return SetupConfig(**config_data)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def json_response(data: ApiResponse) -> str:
    """Return JSON response with proper headers."""
    response.content_type = 'application/json'
    return data.json()


def error_response(message: str, status_code: int = 500) -> str:
    """Return error response."""
    response.status = status_code
    error_resp = ApiResponse(status="FAIL", message=message)
    return json_response(error_resp)


@app.route('/status', method='GET')
def get_status():
    """Get WiFi connection status."""
    try:
        status_data = wifi_manager.get_status()
        api_resp = ApiResponse(
            status="OK",
            message="status",
            payload=status_data
        )
        return json_response(api_resp)
    except Exception as e:
        logger.error(f"Status error: {e}")
        return error_response(str(e))


@app.route('/connect', method='POST')
def connect_network():
    """Connect to a WiFi network."""
    try:
        # Parse request body
        try:
            data = request.json
            if not data:
                raise ValueError("No JSON data provided")
            credentials = WpaCredentials(**data)
        except ValidationError as e:
            return error_response(f"Invalid credentials: {e}", 400)
        except Exception as e:
            return error_response(f"Failed to parse request: {e}", 400)

        logger.info(f"Connect request for SSID: {credentials.ssid}")

        # Attempt connection
        connection = wifi_manager.connect_network(credentials)
        
        api_resp = ApiResponse(
            status="OK",
            message="Connection",
            payload=connection.dict()
        )
        return json_response(api_resp)

    except Exception as e:
        logger.error(f"Connection error: {e}")
        return error_response(str(e))


@app.error(404)
def error404(error):
    """Handle 404 errors."""
    return error_response("Endpoint not found", 404)


@app.error(500)
def error500(error):
    """Handle 500 errors."""
    return error_response("Internal server error", 500)


def setup_cors():
    """Setup CORS headers for all responses."""
    @app.hook('after_request')
    def enable_cors():
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Content-Length, X-Requested-With, Accept, Origin'

    @app.route('/<path:path>', method='OPTIONS')
    def options_handler(path=None):
        return {}


def main():
    """Main application entry point."""
    global wifi_manager, logger
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting IOT WiFi Python version...")
    
    # Get configuration
    config_path = os.getenv('IOTWIFI_CFG', '/cfg/wificfg.json')
    port = int(os.getenv('IOTWIFI_PORT', '8080'))
    
    try:
        # Load configuration
        setup_cfg = load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
        
        # Initialize WiFi manager
        wifi_manager = WiFiManager(setup_cfg, logger)
        
        # Start WiFi services in background
        wifi_manager.start_services()
        
        # Setup CORS
        setup_cors()
        
        # Start HTTP server
        logger.info(f"Starting HTTP server on port {port}")
        run(app, host='0.0.0.0', port=port, debug=False, quiet=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if wifi_manager:
            wifi_manager.cleanup()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
