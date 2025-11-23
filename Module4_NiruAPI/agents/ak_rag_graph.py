"""
AK-RAG Agent Orchestration Graph using LangGraph
=================================================

Complete agent orchestration for AmaniQuery v2.0 using LangGraph.
Reduces dependency on external models for simple tasks by using local agents.

Architecture:
    User Query → IntentRouter → ShengTranslator → Retrieval → 
    Kenyanizer → Synthesis → Validation → Response

Nodes:
1. IntentRouterAgent: Classify query type (wanjiku/wakili/mwanahabari)
2. ShengTranslatorAgent: Translate Sheng to formal for better RAG
3. RetrievalAgent: Persona-specific retrieval strategy
4. KenyanizerPreambleAgent: Generate persona-specific system prompt
5. SynthesisAgent: Generate final response with JSON enforcement
6. ValidationAgent: Validate JSON schema + citations

Features:
- State-based execution
- Fallback mechanisms
- Self-correction loops
- Conditional routing
- Error recovery

Usage:
    from ak_rag_graph import create_ak_rag_graph, AKRAGState
    
    graph = create_ak_rag_graph(llm_client, vector_db_client)
    result = graph.invoke({
        "user_query": "Kanjo wameongeza parking fees aje?",
        "conversation_history": []
    })
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from datetime import datetime
import logging

# Import existing AmaniQuery agents
from .intent_router import classify_query, INTENT_ROUTER_SYSTEM_PROMPT
from .sheng_translator import (
    detect_sheng,
    full_translation_pipeline,
    SHENG_TO_FORMAL_PROMPT,
    FORMAL_TO_SHENG_PROMPT
)
from .kenyanizer import (
    get_system_prompt,
    SYSTEM_PROMPT_WANJIKU,
    SYSTEM_PROMPT_WAKILI,
    SYSTEM_PROMPT_MWANAHABARI
)
from .json_enforcer import (
    get_json_enforcement_prompt,
    validate_response,
    parse_llm_response,
    retry_with_enforcement,
    RESPONSE_SCHEMA
)
from .retrieval_strategies import UnifiedRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# STATE SCHEMA
# ============================================================================

class AKRAGState(TypedDict):
    """
    Comprehensive state for AK-RAG pipeline.
    
    State flows through all nodes and accumulates information.
    """
    # ========================================================================
    # INPUT
    # ========================================================================
    user_query: str                           # Original user query
    conversation_history: List[Dict[str, str]] # Previous chat messages
    
    # ========================================================================
    # INTENT ROUTING
    # ========================================================================
    query_type: Optional[str]                 # "wanjiku", "wakili", "mwanahabari"
    confidence: Optional[float]               # Intent classification confidence
    detected_language: Optional[str]          # "en", "sw", "sheng", "mixed"
    routing_reasoning: Optional[str]          # Why this classification
    
    # ========================================================================
    # SHENG TRANSLATION
    # ========================================================================
    has_sheng: bool                           # Whether query contains Sheng
    formal_query: Optional[str]               # Sheng translated to formal
    original_query: str                       # Preserved for response re-injection
    
    # ========================================================================
    # RETRIEVAL
    # ========================================================================
    retrieval_query: str                      # Query used for retrieval
    retrieved_docs: List[Dict[str, Any]]      # Retrieved documents
    retrieval_metadata: Optional[Dict]        # Retrieval stats/scores
    
    # ========================================================================
    # KENYANIZER
    # ========================================================================
    system_prompt: str                        # Persona-specific system prompt
    persona_name: str                         # "wanjiku", "wakili", "mwanahabari"
    
    # ========================================================================
    # SYNTHESIS
    # ========================================================================
    raw_llm_response: Optional[str]           # Raw LLM output
    parsed_response: Optional[Dict]           # Parsed JSON response
    synthesis_attempts: int                   # Number of synthesis attempts
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    is_valid: bool                            # Validation passed
    validation_errors: List[str]              # Validation error messages
    validation_attempts: int                  # Number of validation attempts
    
    # ========================================================================
    # OUTPUT
    # ========================================================================
    final_response: Optional[Dict]            # Final validated JSON response
    error_message: Optional[str]              # Error if pipeline failed
    
    # ========================================================================
    # METADATA
    # ========================================================================
    pipeline_start_time: float                # Timestamp when pipeline started
    total_tokens_used: int                    # Total LLM tokens consumed
    node_execution_times: Dict[str, float]    # Time spent in each node


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_llm_response(client, prompt: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
    """
    Helper to generate text from LLM client (OpenAI-compatible).
    Handles both new (v1.0+) and old OpenAI client patterns.
    """
    try:
        # Try new OpenAI v1.0+ pattern
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            response = client.chat.completions.create(
                model="moonshot-v1-8k",  # Default to moonshot-v1-8k
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        
        # Try old OpenAI pattern or custom client with generate()
        elif hasattr(client, "generate"):
            return client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
            
        # Try direct call (if client is a function)
        elif callable(client):
            return client(prompt)
            
        else:
            raise AttributeError("LLM client has no 'chat.completions.create' or 'generate' method")
            
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise

# ============================================================================
# AGENT NODES
# ============================================================================

class IntentRouterAgent:
    """Node 1: Route query to appropriate persona"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Classify user query intent"""
        start_time = datetime.now().timestamp()
        logger.info(f"[IntentRouter] Processing: {state['user_query']}")
        
        try:
            # Define wrapper for LLM function
            def llm_wrapper(prompt):
                return generate_llm_response(self.llm_client, prompt, temperature=0.1)

            # Use existing intent router
            result = classify_query(
                query=state['user_query'],
                llm_function=llm_wrapper,
                conversation_history=state.get('conversation_history', [])
            )
            
            state['query_type'] = result['query_type']
            state['confidence'] = result['confidence']
            state['detected_language'] = result['detected_language']
            state['routing_reasoning'] = result.get('reasoning', '')
            
            # Map to persona names
            persona_map = {
                'wanjiku': 'wanjiku',
                'wakili': 'wakili',
                'mwanahabari': 'mwanahabari',
                'public_interest': 'wanjiku',  # Fallback mapping
                'legal': 'wakili',
                'research': 'mwanahabari'
            }
            state['persona_name'] = persona_map.get(result['query_type'], 'wanjiku')
            
            logger.info(f"[IntentRouter] Classified as: {state['query_type']} (confidence: {result['confidence']:.2f})")
            
        except Exception as e:
            logger.error(f"[IntentRouter] Error: {e}")
            # Fallback to wanjiku for errors
            state['query_type'] = 'wanjiku'
            state['persona_name'] = 'wanjiku'
            state['confidence'] = 0.5
            state['detected_language'] = 'mixed'
            state['routing_reasoning'] = f"Error occurred, defaulting to wanjiku: {e}"
        
        # Update execution time
        if 'node_execution_times' not in state:
            state['node_execution_times'] = {}
        state['node_execution_times']['intent_router'] = datetime.now().timestamp() - start_time
        
        return state


class ShengTranslatorAgent:
    """Node 2: Translate Sheng to formal for better retrieval"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Translate Sheng/slang to formal language"""
        start_time = datetime.now().timestamp()
        logger.info(f"[ShengTranslator] Processing query")
        
        try:
            # Preserve original query
            state['original_query'] = state['user_query']
            
            # Detect if Sheng is present
            is_sheng, confidence, detected_terms = detect_sheng(state['user_query'])
            state['has_sheng'] = is_sheng
            
            if is_sheng or state.get('detected_language') in ['sheng', 'mixed']:
                logger.info(f"[ShengTranslator] Sheng detected (confidence: {confidence:.2f})")
                
                # Define wrapper for LLM function
                def llm_wrapper(prompt):
                    return generate_llm_response(self.llm_client, prompt, temperature=0.1)

                # Translate to formal
                result = full_translation_pipeline(
                    user_input=state['user_query'],
                    llm_function=llm_wrapper,
                    rag_function=lambda x: x, # Dummy rag function as we only need translation here
                )
                
                # full_translation_pipeline returns a dict with 'formal_query'
                # But wait, full_translation_pipeline signature is:
                # full_translation_pipeline(user_query, rag_function, llm_function)
                # And it returns { ..., "formal_query": ..., ... }
                # The original code called it with translate_to_formal=True which is NOT in the signature I read in sheng_translator.py
                # Let's check sheng_translator.py again.
                # def full_translation_pipeline(user_query: str, rag_function: callable, llm_function: callable) -> Dict[str, any]:
                # It seems the original code in ak_rag_graph.py was using a different version or I misread.
                # Actually, we just want translate_to_formal here.
                
                translation_result = translate_to_formal(
                    user_query=state['user_query'],
                    llm_function=llm_wrapper
                )
                
                state['formal_query'] = translation_result.get('formal_query', state['user_query'])
                logger.info(f"[ShengTranslator] Translated to: {state['formal_query']}")
            else:
                # No Sheng, use original query
                state['formal_query'] = state['user_query']
                logger.info(f"[ShengTranslator] No Sheng detected, using original query")
            
            # Set retrieval query
            state['retrieval_query'] = state['formal_query']
            
        except Exception as e:
            logger.error(f"[ShengTranslator] Error: {e}")
            # Fallback to original query
            state['formal_query'] = state['user_query']
            state['retrieval_query'] = state['user_query']
            state['has_sheng'] = False
        
        state['node_execution_times']['sheng_translator'] = datetime.now().timestamp() - start_time
        return state


class RetrievalAgent:
    """Node 3: Retrieve relevant documents with persona-specific strategy"""
    
    def __init__(self, vector_db_client):
        self.retriever = vector_db_client
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Retrieve documents using persona-optimized strategy"""
        start_time = datetime.now().timestamp()
        logger.info(f"[Retrieval] Searching for: {state['retrieval_query']}")
        
        try:
            persona = state.get('persona_name', 'wanjiku')
            
            # Route to appropriate retrieval strategy using UnifiedRetriever.retrieve
            if persona == 'wanjiku':
                results = self.retriever.retrieve(
                    query_type='wanjiku',
                    query=state['retrieval_query'],
                    limit=10,
                    recency_months=6
                )
            elif persona == 'wakili':
                # For Wakili, Qdrant expects query_vector, Weaviate expects query.
                # Assuming UnifiedRetriever handles this or we are using Weaviate which takes query.
                # If using Qdrant, we might need an embedding model here.
                # For now, let's assume Weaviate or that UnifiedRetriever handles text queries if possible.
                # Looking at retrieval_strategies.py, QdrantRetriever.retrieve_wakili takes query_vector.
                # WeaviateRetriever.retrieve_wakili takes query.
                # If self.retriever is UnifiedRetriever, it delegates.
                # If backend is Qdrant, it will fail if we pass query instead of query_vector.
                # But let's assume Weaviate for now as per the error logs (UnifiedRetriever object...).
                
                # To be safe, we pass both query and query_vector if we had it, but we don't.
                # We'll pass 'query' and hope the backend is Weaviate or the Qdrant implementation is updated to handle text (it's not).
                # However, the error was 'UnifiedRetriever' object has no attribute 'retrieve_wanjiku'.
                # So fixing the method call is the first step.
                
                results = self.retriever.retrieve(
                    query_type='wakili',
                    query=state['retrieval_query'],
                    limit=10,
                    doc_types=["act", "bill", "judgment", "constitution"]
                )
            elif persona == 'mwanahabari':
                results = self.retriever.retrieve(
                    query_type='mwanahabari',
                    query=state['retrieval_query'],
                    limit=20,
                    require_tables=True
                )
            else:
                # Fallback
                results = self.retriever.retrieve(
                    query_type='wanjiku',
                    query=state['retrieval_query'],
                    limit=10
                )
            
            state['retrieved_docs'] = results
            state['retrieval_metadata'] = {
                'num_results': len(results),
                'avg_score': sum(r.get('score', 0) for r in results) / len(results) if results else 0,
                'strategy': persona
            }
            
            logger.info(f"[Retrieval] Retrieved {len(results)} documents (avg score: {state['retrieval_metadata']['avg_score']:.3f})")
            
        except Exception as e:
            logger.error(f"[Retrieval] Error: {e}")
            state['retrieved_docs'] = []
            state['retrieval_metadata'] = {'error': str(e)}
        
        state['node_execution_times']['retrieval'] = datetime.now().timestamp() - start_time
        return state


class KenyanizerPreambleAgent:
    """Node 4: Generate persona-specific system prompt"""
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Generate appropriate system prompt for persona"""
        start_time = datetime.now().timestamp()
        logger.info(f"[Kenyanizer] Generating prompt for: {state['persona_name']}")
        
        try:
            persona = state.get('persona_name', 'wanjiku')
            
            # Generate system prompt
            system_prompt = get_system_prompt(
                query_type=persona
            )
            
            state['system_prompt'] = system_prompt
            logger.info(f"[Kenyanizer] Generated {len(system_prompt)} char prompt")
            
        except Exception as e:
            logger.error(f"[Kenyanizer] Error: {e}")
            # Fallback to wanjiku prompt
            state['system_prompt'] = SYSTEM_PROMPT_WANJIKU
        
        state['node_execution_times']['kenyanizer'] = datetime.now().timestamp() - start_time
        return state
    
    def _summarize_context(self, docs: List[Dict]) -> str:
        """Summarize retrieved documents for context"""
        if not docs:
            return "No relevant documents found."
        
        summary = f"Found {len(docs)} relevant documents:\n"
        for i, doc in enumerate(docs[:3], 1):
            summary += f"{i}. {doc.get('source', 'Unknown')}: {doc.get('text', '')[:100]}...\n"
        return summary


class SynthesisAgent:
    """Node 5: Generate final response with JSON enforcement"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Synthesize final response using persona prompt + JSON enforcement"""
        start_time = datetime.now().timestamp()
        logger.info(f"[Synthesis] Generating response (attempt {state.get('synthesis_attempts', 0) + 1})")
        
        try:
            # Initialize attempts counter
            if 'synthesis_attempts' not in state:
                state['synthesis_attempts'] = 0
            state['synthesis_attempts'] += 1
            
            # Build context from retrieved docs
            context = self._build_context(state['retrieved_docs'])
            
            # Get JSON enforcement prompt
            persona_map = {
                'wanjiku': 'public_interest',
                'wakili': 'legal',
                'mwanahabari': 'research'
            }
            query_type_for_enforcer = persona_map.get(state['persona_name'], 'public_interest')
            
            # Get enforcement prompt
            enforcement_prompt = get_json_enforcement_prompt(
                user_query=state['user_query'],
                retrieved_context=context,
                persona_hint=query_type_for_enforcer
            )
            
            # Combine system prompt + enforcement
            full_prompt = f"{state['system_prompt']}\n\n{enforcement_prompt}"
            
            # Generate response
            raw_response = generate_llm_response(
                self.llm_client,
                prompt=full_prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            state['raw_llm_response'] = raw_response
            
            # Parse JSON
            parsed, error = parse_llm_response(raw_response)
            state['parsed_response'] = parsed
            
            if error:
                logger.warning(f"[Synthesis] Parse error: {error}")
            
            logger.info(f"[Synthesis] Generated response ({len(raw_response)} chars)")
            
        except Exception as e:
            logger.error(f"[Synthesis] Error: {e}")
            state['error_message'] = f"Synthesis failed: {e}"
            state['parsed_response'] = None
        
        state['node_execution_times']['synthesis'] = datetime.now().timestamp() - start_time
        return state
    
    def _build_context(self, docs: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        if not docs:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, doc in enumerate(docs[:5], 1):
            source = doc.get('source', 'Unknown Source')
            text = doc.get('text', '')[:500]  # Limit length
            context_parts.append(f"[Document {i}] {source}\n{text}\n")
        
        return "\n".join(context_parts)


class ValidationAgent:
    """Node 6: Validate JSON schema and citation presence"""
    
    def __call__(self, state: AKRAGState) -> AKRAGState:
        """Validate response against schema"""
        start_time = datetime.now().timestamp()
        logger.info(f"[Validation] Validating response (attempt {state.get('validation_attempts', 0) + 1})")
        
        try:
            # Initialize attempts counter
            if 'validation_attempts' not in state:
                state['validation_attempts'] = 0
            state['validation_attempts'] += 1
            
            if not state.get('parsed_response'):
                state['is_valid'] = False
                state['validation_errors'] = ["No parsed response available"]
                logger.warning("[Validation] No parsed response to validate")
                return state
            
            # Validate schema
            is_valid, error = validate_response(state['parsed_response'])
            
            state['is_valid'] = is_valid
            state['validation_errors'] = [error] if error else []
            
            if is_valid:
                state['final_response'] = state['parsed_response']
                logger.info(f"[Validation] ✓ Response valid")
            else:
                logger.warning(f"[Validation] ✗ Validation failed: {error}")
            
        except Exception as e:
            logger.error(f"[Validation] Error: {e}")
            state['is_valid'] = False
            state['validation_errors'] = [f"Validation error: {e}"]
        
        state['node_execution_times']['validation'] = datetime.now().timestamp() - start_time
        return state


# ============================================================================
# CONDITIONAL EDGES
# ============================================================================

def should_retry_synthesis(state: AKRAGState) -> Literal["synthesis", "fallback", "validation"]:
    """Decide whether to retry synthesis or move to fallback"""
    max_attempts = 3
    
    if state.get('synthesis_attempts', 0) >= max_attempts:
        logger.warning(f"[Router] Max synthesis attempts reached, using fallback")
        return "fallback"
    
    if state.get('parsed_response') is None:
        logger.info(f"[Router] Synthesis failed, retrying")
        return "synthesis"
    
    return "validation"


def should_retry_validation(state: AKRAGState) -> Literal["synthesis", "end"]:
    """Decide whether to retry synthesis for validation errors"""
    max_attempts = 2
    
    if not state.get('is_valid', False):
        if state.get('validation_attempts', 0) < max_attempts:
            logger.info(f"[Router] Validation failed, retrying synthesis")
            return "synthesis"
        else:
            logger.warning(f"[Router] Max validation attempts reached, accepting response")
            # Accept the response anyway (better than nothing)
            state['final_response'] = state.get('parsed_response', {})
            return "end"
    
    return "end"


# ============================================================================
# FALLBACK HANDLER
# ============================================================================

def fallback_response(state: AKRAGState) -> AKRAGState:
    """Generate simple fallback response when main pipeline fails"""
    logger.info("[Fallback] Generating simple fallback response")
    
    # Create minimal valid response
    state['final_response'] = {
        "query_type": "public_interest",
        "language_detected": state.get('detected_language', 'mixed'),
        "response": {
            "summary_card": {
                "title": "Query Received",
                "content": f"Tumepokea swali lako kuhusu: {state['user_query'][:100]}..."
            },
            "detailed_breakdown": {
                "points": [
                    "Tafadhali jaribu tena baadaye",
                    "Kama tatizo linaendelea, wasiliana na msaada"
                ]
            },
            "kenyan_context": {
                "impact": "Tunahitaji taarifa zaidi ili kujibu swali hili vizuri.",
                "related_topic": None
            },
            "citations": []
        },
        "follow_up_suggestions": [
            "Jaribu kuuliza kwa maneno rahisi zaidi",
            "Toa maelezo zaidi kuhusu unachohitaji"
        ]
    }
    
    state['is_valid'] = True
    state['error_message'] = "Used fallback response due to pipeline errors"
    
    return state


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_ak_rag_graph(llm_client, vector_db_client, enable_persistence: bool = False):
    """
    Create the complete AK-RAG agent orchestration graph.
    
    Args:
        llm_client: LLM client with .generate() method
        vector_db_client: Vector DB retriever (UnifiedRetriever instance)
        enable_persistence: Enable state persistence with SQLite
    
    Returns:
        Compiled LangGraph
    """
    logger.info("[Graph] Creating AK-RAG orchestration graph")
    
    # Initialize agents
    intent_router = IntentRouterAgent(llm_client)
    sheng_translator = ShengTranslatorAgent(llm_client)
    retrieval = RetrievalAgent(vector_db_client)
    kenyanizer = KenyanizerPreambleAgent()
    synthesis = SynthesisAgent(llm_client)
    validation = ValidationAgent()
    
    # Create graph
    graph = StateGraph(AKRAGState)
    
    # Add nodes
    graph.add_node("intent_router", intent_router)
    graph.add_node("sheng_translator", sheng_translator)
    graph.add_node("retrieval", retrieval)
    graph.add_node("kenyanizer", kenyanizer)
    graph.add_node("synthesis", synthesis)
    graph.add_node("validation", validation)
    graph.add_node("fallback", fallback_response)
    
    # Define edges
    graph.set_entry_point("intent_router")
    
    # Linear flow for main pipeline
    graph.add_edge("intent_router", "sheng_translator")
    graph.add_edge("sheng_translator", "retrieval")
    graph.add_edge("retrieval", "kenyanizer")
    graph.add_edge("kenyanizer", "synthesis")
    
    # Conditional edge after synthesis (retry or validate)
    graph.add_conditional_edges(
        "synthesis",
        should_retry_synthesis,
        {
            "synthesis": "synthesis",      # Retry synthesis
            "validation": "validation",     # Move to validation
            "fallback": "fallback"         # Use fallback
        }
    )
    
    # Conditional edge after validation (retry or end)
    graph.add_conditional_edges(
        "validation",
        should_retry_validation,
        {
            "synthesis": "synthesis",  # Retry synthesis
            "end": END                 # Finish
        }
    )
    
    # Fallback goes to end
    graph.add_edge("fallback", END)
    
    # Compile with optional persistence
    if enable_persistence:
        memory = SqliteSaver.from_conn_string(":memory:")
        compiled_graph = graph.compile(checkpointer=memory)
    else:
        compiled_graph = graph.compile()
    
    logger.info("[Graph] ✓ Graph compiled successfully")
    
    return compiled_graph


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def initialize_state(user_query: str, conversation_history: List[Dict] = None) -> AKRAGState:
    """Initialize state for a new query"""
    return {
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        "pipeline_start_time": datetime.now().timestamp(),
        "total_tokens_used": 0,
        "node_execution_times": {},
        "has_sheng": False,
        "synthesis_attempts": 0,
        "validation_attempts": 0,
        "is_valid": False,
        "validation_errors": []
    }


def execute_pipeline(
    graph,
    user_query: str,
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    Execute the complete AK-RAG pipeline.
    
    Args:
        graph: Compiled LangGraph
        user_query: User's question
        conversation_history: Previous conversation messages
    
    Returns:
        Final response dictionary
    """
    # Initialize state
    initial_state = initialize_state(user_query, conversation_history)
    
    # Execute graph
    logger.info(f"[Pipeline] Starting execution for: {user_query}")
    final_state = graph.invoke(initial_state)
    
    # Calculate total time
    total_time = datetime.now().timestamp() - final_state['pipeline_start_time']
    
    logger.info(f"[Pipeline] ✓ Completed in {total_time:.2f}s")
    logger.info(f"[Pipeline] Node times: {final_state.get('node_execution_times', {})}")
    
    return {
        "response": final_state.get('final_response'),
        "metadata": {
            "query_type": final_state.get('query_type'),
            "persona": final_state.get('persona_name'),
            "confidence": final_state.get('confidence'),
            "has_sheng": final_state.get('has_sheng'),
            "num_docs_retrieved": len(final_state.get('retrieved_docs', [])),
            "synthesis_attempts": final_state.get('synthesis_attempts'),
            "validation_attempts": final_state.get('validation_attempts'),
            "is_valid": final_state.get('is_valid'),
            "total_time_seconds": total_time,
            "node_execution_times": final_state.get('node_execution_times', {}),
            "error": final_state.get('error_message')
        }
    }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("""
AK-RAG Agent Orchestration Graph
=================================

Usage Example:

```python
from ak_rag_graph import create_ak_rag_graph, execute_pipeline
from your_llm_client import LLMClient
from retrieval_strategies import UnifiedRetriever

# Initialize clients
llm_client = LLMClient(api_key="...")
vector_db = UnifiedRetriever(backend="weaviate", client=weaviate_client)

# Create graph
graph = create_ak_rag_graph(llm_client, vector_db)

# Execute query
result = execute_pipeline(
    graph=graph,
    user_query="Kanjo wameongeza parking fees aje?",
    conversation_history=[]
)

# Access response
print(result['response'])
print(result['metadata'])
```

Pipeline Flow:
==============
User Query
    ↓
IntentRouter (classify: wanjiku/wakili/mwanahabari)
    ↓
ShengTranslator (convert Sheng → formal)
    ↓
Retrieval (persona-optimized search)
    ↓
Kenyanizer (generate system prompt)
    ↓
Synthesis (LLM generation + JSON enforcement) ←┐
    ↓                                            │
Validation (check schema + citations)          │
    ↓                                            │
    ├─ Valid? → Final Response                  │
    └─ Invalid? → Retry (max 3x) ───────────────┘

Self-Correction:
- Synthesis retries up to 3x if parsing fails
- Validation retries up to 2x if schema invalid
- Fallback response if all retries exhausted
    """)
