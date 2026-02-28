"""Workspace tool implementations."""

from typing import Optional

from src.models import WorkspaceInfoResponse
from src.workspace import WorkspaceManager
from src.logging_config import get_logger

logger = get_logger(__name__)


class WorkspaceTools:
    """Workspace tool implementations."""

    def __init__(self, workspace: WorkspaceManager, secret_manager=None):
        """Initialize workspace tools.

        Args:
            workspace: Workspace manager instance
            secret_manager: Optional SecretManager for reporting secret count
        """
        self.workspace = workspace
        self.secret_manager = secret_manager

    async def info(self) -> WorkspaceInfoResponse:
        """Get workspace information.

        Returns:
            Workspace configuration and status
        """
        workspace_info = self.workspace.get_workspace_info()

        secret_count = 0
        if self.secret_manager is not None:
            secret_count = self.secret_manager.count()

        logger.info("workspace_info_retrieved", secret_count=secret_count)

        return WorkspaceInfoResponse(
            default_workspace=workspace_info["default_workspace"],
            available_directories=[workspace_info["default_workspace"]],
            disk_usage=workspace_info["disk_usage"],
            tool_categories=["fs", "workspace", "shell", "git", "docker", "http", "memory", "plan"],
            secret_count=secret_count,
        )
