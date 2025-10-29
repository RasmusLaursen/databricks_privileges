"""
GitHub integration module for detecting service requests in pull requests.

This module provides functionality to identify service request files that are part
of the current pull request and parse them accordingly.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from privileges.logger import logging_helper
from privileges.service_requests.parser import ServiceRequest, ServiceRequestParser

logger = logging_helper.get_logger(__name__)


class GitHubIntegration:
    """Integration class for GitHub operations and PR detection."""

    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize GitHub integration.
        
        Args:
            repo_root: Root directory of the git repository. If None, uses current directory.
        """
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.service_request_parser = ServiceRequestParser()

    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """
        Get list of files changed in the current branch compared to base branch.
        
        Args:
            base_branch: The base branch to compare against (default: "main")
            
        Returns:
            List of changed file paths relative to repo root
            
        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        try:
            # Get files changed between base branch and current HEAD
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return changed_files
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get changed files: {e}")
            logger.error(f"Git error output: {e.stderr}")
            raise

    def get_changed_files_from_env(self) -> List[str]:
        """
        Get changed files from GitHub Actions environment variables.
        
        This method is useful when running in GitHub Actions where we can use
        environment variables to get the changed files.
        
        Returns:
            List of changed file paths, empty list if not in GitHub Actions
        """
        changed_files = []
        
        # Try to get files from GitHub Actions environment
        if os.getenv("GITHUB_ACTIONS"):
            # In GitHub Actions, we can use the GitHub API or git commands
            base_sha = os.getenv("GITHUB_BASE_REF", "main")
            
            try:
                changed_files = self.get_changed_files(base_sha)
            except subprocess.CalledProcessError:
                logger.warning("Failed to get changed files from git, falling back to empty list")
                
        return changed_files

    def filter_service_request_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter file paths to only include service request files.
        
        Args:
            file_paths: List of file paths to filter
            
        Returns:
            List of service request file paths (YAML files in service_requests directories)
        """
        service_request_files = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            # Check if file is in service_requests directory and is YAML
            if (
                "service_requests" in path.parts and
                path.suffix.lower() in [".yml", ".yaml"] and
                path.exists() and
                path.is_file()
            ):
                service_request_files.append(file_path)
        
        return service_request_files

    def get_pr_service_requests(self, base_branch: str = "main") -> List[ServiceRequest]:
        """
        Get all service requests that are part of the current pull request.
        
        Args:
            base_branch: The base branch to compare against (default: "main")
            
        Returns:
            List of parsed ServiceRequest objects from files changed in the PR
            
        Raises:
            Exception: If unable to parse service request files
        """
        try:
            # First try to get changed files from environment (GitHub Actions)
            changed_files = self.get_changed_files_from_env()
            
            # If not in GitHub Actions or no files found, use git directly
            if not changed_files:
                changed_files = self.get_changed_files(base_branch)
            
            # Filter to only service request files
            service_request_files = self.filter_service_request_files(changed_files)
            
            if not service_request_files:
                return []
            
            # Parse each service request file
            service_requests = []
            for file_path in service_request_files:
                try:
                    full_path = self.repo_root / file_path
                    
                    # Parse the individual file
                    request = self.service_request_parser.parse_service_request_file(str(full_path))
                    if request:
                        service_requests.append(request)
                    
                except Exception as e:
                    logger.error(f"Failed to parse service request file {file_path}: {e}")
                    # Continue with other files instead of failing completely
                    continue
            
            return service_requests
            
        except Exception as e:
            logger.error(f"Failed to get PR service requests: {e}")
            raise

    def validate_pr_service_requests(self, base_branch: str = "main") -> Tuple[List[ServiceRequest], List[str]]:
        """
        Get and validate service requests from the current PR.
        
        Args:
            base_branch: The base branch to compare against (default: "main")
            
        Returns:
            Tuple of (valid_service_requests, validation_errors)
        """
        validation_errors = []
        valid_requests = []
        
        try:
            service_requests = self.get_pr_service_requests(base_branch)
            
            for request in service_requests:
                try:
                    # Validate each service request
                    if self.service_request_parser.validate_service_request(request):
                        valid_requests.append(request)
                    else:
                        error_msg = f"Service request '{request.name}' failed validation"
                        validation_errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Error validating service request '{request.name}': {e}"
                    validation_errors.append(error_msg)
                    logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Error getting PR service requests: {e}"
            validation_errors.append(error_msg)
            logger.error(error_msg)
        
        return valid_requests, validation_errors

    def is_in_pull_request(self) -> bool:
        """
        Check if we're currently in a pull request context.
        
        Returns:
            True if in a PR context (GitHub Actions with PR event or git branch != main)
        """
        # Check GitHub Actions environment
        if os.getenv("GITHUB_ACTIONS"):
            github_event = os.getenv("GITHUB_EVENT_NAME")
            if github_event in ["pull_request", "pull_request_target"]:
                return True
        
        # Check if current branch is not main/master
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            return current_branch not in ["main", "master"]
            
        except subprocess.CalledProcessError:
            logger.warning("Could not determine current git branch")
            return False


def get_pr_service_requests(repo_root: Optional[str] = None, base_branch: str = "main") -> List[ServiceRequest]:
    """
    Convenience function to get service requests from the current PR.
    
    Args:
        repo_root: Root directory of the git repository
        base_branch: The base branch to compare against
        
    Returns:
        List of ServiceRequest objects from the PR
    """
    github_integration = GitHubIntegration(repo_root)
    return github_integration.get_pr_service_requests(base_branch)


def validate_pr_service_requests(repo_root: Optional[str] = None, base_branch: str = "main") -> Tuple[List[ServiceRequest], List[str]]:
    """
    Convenience function to get and validate service requests from the current PR.
    
    Args:
        repo_root: Root directory of the git repository
        base_branch: The base branch to compare against
        
    Returns:
        Tuple of (valid_service_requests, validation_errors)
    """
    github_integration = GitHubIntegration(repo_root)
    return github_integration.validate_pr_service_requests(base_branch)
