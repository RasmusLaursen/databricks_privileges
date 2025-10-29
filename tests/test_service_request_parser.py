"""
Unit tests for service request parsing functionality.
"""

import os
import tempfile

import pytest

from privileges.service_requests.parser import Principal, ServiceRequest, ServiceRequestItem, ServiceRequestParser


class TestServiceRequestParser:
    """Test cases for service request parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ServiceRequestParser()
        self.valid_yaml_content = {
            "request-name": "Test Request",
            "request-type": "access",
            "request-status": "pending",
            "requests": [
                {
                    "principal": {"type": "user", "id": "user-123"},
                    "resource": "database.table",
                    "privileges": ["SELECT"],
                }
            ],
        }

    def test_parse_valid_service_request(self):
        """Test parsing a valid service request YAML content."""
        service_request = self.parser._parse_yaml_content(self.valid_yaml_content, "test.yml")

        assert isinstance(service_request, ServiceRequest)
        assert service_request.name == "Test Request"
        assert service_request.request_type == "access"
        assert len(service_request.requests) == 1

        request_item = service_request.requests[0]
        assert request_item.principal.type == "user"
        assert request_item.principal.id == "user-123"
        assert request_item.resource == "database.table"
        assert request_item.privileges == ["SELECT"]

    def test_parse_missing_required_keys(self):
        """Test parsing YAML with missing required keys."""
        invalid_yaml = {
            "request-name": "Test Request"
            # Missing 'request-type' and 'requests'
        }

        with pytest.raises(ValueError, match="Missing required keys"):
            self.parser._parse_yaml_content(invalid_yaml, "test.yml")

    def test_parse_invalid_requests_format(self):
        """Test parsing YAML with invalid requests format."""
        invalid_yaml = self.valid_yaml_content.copy()
        invalid_yaml["requests"] = "not a list"

        with pytest.raises(ValueError, match="requests must be a list"):
            self.parser._parse_yaml_content(invalid_yaml, "test.yml")

    def test_parse_invalid_principal_format(self):
        """Test parsing YAML with invalid principal format."""
        invalid_yaml = self.valid_yaml_content.copy()
        invalid_yaml["requests"][0]["principal"] = "not a dict"

        with pytest.raises(ValueError, match=r"Principal in request item .* must be a dictionary"):
            self.parser._parse_yaml_content(invalid_yaml, "test.yml")

    def test_validate_service_request_valid(self):
        """Test validation of a valid service request."""
        service_request = ServiceRequest(
            name="Test Request",
            request_type="access",
            request_status="pending",
            requests=[
                ServiceRequestItem(
                    principal=Principal(type="user", id="user-123"), resource="database.table", privileges=["SELECT"]
                )
            ],
        )

        errors = self.parser.validate_service_request(service_request)
        assert errors == []

    def test_validate_service_request_invalid(self):
        """Test validation of an invalid service request."""
        service_request = ServiceRequest(
            name="",  # Empty name
            request_type="",  # Empty type
            request_status="",  # Empty status
            requests=[
                ServiceRequestItem(
                    principal=Principal(type="", id=""), resource="", privileges=[]  # Empty principal  # Empty resource
                )
            ],
        )

        errors = self.parser.validate_service_request(service_request)
        assert len(errors) > 0
        assert any("name cannot be empty" in error for error in errors)
        assert any("type cannot be empty" in error for error in errors)

    def test_get_service_request_summary(self):
        """Test generating service request summary."""
        service_request = ServiceRequest(
            name="Test Request",
            request_type="access",
            request_status="pending",
            requests=[
                ServiceRequestItem(
                    principal=Principal(type="user", id="user-123"), resource="database.table", privileges=["SELECT"]
                )
            ],
        )

        summary = self.parser.get_service_request_summary(service_request)

        assert summary["name"] == "Test Request"
        assert summary["type"] == "access"
        assert summary["total_requests"] == 1
        assert "database.table" in summary["resources"]
        assert "user:user-123" in summary["principals"]
        assert "SELECT" in summary["privileges"]

    def test_parse_service_request_file(self):
        """Test parsing a service request from file."""
        # Create a temporary YAML file
        yaml_content = """
request-name: Test File Request
request-type: access
request-status: pending
requests:
  - principal:
      type: user
      id: user-456
    resource: database.table
    privileges:
      - SELECT
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name

        try:
            service_request = self.parser.parse_service_request_file(temp_file)
            assert service_request.name == "Test File Request"
            assert service_request.request_type == "access"
            assert len(service_request.requests) == 1
        finally:
            os.unlink(temp_file)
