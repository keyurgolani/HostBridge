"""Integration tests for git API endpoints."""

import os
import pytest
import tempfile
import shutil
import subprocess
from httpx import AsyncClient

from src.main import app


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
async def git_repo(temp_workspace):
    """Create a test git repository."""
    repo_path = os.path.join(temp_workspace, "test_repo")
    os.makedirs(repo_path)
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    
    # Create initial commit
    test_file = os.path.join(repo_path, "README.md")
    with open(test_file, "w") as f:
        f.write("# Test Repository\n")
    
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    
    return "test_repo"


@pytest.fixture
def setup_workspace(temp_workspace, monkeypatch):
    """Setup workspace environment."""
    monkeypatch.setenv("WORKSPACE_BASE_DIR", temp_workspace)
    # Reload config
    from src import config as config_module
    config_module.config = config_module.load_config()


@pytest.mark.asyncio
async def test_git_status_endpoint(git_repo, setup_workspace):
    """Test git status API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/status",
            json={"repo_path": git_repo},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "branch" in data
    assert "staged" in data
    assert "unstaged" in data
    assert "untracked" in data
    assert "clean" in data


@pytest.mark.asyncio
async def test_git_log_endpoint(git_repo, setup_workspace):
    """Test git log API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/log",
            json={"repo_path": git_repo, "max_count": 10},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "commits" in data
    assert "total_shown" in data
    assert len(data["commits"]) >= 1


@pytest.mark.asyncio
async def test_git_diff_endpoint(git_repo, setup_workspace):
    """Test git diff API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/diff",
            json={"repo_path": git_repo},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "diff" in data
    assert "files_changed" in data
    assert "insertions" in data
    assert "deletions" in data


@pytest.mark.asyncio
async def test_git_list_branches_endpoint(git_repo, setup_workspace):
    """Test git list branches API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/list_branches",
            json={"repo_path": git_repo},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "branches" in data
    assert len(data["branches"]) >= 1


@pytest.mark.asyncio
async def test_git_show_endpoint(git_repo, setup_workspace):
    """Test git show API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/show",
            json={"repo_path": git_repo, "ref": "HEAD"},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "hash" in data
    assert "author" in data
    assert "date" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_git_remote_list_endpoint(git_repo, setup_workspace):
    """Test git remote list API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/remote",
            json={"repo_path": git_repo, "action": "list"},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "remotes" in data
    assert "action" in data


@pytest.mark.asyncio
async def test_git_stash_list_endpoint(git_repo, setup_workspace):
    """Test git stash list API endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/stash",
            json={"repo_path": git_repo, "action": "list"},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "stashes" in data


@pytest.mark.asyncio
async def test_git_status_sub_app_endpoint(git_repo, setup_workspace):
    """Test git status sub-app endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/tools/git/status",
            json={"repo_path": git_repo},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "branch" in data


@pytest.mark.asyncio
async def test_git_log_sub_app_endpoint(git_repo, setup_workspace):
    """Test git log sub-app endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/tools/git/log",
            json={"repo_path": git_repo, "max_count": 5},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "commits" in data


@pytest.mark.asyncio
async def test_git_invalid_repo(setup_workspace):
    """Test git status with invalid repository."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/tools/git/status",
            json={"repo_path": "nonexistent_repo"},
        )
    
    assert response.status_code in [400, 404, 500]


@pytest.mark.asyncio
async def test_git_openapi_spec():
    """Test that git tools appear in OpenAPI spec."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
    
    assert response.status_code == 200
    spec = response.json()
    
    # Check that git endpoints are in the spec
    paths = spec.get("paths", {})
    assert "/api/tools/git/status" in paths
    assert "/api/tools/git/log" in paths
    assert "/api/tools/git/diff" in paths
    assert "/api/tools/git/commit" in paths
    assert "/api/tools/git/push" in paths
    assert "/api/tools/git/pull" in paths
    assert "/api/tools/git/checkout" in paths
    assert "/api/tools/git/branch" in paths
    assert "/api/tools/git/list_branches" in paths
    assert "/api/tools/git/stash" in paths
    assert "/api/tools/git/show" in paths
    assert "/api/tools/git/remote" in paths
