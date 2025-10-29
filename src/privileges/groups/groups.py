from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import Group


def list_groups(workspace_client: WorkspaceClient) -> list[Group]:
    """
    List all groups in the Databricks workspace.

    Args:
        workspace_client: Optional WorkspaceClient instance. If None, creates a new one.

    Returns:
        List[Group]: A list of Group objects from the workspace

    Raises:
        Exception: If there's an error connecting to Databricks or fetching groups
    """
    if workspace_client is None:
        workspace_client = WorkspaceClient()

    try:
        groups = list(workspace_client.groups.list())
        return groups
    except Exception as e:
        raise Exception(f"Failed to list groups: {e}") from e


def get_group_by_name(group_name: str, workspace_client: WorkspaceClient) -> Optional[Group]:
    """
    Get a specific group by name.

    Args:
        group_name: The display name of the group to find
        workspace_client: Optional WorkspaceClient instance. If None, creates a new one.

    Returns:
        Optional[Group]: The Group object if found, None otherwise

    Raises:
        Exception: If there's an error connecting to Databricks or fetching groups
        ValueError: If group_name is empty or None
    """

    if not group_name or not group_name.strip():
        msg = "Group name cannot be empty or None"
        raise ValueError(msg)

    try:
        groups = list_groups(workspace_client)

        for group in groups:
            if group.display_name == group_name:
                return group

        return None
    except Exception as e:
        raise Exception(f"Failed to get group {group_name}: {e}") from e
