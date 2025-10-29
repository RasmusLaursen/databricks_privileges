"""
ABAC Policies Module

This module provides a comprehensive interface for managing Databricks Unity Catalog
ABAC (Attribute-Based Access Control) policies.
"""

from abac.abac.abac import (
    ABACPoliciesInterface,
    abac_policies,
    create_abac_policy,
    delete_abac_policy,
    get_abac_policy,
    get_catalog_policies,
    get_schema_policies,
    get_table_policies,
    list_abac_policies,
    update_abac_policy,
)

__all__ = [
    "ABACPoliciesInterface",
    "abac_policies",
    "create_abac_policy",
    "delete_abac_policy",
    "get_abac_policy",
    "get_catalog_policies",
    "get_schema_policies",
    "get_table_policies",
    "list_abac_policies",
    "update_abac_policy",
]
