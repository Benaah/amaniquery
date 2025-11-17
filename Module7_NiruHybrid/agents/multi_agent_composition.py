"""
Multi-Agent Composition for Hybrid Module
Specialist agents: Citer, Editor, Validator
"""
from typing import Dict, Any, List, Optional
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module4_NiruAPI.agents.composition.sub_agent_factory import SubAgentFactory, SubAgent
from Module4_NiruAPI.agents.composition.agent_orchestrator import AgentOrchestrator


class MultiAgentComposition:
    """
    Multi-agent composition for hybrid module
    Coordinates specialist agents via LangGraph subgraphs
    """
    
    def __init__(self):
        """Initialize multi-agent composition"""
        self.orchestrator = AgentOrchestrator()
        self.citer_agent = SubAgentFactory.create_agent('citer')
        self.editor_agent = SubAgentFactory.create_agent('editor')
        self.validator_agent = SubAgentFactory.create_agent('validator')
    
    def process_with_agents(
        self,
        content: str,
        sources: List[Dict[str, Any]],
        use_citer: bool = True,
        use_editor: bool = True,
        use_validator: bool = True
    ) -> Dict[str, Any]:
        """
        Process content through specialist agents
        
        Args:
            content: Content to process
            sources: Sources for citation
            use_citer: Whether to use citer agent
            use_editor: Whether to use editor agent
            use_validator: Whether to use validator agent
            
        Returns:
            Processed content with agent outputs
        """
        agent_chain = []
        
        if use_validator:
            agent_chain.append('validator')
        if use_editor:
            agent_chain.append('editor')
        if use_citer:
            agent_chain.append('citer')
        
        input_data = {
            'content': content,
            'sources': sources
        }
        
        result = self.orchestrator.orchestrate(
            task='hybrid_processing',
            input_data=input_data,
            agent_chain=agent_chain
        )
        
        return result
    
    def cite_sources(self, content: str, sources: List[Dict[str, Any]]) -> str:
        """Add citations to content using Citer agent"""
        if not self.citer_agent:
            return content
        
        result = self.citer_agent.process({
            'content': content,
            'sources': sources
        })
        
        return result.get('formatted_content', content)
    
    def edit_content(self, content: str) -> str:
        """Edit content using Editor agent"""
        if not self.editor_agent:
            return content
        
        result = self.editor_agent.process({
            'content': content
        })
        
        return result.get('edited_content', content)
    
    def validate_content(self, content: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate content using Validator agent"""
        if not self.validator_agent:
            return {'validated': True, 'validation_score': 1.0}
        
        result = self.validator_agent.process({
            'content': content,
            'sources': sources
        })
        
        return result

