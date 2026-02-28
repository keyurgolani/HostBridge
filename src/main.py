"""Main FastAPI application."""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import load_config
from src.database import Database
from src.logging_config import setup_logging, get_logger
from src.workspace import WorkspaceManager, SecurityError
from src.audit import AuditLogger
from src.policy import PolicyEngine
from src.tools.fs_tools import FilesystemTools
from src.tools.workspace_tools import WorkspaceTools
from src.models import (
    FsReadRequest,
    FsReadResponse,
    WorkspaceInfoResponse,
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

# Initialize tools
fs_tools = FilesystemTools(workspace_manager)
workspace_tools = WorkspaceTools(workspace_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("starting_hostbridge", version="0.1.0")
    await db.connect()
    logger.info("hostbridge_started")
    
    yield
    
    # Shutdown
    logger.info("shutting_down_hostbridge")
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
):
    """Execute a tool with policy enforcement and audit logging.
    
    Args:
        tool_category: Tool category
        tool_name: Tool name
        params: Tool parameters
        tool_func: Tool function to execute
        protocol: Protocol used (openapi or mcp)
        
    Returns:
        Tool execution result
    """
    start_time = time.time()
    
    # Policy check
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
    
    # TODO: HITL implementation in Slice 2
    if decision == "hitl":
        logger.warning("hitl_not_implemented", tool=f"{tool_category}_{tool_name}")
        # For now, allow it (HITL will be implemented in Slice 2)
    
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
            status="success",
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


# Mount sub-apps
app.mount("/tools/fs", fs_app)
app.mount("/tools/workspace", workspace_app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )
