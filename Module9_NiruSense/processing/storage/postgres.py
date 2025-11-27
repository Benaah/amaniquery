import asyncpg
import json
from ..config import settings

class PostgresClient:
    def __init__(self):
        self.dsn = settings.POSTGRES_DSN
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.dsn)
            await self._init_db()

    async def _init_db(self):
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
                
                CREATE TABLE IF NOT EXISTS analysis_results (
                    document_id UUID REFERENCES documents(id),
                    agent_id VARCHAR(50),
                    result_json JSONB,
                    model_version VARCHAR(50),
                    execution_time_ms INT,
                    PRIMARY KEY (document_id, agent_id)
                );
            """)

    async def save_document(self, doc: dict):
        async with self.pool.acquire() as conn:
            # Upsert document
            row = await conn.fetchrow("""
                INSERT INTO documents (url, raw_content, source_domain, published_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (url) DO UPDATE SET raw_content = $2
                RETURNING id
            """, doc.get('url', 'unknown'), doc.get('text', ''), doc.get('source', 'unknown'), None) # TODO: Parse date
            return row['id']

    async def save_analysis(self, doc_id, agent_id, result):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO analysis_results (document_id, agent_id, result_json, model_version, execution_time_ms)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (document_id, agent_id) DO UPDATE SET result_json = $3
            """, doc_id, agent_id, json.dumps(result), "v1", 0)

postgres = PostgresClient()
