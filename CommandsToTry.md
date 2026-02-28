# HostBridge - Commands to Try

This document provides sample requests you can give to an LLM that has access to the HostBridge tool server. These commands demonstrate the capabilities of each tool currently available.

## Protocol Support

HostBridge supports two protocols:
- **OpenAPI (REST)**: Traditional HTTP REST API
- **MCP (Model Context Protocol)**: Modern protocol for AI tool integration using Streamable HTTP

Both protocols expose the same tools from a single source of truth - no code duplication.

## Getting Started

Before trying file operations, it's helpful to understand the workspace configuration:

### Workspace Information

**"What workspace am I working in?"**
- Gets the default workspace directory, available paths, disk usage, and tool categories

**"Show me the workspace configuration"**
- Returns workspace boundaries and available tool categories

## Filesystem Tools

### Reading Files

**"Read the contents of README.md"**
- Reads the entire file from the workspace

**"Show me the first 10 lines of example.txt"**
- Reads a file with a line limit

**"Read lines 5 through 15 of test.txt"**
- Reads a specific range of lines from a file

**"What's in the file at workspace/nested/deep/file.txt?"**
- Reads a file from a nested directory path

**"Show me the contents of test.conf"**
- Reads a configuration file

### Writing Files

**"Create a new file called hello.txt with the content 'Hello, World!'"**
- Creates a new file with specified content

**"Overwrite example.txt with 'New content here'"**
- Replaces the entire contents of an existing file

**"Append 'Additional line' to the end of test.txt"**
- Adds content to the end of an existing file

**"Create a file at workspace/new_folder/document.txt with content 'Test' and create any missing directories"**
- Creates a file and automatically creates parent directories if they don't exist

**"Write a configuration file at config/app.yaml with the following YAML content: [your YAML here]"**
- Creates a configuration file (may require HITL approval depending on policy)

## Understanding Tool Behavior

### Security and Boundaries

**"Try to read /etc/passwd"**
- This will fail with a security error - paths must be within the workspace boundary

**"Read a file at ../../../etc/passwd"**
- Path traversal attempts are blocked by the workspace security model

### Error Handling

**"Read a file called nonexistent.txt"**
- Demonstrates file not found error with helpful suggestion to use workspace info

**"Write to example.txt with mode 'create'"**
- If the file exists, this will fail and suggest using 'overwrite' or 'append' mode

### HITL (Human-in-the-Loop) Scenarios

Depending on your policy configuration, certain operations may require human approval:

**"Overwrite the file test.conf with new configuration"**
- Writing to .conf files typically requires approval

**"Create a new .env file with environment variables"**
- Writing to .env files typically requires approval

**"Write to an existing file with mode 'overwrite'"**
- Overwriting existing files may require approval depending on policy

## Advanced Usage Patterns

### Working with Encodings

**"Read the file data.txt using UTF-8 encoding"**
- Explicitly specify file encoding (UTF-8 is the default)

**"Read the file legacy.txt using latin-1 encoding"**
- Read files with non-UTF-8 encodings

### Large File Handling

**"Read the first 100 lines of large_log.txt"**
- Limit the number of lines returned for large files

**"Show me lines 1000 to 1100 of big_file.txt"**
- Read a specific section from a large file

### Multi-Step Workflows

**"First, show me what's in the workspace, then read README.md, and create a summary file called SUMMARY.txt"**
- Combines workspace info, file reading, and file writing

**"Read test.txt, then create a backup called test.txt.backup with the same content"**
- Demonstrates reading and writing in sequence

## Testing Tool Server Features

### Policy Enforcement

**"Write to a file called .secret"**
- Tests dotfile blocking policy (if configured)

**"Try to write binary content to a file"**
- Tests binary file blocking (if configured)

### Workspace Override (Advanced)

**"Read a file from a different workspace directory"**
- Tests workspace_dir parameter override (may require HITL approval)

## Tips for LLM Interaction

When working with an LLM that has access to these tools:

1. **Be specific about paths** - Use relative paths from the workspace root or full paths within the workspace
2. **Specify your intent clearly** - "Create a new file" vs "Overwrite existing file" vs "Append to file"
3. **Check before destructive operations** - Ask the LLM to read a file before overwriting it
4. **Use natural language** - The LLM will translate your request into the appropriate tool calls
5. **Combine operations** - You can ask for multi-step workflows in a single request

## Current Tool Inventory

As of this version, HostBridge supports:

- **Health Check** (via MCP: `health_check_health_get`)
  - Check server health and version

- **Filesystem Tools** (category: `fs`)
  - `fs_read` - Read file contents with optional line ranges and encoding
  - `fs_write` - Write, overwrite, or append to files with security controls

- **Workspace Tools** (category: `workspace`)
  - `workspace_info` - Get workspace configuration and boundaries

### MCP-Specific Tool Names

When using MCP clients (Claude Desktop, Cursor, etc.), tools are identified by their operation IDs:
- `health_check_health_get` - Health check
- `fs_read` - Read files
- `fs_write` - Write files
- `workspace_info` - Workspace information

### OpenAPI Endpoints

When using REST API directly:
- `POST /health` - Health check
- `POST /api/tools/fs/read` - Read files
- `POST /api/tools/fs/write` - Write files
- `POST /api/tools/workspace/info` - Workspace information

## Future Tools (Coming Soon)

The following tools are planned for future releases:

- **Git Tools** - Status, commit, push, pull, branch management
- **Docker Tools** - Container management, image operations
- **Shell Tools** - Execute shell commands with output capture
- **HTTP Tools** - Make HTTP requests with authentication
- **Memory Tools** - Persistent key-value storage across sessions
- **Plan Tools** - Task planning and tracking

This document will be updated as new tools are added to the server.

---

**Note:** The actual behavior of these commands depends on:
- Your workspace configuration and mounted volumes
- Policy rules defined in `config.yaml`
- HITL settings and approval requirements
- The specific LLM client you're using (Open WebUI, Claude Desktop, etc.)
