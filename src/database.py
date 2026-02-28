"""Database initialization and management."""

import aiosqlite
from pathlib import Path
from typing import Optional

from src.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """Database manager for SQLite."""
    
    def __init__(self, db_path: str = "/data/hostbridge.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """Connect to database and initialize schema."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better concurrency
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")
        
        await self._init_schema()
        logger.info("database_connected", path=self.db_path)
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            logger.info("database_closed")
    
    async def _init_schema(self):
        """Initialize database schema."""
        # Audit log table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tool_name TEXT NOT NULL,
                tool_category TEXT NOT NULL,
                protocol TEXT NOT NULL,
                request_params TEXT NOT NULL,
                response_body TEXT,
                status TEXT NOT NULL,
                duration_ms INTEGER,
                error_message TEXT,
                hitl_request_id TEXT,
                container_logs TEXT,
                workspace_dir TEXT,
                client_info TEXT
            )
        """)
        
        # Index for common queries
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
            ON audit_log(timestamp DESC)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_tool 
            ON audit_log(tool_name, tool_category)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_status 
            ON audit_log(status)
        """)
        
        await self._connection.commit()
        logger.info("database_schema_initialized")
    
    @property
    def connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection
