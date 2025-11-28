import asyncpg
import json
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime
from ..config import settings

class PostgresClient:
    """PostgreSQL client with connection pooling and retry logic"""
    
    def __init__(self):
        self.dsn = settings.DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(asyncpg.PostgresConnectionError)
    )
    async def connect(self):
        """Connect to PostgreSQL with retry logic"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=settings.DB_POOL_MIN_SIZE,
                max_size=settings.DB_POOL_MAX_SIZE,
                command_timeout=settings.DB_TIMEOUT
            )
            await self._init_db()
            print(f"PostgreSQL connected: {settings.DB_POOL_MIN_SIZE}-{settings.DB_POOL_MAX_SIZE} pool")

    async def _init_db(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    url TEXT UNIQUE NOT NULL,
                    raw_content TEXT,
                    normalized_content TEXT,
                    source_domain VARCHAR(255),
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_domain);
                CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at);
                
                CREATE TABLE IF NOT EXISTS analysis_results (
                    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                    agent_id VARCHAR(50),
                    result_json JSONB,
                    model_version VARCHAR(50),
                    execution_time_ms INT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (document_id, agent_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_analysis_agent ON analysis_results(agent_id);
            """)

    async def save_document(self, doc: Dict[str, Any]) -> str:
        """Save document with proper field handling"""
        async with self.pool.acquire() as conn:
            # Parse published_at if available
            published_at = None
            if doc.get('published_at'):
                try:
                    published_at = datetime.fromisoformat(doc['published_at'])
                except (ValueError, TypeError):
                    pass
            
            row = await conn.fetchrow("""
                INSERT INTO documents (url, raw_content, normalized_content, source_domain, published_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (url) DO UPDATE 
                SET raw_content = EXCLUDED.raw_content,
                    normalized_content = EXCLUDED.normalized_content
                RETURNING id
            """, 
                doc.get('url', 'unknown'), 
                doc.get('raw_content', doc.get('text', '')),
                doc.get('normalized_content', ''),
                doc.get('source', doc.get('source_domain', 'unknown')),
                published_at
            )
            return str(row['id'])

    async def save_analysis(self, doc_id: str, agent_id: str, result: Dict[str, Any]):
        """Save agent analysis results"""
        # Extract execution time from meta if available
        execution_time = result.get('_meta', {}).get('execution_time_ms', 0)
        model_version = result.get('_meta', {}).get('model_version', 'v1')
        
        # Remove meta before storing
        result_clean = {k: v for k, v in result.items() if k != '_meta'}
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO analysis_results (document_id, agent_id, result_json, model_version, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (document_id, agent_id) 
                DO UPDATE SET 
                    result_json = EXCLUDED.result_json,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    created_at = NOW()
            """, doc_id, agent_id, json.dumps(result_clean), model_version, execution_time)

    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return {
                    "status": "healthy" if result == 1 else "degraded",
                    "pool_size": self.pool.get_size(),
                    "pool_free": self.pool.get_idle_size()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self):
        """Close database pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

postgres = PostgresClient()

