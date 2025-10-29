# ABAC (Attribute-Based Access Control)

A Python project for implementing Attribute-Based Access Control (ABAC) systems.

## Description

This project provides a foundation for building ABAC systems in Python, using modern development practices and tools managed by Hatch.

## Installation

```bash
pip install -e .
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
│   └── abac/
│       ├── __init__.py
│       ├── __about__.py
│       └── core.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── pyproject.toml
└── README.md
```

## Usage

```python
from abac.core import ABACPolicy, hello_abac

# Basic usage
print(hello_abac())

# Create a policy
policy = ABACPolicy("example_policy")
policy.add_rule("allow if subject.role == 'admin'")

# Evaluate policy
subject_attrs = {"role": "admin"}
resource_attrs = {"type": "document"}
action_attrs = {"action": "read"}

if policy.evaluate(subject_attrs, resource_attrs, action_attrs):
    print("Access granted!")
else:
    print("Access denied!")
```

## Testing

The project includes comprehensive test coverage for all ABAC policies functionality:

- **33 tests** covering all CRUD operations
- **100% pass rate** with full functionality coverage
- **Integration tests** for end-to-end workflows
- **Error handling** and edge case validation

Run tests with:
```bash
cd tests
python -m pytest test_abac_policies.py test_abac_policies_integration.py -v
```

See `tests/TEST_COVERAGE_SUMMARY.md` for detailed coverage information.

## Documentation

- **API Reference**: `docs/ABAC_POLICIES_CRUD.md` - Complete interface documentation
- **Demo Scripts**: `demo_abac_policies_crud.py` - Working examples
- **Test Coverage**: `tests/TEST_COVERAGE_SUMMARY.md` - Test coverage details