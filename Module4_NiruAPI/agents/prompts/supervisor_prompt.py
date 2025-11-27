"""
AmaniQ v2 Supervisor Node - Bulletproof System Prompt
=====================================================

This module contains:
1. Pydantic models for strict JSON output validation
2. The supervisor system prompt with few-shot examples
3. Token counting utilities
4. Prompt construction functions

Author: Eng. Onyango Benard
Version: 2.0
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import tiktoken


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class IntentType(str, Enum):
    """Exact intent classifications - no others allowed"""
    LEGAL_RESEARCH = "LEGAL_RESEARCH"
    NEWS_SUMMARY = "NEWS_SUMMARY"
    GENERAL_CHAT = "GENERAL_CHAT"
    CLARIFY = "CLARIFY"
    ESCALATE = "ESCALATE"


class ToolName(str, Enum):
    """Exact tool names - supervisor cannot hallucinate others.
    
    All tools query the local Qdrant vector store via kb_search - NO external API calls.
    """
    SEARCH_KENYA_LAW_REPORTS = "search_kenya_law_reports"
    SEARCH_CONSTITUTION = "search_constitution"
    SEARCH_HANSARD = "search_hansard"
    SEARCH_RECENT_NEWS = "search_recent_news"
    LOOKUP_COURT_CALENDAR = "lookup_court_calendar"
    KB_SEARCH = "kb_search"  # General knowledge base search across all namespaces
    CALCULATOR = "calculator"  # For legal calculations (fees, penalties, time limits)


# Tool descriptions for supervisor context
TOOL_DESCRIPTIONS: Dict[str, str] = {
    "search_kenya_law_reports": "Search Kenya Law Reports for case law, judgments, and legal precedents from the kenya_law namespace. Use for: case citations, legal principles, court decisions, eKLR cases.",
    "search_constitution": "Search the Constitution of Kenya 2010 from the kenya_law namespace. Use for: fundamental rights, government structure, constitutional provisions, Bill of Rights, Article queries.",
    "search_hansard": "Search Kenya Parliamentary Hansard records from the kenya_parliament namespace. Use for: legislative debates, bill discussions, MP statements, committee reports.",
    "search_recent_news": "Search Kenyan news articles from kenya_news and global_trends namespaces. Use for: current events, recent legal developments, breaking news about cases.",
    "lookup_court_calendar": "Look up court schedules and hearing dates from the kenya_law namespace. Use for: case hearing dates, court sessions, judicial calendar queries.",
    "kb_search": "General search across ALL namespaces (kenya_law, kenya_news, kenya_parliament, historical, global_trends). Use when query spans multiple domains or for broad searches.",
    "calculator": "Perform mathematical calculations. Use for: legal fee calculations, penalty computations, time limit calculations, interest rates.",
}


# Maximum context window
MAX_CONTEXT_TOKENS = 12000


# =============================================================================
# PYDANTIC MODELS FOR STRICT JSON OUTPUT
# =============================================================================

class ToolCall(BaseModel):
    """Single tool invocation in the parallel plan"""
    tool_name: ToolName = Field(
        ...,
        description="Exact tool name from allowed list. No hallucination allowed."
    )
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Optimized search query for this specific tool"
    )
    priority: Literal[1, 2, 3] = Field(
        default=2,
        description="Execution priority: 1=critical, 2=important, 3=supplementary"
    )
    
    @field_validator('tool_name', mode='before')
    @classmethod
    def validate_tool_name(cls, v):
        """Ensure tool name is exactly one of the allowed values"""
        if isinstance(v, str):
            # Normalize and validate
            normalized = v.lower().strip()
            valid_tools = [t.value for t in ToolName]
            if normalized not in valid_tools:
                raise ValueError(
                    f"Invalid tool name '{v}'. Must be exactly one of: {valid_tools}"
                )
            return normalized
        return v


class ClarificationRequest(BaseModel):
    """Structured clarification when more info needed"""
    missing_fields: List[str] = Field(
        ...,
        min_length=1,
        description="List of specific missing information (e.g., 'year', 'case_number', 'act_name')"
    )
    clarification_question: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Clear, specific question to ask the user in English or Swahili"
    )
    partial_understanding: str = Field(
        ...,
        max_length=200,
        description="What you understood so far from the query"
    )


class SupervisorDecision(BaseModel):
    """
    The ONLY output format for the Supervisor node.
    Strict JSON validation - any deviation will be rejected.
    """
    
    # Required fields
    intent: IntentType = Field(
        ...,
        description="Exactly one of: LEGAL_RESEARCH, NEWS_SUMMARY, GENERAL_CHAT, CLARIFY, ESCALATE"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    
    reasoning: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Brief chain-of-thought explanation (max 200 chars)"
    )
    
    # Conditional fields based on intent
    tool_plan: Optional[List[ToolCall]] = Field(
        default=None,
        description="Required if intent is LEGAL_RESEARCH or NEWS_SUMMARY. List of tools to call in parallel."
    )
    
    clarification: Optional[ClarificationRequest] = Field(
        default=None,
        description="Required if intent is CLARIFY. Details about what info is missing."
    )
    
    direct_response: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Required if intent is GENERAL_CHAT. Direct answer without tool calls."
    )
    
    escalation_reason: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Required if intent is ESCALATE. Why human review is needed."
    )
    
    # Metadata
    detected_language: Literal["en", "sw", "mixed"] = Field(
        default="en",
        description="Detected query language: English, Swahili, or mixed"
    )
    
    detected_entities: List[str] = Field(
        default_factory=list,
        description="Extracted legal entities: case names, statute refs, dates, courts"
    )
    
    token_count: int = Field(
        ...,
        ge=0,
        description="Estimated token count of the input context"
    )
    
    context_overflow: bool = Field(
        default=False,
        description="True if context exceeds 12k tokens - must refuse processing"
    )
    
    @model_validator(mode='after')
    def validate_conditional_fields(self):
        """Ensure required fields are present based on intent"""
        
        # Context overflow check
        if self.context_overflow:
            if self.intent != IntentType.ESCALATE:
                raise ValueError(
                    "When context_overflow=True, intent must be ESCALATE"
                )
            return self
        
        # Intent-specific validation
        if self.intent == IntentType.LEGAL_RESEARCH:
            if not self.tool_plan or len(self.tool_plan) == 0:
                raise ValueError(
                    "LEGAL_RESEARCH intent requires non-empty tool_plan"
                )
            # Validate at least one legal tool is included
            legal_tools = {ToolName.SEARCH_KENYA_LAW_REPORTS, ToolName.SEARCH_CONSTITUTION, ToolName.SEARCH_HANSARD}
            plan_tools = {tc.tool_name for tc in self.tool_plan}
            if not plan_tools.intersection(legal_tools):
                raise ValueError(
                    "LEGAL_RESEARCH must include at least one legal tool"
                )
                
        elif self.intent == IntentType.NEWS_SUMMARY:
            if not self.tool_plan or len(self.tool_plan) == 0:
                raise ValueError(
                    "NEWS_SUMMARY intent requires non-empty tool_plan"
                )
            # Must include news tool
            if not any(tc.tool_name == ToolName.SEARCH_RECENT_NEWS for tc in self.tool_plan):
                raise ValueError(
                    "NEWS_SUMMARY must include search_recent_news tool"
                )
                
        elif self.intent == IntentType.CLARIFY:
            if not self.clarification:
                raise ValueError(
                    "CLARIFY intent requires clarification field"
                )
                
        elif self.intent == IntentType.GENERAL_CHAT:
            if not self.direct_response:
                raise ValueError(
                    "GENERAL_CHAT intent requires direct_response field"
                )
                
        elif self.intent == IntentType.ESCALATE:
            if not self.escalation_reason and not self.context_overflow:
                raise ValueError(
                    "ESCALATE intent requires escalation_reason field"
                )
        
        return self


# =============================================================================
# TOKEN COUNTING UTILITY
# =============================================================================

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.
    Falls back to word-based estimation if tiktoken fails.
    
    Args:
        text: Input text to count
        model: Model name for tokenizer selection
        
    Returns:
        Estimated token count
    """
    try:
        # Use cl100k_base encoding (works for most modern models)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate of 1 token per 4 characters
        return len(text) // 4


def check_context_overflow(messages: List[Dict[str, Any]], max_tokens: int = MAX_CONTEXT_TOKENS) -> tuple[int, bool]:
    """
    Check if message context exceeds token limit.
    
    Args:
        messages: List of message dictionaries
        max_tokens: Maximum allowed tokens
        
    Returns:
        Tuple of (token_count, is_overflow)
    """
    total_text = ""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_text += content + "\n"
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    total_text += str(item.get("text", "")) + "\n"
    
    token_count = count_tokens(total_text)
    return token_count, token_count > max_tokens


# =============================================================================
# SUPERVISOR SYSTEM PROMPT
# =============================================================================

SUPERVISOR_SYSTEM_PROMPT = """You are the AmaniQ Supervisor, the routing brain for a Kenyan legal research assistant serving 5,000+ daily users including law students, paralegals, and citizens.

## YOUR ROLE
You analyze user queries and decide:
1. What is the user's intent?
2. Which tools (if any) should be called IN PARALLEL?
3. Is clarification needed before proceeding?

## CRITICAL RULES - VIOLATIONS WILL CAUSE SYSTEM FAILURE

### Rule 1: INTENT CLASSIFICATION (Exactly ONE)
You MUST classify every query into exactly ONE of these intents:
- `LEGAL_RESEARCH`: Questions about Kenyan law, cases, statutes, constitutional provisions, legal procedures
- `NEWS_SUMMARY`: Requests for recent news, current events, trending topics in Kenya
- `GENERAL_CHAT`: Greetings, thanks, simple questions not requiring tools, off-topic queries
- `CLARIFY`: Query is ambiguous or missing critical information (year, case name, specific act)
- `ESCALATE`: Sensitive topics, potential harm, context overflow, or system limitations

### Rule 2: TOOL NAMES ARE SACRED
You may ONLY use these exact tool names. ANY other name is a hallucination and will crash the system:
```
search_kenya_law_reports  - Kenya Law Reports (eKLR) for case law and judgments
search_constitution       - Constitution of Kenya 2010
search_hansard           - Parliamentary Hansard records
search_recent_news       - Recent Kenyan news articles  
lookup_court_calendar    - Court schedules and hearing dates
```

### Rule 3: PARALLEL TOOL EXECUTION
When intent is LEGAL_RESEARCH or NEWS_SUMMARY, you MUST provide a tool_plan with 1-4 tools to call simultaneously.
- Group complementary tools (e.g., search_kenya_law_reports + search_constitution for rights questions)
- Each tool gets its own optimized query string
- Assign priority: 1=critical, 2=important, 3=supplementary

### Rule 4: TOKEN COUNTING
You MUST estimate the token count of the input context.
If token_count > 12000:
- Set context_overflow = true
- Set intent = "ESCALATE"
- Set escalation_reason = "Context exceeds 12k token limit. Please start a new conversation or simplify your query."

### Rule 5: CLARIFICATION TRIGGERS
Set intent = "CLARIFY" when:
- User mentions "that case" without specifying which case
- Legal question lacks year/timeframe when relevant
- Statute reference is incomplete (e.g., "the Act" without name)
- Case number format is ambiguous
- Multiple possible interpretations exist

### Rule 6: OUTPUT FORMAT
You MUST output ONLY valid JSON matching the SupervisorDecision schema. No markdown, no explanation outside JSON.

## AVAILABLE TOOL DESCRIPTIONS

| Tool | Use For |
|------|---------|
| search_kenya_law_reports | Case citations, judgments, legal precedents, court decisions |
| search_constitution | Fundamental rights, Bill of Rights, government structure, constitutional provisions |
| search_hansard | Legislative debates, bill discussions, MP statements, committee reports |
| search_recent_news | Current events, recent legal developments, breaking news |
| lookup_court_calendar | Court hearing dates, judicial calendar, case schedules |

## FEW-SHOT EXAMPLES

### Example 1: Clear Legal Research Query
**User Query**: "What did the Supreme Court say about the two-thirds gender rule in the BBI case?"

**Output**:
```json
{
  "intent": "LEGAL_RESEARCH",
  "confidence": 0.95,
  "reasoning": "Clear question about Supreme Court ruling on BBI case regarding gender rule - requires case law and constitution search",
  "tool_plan": [
    {
      "tool_name": "search_kenya_law_reports",
      "query": "BBI Building Bridges Initiative Supreme Court two-thirds gender rule 2022",
      "priority": 1
    },
    {
      "tool_name": "search_constitution",
      "query": "Article 27 two-thirds gender principle representation",
      "priority": 2
    }
  ],
  "clarification": null,
  "direct_response": null,
  "escalation_reason": null,
  "detected_language": "en",
  "detected_entities": ["Supreme Court", "BBI case", "two-thirds gender rule"],
  "token_count": 847,
  "context_overflow": false
}
```

### Example 2: Query Needing Clarification
**User Query**: "Nataka kujua kuhusu ile kesi ya ardhi" (I want to know about that land case)

**Output**:
```json
{
  "intent": "CLARIFY",
  "confidence": 0.85,
  "reasoning": "User asks about 'that land case' in Swahili but doesn't specify which case, parties, year, or location",
  "tool_plan": null,
  "clarification": {
    "missing_fields": ["case_name", "year", "parties", "county"],
    "clarification_question": "Tafadhali nisaidie kuelewa kesi gani ya ardhi unamaanisha. Je, unaweza kutoa: jina la kesi, mwaka, au mahakama iliyohusika? (Please help me understand which land case you mean. Can you provide: case name, year, or court involved?)",
    "partial_understanding": "User is interested in a land dispute case in Kenya"
  },
  "direct_response": null,
  "escalation_reason": null,
  "detected_language": "sw",
  "detected_entities": ["land case"],
  "token_count": 623,
  "context_overflow": false
}
```

### Example 3: News Summary Request
**User Query**: "What's the latest on the Finance Bill 2024 protests?"

**Output**:
```json
{
  "intent": "NEWS_SUMMARY",
  "confidence": 0.92,
  "reasoning": "User asks for recent news about Finance Bill 2024 protests - a current event requiring news search plus parliamentary context",
  "tool_plan": [
    {
      "tool_name": "search_recent_news",
      "query": "Kenya Finance Bill 2024 protests Gen Z demonstrations",
      "priority": 1
    },
    {
      "tool_name": "search_hansard",
      "query": "Finance Bill 2024 parliamentary debate",
      "priority": 2
    }
  ],
  "clarification": null,
  "direct_response": null,
  "escalation_reason": null,
  "detected_language": "en",
  "detected_entities": ["Finance Bill 2024", "protests"],
  "token_count": 512,
  "context_overflow": false
}
```

### Example 4: General Chat (No Tools Needed)
**User Query**: "Asante sana for the help yesterday!"

**Output**:
```json
{
  "intent": "GENERAL_CHAT",
  "confidence": 0.98,
  "reasoning": "User expressing gratitude in Swahili-English mix - no research needed, direct response appropriate",
  "tool_plan": null,
  "clarification": null,
  "direct_response": "Karibu sana! I'm glad I could help. Feel free to ask if you have any more questions about Kenyan law or legal matters. 🇰🇪",
  "escalation_reason": null,
  "detected_language": "mixed",
  "detected_entities": [],
  "token_count": 234,
  "context_overflow": false
}
```

### Example 5: Complex Multi-Tool Legal Query
**User Query**: "I'm a law student at UoN. Can you help me understand the Njoya case on constitutional amendments and how it relates to Article 255 basic structure doctrine?"

**Output**:
```json
{
  "intent": "LEGAL_RESEARCH",
  "confidence": 0.97,
  "reasoning": "Law student asking about landmark Njoya case and basic structure doctrine - requires comprehensive legal research across case law, constitution, and possibly academic commentary",
  "tool_plan": [
    {
      "tool_name": "search_kenya_law_reports",
      "query": "Njoya v Attorney General constitutional amendment basic structure 2004",
      "priority": 1
    },
    {
      "tool_name": "search_constitution",
      "query": "Article 255 amendment procedure basic structure entrenched provisions",
      "priority": 1
    },
    {
      "tool_name": "search_kenya_law_reports",
      "query": "basic structure doctrine Kenya constitutional amendment limits",
      "priority": 2
    }
  ],
  "clarification": null,
  "direct_response": null,
  "escalation_reason": null,
  "detected_language": "en",
  "detected_entities": ["Njoya case", "Article 255", "basic structure doctrine", "UoN", "constitutional amendments"],
  "token_count": 1024,
  "context_overflow": false
}
```

## HANDLING EDGE CASES

### Swahili Queries
- Detect language and respond appropriately
- Common legal terms: sheria (law), haki (right), katiba (constitution), mahakama (court), kesi (case)
- Translate query concepts to English for tool execution

### Ambiguous Queries
When in doubt, prefer CLARIFY over guessing. A wrong search wastes user time.

### Sensitive Topics
Set intent = "ESCALATE" for:
- Requests for specific legal advice (vs. legal information)
- Questions about ongoing criminal cases where user may be involved
- Any indication of harm or violence
- Professional ethics violations

### Context Overflow
If estimated tokens > 12000, you MUST refuse:
```json
{
  "intent": "ESCALATE",
  "confidence": 1.0,
  "reasoning": "Context window exceeded - cannot process safely",
  "tool_plan": null,
  "clarification": null,
  "direct_response": null,
  "escalation_reason": "Your conversation has exceeded the 12,000 token limit. Please start a new conversation or summarize your question.",
  "detected_language": "en",
  "detected_entities": [],
  "token_count": 12847,
  "context_overflow": true
}
```

## FINAL REMINDER
Your output MUST be valid JSON matching SupervisorDecision schema.
- No markdown code blocks
- No explanatory text outside JSON
- No hallucinated tool names
- One intent only
- All required fields for that intent must be present

You are the gatekeeper. Route wisely."""


# =============================================================================
# PROMPT CONSTRUCTION FUNCTIONS
# =============================================================================

def build_supervisor_messages(
    user_query: str,
    message_history: List[Dict[str, Any]],
    user_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Build the complete message list for supervisor invocation.
    
    Args:
        user_query: Current user query
        message_history: Previous messages in conversation
        user_context: Optional user metadata (expertise level, preferences)
        
    Returns:
        List of messages for LLM invocation
    """
    messages = [
        {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT}
    ]
    
    # Add context about user if available
    if user_context:
        context_str = f"""
## USER CONTEXT
- Expertise Level: {user_context.get('expertise_level', 'unknown')}
- Frequent Topics: {', '.join(user_context.get('frequent_topics', []))}
- Preferred Language: {user_context.get('preferred_language', 'en')}
- Session Queries So Far: {user_context.get('session_query_count', 0)}
"""
        messages[0]["content"] += context_str
    
    # Add relevant message history (last 10 messages max)
    for msg in message_history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ["user", "assistant"]:
            messages.append({"role": role, "content": content})
    
    # Add current query
    messages.append({
        "role": "user",
        "content": f"Analyze this query and output your decision as JSON:\n\n{user_query}"
    })
    
    return messages


def get_moonshot_config() -> Dict[str, Any]:
    """
    Get Moonshot AI configuration for supervisor calls.
    Forces JSON mode for reliable structured output.
    
    Returns:
        Configuration dictionary for Moonshot API
    """
    return {
        "model": "moonshot-v1-32k",
        "temperature": 0.1,  # Low temperature for deterministic routing
        "max_tokens": 800,   # Enough for full response
        "response_format": {"type": "json_object"},  # Force JSON mode
        "top_p": 0.95,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }


# =============================================================================
# VALIDATION AND PARSING
# =============================================================================

def parse_supervisor_response(response_text: str) -> SupervisorDecision:
    """
    Parse and validate supervisor response.
    
    Args:
        response_text: Raw JSON string from LLM
        
    Returns:
        Validated SupervisorDecision
        
    Raises:
        ValueError: If response is invalid
    """
    import json
    
    try:
        # Clean response (remove markdown if present)
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # Remove markdown code block
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        
        # Parse JSON
        data = json.loads(cleaned)
        
        # Validate with Pydantic
        decision = SupervisorDecision(**data)
        return decision
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in supervisor response: {e}")
    except Exception as e:
        raise ValueError(f"Failed to validate supervisor response: {e}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "IntentType",
    "ToolName",
    # Models
    "ToolCall",
    "ClarificationRequest", 
    "SupervisorDecision",
    # Constants
    "TOOL_DESCRIPTIONS",
    "MAX_CONTEXT_TOKENS",
    "SUPERVISOR_SYSTEM_PROMPT",
    # Functions
    "count_tokens",
    "check_context_overflow",
    "build_supervisor_messages",
    "get_moonshot_config",
    "parse_supervisor_response",
]
