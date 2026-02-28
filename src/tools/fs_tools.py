"""Filesystem tool implementations."""

import os
from pathlib import Path

from src.models import FsReadRequest, FsReadResponse
from src.workspace import WorkspaceManager, SecurityError
from src.logging_config import get_logger

logger = get_logger(__name__)


class FilesystemTools:
    """Filesystem tool implementations."""
    
    def __init__(self, workspace: WorkspaceManager):
        """Initialize filesystem tools.
        
        Args:
            workspace: Workspace manager instance
        """
        self.workspace = workspace
    
    async def read(self, request: FsReadRequest) -> FsReadResponse:
        """Read file contents.
        
        Args:
            request: Read request
            
        Returns:
            File contents and metadata
            
        Raises:
            SecurityError: If path escapes workspace
            FileNotFoundError: If file doesn't exist
            ValueError: If parameters are invalid
        """
        # Resolve path with security checks
        resolved_path = self.workspace.resolve_path(
            request.path,
            request.workspace_dir,
        )
        
        # Check if file exists
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(
                f"File not found: {request.path}. "
                f"Use fs_list to see available files."
            )
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(resolved_path):
            raise ValueError(
                f"Path is not a file: {request.path}. "
                f"Use fs_list to list directory contents."
            )
        
        # Get file size
        size_bytes = os.path.getsize(resolved_path)
        
        # Read file contents
        try:
            with open(resolved_path, "r", encoding=request.encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Failed to decode file with encoding '{request.encoding}': {str(e)}. "
                f"Try a different encoding or check if this is a binary file."
            )
        
        line_count = len(lines)
        
        # Apply line range if specified
        if request.line_start is not None or request.line_end is not None:
            start = (request.line_start - 1) if request.line_start else 0
            end = request.line_end if request.line_end else line_count
            
            # Validate range
            if start < 0 or start >= line_count:
                raise ValueError(
                    f"line_start {request.line_start} is out of range. "
                    f"File has {line_count} lines."
                )
            if end < start:
                raise ValueError(
                    f"line_end {request.line_end} is before line_start {request.line_start}"
                )
            
            lines = lines[start:end]
        
        # Apply max_lines limit
        if request.max_lines is not None and len(lines) > request.max_lines:
            lines = lines[:request.max_lines]
        
        content = "".join(lines)
        
        logger.info(
            "file_read",
            path=resolved_path,
            size_bytes=size_bytes,
            lines_returned=len(lines),
            total_lines=line_count,
        )
        
        return FsReadResponse(
            content=content,
            path=resolved_path,
            size_bytes=size_bytes,
            line_count=line_count,
            encoding=request.encoding,
        )
