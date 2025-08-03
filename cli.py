#!/usr/bin/env python3
"""
ReOrc MCP Client CLI

A command-line interface for working with local model projects.
"""

import os
import sys

# Add the current directory to the Python path to allow imports to work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modular components
from utils.common.cli_parser import create_parser
from utils.file_operations import handle_file_operations
from utils.git_operations import handle_git_operations
from utils.auth_operations import handle_auth_operations
from utils.project_operations import handle_project_operations


def main():
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.operation == "file":
        handle_file_operations(args)
    elif args.operation == "git":
        handle_git_operations(args)
    elif args.operation == "auth":
        handle_auth_operations(args)
    elif args.operation == "project":
        handle_project_operations(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 