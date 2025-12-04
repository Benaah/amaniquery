# JSON Enforcer - 100% Compliance Guarantee

## 🎯 Purpose

The **JSON Enforcer** guarantees that LLMs (Claude 3.5 Sonnet, Grok-4, GPT-4, etc.) **ALWAYS** output valid JSON matching the exact schema, even under high load or edge cases.

---

## 🔒 The Unified Schema

Every response MUST match this exact structure with `query_type` being one of: `public_interest`, `legal`, or `research`.

### Complete Examples

See `json_enforcer.py` for 3 full examples covering all personas with perfect JSON compliance.

---

## 🚀 Quick Usage

```python
from Module4_NiruAPI.agents.json_enforcer import (
    get_json_enforcement_prompt,
    parse_llm_response,
    retry_with_enforcement
)

# Generate prompt
prompt = get_json_enforcement_prompt(
    user_query="Kanjo wameongeza parking fees?",
    retrieved_context="Resolution 42/2024...",
    persona_hint="public_interest"
)

# Get response with retry
response, error = retry_with_enforcement(llm_func, prompt)
```

---

**Built for AmaniQuery v2.0** 🇰🇪
