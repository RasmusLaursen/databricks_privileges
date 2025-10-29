"""
Databricks Grants Module

This module provides functionality to apply and manage privileges in Databricks
using the Databricks SDK based on resource types defined in the privileges module.
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import PermissionsChange, Privilege

from privileges.logger import logging_helper
from privileges.privileges.privileges import ObjectType, StandardPrivileges

logger = logging_helper.get_logger(__name__)


class PrivilegeGrantManager:
    """Manages privilege grants in Databricks using the SDK."""

    def __init__(self, workspace_client: WorkspaceClient):
        """
        Initialize the PrivilegeGrantManager.

        Args:
            workspace_client: Databricks WorkspaceClient instance
        """
        self.workspace_client = workspace_client
        self.logger = logging_helper.get_logger(__name__)

    def _get_securable_type(self, object_type: ObjectType) -> str:
        """
        Map ObjectType to Databricks SecurableType string.

        Args:
            object_type: The ObjectType enum value

        Returns:
            str: The corresponding securable type string
        """
        type_mapping = {
            ObjectType.CATALOG: "catalog",
            ObjectType.SCHEMA: "schema",
            ObjectType.TABLE: "table",
            ObjectType.VIEW: "table",  # Views are treated as tables in grants
            ObjectType.FUNCTION: "function",
            ObjectType.VOLUME: "volume",
            ObjectType.MODEL: "registered_model",
        }
        return type_mapping.get(object_type, "table")

    def validate_privilege_for_resource(self, privilege: str, object_type: ObjectType) -> bool:
        """
        Validate if a privilege is valid for a specific resource type.

        Args:
            privilege: The privilege to validate
            object_type: The resource type

        Returns:
            bool: True if privilege is valid for the resource type
        """
        return StandardPrivileges.validate_privilege(privilege, object_type)

    def apply_multiple_privileges(
        self, resource_name: str, object_type: ObjectType, principal: str, privileges: list[str], is_add: bool = True
    ) -> dict[str, bool]:
        """
        Apply or remove multiple privileges to/from a principal on a resource.

        Args:
            resource_name: Full name of the resource
            object_type: Type of the resource
            principal: The principal to grant privileges to
            privileges: list of privileges to grant or revoke
            is_add: True to add privileges, False to remove privileges

        Returns:
            dict[str, bool]: dictionary mapping privilege to success status
        """
        results = {}
        valid_privileges = []

        # Validate all privileges first
        for privilege in privileges:
            if self.validate_privilege_for_resource(privilege, object_type):
                valid_privileges.append(privilege)
                results[privilege] = False  # Will be updated on success
            else:
                # Handle both ObjectType enum and string
                object_type_str = object_type.value if hasattr(object_type, "value") else str(object_type)
                self.logger.error(f"Invalid privilege '{privilege}' for resource type '{object_type_str}'")
                results[privilege] = False

        if not valid_privileges:
            self.logger.error("No valid privileges to grant")
            return results

        try:
            # Get securable type
            securable_type = self._get_securable_type(object_type)

            # Convert privileges to enums
            privilege_enums = []
            for privilege in valid_privileges:
                try:
                    privilege_enums.append(Privilege[privilege.upper()])
                except KeyError:
                    self.logger.error(f"Unknown privilege: {privilege}")
                    results[privilege] = False
                    continue

            if not privilege_enums:
                self.logger.error("No valid privilege enums found")
                return results

            # Create permissions change
            permissions_change = PermissionsChange(
                principal=principal,
                add=privilege_enums if is_add else None,
                remove=privilege_enums if not is_add else None,
            )

            # Apply all grants in one call
            self.workspace_client.grants.update(
                securable_type=securable_type, full_name=resource_name, changes=[permissions_change]
            )

            # Mark all valid privileges as successful
            for privilege in valid_privileges:
                results[privilege] = True

        except Exception as e:
            action = "granting" if is_add else "revoking"
            preposition = "to" if is_add else "from"
            self.logger.error(f"Error {action} privileges on '{resource_name}' {preposition} '{principal}': {e}")
            # All privileges failed
            for privilege in valid_privileges:
                results[privilege] = False

        return results


def create_grant_manager(workspace_client: WorkspaceClient) -> PrivilegeGrantManager:
    """
    Factory function to create a PrivilegeGrantManager instance.

    Args:
        workspace_client: Databricks WorkspaceClient instance

    Returns:
        PrivilegeGrantManager: Configured grant manager
    """
    return PrivilegeGrantManager(workspace_client)
