# ABAC Policies Interface - Enhanced CRUD Operations

This document describes the enhanced ABAC (Attribute-Based Access Control) policies interface for Databricks Unity Catalog, now supporting full CRUD (Create, Read, Update, Delete) operations.

## Overview

The ABAC policies interface provides a comprehensive Python API for managing Unity Catalog policies, including:

- **Column Mask Policies**: Control how sensitive data in columns is displayed to users
- **Row Filter Policies**: Control which rows users can see based on conditions

## Features

### Complete CRUD Operations
- **Create**: Create new column mask and row filter policies
- **Read**: List and retrieve existing policies with filtering options
- **Update**: Modify existing policies with new configurations
- **Delete**: Remove policies from securable objects

### Flexible Interface
- **Class-based**: `ABACPoliciesInterface` class for object-oriented usage
- **Functional**: Convenience functions for quick operations
- **Type-safe**: Full type hints and validation

### Advanced Features
- Policy inheritance handling
- Principal and exception lists
- Custom function arguments
- Conditional policy application
- Column matching configurations

## Quick Start

### Basic Usage

```python
from src.abac.abac import create_abac_policy, list_abac_policies, delete_abac_policy

# Create a column mask policy
policy = create_abac_policy(
    name="ssn_mask",
    securable_type="table",
    securable_fullname="hr.employees.personal_data",
    policy_type="POLICY_TYPE_COLUMN_MASK",
    principals=["group:hr_analysts"],
    column_mask_function="mask",
    column_mask_on_column="ssn",
    comment="Mask SSN for HR analysts"
)

# List policies for a table
policies = list_abac_policies(
    securable_object="hr.employees.personal_data",
    securable_type="table"
)

# Delete a policy
delete_abac_policy(
    securable_type="table",
    securable_fullname="hr.employees.personal_data",
    policy_name="ssn_mask"
)
```

### Advanced Usage with Class Interface

```python
from databricks.sdk import WorkspaceClient
from src.abac.abac import ABACPoliciesInterface

# Initialize interface
client = WorkspaceClient()
policies = ABACPoliciesInterface(client)

# Create a complex row filter policy
policy = policies.create_policy(
    name="department_access",
    securable_type="table",
    securable_fullname="company.employees.all_data",
    policy_type="POLICY_TYPE_ROW_FILTER",
    principals=["group:managers"],
    row_filter_function="department_filter",
    row_filter_using_args=[
        {"parameter_name": "user_department", "parameter_value": "current_user_department()"}
    ],
    when_condition="employment_status = 'ACTIVE'",
    except_principals=["group:hr_admins"],
    comment="Managers can only see employees in their department"
)
```

## API Reference

### Core Methods

#### `create_policy()`
Create a new ABAC policy.

**Parameters:**
- `name` (str): Policy name
- `securable_type` (str): Type of securable ('catalog', 'schema', 'table', etc.)
- `securable_fullname` (str): Full name of the securable object
- `policy_type` (str): 'POLICY_TYPE_COLUMN_MASK' or 'POLICY_TYPE_ROW_FILTER'
- `principals` (List[str]): List of principals to apply policy to
- `column_mask_function` (Optional[str]): Function for column masking
- `column_mask_on_column` (Optional[str]): Column to mask
- `row_filter_function` (Optional[str]): Function for row filtering
- `when_condition` (Optional[str]): SQL condition for policy application
- `except_principals` (Optional[List[str]]): Principals to exclude
- `comment` (Optional[str]): Policy description

#### `update_policy()`
Update an existing ABAC policy.

**Parameters:**
- `securable_type` (str): Type of securable
- `securable_fullname` (str): Full name of securable object
- `policy_name` (str): Name of policy to update
- Additional parameters same as `create_policy()` (all optional for updates)

#### `delete_policy()`
Delete an ABAC policy.

**Parameters:**
- `securable_type` (str): Type of securable
- `securable_fullname` (str): Full name of securable object
- `policy_name` (str): Name of policy to delete

#### `get_policy()`
Retrieve a specific policy by name.

**Parameters:**
- `securable_type` (str): Type of securable
- `securable_fullname` (str): Full name of securable object
- `policy_name` (str): Name of policy to retrieve

#### `list_policies()`
List policies with optional filtering.

**Parameters:**
- `securable_type` (Optional[str]): Filter by securable type
- `securable_fullname` (Optional[str]): Filter by securable object
- `include_inherited` (bool): Include inherited policies (default: False)

## Policy Types

### Column Mask Policies
Control how data in specific columns is displayed to users.

**Required Parameters:**
- `policy_type`: "POLICY_TYPE_COLUMN_MASK"
- `column_mask_function`: Name of the masking function
- `column_mask_on_column`: Column to apply masking to

**Example:**
```python
create_abac_policy(
    name="email_mask",
    securable_type="table",
    securable_fullname="users.profiles.contacts",
    policy_type="POLICY_TYPE_COLUMN_MASK",
    principals=["group:support"],
    column_mask_function="email_mask",
    column_mask_on_column="email_address",
    column_mask_using_args=[
        {"parameter_name": "mask_domain", "parameter_value": "true"}
    ]
)
```

### Row Filter Policies
Control which rows users can see based on conditions.

**Required Parameters:**
- `policy_type`: "POLICY_TYPE_ROW_FILTER"
- `row_filter_function`: Name of the filtering function

**Example:**
```python
create_abac_policy(
    name="regional_filter",
    securable_type="table",
    securable_fullname="sales.data.transactions",
    policy_type="POLICY_TYPE_ROW_FILTER",
    principals=["group:regional_managers"],
    row_filter_function="region_access",
    row_filter_using_args=[
        {"parameter_name": "user_region", "parameter_value": "get_user_region()"}
    ],
    when_condition="transaction_date >= '2024-01-01'"
)
```

## Convenience Functions

The module provides convenience functions for common operations:

- `create_abac_policy()`: Create policies using global interface
- `update_abac_policy()`: Update policies using global interface
- `delete_abac_policy()`: Delete policies using global interface
- `get_abac_policy()`: Get specific policies using global interface
- `list_abac_policies()`: List policies using global interface
- `get_table_policies()`: Get policies for specific tables
- `get_schema_policies()`: Get policies for specific schemas
- `get_catalog_policies()`: Get policies for specific catalogs

## Error Handling

The interface includes comprehensive error handling:

```python
try:
    policy = create_abac_policy(
        name="test_policy",
        securable_type="table",
        securable_fullname="test.table",
        policy_type="POLICY_TYPE_COLUMN_MASK",
        principals=["user@example.com"],
        # Missing required column_mask_function - will raise ValueError
    )
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## Type Safety

The interface provides full type hints for better IDE support and error detection:

```python
from src.abac.abac import ABACPoliciesInterface
from databricks.sdk.service.catalog import PolicyInfo
from typing import List

def process_policies(policies_interface: ABACPoliciesInterface) -> List[PolicyInfo]:
    return policies_interface.list_policies(
        securable_type="table",
        include_inherited=True
    )
```

## Important Notes

### API Availability
The Unity Catalog Policies API may be disabled in some environments. The interface is designed to work when the API becomes available.

### Authentication
Ensure your Databricks workspace client is properly authenticated with the necessary permissions to manage Unity Catalog policies.

### Permissions
Policy management requires appropriate Unity Catalog permissions:
- `CREATE` on the securable object for creating policies
- `MODIFY` on the securable object for updating policies
- `DELETE` on the securable object for deleting policies

## Migration from Previous Version

If you were using the basic listing functionality, your code remains compatible:

```python
# This still works
from src.abac.abac import list_abac_policies
policies = list_abac_policies(securable_object="my.table", securable_type="table")

# New functionality available
from src.abac.abac import create_abac_policy, update_abac_policy
# ... use new functions
```

## Complete Example

Here's a complete example showing policy lifecycle management:

```python
from src.abac.abac import (
    create_abac_policy, 
    update_abac_policy, 
    get_abac_policy, 
    delete_abac_policy,
    list_abac_policies
)

# 1. Create a policy
policy = create_abac_policy(
    name="sensitive_data_policy",
    securable_type="table",
    securable_fullname="finance.transactions.payments",
    policy_type="POLICY_TYPE_COLUMN_MASK",
    principals=["group:finance_analysts"],
    column_mask_function="partial_mask",
    column_mask_on_column="account_number",
    comment="Mask account numbers for analysts"
)
print(f"Created policy: {policy.name}")

# 2. List all policies
policies = list_abac_policies(
    securable_object="finance.transactions.payments",
    securable_type="table"
)
print(f"Total policies: {len(policies)}")

# 3. Update the policy
updated_policy = update_abac_policy(
    securable_type="table",
    securable_fullname="finance.transactions.payments",
    policy_name="sensitive_data_policy",
    principals=["group:finance_analysts", "group:auditors"],
    comment="Updated to include auditors"
)
print(f"Updated policy principals: {updated_policy.to_principals}")

# 4. Get specific policy
specific_policy = get_abac_policy(
    securable_type="table",
    securable_fullname="finance.transactions.payments",
    policy_name="sensitive_data_policy"
)
print(f"Retrieved policy: {specific_policy.name}")

# 5. Clean up
delete_response = delete_abac_policy(
    securable_type="table",
    securable_fullname="finance.transactions.payments",
    policy_name="sensitive_data_policy"
)
print("Policy deleted successfully")
```

This enhanced interface provides a complete solution for managing ABAC policies in Databricks Unity Catalog with full CRUD capabilities, type safety, and comprehensive error handling.