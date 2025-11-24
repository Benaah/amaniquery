from sentence_transformers import SentenceTransformer
import os

def download_model():
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Downloading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    print("Model downloaded successfully.")

if __name__ == "__main__":
    download_model()
