# HostBridge

**Unified MCP + OpenAPI Tool Server for Self-Hosted LLM Stacks**

HostBridge exposes host-machine management capabilities to LLM applications via industry-standard protocols (MCP and OpenAPI). Built for self-hosters running local LLM stacks who want their AI to interact with the host machine in a controlled, auditable manner.

## Features

- **Dual Protocol Support**: Serve tools via both OpenAPI (REST) and MCP (Model Context Protocol) simultaneously
- **MCP Streamable HTTP**: Modern MCP transport using Streamable HTTP (not legacy SSE)
- **Single Source of Truth**: Tools defined once, automatically exposed via both protocols
- **Human-in-the-Loop (HITL)**: Real-time approval system for sensitive operations via WebSocket
- **Security First**: Workspace sandboxing, path traversal prevention, and comprehensive security checks
- **Policy Engine**: Configurable allow/block/HITL rules per tool with pattern matching
- **Complete Audit Trail**: SQLite-based logging of all tool executions with request/response capture
- **File Management**: Read and write files with create/overwrite/append modes
- **Flexible Registration**: Single endpoint for all tools or per-category endpoints for granular control
- **LLM-Optimized**: Flat parameter structures and exhaustive descriptions for better tool selection

## Quick Start

### Prerequisites

- Docker and Docker Compose
- A workspace directory to expose to the LLM

### Installation

1. Clone the repository:
```bash
git clone https://github.com/keyurgolani/HostBridge.git
cd HostBridge
```

2. Copy example configuration files:
```bash
cp .env.example .env
cp config.example.yaml config.yaml
cp secrets.example.env secrets.env
```

3. Edit `.env` to configure your workspace:
```bash
# Required
ADMIN_PASSWORD=your-secure-password

# Workspace - point to your directory
HOST_WORKSPACE_DIR=/path/to/your/workspace
```

4. Edit `config.yaml` to configure tool policies (optional)

5. Start the server:
```bash
docker compose up -d
```

5. Verify it's running:
```bash
curl http://localhost:8080/health
```

The server is now available at `http://localhost:8080`

## Usage

### API Documentation

Interactive API documentation is available at:
- Root app: `http://localhost:8080/docs`
- Filesystem tools: `http://localhost:8080/tools/fs/docs`
- Workspace tools: `http://localhost:8080/tools/workspace/docs`

### Available Tools

#### Workspace Info

Get workspace configuration and disk usage:

```bash
curl -X POST http://localhost:8080/api/tools/workspace/info
```

#### Read File

Read file contents with optional line ranges:

```bash
# Basic usage
curl -X POST http://localhost:8080/api/tools/fs/read \
  -H "Content-Type: application/json" \
  -d '{"path": "README.md"}'

# With line range
curl -X POST http://localhost:8080/api/tools/fs/read \
  -H "Content-Type: application/json" \
  -d '{"path": "file.txt", "line_start": 10, "line_end": 20}'

# With max lines limit
curl -X POST http://localhost:8080/api/tools/fs/read \
  -H "Content-Type: application/json" \
  -d '{"path": "large_file.txt", "max_lines": 100}'
```

#### Write File

Write content to files with multiple modes:

```bash
# Create new file
curl -X POST http://localhost:8080/api/tools/fs/write \
  -H "Content-Type: application/json" \
  -d '{"path": "newfile.txt", "content": "Hello, World!", "mode": "create"}'

# Overwrite existing file
curl -X POST http://localhost:8080/api/tools/fs/write \
  -H "Content-Type: application/json" \
  -d '{"path": "existing.txt", "content": "New content", "mode": "overwrite"}'

# Append to file
curl -X POST http://localhost:8080/api/tools/fs/write \
  -H "Content-Type: application/json" \
  -d '{"path": "log.txt", "content": "\nNew log entry", "mode": "append"}'

# Create nested directories
curl -X POST http://localhost:8080/api/tools/fs/write \
  -H "Content-Type: application/json" \
  -d '{"path": "nested/deep/file.txt", "content": "Content", "mode": "create", "create_dirs": true}'
```

**Note**: Writing to configuration files (*.conf, *.env, *.yaml, *.yml) requires HITL approval by default.

### Integration with LLM Applications

#### MCP Clients (Claude Desktop, Cursor, etc.)

Configure the MCP server in your client's configuration:

```json
{
  "mcpServers": {
    "hostbridge": {
      "url": "http://localhost:8080/mcp",
      "description": "HostBridge - Local filesystem and workspace operations"
    }
  }
}
```

**Features:**
- Streamable HTTP transport (modern, recommended)
- Automatic tool discovery from FastAPI endpoints
- Session management with session IDs
- JSON-RPC 2.0 compliant

**Available MCP Tools:**
- `health_check_health_get` - Server health check
- `fs_read` - Read file contents
- `fs_write` - Write/create/append files
- `workspace_info` - Get workspace configuration

#### Open WebUI

1. Go to Settings → Tools
2. Click "Add Tool Server"
3. Enter URL: `http://hostbridge:8080/` (if in same Docker network) or `http://localhost:8080/`
4. Tools will appear in your chat interface

#### Other OpenAPI-Compatible Clients

Register the OpenAPI endpoint:
- All tools: `http://localhost:8080/openapi.json`
- Filesystem only: `http://localhost:8080/tools/fs/openapi.json`
- Workspace only: `http://localhost:8080/tools/workspace/openapi.json`

## Human-in-the-Loop (HITL) System

HostBridge includes a real-time approval system for sensitive operations. When a tool call requires approval, the HTTP connection blocks while waiting for admin decision via WebSocket.

### How It Works

1. LLM makes a tool call that requires approval (e.g., writing to a config file)
2. Server creates HITL request and holds the connection
3. Admin receives real-time notification via WebSocket
4. Admin approves or rejects the request
5. Server executes (if approved) or returns error (if rejected)
6. LLM receives the result

This is completely transparent to the LLM - it simply experiences a slow tool call.

### WebSocket Connection

Connect to the HITL WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/hitl');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'hitl_request') {
    const request = data.data;
    console.log('Approval needed:', request.tool_name);
    console.log('Parameters:', request.request_params);
    
    // Send approval
    ws.send(JSON.stringify({
      type: 'hitl_decision',
      data: {
        id: request.id,
        decision: 'approve',  // or 'reject'
        note: 'Looks safe'
      }
    }));
  }
};
```

### HITL Configuration

Configure which operations require approval in `config.yaml`:

```yaml
hitl:
  default_ttl_seconds: 300  # 5 minutes timeout

tools:
  fs:
    write:
      policy: "allow"
      hitl_patterns:
        - "*.conf"
        - "*.env"
        - "*.yaml"
        - "*.yml"
      block_patterns:
        - "*.exe"
        - "*.bin"
```

**Note**: An admin dashboard for HITL management is planned for a future release.

### Registration Modes

HostBridge supports two registration modes:

**Mode A: Single URL (All Tools)**
- Register `http://localhost:8080/` to access all tools
- Best for: Simple setups, full access

**Mode B: Per-Category URLs**
- Register individual categories as separate servers
- `http://localhost:8080/tools/fs/` - Filesystem tools only
- `http://localhost:8080/tools/workspace/` - Workspace tools only
- Best for: Granular control, limiting tool access per model

## Configuration

### Environment Variables

Edit `.env`:

```env
# Required
ADMIN_PASSWORD=changeme

# Workspace
WORKSPACE_BASE_DIR=/workspace
HOST_WORKSPACE_DIR=./workspace

# Optional
HOSTBRIDGE_PORT=8080
AUDIT_RETENTION_DAYS=30
LOG_LEVEL=INFO
```

### Tool Policies

Edit `config.yaml` to configure per-tool policies:

```yaml
tools:
  fs:
    read:
      policy: "allow"  # "allow", "block", or "hitl"
      workspace_override: "allow"
    write:
      policy: "allow"
      hitl_patterns:
        - "*.conf"
        - "*.env"
      block_patterns:
        - "*.exe"
        - "*.bin"
```

### Workspace Management

Configure your workspace directory in `.env`:

```env
HOST_WORKSPACE_DIR=/path/to/your/workspace
```

Then restart:
```bash
docker compose restart
```

## Security

HostBridge implements defense-in-depth security:

1. **Docker Isolation**: Container-level isolation from host
2. **Workspace Boundaries**: All file operations sandboxed to configured directories
3. **Path Resolution**: Comprehensive checks prevent path traversal attacks
4. **Policy Engine**: Configurable allow/block rules per tool
5. **Audit Logging**: Complete request/response logging for accountability

### Security Features

- Path traversal prevention (`../` attacks blocked)
- Symlink resolution and validation
- Null byte detection
- Workspace boundary enforcement
- Pattern-based blocking (e.g., block `*.exe` files)

Example of blocked operation:
```bash
curl -X POST http://localhost:8080/api/tools/fs/read \
  -H "Content-Type: application/json" \
  -d '{"path": "../../etc/passwd"}'

# Returns 403 Forbidden:
# "Path escapes workspace boundary"
```

## Error Handling

HostBridge returns structured error responses with helpful suggestions:

```json
{
  "error": true,
  "error_type": "file_not_found",
  "message": "File not found: nonexistent.txt. Use fs_list to see available files.",
  "suggestion_tool": "fs_list"
}
```

Error types:
- `security_error` (403) - Path escapes workspace or violates policy
- `file_not_found` (404) - File doesn't exist
- `invalid_parameter` (400) - Invalid request parameters
- `internal_error` (500) - Unexpected server error

## Monitoring

### View Logs

```bash
docker compose logs -f hostbridge
```

### Check Status

```bash
docker compose ps
```

### Restart Container

```bash
docker compose restart hostbridge
```

## Development

### Running Tests

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
pytest -v
```

### Local Development

```bash
# Run without Docker
source venv/bin/activate
python -m src.main
```

## Architecture

- **Framework**: FastAPI with Uvicorn
- **Database**: SQLite (via aiosqlite)
- **Logging**: Structured logging with structlog
- **Deployment**: Docker container with Docker Compose

### Project Structure

```
HostBridge/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── workspace.py         # Path resolution & security
│   ├── policy.py            # Policy enforcement
│   ├── audit.py             # Audit logging
│   ├── database.py          # SQLite management
│   └── tools/               # Tool implementations
│       ├── fs_tools.py      # Filesystem tools
│       └── workspace_tools.py
├── tests/                   # Test suite
├── config.yaml              # Tool policies
├── docker-compose.yaml      # Docker deployment
└── .env                     # Environment configuration
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs hostbridge
```

Common issues:
- Port 8080 in use: Change `HOSTBRIDGE_PORT` in `.env`
- Permission denied: Check volume mount permissions

### Tool returns 403 Forbidden

The path is outside workspace boundaries. Verify:
1. File path is relative to workspace
2. Workspace directory is correctly mounted
3. No path traversal attempts (`../`)

### Tool returns 404 Not Found

File doesn't exist. Use `workspace_info` to check workspace path.

## Roadmap

Planned features:
- Admin dashboard for HITL monitoring and approval (UI in progress)
- Additional filesystem tools (list, delete, search, copy, move)
- Git tools (status, commit, push, pull, branch management)
- Docker container management tools
- Shell execution tools with output capture
- Secret management with template resolution (`{{secret:KEY}}` syntax)
- HTTP client tool for API requests
- Memory/knowledge graph tools for persistent storage
- Plan/DAG execution tools for multi-step workflows

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built for the self-hosting community running local LLM stacks (Open WebUI, Ollama, LM Studio, etc.)
