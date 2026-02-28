"""Configuration management for HostBridge."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])


class WorkspaceConfig(BaseModel):
    """Workspace configuration."""
    base_dir: str = "/workspace"


class SecretsConfig(BaseModel):
    """Secrets configuration."""
    file: str = "/secrets/secrets.env"


class AuthConfig(BaseModel):
    """Authentication configuration."""
    admin_password: str = "admin"
    session_timeout_hours: int = 24


class HITLConfig(BaseModel):
    """HITL configuration."""
    default_ttl_seconds: int = 300
    notification_sound: bool = True
    auto_reject_on_expiry: bool = True


class AuditConfig(BaseModel):
    """Audit configuration."""
    retention_days: int = 30
    log_level: str = "INFO"


class ToolPolicyConfig(BaseModel):
    """Tool policy configuration."""
    policy: str = "allow"  # "allow", "block", or "hitl"
    workspace_override: str = "allow"  # "allow", "block", or "hitl"
    hitl_patterns: List[str] = Field(default_factory=list)
    block_patterns: List[str] = Field(default_factory=list)
    allow_commands: List[str] = Field(default_factory=list)
    block_commands: List[str] = Field(default_factory=list)


class ToolsConfig(BaseModel):
    """Tools configuration."""
    defaults: ToolPolicyConfig = Field(default_factory=lambda: ToolPolicyConfig(workspace_override="hitl"))
    fs: Dict[str, ToolPolicyConfig] = Field(default_factory=dict)
    workspace: Dict[str, ToolPolicyConfig] = Field(default_factory=dict)


class Config(BaseModel):
    """Main configuration."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    hitl: HITLConfig = Field(default_factory=HITLConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file with environment variable substitution."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Return default config
        return Config()
    
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)
    
    # Substitute environment variables
    config_data = _substitute_env_vars(config_data)
    
    return Config(**config_data)


def _substitute_env_vars(data: Any) -> Any:
    """Recursively substitute environment variables in config data."""
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Handle ${VAR:-default} syntax
        if data.startswith("${") and data.endswith("}"):
            var_expr = data[2:-1]
            if ":-" in var_expr:
                var_name, default = var_expr.split(":-", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_expr, data)
        return data
    return data
