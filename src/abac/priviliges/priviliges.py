"""
Databricks Privileges Module

This module provides utilities for working with Databricks privileges using the official SDK enums.
It maps SDK privileges to resource types and provides validation functionality.
"""

from enum import Enum

from databricks.sdk.service.catalog import Privilege, SecurableType


class ObjectType(Enum):
    """Enumeration mapping our internal resource types to SDK SecurableType values."""

    CATALOG = SecurableType.CATALOG
    SCHEMA = SecurableType.SCHEMA
    TABLE = SecurableType.TABLE
    VIEW = SecurableType.TABLE  # Views are treated as tables in Unity Catalog
    FUNCTION = SecurableType.FUNCTION
    VOLUME = SecurableType.VOLUME
    MODEL = SecurableType.TABLE  # Models are registered as tables in UC
    PIPELINE = SecurableType.PIPELINE
    CONNECTION = SecurableType.CONNECTION
    CREDENTIAL = SecurableType.CREDENTIAL
    EXTERNAL_LOCATION = SecurableType.EXTERNAL_LOCATION
    STORAGE_CREDENTIAL = SecurableType.STORAGE_CREDENTIAL
    SHARE = SecurableType.SHARE
    RECIPIENT = SecurableType.RECIPIENT
    PROVIDER = SecurableType.PROVIDER
    CLEAN_ROOM = SecurableType.CLEAN_ROOM
    METASTORE = SecurableType.METASTORE
    UNKNOWN = "unknown"


class PrivilegeMapping:
    """
    Maps SDK privileges to resource types based on Unity Catalog documentation.
    Uses the official Databricks SDK Privilege enum.
    """

    # Catalog-level privileges
    CATALOG_PRIVILEGES: frozenset[Privilege] = frozenset(
        [
            Privilege.USE_CATALOG,
            Privilege.CREATE_SCHEMA,
            Privilege.CREATE_TABLE,
            Privilege.CREATE_VOLUME,
            Privilege.CREATE_FUNCTION,
            Privilege.CREATE_MODEL,
            Privilege.CREATE_EXTERNAL_TABLE,
            Privilege.CREATE_EXTERNAL_VOLUME,
            Privilege.CREATE_MATERIALIZED_VIEW,
            Privilege.ALL_PRIVILEGES,
        ]
    )

    # Schema-level privileges
    SCHEMA_PRIVILEGES: frozenset[Privilege] = frozenset(
        [
            Privilege.USE_SCHEMA,
            Privilege.CREATE_TABLE,
            Privilege.CREATE_VIEW,
            Privilege.CREATE_FUNCTION,
            Privilege.CREATE_VOLUME,
            Privilege.CREATE_MODEL,
            Privilege.CREATE_EXTERNAL_TABLE,
            Privilege.CREATE_EXTERNAL_VOLUME,
            Privilege.CREATE_MATERIALIZED_VIEW,
            Privilege.MODIFY,
            Privilege.ALL_PRIVILEGES,
        ]
    )

    # Table-level privileges
    TABLE_PRIVILEGES: frozenset[Privilege] = frozenset(
        [Privilege.SELECT, Privilege.MODIFY, Privilege.ALL_PRIVILEGES, Privilege.APPLY_TAG]
    )

    # Function-level privileges
    FUNCTION_PRIVILEGES: frozenset[Privilege] = frozenset(
        [Privilege.EXECUTE, Privilege.ALL_PRIVILEGES, Privilege.MODIFY]
    )

    # Volume-level privileges
    VOLUME_PRIVILEGES: frozenset[Privilege] = frozenset(
        [
            Privilege.READ_VOLUME,
            Privilege.WRITE_VOLUME,
            Privilege.READ_FILES,
            Privilege.WRITE_FILES,
            Privilege.ALL_PRIVILEGES,
        ]
    )

    # Connection-level privileges
    CONNECTION_PRIVILEGES: frozenset[Privilege] = frozenset([Privilege.USE_CONNECTION, Privilege.ALL_PRIVILEGES])

    # External location privileges
    EXTERNAL_LOCATION_PRIVILEGES: frozenset[Privilege] = frozenset(
        [Privilege.READ_FILES, Privilege.WRITE_FILES, Privilege.CREATE_EXTERNAL_TABLE, Privilege.ALL_PRIVILEGES]
    )

    # Share privileges
    SHARE_PRIVILEGES: frozenset[Privilege] = frozenset(
        [Privilege.USE_SHARE, Privilege.SET_SHARE_PERMISSION, Privilege.ALL_PRIVILEGES]
    )

    # Provider privileges
    PROVIDER_PRIVILEGES: frozenset[Privilege] = frozenset([Privilege.USE_PROVIDER, Privilege.ALL_PRIVILEGES])

    # Recipient privileges
    RECIPIENT_PRIVILEGES: frozenset[Privilege] = frozenset([Privilege.USE_RECIPIENT, Privilege.ALL_PRIVILEGES])

    @classmethod
    def get_privileges_for_resource_type(cls, object_type: ObjectType) -> frozenset[Privilege]:
        """Get all valid privileges for a specific resource type."""
        privilege_map = {
            ObjectType.CATALOG: cls.CATALOG_PRIVILEGES,
            ObjectType.SCHEMA: cls.SCHEMA_PRIVILEGES,
            ObjectType.TABLE: cls.TABLE_PRIVILEGES,
            ObjectType.VIEW: cls.TABLE_PRIVILEGES,  # Views use same privileges as tables
            ObjectType.FUNCTION: cls.FUNCTION_PRIVILEGES,
            ObjectType.VOLUME: cls.VOLUME_PRIVILEGES,
            ObjectType.MODEL: cls.TABLE_PRIVILEGES,  # Models are treated as tables in UC
            ObjectType.CONNECTION: cls.CONNECTION_PRIVILEGES,
            ObjectType.EXTERNAL_LOCATION: cls.EXTERNAL_LOCATION_PRIVILEGES,
            ObjectType.SHARE: cls.SHARE_PRIVILEGES,
            ObjectType.PROVIDER: cls.PROVIDER_PRIVILEGES,
            ObjectType.RECIPIENT: cls.RECIPIENT_PRIVILEGES,
            ObjectType.PIPELINE: frozenset([Privilege.ALL_PRIVILEGES]),
            ObjectType.CREDENTIAL: frozenset([Privilege.ALL_PRIVILEGES]),
            ObjectType.STORAGE_CREDENTIAL: frozenset([Privilege.ALL_PRIVILEGES]),
            ObjectType.CLEAN_ROOM: frozenset([Privilege.ALL_PRIVILEGES]),
            ObjectType.METASTORE: frozenset([Privilege.ALL_PRIVILEGES]),
            ObjectType.UNKNOWN: frozenset(),
        }
        return privilege_map.get(object_type, frozenset())

    @classmethod
    def get_all_privileges(cls) -> frozenset[Privilege]:
        """Get all available privileges across all resource types."""
        all_privileges = set()

        all_privileges.update(cls.CATALOG_PRIVILEGES)
        all_privileges.update(cls.SCHEMA_PRIVILEGES)
        all_privileges.update(cls.TABLE_PRIVILEGES)
        all_privileges.update(cls.FUNCTION_PRIVILEGES)
        all_privileges.update(cls.VOLUME_PRIVILEGES)
        all_privileges.update(cls.CONNECTION_PRIVILEGES)
        all_privileges.update(cls.EXTERNAL_LOCATION_PRIVILEGES)
        all_privileges.update(cls.SHARE_PRIVILEGES)
        all_privileges.update(cls.PROVIDER_PRIVILEGES)
        all_privileges.update(cls.RECIPIENT_PRIVILEGES)

        return frozenset(all_privileges)

    @classmethod
    def validate_privilege(cls, privilege: str, object_type: ObjectType = ObjectType.UNKNOWN) -> bool:
        """Validate if a privilege is valid for a given type or globally."""
        try:
            # Convert string to Privilege enum
            privilege_enum = Privilege[privilege.upper()]
        except KeyError:
            return False

        if object_type and object_type != ObjectType.UNKNOWN:
            valid_privileges = cls.get_privileges_for_resource_type(object_type)
            return privilege_enum in valid_privileges
        else:
            # For unknown types, validate against all privileges
            all_privileges = cls.get_all_privileges()
            return privilege_enum in all_privileges

    @classmethod
    def get_privilege_suggestions(cls, partial_privilege: str) -> list[str]:
        """Get privilege suggestions based on partial input."""
        all_privileges = cls.get_all_privileges()
        suggestions = [priv.value for priv in all_privileges if partial_privilege.upper() in priv.value.upper()]
        return sorted(suggestions)


class StandardPrivileges:
    """
    Compatibility layer for existing code that uses StandardPrivileges.
    Delegates to PrivilegeMapping for actual functionality.
    """

    @staticmethod
    def get_all_privileges_by_type(object_type: ObjectType) -> frozenset[str]:
        """Get all privileges for a specific object type as strings."""
        privileges = PrivilegeMapping.get_privileges_for_resource_type(object_type)
        return frozenset(priv.value for priv in privileges)

    @staticmethod
    def validate_privilege(privilege: str, object_type: ObjectType = ObjectType.UNKNOWN) -> bool:
        """Validate if a privilege is valid for a given type."""
        return PrivilegeMapping.validate_privilege(privilege, object_type)

    @staticmethod
    def get_all_privileges() -> frozenset[str]:
        """Get all available privileges as strings."""
        privileges = PrivilegeMapping.get_all_privileges()
        return frozenset(priv.value for priv in privileges)

    @staticmethod
    def get_privilege_suggestions(partial_privilege: str) -> list[str]:
        """Get privilege suggestions based on partial input."""
        return PrivilegeMapping.get_privilege_suggestions(partial_privilege)


# Convenience instances for easy access
PRIVILEGES = PrivilegeMapping()
PRIVILEGE_MAPPING = PrivilegeMapping()
