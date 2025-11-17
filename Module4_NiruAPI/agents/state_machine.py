"""
LangGraph State Machine for Agentic Research
Implements: plan → decide → act → tools → reflect → finalize
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import json
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError:
    logger.warning("LangGraph not installed. Install with: pip install langgraph langchain-core")
    StateGraph = None
    END = None

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from Module4_NiruAPI.rag_pipeline import RAGPipeline
except ImportError:
    RAGPipeline = None
from .swarm.swarm_orchestrator import SwarmOrchestrator
from .tools.tool_registry import ToolRegistry
from .memory.memory_manager import AgentMemoryManager
from .reasoning.planner import Planner
from .reasoning.reflection import ReflectionEngine


class AgentState(TypedDict):
    """State schema for the agentic research system"""
    query: str
    plan: Optional[List[Dict[str, Any]]]
    current_step: Optional[int]
    actions_taken: List[Dict[str, Any]]
    tools_used: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    reflection: Optional[str]
    final_answer: Optional[str]
    confidence: Optional[float]
    sources: List[Dict[str, Any]]
    error: Optional[str]
    iteration_count: int
    max_iterations: int


class AgenticResearchSystem:
    """
    Main agentic research system using LangGraph state machine
    """
    
    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        swarm_orchestrator: Optional[SwarmOrchestrator] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[AgentMemoryManager] = None,
        max_iterations: int = 5
    ):
        """
        Initialize the agentic research system
        
        Args:
            rag_pipeline: RAG pipeline instance
            swarm_orchestrator: Swarm orchestrator for multi-LLM queries
            tool_registry: Tool registry for available tools
            memory_manager: Memory manager for agent state
            max_iterations: Maximum iterations before finalizing
        """
        self.rag_pipeline = rag_pipeline
        self.swarm_orchestrator = swarm_orchestrator
        self.tool_registry = tool_registry or ToolRegistry()
        self.memory_manager = memory_manager or AgentMemoryManager()
        self.max_iterations = max_iterations
        
        # Initialize components
        self.planner = Planner(rag_pipeline=rag_pipeline)
        self.reflection_engine = ReflectionEngine()
        
        # Build the state graph
        if StateGraph is not None:
            self.graph = self._build_graph()
        else:
            self.graph = None
            logger.warning("LangGraph not available. Using fallback mode.")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("decide", self._decide_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("reflect", self._reflect_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        # Add edges
        workflow.add_edge("plan", "decide")
        workflow.add_conditional_edges(
            "decide",
            self._should_use_tools,
            {
                "tools": "tools",
                "act": "act",
                "finalize": "finalize"
            }
        )
        workflow.add_edge("tools", "reflect")
        workflow.add_edge("act", "reflect")
        workflow.add_conditional_edges(
            "reflect",
            self._should_continue,
            {
                "continue": "decide",
                "finalize": "finalize"
            }
        )
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _plan_node(self, state: AgentState) -> AgentState:
        """Planning node - creates a research plan"""
        logger.info(f"Planning for query: {state['query']}")
        
        try:
            plan = self.planner.create_plan(state['query'])
            state['plan'] = plan
            state['current_step'] = 0
            state['actions_taken'] = []
            state['tools_used'] = []
            state['tool_results'] = []
            state['iteration_count'] = 0
            state['sources'] = []
            
            logger.info(f"Created plan with {len(plan)} steps")
        except Exception as e:
            logger.error(f"Error in planning: {e}")
            state['error'] = f"Planning failed: {str(e)}"
            state['plan'] = []
        
        return state
    
    def _decide_node(self, state: AgentState) -> AgentState:
        """Decision node - decides what action to take"""
        logger.info("Making decision on next action")
        
        if state.get('error'):
            return state
        
        if not state.get('plan'):
            state['error'] = "No plan available"
            return state
        
        # Check if we've exceeded max iterations
        if state.get('iteration_count', 0) >= self.max_iterations:
            logger.warning("Max iterations reached")
            return state
        
        state['iteration_count'] = state.get('iteration_count', 0) + 1
        
        return state
    
    def _should_use_tools(self, state: AgentState) -> Literal["tools", "act", "finalize"]:
        """Determine if tools should be used"""
        if state.get('error'):
            return "finalize"
        
        if state.get('iteration_count', 0) >= self.max_iterations:
            return "finalize"
        
        plan = state.get('plan', [])
        current_step = state.get('current_step', 0)
        
        if current_step >= len(plan):
            return "finalize"
        
        current_plan_step = plan[current_step]
        
        # Check if this step requires tools
        if current_plan_step.get('requires_tools', False):
            return "tools"
        elif current_plan_step.get('action_type') == 'reasoning':
            return "act"
        else:
            return "finalize"
    
    def _tools_node(self, state: AgentState) -> AgentState:
        """Tools node - executes tools"""
        logger.info("Executing tools")
        
        plan = state.get('plan', [])
        current_step = state.get('current_step', 0)
        
        if current_step >= len(plan):
            return state
        
        plan_step = plan[current_step]
        tool_name = plan_step.get('tool')
        tool_args = plan_step.get('tool_args', {})
        
        try:
            result = self.tool_registry.execute_tool(tool_name, tool_args)
            
            state['tools_used'].append({
                'tool': tool_name,
                'args': tool_args,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            state['tool_results'].append({
                'tool': tool_name,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Update sources if tool returned sources
            if isinstance(result, dict) and 'sources' in result:
                state['sources'].extend(result['sources'])
            
            logger.info(f"Tool {tool_name} executed successfully")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            state['error'] = f"Tool execution failed: {str(e)}"
        
        state['current_step'] = current_step + 1
        
        return state
    
    def _act_node(self, state: AgentState) -> AgentState:
        """Act node - performs reasoning/analysis"""
        logger.info("Performing reasoning/analysis")
        
        plan = state.get('plan', [])
        current_step = state.get('current_step', 0)
        
        if current_step >= len(plan):
            return state
        
        plan_step = plan[current_step]
        action_type = plan_step.get('action_type', 'reasoning')
        
        try:
            # Use swarm orchestrator for reasoning
            if self.swarm_orchestrator:
                query = state['query']
                context = {
                    'plan_step': plan_step,
                    'previous_results': state.get('tool_results', []),
                    'actions_taken': state.get('actions_taken', [])
                }
                
                response = self.swarm_orchestrator.query_with_context(query, context)
                
                state['actions_taken'].append({
                    'action_type': action_type,
                    'result': response,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                # Fallback to simple reasoning
                state['actions_taken'].append({
                    'action_type': action_type,
                    'result': 'Reasoning completed',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            state['current_step'] = current_step + 1
        except Exception as e:
            logger.error(f"Error in act node: {e}")
            state['error'] = f"Action failed: {str(e)}"
        
        return state
    
    def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflection node - evaluates progress and quality"""
        logger.info("Reflecting on progress")
        
        try:
            reflection = self.reflection_engine.reflect(
                query=state['query'],
                plan=state.get('plan', []),
                actions_taken=state.get('actions_taken', []),
                tools_used=state.get('tools_used', []),
                tool_results=state.get('tool_results', [])
            )
            
            state['reflection'] = reflection
            
            # Store in memory
            self.memory_manager.store_episode(
                query=state['query'],
                actions=state.get('actions_taken', []),
                tools=state.get('tools_used', []),
                reflection=reflection
            )
        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            state['reflection'] = "Reflection completed with errors"
        
        return state
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "finalize"]:
        """Determine if we should continue or finalize"""
        if state.get('error'):
            return "finalize"
        
        if state.get('iteration_count', 0) >= self.max_iterations:
            return "finalize"
        
        plan = state.get('plan', [])
        current_step = state.get('current_step', 0)
        
        if current_step >= len(plan):
            return "finalize"
        
        # Check reflection to see if we should continue
        reflection = state.get('reflection', '')
        if 'sufficient' in reflection.lower() or 'complete' in reflection.lower():
            return "finalize"
        
        return "continue"
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize node - synthesizes final answer"""
        logger.info("Finalizing answer")
        
        try:
            # Use swarm orchestrator to synthesize final answer
            if self.swarm_orchestrator:
                query = state['query']
                context = {
                    'plan': state.get('plan', []),
                    'actions_taken': state.get('actions_taken', []),
                    'tool_results': state.get('tool_results', []),
                    'reflection': state.get('reflection', '')
                }
                
                # Handle async method call
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                final_answer = loop.run_until_complete(
                    self.swarm_orchestrator.synthesize_final_answer(query, context)
                )
                state['final_answer'] = final_answer
            else:
                # Fallback synthesis
                state['final_answer'] = self._fallback_synthesis(state)
            
            # Calculate confidence
            state['confidence'] = self._calculate_confidence(state)
            
        except Exception as e:
            logger.error(f"Error in finalization: {e}")
            state['error'] = f"Finalization failed: {str(e)}"
            state['final_answer'] = "Unable to generate final answer due to errors."
        
        return state
    
    def _fallback_synthesis(self, state: AgentState) -> str:
        """Fallback synthesis when swarm orchestrator is not available"""
        query = state['query']
        actions = state.get('actions_taken', [])
        tool_results = state.get('tool_results', [])
        
        synthesis = f"Research query: {query}\n\n"
        
        if actions:
            synthesis += "Analysis performed:\n"
            for action in actions:
                synthesis += f"- {action.get('action_type', 'action')}: {action.get('result', 'N/A')}\n"
        
        if tool_results:
            synthesis += "\nData gathered:\n"
            for result in tool_results:
                synthesis += f"- {result.get('tool', 'tool')}: {len(str(result.get('result', '')))} characters\n"
        
        return synthesis
    
    def _calculate_confidence(self, state: AgentState) -> float:
        """Calculate confidence score for the final answer"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on sources
        sources_count = len(state.get('sources', []))
        confidence += min(sources_count * 0.1, 0.3)
        
        # Increase confidence based on tools used
        tools_count = len(state.get('tools_used', []))
        confidence += min(tools_count * 0.05, 0.1)
        
        # Decrease confidence if there were errors
        if state.get('error'):
            confidence -= 0.2
        
        # Increase confidence if reflection is positive
        reflection = state.get('reflection', '').lower()
        if 'complete' in reflection or 'sufficient' in reflection:
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    async def research(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute agentic research on a query
        
        Args:
            query: Research query
            context: Optional additional context
            
        Returns:
            Research results with answer, sources, and metadata
        """
        # Initialize state
        initial_state: AgentState = {
            'query': query,
            'plan': None,
            'current_step': None,
            'actions_taken': [],
            'tools_used': [],
            'tool_results': [],
            'reflection': None,
            'final_answer': None,
            'confidence': None,
            'sources': [],
            'error': None,
            'iteration_count': 0,
            'max_iterations': self.max_iterations
        }
        
        try:
            if self.graph:
                # Run the state machine
                final_state = await self.graph.ainvoke(initial_state)
            else:
                # Fallback mode without LangGraph
                logger.warning("Running in fallback mode without LangGraph")
                final_state = await self._run_fallback(initial_state)
            
            # Format response
            return {
                'query': query,
                'answer': final_state.get('final_answer', 'No answer generated'),
                'sources': final_state.get('sources', []),
                'confidence': final_state.get('confidence', 0.0),
                'tools_used': final_state.get('tools_used', []),
                'reflection': final_state.get('reflection'),
                'metadata': {
                    'iterations': final_state.get('iteration_count', 0),
                    'actions_count': len(final_state.get('actions_taken', [])),
                    'tools_count': len(final_state.get('tools_used', [])),
                    'timestamp': datetime.utcnow().isoformat()
                },
                'error': final_state.get('error')
            }
        except Exception as e:
            logger.error(f"Error in agentic research: {e}")
            return {
                'query': query,
                'answer': f"Error during research: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _run_fallback(self, state: AgentState) -> AgentState:
        """Fallback execution without LangGraph"""
        # Execute nodes sequentially
        state = self._plan_node(state)
        if state.get('error'):
            return self._finalize_node(state)
        
        while state.get('iteration_count', 0) < self.max_iterations:
            state = self._decide_node(state)
            
            decision = self._should_use_tools(state)
            if decision == "tools":
                state = self._tools_node(state)
            elif decision == "act":
                state = self._act_node(state)
            else:
                break
            
            state = self._reflect_node(state)
            
            if self._should_continue(state) == "finalize":
                break
        
        return self._finalize_node(state)

