"""
Knowledge Base Search Tool - Searches and adds to knowledge base
"""
from typing import Dict, Any, Optional, List
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Module3_NiruDB.vector_store import VectorStore


class KnowledgeBaseSearchTool:
    """Tool for searching and adding to the knowledge base"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize KB search tool
        
        Args:
            vector_store: Vector store instance (creates new if None)
        """
        self.vector_store = vector_store or VectorStore()
    
    def execute(
        self,
        query: str,
        top_k: int = 5,
        add_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        namespace: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search knowledge base and optionally add content
        
        Args:
            query: Search query
            top_k: Number of results to return
            add_content: Optional content to add to KB
            metadata: Optional metadata for added content
            namespace: Optional list of namespaces to search (searches all if None)
            
        Returns:
            Search results and add operation result
        """
        result = {
            'query': query,
            'search_results': [],
            'add_result': None
        }
        
        try:
            # Search knowledge base
            search_namespace = namespace or ["kenya_law", "kenya_news", "kenya_parliament", "historical", "global_trends"]
            search_results = self.vector_store.query(query_text=query, n_results=top_k, namespace=search_namespace)
            
            formatted_results = []
            for item in search_results:
                # Handle different response formats
                content = item.get('content') or item.get('text') or item.get('document', '')
                formatted_results.append({
                    'content': (content[:500] if isinstance(content, str) else str(content)[:500]),
                    'metadata': item.get('metadata', {}),
                    'score': item.get('score', item.get('distance', 0.0))
                })
            
            result['search_results'] = formatted_results
            
            # Add content if provided
            if add_content:
                try:
                    add_result = self.vector_store.add_documents(
                        texts=[add_content],
                        metadatas=[metadata or {}]
                    )
                    result['add_result'] = {
                        'success': True,
                        'documents_added': 1
                    }
                except Exception as e:
                    logger.error(f"Error adding to KB: {e}")
                    result['add_result'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            return result
        except Exception as e:
            logger.error(f"Error in KB search: {e}")
            return {
                'query': query,
                'search_results': [],
                'error': str(e)
            }

