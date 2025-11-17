"""
Sub-Agent Factory - Creates specialist agents (Researcher, Citer, Editor, Validator)
"""
from typing import Dict, Any, Optional
from loguru import logger


class SubAgent:
    """Base class for sub-agents"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output"""
        raise NotImplementedError


class ResearcherAgent(SubAgent):
    """Specialist agent for research tasks"""
    
    def __init__(self):
        super().__init__("Researcher", "Conducts research and gathers information")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process research task"""
        query = input_data.get('query', '')
        
        return {
            'agent': self.name,
            'task': 'research',
            'query': query,
            'result': f"Research conducted on: {query}"
        }


class CiterAgent(SubAgent):
    """Specialist agent for citation and source management"""
    
    def __init__(self):
        super().__init__("Citer", "Manages citations and sources")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process citation task"""
        content = input_data.get('content', '')
        sources = input_data.get('sources', [])
        
        # Format citations
        citations = []
        for i, source in enumerate(sources, 1):
            citations.append(f"[{i}] {source.get('title', 'Source')} - {source.get('url', '')}")
        
        return {
            'agent': self.name,
            'task': 'citation',
            'citations': citations,
            'formatted_content': f"{content}\n\nSources:\n" + "\n".join(citations)
        }


class EditorAgent(SubAgent):
    """Specialist agent for editing and formatting"""
    
    def __init__(self):
        super().__init__("Editor", "Edits and formats content")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process editing task"""
        content = input_data.get('content', '')
        
        # Simple editing (in production, use LLM for better editing)
        edited = content.strip()
        
        return {
            'agent': self.name,
            'task': 'editing',
            'original_length': len(content),
            'edited_length': len(edited),
            'edited_content': edited
        }


class ValidatorAgent(SubAgent):
    """Specialist agent for validation and fact-checking"""
    
    def __init__(self):
        super().__init__("Validator", "Validates and fact-checks content")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process validation task"""
        content = input_data.get('content', '')
        sources = input_data.get('sources', [])
        
        # Simple validation checks
        has_sources = len(sources) > 0
        has_content = len(content) > 0
        is_well_formed = content.count('.') > 0  # Has sentences
        
        validation_score = sum([has_sources, has_content, is_well_formed]) / 3.0
        
        return {
            'agent': self.name,
            'task': 'validation',
            'validation_score': validation_score,
            'checks': {
                'has_sources': has_sources,
                'has_content': has_content,
                'is_well_formed': is_well_formed
            },
            'validated': validation_score >= 0.7
        }


class SubAgentFactory:
    """Factory for creating specialist sub-agents"""
    
    _agents = {
        'researcher': ResearcherAgent,
        'citer': CiterAgent,
        'editor': EditorAgent,
        'validator': ValidatorAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str) -> Optional[SubAgent]:
        """
        Create a sub-agent
        
        Args:
            agent_type: Type of agent (researcher, citer, editor, validator)
            
        Returns:
            Sub-agent instance or None
        """
        agent_class = cls._agents.get(agent_type.lower())
        if agent_class:
            return agent_class()
        else:
            logger.warning(f"Unknown agent type: {agent_type}")
            return None
    
    @classmethod
    def list_agent_types(cls) -> list:
        """List available agent types"""
        return list(cls._agents.keys())

