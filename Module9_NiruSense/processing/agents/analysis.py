from .base import BaseAgent
import random

class TopicClassifier(BaseAgent):
    def __init__(self):
        super().__init__("topic_classifier")
        self.topics = ["Politics", "Economy", "Sports", "Social", "Technology"]

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"topics": [random.choice(self.topics)], "scores": [0.9]}

class EntityExtractor(BaseAgent):
    def __init__(self):
        super().__init__("entity_extractor")

    def process(self, text: str, metadata: dict = None) -> dict:
        entities = []
        if "Ruto" in text:
            entities.append({"text": "Ruto", "label": "PERSON"})
        if "Nairobi" in text:
            entities.append({"text": "Nairobi", "label": "LOC"})
        return {"entities": entities}

class SentimentAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__("sentiment_analyzer")

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"sentiment": "neutral", "score": 0.5}

class EmotionDetector(BaseAgent):
    def __init__(self):
        super().__init__("emotion_detector")

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"emotion": "anticipation", "score": 0.7}
