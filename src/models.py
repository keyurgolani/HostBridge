"""Pydantic models for tool requests and responses."""

from typing import Optional
from pydantic import BaseModel, Field


# Filesystem tool models

class FsReadRequest(BaseModel):
    """Request model for fs_read tool."""
    path: str = Field(..., description="File path relative to workspace")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")
    encoding: str = Field("utf-8", description="File encoding")
    max_lines: Optional[int] = Field(None, description="Limit returned lines (for large files)")
    line_start: Optional[int] = Field(None, description="Start reading from this line (1-indexed)")
    line_end: Optional[int] = Field(None, description="Stop reading at this line (1-indexed)")


class FsReadResponse(BaseModel):
    """Response model for fs_read tool."""
    content: str = Field(..., description="File contents")
    path: str = Field(..., description="Resolved absolute path")
    size_bytes: int = Field(..., description="File size in bytes")
    line_count: int = Field(..., description="Total number of lines")
    encoding: str = Field(..., description="File encoding used")


class FsWriteRequest(BaseModel):
    """Request model for fs_write tool."""
    path: str = Field(..., description="File path relative to workspace")
    content: str = Field(..., description="Content to write")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")
    mode: str = Field("create", description="Write mode: 'create', 'overwrite', or 'append'")
    create_dirs: bool = Field(True, description="Create parent directories if they don't exist")
    encoding: str = Field("utf-8", description="File encoding")


class FsWriteResponse(BaseModel):
    """Response model for fs_write tool."""
    path: str = Field(..., description="Resolved absolute path")
    bytes_written: int = Field(..., description="Number of bytes written")
    created: bool = Field(..., description="Whether file was newly created")
    mode: str = Field(..., description="Write mode used")


# Workspace tool models

class WorkspaceInfoResponse(BaseModel):
    """Response model for workspace_info tool."""
    default_workspace: str = Field(..., description="Default workspace directory")
    available_directories: list[str] = Field(..., description="Available workspace directories")
    disk_usage: dict = Field(..., description="Disk usage information")
    tool_categories: list[str] = Field(..., description="Available tool categories")
    secret_count: int = Field(0, description="Number of configured secrets")


# Error response model

class ErrorResponse(BaseModel):
    """Error response model."""
    error: bool = True
    error_type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for recovery")
    suggestion_tool: Optional[str] = Field(None, description="Suggested tool to use instead")
