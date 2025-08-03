import os
import json
import re
from utils.common.cli_utils import http_get, http_post
from utils.common.cli_utils import get_auth_config


def handle_auth_operations(args):
    """Handle authentication operations."""
    server_url, base_url, token, server_config, config = get_auth_config()
    if not server_url:
        return None
    
    if args.command == "validate":
        # Call the server to validate token
        validate_url = f"{base_url}/mcp/auth/validate-token?access_token={token}"
        
        try:
            response = http_get(validate_url)
            if response.get("valid"):
                print("Token validation successful")
                return True
            else:
                print("Token validation failed")
                return False
        except Exception as e:
            print(f"Token validation failed: {str(e)}")
            return False
    
    elif args.command == "login":
        # Login to get a new token
        login_url = f"{base_url}/mcp/auth/login"

        print(f"login_url: {login_url}")
        
        # Use provided credentials or default credentials from config
        auth_config = config.get("auth", {})
        default_credentials = auth_config.get("defaultCredentials", {})
        
        email = args.email or default_credentials.get("email") or input("Email: ")
        password = args.password or default_credentials.get("password") or input("Password: ")
        tenant = args.tenant or default_credentials.get("tenant_domain") or input("Tenant domain: ")
        
        payload = {
            "email": email,
            "password": password,
            "tenant_domain": tenant
        }
        
        try:
            response = http_post(login_url, payload)
            if "access_token" in response:
                new_token = response["access_token"]
                
                # Update token in server URL
                new_url = re.sub(r"access_token=[^&]+", f"access_token={new_token}", server_url)
                server_config["url"] = new_url
                
                # Save updated config
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cursor", "mcp.json")
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)
                
                print("Login successful, token updated")
                return True
            else:
                print(f"Login failed: {response.get('detail', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Login failed exception: {str(e)}")
            return False
    
    else:
        print(f"Unknown command: {args.command}")
        return False 