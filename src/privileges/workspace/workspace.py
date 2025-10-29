from databricks.sdk import WorkspaceClient

from privileges.logger import logging_helper

logger = logging_helper.get_logger(__name__)


def get_workspace(host:str, token:str) -> WorkspaceClient:
    logger.debug(f"Creating WorkspaceClient with host: {host}")
    logger.debug(f"Host: {host}, Token: {'****' if token else None}")
    if host == 'None':
        logger.info("Using default authentication for WorkspaceClient")
        return WorkspaceClient()
    return WorkspaceClient(host=host, token=token)
