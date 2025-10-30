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
from privileges.workspace import workspace
from privileges.grants.grants import create_grant_manager
from privileges.apply_priviliges import determine_uc_object_type

logger = logging_helper.get_logger(__name__)


def validate_pr_privileges(base_branch: str = "main", verbose: bool = False, validate_databricks: bool = False) -> int:
    """
    Validate service requests from the current PR without applying them.
    
    Args:
        base_branch: Base branch to compare against for PR detection
        verbose: If True, show detailed information about each service request
        validate_databricks: If True, validate principals and resources exist in Databricks
        
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
                logger.error(f"  {error}")
            return 1
        
        if not valid_requests:
            logger.info("No service requests found in the current PR - nothing to validate.")
            return 0
        
        # Validate against Databricks if requested
        if validate_databricks:
            logger.info("Validating principals and resources in Databricks...")
            databricks_errors = []
            
            try:
                # Get Databricks workspace client
                workspace_client = workspace.get_workspace(None, None)
                grant_manager = create_grant_manager(workspace_client)
                
                for request in valid_requests:
                    for i, item in enumerate(request.requests, 1):
                        # Validate principal exists
                        principal_exists, principal_error = grant_manager.validate_principal_exists(
                            item.principal.id, item.principal.type
                        )
                        if not principal_exists:
                            databricks_errors.append(
                                f"{request.name} - Request {i}: {principal_error}"
                            )
                        
                        # Validate resource exists
                        try:
                            object_type = determine_uc_object_type(workspace_client, item.resource)
                            resource_exists, resource_error = grant_manager.validate_resource_exists(
                                item.resource, object_type
                            )
                            if not resource_exists:
                                databricks_errors.append(
                                    f"{request.name} - Request {i}: {resource_error}"
                                )
                        except Exception as e:
                            databricks_errors.append(
                                f"{request.name} - Request {i}: Error determining resource type for '{item.resource}': {e}"
                            )
                
                if databricks_errors:
                    logger.error("Databricks validation failed:")
                    for error in databricks_errors:
                        logger.error(f"  {error}")
                    return 1
                
                logger.info("Databricks validation successful")
                
            except Exception as e:
                logger.error(f"Error during Databricks validation: {e}")
                return 1
        
        logger.info(f"Successfully validated {len(valid_requests)} service request(s)")
        
        # Show detailed information if verbose
        if verbose:
            for request in valid_requests:
                logger.info(f"{request.name} [{request.request_status}] - {len(request.requests)} items")
                for i, item in enumerate(request.requests, 1):
                    logger.info(f"  {i}. {item.principal.type}:{item.principal.id} -> {item.resource} ({', '.join(item.privileges)})")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error validating PR service requests: {e}")
        return 1


def main():
    """Main entry point."""
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    validate_databricks = "--validate-databricks" in sys.argv or "--databricks" in sys.argv
    base_branch = os.getenv("BASE_BRANCH", "main")
    
    # Get base branch from command line if provided
    for i, arg in enumerate(sys.argv):
        if arg == "--base-branch" and i + 1 < len(sys.argv):
            base_branch = sys.argv[i + 1]
            break
    
    exit_code = validate_pr_privileges(
        base_branch=base_branch, 
        verbose=verbose,
        validate_databricks=validate_databricks
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()