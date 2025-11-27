from qdrant_client import QdrantClient
from qdrant_client.http import models
from ..config import settings

class QdrantStorage:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.client.get_collection(settings.QDRANT_COLLECTION)
        except:
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )

    def upsert(self, doc_id: str, vector: list, payload: dict):
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[
                models.PointStruct(
                    id=str(doc_id),
                    vector=vector,
                    payload=payload
                )
            ]
        )

qdrant_storage = QdrantStorage()
