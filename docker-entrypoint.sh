#!/bin/bash
set -e

# Create workspace directory if it doesn't exist
if [ ! -d "$WORKSPACE_BASE_DIR" ]; then
    echo "Creating workspace directory: $WORKSPACE_BASE_DIR"
    mkdir -p "$WORKSPACE_BASE_DIR"
fi

# Execute the main command
exec "$@"
