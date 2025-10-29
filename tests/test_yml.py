"""
Unit tests for YAML reading functionality.
"""

import os
import tempfile

import pytest

from privileges.files import yml


class TestYMLReader:
    """Test cases for YAML reading functionality."""

    def test_read_valid_yaml_file(self):
        """Test reading a valid YAML file."""
        # Create a temporary YAML file
        yaml_content = """
name: test
value: 123
items:
  - item1
  - item2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name

        try:
            result = yml.read_yaml_file(temp_file)
            assert isinstance(result, dict)
            assert result["name"] == "test"
            assert result["value"] == 123
            assert result["items"] == ["item1", "item2"]
        finally:
            os.unlink(temp_file)

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            yml.read_yaml_file("nonexistent.yml")

    def test_read_empty_yaml_file(self):
        """Test reading an empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            result = yml.read_yaml_file(temp_file)
            assert result == {}
        finally:
            os.unlink(temp_file)

    def test_validate_yaml_structure(self):
        """Test YAML structure validation."""
        valid_yaml = {"key1": "value1", "key2": "value2"}
        required_keys = ["key1", "key2"]

        assert yml.validate_yaml_structure(valid_yaml, required_keys) is True

        # Test missing key
        invalid_yaml = {"key1": "value1"}
        assert yml.validate_yaml_structure(invalid_yaml, required_keys) is False

        # Test non-dict input
        assert yml.validate_yaml_structure(["not", "a", "dict"], required_keys) is False

    def test_get_nested_value(self):
        """Test getting nested values from YAML content."""
        yaml_content = {"level1": {"level2": {"value": "found"}}, "list_data": [{"item": "first"}, {"item": "second"}]}

        # Test nested dict access
        assert yml.get_nested_value(yaml_content, "level1.level2.value") == "found"

        # Test list access
        assert yml.get_nested_value(yaml_content, "list_data.0.item") == "first"
        assert yml.get_nested_value(yaml_content, "list_data.1.item") == "second"

        # Test non-existent path
        assert yml.get_nested_value(yaml_content, "non.existent.path", "default") == "default"

        # Test invalid index
        assert yml.get_nested_value(yaml_content, "list_data.99.item", "default") == "default"
