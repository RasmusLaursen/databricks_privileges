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

from github import Github



class GitHubIntegration:
    """Integration class for GitHub operations and PR detection using GitHub API v3."""

    def __init__(self, repo_root: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize GitHub integration.
        
        Args:
            repo_root: Root directory of the git repository. If None, uses current directory.
            github_token: GitHub personal access token. If None, uses GITHUB_TOKEN env var.
        """
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.service_request_parser = ServiceRequestParser()
        
        # Initialize GitHub API client
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        # In GitHub Actions, the token is automatically available
        if not self.github_token and os.getenv("GITHUB_ACTIONS"):
            logger.warning("Running in GitHub Actions but no GITHUB_TOKEN found. Make sure it's available in your workflow.")
        
        self.github_client = Github(self.github_token) if self.github_token else None
        
        # GitHub repository info
        self.repo_owner = None
        self.repo_name = None
        self.pr_number = None
        
        self._initialize_repo_info()

    def _initialize_repo_info(self):
        """Initialize repository information from environment variables."""
        if os.getenv("GITHUB_ACTIONS"):
            # Extract repo info from GitHub Actions environment
            github_repository = os.getenv("GITHUB_REPOSITORY")  # format: "owner/repo"
            if github_repository:
                self.repo_owner, self.repo_name = github_repository.split("/")
            
            # Get PR number from different possible sources
            github_event = os.getenv("GITHUB_EVENT_NAME")
            if github_event == "pull_request":
                # Try to get PR number from GitHub context
                github_ref = os.getenv("GITHUB_REF")  # format: "refs/pull/123/merge"
                if github_ref and github_ref.startswith("refs/pull/"):
                    try:
                        self.pr_number = int(github_ref.split("/")[2])
                    except (IndexError, ValueError):
                        pass
                
                # Fallback: try environment variable set by some actions
                if not self.pr_number:
                    pr_num_str = os.getenv("GITHUB_PR_NUMBER") or os.getenv("PR_NUMBER")
                    if pr_num_str:
                        try:
                            self.pr_number = int(pr_num_str)
                        except ValueError:
                            pass

    def get_repository(self):
        """Get the GitHub repository object."""
        if not self.github_client or not self.repo_owner or not self.repo_name:
            return None
        
        try:
            return self.github_client.get_repo(f"{self.repo_owner}/{self.repo_name}")
        except Exception as e:
            logger.error(f"Failed to get repository {self.repo_owner}/{self.repo_name}: {e}")
            return None

    def get_pull_request(self, pr_number: Optional[int] = None):
        """
        Get the pull request object.
        
        Args:
            pr_number: PR number. If None, uses the detected PR number.
            
        Returns:
            PullRequest object or None if not found
        """
        repo = self.get_repository()
        if not repo:
            return None
        
        pr_num = pr_number or self.pr_number
        if not pr_num:
            logger.warning("No PR number available")
            return None
        
        try:
            return repo.get_pull(pr_num)
        except Exception as e:
            logger.error(f"Failed to get pull request #{pr_num}: {e}")
            return None

    def get_changed_files_from_api(self, pr_number: Optional[int] = None) -> List[str]:
        """
        Get list of files changed in the pull request using GitHub API v3.
        
        Args:
            pr_number: PR number. If None, uses the detected PR number.
            
        Returns:
            List of changed file paths
        """
        pull_request = self.get_pull_request(pr_number)
        if not pull_request:
            logger.warning("Could not get pull request, falling back to git commands")
            return []
        
        try:
            changed_files = []
            
            # Get all files changed in the PR
            files = pull_request.get_files()
            
            for file_obj in files:
                # Include files that were added, modified, or renamed
                # Exclude deleted files since we can't parse them
                if file_obj.status in ["added", "modified", "renamed"]:
                    changed_files.append(file_obj.filename)
            
            logger.info(f"Successfully got {len(changed_files)} changed files from GitHub API")
            return changed_files
            
        except Exception as e:
            logger.error(f"Failed to get changed files from GitHub API: {e}")
            return []

    def get_changed_files(self, pr_number: Optional[int] = None, base_branch: str = "main") -> List[str]:
        """
        Get list of files changed in the current pull request.
        
        This method first tries to use the GitHub API v3, then falls back to git commands.
        
        Args:
            pr_number: PR number. If None, uses the detected PR number.
            base_branch: The base branch to compare against (used for git fallback)
            
        Returns:
            List of changed file paths
        """
        # First try GitHub API if we have the necessary information
        if self.github_client and (pr_number or self.pr_number):
            try:
                api_files = self.get_changed_files_from_api(pr_number)
                if api_files:  # If we got files from API, return them
                    return api_files
                else:
                    logger.info("GitHub API returned no files, falling back to git")
            except Exception as e:
                logger.warning(f"GitHub API failed, falling back to git: {e}")
        
        # Fallback to git commands
        return self.get_changed_files_from_git(base_branch)

    def get_changed_files_from_git(self, base_branch: str = "main") -> List[str]:
        """
        Get list of files changed using git commands (fallback method).
        
        Args:
            base_branch: The base branch to compare against (default: "main")
            
        Returns:
            List of changed file paths relative to repo root
        """
        # Try different branch references in order of preference
        branch_refs = [
            f"origin/{base_branch}",  # Remote branch (most reliable)
            base_branch,              # Local branch
            f"upstream/{base_branch}" # Upstream branch (for forks)
        ]
        
        for branch_ref in branch_refs:
            try:
                # Get files changed between base branch and current HEAD
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{branch_ref}...HEAD"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                changed_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                logger.info(f"Successfully got changed files using {branch_ref}")
                return changed_files
                
            except subprocess.CalledProcessError as e:
                logger.debug(f"Failed to get changed files using {branch_ref}: {e}")
                logger.debug(f"Command stderr: {e.stderr}")
                last_error = e
                continue
        
        # If all attempts failed, try a fallback approach
        logger.warning(f"Failed to get changed files using any branch reference: {branch_refs}")
        logger.info("Trying fallback: get all tracked files")
        
        try:
            # Fallback: get all tracked files in the repository
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            all_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            logger.info(f"Fallback successful: found {len(all_files)} tracked files")
            return all_files
            
        except subprocess.CalledProcessError as fallback_error:
            logger.error("Fallback also failed")
            logger.error(f"Fallback error: {fallback_error}")
            
            # Raise the original error with more details
            if 'last_error' in locals():
                logger.error(f"Original error command: {last_error.cmd}")
                logger.error(f"Original error stderr: {last_error.stderr}")
                logger.error(f"Original error stdout: {last_error.stdout}")
                raise last_error
            else:
                raise subprocess.CalledProcessError(
                    1, 
                    f"git diff --name-only", 
                    f"Could not find any valid branch reference from: {', '.join(branch_refs)}"
                )

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
                changed_files = self.get_changed_files_from_git(base_sha)
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

    def get_pr_service_requests(self, pr_number: Optional[int] = None, base_branch: str = "main") -> List[ServiceRequest]:
        """
        Get all service requests that are part of the current pull request.
        
        Args:
            pr_number: PR number. If None, uses the detected PR number.
            base_branch: The base branch to compare against (used for git fallback)
            
        Returns:
            List of parsed ServiceRequest objects from files changed in the PR
            
        Raises:
            Exception: If unable to parse service request files
        """
        try:
            # Get changed files using GitHub API or git (GitHub API is preferred)
            changed_files = self.get_changed_files(pr_number, base_branch)
            
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

    def validate_pr_service_requests(self, pr_number: Optional[int] = None, base_branch: str = "main") -> Tuple[List[ServiceRequest], List[str]]:
        """
        Get and validate service requests from the current PR.
        
        Args:
            pr_number: PR number. If None, uses the detected PR number.
            base_branch: The base branch to compare against (used for git fallback)
            
        Returns:
            Tuple of (valid_service_requests, validation_errors)
        """
        validation_errors = []
        valid_requests = []
        
        try:
            service_requests = self.get_pr_service_requests(pr_number, base_branch)
            
            for request in service_requests:
                try:
                    # Validate each service request
                    validation_result = self.service_request_parser.validate_service_request(request)
                    if not validation_result:  # Empty list means valid
                        valid_requests.append(request)
                    else:
                        # Add specific validation errors
                        for error in validation_result:
                            validation_errors.append(f"Service request '{request.name}': {error}")
                        
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


def get_pr_service_requests(repo_root: Optional[str] = None, pr_number: Optional[int] = None, base_branch: str = "main") -> List[ServiceRequest]:
    """
    Convenience function to get service requests from the current PR.
    
    Args:
        repo_root: Root directory of the git repository
        pr_number: PR number. If None, auto-detects from environment
        base_branch: The base branch to compare against
        
    Returns:
        List of ServiceRequest objects from the PR
    """
    github_integration = GitHubIntegration(repo_root)
    return github_integration.get_pr_service_requests(pr_number, base_branch)


def validate_pr_service_requests(repo_root: Optional[str] = None, pr_number: Optional[int] = None, base_branch: str = "main") -> Tuple[List[ServiceRequest], List[str]]:
    """
    Convenience function to get and validate service requests from the current PR.
    
    Args:
        repo_root: Root directory of the git repository
        pr_number: PR number. If None, auto-detects from environment
        base_branch: The base branch to compare against
        
    Returns:
        Tuple of (valid_service_requests, validation_errors)
    """
    github_integration = GitHubIntegration(repo_root)
    return github_integration.validate_pr_service_requests(pr_number, base_branch)
