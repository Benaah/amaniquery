# Constitutional Alignment Module

## Overview

The Constitutional Alignment Module is AmaniQuery's **core unique value proposition**. It performs sophisticated dual-retrieval RAG analysis to compare Bills/Acts with the Kenyan Constitution, providing structured comparative analysis that highlights areas of alignment, overlap, and potential constitutional questions.

## 🎯 What Makes This Special

This is **not** a simple "ask the LLM if it's constitutional" approach. Instead, it's a multi-step intelligent workflow that:

1. **Deconstructs** user queries to identify Bills and constitutional concepts
2. **Retrieves separately** from Bill sources and Constitution sources
3. **Structures the prompt** to force comparative analysis
4. **Generates objective analysis** with proper citations, not legal opinions

## 🏗️ Architecture

```
User Query
    ↓
Query Analyzer (identifies Bill + concepts)
    ↓
    ├─→ Bill Retrieval (filter: category='Bill')
    │   └─→ Top 3 Bill chunks
    └─→ Constitution Retrieval (filter: category='Constitution')
        └─→ Top 3 Constitution chunks
    ↓
Structured Prompt Construction
    ↓
LLM Analysis (Moonshot AI)
    ↓
Structured Response with Citations
```

## 📋 Prerequisites

### Enhanced Metadata (Module 2)

The alignment analysis depends on **granular metadata** extracted during processing:

#### Constitution Chunks
```json
{
  "text": "Every person has the right to accessible and adequate housing...",
  "category": "Constitution",
  "document_type": "Constitution",
  "article_number": "43",
  "article_title": "Economic and social rights",
  "clause": "1(b)",
  "legal_subjects": ["economic_rights", "housing", "rights"]
}
```

#### Bill/Act Chunks
```json
{
  "text": "A mandatory housing levy of 1.5% shall be imposed...",
  "category": "Bill",
  "document_type": "Bill",
  "bill_title": "The Finance Bill, 2025",
  "clause_number": "16",
  "subject": "Housing Levy",
  "year": "2025",
  "legal_subjects": ["taxation", "housing", "finance"]
}
```

### Legal Metadata Enricher

Use the `LegalMetadataEnricher` in Module 2 to automatically extract this metadata:

```python
from Module2_NiruParser.enrichers import LegalMetadataEnricher

enricher = LegalMetadataEnricher()

# Auto-detect and enrich
chunk = enricher.auto_enrich(chunk)

# Or specific enrichment
constitution_chunk = enricher.enrich_constitution(chunk)
bill_chunk = enricher.enrich_bill(chunk)
```

## 🔧 Components

### 1. Query Analyzer

Extracts key information from natural language queries:

```python
from Module4_NiruAPI.alignment_pipeline import QueryAnalyzer

analyzer = QueryAnalyzer()
result = analyzer.analyze(
    "How does the Finance Bill housing levy align with the constitution?"
)

# Result:
{
    "bill_name": "Finance Bill",
    "legal_concepts": ["housing", "taxation", "economic_rights"],
    "keywords": ["housing", "levy", "align", "constitution"],
    "analysis_type": "alignment"
}
```

### 2. Dual-Retrieval Engine

Performs two parallel vector searches:

```python
# Branch 1: Bill context
bill_chunks = vector_store.search(
    query_text="Finance Bill housing levy",
    top_k=3,
    filter_dict={"category": "Bill"}
)

# Branch 2: Constitution context
constitution_chunks = vector_store.search(
    query_text="housing taxation economic rights",
    top_k=3,
    filter_dict={"category": "Constitution"}
)
```

### 3. Prompt Constructor

Creates structured prompts that force comparative analysis:

```
CONTEXT FROM BILL:
[Clause 16 from Finance Bill: "A mandatory housing levy..."]
[Clause 17 from Finance Bill: "Funds shall be used..."]

CONTEXT FROM CONSTITUTION:
[Article 43(1)(b): "Right to accessible housing..."]
[Article 40: "Right to property..."]

YOUR ANALYSIS:
1. The Bill's Proposal: [summarize with citations]
2. Relevant Constitutional Provisions: [list with citations]
3. Alignment Analysis: [compare objectively]
4. Key Considerations: [highlight important points]
```

## 📡 API Endpoints

### POST /alignment-check

Full constitutional alignment analysis.

**Request:**
```json
{
  "query": "How does the Finance Bill housing levy align with the constitution?",
  "bill_top_k": 3,
  "constitution_top_k": 3,
  "temperature": 0.3,
  "max_tokens": 2000
}
```

**Response:**
```json
{
  "analysis": "Based on the provided documents...\n\n**1. The Bill's Proposal:**\nThe Finance Bill, 2025, proposes a mandatory housing levy...[Source: Finance Bill, Clause 16]\n\n**2. Relevant Constitutional Provisions:**\nArticle 43(1)(b) guarantees...[Source: Constitution, Art. 43]\n\n**3. Alignment Analysis:**\nThe bill's stated aim appears to align with...",
  
  "bill_context": [
    {
      "text": "A mandatory housing levy of 1.5%...",
      "clause_number": "16",
      "subject": "Housing Levy",
      "title": "The Finance Bill, 2025"
    }
  ],
  
  "constitution_context": [
    {
      "text": "Every person has the right to accessible and adequate housing...",
      "article_number": "43",
      "article_title": "Economic and social rights",
      "clause": "1(b)"
    }
  ],
  
  "metadata": {
    "bill_name": "Finance Bill",
    "legal_concepts": ["housing", "taxation", "economic_rights"],
    "analysis_type": "alignment",
    "bill_chunks_count": 3,
    "constitution_chunks_count": 3
  },
  
  "query_time": 2.34
}
```

### POST /alignment-quick-check

Simplified endpoint for quick checks.

**Request:**
```
POST /alignment-quick-check?bill_name=Finance%20Bill%202025&constitutional_topic=taxation
```

**Response:** Same structure as `/alignment-check`

## 💻 Usage Examples

### Python

```python
import requests

# Full alignment analysis
response = requests.post(
    "http://localhost:8000/alignment-check",
    json={
        "query": "Does the Data Protection Act comply with constitutional privacy rights?",
        "bill_top_k": 4,
        "constitution_top_k": 4,
        "temperature": 0.3
    }
)

result = response.json()
print(result["analysis"])

# Quick check
response = requests.post(
    "http://localhost:8000/alignment-quick-check",
    params={
        "bill_name": "Finance Bill 2025",
        "constitutional_topic": "taxation"
    }
)
```

### cURL

```bash
# Alignment analysis
curl -X POST "http://localhost:8000/alignment-check" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does the housing levy align with the constitution?",
    "bill_top_k": 3,
    "constitution_top_k": 3
  }'

# Quick check
curl -X POST "http://localhost:8000/alignment-quick-check?bill_name=Finance%20Bill%202025&constitutional_topic=housing"
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/alignment-check', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Finance Bill taxation measures and constitutional property rights',
    bill_top_k: 3,
    constitution_top_k: 3,
    temperature: 0.3
  })
});

const result = await response.json();
console.log(result.analysis);
```

## 🎓 Example Queries

### ✅ Good Queries (Clear Bill + Concept)

- "How does the Finance Bill 2025 housing levy align with the constitution?"
- "Does the Data Protection Act comply with constitutional privacy rights?"
- "What constitutional issues arise from the new taxation in the Finance Bill?"
- "How does the Healthcare Bill align with the right to health in the constitution?"

### ❌ Poor Queries (Too Vague)

- "Is this bill constitutional?"  (Which bill?)
- "Constitution and housing"  (No bill specified)
- "Finance Bill"  (No constitutional concept)

## 🔍 How It Differs from Regular RAG

| Feature | Regular `/query` | Alignment `/alignment-check` |
|---------|-----------------|------------------------------|
| **Retrieval** | Single search, mixed sources | Dual search: Bill + Constitution |
| **Filtering** | Optional category filter | Mandatory: Bill vs Constitution |
| **Prompt** | General Q&A | Structured comparative analysis |
| **Output** | Answer with sources | Sectioned analysis with citations |
| **Use Case** | General questions | Constitutional compliance review |
| **Temperature** | 0.7 (default) | 0.3 (more factual) |

## ⚖️ Important Legal Disclaimer

This tool provides **factual analysis**, NOT legal opinions:

- ✅ Highlights alignment and tensions
- ✅ Provides structured comparison
- ✅ Cites specific articles and clauses
- ❌ Does NOT declare something "constitutional" or "unconstitutional"
- ❌ Does NOT replace legal expert review
- ❌ Does NOT provide court-admissible opinions

**Always consult qualified legal professionals for official interpretations.**

## 🛠️ Advanced Usage

### Programmatic Use

```python
from Module4_NiruAPI.alignment_pipeline import ConstitutionalAlignmentPipeline
from Module3_NiruDB import VectorStore
from Module4_NiruAPI import RAGPipeline

# Initialize
vector_store = VectorStore()
rag_pipeline = RAGPipeline(vector_store=vector_store)
alignment_pipeline = ConstitutionalAlignmentPipeline(
    vector_store=vector_store,
    rag_pipeline=rag_pipeline
)

# Analyze
result = alignment_pipeline.analyze_alignment(
    query="Finance Bill housing levy constitutional alignment",
    bill_top_k=5,
    constitution_top_k=5
)

print(result["analysis"])
```

### Custom Query Analysis

```python
from Module4_NiruAPI.alignment_pipeline import QueryAnalyzer

analyzer = QueryAnalyzer()
analysis = analyzer.analyze("Your query here")

print(f"Bill: {analysis['bill_name']}")
print(f"Concepts: {analysis['legal_concepts']}")
print(f"Type: {analysis['analysis_type']}")
```

## 📊 Performance Tips

1. **Optimal Chunk Counts:**
   - `bill_top_k: 3-5` (Bills are focused)
   - `constitution_top_k: 3-5` (Constitution is structured)

2. **Temperature:**
   - Use `0.2-0.3` for factual analysis
   - Use `0.4-0.5` for more nuanced interpretation

3. **Query Quality:**
   - Mention the specific bill name
   - Include the constitutional concept (rights, taxation, etc.)
   - Be specific about what you want to compare

## 🚀 Future Enhancements

- [ ] Multi-bill comparison
- [ ] Historical precedent integration
- [ ] Conflict severity scoring
- [ ] Visual alignment matrix
- [ ] Export to legal brief format
- [ ] Integration with Kenyan case law

## 📚 See Also

- [Main README](../README.md)
- [API Documentation](http://localhost:8000/docs)
- [Example Script](../examples/example_alignment.py)
- [Legal Metadata Enricher](../Module2_NiruParser/enrichers/legal_metadata_enricher.py)
