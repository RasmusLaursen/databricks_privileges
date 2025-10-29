# GitHub Integration for Service Requests

This module provides functionality to detect and process service request files that are part of the current pull request.

## Features

- **PR Detection**: Automatically detect if running in a pull request context
- **Changed File Detection**: Get list of files changed in the current PR
- **Service Request Filtering**: Filter changed files to only include service request YAML files
- **Validation**: Validate service requests before processing
- **GitHub Actions Integration**: Works seamlessly in GitHub Actions workflows

## Usage

### Basic Usage

```python
from privileges.github.github import get_pr_service_requests, validate_pr_service_requests

# Get all service requests from the current PR
service_requests = get_pr_service_requests()

# Get and validate service requests
valid_requests, errors = validate_pr_service_requests()
```

### Advanced Usage with GitHubIntegration Class

```python
from privileges.github.github import GitHubIntegration

# Initialize integration
github = GitHubIntegration()

# Check if we're in a PR
if github.is_in_pull_request():
    # Get changed files
    changed_files = github.get_changed_files("main")
    
    # Filter to service request files
    sr_files = github.filter_service_request_files(changed_files)
    
    # Get parsed service requests
    requests = github.get_pr_service_requests("main")
```

## Command Line Tools

### Validate PR Privileges Script

A dedicated script for validating service requests from PR changes:

```bash
# Basic validation
hatch run validate_service_request:run

# Detailed validation with verbose output
hatch run validate_service_request:verbose

# Alternative command (same as run)
hatch run validate_service_request:validate
```

### Example Script

Use the example script to explore functionality:

```bash
python examples/pr_service_requests.py
```

## GitHub Actions Integration

The integration automatically detects GitHub Actions environment and uses appropriate methods:

- Uses `GITHUB_ACTIONS` environment variable to detect CI environment
- Uses `GITHUB_EVENT_NAME` to detect pull request events
- Uses `GITHUB_BASE_REF` to determine base branch for comparison

### Environment Variables

- `GITHUB_ACTIONS`: Set by GitHub Actions automatically
- `GITHUB_EVENT_NAME`: Event that triggered the workflow
- `GITHUB_BASE_REF`: Base branch for pull requests
- `BASE_BRANCH`: Override base branch (defaults to "main")

## Workflow Integration

Add to your GitHub Actions workflow:

```yaml
jobs:
  validate-pr-privileges:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for git diff
      - name: Validate PR Service Requests
        run: hatch run validate_service_request:run
        
  validate-pr-privileges-verbose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for git diff
      - name: Validate PR Service Requests (Verbose)
        run: hatch run validate_service_request:verbose
```

## API Reference

### GitHubIntegration Class

#### Methods

- `get_changed_files(base_branch="main")`: Get files changed in PR
- `get_changed_files_from_env()`: Get changed files from GitHub Actions environment
- `filter_service_request_files(file_paths)`: Filter to service request files only
- `get_pr_service_requests(base_branch="main")`: Get parsed service requests from PR
- `validate_pr_service_requests(base_branch="main")`: Get and validate service requests
- `is_in_pull_request()`: Check if in PR context

### Convenience Functions

- `get_pr_service_requests(repo_root=None, base_branch="main")`: Get PR service requests
- `validate_pr_service_requests(repo_root=None, base_branch="main")`: Validate PR service requests

## Error Handling

The integration includes comprehensive error handling:

- Git command failures are caught and logged
- Invalid service request files are logged but don't stop processing of other files
- Validation errors are collected and returned for review
- Network issues and GitHub API problems are handled gracefully

## Testing

### Script Features

The validation script provides:

- **PR Context Detection**: Only runs when in a pull request
- **File Change Analysis**: Shows which service request files changed
- **Comprehensive Validation**: Validates syntax and content of service requests
- **Detailed Reporting**: Shows validation results with optional verbose mode
- **CI/CD Integration**: Returns appropriate exit codes for pipeline integration
- **Rich Logging**: Clear success/failure indicators

### Exit Codes

- `0`: Success - all service requests are valid or no service requests found
- `1`: Failure - validation errors found or script execution failed

### Testing

Run the GitHub integration tests:

```bash
hatch run unit-test:run tests/test_github_integration.py -v
```

All functionality is thoroughly tested with both unit tests and integration scenarios.