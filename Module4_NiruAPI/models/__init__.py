"""
Pydantic models for API requests and responses
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="The question or query text", min_length=1)
    top_k: int = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    category: Optional[str] = Field(None, description="Filter by category")
    source: Optional[str] = Field(None, description="Filter by source name")
    include_sources: bool = Field(True, description="Include source citations")
    temperature: float = Field(0.7, description="LLM temperature", ge=0.0, le=2.0)
    max_tokens: int = Field(1500, description="Maximum tokens in response", ge=100, le=4000)


class Source(BaseModel):
    """Source citation model"""
    title: str
    url: str
    source_name: str
    category: str
    author: Optional[str] = None
    publication_date: Optional[str] = None
    relevance_score: Optional[float] = None
    excerpt: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="The generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    query_time: float = Field(..., description="Query processing time in seconds")
    retrieved_chunks: int = Field(..., description="Number of chunks retrieved")
    model_used: str = Field(..., description="LLM model used")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database_chunks: int
    embedding_model: str
    llm_provider: str


class StatsResponse(BaseModel):
    """Statistics response"""
    total_chunks: int
    categories: Dict[str, int]
    sources: List[str]
    database_size_mb: Optional[float] = None
