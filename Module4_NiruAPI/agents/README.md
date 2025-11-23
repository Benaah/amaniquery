# AmaniQuery v2.0 - Intent Router & Kenyanizer System

## 🎯 Complete System Overview

The AmaniQuery v2.0 intent routing and response personalization system consists of **three core modules** that work together to provide Kenyan-centric civic AI:

```
User Query
    ↓
[1] Intent Router → Classifies user type (wanjiku/wakili/mwanahabari)
    ↓
[2] Sheng Translator → Converts Sheng to formal (if needed)
    ↓
RAG Retrieval → Searches parliamentary/government data
    ↓
[3] Kenyanizer → Formats response for user persona
    ↓
Final Answer (Personalized for Kenyan context)
```

---

## 📦 Module Documentation

### 1. Intent Router ([`intent_router.py`](./intent_router.py))

**Purpose:** Zero-shot classification of incoming queries into three user personas

**Key Features:**
- ✅ 120+ token classification prompt
- ✅ 15 diverse few-shot examples (Sheng, English, Swahili, mixed)
- ✅ Handles edge cases (law students, journalists using slang)
- ✅ JSON output with confidence scores
- ✅ Works on gemini-1.5-flash or llama-3-70b

**User Personas:**
| Persona | Description | Example Query |
|---------|-------------|---------------|
| **wanjiku** 🧑‍🌾 | Ordinary citizen | "Kanjo wameamua nini kuhusu parking doh?" |
| **wakili** ⚖️ | Legal professional | "Section 3(b) of Finance Act 2023?" |
| **mwanahabari** 📰 | Journalist/researcher | "MP attendance rate Q3 2024?" |

**Quick Start:**
```python
from Module4_NiruAPI.agents.intent_router import classify_query

result = classify_query("Naskia tax inakuja?", llm_function=my_llm)
# {"query_type": "wanjiku", "confidence": 0.9, ...}
```

📖 **[Full Documentation](./INTENT_ROUTER_GUIDE.md)**

---

### 2. Sheng Translator ([`sheng_translator.py`](./sheng_translator.py))

**Purpose:** Bidirectional translation between Kenyan Sheng and formal institutional language

**Key Features:**
- ✅ 120+ Sheng ↔ Formal term dictionary
- ✅ Automatic Sheng detection with confidence scoring
- ✅ Two translation modes: dictionary-only or LLM-powered
- ✅ Response re-injection to preserve user's language style
- ✅ Full pipeline integration

**Translation Flow:**
```
"Kanjo wameamua nini kuhusu parking doh?"
    ↓ [Detect Sheng: 75% confidence]
"What has Nairobi City County resolved regarding parking fees?"
    ↓ [RAG Search]
"Nairobi City County increased parking fees to KES 300..."
    ↓ [Re-inject Sheng]
"Kanjo wameongeza parking fees kwa town to KES 300 per day..."
```

**Dictionary Categories:**
- Government & Institutions (8 terms)
- Political Figures (10 terms)
- Money & Finance (10 terms)
- Transport (9 terms)
- And 80+ more!

**Quick Start:**
```python
from Module4_NiruAPI.agents.sheng_translator import (
    translate_to_formal,
    translate_to_sheng,
    detect_sheng
)

# Step 1: Detect Sheng
is_sheng, conf, terms = detect_sheng("Kanjo wameamua nini?")

# Step 2: Translate to formal
result = translate_to_formal("Kanjo wameamua nini?", llm_function=my_llm)
# {"formal_query": "What has Nairobi City County resolved?"}

# Step 3: Re-inject Sheng into response
sheng_answer = translate_to_sheng(
    user_query="Kanjo wameamua nini?",
    formal_answer="Nairobi City County increased fees...",
    llm_function=my_llm
)
```

📖 **[Full Documentation](./SHENG_TRANSLATOR_GUIDE.md)**

---

### 3. Kenyanizer ([`kenyanizer.py`](./kenyanizer.py))

**Purpose:** Persona-specific system prompts for response synthesis

**Key Features:**
- ✅ Three specialized system prompts (<350 tokens each)
- ✅ Kenyan cultural analogies for wanjiku
- ✅ Strict citation formats for wakili
- ✅ Data-driven neutrality for mwanahabari
- ✅ Structured JSON output schemas
- ✅ Dynamic date injection (November 23, 2025)

**System Prompts:**

#### WANJIKU (Ordinary Citizen)
- Uses simple language and Kenyan cultural analogies
- Focuses on practical impact
- Mixes Swahili/Sheng naturally
- Example analogy: "Budget allocation is like dividing ugali at the dinner table"

#### WAKILI (Legal Professional)
- Requires exact citations: "Section 3(2)(b) of the Finance Act, 2023"
- Includes verbatim statutory provisions
- Formal legal terminology and analysis
- References Hansard with page numbers

#### MWANAHABARI (Journalist)
- Leads with data and statistics
- Provides comparative analysis and trends
- Maintains strict neutrality
- Flags data limitations transparently

**Quick Start:**
```python
from Module4_NiruAPI.agents.kenyanizer import (
    get_system_prompt,
    format_prompt_with_context
)

# Get persona-specific prompt
prompt = get_system_prompt("wanjiku")

# Format complete prompt with RAG context
full_prompt = format_prompt_with_context(
    query_type="wanjiku",
    user_query="Kanjo wameongeza parking fees?",
    retrieved_context="Nairobi County Assembly Resolution 42/2024..."
)
```

**JSON Output Schemas:**

**Wanjiku Schema:**
```json
{
  "answer": "Main answer in simple language",
  "key_points": ["3-5 bullet points"],
  "cultural_context": "Kenyan analogy if helpful",
  "next_steps": "What citizen can do next",
  "sources": ["Simple source names"]
}
```

**Wakili Schema:**
```json
{
  "answer": "Formal legal analysis",
  "legal_citations": ["Exact citations with sections"],
  "statutory_provisions": "Verbatim law text",
  "precedents": ["Case law or Hansard references"],
  "interpretation": "Legal analysis",
  "sources": ["Formal citations"]
}
```

**Mwanahabari Schema:**
```json
{
  "answer": "Objective summary",
  "statistics": {
    "key_figures": ["Numbers with context"],
    "trends": "Trend analysis",
    "comparisons": "Comparative data"
  },
  "timeline": ["Chronological events"],
  "sources": ["Data sources with dates"],
  "methodology_note": "Data limitations"
}
```

---

## 🔄 Complete Integration Example

Here's how all three modules work together:

```python
from Module4_NiruAPI.agents.intent_router import classify_query
from Module4_NiruAPI.agents.sheng_translator import translate_to_formal, translate_to_sheng
from Module4_NiruAPI.agents.kenyanizer import format_prompt_with_context

def process_kenyan_query(user_query: str, llm_func, rag_func):
    # Step 1: Classify intent
    intent = classify_query(user_query, llm_func)
    query_type = intent["query_type"]  # wanjiku/wakili/mwanahabari
    
    # Step 2: Translate Sheng if wanjiku
    if query_type == "wanjiku":
        translation = translate_to_formal(user_query, llm_func)
        search_query = translation["formal_query"]
        sheng_detected = translation["detected_sheng"]
    else:
        search_query = user_query
        sheng_detected = False
    
    # Step 3: RAG retrieval
    retrieved_context = rag_func(search_query)
    
    # Step 4: Generate response with persona-specific prompt
    synthesis_prompt = format_prompt_with_context(
        query_type=query_type,
        user_query=user_query,
        retrieved_context=retrieved_context
    )
    
    formal_response = llm_func(synthesis_prompt)
    
    # Step 5: Re-inject Sheng if needed
    if query_type == "wanjiku" and sheng_detected:
        final = translate_to_sheng(user_query, formal_response, llm_func)
        return final["sheng_response"]
    else:
        return formal_response
```

📖 **[See Full Integration Example](./integration_example.py)**

---

## 📊 Module Statistics

| Module | Lines of Code | Key Functions | Dictionary Size |
|--------|---------------|---------------|-----------------|
| Intent Router | ~650 | 8 | 15 examples |
| Sheng Translator | ~850 | 12 | 120+ terms |
| Kenyanizer | ~550 | 6 | 3 prompts |
| **Total** | **~2,050** | **26** | **135+ items** |

---

## 🚀 Quick Installation & Testing

### 1. Run All Tests

```bash
cd Module4_NiruAPI/agents

# Test intent router
python intent_router.py

# Test Sheng translator
python sheng_translator.py

# Test Kenyanizer
python kenyanizer.py

# Test full integration
python integration_example.py
```

### 2. Validate Examples

All test files include validation:
- ✅ Intent router: 15/15 examples pass schema validation
- ✅ Sheng translator: 120+ terms in dictionary
- ✅ Kenyanizer: 3 prompts all under 350 tokens

---

## 🎯 Use Cases & Examples

### Example 1: Ordinary Citizen (Wanjiku)

**Input:** `"Kanjo wameamua nini kuhusu parking doh?"`

**Flow:**
1. **Intent:** wanjiku (92% confidence, sheng detected)
2. **Translation:** "What has Nairobi City County resolved regarding parking fees?"
3. **RAG Search:** Retrieves County Assembly Resolution 42/2024
4. **Synthesis:** Uses WANJIKU system prompt with cultural analogies
5. **Output:**
   ```json
   {
     "answer": "Kanjo wameongeza parking fees kwa town centre from KES 200 to KES 300 per day, starting March 1, 2024.",
     "key_points": [
       "Old fee: KES 200, New fee: KES 300 (50% increase)",
       "CBD only - estates are not affected",
       "Money goes to road improvements",
       "Started March 1, 2024"
     ],
     "cultural_context": "Think of it like your landlord increasing rent - County Assembly had to approve it first.",
     "next_steps": "Pay at kanjo meters or M-Pesa. Keep receipt to avoid clamping.",
     "sources": ["County Assembly Resolution 42/2024"]
   }
   ```

### Example 2: Legal Professional (Wakili)

**Input:** `"What does Section 3(b) of the Finance Act 2023 say?"`

**Flow:**
1. **Intent:** wakili (98% confidence)
2. **No translation needed** (formal query)
3. **RAG Search:** Retrieves Finance Act 2023 full text
4. **Synthesis:** Uses WAKILI system prompt with citations
5. **Output:**
   ```json
   {
     "answer": "Section 3(b) of the Finance Act, 2023 amends the VAT Act by introducing 16% VAT on digital services from non-residents.",
     "legal_citations": [
       "Finance Act, 2023, Section 3(b)",
       "Value Added Tax Act, 2013 (as amended)"
     ],
     "statutory_provisions": "Section 3(b) states: 'The VAT Act is amended in section 8...'",
     "precedents": ["National Assembly Hansard, March 15, 2023, pg. 42-67"],
     "interpretation": "Extends VAT to non-resident digital service providers...",
     "sources": ["Kenya Gazette No. 123, 2023"]
   }
   ```

### Example 3: Journalist (Mwanahabari)

**Input:** `"MP attendance Q3 2024?"`

**Flow:**
1. **Intent:** mwanahabari (97% confidence)
2. **No translation needed**
3. **RAG Search:** Retrieves parliamentary attendance data
4. **Synthesis:** Uses MWANAHABARI system prompt with stats
5. **Output:**
   ```json
   {
     "answer": "Average MP attendance in Q3 2024 was 67% (223 of 349 MPs on average).",
     "statistics": {
       "key_figures": [
         "Average: 67% (223/349 MPs)",
         "Highest: 95%, Lowest: 34%",
         "Finance Committee: 72%"
       ],
       "trends": "Up from 58% in Q2 2024",
       "comparisons": "Higher than 2023 average (62%)"
     },
     "timeline": ["July: 68%", "Aug: 71%", "Sep: 76%"],
     "sources": ["National Assembly Journal Q3 2024"],
     "methodology_note": "Based on roll call, not late arrivals"
   }
   ```

---

## 🛠️ API Integration

### FastAPI Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from Module4_NiruAPI.agents import (
    classify_query,
    translate_to_formal,
    translate_to_sheng,
    get_system_prompt
)

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/amaniquery")
async def process_query(request: QueryRequest):
    # 1. Classify
    intent = classify_query(request.query, llm_function)
    
    # 2. Translate if needed
    if intent["query_type"] == "wanjiku":
        formal_query = translate_to_formal(request.query, llm_function)
    else:
        formal_query = request.query
    
    # 3. RAG search
    context = rag_search(formal_query)
    
    # 4. Generate response
    prompt = get_system_prompt(intent["query_type"])
    answer = llm_function(f"{prompt}\n\nContext: {context}\n\nQuery: {request.query}")
    
    return {"answer": answer, "intent": intent["query_type"]}
```

---

## ✅ Production Checklist

- [ ] Intent router configured with Gemini/Groq API
- [ ] Sheng dictionary customized for your use case
- [ ] All three system prompts reviewed and approved
- [ ] JSON schema validation enabled
- [ ] Logging added for classification metrics
- [ ] Error handling for LLM failures
- [ ] Caching enabled for common queries
- [ ] Response time optimized (<2s total)

---

## 📚 File Structure

```
Module4_NiruAPI/agents/
├── intent_router.py              # Intent classification (650 lines)
├── INTENT_ROUTER_GUIDE.md        # Documentation (600 lines)
├── test_intent_router.py         # Tests & demos (300 lines)
├── sheng_translator.py           # Sheng ↔ Formal translation (850 lines)
├── SHENG_TRANSLATOR_GUIDE.md     # Documentation (700 lines)
├── kenyanizer.py                 # System prompts (550 lines)
├── integration_example.py        # Full pipeline example (400 lines)
└── README.md                     # This file
```

**Total:** ~4,050 lines of code and documentation

---

## 🎓 Key Concepts

### Intent Classification
Determines *who* is asking → Routes to appropriate response style

### Sheng Translation
Understands *how* they're asking → Normalizes for search, preserves for response

### Kenyanization
Formats *what* we answer → Persona-specific tone and structure

---

## 🇰🇪 Why This Matters

**AmaniQuery v2.0** makes Kenyan civic information accessible to **everyone**:

- **Wanjiku** gets answers in her language with relatable analogies
- **Wakili** gets precise legal citations for court preparation
- **Mwanahabari** gets data-driven facts for investigative journalism

**Result:** Democracy thrives when information is accessible to all, not just the elite.

---

**Built with 🇰🇪 for Kenya**  
*AmaniQuery Engine v2.0 - Powered by Gemini*

For questions and contributions, see [CONTRIBUTING.md](../../../CONTRIBUTING.md)
