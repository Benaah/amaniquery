from .base import BaseAgent

class BiasDetector(BaseAgent):
    def __init__(self):
        super().__init__("bias_detector")

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"bias_level": "low", "flags": []}

class Summarizer(BaseAgent):
    def __init__(self):
        super().__init__("summarizer")

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"summary": text[:100] + "..."}

class QualityScorer(BaseAgent):
    def __init__(self):
        super().__init__("quality_scorer")

    def process(self, text: str, metadata: dict = None) -> dict:
        return {"quality_score": 8.5, "reasoning": "Good content"}
