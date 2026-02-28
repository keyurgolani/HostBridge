"""Main FastAPI application."""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_mcp import FastApiMCP

from src.config import load_config
from src.database import Database
from src.logging_config import setup_logging, get_logger
from src.workspace import WorkspaceManager, SecurityError
from src.audit import AuditLogger
from src.policy import PolicyEngine
from src.hitl import HITLManager
from src.tools.fs_tools import FilesystemTools
from src.tools.workspace_tools import WorkspaceTools
from src.tools.shell_tools import ShellTools
from src.tools.git_tools import GitTools
from src.models import (
    FsReadRequest,
    FsReadResponse,
    FsWriteRequest,
    FsWriteResponse,
    FsListRequest,
    FsListResponse,
    FsSearchRequest,
    FsSearchResponse,
    ShellExecuteRequest,
    ShellExecuteResponse,
    WorkspaceInfoResponse,
    GitStatusRequest,
    GitStatusResponse,
    GitLogRequest,
    GitLogResponse,
    GitDiffRequest,
    GitDiffResponse,
    GitCommitRequest,
    GitCommitResponse,
    GitPushRequest,
    GitPushResponse,
    GitPullRequest,
    GitPullResponse,
    GitCheckoutRequest,
    GitCheckoutResponse,
    GitBranchRequest,
    GitBranchResponse,
    GitListBranchesRequest,
    GitListBranchesResponse,
    GitStashRequest,
    GitStashResponse,
    GitShowRequest,
    GitShowResponse,
    GitRemoteRequest,
    GitRemoteResponse,
    ErrorResponse,
)

# Global state
config = load_config()
setup_logging(config.audit.log_level)
logger = get_logger(__name__)

# Initialize components
db = Database()
workspace_manager = WorkspaceManager(config.workspace.base_dir)
audit_logger = AuditLogger(db)
policy_engine = PolicyEngine(config)
hitl_manager = HITLManager(db, config.hitl.default_ttl_seconds)

# Initialize tools
fs_tools = FilesystemTools(workspace_manager)
workspace_tools = WorkspaceTools(workspace_manager)
shell_tools = ShellTools(workspace_manager)
git_tools = GitTools(workspace_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("starting_hostbridge", version="0.1.0")
    app.state.start_time = time.time()
    await db.connect()
    await hitl_manager.start()
    logger.info("hostbridge_started")
    
    yield
    
    # Shutdown
    logger.info("shutting_down_hostbridge")
    await hitl_manager.stop()
    await db.close()
    logger.info("hostbridge_stopped")


# Create FastAPI apps
app = FastAPI(
    title="HostBridge",
    description="Unified MCP + OpenAPI Tool Server for Self-Hosted LLM Stacks",
    version="0.1.0",
    lifespan=lifespan,
)

# Per-category sub-apps
fs_app = FastAPI(
    title="HostBridge — Filesystem Tools",
    description="Filesystem operations for HostBridge",
    version="0.1.0",
)

workspace_app = FastAPI(
    title="HostBridge — Workspace Tools",
    description="Workspace management for HostBridge",
    version="0.1.0",
)

git_app = FastAPI(
    title="HostBridge — Git Tools",
    description="Git repository management for HostBridge",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError):
    """Handle security errors."""
    logger.warning("security_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(
            error_type="security_error",
            message=str(exc),
            suggestion="Ensure the path is within the workspace boundary",
        ).model_dump(),
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle file not found errors."""
    logger.warning("file_not_found", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error_type="file_not_found",
            message=str(exc),
            suggestion_tool="fs_list",
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    logger.warning("value_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_type="invalid_parameter",
            message=str(exc),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle general errors."""
    logger.error("unexpected_error", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_type="internal_error",
            message="An unexpected error occurred. Please check the logs.",
        ).model_dump(),
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# Tool execution wrapper with policy and audit
async def execute_tool(
    tool_category: str,
    tool_name: str,
    params: Dict[str, Any],
    tool_func,
    protocol: str = "openapi",
    force_hitl: bool = False,
    hitl_reason: Optional[str] = None,
):
    """Execute a tool with policy enforcement and audit logging.
    
    Args:
        tool_category: Tool category
        tool_name: Tool name
        params: Tool parameters
        tool_func: Tool function to execute
        protocol: Protocol used (openapi or mcp)
        force_hitl: Force HITL approval regardless of policy
        hitl_reason: Reason for HITL requirement
        
    Returns:
        Tool execution result
    """
    start_time = time.time()
    
    # Policy check (skip if force_hitl is True)
    if force_hitl:
        decision = "hitl"
        reason = hitl_reason or "Requires approval"
    else:
        decision, reason = policy_engine.evaluate(tool_category, tool_name, params)
    
    if decision == "block":
        # Log blocked execution
        await audit_logger.log_execution(
            tool_name=tool_name,
            tool_category=tool_category,
            protocol=protocol,
            request_params=params,
            status="blocked",
            error_message=reason,
        )
        
        raise SecurityError(f"Operation blocked: {reason}")
    
    # HITL handling
    if decision == "hitl":
        logger.info("hitl_required", tool=f"{tool_category}_{tool_name}", reason=reason)
        
        # Create HITL request
        hitl_request = await hitl_manager.create_request(
            tool_name=tool_name,
            tool_category=tool_category,
            request_params=params,
            request_context={"protocol": protocol},
            policy_rule_matched=reason,
        )
        
        # Wait for decision (this blocks the HTTP connection)
        decision_result = await hitl_manager.wait_for_decision(hitl_request.id)
        
        if decision_result == "rejected":
            # Log rejected execution
            await audit_logger.log_execution(
                tool_name=tool_name,
                tool_category=tool_category,
                protocol=protocol,
                request_params=params,
                status="hitl_rejected",
                error_message="Operation rejected by administrator",
                hitl_request_id=hitl_request.id,
            )
            
            raise SecurityError(
                "Operation not permitted. The request was reviewed and rejected."
            )
        
        elif decision_result == "expired":
            # Log expired execution
            await audit_logger.log_execution(
                tool_name=tool_name,
                tool_category=tool_category,
                protocol=protocol,
                request_params=params,
                status="hitl_expired",
                error_message="Operation timed out waiting for approval",
                hitl_request_id=hitl_request.id,
            )
            
            raise TimeoutError(
                "Operation timed out waiting for processing. Please try again later."
            )
        
        # If approved, continue with execution
        logger.info("hitl_approved_executing", tool=f"{tool_category}_{tool_name}")
    
    # Execute tool
    try:
        result = await tool_func()
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful execution
        await audit_logger.log_execution(
            tool_name=tool_name,
            tool_category=tool_category,
            protocol=protocol,
            request_params=params,
            response_body=result.model_dump() if hasattr(result, "model_dump") else result,
            status="success" if decision != "hitl" else "hitl_approved",
            duration_ms=duration_ms,
            workspace_dir=workspace_manager.base_dir,
        )
        
        return result
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failed execution
        await audit_logger.log_execution(
            tool_name=tool_name,
            tool_category=tool_category,
            protocol=protocol,
            request_params=params,
            status="error",
            duration_ms=duration_ms,
            error_message=str(e),
        )
        
        raise


# Filesystem tools - Root app
@app.post(
    "/api/tools/fs/read",
    operation_id="fs_read",
    summary="Read File",
    description="""Read the contents of a file at the specified path.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided. Returns the file contents 
as text.

Use this tool when you need to:
- Examine file contents before making changes
- Read configuration files
- Inspect source code
- Check log files

Required: path (relative to workspace directory)
Optional: encoding, max_lines (for large files), line_start/line_end (for specific sections)""",
    response_model=FsReadResponse,
    tags=["filesystem"],
)
async def fs_read_root(request: FsReadRequest) -> FsReadResponse:
    """Read file contents (root app endpoint)."""
    return await execute_tool(
        "fs",
        "read",
        request.model_dump(),
        lambda: fs_tools.read(request),
    )


# Filesystem tools - Sub-app
@fs_app.post(
    "/read",
    operation_id="fs_read",
    summary="Read File",
    description="""Read the contents of a file at the specified path.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided. Returns the file contents 
as text.

Use this tool when you need to:
- Examine file contents before making changes
- Read configuration files
- Inspect source code
- Check log files

Required: path (relative to workspace directory)
Optional: encoding, max_lines (for large files), line_start/line_end (for specific sections)""",
    response_model=FsReadResponse,
    tags=["filesystem"],
)
async def fs_read_sub(request: FsReadRequest) -> FsReadResponse:
    """Read file contents (sub-app endpoint)."""
    return await execute_tool(
        "fs",
        "read",
        request.model_dump(),
        lambda: fs_tools.read(request),
    )


# Workspace tools - Root app
@app.post(
    "/api/tools/workspace/info",
    operation_id="workspace_info",
    summary="Get Workspace Information",
    description="""Get information about the workspace configuration.

Returns the default workspace directory, available paths, disk usage,
and available tool categories.

Use this tool when you need to:
- Understand the workspace boundaries
- Check available disk space
- See what tool categories are available
- Get the base workspace path for other operations

No parameters required.""",
    response_model=WorkspaceInfoResponse,
    tags=["workspace"],
)
async def workspace_info_root() -> WorkspaceInfoResponse:
    """Get workspace information (root app endpoint)."""
    return await execute_tool(
        "workspace",
        "info",
        {},
        lambda: workspace_tools.info(),
    )


# Workspace tools - Sub-app
@workspace_app.post(
    "/info",
    operation_id="workspace_info",
    summary="Get Workspace Information",
    description="""Get information about the workspace configuration.

Returns the default workspace directory, available paths, disk usage,
and available tool categories.

Use this tool when you need to:
- Understand the workspace boundaries
- Check available disk space
- See what tool categories are available
- Get the base workspace path for other operations

No parameters required.""",
    response_model=WorkspaceInfoResponse,
    tags=["workspace"],
)
async def workspace_info_sub() -> WorkspaceInfoResponse:
    """Get workspace information (sub-app endpoint)."""
    return await execute_tool(
        "workspace",
        "info",
        {},
        lambda: workspace_tools.info(),
    )


# Include admin API
from src.admin_api import router as admin_router
app.include_router(admin_router)

# Serve admin dashboard static files with SPA fallback
import os
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "admin")
if os.path.exists(static_dir):
    # Mount static assets
    app.mount("/admin/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="admin-assets")
    
    # Serve index.html for all admin routes (SPA fallback)
    @app.get("/admin/{full_path:path}")
    async def serve_admin(full_path: str):
        """Serve admin dashboard with SPA fallback."""
        # Try to serve the file if it exists
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise serve index.html (SPA fallback)
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    logger.info("admin_dashboard_mounted", path="/admin")
else:
    logger.warning("admin_dashboard_not_found", path=static_dir)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )


# WebSocket endpoint for HITL
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_error", error=str(e))
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

connection_manager = ConnectionManager()

# Register WebSocket callback with HITL manager
async def hitl_websocket_callback(event_type: str, data: dict):
    """Callback for HITL events to broadcast via WebSocket."""
    await connection_manager.broadcast({
        "type": event_type,
        "data": data,
    })

hitl_manager.register_websocket_callback(hitl_websocket_callback)


@app.websocket("/ws/hitl")
async def websocket_hitl(websocket: WebSocket):
    """WebSocket endpoint for HITL notifications and decisions."""
    await connection_manager.connect(websocket)
    
    try:
        # Send current pending requests
        pending = hitl_manager.get_pending_requests()
        await websocket.send_json({
            "type": "pending_requests",
            "data": [req.to_dict() for req in pending],
        })
        
        # Listen for decisions
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "request_pending":
                # Client is requesting current pending requests
                pending = hitl_manager.get_pending_requests()
                await websocket.send_json({
                    "type": "pending_requests",
                    "data": [req.to_dict() for req in pending],
                })
            
            elif data.get("type") == "hitl_decision":
                decision_data = data.get("data", {})
                request_id = decision_data.get("id")
                decision = decision_data.get("decision")
                note = decision_data.get("note")
                
                if not request_id or not decision:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Missing required fields: id and decision"},
                    })
                    continue
                
                try:
                    if decision == "approve":
                        await hitl_manager.approve(request_id, reviewer="admin", note=note)
                        await websocket.send_json({
                            "type": "decision_accepted",
                            "data": {"id": request_id, "decision": "approved"},
                        })
                    elif decision == "reject":
                        await hitl_manager.reject(request_id, reviewer="admin", note=note)
                        await websocket.send_json({
                            "type": "decision_accepted",
                            "data": {"id": request_id, "decision": "rejected"},
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": f"Invalid decision: {decision}"},
                        })
                
                except ValueError as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e), exc_info=True)
        connection_manager.disconnect(websocket)


# fs_write endpoints
@app.post(
    "/api/tools/fs/write",
    operation_id="fs_write",
    summary="Write File",
    description="""Write content to a file at the specified path.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Create new files
- Update existing files
- Append content to files
- Save generated content

Required: path, content
Optional: mode ('create', 'overwrite', 'append'), workspace_dir, create_dirs, encoding

Note: Writing to configuration files (*.conf, *.env, *.yaml, *.yml) requires approval.""",
    response_model=FsWriteResponse,
    tags=["filesystem"],
)
async def fs_write_root(request: FsWriteRequest) -> FsWriteResponse:
    """Write file contents (root app endpoint)."""
    return await execute_tool(
        "fs",
        "write",
        request.model_dump(),
        lambda: fs_tools.write(request),
    )


@fs_app.post(
    "/write",
    operation_id="fs_write",
    summary="Write File",
    description="""Write content to a file at the specified path.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Create new files
- Update existing files
- Append content to files
- Save generated content

Required: path, content
Optional: mode ('create', 'overwrite', 'append'), workspace_dir, create_dirs, encoding

Note: Writing to configuration files (*.conf, *.env, *.yaml, *.yml) requires approval.""",
    response_model=FsWriteResponse,
    tags=["filesystem"],
)
async def fs_write_sub(request: FsWriteRequest) -> FsWriteResponse:
    """Write file contents (sub-app endpoint)."""
    return await execute_tool(
        "fs",
        "write",
        request.model_dump(),
        lambda: fs_tools.write(request),
    )


# fs_list endpoints
@app.post(
    "/api/tools/fs/list",
    operation_id="fs_list",
    summary="List Directory",
    description="""List contents of a directory.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Browse directory contents
- Find files in a directory
- Explore project structure
- Check if files exist

Optional: path (default: '.'), workspace_dir, recursive, max_depth, include_hidden, pattern

Supports glob patterns like '*.py', 'test_*.txt' for filtering.""",
    response_model=FsListResponse,
    tags=["filesystem"],
)
async def fs_list_root(request: FsListRequest) -> FsListResponse:
    """List directory contents (root app endpoint)."""
    return await execute_tool(
        "fs",
        "list",
        request.model_dump(),
        lambda: fs_tools.list(request),
    )


@fs_app.post(
    "/list",
    operation_id="fs_list",
    summary="List Directory",
    description="""List contents of a directory.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Browse directory contents
- Find files in a directory
- Explore project structure
- Check if files exist

Optional: path (default: '.'), workspace_dir, recursive, max_depth, include_hidden, pattern

Supports glob patterns like '*.py', 'test_*.txt' for filtering.""",
    response_model=FsListResponse,
    tags=["filesystem"],
)
async def fs_list_sub(request: FsListRequest) -> FsListResponse:
    """List directory contents (sub-app endpoint)."""
    return await execute_tool(
        "fs",
        "list",
        request.model_dump(),
        lambda: fs_tools.list(request),
    )


# fs_search endpoints
@app.post(
    "/api/tools/fs/search",
    operation_id="fs_search",
    summary="Search Files",
    description="""Search for files by name or content.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Find files by name
- Search file contents
- Locate specific code or text
- Discover files matching patterns

Required: query
Optional: path (default: '.'), workspace_dir, search_type ('filename', 'content', 'both'), 
         regex, max_results, include_content_preview

Supports both simple text search and regex patterns.""",
    response_model=FsSearchResponse,
    tags=["filesystem"],
)
async def fs_search_root(request: FsSearchRequest) -> FsSearchResponse:
    """Search files (root app endpoint)."""
    return await execute_tool(
        "fs",
        "search",
        request.model_dump(),
        lambda: fs_tools.search(request),
    )


@fs_app.post(
    "/search",
    operation_id="fs_search",
    summary="Search Files",
    description="""Search for files by name or content.

The path is relative to the workspace directory unless an absolute 
path within the workspace is provided.

Use this tool when you need to:
- Find files by name
- Search file contents
- Locate specific code or text
- Discover files matching patterns

Required: query
Optional: path (default: '.'), workspace_dir, search_type ('filename', 'content', 'both'), 
         regex, max_results, include_content_preview

Supports both simple text search and regex patterns.""",
    response_model=FsSearchResponse,
    tags=["filesystem"],
)
async def fs_search_sub(request: FsSearchRequest) -> FsSearchResponse:
    """Search files (sub-app endpoint)."""
    return await execute_tool(
        "fs",
        "search",
        request.model_dump(),
        lambda: fs_tools.search(request),
    )


# shell_execute endpoints
@app.post(
    "/api/tools/shell/execute",
    operation_id="shell_execute",
    summary="Execute Shell Command",
    description="""Execute a shell command in the workspace.

Use this tool when you need to:
- Run system commands
- Execute build scripts
- Run tests
- Interact with CLI tools
- Perform system operations

Required: command
Optional: workspace_dir, timeout (default: 60s), env (environment variables)

Security notes:
- Commands with dangerous metacharacters (;, |, &, >, <, etc.) require approval
- Commands not in the allowlist require approval
- Use {{secret:KEY}} syntax in env values for sensitive data
- Output is truncated at 100KB

Allowlisted commands: ls, cat, echo, pwd, git, python, node, npm, docker, curl, and more.""",
    response_model=ShellExecuteResponse,
    tags=["shell"],
)
async def shell_execute_root(request: ShellExecuteRequest) -> ShellExecuteResponse:
    """Execute shell command (root app endpoint)."""
    # Check command safety for policy
    is_safe, reason = shell_tools._check_command_safety(request.command)
    
    # Evaluate policy with safety check
    decision, policy_reason = policy_engine.evaluate_shell_command(
        request.command,
        is_safe,
        reason,
    )
    
    # Handle policy decision
    if decision == "block":
        raise SecurityError(policy_reason or "Command execution blocked by policy")
    
    # Execute with HITL if needed
    if decision == "hitl":
        return await execute_tool(
            "shell",
            "execute",
            request.model_dump(),
            lambda: shell_tools.execute(request),
            force_hitl=True,
            hitl_reason=policy_reason or reason,
        )
    
    # Execute normally
    return await execute_tool(
        "shell",
        "execute",
        request.model_dump(),
        lambda: shell_tools.execute(request),
    )


# Create shell sub-app
shell_app = FastAPI(
    title="HostBridge — Shell Tools",
    description="Shell command execution for HostBridge",
    version="0.1.0",
)


@shell_app.post(
    "/execute",
    operation_id="shell_execute",
    summary="Execute Shell Command",
    description="""Execute a shell command in the workspace.

Use this tool when you need to:
- Run system commands
- Execute build scripts
- Run tests
- Interact with CLI tools
- Perform system operations

Required: command
Optional: workspace_dir, timeout (default: 60s), env (environment variables)

Security notes:
- Commands with dangerous metacharacters (;, |, &, >, <, etc.) require approval
- Commands not in the allowlist require approval
- Use {{secret:KEY}} syntax in env values for sensitive data
- Output is truncated at 100KB

Allowlisted commands: ls, cat, echo, pwd, git, python, node, npm, docker, curl, and more.""",
    response_model=ShellExecuteResponse,
    tags=["shell"],
)
async def shell_execute_sub(request: ShellExecuteRequest) -> ShellExecuteResponse:
    """Execute shell command (sub-app endpoint)."""
    # Check command safety for policy
    is_safe, reason = shell_tools._check_command_safety(request.command)
    
    # Evaluate policy with safety check
    decision, policy_reason = policy_engine.evaluate_shell_command(
        request.command,
        is_safe,
        reason,
    )
    
    # Handle policy decision
    if decision == "block":
        raise SecurityError(policy_reason or "Command execution blocked by policy")
    
    # Execute with HITL if needed
    if decision == "hitl":
        return await execute_tool(
            "shell",
            "execute",
            request.model_dump(),
            lambda: shell_tools.execute(request),
            force_hitl=True,
            hitl_reason=policy_reason or reason,
        )
    
    # Execute normally
    return await execute_tool(
        "shell",
        "execute",
        request.model_dump(),
        lambda: shell_tools.execute(request),
    )


# Create git sub-app
git_app = FastAPI(
    title="HostBridge — Git Tools",
    description="Git repository management for HostBridge",
    version="0.1.0",
)


# Git tool endpoints

@app.post(
    "/api/tools/git/status",
    operation_id="git_status",
    summary="Get Git Repository Status",
    description="""Get the current status of a git repository.

Shows:
- Current branch
- Staged files
- Unstaged changes
- Untracked files
- Commits ahead/behind remote

Use this tool to check the state of a repository before making changes.""",
    response_model=GitStatusResponse,
    tags=["git"],
)
async def git_status_root(request: GitStatusRequest) -> GitStatusResponse:
    """Get git repository status (root endpoint)."""
    return await execute_tool(
        "git",
        "status",
        request.model_dump(),
        lambda: git_tools.status(
            repo_path=request.repo_path,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/status",
    operation_id="git_status",
    summary="Get Git Repository Status",
    description="""Get the current status of a git repository.

Shows:
- Current branch
- Staged files
- Unstaged changes
- Untracked files
- Commits ahead/behind remote

Use this tool to check the state of a repository before making changes.""",
    response_model=GitStatusResponse,
    tags=["git"],
)
async def git_status_sub(request: GitStatusRequest) -> GitStatusResponse:
    """Get git repository status (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "status",
        request.model_dump(),
        lambda: git_tools.status(
            repo_path=request.repo_path,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/log",
    operation_id="git_log",
    summary="View Git Commit History",
    description="""View the commit history of a git repository.

Supports filtering by:
- Author
- Date range (since/until)
- File path
- Maximum number of commits

Use this tool to review recent changes or find specific commits.""",
    response_model=GitLogResponse,
    tags=["git"],
)
async def git_log_root(request: GitLogRequest) -> GitLogResponse:
    """View git commit history (root endpoint)."""
    return await execute_tool(
        "git",
        "log",
        request.model_dump(),
        lambda: git_tools.log(
            repo_path=request.repo_path,
            max_count=request.max_count,
            author=request.author,
            since=request.since,
            until=request.until,
            path=request.path,
            format=request.format,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/log",
    operation_id="git_log",
    summary="View Git Commit History",
    description="""View the commit history of a git repository.

Supports filtering by:
- Author
- Date range (since/until)
- File path
- Maximum number of commits

Use this tool to review recent changes or find specific commits.""",
    response_model=GitLogResponse,
    tags=["git"],
)
async def git_log_sub(request: GitLogRequest) -> GitLogResponse:
    """View git commit history (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "log",
        request.model_dump(),
        lambda: git_tools.log(
            repo_path=request.repo_path,
            max_count=request.max_count,
            author=request.author,
            since=request.since,
            until=request.until,
            path=request.path,
            format=request.format,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/diff",
    operation_id="git_diff",
    summary="View Git File Differences",
    description="""View file differences in a git repository.

Can show:
- Unstaged changes (default)
- Staged changes (--cached)
- Diff against specific commit/branch
- Statistics only (files changed, insertions, deletions)

Use this tool to review changes before committing.""",
    response_model=GitDiffResponse,
    tags=["git"],
)
async def git_diff_root(request: GitDiffRequest) -> GitDiffResponse:
    """View git file differences (root endpoint)."""
    return await execute_tool(
        "git",
        "diff",
        request.model_dump(),
        lambda: git_tools.diff(
            repo_path=request.repo_path,
            ref=request.ref,
            path=request.path,
            staged=request.staged,
            stat_only=request.stat_only,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/diff",
    operation_id="git_diff",
    summary="View Git File Differences",
    description="""View file differences in a git repository.

Can show:
- Unstaged changes (default)
- Staged changes (--cached)
- Diff against specific commit/branch
- Statistics only (files changed, insertions, deletions)

Use this tool to review changes before committing.""",
    response_model=GitDiffResponse,
    tags=["git"],
)
async def git_diff_sub(request: GitDiffRequest) -> GitDiffResponse:
    """View git file differences (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "diff",
        request.model_dump(),
        lambda: git_tools.diff(
            repo_path=request.repo_path,
            ref=request.ref,
            path=request.path,
            staged=request.staged,
            stat_only=request.stat_only,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/commit",
    operation_id="git_commit",
    summary="Create Git Commit",
    description="""Create a git commit with the specified message.

This operation:
- Stages specified files (or all changes if none specified)
- Creates a commit with the provided message
- Returns the commit hash and list of files committed

IMPORTANT: This operation requires approval by default as it modifies repository history.

Use this tool after reviewing changes with git_diff.""",
    response_model=GitCommitResponse,
    tags=["git"],
)
async def git_commit_root(request: GitCommitRequest) -> GitCommitResponse:
    """Create git commit (root endpoint)."""
    return await execute_tool(
        "git",
        "commit",
        request.model_dump(),
        lambda: git_tools.commit(
            message=request.message,
            repo_path=request.repo_path,
            files=request.files,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git commit requires approval",
    )


@git_app.post(
    "/commit",
    operation_id="git_commit",
    summary="Create Git Commit",
    description="""Create a git commit with the specified message.

This operation:
- Stages specified files (or all changes if none specified)
- Creates a commit with the provided message
- Returns the commit hash and list of files committed

IMPORTANT: This operation requires approval by default as it modifies repository history.

Use this tool after reviewing changes with git_diff.""",
    response_model=GitCommitResponse,
    tags=["git"],
)
async def git_commit_sub(request: GitCommitRequest) -> GitCommitResponse:
    """Create git commit (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "commit",
        request.model_dump(),
        lambda: git_tools.commit(
            message=request.message,
            repo_path=request.repo_path,
            files=request.files,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git commit requires approval",
    )


@app.post(
    "/api/tools/git/push",
    operation_id="git_push",
    summary="Push to Git Remote",
    description="""Push commits to a remote repository.

This operation:
- Pushes commits to the specified remote and branch
- Can force push if needed (use with caution)
- Returns number of commits pushed

IMPORTANT: This operation requires approval by default as it modifies remote repository.

Use {{secret:KEY}} syntax for git credentials in environment variables.

Example with credentials:
Set GIT_ASKPASS environment variable to use stored credentials.""",
    response_model=GitPushResponse,
    tags=["git"],
)
async def git_push_root(request: GitPushRequest) -> GitPushResponse:
    """Push to git remote (root endpoint)."""
    return await execute_tool(
        "git",
        "push",
        request.model_dump(),
        lambda: git_tools.push(
            repo_path=request.repo_path,
            remote=request.remote,
            branch=request.branch,
            force=request.force,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git push requires approval",
    )


@git_app.post(
    "/push",
    operation_id="git_push",
    summary="Push to Git Remote",
    description="""Push commits to a remote repository.

This operation:
- Pushes commits to the specified remote and branch
- Can force push if needed (use with caution)
- Returns number of commits pushed

IMPORTANT: This operation requires approval by default as it modifies remote repository.

Use {{secret:KEY}} syntax for git credentials in environment variables.

Example with credentials:
Set GIT_ASKPASS environment variable to use stored credentials.""",
    response_model=GitPushResponse,
    tags=["git"],
)
async def git_push_sub(request: GitPushRequest) -> GitPushResponse:
    """Push to git remote (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "push",
        request.model_dump(),
        lambda: git_tools.push(
            repo_path=request.repo_path,
            remote=request.remote,
            branch=request.branch,
            force=request.force,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git push requires approval",
    )


@app.post(
    "/api/tools/git/pull",
    operation_id="git_pull",
    summary="Pull from Git Remote",
    description="""Pull commits from a remote repository.

This operation:
- Fetches and merges (or rebases) commits from remote
- Returns list of files changed
- Can use rebase instead of merge

Use {{secret:KEY}} syntax for git credentials in environment variables.""",
    response_model=GitPullResponse,
    tags=["git"],
)
async def git_pull_root(request: GitPullRequest) -> GitPullResponse:
    """Pull from git remote (root endpoint)."""
    return await execute_tool(
        "git",
        "pull",
        request.model_dump(),
        lambda: git_tools.pull(
            repo_path=request.repo_path,
            remote=request.remote,
            branch=request.branch,
            rebase=request.rebase,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/pull",
    operation_id="git_pull",
    summary="Pull from Git Remote",
    description="""Pull commits from a remote repository.

This operation:
- Fetches and merges (or rebases) commits from remote
- Returns list of files changed
- Can use rebase instead of merge

Use {{secret:KEY}} syntax for git credentials in environment variables.""",
    response_model=GitPullResponse,
    tags=["git"],
)
async def git_pull_sub(request: GitPullRequest) -> GitPullResponse:
    """Pull from git remote (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "pull",
        request.model_dump(),
        lambda: git_tools.pull(
            repo_path=request.repo_path,
            remote=request.remote,
            branch=request.branch,
            rebase=request.rebase,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/checkout",
    operation_id="git_checkout",
    summary="Git Checkout Branch or Commit",
    description="""Switch to a different branch or commit.

This operation:
- Switches to the specified branch or commit
- Can create a new branch if requested
- Returns previous and current branch

IMPORTANT: This operation requires approval by default as it modifies working tree.

Use this tool to switch between branches or restore files.""",
    response_model=GitCheckoutResponse,
    tags=["git"],
)
async def git_checkout_root(request: GitCheckoutRequest) -> GitCheckoutResponse:
    """Git checkout (root endpoint)."""
    return await execute_tool(
        "git",
        "checkout",
        request.model_dump(),
        lambda: git_tools.checkout(
            target=request.target,
            repo_path=request.repo_path,
            create=request.create,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git checkout requires approval",
    )


@git_app.post(
    "/checkout",
    operation_id="git_checkout",
    summary="Git Checkout Branch or Commit",
    description="""Switch to a different branch or commit.

This operation:
- Switches to the specified branch or commit
- Can create a new branch if requested
- Returns previous and current branch

IMPORTANT: This operation requires approval by default as it modifies working tree.

Use this tool to switch between branches or restore files.""",
    response_model=GitCheckoutResponse,
    tags=["git"],
)
async def git_checkout_sub(request: GitCheckoutRequest) -> GitCheckoutResponse:
    """Git checkout (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "checkout",
        request.model_dump(),
        lambda: git_tools.checkout(
            target=request.target,
            repo_path=request.repo_path,
            create=request.create,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=True,
        hitl_reason="Git checkout requires approval",
    )


@app.post(
    "/api/tools/git/branch",
    operation_id="git_branch",
    summary="Create or Delete Git Branch",
    description="""Create or delete a git branch.

This operation:
- Creates a new branch from current HEAD
- Or deletes an existing branch
- Can force delete unmerged branches

IMPORTANT: Branch deletion requires approval by default.

Use git_list_branches to see available branches.""",
    response_model=GitBranchResponse,
    tags=["git"],
)
async def git_branch_root(request: GitBranchRequest) -> GitBranchResponse:
    """Create or delete git branch (root endpoint)."""
    force_hitl = request.action == "delete"
    return await execute_tool(
        "git",
        "branch",
        request.model_dump(),
        lambda: git_tools.branch(
            name=request.name,
            repo_path=request.repo_path,
            action=request.action,
            force=request.force,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=force_hitl,
        hitl_reason="Git branch deletion requires approval" if force_hitl else None,
    )


@git_app.post(
    "/branch",
    operation_id="git_branch",
    summary="Create or Delete Git Branch",
    description="""Create or delete a git branch.

This operation:
- Creates a new branch from current HEAD
- Or deletes an existing branch
- Can force delete unmerged branches

IMPORTANT: Branch deletion requires approval by default.

Use git_list_branches to see available branches.""",
    response_model=GitBranchResponse,
    tags=["git"],
)
async def git_branch_sub(request: GitBranchRequest) -> GitBranchResponse:
    """Create or delete git branch (sub-app endpoint)."""
    force_hitl = request.action == "delete"
    return await execute_tool(
        "git",
        "branch",
        request.model_dump(),
        lambda: git_tools.branch(
            name=request.name,
            repo_path=request.repo_path,
            action=request.action,
            force=request.force,
            workspace_dir=request.workspace_dir,
        ),
        force_hitl=force_hitl,
        hitl_reason="Git branch deletion requires approval" if force_hitl else None,
    )


@app.post(
    "/api/tools/git/list_branches",
    operation_id="git_list_branches",
    summary="List Git Branches",
    description="""List all branches in a git repository.

Shows:
- Branch names
- Current branch indicator
- Remote branches (if requested)
- Last commit on each branch

Use this tool to see available branches before checkout.""",
    response_model=GitListBranchesResponse,
    tags=["git"],
)
async def git_list_branches_root(request: GitListBranchesRequest) -> GitListBranchesResponse:
    """List git branches (root endpoint)."""
    return await execute_tool(
        "git",
        "list_branches",
        request.model_dump(),
        lambda: git_tools.list_branches(
            repo_path=request.repo_path,
            remote=request.remote,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/list_branches",
    operation_id="git_list_branches",
    summary="List Git Branches",
    description="""List all branches in a git repository.

Shows:
- Branch names
- Current branch indicator
- Remote branches (if requested)
- Last commit on each branch

Use this tool to see available branches before checkout.""",
    response_model=GitListBranchesResponse,
    tags=["git"],
)
async def git_list_branches_sub(request: GitListBranchesRequest) -> GitListBranchesResponse:
    """List git branches (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "list_branches",
        request.model_dump(),
        lambda: git_tools.list_branches(
            repo_path=request.repo_path,
            remote=request.remote,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/stash",
    operation_id="git_stash",
    summary="Git Stash Operations",
    description="""Manage git stash (temporary storage for changes).

Supported actions:
- push: Save current changes to stash
- pop: Apply and remove most recent stash
- list: Show all stashes
- drop: Remove a specific stash

Use this tool to temporarily save work in progress.""",
    response_model=GitStashResponse,
    tags=["git"],
)
async def git_stash_root(request: GitStashRequest) -> GitStashResponse:
    """Git stash operations (root endpoint)."""
    return await execute_tool(
        "git",
        "stash",
        request.model_dump(),
        lambda: git_tools.stash(
            repo_path=request.repo_path,
            action=request.action,
            message=request.message,
            index=request.index,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/stash",
    operation_id="git_stash",
    summary="Git Stash Operations",
    description="""Manage git stash (temporary storage for changes).

Supported actions:
- push: Save current changes to stash
- pop: Apply and remove most recent stash
- list: Show all stashes
- drop: Remove a specific stash

Use this tool to temporarily save work in progress.""",
    response_model=GitStashResponse,
    tags=["git"],
)
async def git_stash_sub(request: GitStashRequest) -> GitStashResponse:
    """Git stash operations (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "stash",
        request.model_dump(),
        lambda: git_tools.stash(
            repo_path=request.repo_path,
            action=request.action,
            message=request.message,
            index=request.index,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/show",
    operation_id="git_show",
    summary="Show Git Commit Details",
    description="""Show detailed information about a specific commit.

Returns:
- Commit hash and metadata
- Author and date
- Commit message and body
- Full diff of changes
- List of files changed

Use this tool to inspect a specific commit.""",
    response_model=GitShowResponse,
    tags=["git"],
)
async def git_show_root(request: GitShowRequest) -> GitShowResponse:
    """Show git commit details (root endpoint)."""
    return await execute_tool(
        "git",
        "show",
        request.model_dump(),
        lambda: git_tools.show(
            repo_path=request.repo_path,
            ref=request.ref,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/show",
    operation_id="git_show",
    summary="Show Git Commit Details",
    description="""Show detailed information about a specific commit.

Returns:
- Commit hash and metadata
- Author and date
- Commit message and body
- Full diff of changes
- List of files changed

Use this tool to inspect a specific commit.""",
    response_model=GitShowResponse,
    tags=["git"],
)
async def git_show_sub(request: GitShowRequest) -> GitShowResponse:
    """Show git commit details (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "show",
        request.model_dump(),
        lambda: git_tools.show(
            repo_path=request.repo_path,
            ref=request.ref,
            workspace_dir=request.workspace_dir,
        ),
    )


@app.post(
    "/api/tools/git/remote",
    operation_id="git_remote",
    summary="Manage Git Remotes",
    description="""Manage git remote repositories.

Supported actions:
- list: Show all configured remotes
- add: Add a new remote
- remove: Remove an existing remote

Use this tool to configure remote repositories.""",
    response_model=GitRemoteResponse,
    tags=["git"],
)
async def git_remote_root(request: GitRemoteRequest) -> GitRemoteResponse:
    """Manage git remotes (root endpoint)."""
    return await execute_tool(
        "git",
        "remote",
        request.model_dump(),
        lambda: git_tools.remote(
            repo_path=request.repo_path,
            action=request.action,
            name=request.name,
            url=request.url,
            workspace_dir=request.workspace_dir,
        ),
    )


@git_app.post(
    "/remote",
    operation_id="git_remote",
    summary="Manage Git Remotes",
    description="""Manage git remote repositories.

Supported actions:
- list: Show all configured remotes
- add: Add a new remote
- remove: Remove an existing remote

Use this tool to configure remote repositories.""",
    response_model=GitRemoteResponse,
    tags=["git"],
)
async def git_remote_sub(request: GitRemoteRequest) -> GitRemoteResponse:
    """Manage git remotes (sub-app endpoint)."""
    return await execute_tool(
        "git",
        "remote",
        request.model_dump(),
        lambda: git_tools.remote(
            repo_path=request.repo_path,
            action=request.action,
            name=request.name,
            url=request.url,
            workspace_dir=request.workspace_dir,
        ),
    )


# Initialize and mount MCP server using Streamable HTTP transport (recommended)
# IMPORTANT: This must be done AFTER all endpoints are defined, as fastapi-mcp
# discovers tools at mount time
mcp = FastApiMCP(app)
mcp.mount_http()
logger.info("mcp_server_mounted", path="/mcp", transport="streamable_http")

# Mount sub-apps
app.mount("/tools/fs", fs_app)
app.mount("/tools/workspace", workspace_app)
app.mount("/tools/shell", shell_app)
app.mount("/tools/git", git_app)
