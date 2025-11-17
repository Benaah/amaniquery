"""
Agentic AI System - 7-Layer Architecture
"""
from typing import Optional, Any

__all__ = [
    "AgenticResearchSystem",
]

# Lazy imports to avoid circular dependencies
_agentic_system: Optional[Any] = None

def get_agentic_research_system():
    """Get or create the agentic research system instance"""
    global _agentic_system
    if _agentic_system is None:
        from .state_machine import AgenticResearchSystem
        _agentic_system = AgenticResearchSystem()
    return _agentic_system

