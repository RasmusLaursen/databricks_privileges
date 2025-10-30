# ABAC (Attribute-Based Access Control)

A Python project for managing Databricks Unity Catalog privileges and implementing Attribute-Based Access Control (ABAC) systems.

## Description

This project provides tools for:
- Managing Databricks Unity Catalog privileges through declarative service requests
- Implementing ABAC policies for fine-grained access control *(under development)*
- Automated validation and application of access control changes
- Integration with GitHub Actions for CI/CD workflows

## Quick Start

### Installation

```bash
pip install -e .
```

### Create a Service Request

Create a YAML file in `service_requests/priviliges/`:

```yaml
request-name: Analytics Team Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: analytics_team
    resource: production.sales.transactions
    privileges:
      - SELECT
```

### Validate and Apply

```bash
# Validate service requests
hatch run validate_service_request:databricks

# Apply privileges
hatch run apply_privileges:run
```

## Documentation

- **[Service Requests Guide](docs/SERVICE_REQUESTS.md)** - Complete guide to managing privileges
- **[ABAC Policies](docs/ABAC_POLICIES_CRUD.md)** - ABAC policy documentation
- **[Test Coverage](tests/TEST_COVERAGE_SUMMARY.md)** - Test coverage details

## Installation

```bash
pip install -e .
```

## Available Commands

### Service Request Management

```bash
# Validate service requests (structure only)
hatch run validate_service_request:run

# Validate with Databricks checks
hatch run validate_service_request:databricks

# Validate all service request files
hatch run validate_all_service_requests:run

# Apply active service requests
hatch run apply_privileges:run
```

### Testing

```bash
# Run all tests
hatch run unit-test:run

# Run with coverage
hatch run unit-test:coverage

# Run specific test files
hatch run unit-test:run-parser
hatch run unit-test:run-abac
```

### Code Quality

```bash
# Run linting and formatting
hatch run lint:all

# Format code
hatch run lint:fmt

# Type checking
hatch run lint:typing
```

## Development

This project uses [Hatch](https://hatch.pypa.io/) for project management.

### Setting up the development environment

```bash
# Install Hatch if you haven't already
pip install hatch

# Create and enter a shell in the default environment
hatch shell

# Or run commands in the environment
hatch run python -c "import abac; print('ABAC imported successfully!')"
```

### Running tests

```bash
# Run tests
hatch run test

# Run tests with coverage
hatch run cov

# Run tests in all Python versions
hatch run all:test
```

### Code quality

```bash
# Run linting and formatting
hatch run lint:all

# Format code
hatch run lint:fmt

# Type checking
hatch run lint:typing
```

### Available environments

- `default`: For running tests and general development
- `lint`: For code quality tools (black, ruff, mypy)
- `all`: Matrix environment for testing across Python versions

## Project Structure

```
├── src/
│   └── privileges/
│       ├── __init__.py
│       ├── __about__.py
│       ├── apply_priviliges.py         # Apply service requests
│       ├── validate_service_request.py # Validate PR service requests
│       ├── abac/                       # ABAC policies
│       ├── grants/                     # Grant management
│       ├── groups/                     # Group utilities
│       ├── privileges/                 # Privilege definitions
│       ├── service_requests/           # Service request parser
│       └── workspace/                  # Databricks workspace client
├── service_requests/
│   ├── priviliges/                    # Privilege service requests
│   └── abac/                          # ABAC policy requests
├── tests/
│   ├── test_service_request_parser.py
│   ├── test_abac_policies.py
│   └── test_github_integration.py
├── docs/
│   ├── SERVICE_REQUESTS.md            # Service request guide
│   └── ABAC_POLICIES_CRUD.md         # ABAC documentation
└── pyproject.toml
```

## Features

### Declarative Access Control

Define privileges in version-controlled YAML files:

```yaml
request-name: Data Team Access
request-type: access
request-status: active

requests:
  - principal:
      type: group
      id: data_engineers
    resource: production.analytics.metrics
    privileges:
      - SELECT
      - MODIFY
```

### Automatic Parent Privileges

When granting table-level access, the system automatically grants:
- `USE_CATALOG` on the parent catalog
- `USE_SCHEMA` on the parent schema

### Validation

- **Structure validation** - YAML syntax and required fields
- **Databricks validation** - Principal and resource existence checks
- **Privilege validation** - Correct privileges for resource types

### GitHub Integration

- Automatic detection of service request changes in pull requests
- CI/CD integration for automated validation
- Support for both GitHub API and git fallback

## Usage Examples

### Example 1: Grant Table Access

```yaml
request-name: Analysts Read Sales Data
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

Apply with:
```bash
hatch run apply_privileges:run
```

### Example 2: Revoke Access

Change status to `decomissioned`:

```yaml
request-name: Temporary Audit Access
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

### Example 3: Validate Before Applying

```bash
# Basic validation
hatch run validate_all_service_requests:run

# With Databricks checks
hatch run validate_service_request:databricks

# Apply if validation passes
hatch run apply_privileges:run
```

## Testing

The project includes comprehensive test coverage:

- **57 tests** passing with full functionality coverage
- Service request parsing and validation
- GitHub integration (API and git fallback)
- ABAC policy CRUD operations
- Privilege management

Run tests with:
```bash
hatch run unit-test:run
```

## Authentication

### Databricks CLI (Recommended)

```bash
databricks configure --token
```

### Environment Variables

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=your-token
```

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Validate Service Requests
  run: hatch run validate_service_request:databricks
  env:
    DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
    DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}

- name: Apply Privileges
  if: github.ref == 'refs/heads/main'
  run: hatch run apply_privileges:run
```

## Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[Service Requests Guide](docs/SERVICE_REQUESTS.md)** - Complete guide to managing privileges
- **[ABAC Policies](docs/ABAC_POLICIES_CRUD.md)** - ABAC policy documentation *(under development)*
- **[Test Coverage](tests/TEST_COVERAGE_SUMMARY.md)** - Test coverage details## License

This project is licensed under the terms specified in the LICENSE file.