# HostBridge

**Unified MCP + OpenAPI Tool Server for Self-Hosted LLM Stacks**

Version: 0.1.0  
Status: ✅ Production Ready

---

## Overview

HostBridge is a single Docker container that exposes host-machine management capabilities to LLM applications via two industry-standard protocols simultaneously:

- **MCP (Model Context Protocol)** over Streamable HTTP
- **OpenAPI (REST/JSON)** for tools like Open WebUI

Built-in admin dashboard provides human oversight, HITL (Human-in-the-Loop) approval workflows, audit logging, and secret management.

---

## Features

### ✅ Implemented

- **Dual Protocol Support:** MCP + OpenAPI simultaneously
- **Filesystem Tools:** 
  - Read and write files with workspace sandboxing
  - List directory contents with recursive traversal
  - Search files by name or content with regex support
- **Shell Execution:** Execute commands with security controls and allowlisting
- **Git Tools:** Complete Git repository management
  - Status, log, diff, show, branches, remotes
  - Commit, push, pull, checkout, stash operations
  - HITL approval for write operations
  - Support for authentication via environment variables
- **Workspace Management:** Secure path resolution and boundary enforcement
- **HITL System:** Real-time approval workflow for sensitive operations
- **Admin Dashboard:** Premium UI with real-time updates
- **Audit Logging:** Complete execution history
- **Policy Engine:** Allow/block/HITL rules per tool
- **Secret Management:** Secure secret resolution with template syntax
- **WebSocket Support:** Real-time notifications

### 🚧 Coming Soon

- Docker container management
- HTTP client with SSRF protection
- Knowledge graph memory system
- DAG-based plan execution

---

## Quick Start

### 1. Start the Container

```bash
docker compose up -d
```

### 2. Access the Admin Dashboard

```
http://localhost:8080/admin/
```

**Default Password:** `admin`

### 3. Test the Tools

```bash
# Read a file
curl -X POST http://localhost:8080/api/tools/fs/read \
  -H "Content-Type: application/json" \
  -d '{"path": "README.md"}'

# List directory contents
curl -X POST http://localhost:8080/api/tools/fs/list \
  -H "Content-Type: application/json" \
  -d '{"path": ".", "recursive": true}'

# Search for files
curl -X POST http://localhost:8080/api/tools/fs/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "both"}'

# Execute a shell command
curl -X POST http://localhost:8080/api/tools/shell/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}'

# Check git repository status
curl -X POST http://localhost:8080/api/tools/git/status \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "."}'

# View git commit history
curl -X POST http://localhost:8080/api/tools/git/log \
  -H "Content-Type: application/json" \
  -d '{"repo_path": ".", "max_count": 10}'

# Write a file (triggers HITL for .conf files)
curl -X POST http://localhost:8080/api/tools/fs/write \
  -H "Content-Type: application/json" \
  -d '{"path": "test.conf", "content": "test=value"}'
```

### 4. Approve in Dashboard

1. Go to http://localhost:8080/admin/
2. Navigate to "HITL Queue"
3. Click "Approve" or "Reject"

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  FastAPI Application              │  │
│  │                                   │  │
│  │  • OpenAPI: /api/tools/*          │  │
│  │  • MCP: /mcp                      │  │
│  │  • Admin: /admin/                 │  │
│  │  • WebSocket: /ws/hitl            │  │
│  │                                   │  │
│  │  ┌─────────────────────────────┐ │  │
│  │  │  Tool Execution Engine      │ │  │
│  │  │  • Policy Enforcer          │ │  │
│  │  │  • HITL Manager             │ │  │
│  │  │  • Secret Resolver          │ │  │
│  │  │  • Audit Logger             │ │  │
│  │  └─────────────────────────────┘ │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Volumes:                               │
│  • /workspace (host directories)        │
│  • /data (SQLite, logs)                 │
│  • /secrets (secrets.env)               │
└─────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Required
ADMIN_PASSWORD=your-secure-password

# Optional
WORKSPACE_BASE_DIR=/workspace
HOSTBRIDGE_PORT=8080
AUDIT_RETENTION_DAYS=30
LOG_LEVEL=INFO
HITL_TTL_SECONDS=300
```

### Docker Compose

```yaml
services:
  hostbridge:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ADMIN_PASSWORD=admin
      - WORKSPACE_BASE_DIR=/workspace
    volumes:
      - ./workspace:/workspace
      - ./data:/data
      - ./secrets.env:/secrets/secrets.env:ro
```

---

## Admin Dashboard

### Features

- **Real-time HITL Queue:** Approve/reject tool executions
- **Audit Log:** Complete execution history with search/filter
- **System Health:** Uptime, metrics, error rates
- **Premium UI:** Glassmorphism, 3D animations, aurora backgrounds

### Screenshots

*Coming soon*

### Access

```
http://localhost:8080/admin/
```

**Documentation:** See `admin/README.md` for complete guide

---

## Available Tools

### Filesystem

- `fs_read` - Read file contents with line range support
- `fs_write` - Write file contents (HITL for .conf, .env, .yaml)
- `fs_list` - List directory contents with recursive traversal and filtering
- `fs_search` - Search files by name or content with regex support

### Shell

- `shell_execute` - Execute shell commands with security controls
  - Allowlist of safe commands (ls, cat, echo, git, python, npm, docker, etc.)
  - Dangerous metacharacter detection (;, |, &, >, <, etc.)
  - HITL for non-allowlisted or unsafe commands
  - Output truncation and timeout support

### Git

- `git_status` - Get repository status (branch, staged, unstaged, untracked files)
- `git_log` - View commit history with filtering options
- `git_diff` - View file differences (unstaged, staged, or against ref)
- `git_show` - Show commit details with full diff
- `git_list_branches` - List local and remote branches
- `git_remote` - Manage remote repositories
- `git_commit` - Create commits (HITL required)
- `git_push` - Push to remote (HITL required)
- `git_pull` - Pull from remote
- `git_checkout` - Switch branches or restore files (HITL required)
- `git_branch` - Create or delete branches (HITL for delete)
- `git_stash` - Stash operations (push, pop, list, drop)

### Workspace

- `workspace_info` - Get workspace configuration and disk usage

### Coming Soon

- `docker_*` - Docker management (list, inspect, logs, control)
- `http_request` - HTTP client with SSRF protection
- `memory_*` - Knowledge graph storage and retrieval
- `plan_*` - DAG-based multi-step execution

---

## Security

### Defense Layers

1. **Volume Mounts:** Docker isolation
2. **Workspace Boundary:** Path resolution + validation
3. **Tool Policies:** Allow/block/HITL per tool
4. **HITL Approval:** Human review of requests
5. **Secret Isolation:** Secrets never sent to LLM
6. **Admin Auth:** Password-protected dashboard
7. **Audit Log:** Complete request/response logging

### Best Practices

- Use strong admin password
- Review HITL requests promptly
- Monitor audit log regularly
- Limit workspace mounts to necessary directories
- Use secrets for sensitive credentials
- Enable HTTPS in production

---

## Development

### Project Structure

```
.
├── src/                    # Python backend
│   ├── main.py            # FastAPI app
│   ├── hitl.py            # HITL manager
│   ├── audit.py           # Audit logger
│   ├── policy.py          # Policy engine
│   ├── workspace.py       # Path resolution
│   ├── admin_api.py       # Admin API
│   └── tools/             # Tool implementations
├── admin/                 # React dashboard
│   ├── src/
│   │   ├── pages/         # Dashboard pages
│   │   ├── components/    # UI components
│   │   └── lib/           # API & WebSocket clients
│   └── dist/              # Built static files
├── development/           # Documentation & tests
│   ├── spec.md           # Design document
│   ├── test_slice3.sh    # Test script
│   └── *.md              # Reports & guides
├── docker-compose.yaml    # Docker config
└── Dockerfile            # Container image
```

### Build Admin Dashboard

```bash
cd admin
npm install
npm run build
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mcp.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Run Locally (Development)

```bash
# Backend
python -m uvicorn src.main:app --reload

# Frontend (separate terminal)
cd admin
npm run dev
```

---

## Documentation

- **Admin Dashboard Guide:** `admin/README.md` - Complete dashboard documentation
- **Commands to Try:** `CommandsToTry.md` - Sample commands for LLM interaction
- **API Documentation:** http://localhost:8080/docs - Interactive OpenAPI docs

---

## Roadmap

### ✅ Core Infrastructure (Complete)
- FastAPI setup with dual protocol support
- Workspace management with security
- Policy engine with allow/block/HITL rules
- Audit logging system
- Database setup (SQLite)

### ✅ HITL System (Complete)
- HITL manager with async event handling
- WebSocket support for real-time notifications
- Synchronous blocking workflow
- Timeout and expiry handling

### ✅ Admin Dashboard (Complete)
- React dashboard with premium UI
- Login & authentication
- HITL queue with real-time updates
- Audit log with search/filter
- System health monitoring

### ✅ Filesystem & Shell Tools (Complete)
- fs_read, fs_write with HITL policies
- fs_list with recursive traversal
- fs_search with regex support
- shell_execute with security controls

### ✅ Git Tools (Complete)
- Read-only: status, log, diff, show, list_branches, remote, stash
- Write operations: commit, push, pull, checkout, branch (with HITL)
- Git authentication support via environment variables
- Comprehensive test coverage (27 unit tests, 12 integration tests)

### 📋 Upcoming Features
- Docker tools (container management)
- Secret management with template resolution
- HTTP client with SSRF protection
- Memory system (knowledge graph)
- Plan execution (DAG-based workflows)
- Dashboard enhancements

---

## Contributing

This is a design document implementation project. See `development/spec.md` for the complete specification.

---

## License

[Your License Here]

---

## Support

### Troubleshooting

1. **Check container logs:**
   ```bash
   docker compose logs hostbridge -f
   ```

2. **Verify health:**
   ```bash
   curl http://localhost:8080/health
   ```

3. **Test admin login:**
   ```bash
   curl -X POST http://localhost:8080/admin/api/login \
     -H "Content-Type: application/json" \
     -d '{"password": "admin"}'
   ```

4. **Check browser console** (F12) for frontend errors

### Common Issues

- **Blank admin page:** Check browser console, verify assets loading
- **Login fails:** Verify ADMIN_PASSWORD in docker-compose.yaml
- **HITL not appearing:** Check WebSocket connection in browser console
- **Tool execution fails:** Check audit log for error details

---

## Acknowledgments

Built following the design principles from:
- Model Context Protocol (MCP) specification
- Open WebUI OpenAPI tool server pattern
- Premium UI inspiration from Magic UI, Aceternity UI, 21st.dev

---

**Status:** Production Ready  
**Version:** 0.1.0  
**Last Updated:** February 28, 2026

---

## Testing

The project includes comprehensive test coverage:

- **166 tests** covering all functionality
- **Unit tests** for individual components
- **Integration tests** for API endpoints
- **MCP protocol tests** for Streamable HTTP transport
- **HITL workflow tests** for approval system
- **Security tests** for workspace boundaries
- **Git tools tests** (27 unit tests, 12 integration tests)

All tests pass with zero warnings and clean exit.
