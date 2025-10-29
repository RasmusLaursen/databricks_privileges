from databricks.sdk import WorkspaceClient


def get_workspace(host:str, token:str) -> WorkspaceClient:
    return WorkspaceClient(host=host, token=token)
