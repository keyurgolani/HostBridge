"""Workspace tool implementations."""

from src.models import WorkspaceInfoResponse
from src.workspace import WorkspaceManager
from src.logging_config import get_logger

logger = get_logger(__name__)


class WorkspaceTools:
    """Workspace tool implementations."""
    
    def __init__(self, workspace: WorkspaceManager):
        """Initialize workspace tools.
        
        Args:
            workspace: Workspace manager instance
        """
        self.workspace = workspace
    
    async def info(self) -> WorkspaceInfoResponse:
        """Get workspace information.
        
        Returns:
            Workspace configuration and status
        """
        workspace_info = self.workspace.get_workspace_info()
        
        logger.info("workspace_info_retrieved")
        
        return WorkspaceInfoResponse(
            default_workspace=workspace_info["default_workspace"],
            available_directories=[workspace_info["default_workspace"]],
            disk_usage=workspace_info["disk_usage"],
            tool_categories=["fs", "workspace"],
            secret_count=0,  # Will be implemented in later slices
        )
