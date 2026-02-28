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


# Filesystem list models

class FsListRequest(BaseModel):
    """Request model for fs_list tool."""
    path: str = Field(".", description="Directory path relative to workspace")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")
    recursive: bool = Field(False, description="List subdirectories recursively")
    max_depth: int = Field(3, description="Maximum depth for recursive listing")
    include_hidden: bool = Field(False, description="Include hidden files (starting with .)")
    pattern: Optional[str] = Field(None, description="Glob pattern filter (e.g., '*.py', 'test_*.txt')")


class FsListEntry(BaseModel):
    """Single entry in directory listing."""
    name: str = Field(..., description="File or directory name")
    type: str = Field(..., description="Entry type: 'file' or 'directory'")
    size: int = Field(..., description="Size in bytes (0 for directories)")
    modified: str = Field(..., description="Last modified timestamp")
    permissions: str = Field(..., description="Unix permissions string")


class FsListResponse(BaseModel):
    """Response model for fs_list tool."""
    entries: list[FsListEntry] = Field(..., description="Directory entries")
    total_entries: int = Field(..., description="Total number of entries")
    path: str = Field(..., description="Resolved directory path")


# Filesystem search models

class FsSearchRequest(BaseModel):
    """Request model for fs_search tool."""
    query: str = Field(..., description="Search pattern")
    path: str = Field(".", description="Directory to search in")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")
    search_type: str = Field("filename", description="Search type: 'filename', 'content', or 'both'")
    regex: bool = Field(False, description="Treat query as regex pattern")
    max_results: int = Field(50, description="Maximum number of results to return")
    include_content_preview: bool = Field(True, description="Include content preview for matches")


class FsSearchMatch(BaseModel):
    """Single search result."""
    path: str = Field(..., description="File path")
    type: str = Field(..., description="Match type: 'filename' or 'content'")
    match_line: Optional[int] = Field(None, description="Line number for content matches")
    preview: Optional[str] = Field(None, description="Content preview around match")


class FsSearchResponse(BaseModel):
    """Response model for fs_search tool."""
    results: list[FsSearchMatch] = Field(..., description="Search results")
    total_matches: int = Field(..., description="Total number of matches found")
    search_time_ms: int = Field(..., description="Search duration in milliseconds")


# Shell execution models

class ShellExecuteRequest(BaseModel):
    """Request model for shell_execute tool."""
    command: str = Field(..., description="Shell command to execute")
    workspace_dir: Optional[str] = Field(None, description="Working directory for command execution")
    timeout: int = Field(60, description="Timeout in seconds")
    env: Optional[dict[str, str]] = Field(None, description="Additional environment variables (use {{secret:KEY}} for sensitive values)")


class ShellExecuteResponse(BaseModel):
    """Response model for shell_execute tool."""
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    exit_code: int = Field(..., description="Exit code")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    command: str = Field(..., description="The command as executed")
    working_directory: str = Field(..., description="Working directory used")


# Error response model

class ErrorResponse(BaseModel):
    """Error response model."""
    error: bool = True
    error_type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for recovery")
    suggestion_tool: Optional[str] = Field(None, description="Suggested tool to use instead")
