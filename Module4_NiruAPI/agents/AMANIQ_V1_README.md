# AmaniQ v1.0 - Production-Ready RAG Agent Graph

## Overview

AmaniQ v1 is a stateful, multi-agent orchestration system built on LangGraph, designed specifically for Kenyan legal and media intelligence. It provides contextually accurate, bilingual (English/Swahili) responses with evidential traceability.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AmaniQ Control Plane                      │
│             (LangGraph Stateful Graph)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  Entry Gate  │
                      │ (Classify &  │
                      │  Language)   │
                      └──────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌──────────────┐    ┌─────────────┐
            │    Sheng     │    │   Planner   │
            │  Translator  │───▶│  (Research  │
            └──────────────┘    │   Plan)     │
                                └──────┬──────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │     Tool     │
                                │   Executor   │
                                │  (KB Search  │
                                │   + Others)  │
                                └──────┬───────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │  Reasoning   │
                                │    Engine    │
                                └──────┬───────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │   Persona    │
                                │  Synthesis   │
                                │  (wanjiku/   │
                                │ wakili/      │
                                │mwanahabari)  │
                                └──────┬───────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │   Quality    │
                                │     Gate     │
                                └──────┬───────┘
                                       │
                            ┌──────────┴──────────┐
                            ▼                     ▼
                      ┌──────────┐        ┌──────────┐
                      │ Re-plan  │        │   Exit   │
                      │(if low   │        │   Gate   │
                      │confidence)        └──────────┘
                      └──────────┘
```

## Key Features

### 1. **Stateful Multi-Agent Orchestration**
- **LangGraph StateGraph**: Manages complex agent workflows
- **Conditional Routing**: Dynamic path selection based on query classification
- **Iteration Support**: Up to 3 iterations for low-confidence queries

### 2. **Vector DB-Centric Retrieval**
- **Primary Source**: All retrievals from vector database via KB search
- **No External APIs**: Self-contained knowledge base
- **Namespace-Based Search**: Separate namespaces for law, news, parliament, historical data

### 3. **Persona-Specific Synthesis**
- **Wanjiku** (Simple queries): Conversational, uses Kenyan cultural analogies
- **Wakili** (Legal queries): Formal legal analysis with precise citations
- **Mwanahabari** (News queries): Objective, data-driven reporting

### 4. **Bilingual & Cultural Fluency**
- **Language Detection**: Auto-detects English, Swahili, Sheng
- **Sheng Translation**: Converts informal Swahili to formal for better retrieval
- **47 Kenyan Counties**: Context-aware responses for all counties
- **Cultural Ontology**: Understands Kenyan political/economic landscape

### 5. **Reasoning-Guided Tool Orchestration**
- **Planner**: Creates research plans based on query intent
- **Tool Executor**: Orchestrates KB search and other tools
- **Reasoner**: Chain-of-thought and ReAct pattern reasoning
- **Multi-hop Queries**: Decomposes complex queries into sub-queries

### 6. **Quality Assurance**
- **Confidence Scoring**: Multi-factor confidence assessment
- **Source Diversity**: Ensures multiple sources and types
- **Human-in-the-Loop**: Flags legal risk and low-confidence queries
- **Temporal Consistency**: Validates timeline alignment

## Graph Nodes

### Entry Gate
**Purpose**: Query classification and language detection

**Actions**:
- Detect language (English/Swahili/Sheng)
- Classify intent (news/law/hybrid/general)
- Select persona (wanjiku/wakili/mwanahabari)
- Initialize state tracking

**Outputs**: Intent classification, persona, language flags

---

### Sheng Translator
**Purpose**: Convert informal Swahili to formal language

**Conditional**: Only executes if Sheng or Swahili detected

**Actions**:
- Use translation pipeline
- Enhance query for better retrieval

---

### Planner
**Purpose**: Create structured research plan

**Actions**:
- Determine search namespaces based on intent
- Create tool execution plan (primarily KB search)
- Add analysis steps

**Output**: Research plan with tool calls

---

### Tool Executor
**Purpose**: Execute research plan using available tools

**Primary Tool**: KB Search (vector database)

**Optional Tools**:
- Web Search
- News Search
- Twitter Scraper

**Actions**:
- Execute tool calls from plan
- Process results into Evidence objects
- Create Source attributions

---

### Reasoning Engine
**Purpose**: Multi-hop reasoning and verification

**Actions**:
- Analyze retrieved evidence
- Check temporal consistency
- Verify entity consistency
- Assess coverage (need more info?)
- Apply chain-of-thought reasoning

**Output**: Reasoning path, synthesis prep

---

### Persona Synthesis
**Purpose**: Format response using persona-specific prompts

**Actions**:
- Select appropriate system prompt
- Use RAG pipeline for synthesis
- Apply persona-specific formatting

**Personas**:
- **Wanjiku**: Simple language, cultural analogies
- **Wakili**: Legal terminology, citations
- **Mwanahabari**: Data-driven, objective

---

### Quality Gate
**Purpose**: Confidence scoring and validation

**Checks**:
- Source count and diversity
- Evidence confidence scores
- Persona-specific quality (e.g., legal sources for wakili)
- Legal risk indicators

**Decision**: Iterate (re-plan) or proceed to exit

---

### Exit Gate
**Purpose**: Final response formatting and attribution

**Actions**:
- Format final response
- Add source citations
- Include disclaimers based on confidence
- Add quality notes

**Output**: Final response with metadata

## State Schema

```python
class AmaniqV1State(TypedDict):
    # Input
    user_query: str
    session_context: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    
    # Classification & Language
    intent_classification: Literal["news", "law", "hybrid", "general"]
    persona: Literal["wanjiku", "wakili", "mwanahabari"]
    swahili_language_flag: bool
    translated_query: Optional[str]
    detected_language: str
    
    # Planning & Execution
    research_plan: List[PlanStep]
    current_step: int
    
    # Retrieval & Evidence
    retrieved_evidence: List[Evidence]
    source_attributions: List[Source]
    
    # Reasoning
    reasoning_path: List[Thought]
    sub_queries: List[str]
    synthesis_result: Optional[str]
    
    # Quality Control
    confidence_score: float
    human_review_flag: bool
    quality_issues: List[str]
    
    # Output
    final_response: str
    formatted_response: Dict[str, Any]
    
    # Metadata
    iteration_count: int
    agent_path: List[str]
    error_log: List[str]
    max_iterations: int
```

## Usage

### Basic Usage

```python
from Module4_NiruAPI.agents.amaniq_v1 import create_amaniq_v1_graph, query_amaniq
from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.rag_pipeline import RAGPipeline

# Initialize components
vector_store = VectorStore()
rag_pipeline = RAGPipeline(vector_store=vector_store)

# Create graph
graph = create_amaniq_v1_graph(
    vector_store=vector_store,
    rag_pipeline=rag_pipeline,
    enable_reasoning=True,
    enable_quality_gate=True
)

# Query the agent
result = query_amaniq(
    query="What did the Treasury announce about tax reforms?",
    session_context={"user_county": "Nairobi"},
    graph=graph
)

print(result["answer"])
print(f"Confidence: {result['confidence']:.2f}")
print(f"Persona: {result['persona']}")
```

### Advanced Usage

```python
# Direct graph invocation for more control
initial_state = {
    "user_query": "Sheria mpya ya Finance Bill inaaathiri biashara vipi?",
    "session_context": {"user_county": "Nairobi"},
    "conversation_history": [],
    "max_iterations": 2
}

result = graph.invoke(initial_state)

# Access detailed information
print(f"Agent Path: {' → '.join(result['agent_path'])}")
print(f"Reasoning Steps: {len(result['reasoning_path'])}")
print(f"Evidence Count: {len(result['retrieved_evidence'])}")
print(f"Quality Issues: {result['quality_issues']}")
```

### With Persistence

```python
# Enable checkpointing for conversation state
graph = create_amaniq_v1_graph(
    vector_store=vector_store,
    rag_pipeline=rag_pipeline,
    enable_persistence=True,
    checkpoint_path="./checkpoints/amaniq_v1.db"
)

# Query with thread_id for conversation tracking
from langgraph.checkpoint.sqlite import SqliteSaver

config = {"configurable": {"thread_id": "user_123_session_1"}}
result = graph.invoke(initial_state, config=config)
```

## Configuration

### Graph Creation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vector_store` | VectorStore | None | Vector database instance |
| `rag_pipeline` | RAGPipeline | None | RAG pipeline for synthesis |
| `enable_reasoning` | bool | True | Enable reasoning engine |
| `enable_quality_gate` | bool | True | Enable quality validation |
| `enable_persistence` | bool | False | Enable state checkpointing |
| `checkpoint_path` | str | "./checkpoints/amaniq_v1.db" | Checkpoint database path |
| `config_manager` | Any | None | Configuration manager |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | Required | User query |
| `session_context` | Dict | {} | User context (county, preferences) |
| `conversation_history` | List | [] | Previous conversation |
| `graph` | StateGraph | None | Pre-built graph (creates if None) |
| `max_iterations` | int | 2 | Maximum refinement iterations |

## Response Format

### Frontend-Compatible Format (AmaniQueryResponse)

The agent returns responses matching the frontend `AmaniQueryResponse` component structure:

```typescript
{
  "query_type": "public_interest" | "legal" | "research",  // Maps from persona
  "language_detected": string,                              // en, sw, sheng
  "response": {
    "summary_card": {
      "title": string,        // Main heading (100 chars max)
      "content": string       // Summary paragraph (300 chars max)
    },
    "detailed_breakdown": {
      "points": string[]      // 3-5 key points from evidence
    },
    "kenyan_context": {
      "impact": string,                    // How it affects Kenyans
      "related_topic": string | null       // Related context
    },
    "citations": Array<{
      "source": string,       // Source title
      "url": string,          // Source URL or "N/A"
      "quote": string | null  // Optional quote from source
    }>
  },
  "follow_up_suggestions": string[],  // 3 related questions
  "metadata": {                        // Backend metadata (not shown in UI)
    "confidence": float,
    "persona": string,
    "evidence_count": int,
    "reasoning_steps": int,
    "human_review_required": bool,
    "intent": string,
    "agent_path": string[],
    "quality_issues": string[],
    "timestamp": string,
    "iteration_count": int
  }
}
```

### Persona to Query Type Mapping

- `wanjiku` → `public_interest` (Orange/Green theme, 🇰🇪 icon)
- `wakili` → `legal` (Navy/Gold theme, ⚖️ icon)
- `mwanahabari` → `research` (Slate/Teal theme, 📊 icon)

### Legacy Text Format

For backward compatibility, `final_response` contains markdown-formatted text:

```markdown
# Title

Summary content

## Key Points:
1. Point 1
2. Point 2
3. Point 3

🇰🇪 **Kenyan Context:** Impact statement

📚 **Sources:**
[1] Source 1
[2] Source 2

⚖️ **Legal Disclaimer:** (if applicable)
⚠️ **Note:** (if low confidence)
🔍 **Review Required:** (if flagged)
```

## Personas

### Wanjiku (Ordinary Citizen)

**Use Case**: General queries, simple explanations

**Style**:
- Short sentences
- Simple words (avoids jargon)
- Kenyan cultural analogies
- Mix of Swahili/Sheng terms
- Practical focus ("What does this mean for me?")

**Example Analogies**:
- Parliamentary committees → "Like a WhatsApp group for a specific topic"
- Budget allocation → "Like dividing ugali at the dinner table"
- County vs National → "Like your village chief vs the President"

---

### Wakili (Legal Professional)

**Use Case**: Legal queries, constitutional matters

**Style**:
- Formal legal terminology
- Precise citations
- Statutory provisions verbatim
- Case law precedents
- Legal interpretation and analysis

**Includes**:
- Legal citations with sections/clauses
- Relevant case law
- Statutory provisions
- Risk factors
- Legal disclaimers

---

### Mwanahabari (Journalist/Researcher)

**Use Case**: News queries, data analysis

**Style**:
- Objective, data-driven
- Statistics and key figures
- Trend analysis
- Comparative data
- Timeline of events

**Includes**:
- Key statistics
- Chronological timeline
- Data comparisons
- Methodology notes
- Source dates

## Confidence Thresholds

| Score | Interpretation | Action |
|-------|----------------|--------|
| < 0.6 | Low | Human review required, strong disclaimer |
| 0.6-0.8 | Medium | Verification recommended |
| > 0.8 | High | Proceed with full attribution |

## Human-in-the-Loop Triggers

1. **Low Confidence**: Score < 0.6
2. **Legal Risk**: Land disputes, constitutional questions
3. **Insufficient Sources**: < 2 sources from knowledge base
4. **Novel Precedent**: Case law < 30 days old
5. **Bill of Rights**: Article 10, 19, or 27 cited

## Kenyan Context Features

### Counties (47)
All Kenyan counties recognized for location-specific queries

### Keywords

**Legal**: court, constitution, judgment, bill, act, law, statute, mahakama, katiba, sheria

**News**: treasury, parliament, county, governor, senator, mp, cabinet, habari, taarifa

**Swahili Indicators**: katiba, mahakama, habari, serikali, waziri, gavana, uchaguzi

### Namespaces

- `kenya_law`: Legal documents, constitution, acts, regulations
- `kenya_news`: News articles, media reports  
- `kenya_parliament`: Hansard, parliamentary proceedings, bills
- `historical`: Pre-2010 documents, historical context
- `global_trends`: International context and comparisons

**Note:** Namespaces are implemented using underscore naming (e.g., `kenya_law`) to match the vector_store collection naming convention for faster querying.

## Performance Optimization

1. **Lazy Loading**: Embedding model loaded only when needed
2. **Namespace Filtering**: Search only relevant namespaces
3. **Top-K Limiting**: Configurable result counts
4. **Caching**: RAG pipeline caches common queries
5. **Quantization**: Dynamic quantization for CPU inference

## Error Handling

- **Graceful Degradation**: Falls back to simpler synthesis if RAG fails
- **Error Logging**: All errors captured in `error_log`
- **Tool Failures**: Continues with available tools
- **Translation Errors**: Uses original query if translation fails

## Testing

```bash
# Run examples
python Module4_NiruAPI/agents/amaniq_v1.py

# Test specific persona
python -c "
from Module4_NiruAPI.agents.amaniq_v1 import query_amaniq
result = query_amaniq('What does Article 10 say?')
print(result['persona'])  # Should be 'wakili'
"
```

## Visualization

```python
from Module4_NiruAPI.agents.amaniq_v1 import visualize_graph

# Generate Mermaid diagram
visualize_graph(output_path="./amaniq_v1_graph.mmd")
```

## Limitations

1. **Knowledge Base Dependent**: Quality depends on vector DB content
2. **Iteration Limit**: Max 3 iterations to prevent infinite loops
3. **Synthesis Fallback**: If RAG pipeline unavailable, uses template-based synthesis
4. **Tool Availability**: Optional tools (web, news, twitter) may not be available

## Future Enhancements

1. **Real-time Updates**: Integrate with live news feeds
2. **Citation Verification**: Cross-reference with external fact-checkers
3. **Multi-modal**: Support image/document analysis
4. **Fine-tuned Models**: Kenya-specific LLM fine-tuning
5. **County-specific Embeddings**: Enhanced local context

## Dependencies

```bash
pip install langgraph langchain sentence-transformers chromadb
pip install qdrant-client upstash-vector loguru openai anthropic
```

## License

See main AmaniQuery LICENSE file

## Support

For issues or questions, see main AmaniQuery repository
