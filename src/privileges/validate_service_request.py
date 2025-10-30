#!/usr/bin/env python3
"""
Script to validate service requests in the current pull request.

This script is designed to be used in CI/CD pipelines to automatically
validate service requests that are part of the current PR without applying them.
"""

import sys
import os

from privileges.github.github import GitHubIntegration, validate_pr_service_requests
from privileges.logger import logging_helper

logger = logging_helper.get_logger(__name__)


def validate_pr_privileges(base_branch: str = "main", verbose: bool = False) -> int:
    """
    Validate service requests from the current PR without applying them.
    
    Args:
        base_branch: Base branch to compare against for PR detection
        verbose: If True, show detailed information about each service request
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Initialize GitHub integration
        github_integration = GitHubIntegration()
        
        # Check if we're in a PR context
        if not github_integration.is_in_pull_request():
            logger.info("Not in a pull request context - nothing to validate.")
            return 0
        
        # Get changed files for context (using GitHub API if available)
        try:
            changed_files = github_integration.get_changed_files(base_branch=base_branch)
            service_request_files = github_integration.filter_service_request_files(changed_files)
            
            logger.info(f"Found {len(service_request_files)} service request file(s) to validate")
            
        except Exception as e:
            logger.warning(f"Could not get changed files information: {e}")
        
        # Get and validate service requests from PR (using GitHub API if available)
        valid_requests, validation_errors = validate_pr_service_requests(base_branch=base_branch)
        
        if validation_errors:
            logger.error("Service request validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        
        if not valid_requests:
            logger.info("No service requests found in the current PR - nothing to validate.")
            return 0
        
        logger.info(f"Successfully validated {len(valid_requests)} service request(s)")
        
        # Show detailed information if verbose
        if verbose:
            for request in valid_requests:
                logger.info(f"Service Request: {request.name}")
                logger.info(f"   Status: {request.status}")
                logger.info(f"   Items: {len(request.requests)}")
                
                for i, item in enumerate(request.requests, 1):
                    logger.info(f"   {i}. Principal: {item.principal.type}:{item.principal.id}")
                    logger.info(f"      Resource: {item.resource}")
                    logger.info(f"      Privileges: {', '.join(item.privileges)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error validating PR service requests: {e}")
        return 1


def main():
    """Main entry point."""
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    base_branch = os.getenv("BASE_BRANCH", "main")
    
    # Get base branch from command line if provided
    for i, arg in enumerate(sys.argv):
        if arg == "--base-branch" and i + 1 < len(sys.argv):
            base_branch = sys.argv[i + 1]
            break
    
    exit_code = validate_pr_privileges(base_branch=base_branch, verbose=verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()