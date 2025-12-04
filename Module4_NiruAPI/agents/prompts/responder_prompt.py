"""
AmaniQuery Engine v2.0 - Responder Prompt Module
=================================================

This module defines the core system prompt and logic for the Responder node,
which synthesizes tool results into final responses.

It enforces:
1. Strict citation rules (Bluebook/Kenyan style)
2. Handling of repealed laws
3. Conflict flagging
4. Stale data disclaimers
5. Tone and persona consistency

Usage:
    from Module4_NiruAPI.agents.prompts.responder_prompt import (
        RESPONDER_SYSTEM_PROMPT,
        build_responder_messages,
        extract_analysis,
        Citation,
        CitationType,
        ResponseMetadata,
        format_tool_data,
        get_responder_config,
        validate_citations
    )
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from enum import Enum
from pydantic import BaseModel, Field

# ============================================================================
# CURRENT DATE
# ============================================================================
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class CitationType(str, Enum):
    """Types of legal citations"""
    CASE_LAW = "case_law"
    STATUTE = "statute"
    CONSTITUTION = "constitution"
    HANSARD = "hansard"
    NEWS = "news"
    SECONDARY = "secondary"


class Citation(BaseModel):
    """Structured citation for legal sources"""
    type: CitationType = Field(default=CitationType.SECONDARY)
    title: str = Field(..., description="Case name, statute title, or article name")
    reference: str = Field(..., description="e.g., [2022] eKLR, Cap 63, Article 27")
    url: Optional[str] = Field(default=None, description="Direct URL to source")
    section: Optional[str] = Field(default=None, description="Specific section/article")
    year: Optional[int] = Field(default=None)
    court: Optional[str] = Field(default=None, description="For case law")
    is_current: bool = Field(default=True, description="False if repealed/overruled")
    
    def format_citation(self) -> str:
        """Format citation string based on type"""
        if self.type == CitationType.CASE_LAW:
            return f"*{self.title}* {self.reference}"
        elif self.type == CitationType.STATUTE:
            return f"{self.section}, {self.title} ({self.reference})"
        elif self.type == CitationType.CONSTITUTION:
            return f"{self.section}, {self.title}"
        return f"{self.title} ({self.reference})"


class ResponseMetadata(BaseModel):
    """Metadata for the response"""
    confidence_score: float
    sources_used: List[str]
    legal_warning: bool = False


# ============================================================================
# RESPONDER SYSTEM PROMPT
# ============================================================================

RESPONDER_SYSTEM_PROMPT = f"""You are AmaniQ, a senior legal research assistant serving Kenyans. Your job is to transform raw search results into clear, accurate, and properly-cited legal information.

## YOUR IDENTITY
You are like that brilliant friend who went to law school - knowledgeable but approachable. You speak naturally, mixing English and Swahili the way educated Kenyans do. You never sound like a robot or a colonial-era textbook.

## CRITICAL RULES - VIOLATIONS ARE UNACCEPTABLE

### Rule 1: THINK BEFORE YOU WRITE
Before writing your response, you MUST complete this internal analysis (wrapped in <analysis> tags that won't be shown to user):

```
<analysis>
1. QUESTION UNDERSTOOD: [Restate what user is really asking]
2. SOURCES REVIEW: [List each source, its date, relevance score]
3. CURRENT LAW CHECK: [Verify no source is repealed/overruled]
4. CONFLICT CHECK: [Do any sources contradict each other?]
5. GAPS IDENTIFIED: [What relevant info is missing?]
6. RESPONSE PLAN: [How will I structure the answer?]
</analysis>
```

### Rule 2: CITATION REQUIREMENTS
Every legal claim MUST have a citation. Format:
- **Case Law**: *Case Name* [Year] eKLR or [Year] KLR (Court)
- **Constitution**: Article X(Y), Constitution of Kenya 2010
- **Statutes**: Section X, [Act Name] (Cap XX)
- **Hansard**: Kenya Hansard, [Date], Page X

Include the source URL when available: `[Read full judgment](url)`

### Rule 3: NEVER CITE REPEALED LAW AS CURRENT
If a statute has been repealed or a case overruled:
- ❌ Do NOT cite it as current law
- ✅ DO mention it with clear caveat: "This was the position under the repealed [Act], but under the current [New Act]..."

### Rule 4: HANDLE CONFLICTS
If sources disagree (e.g., High Court vs Court of Appeal):
- State the conflict clearly: "While the High Court held X, the Court of Appeal overturned this in Y..."
- Prioritize the higher court or more recent statute.

### Rule 5: BE HONEST ABOUT GAPS
If the search results don't answer the question:
- Say: "I couldn't find specific information on [X] in the available sources."
- Do NOT hallucinate.

### Rule 6: TONE & STYLE
- **Professional but Warm**: "Habari! Here is what the law says..."
- **Plain English**: Explain "res judicata" as "a matter already judged".
- **Kenyan Context**: Use examples relevant to Kenya (e.g., M-Pesa, land registry).

### Rule 7: STRUCTURE YOUR RESPONSE

```
[Warm acknowledgment of the question]

**Quick Answer**: [1-2 sentence direct answer]

**Detailed Explanation**:
[Well-structured explanation with citations]

**Key Points to Remember**:
• [Bullet 1]
• [Bullet 2]

**Relevant Citations**:
1. [Full citation with URL]
2. [Full citation with URL]

[Any disclaimers if needed]

[Friendly closing - offer to clarify or explore further]
```

## TODAY'S DATE: {CURRENT_DATE}

You are AmaniQ. Saidia Mkenya mwenzako."""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_responder_messages(
    original_question: str,
    tool_results: List[Dict[str, Any]],
    supervisor_decision: Dict[str, Any],
    message_history: Optional[List[Dict[str, Any]]] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Build the complete message list for responder invocation.
    """
    messages = [
        {"role": "system", "content": RESPONDER_SYSTEM_PROMPT}
    ]
    
    # Add context about user if available
    if user_context:
        context_str = f"\\n## USER CONTEXT\\n- Expertise Level: {user_context.get('expertise_level', 'unknown')}\\n"
        messages[0]["content"] += context_str
    
    # Add conversation history
    if message_history:
        for msg in message_history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})
    
    # Build the context message with all tool results
    context_parts = [
        "## USER'S QUESTION",
        f"```\\n{original_question}\\n```",
        "",
        "## SUPERVISOR ANALYSIS",
        f"- Intent: {supervisor_decision.get('intent', 'unknown')}",
        "",
        "## TOOL RESULTS",
    ]
    
    # Add each tool's results
    for i, result in enumerate(tool_results, 1):
        tool_name = result.get("tool_name", "unknown")
        data = result.get("data", {})
        context_parts.append(f"\\n### Tool {i}: {tool_name}")
        context_parts.append(format_tool_data(tool_name, data))
    
    # Add instructions
    context_parts.extend([
        "",
        "---",
        "## YOUR TASK",
        "Using the above tool results, provide a comprehensive, well-cited response to the user's question.",
        "Remember to:",
        "1. Complete your <analysis> thinking first",
        "2. Include exact citations with URLs",
        "3. Check for repealed laws or conflicting authorities",
        "4. Add stale data disclaimer if sources are old",
        "5. Use natural Kenyan English/Swahili mix",
        "",
        "Generate your response now:"
    ])
    
    messages.append({
        "role": "user",
        "content": "\\n".join(context_parts)
    })
    
    return messages


def format_tool_data(tool_name: str, data: Dict[str, Any]) -> str:
    """Format tool-specific data for the responder context"""
    
    if tool_name == "kb_search":
        results = data.get("search_results", [])
        if not results:
            return "**Results**: No relevant documents found."
        
        lines = ["**Results**:"]
        for i, item in enumerate(results, 1):
            content = item.get("content", "")[:500]
            metadata = item.get("metadata", {})
            score = item.get("score", 0)
            
            lines.append(f"\\n**[{i}]** (relevance: {score:.2f})")
            lines.append(f"- Title: {metadata.get('title', 'Untitled')}")
            lines.append(f"- Source: {metadata.get('source_name', metadata.get('category', 'Unknown'))}")
            if metadata.get('source_url'):
                lines.append(f"- URL: {metadata.get('source_url')}")
            lines.append(f"- Snippet: {content}")
        
        return "\\n".join(lines)
    
    elif tool_name == "news_search":
        articles = data.get("articles", data.get("results", []))
        if not articles:
            return "**Results**: No news articles found."
        
        lines = ["**Results**:"]
        for i, article in enumerate(articles[:5], 1):
            lines.append(f"\\n**[{i}]** {article.get('title', 'Untitled')}")
            lines.append(f"- Source: {article.get('source', 'Unknown')}")
            lines.append(f"- Date: {article.get('date', article.get('published', 'Unknown'))}")
            if article.get('url'):
                lines.append(f"- URL: {article.get('url')}")
        
        return "\\n".join(lines)
    
    # Default formatting
    return f"**Results**:\\n```json\\n{json.dumps(data, indent=2, default=str)[:1500]}\\n```"


def get_responder_config() -> Dict[str, Any]:
    """Get Moonshot AI configuration for responder calls"""
    return {
        "model": "moonshot-v1-128k",
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": True,
    }


def extract_analysis(response: str) -> tuple[str, str]:
    """Extract the <analysis> section and main response"""
    import re
    
    analysis_match = re.search(r'<analysis>(.*?)</analysis>', response, re.DOTALL)
    
    if analysis_match:
        analysis = analysis_match.group(1).strip()
        user_response = re.sub(r'<analysis>.*?</analysis>', '', response, flags=re.DOTALL).strip()
        return analysis, user_response
    
    return "", response


def validate_citations(response: str) -> List[str]:
    """Check if response contains proper citations"""
    warnings = []
    uncited_patterns = [
        (r'the law (says|requires|provides|states)', "Legal claim without citation"),
        (r'under (the|Kenyan) law', "Reference to law without specific statute"),
    ]
    
    import re
    for pattern, warning in uncited_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            if not re.search(r'\[\d{4}\]|Article \d+|Section \d+|Cap \d+', response):
                warnings.append(warning)
    
    return warnings
