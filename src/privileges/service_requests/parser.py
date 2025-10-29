"""
Service Request Parser module for ABAC.

This module provides functionality to parse and validate service request YAML files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from privileges.files import yml
from privileges.logger import logging_helper


@dataclass
class Principal:
    """Represents a principal in a service request."""

    type: str
    id: str


@dataclass
class ServiceRequestItem:
    """Represents a single service request item."""

    principal: Principal
    resource: str
    privileges: list[str]


@dataclass
class ServiceRequest:
    """Represents a complete service request."""

    name: str
    request_type: str
    request_status: str
    requests: list[ServiceRequestItem]
    file_info: Optional[dict[str, str]] = None


class ServiceRequestParser:
    """Parser for service request YAML files."""

    def __init__(self):
        """Initialize the service request parser."""
        self.logger = logging_helper.get_logger(__name__)
        self.required_keys = ["request-name", "request-type", "request-status", "requests"]
        self.required_request_keys = ["principal", "resource"]

    def parse_service_request_file(self, file_path: str) -> ServiceRequest:
        """
        Parse a single service request YAML file.

        Args:
            file_path: Path to the service request YAML file

        Returns:
            ServiceRequest: Parsed service request object

        Raises:
            ValueError: If the YAML structure is invalid
            FileNotFoundError: If the file doesn't exist
        """
        self.logger.info(f"Parsing service request file: {file_path}")

        try:
            # Read the YAML file
            yaml_content = yml.read_yaml_file(file_path)

            # Validate required keys
            if not yml.validate_yaml_structure(yaml_content, self.required_keys):
                missing_keys = [key for key in self.required_keys if key not in yaml_content]
                raise ValueError(f"Missing required keys in service request: {missing_keys}")

            # Parse the service request
            service_request = self._parse_yaml_content(yaml_content, file_path)

            self.logger.info(f"Successfully parsed service request: {service_request.name}")
            return service_request

        except Exception as e:
            self.logger.error(f"Error parsing service request file {file_path}: {e}")
            raise

    def parse_service_requests_directory(self, directory_path: str) -> list[ServiceRequest]:
        """
        Parse all service request YAML files from a directory.

        Args:
            directory_path: Path to directory containing service request files

        Returns:
            list[ServiceRequest]: List of parsed service request objects
        """
        self.logger.info(f"Parsing service requests from directory: {directory_path}")

        try:
            yaml_files_content = yml.read_yaml_files_from_directory(directory_path, "*.yml")
            service_requests = []

            for yaml_content in yaml_files_content:
                try:
                    if yml.validate_yaml_structure(yaml_content, self.required_keys):
                        service_request = self._parse_yaml_content(
                            yaml_content, yaml_content.get("_file_info", {}).get("filepath", "unknown")
                        )
                        service_requests.append(service_request)
                    else:
                        self.logger.warning(
                            "Skipping invalid service request file: {}".format(
                                yaml_content.get("_file_info", {}).get("filename", "unknown")
                            )
                        )
                except Exception as e:
                    self.logger.error(f"Error parsing service request: {e}")
                    continue

            self.logger.info(f"Successfully parsed {len(service_requests)} service requests")
            return service_requests

        except Exception as e:
            self.logger.error(f"Error parsing service requests from directory {directory_path}: {e}")
            raise

    def _parse_yaml_content(self, yaml_content: dict[str, Any], file_path: str) -> ServiceRequest:
        """
        Parse YAML content into a ServiceRequest object.

        Args:
            yaml_content: Parsed YAML content
            file_path: Path to the original file

        Returns:
            ServiceRequest: Parsed service request object
        """
        # Validate required keys first
        missing_keys = [key for key in self.required_keys if key not in yaml_content]
        if missing_keys:
            raise ValueError(f"Missing required keys in service request: {missing_keys}")

        # Extract basic info
        name = yaml_content["request-name"]
        request_type = yaml_content["request-type"]
        request_status = yaml_content["request-status"]

        # Parse requests
        requests_data = yaml_content["requests"]
        if not isinstance(requests_data, list):
            msg = "requests must be a list"
            raise ValueError(msg)

        requests = []
        for i, request_data in enumerate(requests_data):
            if not isinstance(request_data, dict):
                raise ValueError(f"Request item {i} must be a dictionary")

            # Validate required keys for each request
            missing_keys = [key for key in self.required_request_keys if key not in request_data]
            if missing_keys:
                raise ValueError(f"Request item {i} missing required keys: {missing_keys}")

            # Parse principal
            principal_data = request_data["principal"]
            if not isinstance(principal_data, dict):
                raise ValueError(f"Principal in request item {i} must be a dictionary")

            if "type" not in principal_data or "id" not in principal_data:
                raise ValueError(f"Principal in request item {i} must have 'type' and 'id'")

            principal = Principal(type=principal_data["type"], id=principal_data["id"])

            # Parse privileges (convert to list if needed)
            privileges = request_data.get("privileges", [])
            if isinstance(privileges, str):
                privileges = [privileges]
            elif not isinstance(privileges, list):
                privileges = []

            # Create service request item
            request_item = ServiceRequestItem(
                principal=principal, resource=request_data["resource"], privileges=privileges
            )

            requests.append(request_item)

        # Create file info
        file_info = yaml_content.get(
            "_file_info", {"filename": Path(file_path).name, "filepath": file_path, "stem": Path(file_path).stem}
        )

        return ServiceRequest(
            name=name, request_type=request_type, request_status=request_status, requests=requests, file_info=file_info
        )

    def validate_service_request(self, service_request: ServiceRequest) -> list[str]:
        """
        Validate a service request object and return any validation errors.

        Args:
            service_request: The service request to validate

        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []

        # Validate basic fields
        if not service_request.name or not service_request.name.strip():
            errors.append("Service request name cannot be empty")

        if not service_request.request_type or not service_request.request_type.strip():
            errors.append("Service request type cannot be empty")

        if not service_request.requests:
            errors.append("Service request must have at least one request item")

        # Validate each request item
        for i, request_item in enumerate(service_request.requests):
            if not request_item.resource or not request_item.resource.strip():
                errors.append(f"Request item {i}: resource cannot be empty")

            if not request_item.principal.type or not request_item.principal.type.strip():
                errors.append(f"Request item {i}: principal type cannot be empty")

            if not request_item.principal.id or not request_item.principal.id.strip():
                errors.append(f"Request item {i}: principal id cannot be empty")

        return errors

    def get_service_request_summary(self, service_request: ServiceRequest) -> dict[str, Any]:
        """
        Generate a summary of a service request.

        Args:
            service_request: The service request to summarize

        Returns:
            dict[str, Any]: Summary information
        """
        return {
            "name": service_request.name,
            "type": service_request.request_type,
            "total_requests": len(service_request.requests),
            "resources": list({req.resource for req in service_request.requests}),
            "principals": list({f"{req.principal.type}:{req.principal.id}" for req in service_request.requests}),
            "privileges": list({priv for req in service_request.requests for priv in req.privileges}),
            "file_info": service_request.file_info,
        }
