#!/usr/bin/env python3
"""
Script to validate all service request files in the service_requests folder.

This script validates all YAML files in the service_requests directory structure
without requiring a PR context. It's useful for batch validation of all service requests.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

from privileges.service_requests.parser import ServiceRequestParser, ServiceRequest
from privileges.logger import logging_helper

logger = logging_helper.get_logger(__name__)


def find_service_request_files(base_path: str = "service_requests") -> List[Path]:
    """
    Find all YAML files in the service_requests directory structure.
    
    Args:
        base_path: Base path to search for service request files
        
    Returns:
        List of Path objects for YAML files found
    """
    service_request_files = []
    base_path_obj = Path(base_path)
    
    if not base_path_obj.exists():
        logger.warning(f"Service requests directory '{base_path}' does not exist")
        return service_request_files
    
    # Find all YAML files recursively
    for file_path in base_path_obj.rglob("*.yml"):
        service_request_files.append(file_path)
    
    for file_path in base_path_obj.rglob("*.yaml"):
        service_request_files.append(file_path)
    
    logger.info(f"Found {len(service_request_files)} service request file(s) to validate")
    return sorted(service_request_files)


def validate_all_service_requests(base_path: str = "service_requests", verbose: bool = False) -> int:
    """
    Validate all service request files in the service_requests directory.
    
    Args:
        base_path: Base path to search for service request files
        verbose: If True, show detailed information about each service request
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Initialize service request parser
        parser = ServiceRequestParser()
        
        # Find all service request files
        service_request_files = find_service_request_files(base_path)
        
        if not service_request_files:
            logger.info("No service request files found - nothing to validate.")
            return 0
        
        valid_requests = []
        validation_errors = []
        
        # Validate each file
        for file_path in service_request_files:
            logger.info(f"Validating: {file_path}")
            
            try:
                # Parse the service request file
                service_request = parser.parse_service_request_file(str(file_path))
                
                if service_request:
                    # Validate the parsed service request
                    file_validation_errors = parser.validate_service_request(service_request)
                    
                    if not file_validation_errors:  # Empty list means valid
                        valid_requests.append(service_request)
                        logger.info(f"Valid: {file_path}")
                    else:
                        # Add specific validation errors
                        for error in file_validation_errors:
                            validation_errors.append(f"{file_path}: {error}")
                        logger.error(f"Invalid: {file_path}")
                else:
                    validation_errors.append(f"{file_path}: Failed to parse service request")
                    logger.error(f"Parse error: {file_path}")
                    
            except Exception as e:
                error_msg = f"{file_path}: Error processing file: {e}"
                validation_errors.append(error_msg)
                logger.error(f"Processing error: {file_path} - {e}")
        
        # Report results
        if validation_errors:
            logger.error(f"Validation failed with {len(validation_errors)} issue(s):")
            for error in validation_errors:
                logger.error(f"  {error}")
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
        logger.error(f"Error validating service requests: {e}")
        return 1


def main():
    """Main entry point."""
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Get base path from command line if provided
    base_path = "service_requests"
    for i, arg in enumerate(sys.argv):
        if arg == "--path" and i + 1 < len(sys.argv):
            base_path = sys.argv[i + 1]
            break
    
    exit_code = validate_all_service_requests(base_path=base_path, verbose=verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()