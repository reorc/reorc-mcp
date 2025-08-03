import json
import os
import shutil
import tarfile
import time

from utils.common.cli_utils import http_get
from utils.common.cli_utils import print_json, get_auth_config
from utils.file_operations import FileOperations
from utils.git_operations import GitOperations


def handle_project_operations(args):
    """Handle project operations."""
    _, base_url, token, _, _ = get_auth_config()
    if not token:
        print("No token found")
        return None
    
    if args.command == "list-sources":
        # List all projects via API @app.get("/mcp/projects/{project_code}/list-sources")
        list_sources_url = f"{base_url}/mcp/projects/{args.project_code}/list-sources"
        headers = {"Authorization": f"Bearer {token}"}
        sources_response = http_get(list_sources_url, headers)
        # print_json(sources_response)


        # check if local-source-databases/<project_code> dir exists
        source_raw_databases_path = os.path.join("local-source-databases", args.project_code)
        if not os.path.exists(source_raw_databases_path):
            os.makedirs(source_raw_databases_path)

        cached_sources_file = os.path.join(source_raw_databases_path, f"{args.project_code}_raw_sources.json")
        clear_cache = False
        if os.path.exists(cached_sources_file):
            # check if the file is updated within 1 day
            file_mtime = os.path.getmtime(cached_sources_file)
            if file_mtime > time.time() - 86400:
                print(f"Raw sources json file for project {args.project_code} is updated within 1 day")
                with open(cached_sources_file, "r") as f:
                    cached_response = json.load(f)
                
                # Check if cached response is valid and has the expected structure
                if (isinstance(cached_response, list) and len(cached_response) > 0):
                    return cached_response
                else:
                    print(f"Raw sources json file for project {args.project_code} is not valid or has wrong format")
                    print_json(cached_response)
                    clear_cache = True
            else:
                print(f"Raw sources json file for project {args.project_code} is older than 1 day")
                clear_cache = True
        else:
            print(f"Raw sources json file for project {args.project_code} does not exist")
            clear_cache = True

        if clear_cache:
            # delete everything in local-source-databases/<project_code>
            for file in os.listdir(source_raw_databases_path):
                os.remove(os.path.join(source_raw_databases_path, file))
            print(f"Deleted everything in {source_raw_databases_path}")

        # Cache the response as JSON
        with open(cached_sources_file, "w") as f:
            json.dump(sources_response, f, indent=2)
        
        # Parse and cache databases as individual YAML files
        # Handle case where sources_response might be a list instead of dict
        if isinstance(sources_response, list):
            # If sources_response is directly a list of databases
            databases = sources_response
        else:
            print(f"Unexpected response format: {type(sources_response)}")
            return None
        
        # Import yaml module
        import yaml
        
        for database in databases:
            database_name = database.get("database_name")
            schema_name = database.get("schema_name")

            if schema_name is None:
                # Use database name as filename
                yaml_filename = f"{database_name}.yaml"
            else:
                # Use database name and schema name as filename
                yaml_filename = f"{database_name}_{schema_name}.yaml"
            
            yaml_file_path = os.path.join(source_raw_databases_path, yaml_filename)
            
            # Structure data for YAML
            yaml_data = {
                "database_name": database_name,
                "schema_name": database.get("schema_name"),
                "connection_id": database.get("connection_id"),
                "status": database.get("status"),
                "tables": []
            }
            
            # Add tables information
            for table in database.get("tables", []):
                table_data = {
                    "id": table.get("id"),
                    "name": table.get("table_name"),
                    "source_type": table.get("source_type", "table"),
                    "status": table.get("status"),
                    "columns": []
                }
                for column in table.get("columns", []):
                    table_data["columns"].append({
                        "name": column.get("name"),
                        "type": column.get("type"),
                        "normalized_type": column.get("normalized_type"),
                        "comment": column.get("comment")
                    })
                yaml_data["tables"].append(table_data)

            # Write YAML file
            with open(yaml_file_path, "w") as yaml_file:
                yaml.dump(yaml_data, yaml_file, default_flow_style=False, sort_keys=False)
            
            print(f"Created YAML cache file: {yaml_file_path}")
        
        print(f"Cached {len(databases)} databases as YAML files in {source_raw_databases_path}")

        return sources_response
    
    elif args.command == "refresh-sources":
        # Refresh all database sources and tables
        project_code = args.project_code
        print(f"Refreshing sources for project: {project_code}")
        
        # Call the refresh sources endpoint
        refresh_url = f"{base_url}/mcp/projects/{project_code}/refresh-sources"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Initiate refresh operation
            response = http_get(refresh_url, headers)
            
            if "error" in response:
                print(f"Error refreshing sources: {response['error']}")
                return None
                
            task_id = response.get("task_id")
            status = response.get("status")
            
            if not task_id:
                print("No task ID returned from server")
                return None
                
            print(f"Sources refresh initiated successfully with task ID: {task_id}")
            print(f"Initial status: {status}")
            
            # Poll for task completion
            poll_url = f"{base_url}/mcp/tasks/{task_id}/status"
            poll_interval = 2
            poll_timeout = 60
            complete_statuses = response.get("instructions", {}).get("complete_statuses", ["completed", "failed", "error"])
            
            print(f"Polling for task {task_id} completion every {poll_interval} second(s) with timeout of {poll_timeout} second(s)...")
            
            # Start polling
            start_time = time.time()
            while time.time() - start_time < poll_timeout:
                try:
                    poll_response = http_get(poll_url, headers)
                    
                    current_status = poll_response.get("status")
                    print(f"Current status: {current_status}")
                    
                    if current_status in complete_statuses:
                        if current_status == "success":
                            print("Sources refresh completed successfully!")
                            print_json(poll_response)
                            return poll_response
                        else:
                            print(f"Sources refresh failed with status: {current_status}")
                            if "error" in poll_response:
                                print(f"Error: {poll_response['error']}")
                            return poll_response
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    print(f"Error polling task status: {str(e)}")
                    return None
                    
            print(f"Polling timed out after {poll_timeout} seconds. The refresh operation may still be in progress.")
            return {"status": "timeout", "message": "Polling timed out, but the refresh operation may still be in progress"}
            
        except Exception as e:
            print(f"Error refreshing sources: {str(e)}")
            return None
    
    elif args.command == "commit":
        # Commit local changes to git
        local_project_path = os.path.join("local-model-projects", args.project_code)
        
        # Check if project directory exists
        if not os.path.exists(local_project_path):
            print(f"Project directory {local_project_path} not found")
            return None
            
        # Get git status to find modified files
        git_status = GitOperations.get_status(args.project_code)
        modified_paths = []
        
        for filename in git_status.get("modified_files", []):
            if filename.endswith(".sql"):
                modified_paths.append(filename)
                
        if not modified_paths:
            print("No modified SQL models found")
            return None
            
        # Read content of modified files to get model names
        modified_files = []
        for file_path in modified_paths:
            full_path = os.path.join(local_project_path, file_path)
            if os.path.exists(full_path):
                model_name = os.path.splitext(os.path.basename(file_path))[0]
                modified_files.append({
                    "name": model_name,
                    "path": file_path
                })
        
        # Filter models if specified
        if hasattr(args, 'models') and args.models:
            model_list = args.models.split(",")
            modified_files = [f for f in modified_files if f["name"] in model_list]
            
        if not modified_files:
            print("No modified SQL models found matching the criteria")
            return None
            
        # Show what will be committed
        print(f"Modified files to commit:")
        for file in modified_files:
            print(f"  - {file['path']}")

        # Handle commit message
        commit_message = None
        if hasattr(args, 'message') and args.message:
            commit_message = args.message
        elif hasattr(args, 'auto_commit') and args.auto_commit:
            if args.auto_commit == "auto":
                # Generate a default commit message
                models_list = ", ".join([f["name"] for f in modified_files])
                commit_message = f"Update models ({models_list}) - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                commit_message = args.auto_commit
        else:
            # Prompt for commit message
            commit_message = input("Enter commit message: ").strip()
            if not commit_message:
                print("Commit cancelled - no message provided")
                return None

        try:
            commit_result = GitOperations.commit_changes(args.project_code, commit_message)
            if commit_result.get("success"):
                print(f"Successfully committed changes: {commit_message}")
                return commit_result
            else:
                print(f"Failed to commit changes: {commit_result.get('error')}")
                return commit_result
        except Exception as e:
            print(f"Error during commit: {str(e)}")
            return None

    elif args.command == "download":
        download_model_project_result = FileOperations.download_dbt_project(args.project_code, base_url, token)
        print_json(download_model_project_result)
        return None
    
    elif args.command == "download-semantic-project":
        """
        Use cases:
        - Fetch semantic project from server
        - Refresh semantic project
        """
        # Sync semantic project to server
        print(f"Fetching semantic project: {args.project_code}")

        # Step 1: Call download semantic project
        download_result = FileOperations.download_semantic_project(args.project_code, base_url, token)

        # Step 2.1: Check if download failed
        if not download_result or "error" in download_result:
            error_msg = download_result.get("error", "Unknown error occurred during download") if download_result else "Download failed"
            print(f"Error downloading semantic project: {error_msg}")
            return {"error": error_msg}

        # Step 2.2: If success, process the downloaded file
        try:
            # Determine the path to the downloaded tar.gz file
            semantic_project_path = FileOperations.local_semantic_root()
            semantic_project_code_path = os.path.join(semantic_project_path, args.project_code)
            # Remove semantic_project_code_path if it exists
            print(f"Cleaning up semantic project path: {semantic_project_code_path}")
            if os.path.exists(semantic_project_code_path):
                shutil.rmtree(semantic_project_code_path, ignore_errors=True)

            # Create tar.gz file path
            tar_file_path = os.path.join(semantic_project_path, f"{args.project_code}_semantic.tar.gz")

            # Check if the tar.gz file exists
            if not os.path.exists(tar_file_path):
                error_msg = f"Downloaded file not found: {tar_file_path}"
                print(error_msg)
                return {"error": error_msg}

            print(f"Extracting semantic project from: {tar_file_path}")

            # Extract the tar.gz file
            with tarfile.open(tar_file_path, "r:gz") as tar:
                # Extract all contents, overriding existing files
                tar.extractall(path=semantic_project_path)

            print(f"Successfully extracted semantic project to: {semantic_project_path}")

            # Clean up the tar.gz file after successful extraction
            os.remove(tar_file_path)
            print(f"Cleaned up downloaded file: {tar_file_path}")

            return {
                "success": True,
                "message": f"Successfully synced semantic project {args.project_code}",
                "extracted_to": semantic_project_path
            }

        except tarfile.TarError as e:
            error_msg = f"Error extracting tar.gz file: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
        except OSError as e:
            error_msg = f"Error setting file permissions: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during sync: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
    else:
        print(f"Unknown command: {args.command}")
        return None 