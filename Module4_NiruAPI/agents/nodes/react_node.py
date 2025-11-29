"""
ReAct Agent Node for Agentic RAG
Implements Reasoning + Acting loop for complex queries
"""
import json
import re
from typing import Dict, Any
from loguru import logger


# =============================================================================
# REACT PROMPT TEMPLATE
# =============================================================================

REACT_PROMPT = """You are AmaniQuery, an expert on Kenyan law, parliament, and governance.

You have access to these tools:
{tool_descriptions}

Solve the question step-by-step using this format:

Thought: [Your reasoning about what to do next]
Action: tool_name: {{"param1": "value1", "param2": "value2"}}
Observation: [Tool output will appear here - DO NOT FILL THIS]

Repeat Thought-Action-Observation until you have enough information.

When ready to answer:
Thought: I now have enough information to provide a complete answer
Final Answer: [Your comprehensive answer with full citations in Kenyan legal format]

IMPORTANT RULES:
1. Cite ALL sources (e.g., "Finance Bill 2024, Section 12", "Hansard, 15th June 2024")
2. If a tool fails, try an alternative approach
3. Maximum 5 iterations - be efficient
4. STOP when you have enough information
5. Do NOT fill in Observation - only Thought and Action

Question: {query}

Begin:
"""


# =============================================================================
# REACT NODE
# =============================================================================

def react_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    ReAct agent node - iterative tool use with reasoning
    
    Args:
        state: AmaniQState
    
    Returns:
        Updated state with tool results and final answer
    """
    query = state.get("current_query")
    logger.info(f"[ReAct Agent] Processing: {query[:80]}...")
    
    # Get tool registry
    from Module4_NiruAPI.agents.tools.agentic_tools import get_agentic_tools
    tool_registry = get_agentic_tools()
    
    if not tool_registry:
        logger.error("Agentic tools not initialized")
        return {
            "react_iterations": [],
            "react_failed": True,
            "error": "Tools not available"
        }
    
    # Initialize LLM client
    from Module4_NiruAPI.agents.amaniq_v2 import MoonshotClient, AmaniQConfig
    config = AmaniQConfig()
    client = MoonshotClient.get_client(config)
    
    # Build prompt
    tool_descriptions = tool_registry.get_tool_descriptions()
    prompt = REACT_PROMPT.format(
        tool_descriptions=tool_descriptions,
        query=query
    )
    
    iterations = []
    max_iterations = 5
    conversation = prompt
    
    for iteration in range(max_iterations):
        logger.info(f"[ReAct] Iteration {iteration + 1}/{max_iterations}")
        
        # Get LLM response
        try:
            response = client.chat.completions.create(
                model="moonshot-v1-32k",
                messages=[{"role": "user", "content": conversation}],
                temperature=0.3,
                max_tokens=1500
            )
            
            agent_response = response.choices[0].message.content
            logger.debug(f"[ReAct] Agent response: {agent_response[:200]}...")
            
            # Check if final answer
            if "Final Answer:" in agent_response:
                # Extract final answer
                final_answer = agent_response.split("Final Answer:")[-1].strip()
                logger.info("[ReAct] Reached final answer")
                
                iterations.append({
                    "iteration": iteration + 1,
                    "agent_response": agent_response,
                    "final_answer": final_answer
                })
                
                return {
                    "react_iterations": iterations,
                    "react_final_answer": final_answer,
                    "react_success": True,
                    "tool_results": []  # Collect all tool results
                }
            
            # Parse tool  call
            tool_match = re.search(r'Action:\s*(\w+):\s*({.*?})', agent_response, re.DOTALL)
            
            if not tool_match:
                logger.warning("[ReAct] No valid action found - forcing final answer")
                conversation += f"\n\n{agent_response}\n\nThought: I should provide a final answer now.\nFinal Answer:"
                continue
            
            tool_name = tool_match.group(1)
            tool_params_str = tool_match.group(2)
            
            # Parse parameters
            try:
                tool_params = json.loads(tool_params_str)
            except json.JSONDecodeError:
                logger.error(f"[ReAct] Invalid JSON parameters: {tool_params_str}")
                observation = f"ERROR: Invalid parameters format. Please use valid JSON."
                conversation += f"\n\n{agent_response}\nObservation: {observation}\n"
                iterations.append({
                    "iteration": iteration + 1,
                    "thought": agent_response,
                    "action": f"{tool_name}",
                    "observation": observation,
                    "success": False
                })
                continue
            
            # Execute tool
            logger.info(f"[ReAct] Executing {tool_name} with params: {tool_params}")
            tool_result = tool_registry.execute(tool_name, **tool_params)
            
            # Format observation
            if tool_result.get("success"):
                observation = json.dumps(tool_result, indent=2, default=str)[:500]  # Truncate
            else:
                observation = f"ERROR: {tool_result.get('error', 'Unknown error')}"
            
            # Update conversation
            conversation += f"\n\n{agent_response}\nObservation: {observation}\n"
            
            # Store iteration
            iterations.append({
                "iteration": iteration + 1,
                "thought": agent_response,
                "action": f"{tool_name}({tool_params})",
                "observation": observation,
                "tool_result": tool_result,
                "success": tool_result.get("success", False)
            })
            
        except Exception as e:
            logger.error(f"[ReAct] Error in iteration {iteration + 1}: {e}")
            return {
                "react_iterations": iterations,
                "react_failed": True,
                "error": str(e)
            }
    
    # Max iterations reached without final answer
    logger.warning("[ReAct] Max iterations reached - forcing answer")
    
    # Force final answer with what we have
    conversation += "\n\nThought: I've gathered information from multiple tools. Time to synthesize a final answer.\nFinal Answer:"
    
    try:
        response = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=[{"role": "user", "content": conversation}],
            temperature=0.3,
            max_tokens=1000
        )
        
        final_answer = response.choices[0].message.content.strip()
        
        return {
            "react_iterations": iterations,
            "react_final_answer": final_answer,
            "react_success": True,
            "react_max_iterations_reached": True
        }
    except Exception as e:
        logger.error(f"[ReAct] Failed to generate final answer: {e}")
        return {
            "react_iterations": iterations,
            "react_failed": True,
            "error": f"Failed to complete: {str(e)}"
        }
