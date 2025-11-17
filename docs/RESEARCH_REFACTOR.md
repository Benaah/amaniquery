# Refactor Research Mode with Agentic AI Architecture

## Overview

Transform the current simple Gemini-based research module into a sophisticated 7-layer agentic AI system using LangGraph, with swarm intelligence, external data sources, and multi-agent composition.

## Architecture Layers (Following 7-Layer Model)

### 1. Experience Layer

- **Location**: `Module4_NiruAPI/agents/experience/`
- **Files**: `ui_handler.py`, `stream_handler.py`
- **Purpose**: Handle user interactions, input processing, and output delivery
- **Changes**: Update frontend to support agentic research mode with streaming state updates

### 2. Discovery Layer  

- **Location**: `Module4_NiruAPI/agents/discovery/`
- **Files**: `rag_retriever.py`, `hybrid_search.py`, `query_expansion.py`
- **Purpose**: Enhanced RAG with hybrid search (BM25 + embeddings), reranking, context-aware retrieval
- **Integration**: Leverage existing `Module3_NiruDB/vector_store.py` and `Module7_NiruHybrid/`

### 3. Agent Composition Layer

- **Location**: `Module4_NiruAPI/agents/composition/`
- **Files**: `agent_orchestrator.py`, `sub_agent_factory.py`, `router.py`
- **Purpose**: Multi-agent system with specialist agents (Researcher, Citer, Editor, Validator)
- **Framework**: LangGraph for agent coordination

### 4. Reasoning & Planning Layer

- **Location**: `Module4_NiruAPI/agents/reasoning/`
- **Files**: `planner.py`, `reasoner.py`, `reflection.py`
- **Purpose**: LangGraph state machine with plan → decide → act → tools → reflect → finalize
- **Techniques**: Chain-of-Thought, Tree-of-Thoughts, ReAct pattern, self-reflection

### 5. Tool & API Layer

- **Location**: `Module4_NiruAPI/agents/tools/`
- **Files**: 
  - `web_search.py` (DuckDuckGo)
  - `twitter_scraper.py` (twikit)
  - `news_search.py` (serpapi for Google News)
  - `youtube_search.py` (serpapi for YouTube)
  - `url_fetcher.py`
  - `calculator.py`
  - `file_writer.py`
  - `email_drafter.py`
  - `kb_search.py` (Knowledge Base search/add)
- **Purpose**: Autonomous tool use and tool-chaining

### 6. Memory & Feedback Layer

- **Location**: `Module4_NiruAPI/agents/memory/`
- **Files**: `memory_manager.py`, `feedback_handler.py`
- **Purpose**: 
  - Short-term & working memory
  - Long-term memory (PostgreSQL + Vector stores)
  - Episodic & semantic memory
  - Self-critique and feedback loops
- **Integration**: Use existing `Module3_NiruDB/chat_manager.py` and vector stores

### 7. Infrastructure Layer

- **Location**: `Module4_NiruAPI/agents/infrastructure/`
- **Files**: `model_manager.py`, `rate_limiter.py`, `security.py`
- **Purpose**: Model access, compute orchestration, security, rate limiting
- **Integration**: Existing rate limiting and model configs

## Key Components

### LangGraph State Machine

- **File**: `Module4_NiruAPI/agents/state_machine.py`
- **States**: `PLAN`, `DECIDE`, `ACT`, `TOOLS`, `REFLECT`, `FINALIZE`
- **Transitions**: Conditional flows based on agent decisions
- **State Schema**: TypedDict with query, plan, actions, tools_used, reflection, final_answer

### Swarm Intelligence

- **File**: `Module4_NiruAPI/agents/swarm/swarm_orchestrator.py`
- **Approach**: 
  - Parallel LLM queries (OpenAI, Anthropic, Gemini, Moonshot)
  - Response synthesis with redundancy removal
  - Consensus building for complex queries
  - Division of labor for multi-faceted queries
- **Integration**: Use existing multi-model support in `rag_pipeline.py`

### External Data Sources

- **twikit**: Twitter scraping (no API key needed)
  - Install: `pip install twikit`
  - File: `Module4_NiruAPI/agents/tools/twitter_scraper.py`
- **serpapi**: Google News and YouTube search
  - Install: `pip install google-search-results`
  - File: `Module4_NiruAPI/agents/tools/news_search.py`, `youtube_search.py`
  - Note: Requires SERPAPI_API_KEY
- **DuckDuckGo**: Web search (no API key)
  - Install: `pip install duckduckgo-search`
  - File: `Module4_NiruAPI/agents/tools/web_search.py`

### Hybrid Module Enhancements

- **Location**: `Module7_NiruHybrid/agents/`
- **Files**: 
  - `multi_agent_composition.py` - Specialist agents (Citer, Editor, Validator)
  - `structured_outputs.py` - Pydantic validation for deliverables
  - `hybrid_retrieval.py` - BM25 + embeddings, reranking
- **Integration**: Extend existing hybrid encoder and retrieval systems

## Implementation Steps

1. **Setup Dependencies**

   - Add `langgraph`, `twikit`, `google-search-results`, `duckduckgo-search` to requirements.txt
   - Update `Module4_NiruAPI/requirements.txt`

2. **Create Agent Infrastructure**

   - Build 7-layer directory structure
   - Implement base agent classes and interfaces
   - Set up LangGraph state machine skeleton

3. **Implement Tools Layer**

   - Create all tool implementations (web search, Twitter, news, YouTube, etc.)
   - Add tool registry and tool-chaining logic
   - Integrate with LangGraph function calling

4. **Build Reasoning & Planning**

   - Implement LangGraph state machine with all states
   - Add planning, reasoning, and reflection mechanisms
   - Create decision logic for state transitions

5. **Integrate Swarm Intelligence**

   - Build swarm orchestrator for parallel LLM queries
   - Implement response synthesis algorithms
   - Add consensus and division-of-labor logic

6. **Enhance Discovery Layer**

   - Implement hybrid search (BM25 + embeddings)
   - Add reranking and query expansion
   - Integrate with existing vector stores

7. **Refactor Research Module**

   - Replace `Module4_NiruAPI/research_module.py` with agentic version
   - Update API endpoints in `Module4_NiruAPI/api.py`
   - Maintain backward compatibility where possible

8. **Update Hybrid Module**

   - Add multi-agent composition to Module7
   - Implement structured outputs with Pydantic
   - Enhance retrieval with hybrid search

9. **Memory & Feedback Integration**

   - Connect to existing PostgreSQL and vector stores
   - Implement episodic and semantic memory
   - Add feedback loops and self-critique

10. **Testing & Documentation**

    - Unit tests for each layer
    - Integration tests for full agent flow
    - Update API documentation
    - Create usage examples

## File Structure

```
Module4_NiruAPI/
├── agents/
│   ├── __init__.py
│   ├── state_machine.py          # LangGraph state machine
│   ├── experience/
│   ├── discovery/
│   ├── composition/
│   ├── reasoning/
│   ├── tools/
│   ├── memory/
│   ├── infrastructure/
│   └── swarm/
│       └── swarm_orchestrator.py
├── research_module.py            # Refactored to use agents
└── api.py                        # Updated endpoints

Module7_NiruHybrid/
├── agents/
│   ├── multi_agent_composition.py
│   ├── structured_outputs.py
│   └── hybrid_retrieval.py
```

## Dependencies Added

- langgraph>=0.2.0
- twikit>=0.1.0
- google-search-results>=2.4.0
- duckduckgo-search>=6.0.0
- rank-bm25>=0.2.2 (for BM25 search)