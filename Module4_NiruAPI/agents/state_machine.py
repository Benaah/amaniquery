"""
AmaniQ v2 State Machine - LangGraph Workflow

Integrates all v2 components:
- SupervisorDecision routing with Pydantic validation
- Parallel tool execution via ToolExecutor
- Human-in-the-loop clarification cycle
- Responder with citation validation
- Redis caching and optimization
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# Local imports - prompts
from .prompts.supervisor_prompt import (
    SupervisorDecision,
    IntentType,
    ToolName,
    ClarificationRequest,
    build_supervisor_messages,
    parse_supervisor_response,
    SUPERVISOR_SYSTEM_PROMPT
)
from .prompts.responder_prompt import (
    build_responder_messages,
    format_tool_data,
    Citation,
    RESPONDER_SYSTEM_PROMPT
)

# Local imports - nodes
from .nodes.tool_executor import tool_executor_node, ToolExecutor
from .nodes.clarification import (
    clarification_entry_node,
    clarification_resume_node,
    max_clarification_node,
    should_clarify,
    clarification_route,
    after_clarification_route,
    add_clarification_subgraph,
    MAX_CLARIFICATION_ROUNDS
)

# Local imports - optimization
from .optimization import (
    CacheConfig,
    RedisCache,
    AnswerCache,
    VectorSearchCache,
    ConversationSummarizer,
    PreWarmService
)

# Local imports - retrieval
from .retrieval_strategies import AmaniQueryRetriever, Namespace, PERSONA_NAMESPACES

logger = logging.getLogger(__name__)


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """
    Complete state for AmaniQ v2 agent workflow.
    
    Fields:
    - messages: Conversation history with reducer for appending
    - current_query: The user's current question (possibly enriched)
    - original_query: The user's original unmodified query
    - persona: User persona (wanjiku, wakili, mwanahabari)
    - thread_id: Unique conversation thread identifier
    
    Supervisor fields:
    - supervisor_decision: Parsed SupervisorDecision from supervisor
    - supervisor_raw: Raw JSON string from supervisor (for debugging)
    
    Tool fields:
    - tool_plan: List of tools to execute from supervisor
    - tool_results: Results from tool execution
    - retrieval_results: Results from knowledge base retrieval
    
    Clarification fields:
    - clarification_count: Number of clarification rounds (max 3)
    - clarification_history: List of clarification Q&A pairs
    - waiting_for_user: Whether we're paused waiting for user input
    - clarification_question: Current question to ask user
    
    Response fields:
    - final_response: The final formatted response to user
    - citations: Extracted citations from response
    - confidence_score: Response confidence (0-1)
    
    Optimization fields:
    - cache_hit: Whether answer came from cache
    - execution_time_ms: Total execution time
    - tokens_used: Token count for billing
    """
    # Core conversation
    messages: Annotated[List[BaseMessage], add_messages]
    current_query: str
    original_query: str
    persona: str
    thread_id: str
    
    # Supervisor decision
    supervisor_decision: Optional[SupervisorDecision]
    supervisor_raw: Optional[str]
    
    # Tool execution
    tool_plan: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    retrieval_results: List[Dict[str, Any]]
    
    # Clarification tracking
    clarification_count: int
    clarification_history: List[Dict[str, str]]
    waiting_for_user: bool
    clarification_question: Optional[str]
    
    # Response
    final_response: Optional[str]
    citations: List[Citation]
    confidence_score: float
    
    # Optimization metrics
    cache_hit: bool
    execution_time_ms: float
    tokens_used: int


def create_initial_state(
    query: str,
    thread_id: str,
    persona: str = "wanjiku",
    messages: Optional[List[BaseMessage]] = None
) -> AgentState:
    """Create initial state for a new conversation turn."""
    return AgentState(
        messages=messages or [],
        current_query=query,
        original_query=query,
        persona=persona,
        thread_id=thread_id,
        supervisor_decision=None,
        supervisor_raw=None,
        tool_plan=[],
        tool_results={},
        retrieval_results=[],
        clarification_count=0,
        clarification_history=[],
        waiting_for_user=False,
        clarification_question=None,
        final_response=None,
        citations=[],
        confidence_score=0.0,
        cache_hit=False,
        execution_time_ms=0.0,
        tokens_used=0
    )


# =============================================================================
# NODE IMPLEMENTATIONS
# =============================================================================

async def supervisor_node(state: AgentState, config: dict) -> dict:
    """
    Supervisor node - routes query to appropriate handling path.
    
    Uses SupervisorDecision Pydantic model for strict validation.
    Routes to: tools, clarification, or direct response.
    """
    from langchain_openai import ChatOpenAI
    
    start_time = datetime.now()
    
    # Get LLM from config or use default
    llm = config.get("configurable", {}).get("supervisor_llm") or ChatOpenAI(
        model="moonshot-v1-32k",
        temperature=0.1,
        max_tokens=2048
    )
    
    # Build messages for supervisor
    messages = build_supervisor_messages(
        query=state["current_query"],
        persona=state["persona"],
        conversation_history=state["messages"],
        clarification_history=state["clarification_history"]
    )
    
    try:
        # Call supervisor LLM
        response = await llm.ainvoke(messages)
        raw_content = response.content
        
        # Parse and validate response
        decision = parse_supervisor_response(raw_content)
        
        logger.info(f"Supervisor decision: intent={decision.intent}, tools={len(decision.tool_plan)}")
        
        # Convert tool plan to dict format
        tool_plan = [
            {
                "tool": tc.tool.value,
                "arguments": tc.arguments,
                "priority": tc.priority,
                "timeout_seconds": tc.timeout_seconds
            }
            for tc in decision.tool_plan
        ]
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "supervisor_decision": decision,
            "supervisor_raw": raw_content,
            "tool_plan": tool_plan,
            "clarification_question": decision.clarification.clarification_question if decision.clarification else None,
            "execution_time_ms": state.get("execution_time_ms", 0) + elapsed
        }
        
    except Exception as e:
        logger.error(f"Supervisor error: {e}")
        # Create fallback decision - direct response
        fallback = SupervisorDecision(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.5,
            reasoning=f"Fallback due to error: {str(e)}",
            tool_plan=[],
            clarification=None,
            suggested_persona=state["persona"]
        )
        return {
            "supervisor_decision": fallback,
            "supervisor_raw": None,
            "tool_plan": [],
            "execution_time_ms": state.get("execution_time_ms", 0)
        }


async def retrieval_node(state: AgentState, config: dict) -> dict:
    """
    Knowledge base retrieval node.
    
    Uses AmaniQueryRetriever with persona-based namespace selection.
    """
    start_time = datetime.now()
    
    # Get retriever from config or create
    retriever = config.get("configurable", {}).get("retriever") or AmaniQueryRetriever()
    
    try:
        # Retrieve based on persona
        results = await retriever.aretrieve(
            query=state["current_query"],
            persona=state["persona"],
            n_results=10
        )
        
        # Convert to serializable format
        retrieval_results = [
            {
                "content": r.content,
                "metadata": r.metadata,
                "score": r.score,
                "namespace": r.namespace.value if r.namespace else None
            }
            for r in results
        ]
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"Retrieved {len(retrieval_results)} documents for persona={state['persona']}")
        
        return {
            "retrieval_results": retrieval_results,
            "execution_time_ms": state.get("execution_time_ms", 0) + elapsed
        }
        
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return {
            "retrieval_results": [],
            "execution_time_ms": state.get("execution_time_ms", 0)
        }


async def responder_node(state: AgentState, config: dict) -> dict:
    """
    Responder node - generates final response with citations.
    
    Uses RESPONDER_SYSTEM_PROMPT with Kenyan legal context.
    Validates citations and formats response.
    """
    from langchain_openai import ChatOpenAI
    
    start_time = datetime.now()
    
    # Get responder LLM (uses larger context for synthesis)
    llm = config.get("configurable", {}).get("responder_llm") or ChatOpenAI(
        model="moonshot-v1-128k",
        temperature=0.3,
        max_tokens=4096
    )
    
    # Combine tool results and retrieval results
    all_data = {
        "retrieval": state["retrieval_results"],
        "tools": state["tool_results"]
    }
    
    # Build responder messages
    messages = build_responder_messages(
        query=state["current_query"],
        tool_data=all_data,
        persona=state["persona"],
        conversation_history=state["messages"]
    )
    
    try:
        response = await llm.ainvoke(messages)
        final_response = response.content
        
        # Extract citations (basic extraction - could be enhanced)
        citations = extract_citations(final_response, state["retrieval_results"])
        
        # Calculate confidence based on retrieval quality
        confidence = calculate_confidence(
            retrieval_results=state["retrieval_results"],
            tool_results=state["tool_results"],
            response_length=len(final_response)
        )
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        # Add response to messages
        response_message = AIMessage(content=final_response)
        
        return {
            "final_response": final_response,
            "citations": citations,
            "confidence_score": confidence,
            "messages": [response_message],
            "execution_time_ms": state.get("execution_time_ms", 0) + elapsed
        }
        
    except Exception as e:
        logger.error(f"Responder error: {e}")
        error_response = "I apologize, but I encountered an error generating a response. Please try rephrasing your question."
        return {
            "final_response": error_response,
            "citations": [],
            "confidence_score": 0.0,
            "messages": [AIMessage(content=error_response)],
            "execution_time_ms": state.get("execution_time_ms", 0)
        }


async def cache_check_node(state: AgentState, config: dict) -> dict:
    """
    Check cache for existing answer before full processing.
    """
    cache = config.get("configurable", {}).get("answer_cache")
    
    if not cache:
        return {"cache_hit": False}
    
    try:
        cached = await cache.get(
            query=state["current_query"],
            persona=state["persona"]
        )
        
        if cached:
            logger.info(f"Cache hit for query: {state['current_query'][:50]}...")
            return {
                "cache_hit": True,
                "final_response": cached["response"],
                "citations": cached.get("citations", []),
                "confidence_score": cached.get("confidence", 0.8)
            }
    except Exception as e:
        logger.warning(f"Cache check error: {e}")
    
    return {"cache_hit": False}


async def cache_store_node(state: AgentState, config: dict) -> dict:
    """
    Store successful response in cache.
    """
    cache = config.get("configurable", {}).get("answer_cache")
    
    if not cache or not state.get("final_response"):
        return {}
    
    try:
        await cache.set(
            query=state["current_query"],
            persona=state["persona"],
            response=state["final_response"],
            citations=state.get("citations", []),
            confidence=state.get("confidence_score", 0.0)
        )
        logger.debug(f"Cached response for query: {state['current_query'][:50]}...")
    except Exception as e:
        logger.warning(f"Cache store error: {e}")
    
    return {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_citations(response: str, retrieval_results: List[Dict]) -> List[Citation]:
    """
    Extract citations from response text.
    
    Looks for citation markers like [1], [2] etc. and maps to sources.
    """
    import re
    
    citations = []
    
    # Find citation markers in response
    markers = re.findall(r'\[(\d+)\]', response)
    
    for marker in set(markers):
        idx = int(marker) - 1
        if 0 <= idx < len(retrieval_results):
            result = retrieval_results[idx]
            metadata = result.get("metadata", {})
            
            citation = Citation(
                source=metadata.get("source", "Unknown"),
                title=metadata.get("title", metadata.get("filename", "Untitled")),
                url=metadata.get("url"),
                date=metadata.get("date"),
                snippet=result.get("content", "")[:200]
            )
            citations.append(citation)
    
    return citations


def calculate_confidence(
    retrieval_results: List[Dict],
    tool_results: Dict,
    response_length: int
) -> float:
    """
    Calculate response confidence score (0-1).
    
    Based on:
    - Number and quality of retrieval results
    - Successful tool executions
    - Response length (proxy for completeness)
    """
    score = 0.5  # Base score
    
    # Retrieval quality
    if retrieval_results:
        avg_score = sum(r.get("score", 0) for r in retrieval_results) / len(retrieval_results)
        score += min(avg_score * 0.2, 0.2)
        
        # Bonus for multiple results
        if len(retrieval_results) >= 3:
            score += 0.1
    
    # Tool success
    if tool_results:
        successful = sum(1 for v in tool_results.values() if v and not isinstance(v, Exception))
        if successful > 0:
            score += 0.1
    
    # Response completeness
    if response_length > 500:
        score += 0.05
    if response_length > 1000:
        score += 0.05
    
    return min(score, 1.0)


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def route_after_supervisor(state: AgentState) -> str:
    """
    Route after supervisor decision.
    
    Routes:
    - CLARIFY -> clarification_entry
    - LEGAL_RESEARCH, NEWS_SUMMARY -> retrieval (then tools)
    - GENERAL_CHAT, ESCALATE -> respond (direct)
    """
    decision = state.get("supervisor_decision")
    
    if not decision:
        logger.warning("No supervisor decision, routing to respond")
        return "respond"
    
    intent = decision.intent
    
    if intent == IntentType.CLARIFY:
        # Check if we've exceeded max clarifications
        if state.get("clarification_count", 0) >= MAX_CLARIFICATION_ROUNDS:
            logger.info("Max clarifications reached, forcing response")
            return "respond"
        return "clarify"
    
    if intent in (IntentType.LEGAL_RESEARCH, IntentType.NEWS_SUMMARY):
        return "retrieve"
    
    # GENERAL_CHAT, ESCALATE -> direct response
    return "respond"


def route_after_cache(state: AgentState) -> str:
    """Route based on cache hit/miss."""
    if state.get("cache_hit") and state.get("final_response"):
        return "end"
    return "supervisor"


def route_after_retrieval(state: AgentState) -> str:
    """Route after retrieval - to tools if needed, else respond."""
    tool_plan = state.get("tool_plan", [])
    
    if tool_plan:
        return "tools"
    return "respond"


def route_after_tools(state: AgentState) -> str:
    """Route after tool execution - always to responder."""
    return "respond"


def route_after_respond(state: AgentState) -> str:
    """Route after response - to cache store."""
    return "cache_store"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph(
    include_cache: bool = True,
    include_clarification: bool = True
) -> StateGraph:
    """
    Build the AmaniQ v2 state machine graph.
    
    Args:
        include_cache: Whether to include cache nodes
        include_clarification: Whether to include clarification subgraph
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    if include_cache:
        graph.add_node("cache_check", cache_check_node)
        graph.add_node("cache_store", cache_store_node)
    
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("retrieve", retrieval_node)
    graph.add_node("tools", tool_executor_node)
    graph.add_node("respond", responder_node)
    
    # Add clarification subgraph if enabled
    if include_clarification:
        add_clarification_subgraph(graph)
    
    # Set entry point
    if include_cache:
        graph.set_entry_point("cache_check")
        graph.add_conditional_edges(
            "cache_check",
            route_after_cache,
            {
                "supervisor": "supervisor",
                "end": END
            }
        )
    else:
        graph.set_entry_point("supervisor")
    
    # Supervisor routing
    if include_clarification:
        graph.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            {
                "clarify": "clarification_entry",
                "retrieve": "retrieve",
                "respond": "respond"
            }
        )
    else:
        graph.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            {
                "clarify": "respond",  # Skip clarification if disabled
                "retrieve": "retrieve",
                "respond": "respond"
            }
        )
    
    # Retrieval to tools or respond
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "tools": "tools",
            "respond": "respond"
        }
    )
    
    # Tools always to respond
    graph.add_edge("tools", "respond")
    
    # Respond to cache store or end
    if include_cache:
        graph.add_edge("respond", "cache_store")
        graph.add_edge("cache_store", END)
    else:
        graph.add_edge("respond", END)
    
    return graph


def compile_graph(
    checkpointer=None,
    include_cache: bool = True,
    include_clarification: bool = True
) -> Any:
    """
    Compile the graph with optional checkpointer for persistence.
    
    Args:
        checkpointer: LangGraph checkpointer for state persistence
        include_cache: Whether to include cache nodes
        include_clarification: Whether to include clarification subgraph
    
    Returns:
        Compiled graph ready for invocation
    """
    graph = build_graph(
        include_cache=include_cache,
        include_clarification=include_clarification
    )
    
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


# =============================================================================
# EXECUTION HELPERS
# =============================================================================

async def run_agent(
    query: str,
    thread_id: str,
    persona: str = "wanjiku",
    messages: Optional[List[BaseMessage]] = None,
    config: Optional[dict] = None,
    graph: Any = None
) -> AgentState:
    """
    Run the agent for a single query.
    
    Args:
        query: User's question
        thread_id: Conversation thread ID
        persona: User persona (wanjiku, wakili, mwanahabari)
        messages: Previous conversation messages
        config: Runtime configuration (LLMs, cache, etc.)
        graph: Pre-compiled graph (creates new if not provided)
    
    Returns:
        Final AgentState with response
    """
    # Create initial state
    state = create_initial_state(
        query=query,
        thread_id=thread_id,
        persona=persona,
        messages=messages
    )
    
    # Add user message
    state["messages"].append(HumanMessage(content=query))
    
    # Get or create graph
    if graph is None:
        graph = compile_graph()
    
    # Build config
    run_config = {"configurable": config or {}}
    
    # Run graph
    final_state = await graph.ainvoke(state, run_config)
    
    return final_state


async def resume_after_clarification(
    state: AgentState,
    user_response: str,
    config: Optional[dict] = None,
    graph: Any = None
) -> AgentState:
    """
    Resume agent after user provides clarification.
    
    Args:
        state: Current state (waiting_for_user=True)
        user_response: User's clarification response
        config: Runtime configuration
        graph: Pre-compiled graph
    
    Returns:
        Final AgentState with response
    """
    if not state.get("waiting_for_user"):
        raise ValueError("State is not waiting for user input")
    
    # Update state with user response
    state["messages"].append(HumanMessage(content=user_response))
    
    # Get or create graph
    if graph is None:
        graph = compile_graph()
    
    # Build config
    run_config = {"configurable": config or {}}
    
    # Resume from clarification_resume node
    final_state = await graph.ainvoke(state, run_config, start_node="clarification_resume")
    
    return final_state


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_production_config(
    redis_url: Optional[str] = None,
    supervisor_model: str = "moonshot-v1-32k",
    responder_model: str = "moonshot-v1-128k"
) -> dict:
    """
    Create production configuration with all optimizations.
    
    Args:
        redis_url: Redis connection URL for caching
        supervisor_model: Model for supervisor decisions
        responder_model: Model for response generation
    
    Returns:
        Configuration dict for graph execution
    """
    from langchain_openai import ChatOpenAI
    
    config = {
        "supervisor_llm": ChatOpenAI(
            model=supervisor_model,
            temperature=0.1,
            max_tokens=2048
        ),
        "responder_llm": ChatOpenAI(
            model=responder_model,
            temperature=0.3,
            max_tokens=4096
        ),
        "retriever": AmaniQueryRetriever()
    }
    
    # Add cache if Redis available
    if redis_url:
        try:
            cache_config = CacheConfig()
            redis_cache = RedisCache(redis_url, cache_config)
            config["answer_cache"] = AnswerCache(redis_cache, cache_config)
            config["vector_cache"] = VectorSearchCache(redis_cache, cache_config)
            logger.info("Redis caching enabled")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
    
    return config


def create_development_config() -> dict:
    """
    Create development configuration without external dependencies.
    
    Returns:
        Minimal configuration for local development
    """
    from langchain_openai import ChatOpenAI
    
    return {
        "supervisor_llm": ChatOpenAI(
            model="moonshot-v1-8k",  # Smaller model for dev
            temperature=0.1,
            max_tokens=1024
        ),
        "responder_llm": ChatOpenAI(
            model="moonshot-v1-32k",
            temperature=0.3,
            max_tokens=2048
        ),
        "retriever": AmaniQueryRetriever()
    }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # State
    "AgentState",
    "create_initial_state",
    
    # Nodes
    "supervisor_node",
    "retrieval_node",
    "responder_node",
    "cache_check_node",
    "cache_store_node",
    
    # Routing
    "route_after_supervisor",
    "route_after_cache",
    "route_after_retrieval",
    "route_after_tools",
    "route_after_respond",
    
    # Graph
    "build_graph",
    "compile_graph",
    
    # Execution
    "run_agent",
    "resume_after_clarification",
    
    # Config
    "create_production_config",
    "create_development_config"
]
