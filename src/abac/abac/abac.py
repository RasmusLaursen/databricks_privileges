"""
ABAC Policies Interface

This module provides a comprehensive interface to Databricks Unity Catalog policies
for Attribute-Based Access Control (ABAC) operations.
"""

from typing import Any, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import (
    ColumnMaskOptions,
    DeletePolicyResponse,
    FunctionArgument,
    MatchColumn,
    PolicyInfo,
    PolicyType,
    RowFilterOptions,
    SecurableType,
)


class ABACPoliciesInterface:
    """Interface for Databricks Unity Catalog ABAC policies operations."""

    def __init__(self, workspace_client: WorkspaceClient):
        """
        Initialize the ABAC policies interface.

        Args:
            workspace_client: WorkspaceClient instance.
        """
        self.client = workspace_client

    def list_policies(self, securable_type: str, securable_fullname: str, include_inherited: bool = False) -> list[Any]:
        """
        list policies for a specific securable object.

        Args:
            securable_type: Type of securable (e.g., 'table', 'schema', 'catalog')
            securable_fullname: Full name of the securable object
            include_inherited: Whether to include inherited policies

        Returns:
            list[Any]: list of policies
        """
        return list(
            self.client.policies.list_policies(
                on_securable_type=securable_type,
                on_securable_fullname=securable_fullname,
                include_inherited=include_inherited,
            )
        )

    def get_policies_for_securable(
        self, securable_type: str, securable_fullname: str, include_inherited: bool = False
    ) -> list[Any]:
        """
        Get all policies applied to a specific securable object.

        Args:
            securable_type: Type of securable (e.g., 'table', 'schema', 'catalog')
            securable_fullname: Full name of the securable object
            include_inherited: Whether to include inherited policies

        Returns:
            list[Any]: list of policies applied to the securable
        """
        return self.list_policies(
            securable_type=securable_type, securable_fullname=securable_fullname, include_inherited=include_inherited
        )

    def get_policy_summary(self, policy_data: Any) -> dict[str, Any]:
        """
        Get a summary of a policy.

        Args:
            policy_data: The policy object returned from the API

        Returns:
            dict[str, Any]: Policy summary
        """
        return {
            "id": getattr(policy_data, "policy_id", getattr(policy_data, "id", None)),
            "name": getattr(policy_data, "name", None),
            "type": getattr(policy_data, "policy_type", getattr(policy_data, "type", None)),
            "definition": getattr(policy_data, "definition", None),
            "created_at": getattr(policy_data, "created_at", None),
            "updated_at": getattr(policy_data, "updated_at", None),
            "created_by": getattr(policy_data, "created_by", None),
            "updated_by": getattr(policy_data, "updated_by", None),
        }

    def list_policies_with_summary(
        self, securable_type: str, securable_fullname: str, include_inherited: bool = False
    ) -> list[dict[str, Any]]:
        """
        list policies and return them as summaries.

        Args:
            securable_type: Type of securable (e.g., 'table', 'schema', 'catalog')
            securable_fullname: Full name of the securable object
            include_inherited: Whether to include inherited policies

        Returns:
            list[dict[str, Any]]: list of policy summaries
        """
        policies = self.list_policies(securable_type, securable_fullname, include_inherited)
        return [self.get_policy_summary(policy) for policy in policies]

    def create_policy(
        self,
        name: str,
        securable_type: str,
        securable_fullname: str,
        policy_type: str,
        principals: list[str],
        column_mask_function: Optional[str] = None,
        column_mask_on_column: Optional[str] = None,
        column_mask_using_args: Optional[list[dict[str, Any]]] = None,
        row_filter_function: Optional[str] = None,
        row_filter_using_args: Optional[list[dict[str, Any]]] = None,
        when_condition: Optional[str] = None,
        match_columns: Optional[list[dict[str, Any]]] = None,
        except_principals: Optional[list[str]] = None,
        comment: Optional[str] = None,
    ) -> PolicyInfo:
        """
        Create a new ABAC policy.

        Args:
            name: Name of the policy
            securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
            securable_fullname: Full name of the securable object
            policy_type: Type of policy ('POLICY_TYPE_COLUMN_MASK' or 'POLICY_TYPE_ROW_FILTER')
            principals: list of principals to apply the policy to
            column_mask_function: Function name for column masking (required for column mask policies)
            column_mask_on_column: Column name for column masking (required for column mask policies)
            column_mask_using_args: Arguments for column mask function
            row_filter_function: Function name for row filtering (required for row filter policies)
            row_filter_using_args: Arguments for row filter function
            when_condition: SQL condition for when the policy applies
            match_columns: Column matching configuration
            except_principals: Principals to exclude from the policy
            comment: Optional comment for the policy

        Returns:
            PolicyInfo: The created policy

        Raises:
            ValueError: If required parameters for the policy type are missing
        """
        # Validate policy type and required parameters
        if policy_type not in ["POLICY_TYPE_COLUMN_MASK", "POLICY_TYPE_ROW_FILTER"]:
            msg = (
                f"Invalid policy_type. Must be 'POLICY_TYPE_COLUMN_MASK' or "
                f"'POLICY_TYPE_ROW_FILTER', got: {policy_type}"
            )
            raise ValueError(msg)

        if policy_type == "POLICY_TYPE_COLUMN_MASK":
            if not column_mask_function or not column_mask_on_column:
                msg = "Column mask policies require both column_mask_function and column_mask_on_column"
                raise ValueError(msg)

        if policy_type == "POLICY_TYPE_ROW_FILTER":
            if not row_filter_function:
                msg = "Row filter policies require row_filter_function"
                raise ValueError(msg)

        # Convert string types to enum values
        securable_type_enum = SecurableType(securable_type.upper())
        policy_type_enum = PolicyType(policy_type)

        # Build column mask options if needed
        column_mask = None
        if column_mask_function and column_mask_on_column:
            using_args = []
            if column_mask_using_args:
                using_args = [
                    FunctionArgument(
                        alias=arg.get("alias", arg.get("parameter_name")),
                        constant=arg.get("constant", arg.get("parameter_value")),
                    )
                    for arg in column_mask_using_args
                ]

            column_mask = ColumnMaskOptions(
                function_name=column_mask_function,
                on_column=column_mask_on_column,
                using=using_args if using_args else None,
            )

        # Build row filter options if needed
        row_filter = None
        if row_filter_function:
            using_args = []
            if row_filter_using_args:
                using_args = [
                    FunctionArgument(
                        alias=arg.get("alias", arg.get("parameter_name")),
                        constant=arg.get("constant", arg.get("parameter_value")),
                    )
                    for arg in row_filter_using_args
                ]

            row_filter = RowFilterOptions(function_name=row_filter_function, using=using_args if using_args else None)

        # Build match columns if provided
        match_columns_list = None
        if match_columns:
            match_columns_list = [MatchColumn(**col) for col in match_columns]

        # Create PolicyInfo object
        policy_info = PolicyInfo(
            name=name,
            to_principals=principals,
            for_securable_type=securable_type_enum,
            policy_type=policy_type_enum,
            on_securable_type=securable_type_enum,
            on_securable_fullname=securable_fullname,
            column_mask=column_mask,
            row_filter=row_filter,
            when_condition=when_condition,
            match_columns=match_columns_list,
            except_principals=except_principals,
            comment=comment,
        )

        # Create the policy using the Databricks SDK
        return self.client.policies.create_policy(policy_info)

    def update_policy(
        self,
        securable_type: str,
        securable_fullname: str,
        policy_name: str,
        principals: Optional[list[str]] = None,
        column_mask_function: Optional[str] = None,
        column_mask_on_column: Optional[str] = None,
        column_mask_using_args: Optional[list[dict[str, Any]]] = None,
        row_filter_function: Optional[str] = None,
        row_filter_using_args: Optional[list[dict[str, Any]]] = None,
        when_condition: Optional[str] = None,
        match_columns: Optional[list[dict[str, Any]]] = None,
        except_principals: Optional[list[str]] = None,
        comment: Optional[str] = None,
    ) -> PolicyInfo:
        """
        Update an existing ABAC policy.

        Args:
            securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
            securable_fullname: Full name of the securable object
            policy_name: Name of the policy to update
            principals: list of principals to apply the policy to
            column_mask_function: Function name for column masking
            column_mask_on_column: Column name for column masking
            column_mask_using_args: Arguments for column mask function
            row_filter_function: Function name for row filtering
            row_filter_using_args: Arguments for row filter function
            when_condition: SQL condition for when the policy applies
            match_columns: Column matching configuration
            except_principals: Principals to exclude from the policy
            comment: Optional comment for the policy

        Returns:
            PolicyInfo: The updated policy
        """
        # First get the existing policy to determine its type
        existing_policy = self.get_policy(securable_type, securable_fullname, policy_name)

        # Build column mask options if provided
        column_mask = None
        if column_mask_function and column_mask_on_column:
            using_args = []
            if column_mask_using_args:
                using_args = [
                    FunctionArgument(
                        alias=arg.get("alias", arg.get("parameter_name")),
                        constant=arg.get("constant", arg.get("parameter_value")),
                    )
                    for arg in column_mask_using_args
                ]

            column_mask = ColumnMaskOptions(
                function_name=column_mask_function,
                on_column=column_mask_on_column,
                using=using_args if using_args else None,
            )

        # Build row filter options if provided
        row_filter = None
        if row_filter_function:
            using_args = []
            if row_filter_using_args:
                using_args = [
                    FunctionArgument(
                        alias=arg.get("alias", arg.get("parameter_name")),
                        constant=arg.get("constant", arg.get("parameter_value")),
                    )
                    for arg in row_filter_using_args
                ]

            row_filter = RowFilterOptions(function_name=row_filter_function, using=using_args if using_args else None)

        # Build match columns if provided
        match_columns_list = None
        if match_columns:
            match_columns_list = [MatchColumn(**col) for col in match_columns]

        # Create PolicyInfo object with only the fields that should be updated
        policy_update = PolicyInfo(
            to_principals=principals or existing_policy.to_principals,
            for_securable_type=existing_policy.for_securable_type,
            policy_type=existing_policy.policy_type,
            column_mask=column_mask if column_mask else existing_policy.column_mask,
            row_filter=row_filter if row_filter else existing_policy.row_filter,
            when_condition=when_condition if when_condition is not None else existing_policy.when_condition,
            match_columns=match_columns_list if match_columns_list else existing_policy.match_columns,
            except_principals=except_principals if except_principals is not None else existing_policy.except_principals,
            comment=comment if comment is not None else existing_policy.comment,
        )

        # Update the policy using the Databricks SDK
        return self.client.policies.update_policy(
            on_securable_type=securable_type,
            on_securable_fullname=securable_fullname,
            name=policy_name,
            policy_info=policy_update,
        )

    def delete_policy(self, securable_type: str, securable_fullname: str, policy_name: str) -> DeletePolicyResponse:
        """
        Delete an ABAC policy.

        Args:
            securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
            securable_fullname: Full name of the securable object
            policy_name: Name of the policy to delete

        Returns:
            DeletePolicyResponse: Response from the delete operation
        """
        return self.client.policies.delete_policy(
            on_securable_type=securable_type, on_securable_fullname=securable_fullname, name=policy_name
        )

    def get_policy(self, securable_type: str, securable_fullname: str, policy_name: str) -> PolicyInfo:
        """
        Get a specific policy by name.

        Args:
            securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
            securable_fullname: Full name of the securable object
            policy_name: Name of the policy to retrieve

        Returns:
            PolicyInfo: The policy information
        """
        return self.client.policies.get_policy(
            on_securable_type=securable_type, on_securable_fullname=securable_fullname, name=policy_name
        )


workspace_client = WorkspaceClient()

# Global instance for convenience
abac_policies = ABACPoliciesInterface(workspace_client=workspace_client)


# Convenience functions using the global instance
def list_abac_policies(
    securable_object: str, securable_type: str = "table", include_inherited: bool = False
) -> list[Any]:
    """
    list ABAC policies for a securable object.

    Args:
        securable_object: Full name of the securable object (required)
        securable_type: Type of securable (default: 'table')
        include_inherited: Whether to include inherited policies

    Returns:
        list[Any]: list of policies
    """
    return abac_policies.list_policies(
        securable_type=securable_type, securable_fullname=securable_object, include_inherited=include_inherited
    )


def get_policies_summary(
    securable_object: str, securable_type: str = "table", include_inherited: bool = False
) -> list[dict[str, Any]]:
    """
    Get ABAC policies summary for a securable object.

    Args:
        securable_object: Full name of the securable object (required)
        securable_type: Type of securable (default: 'table')
        include_inherited: Whether to include inherited policies

    Returns:
        list[dict[str, Any]]: list of policy summaries
    """
    return abac_policies.list_policies_with_summary(
        securable_type=securable_type, securable_fullname=securable_object, include_inherited=include_inherited
    )


def get_table_policies(table_name: str, include_inherited: bool = False) -> list[Any]:
    """
    Get all policies for a specific table.

    Args:
        table_name: Full table name (catalog.schema.table)
        include_inherited: Whether to include inherited policies

    Returns:
        list[Any]: list of policies for the table
    """
    return list_abac_policies(securable_object=table_name, securable_type="table", include_inherited=include_inherited)


def get_schema_policies(schema_name: str, include_inherited: bool = False) -> list[Any]:
    """
    Get all policies for a specific schema.

    Args:
        schema_name: Full schema name (catalog.schema)
        include_inherited: Whether to include inherited policies

    Returns:
        list[Any]: list of policies for the schema
    """
    return list_abac_policies(
        securable_object=schema_name, securable_type="schema", include_inherited=include_inherited
    )


def get_catalog_policies(catalog_name: str, include_inherited: bool = False) -> list[Any]:
    """
    Get all policies for a specific catalog.

    Args:
        catalog_name: Catalog name
        include_inherited: Whether to include inherited policies

    Returns:
        list[Any]: list of policies for the catalog
    """
    return list_abac_policies(
        securable_object=catalog_name, securable_type="catalog", include_inherited=include_inherited
    )


# Convenience functions for policy management
def create_abac_policy(
    name: str, securable_type: str, securable_fullname: str, policy_type: str, principals: list[str], **kwargs
) -> PolicyInfo:
    """
    Create a new ABAC policy using the global interface.

    Args:
        name: Name of the policy
        securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
        securable_fullname: Full name of the securable object
        policy_type: Type of policy ('POLICY_TYPE_COLUMN_MASK' or 'POLICY_TYPE_ROW_FILTER')
        principals: list of principals to apply the policy to
        **kwargs: Additional policy configuration parameters

    Returns:
        PolicyInfo: The created policy
    """
    return abac_policies.create_policy(
        name=name,
        securable_type=securable_type,
        securable_fullname=securable_fullname,
        policy_type=policy_type,
        principals=principals,
        **kwargs,
    )


def update_abac_policy(securable_type: str, securable_fullname: str, policy_name: str, **kwargs) -> PolicyInfo:
    """
    Update an existing ABAC policy using the global interface.

    Args:
        securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
        securable_fullname: Full name of the securable object
        policy_name: Name of the policy to update
        **kwargs: Policy update parameters

    Returns:
        PolicyInfo: The updated policy
    """
    return abac_policies.update_policy(
        securable_type=securable_type, securable_fullname=securable_fullname, policy_name=policy_name, **kwargs
    )


def delete_abac_policy(securable_type: str, securable_fullname: str, policy_name: str) -> DeletePolicyResponse:
    """
    Delete an ABAC policy using the global interface.

    Args:
        securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
        securable_fullname: Full name of the securable object
        policy_name: Name of the policy to delete

    Returns:
        DeletePolicyResponse: Response from the delete operation
    """
    return abac_policies.delete_policy(
        securable_type=securable_type, securable_fullname=securable_fullname, policy_name=policy_name
    )


def get_abac_policy(securable_type: str, securable_fullname: str, policy_name: str) -> PolicyInfo:
    """
    Get a specific ABAC policy by name using the global interface.

    Args:
        securable_type: Type of securable ('catalog', 'schema', 'table', etc.)
        securable_fullname: Full name of the securable object
        policy_name: Name of the policy to retrieve

    Returns:
        PolicyInfo: The policy information
    """
    return abac_policies.get_policy(
        securable_type=securable_type, securable_fullname=securable_fullname, policy_name=policy_name
    )
