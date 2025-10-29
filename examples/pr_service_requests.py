#!/usr/bin/env python3
"""
Example script demonstrating how to use the GitHub integration to get
service requests from the current pull request.

This script can be used in CI/CD pipelines or locally to process
service requests that are part of the current PR.
"""

import sys
from pathlib import Path

from privileges.github.github import GitHubIntegration, get_pr_service_requests, validate_pr_service_requests
from privileges.logger import logging_helper

logger = logging_helper.get_logger(__name__)


def main():
    """Main function to demonstrate PR service request processing."""
    try:
        # Initialize GitHub integration
        github_integration = GitHubIntegration()
        
        # Check if we're in a PR context
        if not github_integration.is_in_pull_request():
            logger.info("Not in a pull request context, exiting.")
            return 0
        
        logger.info("Processing service requests from current pull request...")
        
        # Method 1: Using the convenience function
        service_requests = get_pr_service_requests()
        
        if not service_requests:
            logger.info("No service requests found in the current PR.")
            return 0
        
        logger.info(f"Found {len(service_requests)} service request(s) in PR:")
        for request in service_requests:
            logger.info(f"  - {request.name}: {len(request.requests)} item(s)")
            for item in request.requests:
                logger.info(f"    * {item.principal.type}:{item.principal.id} -> {item.resource} ({', '.join(item.privileges)})")
        
        # Method 2: Using validation
        valid_requests, validation_errors = validate_pr_service_requests()
        
        if validation_errors:
            logger.error("Validation errors found:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        
        logger.info(f"All {len(valid_requests)} service requests are valid!")
        
        # Method 3: Getting file change information
        changed_files = github_integration.get_changed_files()
        service_request_files = github_integration.filter_service_request_files(changed_files)
        
        logger.info(f"Changed files: {len(changed_files)}, Service request files: {len(service_request_files)}")
        
        if service_request_files:
            for file_path in service_request_files:
                logger.info(f"  - {file_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing PR service requests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)