from .base import BaseAgent

class LanguageIdentifier(BaseAgent):
    def __init__(self):
        super().__init__("language_identifier")

    def process(self, text: str, metadata: dict = None) -> dict:
        # Mock logic
        if "wasee" in text.lower() or "form" in text.lower():
            return {"lang": "sheng", "conf": 0.95}
        return {"lang": "en", "conf": 0.99}

class SlangDecoder(BaseAgent):
    def __init__(self):
        super().__init__("slang_decoder")

    def process(self, text: str, metadata: dict = None) -> dict:
        # Mock logic
        normalized = text.replace("wasee", "guys").replace("form ni gani", "what is the plan")
        return {"normalized_text": normalized, "mappings": {"wasee": "guys"}}
