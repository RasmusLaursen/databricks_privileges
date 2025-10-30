# Service Requests Documentation

## Overview

Service requests are YAML files that define privilege grants for Databricks Unity Catalog resources. They provide a declarative way to manage access control through version-controlled configuration files.

## Table of Contents

- [Service Request Structure](#service-request-structure)
- [Creating a Service Request](#creating-a-service-request)
- [Service Request Status](#service-request-status)
- [Principal Types](#principal-types)
- [Resource Types](#resource-types)
- [Available Privileges](#available-privileges)
- [Validation](#validation)
- [Applying Service Requests](#applying-service-requests)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Service Request Structure

A service request file has the following structure:

```yaml
request-name: <string>
request-type: <string>
request-status: <active|decomissioned>

requests:
  - principal:
      type: <group|user|service_principal>
      id: <principal-name>
    resource: <resource-path>
    privileges:
      - <PRIVILEGE_1>
      - <PRIVILEGE_2>
```

### Required Fields

- **request-name**: A descriptive name for the service request
- **request-type**: Type of request (e.g., "access")
- **request-status**: Current status - either `active` or `decomissioned`
- **requests**: List of privilege grant requests

### Request Item Fields

Each item in the `requests` list must have:

- **principal.type**: Type of principal (group, user, or service_principal)
- **principal.id**: Name/ID of the principal
- **resource**: Full path to the Unity Catalog resource
- **privileges**: List of privileges to grant

## Creating a Service Request

### 1. Choose the Correct Directory

Place your service request files in:
```
service_requests/
├── priviliges/     # For privilege-based requests
└── abac/           # For ABAC policy requests
```

### 2. Create a YAML File

Create a new `.yml` file with a descriptive name:

```bash
service_requests/priviliges/analytics_team_access.yml
```

### 3. Define the Service Request

```yaml
request-name: Analytics Team Data Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: analytics_team
    resource: production.sales.transactions
    privileges:
      - SELECT
      - USE_SCHEMA
```

## Service Request Status

### Active

Status: `active`

- Service request is currently in effect
- Privileges will be granted when applied
- Use this for ongoing access requirements

```yaml
request-status: active
```

### Decommissioned

Status: `decomissioned`

- Service request is being retired
- Privileges will be **removed** when applied
- Use this to revoke access in a controlled manner

```yaml
request-status: decomissioned
```

## Principal Types

### Group

The most common principal type for team-based access:

```yaml
principal:
  type: group
  id: data_engineers
```

### User

For individual user access:

```yaml
principal:
  type: user
  id: user@company.com
```

### Service Principal

For application/service access:

```yaml
principal:
  type: service_principal
  id: my-service-principal
```

## Resource Types

Resources are specified using Unity Catalog three-level namespace:

### Catalog

Format: `catalog_name`

```yaml
resource: production
```

### Schema

Format: `catalog.schema`

```yaml
resource: production.sales
```

### Table

Format: `catalog.schema.table`

```yaml
resource: production.sales.transactions
```

### Function

Format: `catalog.schema.function`

```yaml
resource: production.analytics.calculate_revenue
```

### Volume

Format: `catalog.schema.volume`

```yaml
resource: production.raw_data.landing_zone
```

## Available Privileges

### Catalog Privileges

- `USE_CATALOG` - Access the catalog
- `CREATE_SCHEMA` - Create schemas in the catalog
- `CREATE_FUNCTION` - Create functions
- `CREATE_TABLE` - Create tables
- `CREATE_VOLUME` - Create volumes

### Schema Privileges

- `USE_SCHEMA` - Access the schema
- `CREATE_TABLE` - Create tables in the schema
- `CREATE_FUNCTION` - Create functions
- `CREATE_VOLUME` - Create volumes

### Table/View Privileges

- `SELECT` - Read data
- `MODIFY` - Insert, update, delete data
- `READ_METADATA` - Read table metadata

### Function Privileges

- `EXECUTE` - Execute the function

### Volume Privileges

- `READ_VOLUME` - Read files
- `WRITE_VOLUME` - Write files

## Automatic Parent Privileges

When granting privileges on lower-level resources (tables, views, functions, volumes), the system automatically grants required parent privileges:

- Granting `SELECT` on a table automatically grants:
  - `USE_CATALOG` on the parent catalog
  - `USE_SCHEMA` on the parent schema

This ensures users can actually access the resources they're granted privileges on.

## Validation

### Basic Validation

Validates YAML structure and required fields:

```bash
hatch run validate_service_request:run
```

### Databricks Validation

Validates that principals and resources exist in Databricks:

```bash
hatch run validate_service_request:databricks
```

This checks:
- Principal exists in Databricks
- Resource exists in Unity Catalog
- Resource type is correctly identified

### Validate All Files

Validate all service requests in the directory:

```bash
hatch run validate_all_service_requests:run
```

With verbose output:

```bash
hatch run validate_all_service_requests:verbose
```

## Applying Service Requests

### Apply All Active Requests

```bash
hatch run apply_privileges:run
```

This will:
1. Parse all service request files in `service_requests/priviliges/`
2. Grant privileges for requests with `status: active`
3. Revoke privileges for requests with `status: decomissioned`
4. Automatically grant parent USE privileges

### Environment Variables

Set these environment variables for Databricks authentication:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
```

Or use Databricks CLI authentication (recommended).

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
request-name: Marketing Team Q4 Campaign Data Access

# Avoid
request-name: Request 123
```

### 2. Group Related Access

Group related privileges in a single service request:

```yaml
request-name: Data Science Team Analytics Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: data_science
    resource: production.analytics.customer_features
    privileges:
      - SELECT
  - principal:
      type: group
      id: data_science
    resource: production.analytics.product_features
    privileges:
      - SELECT
```

### 3. Use Groups Over Individual Users

```yaml
# Preferred
principal:
  type: group
  id: analytics_team

# Avoid for team access
principal:
  type: user
  id: individual.user@company.com
```

### 4. Version Control Everything

- Commit service request files to Git
- Use pull requests for changes
- Enable validation in CI/CD pipelines

### 5. Use Decommissioned Status

When removing access, set status to `decomissioned` rather than deleting the file:

```yaml
request-status: decomissioned  # This will revoke the privileges
```

After privileges are revoked, you can safely delete the file.

### 6. Document the Purpose

Use clear request names that explain the business purpose:

```yaml
request-name: Q4 2025 Financial Reporting - Finance Team Read Access
request-type: access
request-status: active
```

## Examples

### Example 1: Simple Table Access

```yaml
request-name: Analysts Read Access to Sales Data
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: business_analysts
    resource: production.sales.transactions
    privileges:
      - SELECT
```

### Example 2: Multi-Resource Access

```yaml
request-name: Data Engineering Pipeline Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: data_engineers
    resource: bronze.raw_data.events
    privileges:
      - SELECT
  - principal:
      type: group
      id: data_engineers
    resource: silver.processed_data.events
    privileges:
      - SELECT
      - MODIFY
  - principal:
      type: group
      id: data_engineers
    resource: gold.analytics.daily_metrics
    privileges:
      - SELECT
      - MODIFY
```

### Example 3: Schema-Level Access

```yaml
request-name: ML Team Model Development Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: ml_engineers
    resource: dev.ml_features
    privileges:
      - USE_SCHEMA
      - CREATE_TABLE
      - CREATE_FUNCTION
```

### Example 4: Service Principal Access

```yaml
request-name: Production ETL Service Access
request-type: access
request-status: active

requests:
  - principal:
      type: service_principal
      id: etl-service
    resource: production.staging.landing
    privileges:
      - SELECT
      - MODIFY
```

### Example 5: Decommissioning Access

```yaml
request-name: Temporary Q3 Audit Access
request-type: access
request-status: decomissioned  # Will revoke privileges

requests:
  - principal:
      type: group
      id: external_auditors
    resource: production.financial.ledger
    privileges:
      - SELECT
```

## Workflow Integration

### GitHub Actions Validation

Add validation to your CI/CD pipeline:

```yaml
- name: Validate Service Requests
  run: hatch run validate_service_request:databricks
```

### Pull Request Process

1. Create service request file
2. Commit and push to feature branch
3. Open pull request
4. Automated validation runs
5. Review and approve
6. Merge to main
7. Apply privileges automatically or manually

## Troubleshooting

### Common Errors

**Error: "Group 'xyz' does not exist"**
- Verify the group exists in Databricks
- Check for typos in the group name
- Use exact group name (case-sensitive)

**Error: "Table 'catalog.schema.table' does not exist"**
- Verify the resource exists in Unity Catalog
- Check the full three-part name
- Ensure you have access to view the resource

**Error: "Invalid privilege 'XYZ' for resource type 'table'"**
- Check the available privileges for that resource type
- See [Available Privileges](#available-privileges) section

### Validation vs. Application

- **Validation** checks structure and existence without making changes
- **Application** actually grants/revokes privileges in Databricks

Always validate before applying:

```bash
# 1. Validate first
hatch run validate_service_request:databricks

# 2. If validation passes, apply
hatch run apply_privileges:run
```

## Additional Resources

- [ABAC Policies Documentation](ABAC_POLICIES_CRUD.md)
- [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Privilege Types Reference](https://docs.databricks.com/data-governance/unity-catalog/manage-privileges/privileges.html)
