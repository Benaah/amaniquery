"""
Module 2: NiruParser - ETL & Embedding Pipeline
"""

__version__ = "1.0.0"

from .pipeline import ProcessingPipeline
from .config import Config

__all__ = ["ProcessingPipeline", "Config"]
