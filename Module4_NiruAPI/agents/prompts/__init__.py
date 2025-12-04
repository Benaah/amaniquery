"""
AmaniQ v2 Agent Prompts
=======================

System prompts for the LangGraph agent nodes.

Modules:
- supervisor_prompt: Intent classification and tool routing
- responder_prompt: Final response synthesis with citations

Author: Eng. Onyango Benard
Version: 2.0
"""

from .supervisor_prompt import (
    # Enums
    IntentType,
    ToolName,
    # Models
    ToolCall,
    ClarificationRequest,
    SupervisorDecision,
    # Constants
    TOOL_DESCRIPTIONS,
    MAX_CONTEXT_TOKENS,
    SUPERVISOR_SYSTEM_PROMPT,
    # Functions
    count_tokens,
    check_context_overflow,
    build_supervisor_messages,
    get_moonshot_config,
    parse_supervisor_response,
)

from .responder_prompt import (
    # Models
    CitationType,
    Citation,
    ResponseMetadata,
    # Prompts
    RESPONDER_SYSTEM_PROMPT,
    # Functions
    build_responder_messages,
    format_tool_data,
    get_responder_config,
    extract_analysis,
    validate_citations,
)

__all__ = [
    # Supervisor exports
    "IntentType",
    "ToolName",
    "ToolCall",
    "ClarificationRequest",
    "SupervisorDecision",
    "TOOL_DESCRIPTIONS",
    "MAX_CONTEXT_TOKENS",
    "SUPERVISOR_SYSTEM_PROMPT",
    "count_tokens",
    "check_context_overflow",
    "build_supervisor_messages",
    "get_moonshot_config",
    "parse_supervisor_response",
    # Responder exports
    "CitationType",
    "Citation",
    "ResponseMetadata",
    "RESPONDER_SYSTEM_PROMPT",
    "build_responder_messages",
    "format_tool_data",
    "get_responder_config",
    "extract_analysis",
    "validate_citations",
]
