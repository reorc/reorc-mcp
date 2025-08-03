#!/usr/bin/env python3
"""
ReOrc MCP Client CLI Utilities

Shared utility functions for the CLI.
"""

import os
import json
import re
import subprocess
import time
from typing import Dict, Any, Optional, Tuple


def print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))


def extract_base_url(server_url: str) -> str:
    """
    Extract the base URL from a server URL by removing the '/mcp?' path and query parameters.
    
    Args:
        server_url: The full server URL
        
    Returns:
        The base URL without '/mcp?' and query parameters
    """
    return server_url.split("/mcp?")[0].rstrip("/")


def extract_token_from_url(url: str) -> Optional[str]:
    """
    Extract access token from MCP server URL.
    
    Args:
        url: The full server URL containing an access_token parameter
        
    Returns:
        The extracted token or None if not found
    """
    match = re.search(r"access_token=([^&]+)", url)
    if match:
        return match.group(1)
    return None


def get_mcp_config() -> Optional[Dict[str, Any]]:
    """
    Get MCP server configuration from .cursor/mcp.json.
    
    Returns:
        The config dictionary or None if not found or error
    """
    # Look for mcp.json in project root directory
    # The file structure is: project_root/utils/common/cli_utils.py, so we need to go up two levels
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, ".cursor", "mcp.json")
    
    if not os.path.exists(config_path):
        print(f"Config file not found at {config_path}")
        return None
        
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"Error loading MCP config: {e}")
        return None


def get_auth_config() -> tuple:
    """
    Get the server URL, base URL, and access token from MCP configuration.
    
    Returns:
        A tuple of (server_url, base_url, token, server_config, config) or (None, None, None, None, None) if error
    """
    config = get_mcp_config()
    if not config:
        print("Error: MCP server configuration not found. Please check .cursor/mcp.json")
        return None, None, None, None, None

    # Extract server configuration
    server_config = next(iter(config.get("mcpServers", {}).values()), None)
    if not server_config:
        print("Error: No MCP server configuration found in .cursor/mcp.json")
        return None, None, None, None, None

    server_url = server_config.get("url", "")
    base_url = extract_base_url(server_url)
    token = extract_token_from_url(server_url)
    
    if not token:
        print("Error: No access token found in MCP server URL")
        return None, None, None, None, None
        
    return server_url, base_url, token, server_config, config 


def run_curl_command(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 60,  # Increased from 30 to 60 seconds
    retries: int = 3,   # Add retry functionality
    retry_delay: int = 2  # Seconds to wait between retries
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Execute an HTTP request using curl command-line tool.
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dictionary
        params: Optional query parameters
        data: Optional JSON data for request body
        timeout: Request timeout in seconds
        retries: Number of times to retry on failure
        retry_delay: Seconds to wait between retries
        
    Returns:
        tuple: (success, response_json, response_text)
    """
    # Build curl command
    cmd = ["curl", "-s", "-X", method]
    
    # Add timeout with increased values
    cmd.extend(["--connect-timeout", "30"])  # Connection timeout
    cmd.extend(["--max-time", str(timeout)])  # Total operation timeout
    
    # Add headers
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    else:
        # Always set Accept header for JSON
        cmd.extend(["-H", "Accept: application/json"])
    
    # Add JSON data if provided
    if data:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(data)])
    
    # Add query parameters to URL if provided
    if params:
        param_strings = []
        for key, value in params.items():
            param_strings.append(f"{key}={value}")
        
        if "?" in url:
            url = f"{url}&{'&'.join(param_strings)}"
        else:
            url = f"{url}?{'&'.join(param_strings)}"
    
    cmd.append(url)
    
    # Add retry logic
    attempt = 0
    last_error = None
    
    while attempt < retries:
        try:
            # Run curl command
            result = subprocess.run(
                cmd,
                check=False,  # Don't raise exception on non-zero exit
                capture_output=True,
                text=True
            )
            
            # Check if command succeeded
            success = result.returncode == 0
            output = result.stdout
            
            # If successful or not a transient error, return immediately
            if success or "Connection refused" not in result.stderr:
                # Try to parse JSON response
                response_json = {}
                if output:
                    try:
                        response_json = json.loads(output)
                    except json.JSONDecodeError:
                        # Not a JSON response
                        pass
                
                return success, response_json, output
            
            # If we got here, it's a connection error that might be transient
            last_error = result.stderr
            
        except Exception as e:
            last_error = str(e)
        
        # Increment attempt count and delay before retry
        attempt += 1
        if attempt < retries:
            print(f"Connection failed. Retrying in {retry_delay} seconds... ({attempt}/{retries})")
            time.sleep(retry_delay)
    
    # If we got here, all retries failed
    return False, {"error": str(last_error)}, str(last_error)


def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
    retries: int = 3
) -> Dict[str, Any]:
    """
    Perform an HTTP GET request using curl.
    
    Args:
        url: The URL to request
        headers: Optional headers dictionary
        params: Optional query parameters
        timeout: Request timeout in seconds
        retries: Number of times to retry on failure
        
    Returns:
        dict: Response data or error
    """
    success, response_json, output = run_curl_command(
        url=url,
        method="GET",
        headers=headers,
        params=params,
        timeout=timeout,
        retries=retries
    )
    
    if success:
        return response_json if response_json else {"data": output}
    else:
        return {"error": output or "Request failed"}


def http_post(
    url: str,
    data: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 120,  # Increased for large uploads
    retries: int = 3
) -> Dict[str, Any]:
    """
    Perform an HTTP POST request using curl.
    
    Args:
        url: The URL to request
        data: JSON data for request body
        headers: Optional headers dictionary
        params: Optional query parameters
        timeout: Request timeout in seconds
        retries: Number of times to retry on failure
        
    Returns:
        dict: Response data or error
    """
    success, response_json, output = run_curl_command(
        url=url,
        method="POST",
        headers=headers,
        params=params,
        data=data,
        timeout=timeout,
        retries=retries
    )
    
    if success:
        return response_json if response_json else {"data": output}
    else:
        return {"error": output or "Request failed"} 