"""
ABAC (Attribute-Based Access Control) module.

This module provides functionality for implementing attribute-based access control
in your applications.
"""

from privileges.grants.grants import create_grant_manager
from privileges.logger import logging_helper
from privileges.privileges.privileges import ObjectType, StandardPrivileges
from privileges.service_requests.parser import ServiceRequestParser
from privileges.workspace import workspace

from typing import Optional
import os

logger = logging_helper.get_logger(__name__)


# Determine the object type of the resource in Databricks UC context using SDK
def determine_uc_object_type(workspace_client, object_path: str) -> ObjectType:
    """
    Determine the Unity Catalog object type using Databricks SDK.

    Args:
        workspace_client: Databricks workspace client
        resource_path: The resource path (e.g., 'catalog.schema.table')

    Returns:
        ObjectType: The object type (e.g., ObjectType.CATALOG, ObjectType.SCHEMA, etc.)
    """
    if not object_path:
        return ObjectType.UNKNOWN

    try:
        parts = object_path.split(".")
        expected_catalog_len = 1
        expected_schema_len = 2
        expected_object_len = 3

        if len(parts) == expected_catalog_len:
            # Check if it's a catalog
            try:
                workspace_client.catalogs.get(parts[0])
                return ObjectType.CATALOG
            except Exception:
                # Could be a volume path or other resource
                if object_path.startswith("/"):
                    return ObjectType.VOLUME
                return ObjectType.UNKNOWN

        elif len(parts) == expected_schema_len:
            # Check if it's a schema
            try:
                workspace_client.schemas.get(f"{parts[0]}.{parts[1]}")
                return ObjectType.SCHEMA
            except Exception:
                return ObjectType.UNKNOWN

        elif len(parts) == expected_object_len:
            catalog_name, schema_name, object_name = parts

            # Check if it's a table
            try:
                workspace_client.tables.get(f"{catalog_name}.{schema_name}.{object_name}")
                return ObjectType.TABLE
            except Exception:
                logger.debug(f"'{object_path}' is not a table")

            # Check if it's a volume
            try:
                workspace_client.volumes.read(f"{catalog_name}.{schema_name}.{object_name}")
                return ObjectType.VOLUME
            except Exception:
                logger.debug(f"'{object_path}' is not a volume")

            # Check if it's a function
            try:
                workspace_client.functions.get(f"{catalog_name}.{schema_name}.{object_name}")
                return ObjectType.FUNCTION
            except Exception:
                logger.debug(f"'{object_path}' is not a function")

            return ObjectType.UNKNOWN

        else:
            return ObjectType.UNKNOWN

    except Exception as e:
        logger.warning(f"Error determining object type for '{object_path}': {e}")
        return ObjectType.UNKNOWN


def validate_privileges_for_resource_type(privileges: list, object_type: ObjectType) -> dict:
    """
    Validate privileges against the allowed privileges for a specific resource type.

    Args:
        privileges: List of privileges to validate
        object_type: The resource type to validate against

    Returns:
        dict: Dictionary with validation results
    """
    results = {"valid_privileges": [], "invalid_privileges": [], "suggestions": {}}

    # Handle None or empty privileges list
    if not privileges:
        logger.warning("No privileges provided for validation")
        return results

    for privilege in privileges:
        if StandardPrivileges.validate_privilege(privilege, object_type):
            results["valid_privileges"].append(privilege)
            logger.debug(f"    '{privilege}' - Valid for {object_type.value}")
        else:
            results["invalid_privileges"].append(privilege)
            logger.warning(f"    '{privilege}' - Invalid for {object_type.value}")

    return results


def apply_service_request_privileges(service_request, workspace_client, dry_run: bool = True):
    """
    Apply or validate privileges from a service request.

    Args:
        service_request: ServiceRequest object
        workspace_client: Databricks WorkspaceClient
        dry_run: If True, only validate without applying. If False, actually apply privileges.
    """
    # Determine operation based on request status
    is_add_operation = service_request.request_status.lower() == "active"
    operation_type = "add" if is_add_operation else "remove"

    logger.debug(
        "{} privileges ({}) for service request: {}".format(
            "Validating" if dry_run else "Applying", operation_type, service_request.name
        )
    )

    # Create grant manager
    grant_manager = create_grant_manager(workspace_client)

    for i, request_item in enumerate(service_request.requests):
        try:
            logger.info(f"Processing request {i + 1}: {request_item.resource}")

            # Check if privileges exist
            if not request_item.privileges:
                logger.warning(f"No privileges found for request {i + 1}")
                continue

            # Determine resource type
            object_type = determine_uc_object_type(workspace_client, request_item.resource)
            logger.debug(f"Determined resource type: {object_type.value}")

            # Validate privileges
            validation_results = validate_privileges_for_resource_type(request_item.privileges, object_type)
        except Exception as e:
            logger.error(f"Error processing request {i + 1}: {e}")
            continue

        if not dry_run and validation_results["valid_privileges"]:
            # Apply valid privileges
            principal = f"{request_item.principal.id}"

            try:
                grant_results = grant_manager.apply_multiple_privileges(
                    resource_name=request_item.resource,
                    object_type=object_type,
                    principal=principal,
                    privileges=validation_results["valid_privileges"],
                    is_add=is_add_operation,
                )
                action = "applied" if is_add_operation else "removed"
                logger.info(f"Successfully {action} privileges for {request_item.resource}")
                logger.debug(f"Grant results: {grant_results}")
            except Exception as e:
                action = "applying" if is_add_operation else "removing"
                logger.error(f"Error {action} privileges for {request_item.resource}: {e}")

    if not dry_run:
        logger.info("Successfully applied service requests")

def get_env_variable(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and required validation.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Value of the environment variable or default
        
    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(var_name, default)
    if required and value is None:
        error_msg = f"Required environment variable '{var_name}' not found"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return value

def main():
    """Main entry point for the apply_priviliges command."""
    # When run as a script, initialize the workspace and list groups
    try:
        host = get_env_variable('DATABRICKS_HOST')
        token = get_env_variable('DATABRICKS_TOKEN')

        workspace_client = workspace.get_workspace(host=str(host), token=str(token))
        parser = ServiceRequestParser()
        service_requests = parser.parse_service_requests_directory("service_requests/priviliges")

        for service_request in service_requests:
            logger.info(f"\n--- Processing Service Request: {service_request.name} ---")
            # Dry run - validate only, don't actually apply
            # apply_service_request_privileges(service_request, workspace_client, dry_run=True)

            # Uncomment the next line to actually apply privileges (use with caution!)
            apply_service_request_privileges(service_request, workspace_client, dry_run=False)

    except Exception as e:
        logger.error(f"Main execution error: {e}")


if __name__ == "__main__":
    main()
