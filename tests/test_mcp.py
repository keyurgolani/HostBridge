"""Tests for MCP endpoint."""

import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

# Set up test environment BEFORE any imports
TEST_WORKSPACE = tempfile.mkdtemp()
TEST_DATA_DIR = tempfile.mkdtemp()


@pytest.fixture
async def client():
    """Create test client."""
    # Set environment variables before importing
    os.environ["WORKSPACE_BASE_DIR"] = TEST_WORKSPACE
    
    # Patch config loading
    import src.config
    original_load = src.config.load_config
    
    def patched_load(config_path="config.yaml"):
        cfg = original_load(config_path)
        cfg.workspace.base_dir = TEST_WORKSPACE
        return cfg
    
    src.config.load_config = patched_load
    
    # Patch the database path to use temp directory
    import src.database
    original_db_init = src.database.Database.__init__
    
    def patched_db_init(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(TEST_DATA_DIR, "hostbridge.db")
        original_db_init(self, db_path)
    
    src.database.Database.__init__ = patched_db_init
    
    # Now import the app and initialize database
    from src.main import app, db
    
    # Connect to database before tests
    await db.connect()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestMCPStreamableHTTP:
    """Test MCP Streamable HTTP endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_mcp_initialize(self, client):
        """Test MCP initialize handshake."""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await client.post(
            "/mcp",
            json=init_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check response structure
        assert "jsonrpc" in result
        assert result["jsonrpc"] == "2.0"
        assert "result" in result
        assert "protocolVersion" in result["result"]
        assert "capabilities" in result["result"]
        assert "serverInfo" in result["result"]
        
        # Check server info
        server_info = result["result"]["serverInfo"]
        assert "name" in server_info
        assert server_info["name"] == "HostBridge"
        
        # Check for session ID in headers
        session_id = response.headers.get("Mcp-Session-Id")
        # Session ID is optional but recommended
        if session_id:
            assert len(session_id) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_tools_list(self, client):
        """Test listing tools via MCP."""
        # First initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        init_response = await client.post(
            "/mcp",
            json=init_request,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        
        session_id = init_response.headers.get("Mcp-Session-Id")
        
        # Now list tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        
        response = await client.post("/mcp", json=list_request, headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        
        # Check response structure
        assert "result" in result
        assert "tools" in result["result"]
        
        tools = result["result"]["tools"]
        assert len(tools) > 0
        
        # Check that our tools are present
        tool_names = [tool["name"] for tool in tools]
        assert "fs_read" in tool_names
        assert "fs_write" in tool_names
        assert "workspace_info" in tool_names
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
    
    @pytest.mark.asyncio
    async def test_mcp_transport_is_streamable_http(self, client):
        """Verify that Streamable HTTP transport is being used (not legacy SSE)."""
        # Streamable HTTP uses POST for all requests
        # Legacy SSE would use GET and return event stream
        
        # Try POST (should work with Streamable HTTP)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        response = await client.post(
            "/mcp",
            json=init_request,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        
        # Verify it's not SSE (which would have text/event-stream)
        assert "text/event-stream" not in response.headers.get("content-type", "")
