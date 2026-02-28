# HostBridge - Commands to Try

This document provides sample requests you can give to an LLM that has access to the HostBridge tool server. These commands demonstrate the capabilities of each tool currently available.

## Admin Dashboard

Before trying commands, you can monitor and approve operations through the admin dashboard:

**Access:** http://localhost:8080/admin/  
**Default Password:** `admin`

The dashboard provides a unified widget-based interface:
- **HITL Approval Queue Widget:** See pending requests, approve/reject directly from dashboard
- **System Health Widget:** Monitor uptime, error rates, and system metrics in real-time
- **Recent Activity Widget:** View last 5 tool executions with status badges

**Features:**
- Expandable/collapsible widgets for flexible monitoring
- Real-time updates via WebSocket (no refresh needed)
- Quick actions directly from dashboard
- "View All" buttons to navigate to dedicated pages for detailed analysis
- Fully responsive design for mobile, tablet, and desktop

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

### Listing Directories

**"List all files in the current directory"**
- Shows files and directories in the workspace root

**"Show me all Python files in the project"**
- Lists files matching the *.py pattern

**"List all files recursively up to 3 levels deep"**
- Recursive directory listing with depth control

**"Show me all files including hidden ones"**
- Lists files including those starting with a dot

**"What files are in the src directory?"**
- Lists contents of a specific subdirectory

### Searching Files

**"Find all files with 'test' in the name"**
- Searches for files by filename

**"Search for files containing the word 'TODO'"**
- Searches file contents for specific text

**"Find all configuration files"**
- Searches for files matching patterns like *.conf, *.yaml

**"Search for 'import requests' in Python files"**
- Searches file contents with specific patterns

**"Find files matching the regex pattern 'test_.*\.py'"**
- Uses regex for advanced filename matching

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

## Shell Execution

### Safe Commands

**"Run 'ls -la' to see all files"**
- Lists files with details using shell command

**"Execute 'pwd' to show current directory"**
- Shows the current working directory

**"Run 'echo Hello World'"**
- Simple echo command

**"Execute 'git status' to check repository status"**
- Runs git commands (if git is available)

**"Run 'python --version' to check Python version"**
- Checks installed software versions

**"Execute 'cat README.md' to read the file"**
- Uses shell commands to read files

### Commands with Environment Variables

**"Run a command with custom environment variables"**
- Executes commands with additional env vars

**"Execute 'echo $MY_VAR' with MY_VAR set to 'test'"**
- Demonstrates environment variable usage

### Working Directory Control

**"Run 'ls' in the src directory"**
- Executes command in a specific directory

**"Execute 'pwd' in workspace/nested"**
- Shows working directory control

### Commands Requiring Approval

**"Run 'rm -rf temp' to delete the temp directory"**
- Dangerous commands require HITL approval

**"Execute 'ls | grep test' to filter results"**
- Commands with pipes require approval

**"Run 'curl https://api.example.com > output.txt'"**
- Commands with redirects require approval

## Git Tools

### Repository Status

**"What's the status of the git repository?"**
- Shows current branch, staged/unstaged files, and untracked files

**"Check the git status of the project"**
- Returns branch info, commits ahead/behind, and working tree status

**"Show me what files have changed in the repository"**
- Lists modified, staged, and untracked files

### Commit History

**"Show me the last 10 commits"**
- Displays recent commit history with hashes, authors, and messages

**"View the commit history for the last week"**
- Filters commits by date range

**"Show commits by John Doe"**
- Filters commit history by author

**"What commits modified README.md?"**
- Shows commit history for a specific file

### Viewing Changes

**"Show me the diff of uncommitted changes"**
- Displays unstaged changes in unified diff format

**"What changes are staged for commit?"**
- Shows diff of staged changes

**"Compare current state with the last commit"**
- Shows differences between working tree and HEAD

**"Show me just the statistics of changes"**
- Returns files changed, insertions, and deletions counts

### Commit Details

**"Show me the details of the last commit"**
- Displays full commit information including diff

**"What did commit abc123 change?"**
- Shows specific commit details by hash

**"Show me the full diff for HEAD"**
- Displays complete commit information with changes

### Branch Management

**"List all branches in the repository"**
- Shows local branches with current branch indicator

**"Show me all branches including remote ones"**
- Lists both local and remote branches

**"Create a new branch called feature-x"**
- Creates a new branch from current HEAD

**"Switch to the develop branch"** (requires HITL approval)
- Checks out a different branch

**"Delete the old-feature branch"** (requires HITL approval)
- Removes a branch (with safety checks)

### Remote Operations

**"List all configured remotes"**
- Shows remote repositories with fetch/push URLs

**"Add a remote called upstream with URL https://github.com/user/repo.git"**
- Configures a new remote repository

**"Remove the old-remote remote"**
- Deletes a remote configuration

### Stash Operations

**"Stash my current changes"**
- Saves working directory changes to stash

**"List all stashes"**
- Shows all saved stashes with messages

**"Apply the most recent stash"**
- Restores stashed changes

**"Drop stash 0"**
- Removes a specific stash

### Write Operations (Require HITL Approval)

**"Commit the staged changes with message 'Add new feature'"** (requires approval)
- Creates a new commit with specified message

**"Commit all changes with message 'Update documentation'"** (requires approval)
- Stages all changes and creates a commit

**"Push changes to origin main"** (requires approval)
- Pushes commits to remote repository

**"Pull latest changes from origin"**
- Fetches and merges changes from remote

**"Checkout the feature branch"** (requires approval)
- Switches to a different branch

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

Certain operations require human approval through the admin dashboard. When triggered, these requests appear in real-time in the HITL Approval Queue widget:

**"Overwrite the file test.conf with new configuration"**
- Writing to .conf files requires approval
- Request appears in dashboard widget with yellow glow and countdown timer
- Expand widget to see request details
- Admin can approve or reject directly from dashboard
- Or click "View All" to see full request details on dedicated page

**"Create a new .env file with environment variables"**
- Writing to .env files requires approval
- Dashboard widget shows pending count badge
- Real-time WebSocket notification

**"Write to production.yaml with updated settings"**
- Writing to .yaml files requires approval
- Widget updates immediately with visual alert
- Sound notification plays (if enabled)

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
  - `fs_list` - List directory contents with recursive traversal and filtering
  - `fs_search` - Search files by name or content with regex support

- **Shell Tools** (category: `shell`)
  - `shell_execute` - Execute shell commands with security controls
    - Allowlist of safe commands (ls, cat, echo, git, python, npm, docker, etc.)
    - Dangerous metacharacter detection (;, |, &, >, <, etc.)
    - HITL for non-allowlisted or unsafe commands

- **Git Tools** (category: `git`)
  - `git_status` - Get repository status (branch, staged, unstaged, untracked)
  - `git_log` - View commit history with filtering options
  - `git_diff` - View file differences (unstaged, staged, or against ref)
  - `git_show` - Show commit details with full diff
  - `git_list_branches` - List local and remote branches
  - `git_remote` - Manage remote repositories (list, add, remove)
  - `git_commit` - Create commits (HITL required)
  - `git_push` - Push to remote (HITL required)
  - `git_pull` - Pull from remote
  - `git_checkout` - Switch branches or restore files (HITL required)
  - `git_branch` - Create or delete branches (HITL for delete)
  - `git_stash` - Stash operations (push, pop, list, drop)

- **Workspace Tools** (category: `workspace`)
  - `workspace_info` - Get workspace configuration and boundaries

### MCP-Specific Tool Names

When using MCP clients (Claude Desktop, Cursor, etc.), tools are identified by their operation IDs:
- `health_check_health_get` - Health check
- `fs_read` - Read files
- `fs_write` - Write files
- `fs_list` - List directories
- `fs_search` - Search files
- `shell_execute` - Execute shell commands
- `git_status` - Git repository status
- `git_log` - Git commit history
- `git_diff` - Git file differences
- `git_show` - Git commit details
- `git_list_branches` - Git branch list
- `git_remote` - Git remote management
- `git_commit` - Git commit creation
- `git_push` - Git push to remote
- `git_pull` - Git pull from remote
- `git_checkout` - Git checkout branch
- `git_branch` - Git branch operations
- `git_stash` - Git stash operations
- `workspace_info` - Workspace information

### OpenAPI Endpoints

When using REST API directly:
- `POST /health` - Health check
- `POST /api/tools/fs/read` - Read files
- `POST /api/tools/fs/write` - Write files
- `POST /api/tools/fs/list` - List directories
- `POST /api/tools/fs/search` - Search files
- `POST /api/tools/shell/execute` - Execute shell commands
- `POST /api/tools/git/status` - Git repository status
- `POST /api/tools/git/log` - Git commit history
- `POST /api/tools/git/diff` - Git file differences
- `POST /api/tools/git/show` - Git commit details
- `POST /api/tools/git/list_branches` - Git branch list
- `POST /api/tools/git/remote` - Git remote management
- `POST /api/tools/git/commit` - Git commit creation
- `POST /api/tools/git/push` - Git push to remote
- `POST /api/tools/git/pull` - Git pull from remote
- `POST /api/tools/git/checkout` - Git checkout branch
- `POST /api/tools/git/branch` - Git branch operations
- `POST /api/tools/git/stash` - Git stash operations
- `POST /api/tools/workspace/info` - Workspace information

## Future Tools (Coming Soon)

The following tools are planned for future releases:

- **Docker Tools** - Container management, image operations
- **HTTP Tools** - Make HTTP requests with authentication and SSRF protection
- **Memory Tools** - Knowledge graph storage for persistent information
- **Plan Tools** - DAG-based multi-step task execution

This document will be updated as new tools are added to the server.

---

**Note:** The actual behavior of these commands depends on:
- Your workspace configuration and mounted volumes
- Policy rules defined in `config.yaml`
- HITL settings and approval requirements
- The specific LLM client you're using (Open WebUI, Claude Desktop, etc.)
