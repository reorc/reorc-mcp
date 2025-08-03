import argparse


def create_parser():
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(description="ReOrc MCP Client CLI")
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")
    
    # File operations
    file_parser = subparsers.add_parser("file", help="File operations")
    file_subparsers = file_parser.add_subparsers(dest="command", help="File command")
    
    # file list
    file_list_parser = file_subparsers.add_parser("list", help="List files")
    file_list_parser.add_argument("project_code", help="Project code")
    file_list_parser.add_argument("--path", help="Path to list (default: root)", default="")
    
    # file read
    file_read_parser = file_subparsers.add_parser("read", help="Read file")
    file_read_parser.add_argument("project_code", help="Project code")
    file_read_parser.add_argument("file_path", help="File path")
    
    # file write
    file_write_parser = file_subparsers.add_parser("write", help="Write file")
    file_write_parser.add_argument("project_code", help="Project code")
    file_write_parser.add_argument("file_path", help="File path")
    file_write_parser.add_argument("--content", help="File content")
    file_write_parser.add_argument("--file", help="Read content from file")
    
    # Git operations
    git_parser = subparsers.add_parser("git", help="Git operations")
    git_subparsers = git_parser.add_subparsers(dest="command", help="Git command")
    
    # git status
    git_status_parser = git_subparsers.add_parser("status", help="Get git status")
    git_status_parser.add_argument("project_code", help="Project code")
    
    # git init
    git_init_parser = git_subparsers.add_parser("init", help="Initialize git repository")
    git_init_parser.add_argument("project_code", help="Project code")
    
    # git commit
    git_commit_parser = git_subparsers.add_parser("commit", help="Commit changes")
    git_commit_parser.add_argument("project_code", help="Project code")
    git_commit_parser.add_argument("message", help="Commit message")
    
    # Auth operations
    auth_parser = subparsers.add_parser("auth", help="Authentication operations")
    auth_subparsers = auth_parser.add_subparsers(dest="command", help="Auth command")
    
    # auth validate
    auth_validate_parser = auth_subparsers.add_parser("validate", help="Validate token")
    
    # auth login
    auth_login_parser = auth_subparsers.add_parser("login", help="Login to get a new token")
    auth_login_parser.add_argument("--email", help="Email")
    auth_login_parser.add_argument("--password", help="Password")
    auth_login_parser.add_argument("--tenant", help="Tenant domain")
    
    # Project operations
    project_parser = subparsers.add_parser("project", help="Project operations")
    project_subparsers = project_parser.add_subparsers(dest="command", help="Project command")
    
    # project commit
    project_commit_parser = project_subparsers.add_parser("commit", help="Commit local changes to git")
    project_commit_parser.add_argument("project_code", help="Project code")
    project_commit_parser.add_argument("--models", help="Comma-separated list of models to commit")
    project_commit_parser.add_argument("--message", "-m", help="Commit message")
    project_commit_parser.add_argument("--auto-commit", metavar="MESSAGE", nargs="?", const="auto", 
                                      help="Auto-generate commit message (use 'auto' for timestamp-based message)")
    
    # project download
    project_download_parser = project_subparsers.add_parser("download", help="Download dbt project from server")
    project_download_parser.add_argument("project_code", help="Project code")

    # project download-semantic-project
    project_download_semantic_parser = project_subparsers.add_parser("download-semantic-project", help="Download semantic project from server")
    project_download_semantic_parser.add_argument("project_code", help="Project code")

    # project list-sources
    project_list_sources_parser = project_subparsers.add_parser("list-sources", help="List all sources")
    project_list_sources_parser.add_argument("project_code", help="Project code")

    # project refresh-sources
    project_refresh_sources_parser = project_subparsers.add_parser("refresh-sources", help="Refresh sources")
    project_refresh_sources_parser.add_argument("project_code", help="Project code")
    
    

    
    return parser 