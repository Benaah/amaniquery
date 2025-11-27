Technical Design Document: Module9_NiruSense
Project: Sauti-Sense (AmaniQuery) Module: Module9_NiruSense Role: Lead Systems Architect Date: November 27, 2025 Status: Final Draft

1. High-Level Architecture
NiruSense operates as an asynchronous, event-driven microservices layer sitting between the raw data ingestion (NiruSpider) and the vector search engine (NiruDB/Qdrant).

The architecture follows a Pipeline-Filter pattern:

Ingestion: Raw text is pushed from NiruSpider into a durable message queue (Local Redis).
Orchestration: The NiruSense Orchestrator picks up jobs and dispatches them to specialized agents.
Processing (The 9 Agents): Parallel and sequential execution of specialized NLP tasks. Some agents (e.g., SlangDecoder) must run before others (e.g., SentimentAnalyzer).
Vectorization: The fully enriched payload is embedded.
Storage: Structured data goes to PostgreSQL; Vectors go to Qdrant.
This decoupling ensures that heavy NLP inference does not block the scraping speed and allows for independent scaling of specific agents (e.g., scaling SentimentAnalyzer more than EntityExtractor).

2. Exact Data Flow
Raw Scrape: NiruSpider scrapes a URL. Output: {"url": "...", "raw_html": "...", "timestamp": "..."}.
Normalization: NiruParser cleans HTML to text. Output: {"text": "Wasee, form ni gani leo?", "metadata": {...}}.
Queue Injection: JSON payload pushed to niru_processing_queue.
Agent Pipeline:
Stage 1 (Pre-processing): LanguageIdentifier -> SlangDecoder.
Stage 2 (Core Analysis): TopicClassifier || EntityExtractor || SentimentAnalyzer || EmotionDetector.
Stage 3 (High-Level): BiasDetector || Summarizer || QualityScorer.
Aggregation: Results merged into a single EnrichedDocument object.
Embedding: EnrichedDocument.text + EnrichedDocument.summary -> Vector (768d).
Persistence:
PostgreSQL: Insert into articles (content) and analysis_results (agent outputs).
Qdrant: Upsert point with ID, Vector, and Payload (full metadata + sentiment/topic tags).
3. Component Responsibilities: The 9 Specialized Agents
Agent Name	Responsibility	Input	Output
1. LanguageIdentifier	Detects if text is English, Swahili, or Sheng (Code-mixed).	Raw Text	{"lang": "sheng", "conf": 0.95}
2. SlangDecoder	Normalizes Sheng/slang to standard English/Swahili for better downstream analysis.	Raw Text	{"normalized_text": "Guys, what is the plan today?", "mappings": {...}}
3. TopicClassifier	Categorizes text into 15+ Kenyan-specific topics (Politics, Economy, Maandamano, Sports, etc.).	Normalized Text	{"topics": ["Social", "Leisure"], "scores": [...]}
4. EntityExtractor	Identifies Kenyan politicians, counties, organizations, and events.	Normalized Text	{"entities": [{"text": "Ruto", "label": "PERSON"}, {"text": "Nairobi", "label": "LOC"}]}
5. SentimentAnalyzer	Determines sentiment polarity (Positive, Negative, Neutral) considering Kenyan context.	Normalized Text	{"sentiment": "neutral", "score": 0.8}
6. EmotionDetector	Detects fine-grained emotions (Anger, Joy, Fear, Disgust, Anticipation).	Normalized Text	{"emotion": "anticipation", "score": 0.7}
7. BiasDetector	Flags potential tribalism, hate speech, or political bias.	Normalized Text	{"bias_level": "low", "flags": []}
8. Summarizer	Generates a concise 2-3 sentence summary of the content.	Normalized Text	{"summary": "..."}
9. QualityScorer	Calculates a composite score of information density and trustworthiness.	Metadata + Text	{"quality_score": 8.5, "reasoning": "..."}
4. Exact Model Choices (Locked for 2025–2026)
We prioritize multilingual efficiency and African language support.

Embeddings: nomic-ai/nomic-embed-text-v1.5

Reason: Matryoshka embeddings (adjustable size), 8192 context length, outperforms OpenAI text-embedding-3-small.
Type: Sentence Transformer.
Language & Sentiment (Base Model): Davlan/afro-xlmr-mini (fine-tuned)

Reason: Extremely fast, supports Swahili, Hausa, Yoruba, etc. We will fine-tune heads for Sentiment and Language ID.
Fallback: Davlan/afro-xlmr-large-75L if accuracy drops.
Topic & Zero-Shot: MoritzLaurer/mDeBERTa-v3-base-mnli-xnli

Reason: Best-in-class multilingual zero-shot classification.
NER (Entities): Davlan/xlm-roberta-base-ner-hrl

Reason: Strong performance on African languages NER.
Summarization: google/mt5-small (fine-tuned on Swahili/English news)

Reason: Efficient text-to-text generation.
Slang/Sheng: Custom Fine-tuned meta-llama/Llama-3.2-3B-Instruct (Quantized)

Reason: Sheng requires generative understanding. A small, quantized LLM is necessary for "translation".
5. Storage Schema
PostgreSQL (Relational Source of Truth)
Table: documents

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    raw_content TEXT,
    normalized_content TEXT,
    source_domain VARCHAR(255),
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
Table: analysis_results

CREATE TABLE analysis_results (
    document_id UUID REFERENCES documents(id),
    agent_id VARCHAR(50), -- e.g., 'sentiment_analyzer'
    result_json JSONB,    -- Stores flexible output
    model_version VARCHAR(50),
    execution_time_ms INT,
    PRIMARY KEY (document_id, agent_id)
);
Qdrant (Vector Payload)
Collection: amani_knowledge_base

Vector: 768 dimensions (Nomic).
Payload:
{
  "document_id": "uuid...",
  "text": "Wasee, form ni gani...",
  "summary": "Users discussing weekend plans...",
  "topics": ["Social", "Leisure"],
  "sentiment": "neutral",
  "entities": ["Nairobi"],
  "quality_score": 8.5,
  "timestamp": 1732687200
}
6. Cost Envelope & Hosting
Constraint: < $30/month.

Component	Service	Tier/Cost	Notes
Compute (API/Agents)	Hugging Face Spaces	$0 (Free)	Use CPU Basic for lightweight agents.
Compute (Heavy)	Google Colab / Kaggle	$0 (Free)	Scheduled batch jobs for Llama-3 (Sheng) if needed.
Vector DB	Qdrant Cloud	$0 (Free)	1GB Cluster (approx 1M vectors).
Relational DB	Neon.tech	$0 (Free)	Serverless Postgres (Free Tier).
Queue	Local Redis	$0 (Free)	Self-hosted instance.
Proxy/Scraper	Nitty / Custom Scripts	$0	Using free tools/libraries; no commercial APIs.
Total Estimated		$0 / month	Completely free stack.
7. Success Metrics
Latency: End-to-end processing (Ingest to Vector) < 5 seconds for standard articles.
Sheng Accuracy: > 85% correct identification and translation of Sheng phrases.
Sentiment F1-Score: > 0.80 on code-mixed Kenyan tweets/comments.
Entity Recall: > 0.90 for major Kenyan political figures.
Throughput: Capable of processing 10,000 documents/day on free tier infrastructure.
8. Risk Registry
Risk ID	Risk Description	Probability	Impact	Mitigation Strategy
R-01	Sheng Evolution: Slang changes rapidly, making the decoder obsolete.	High	Medium	Continuous fine-tuning of Llama-3 adapter with weekly scraped social data.
R-02	Model Drift: Sentiment models failing on new political context.	Medium	High	Monthly re-evaluation against a "Golden Set" of labeled data.
R-03	Resource Starvation: Free tier limits (RAM/CPU) causing crashes.	High	High	Implement aggressive error handling, retries, and batch processing to stay within limits.
R-04	Data Poisoning: Ingesting fake news/spam.	Medium	High	The QualityScorer agent specifically down-ranks low-trust domains.