# AmaniQuery Legal Research & Report Generation

AmaniQuery now includes advanced legal research and report generation capabilities powered by Google Gemini AI, specifically designed for analyzing legal queries and gathering information about Kenya's laws.

## Overview

The research module enables comprehensive analysis of legal queries and information gathering from Kenya's legal system. It provides tools for:

- **Legal Query Analysis**: Deep analysis of legal questions about Kenyan laws
- **Legal Report Generation**: Structured reports on legal matters with applicable laws and guidance
- **Legal Research**: Comprehensive research on specific legal topics and questions
- **Compliance Reports**: Legal compliance assessment and regulatory guidance
- **Constitutional Law Reports**: Specialized analysis of constitutional matters

## Setup

### Prerequisites

1. **Gemini API Key**: Obtain a Google AI API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Environment Configuration**: Add your API key to the `.env` file:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. **Dependencies**: Install the required package:
   ```bash
   pip install google-generativeai==0.3.2
   ```

## API Endpoints

### Research Endpoints

#### `POST /research/analyze-legal-query`
Analyzes a legal query about Kenya's laws and provides comprehensive information.

**Parameters:**
- `query` (string): The legal question or query to analyze
- `context` (string, optional): Additional context about the query (JSON string)

**Response:**
```json
{
  "analysis": {
    "query_interpretation": "...",
    "applicable_laws": "...",
    "legal_analysis": "...",
    "practical_guidance": "...",
    "additional_considerations": "..."
  },
  "timestamp": "2025-11-11T...",
  "model_used": "gemini-1.5-pro",
  "original_query": "...",
  "context_provided": true
}
```

#### `POST /research/generate-legal-report`
Generates comprehensive legal reports based on query analysis results.

**Parameters:**
- `analysis_results` (string): JSON string of analysis results from /research/analyze-legal-query
- `report_focus` (string): Type of legal focus (comprehensive, constitutional, criminal, civil, administrative)

**Response:**
```json
{
  "report": {
    "title": "Legal Report - Comprehensive Analysis",
    "content": "Full report content...",
    "focus_area": "comprehensive",
    "generated_at": "2025-11-11T..."
  },
  "metadata": {
    "sections": ["Query Summary", "Applicable Law", ...],
    "word_count": 2500
  }
}
```

#### `POST /research/legal-research`
Conducts legal research on specific topics related to Kenya's laws.

**Parameters:**
- `legal_topics` (string): JSON array of legal topics to research
- `research_questions` (string): JSON array of specific research questions

**Response:**
```json
{
  "legal_research": {
    "findings": "Detailed research findings...",
    "topics_researched": ["Tax compliance", "Consumer protection", ...],
    "questions_addressed": ["What are the key legal requirements...", ...],
    "generated_at": "2025-11-11T..."
  },
  "metadata": {
    "topic_count": 5,
    "question_count": 5,
    "findings_length": 3500
  }
}
```

### Report Endpoints

#### `POST /reports/legal-query`
Generates a comprehensive legal query report.

**Parameters:**
- `query_analysis` (string): JSON string containing legal query analysis results

#### `POST /reports/legal-research`
Generates a legal research report with analysis of Kenyan laws.

#### `POST /reports/constitutional-law`
Generates a specialized constitutional law report.

#### `POST /reports/compliance`
Generates a legal compliance assessment report.

#### `GET /research/status`
Checks the availability of legal research and report generation capabilities.

## Usage Examples

### Basic Legal Research Workflow

```python
import requests
import json

API_BASE_URL = "http://localhost:8000"

# 1. Analyze a legal query
legal_query = "What are my rights as a tenant in Kenya?"
response = requests.post(f"{API_BASE_URL}/research/analyze-legal-query",
                        data={"query": legal_query})
analysis = response.json()

# 2. Generate comprehensive legal report
response = requests.post(f"{API_BASE_URL}/research/generate-legal-report",
                        data={
                            "analysis_results": json.dumps(analysis),
                            "report_focus": "civil"
                        })
report = response.json()

# 3. Conduct legal research on property law
topics = ["Tenant rights in Kenya", "Landlord obligations", "Rent control laws"]
questions = ["What protections do tenants have?", "How can disputes be resolved?"]
response = requests.post(f"{API_BASE_URL}/research/legal-research",
                        data={
                            "legal_topics": json.dumps(topics),
                            "research_questions": json.dumps(questions)
                        })
```

### Legal Query Analysis Example

The system can analyze complex legal queries such as:

- Tax compliance obligations for small businesses
- Employment law rights and obligations
- Consumer protection under Kenyan law
- Constitutional rights and their enforcement
- Property rights and land law matters
- Criminal law procedures and rights

## Research Applications

### Legal Information Gathering

1. **Citizen Legal Education**: Help individuals understand their rights and obligations
2. **Business Compliance**: Assist businesses in understanding regulatory requirements
3. **Legal Research Support**: Provide comprehensive legal research for professionals
4. **Policy Analysis**: Support analysis of legal implications of policies and laws
5. **Dispute Resolution**: Guide users through legal procedures and alternatives

### Legal Areas Covered

- **Constitutional Law**: Fundamental rights, constitutional interpretation, judicial review
- **Criminal Law**: Offenses, penalties, criminal procedure, rights of accused
- **Civil Law**: Contracts, torts, property law, family law, commercial law
- **Administrative Law**: Government regulations, licensing, administrative procedures
- **Tax Law**: Income tax, VAT, tax procedures, taxpayer rights
- **Employment Law**: Labor rights, workplace regulations, employment contracts
- **Environmental Law**: Environmental protection, compliance requirements
- **Consumer Protection**: Consumer rights, unfair trade practices

## Output Formats

### Analysis Results
- **JSON Format**: Structured data for programmatic processing
- **Text Reports**: Human-readable comprehensive legal reports
- **Metadata**: Generation timestamps, model information, and statistics

### Report Types

1. **Legal Query Reports**: Detailed analysis of specific legal questions
2. **Legal Research Reports**: Comprehensive research on legal topics
3. **Constitutional Law Reports**: Specialized constitutional analysis
4. **Compliance Reports**: Regulatory compliance assessment and guidance
5. **Technical Audit Reports**: System performance and technical analysis
6. **Impact Assessment Reports**: Social and economic impact evaluation

## Best Practices

### Legal Query Analysis
- Provide clear, specific legal questions
- Include relevant context (location, user type, urgency)
- Specify the legal area of interest when possible
- Use plain language while being specific about legal concerns

### Report Generation
- Choose appropriate legal focus based on the query type
- Include all relevant context for accurate legal analysis
- Review generated reports for completeness and accuracy
- Consult legal professionals for complex or high-stakes matters

### Research Design
- Define clear legal research objectives
- Include specific legal topics and jurisdictions
- Focus questions on practical legal implications
- Consider both substantive law and procedural requirements

## Integration with Existing Features

The legal research module integrates seamlessly with AmaniQuery's existing capabilities:

- **RAG Pipeline**: Uses Gemini alongside existing AI models for enhanced legal analysis
- **Vector Store**: Leverages existing legal document embeddings for comprehensive research
- **Legal Database**: Access to comprehensive Kenyan legal materials
- **SMS Pipeline**: Mobile access to legal information and guidance
- **Constitutional Alignment**: Integration with constitutional compliance checking

## Legal Disclaimer

**Important**: The legal research and report generation capabilities are designed to provide general legal information and guidance based on Kenya's laws. The generated content:

- Is not a substitute for professional legal advice
- Should not be relied upon as the sole basis for legal decisions
- May not reflect the most current legal developments
- Should be verified with qualified legal professionals for specific situations

Users are strongly encouraged to consult with qualified legal practitioners for advice on specific legal matters, especially those involving significant rights, obligations, or potential legal consequences.

## Support

For questions about the legal research and report generation features:

1. Check the `/research/status` endpoint for system availability
2. Review the example script in `examples/example_research_reports.py`
3. Ensure proper Gemini API key configuration
4. Monitor API response times and error handling

The legal research capabilities are designed to support informed decision-making and promote access to legal information in Kenya's legal system.</content>
<parameter name="filePath">c:\Users\barne\OneDrive\Desktop\AmaniQuery\docs\RESEARCH_REPORTS.md