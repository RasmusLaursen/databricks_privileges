"""
YAML file handling module for ABAC.

This module provides functionality to read and parse YAML files.
"""

from pathlib import Path
from typing import Any

import yaml

from privileges.logger import logging_helper

logger = logging_helper.get_logger(__name__)


def read_yaml_file(file_path: str) -> dict[str, Any]:
    """
    Read and parse a YAML file.

    Args:
        file_path: Path to the YAML file to read

    Returns:
        dict[str, Any]: Parsed YAML content as a dictionary

    Raises:
        FileNotFoundError: If the specified file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
        Exception: For other reading errors
    """
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        with open(file_path_obj, encoding="utf-8") as file:
            content = yaml.safe_load(file)

        if content is None:
            return {}

        return content

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}") from e
    except FileNotFoundError:
        raise  # Re-raise FileNotFoundError as-is
    except Exception as e:
        raise Exception(f"Error reading YAML file {file_path}: {e}") from e


def read_yaml_files_from_directory(directory_path: str, pattern: str = "*.yml") -> list[dict[str, Any]]:
    """
    Read all YAML files from a directory.

    Args:
        directory_path: Path to the directory containing YAML files
        pattern: File pattern to match (default: "*.yml")

    Returns:
        list[dict[str, Any]]: list of parsed YAML content from all files

    Raises:
        FileNotFoundError: If the directory doesn't exist
    """
    try:
        dir_path = Path(directory_path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory_path}")

        yaml_files = list(dir_path.glob(pattern))
        results = []

        for yaml_file in yaml_files:
            try:
                content = read_yaml_file(str(yaml_file))
                # Add metadata about the file
                content["_file_info"] = {"filename": yaml_file.name, "filepath": str(yaml_file), "stem": yaml_file.stem}
                results.append(content)
            except Exception as e:
                logger.warning(f"Warning: Could not read {yaml_file}: {e}")
                continue

        return results

    except Exception as e:
        raise Exception(f"Error reading YAML files from directory '{directory_path}': {e}") from e


def validate_yaml_structure(yaml_content: dict[str, Any], required_keys: list[str]) -> bool:
    """
    Validate that a YAML content dictionary contains required keys.

    Args:
        yaml_content: The parsed YAML content
        required_keys: list of required keys that must be present

    Returns:
        bool: True if all required keys are present, False otherwise
    """
    if not isinstance(yaml_content, dict):
        return False

    for key in required_keys:
        if key not in yaml_content:
            return False

    return True


def get_nested_value(yaml_content: dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a nested value from YAML content using dot notation.

    Args:
        yaml_content: The parsed YAML content
        key_path: Dot-separated path to the desired value (e.g., "requests.0.action")
        default: Default value to return if key path is not found

    Returns:
        Any: The value at the specified path, or default if not found
    """
    try:
        keys = key_path.split(".")
        current = yaml_content

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index] if 0 <= index < len(current) else default
                except (ValueError, IndexError):
                    return default
            else:
                return default

        return current

    except Exception:
        return default
