# Quick Start Guide

This guide will help you get started with managing Databricks privileges using service requests.

## Prerequisites

- Python 3.9 or higher
- Databricks workspace access
- Hatch package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RasmusLaursen/databricks_privileges.git
cd databricks_privileges
```

2. Install the project:
```bash
pip install -e .
```

3. Authenticate with Databricks:
```bash
databricks configure --token
```

## Your First Service Request

### Step 1: Create a Service Request File

Create a file `service_requests/priviliges/my_first_request.yml`:

```yaml
request-name: My First Access Grant
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: your_group_name
    resource: your_catalog.your_schema.your_table
    privileges:
      - SELECT
```

Replace:
- `your_group_name` with an actual Databricks group name
- `your_catalog.your_schema.your_table` with an actual table path

### Step 2: Validate the Service Request

Run validation to check for errors:

```bash
# Basic validation (structure only)
hatch run validate_all_service_requests:run

# Validate with Databricks (checks if group and table exist)
hatch run validate_all_service_requests:run --validate-databricks
```

Expected output:
```
Found 1 service request file(s) to validate
Validating: service_requests/priviliges/my_first_request.yml
Valid: service_requests/priviliges/my_first_request.yml
Successfully validated 1 service request(s)
```

### Step 3: Apply the Service Request

```bash
hatch run apply_privileges:run
```

Expected output:
```
Processing Service Request: My First Access Grant
Processing request 1: your_catalog.your_schema.your_table
Successfully applied privileges for your_catalog.your_schema.your_table: USE_CATALOG on your_catalog, USE_SCHEMA on your_catalog.your_schema, SELECT
Successfully applied service requests
```

### Step 4: Verify the Grant

Check in Databricks UI:
1. Navigate to your table in Data Explorer
2. Click on "Permissions"
3. Verify your group has SELECT permission

## Common Tasks

### Grant Multiple Privileges

```yaml
requests:
  - principal:
      type: group
      id: data_engineers
    resource: production.analytics.metrics
    privileges:
      - SELECT
      - MODIFY
```

### Grant Access to Multiple Resources

```yaml
requests:
  - principal:
      type: group
      id: analysts
    resource: production.sales.transactions
    privileges:
      - SELECT
  - principal:
      type: group
      id: analysts
    resource: production.sales.customers
    privileges:
      - SELECT
```

### Revoke Access

Change `request-status` to `decomissioned`:

```yaml
request-name: Temporary Access
request-type: access
request-status: decomissioned  # Changed from 'active'

requests:
  - principal:
      type: group
      id: contractors
    resource: production.temp.data
    privileges:
      - SELECT
```

Then apply:
```bash
hatch run apply_privileges:run
```

## Validation Options

### Validate Structure Only

```bash
hatch run validate_all_service_requests:run
```

### Validate with Databricks Checks

```bash
hatch run validate_service_request:databricks
```

This validates:
- ✓ YAML structure
- ✓ Required fields present
- ✓ Principal exists in Databricks
- ✓ Resource exists in Unity Catalog

### Verbose Output

```bash
hatch run validate_all_service_requests:verbose
```

## Workflow Best Practices

### 1. Always Validate First

```bash
# Validate
hatch run validate_all_service_requests:run

# If validation passes, apply
hatch run apply_privileges:run
```

### 2. Use Version Control

```bash
# Create feature branch
git checkout -b add-analyst-access

# Create service request file
# ... edit service_requests/priviliges/analyst_access.yml

# Commit changes
git add service_requests/
git commit -m "Add analyst access to sales data"

# Push and create PR
git push origin add-analyst-access
```

### 3. Use Descriptive Names

```yaml
# Good
request-name: Q4 2025 Analytics Team Sales Data Access

# Avoid
request-name: Request 1
```

### 4. Group Related Privileges

```yaml
request-name: Data Pipeline Access for ETL Service
request-type: access
request-status: active

requests:
  - principal:
      type: service_principal
      id: etl-pipeline
    resource: bronze.raw.events
    privileges:
      - SELECT
  - principal:
      type: service_principal
      id: etl-pipeline
    resource: silver.processed.events
    privileges:
      - SELECT
      - MODIFY
```

## Troubleshooting

### Error: "Group 'xyz' does not exist"

**Solution**: Verify the group exists in Databricks:
1. Go to Databricks UI → Settings → Identity and Access
2. Click on "Groups"
3. Find your group name (case-sensitive)

### Error: "Resource 'catalog.schema.table' does not exist"

**Solution**: Verify the resource exists:
1. Go to Databricks UI → Data
2. Navigate to catalog → schema → table
3. Copy the exact path (case-sensitive)

### Privileges Not Applied

**Check**:
1. Is `request-status: active`? (not `decomissioned`)
2. Did the command complete successfully?
3. Do you have permission to grant privileges?
4. Is the Databricks token valid?

## Next Steps

- Read the [Complete Service Requests Guide](SERVICE_REQUESTS.md)
- Learn about [ABAC Policies](ABAC_POLICIES_CRUD.md)
- Set up [GitHub Actions Integration](.github/workflows/main.yaml)
- Explore privilege types in [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/manage-privileges/privileges.html)

## Getting Help

- Check the [Service Requests Documentation](SERVICE_REQUESTS.md)
- Review [examples](../service_requests/priviliges/)
- Run tests: `hatch run unit-test:run`
