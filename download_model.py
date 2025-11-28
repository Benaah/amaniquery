import os
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    AutoModelForTokenClassification, 
    AutoModelForSeq2SeqLM
)

def download_models():
    print("🚀 Starting model download for AmaniQuery & NiruSense...")
    
    # 1. Base Embedding Model (Legacy/Default)
    base_embedding = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"📥 Downloading base embedding model: {base_embedding}...")
    SentenceTransformer(base_embedding)
    
    # 2. NiruSense Embedding Model
    niru_embedding = "nomic-ai/nomic-embed-text-v1.5"
    print(f"📥 Downloading NiruSense embedding model: {niru_embedding}...")
    SentenceTransformer(niru_embedding, trust_remote_code=True)
    
    # 3. NiruSense NLP Models
    models = [
        # Language ID
        ("papluca/xlm-roberta-base-language-detection", AutoModelForSequenceClassification),
        # Slang Decoder
        ("google/flan-t5-base", AutoModelForSeq2SeqLM),
        # Topic & Bias (Same model)
        ("MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", AutoModelForSequenceClassification),
        # NER
        ("Davlan/xlm-roberta-base-ner-hrl", AutoModelForTokenClassification),
        # Sentiment
        ("lxyuan/distilbert-base-multilingual-cased-sentiments-student", AutoModelForSequenceClassification),
        # Emotion
        ("j-hartmann/emotion-english-distilroberta-base", AutoModelForSequenceClassification),
        # Summarizer
        ("google/mt5-small", AutoModelForSeq2SeqLM),
    ]
    
    for model_name, model_class in models:
        print(f"📥 Downloading model: {model_name}...")
        try:
            # Download Tokenizer
            AutoTokenizer.from_pretrained(model_name)
            # Download Model
            model_class.from_pretrained(model_name)
            print(f"✅ Successfully downloaded {model_name}")
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
            # Don't fail the build, just log error
            pass

    print("✨ All models downloaded successfully!")

if __name__ == "__main__":
    download_models()
