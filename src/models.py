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


# Git tool models

class GitStatusRequest(BaseModel):
    """Request model for git_status tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitStatusResponse(BaseModel):
    """Response model for git_status tool."""
    branch: str = Field(..., description="Current branch name")
    staged: list[dict] = Field(..., description="Staged files with status")
    unstaged: list[dict] = Field(..., description="Unstaged files with status")
    untracked: list[str] = Field(..., description="Untracked files")
    ahead: int = Field(..., description="Commits ahead of remote")
    behind: int = Field(..., description="Commits behind remote")
    clean: bool = Field(..., description="Whether working tree is clean")


class GitLogRequest(BaseModel):
    """Request model for git_log tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    max_count: int = Field(20, description="Maximum number of commits to return")
    author: Optional[str] = Field(None, description="Filter by author")
    since: Optional[str] = Field(None, description="Show commits since date")
    until: Optional[str] = Field(None, description="Show commits until date")
    path: Optional[str] = Field(None, description="Filter by file path")
    format: str = Field("medium", description="Output format: short, medium, or full")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitLogResponse(BaseModel):
    """Response model for git_log tool."""
    commits: list[dict] = Field(..., description="List of commits")
    total_shown: int = Field(..., description="Total number of commits shown")


class GitDiffRequest(BaseModel):
    """Request model for git_diff tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    ref: Optional[str] = Field(None, description="Commit/branch to diff against")
    path: Optional[str] = Field(None, description="Specific file to diff")
    staged: bool = Field(False, description="Show staged changes")
    stat_only: bool = Field(False, description="Show only statistics")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitDiffResponse(BaseModel):
    """Response model for git_diff tool."""
    diff: str = Field(..., description="Unified diff output")
    files_changed: int = Field(..., description="Number of files changed")
    insertions: int = Field(..., description="Number of insertions")
    deletions: int = Field(..., description="Number of deletions")


class GitCommitRequest(BaseModel):
    """Request model for git_commit tool."""
    message: str = Field(..., description="Commit message")
    repo_path: str = Field(".", description="Repository path relative to workspace")
    files: Optional[list[str]] = Field(None, description="Specific files to stage, or all if empty")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitCommitResponse(BaseModel):
    """Response model for git_commit tool."""
    hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message")
    files_committed: list[str] = Field(..., description="Files included in commit")


class GitPushRequest(BaseModel):
    """Request model for git_push tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    remote: str = Field("origin", description="Remote name")
    branch: Optional[str] = Field(None, description="Branch name (current branch if not specified)")
    force: bool = Field(False, description="Force push")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitPushResponse(BaseModel):
    """Response model for git_push tool."""
    remote: str = Field(..., description="Remote name")
    branch: str = Field(..., description="Branch name")
    commits_pushed: int = Field(..., description="Number of commits pushed")
    output: str = Field(..., description="Git command output")


class GitPullRequest(BaseModel):
    """Request model for git_pull tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    remote: str = Field("origin", description="Remote name")
    branch: Optional[str] = Field(None, description="Branch name")
    rebase: bool = Field(False, description="Use rebase instead of merge")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitPullResponse(BaseModel):
    """Response model for git_pull tool."""
    updated: bool = Field(..., description="Whether repository was updated")
    commits_received: int = Field(..., description="Number of commits received")
    files_changed: list[str] = Field(..., description="Files that were changed")
    output: str = Field(..., description="Git command output")


class GitCheckoutRequest(BaseModel):
    """Request model for git_checkout tool."""
    target: str = Field(..., description="Branch name or commit hash")
    repo_path: str = Field(".", description="Repository path relative to workspace")
    create: bool = Field(False, description="Create new branch")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitCheckoutResponse(BaseModel):
    """Response model for git_checkout tool."""
    branch: str = Field(..., description="Current branch after checkout")
    previous_branch: str = Field(..., description="Previous branch")
    output: str = Field(..., description="Git command output")


class GitBranchRequest(BaseModel):
    """Request model for git_branch tool."""
    name: str = Field(..., description="Branch name")
    repo_path: str = Field(".", description="Repository path relative to workspace")
    action: str = Field("create", description="Action: create or delete")
    force: bool = Field(False, description="Force operation")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitBranchResponse(BaseModel):
    """Response model for git_branch tool."""
    branch: str = Field(..., description="Branch name")
    action: str = Field(..., description="Action performed")
    output: str = Field(..., description="Git command output")


class GitListBranchesRequest(BaseModel):
    """Request model for git_list_branches tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    remote: bool = Field(False, description="Include remote branches")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitListBranchesResponse(BaseModel):
    """Response model for git_list_branches tool."""
    branches: list[dict] = Field(..., description="List of branches")


class GitStashRequest(BaseModel):
    """Request model for git_stash tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    action: str = Field("push", description="Action: push, pop, list, or drop")
    message: Optional[str] = Field(None, description="Stash message (for push)")
    index: Optional[int] = Field(None, description="Stash index (for pop/drop)")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitStashResponse(BaseModel):
    """Response model for git_stash tool."""
    action: str = Field(..., description="Action performed")
    stashes: Optional[list[dict]] = Field(None, description="List of stashes (for list action)")
    output: str = Field(..., description="Git command output")


class GitShowRequest(BaseModel):
    """Request model for git_show tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    ref: str = Field("HEAD", description="Commit reference")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitShowResponse(BaseModel):
    """Response model for git_show tool."""
    hash: str = Field(..., description="Commit hash")
    author: str = Field(..., description="Commit author")
    date: str = Field(..., description="Commit date")
    message: str = Field(..., description="Commit message")
    body: str = Field(..., description="Commit body")
    diff: str = Field(..., description="Commit diff")
    files_changed: list[str] = Field(..., description="Files changed in commit")


class GitRemoteRequest(BaseModel):
    """Request model for git_remote tool."""
    repo_path: str = Field(".", description="Repository path relative to workspace")
    action: str = Field("list", description="Action: list, add, or remove")
    name: Optional[str] = Field(None, description="Remote name")
    url: Optional[str] = Field(None, description="Remote URL")
    workspace_dir: Optional[str] = Field(None, description="Override workspace directory")


class GitRemoteResponse(BaseModel):
    """Response model for git_remote tool."""
    remotes: list[dict] = Field(..., description="List of remotes")
    action: str = Field(..., description="Action performed")
    output: Optional[str] = Field(None, description="Git command output")


# Docker tool models

class DockerListRequest(BaseModel):
    """Request model for docker_list tool."""
    all: bool = Field(True, description="Include stopped containers")
    filter_name: Optional[str] = Field(None, description="Filter by container name (partial match)")
    filter_status: Optional[str] = Field(None, description="Filter by status (running, exited, paused, etc.)")


class DockerListResponse(BaseModel):
    """Response model for docker_list tool."""
    containers: list[dict] = Field(..., description="List of containers with id, name, image, status, ports, created")
    total_count: int = Field(..., description="Total number of containers found")


class DockerInspectRequest(BaseModel):
    """Request model for docker_inspect tool."""
    container: str = Field(..., description="Container name or ID")


class DockerInspectResponse(BaseModel):
    """Response model for docker_inspect tool."""
    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Image name")
    status: str = Field(..., description="Container status")
    config: dict = Field(..., description="Container configuration")
    network: dict = Field(..., description="Network settings")
    mounts: list = Field(..., description="Volume mounts")
    ports: dict = Field(..., description="Port mappings")
    created: str = Field(..., description="Creation timestamp")
    state: dict = Field(..., description="Container state details")


class DockerLogsRequest(BaseModel):
    """Request model for docker_logs tool."""
    container: str = Field(..., description="Container name or ID")
    tail: int = Field(100, description="Number of lines from the end of logs")
    since: Optional[str] = Field(None, description="Show logs since timestamp (e.g., '2024-01-01T00:00:00')")
    follow: bool = Field(False, description="Follow log output (not recommended for API calls)")


class DockerLogsResponse(BaseModel):
    """Response model for docker_logs tool."""
    logs: str = Field(..., description="Container logs")
    container: str = Field(..., description="Container name or ID")
    line_count: int = Field(..., description="Number of log lines returned")


class DockerActionRequest(BaseModel):
    """Request model for docker_action tool."""
    container: str = Field(..., description="Container name or ID")
    action: str = Field(..., description="Action to perform: start, stop, restart, pause, unpause")
    timeout: int = Field(30, description="Timeout in seconds for the action")


class DockerActionResponse(BaseModel):
    """Response model for docker_action tool."""
    container: str = Field(..., description="Container name or ID")
    action: str = Field(..., description="Action performed")
    success: bool = Field(..., description="Whether the action succeeded")
    previous_status: str = Field(..., description="Status before action")
    new_status: str = Field(..., description="Status after action")
    message: str = Field(..., description="Result message")


# Workspace secrets models

class WorkspaceSecretsListResponse(BaseModel):
    """Response model for workspace_secrets_list tool."""
    keys: list[str] = Field(..., description="List of configured secret key names (values not exposed)")
    count: int = Field(..., description="Total number of configured secrets")
    secrets_file: str = Field(..., description="Path to the secrets file")


# HTTP request models

class HttpRequestRequest(BaseModel):
    """Request model for http_request tool."""
    url: str = Field(..., description="URL to request")
    method: str = Field("GET", description="HTTP method: GET, POST, PUT, PATCH, DELETE, HEAD")
    headers: Optional[dict[str, str]] = Field(None, description="Request headers (use {{secret:KEY}} for sensitive values)")
    body: Optional[str] = Field(None, description="Request body (for POST/PUT/PATCH)")
    json_body: Optional[dict] = Field(None, description="JSON request body (for POST/PUT/PATCH, mutually exclusive with body)")
    timeout: int = Field(30, description="Request timeout in seconds")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")


class HttpRequestResponse(BaseModel):
    """Response model for http_request tool."""
    status_code: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(..., description="Response headers")
    body: str = Field(..., description="Response body as text")
    url: str = Field(..., description="Final URL after redirects")
    duration_ms: int = Field(..., description="Request duration in milliseconds")
    content_type: Optional[str] = Field(None, description="Response content type")


# Error response model

class ErrorResponse(BaseModel):
    """Error response model."""
    error: bool = True
    error_type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    suggestion: Optional[str] = Field(None, description="Suggestion for recovery")
    suggestion_tool: Optional[str] = Field(None, description="Suggested tool to use instead")

