"""
Research Module for AmaniQuery
Uses Gemini AI to analyze legal queries and generate reports on Kenya's laws
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResearchModule:
    """
    Research module using Gemini AI for analyzing legal queries
    and generating reports on Kenya's laws and legal information
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize research module with Gemini API

        Args:
            api_key: Gemini API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Research module initialized with Gemini AI")
        except ImportError:
            raise ValueError("google-generativeai package not installed. Install with: pip install google-generativeai")

    def analyze_legal_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a legal query about Kenya's laws

        Args:
            query: The legal question or query to analyze
            context: Additional context about the query (optional)

        Returns:
            Dictionary containing analysis results
        """
        context_info = ""
        if context:
            context_info = f"\n\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2)}"

        prompt = f"""
        Analyze the following legal query about Kenya's laws and provide comprehensive information:

        LEGAL QUERY:
        {query}{context_info}

        Please provide a detailed analysis covering:

        1. QUERY INTERPRETATION:
           - Understanding of the legal question
           - Key legal concepts involved
           - Relevant areas of Kenyan law

        2. APPLICABLE LAWS:
           - Specific Kenyan laws, acts, or regulations
           - Constitutional provisions if relevant
           - Case law or precedents

        3. LEGAL ANALYSIS:
           - Step-by-step legal reasoning
           - Rights and obligations involved
           - Potential legal implications

        4. PRACTICAL GUIDANCE:
           - How to approach this legal matter
           - Required documentation or procedures
           - Relevant government agencies or courts

        5. ADDITIONAL CONSIDERATIONS:
           - Related legal areas to consider
           - Potential challenges or limitations
           - When to seek professional legal advice

        Format your response as a JSON object with these sections.
        Include specific references to Kenyan legal sources where possible.
        """

        try:
            response = self.model.generate_content(prompt)
            result = response.text

            # Try to parse as JSON, if it fails, return structured text
            try:
                analysis = json.loads(result)
            except json.JSONDecodeError:
                # If not valid JSON, structure it manually
                analysis = {
                    "query_interpretation": self._extract_section(result, "QUERY INTERPRETATION"),
                    "applicable_laws": self._extract_section(result, "APPLICABLE LAWS"),
                    "legal_analysis": self._extract_section(result, "LEGAL ANALYSIS"),
                    "practical_guidance": self._extract_section(result, "PRACTICAL GUIDANCE"),
                    "additional_considerations": self._extract_section(result, "ADDITIONAL CONSIDERATIONS"),
                    "raw_analysis": result
                }

            return {
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": "gemini-1.5-pro",
                "original_query": query,
                "context_provided": context is not None
            }

        except Exception as e:
            logger.error(f"Error in legal query analysis: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "original_query": query
            }

    def generate_legal_report(self, analysis_results: Dict[str, Any], report_focus: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate a comprehensive legal report based on query analysis

        Args:
            analysis_results: Results from analyze_legal_query
            report_focus: Type of report focus (comprehensive, constitutional, criminal, civil, administrative)

        Returns:
            Dictionary containing the legal report
        """
        analysis = analysis_results.get("analysis", {})

        focus_prompts = {
            "comprehensive": """
            Generate a comprehensive legal report covering all aspects of the query.
            Include legal analysis, applicable laws, practical guidance, and recommendations.
            """,
            "constitutional": """
            Focus on constitutional law aspects, fundamental rights, and constitutional remedies.
            Include relevant constitutional provisions and their interpretation.
            """,
            "criminal": """
            Focus on criminal law aspects, offenses, penalties, and criminal procedure.
            Include relevant criminal statutes and procedural requirements.
            """,
            "civil": """
            Focus on civil law aspects, contracts, torts, and civil remedies.
            Include relevant civil statutes and case law precedents.
            """,
            "administrative": """
            Focus on administrative law aspects, government regulations, and administrative procedures.
            Include relevant administrative statutes and regulatory frameworks.
            """
        }

        prompt = f"""
        Based on the following legal query analysis, generate a detailed legal report:

        ANALYSIS RESULTS:
        {json.dumps(analysis, indent=2)}

        REPORT FOCUS: {report_focus}

        {focus_prompts.get(report_focus, focus_prompts["comprehensive"])}

        STRUCTURE THE LEGAL REPORT AS FOLLOWS:

        1. QUERY SUMMARY
           - Original legal question
           - Key issues identified
           - Legal context

        2. APPLICABLE LAW
           - Relevant statutes and regulations
           - Constitutional provisions
           - Case law and precedents

        3. LEGAL ANALYSIS
           - Detailed legal reasoning
           - Rights and obligations
           - Legal implications and consequences

        4. PROCEDURAL GUIDANCE
           - Required steps and procedures
           - Documentation needed
           - Relevant institutions and agencies

        5. PRACTICAL CONSIDERATIONS
           - Implementation challenges
           - Cost and time considerations
           - Alternative approaches

        6. RECOMMENDATIONS
           - Actionable legal recommendations
           - Risk mitigation strategies
           - When to consult legal professionals

        7. ADDITIONAL RESOURCES
           - Further reading and references
           - Related legal topics
           - Support services and organizations

        8. CONCLUSION
           - Summary of legal position
           - Final recommendations
           - Next steps

        Format the report in a professional, accessible manner suitable for non-lawyers while maintaining legal accuracy.
        Include specific references to Kenyan laws, acts, and regulations where applicable.
        """

        try:
            response = self.model.generate_content(prompt)
            report_content = response.text

            return {
                "report": {
                    "title": f"Legal Report - {report_focus.title()} Analysis",
                    "content": report_content,
                    "focus_area": report_focus,
                    "generated_at": datetime.utcnow().isoformat(),
                    "model_used": "gemini-1.5-pro"
                },
                "metadata": {
                    "analysis_timestamp": analysis_results.get("timestamp"),
                    "report_focus": report_focus,
                    "report_length": len(report_content),
                    "sections": self._extract_report_sections(report_content)
                },
                "source_analysis": analysis_results
            }

        except Exception as e:
            logger.error(f"Error generating legal report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "report_focus": report_focus
            }

    def conduct_legal_research(self, legal_topics: List[str], research_questions: List[str]) -> Dict[str, Any]:
        """
        Conduct legal research on specific topics related to Kenya's laws

        Args:
            legal_topics: List of legal topics to research
            research_questions: List of specific research questions

        Returns:
            Dictionary containing legal research findings
        """
        prompt = f"""
        Conduct comprehensive legal research on Kenya's laws based on the following:

        LEGAL TOPICS:
        {json.dumps(legal_topics, indent=2)}

        RESEARCH QUESTIONS:
        {json.dumps(research_questions, indent=2)}

        For each legal topic, provide:
        1. Overview of the legal framework
        2. Key statutes and regulations
        3. Recent developments and amendments
        4. Practical implications for citizens
        5. Common issues and challenges

        Then address each research question with:
        - Legal analysis and interpretation
        - Relevant case law and precedents
        - Practical guidance and procedures
        - Recommendations for legal compliance

        Focus on providing accurate, up-to-date information about Kenyan law.
        Include references to specific laws, acts, and legal sources.
        Provide information that helps users understand and navigate Kenya's legal system.
        """

        try:
            response = self.model.generate_content(prompt)
            research_findings = response.text

            return {
                "legal_research": {
                    "findings": research_findings,
                    "topics_researched": legal_topics,
                    "questions_addressed": research_questions,
                    "generated_at": datetime.utcnow().isoformat(),
                    "model_used": "gemini-1.5-pro"
                },
                "metadata": {
                    "topic_count": len(legal_topics),
                    "question_count": len(research_questions),
                    "findings_length": len(research_findings)
                }
            }

        except Exception as e:
            logger.error(f"Error conducting legal research: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "topics": legal_topics,
                "questions": research_questions
            }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from text response"""
        # Simple text extraction - look for section headers
        lines = text.split('\n')
        section_lines = []
        in_section = False

        for line in lines:
            if section_name.upper() in line.upper():
                in_section = True
                continue
            elif in_section and line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                # Next numbered section
                break
            elif in_section:
                section_lines.append(line)

        return '\n'.join(section_lines).strip()

    def _extract_report_sections(self, report: str) -> List[str]:
        """Extract section headers from the report"""
        lines = report.split('\n')
        sections = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith(' ') and len(line) < 100:
                # Likely a section header
                if any(keyword in line.upper() for keyword in ['SUMMARY', 'METHODOLOGY', 'ANALYSIS', 'FINDINGS', 'CHALLENGES', 'RECOMMENDATIONS', 'OUTLOOK', 'CONCLUSION']):
                    sections.append(line)

        return sections