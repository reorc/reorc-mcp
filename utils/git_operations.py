import os
import subprocess
from typing import Dict, Optional, Tuple
from utils.common.cli_utils import print_json


def handle_git_operations(args):
    """Handle git operations."""
    if args.command == "status":
        result = GitOperations.get_status(args.project_code)
        print_json(result)
        return None
    elif args.command == "init":
        result = GitOperations.init_repository(args.project_code)
        print_json(result)
        return None
    elif args.command == "commit":
        result = GitOperations.commit_changes(args.project_code, args.message)
        print_json(result)
        return None
    else:
        print(f"Unknown command: {args.command}")
        return None 

class GitOperations:
    """Utilities for managing Git operations for local model projects."""
    
    @staticmethod
    def local_models_root() -> str:
        """Get the base directory for local model projects."""
        return os.path.abspath("./local-model-projects")
    
    @staticmethod
    def run_git_command(command: str, project_code: str) -> Tuple[bool, str]:
        """Run a git command in the project directory.
        
        Args:
            command: Git command to run
            project_code: The project code (e.g., 'dbt_project_1')
            
        Returns:
            tuple: (success, output/error message)
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return False, f"Project directory not found: {project_dir}"
        
        try:
            result = subprocess.run(
                command,
                cwd=project_dir,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, f"Git command failed: {e.stderr}"
    
    @staticmethod
    def init_repository(project_code: str) -> Dict:
        """Initialize a Git repository for the project.
        
        Args:
            project_code: The project code (e.g., 'dbt_project_1')
            
        Returns:
            dict: Dictionary with initialization status or error
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return {"error": f"Project directory not found: {project_dir}"}
        
        if os.path.exists(os.path.join(project_dir, ".git")):
            return {
                "project_code": project_code,
                "status": "info",
                "message": "Git repository already exists"
            }
        
        # Initialize git repository
        success, output = GitOperations.run_git_command("git init", project_code)
        if not success:
            return {"error": output}
        
        # Configure git user
        GitOperations.run_git_command(
            "git config user.email 'reorc-mcp@recurvedata.com'", 
            project_code
        )
        GitOperations.run_git_command(
            "git config user.name 'ReOrc MCP'", 
            project_code
        )
        
        # Add all files and create initial commit
        GitOperations.run_git_command("git add .", project_code)
        success, output = GitOperations.run_git_command(
            "git commit -m 'Initial project state'", 
            project_code
        )
        
        if success:
            return {
                "project_code": project_code,
                "status": "success",
                "message": "Git repository initialized successfully",
                "details": output
            }
        else:
            return {
                "project_code": project_code,
                "status": "warning",
                "message": "Git repository initialized but initial commit failed",
                "details": output
            }
    
    @staticmethod
    def get_status(project_code: str) -> Dict:
        """Get the Git status of the project repository.
        
        Args:
            project_code: The project code (e.g., 'dbt_project_1')
            
        Returns:
            dict: Dictionary with git status information or error
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return {"error": f"Project directory not found: {project_dir}"}
        
        if not os.path.exists(os.path.join(project_dir, ".git")):
            return {
                "error": "Git repository not initialized",
                "status": "not_initialized"
            }
        
        # Get git status in porcelain format for easy parsing
        success, status_output = GitOperations.run_git_command(
            "git status --porcelain", 
            project_code
        )
        
        if not success:
            return {"error": status_output}
        
        # Get current branch
        success, branch_output = GitOperations.run_git_command(
            "git branch --show-current", 
            project_code
        )
        
        branch = branch_output if success else "unknown"
        
        # Parse status output
        modified_files = []
        staged_files = []
        untracked_files = []
        
        for line in status_output.split('\n'):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            if status_code.startswith('??'):
                untracked_files.append(filename)
            elif status_code.startswith('M'):
                modified_files.append(filename)
            elif status_code.startswith('A'):
                staged_files.append(filename)
        
        return {
            "project_code": project_code,
            "branch": branch,
            "modified_files": modified_files,
            "staged_files": staged_files,
            "untracked_files": untracked_files,
            "has_changes": bool(modified_files or staged_files or untracked_files)
        }
    
    @staticmethod
    def commit_changes(
        project_code: str,
        message: str,
        stage_all: bool = True
    ) -> Dict:
        """Commit changes to the Git repository.
        
        Args:
            project_code: The project code (e.g., 'dbt_project_1')
            message: Commit message
            stage_all: Whether to stage all changes before committing
            
        Returns:
            dict: Dictionary with commit status or error
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return {"error": f"Project directory not found: {project_dir}"}
        
        if not os.path.exists(os.path.join(project_dir, ".git")):
            return {"error": "Git repository not initialized"}
        
        # Stage all changes if requested
        if stage_all:
            success, output = GitOperations.run_git_command("git add .", project_code)
            if not success:
                return {"error": f"Failed to stage changes: {output}"}
        
        # Commit changes
        success, output = GitOperations.run_git_command(
            f'git commit -m "{message}"', 
            project_code
        )
        
        if success:
            return {
                "project_code": project_code,
                "status": "success",
                "message": "Changes committed successfully",
                "details": output
            }
        else:
            return {
                "project_code": project_code,
                "status": "error",
                "message": "Commit failed or no changes to commit",
                "details": output
            }
    
    @staticmethod
    def reset_changes(
        project_code: str,
        hard_reset: bool = False,
        file_path: Optional[str] = None
    ) -> Dict:
        """Reset changes in the Git repository.
        
        Args:
            project_code: The project code (e.g., 'dbt_project_1')
            hard_reset: Whether to perform a hard reset (discard all changes)
            file_path: Optional specific file to reset
            
        Returns:
            dict: Dictionary with reset status or error
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return {"error": f"Project directory not found: {project_dir}"}
        
        if not os.path.exists(os.path.join(project_dir, ".git")):
            return {"error": "Git repository not initialized"}
        
        # Reset specific file or all files
        if file_path:
            if hard_reset:
                success, output = GitOperations.run_git_command(
                    f"git checkout HEAD -- {file_path}", 
                    project_code
                )
                reset_type = "hard reset for specific file"
            else:
                success, output = GitOperations.run_git_command(
                    f"git reset -- {file_path}", 
                    project_code
                )
                reset_type = "soft reset for specific file"
        else:
            if hard_reset:
                success, output = GitOperations.run_git_command(
                    "git reset --hard", 
                    project_code
                )
                reset_type = "hard reset (all files)"
            else:
                success, output = GitOperations.run_git_command(
                    "git reset", 
                    project_code
                )
                reset_type = "soft reset (all files)"
        
        if success:
            return {
                "project_code": project_code,
                "status": "success",
                "message": f"Successfully performed {reset_type}",
                "details": output
            }
        else:
            return {
                "project_code": project_code,
                "status": "error",
                "message": f"Reset failed for {reset_type}",
                "details": output
            }
    
    @staticmethod
    def get_history(project_code: str, max_count: int = 10) -> Dict:
        """Get commit history for the Git repository.
        
        Args:
            project_code: The project code (e.g., 'dbt_project_1')
            max_count: Maximum number of commits to return
            
        Returns:
            dict: Dictionary with commit history or error
        """
        project_dir = os.path.join(GitOperations.local_models_root(), project_code)
        
        if not os.path.exists(project_dir):
            return {"error": f"Project directory not found: {project_dir}"}
        
        if not os.path.exists(os.path.join(project_dir, ".git")):
            return {"error": "Git repository not initialized"}
        
        # Get commit history
        success, output = GitOperations.run_git_command(
            f'git log --pretty=format:"%h|%an|%ad|%s" --date=iso --max-count={max_count}',
            project_code
        )
        
        if not success:
            return {"error": output}
        
        # Parse the log output
        commits = []
        for line in output.split('\n'):
            if not line:
                continue
            
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        
        return {
            "project_code": project_code,
            "total_commits": len(commits),
            "commits": commits
        } 