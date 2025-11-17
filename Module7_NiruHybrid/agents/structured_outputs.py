"""
Structured Outputs with Pydantic Validation
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger


class Dossier(BaseModel):
    """Structured dossier output"""
    title: str = Field(..., description="Title of the dossier")
    summary: str = Field(..., description="Executive summary")
    key_findings: List[str] = Field(..., description="Key findings")
    sources: List[Dict[str, str]] = Field(..., description="Source citations")
    recommendations: List[str] = Field(..., description="Recommendations")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EmailDraft(BaseModel):
    """Structured email draft output"""
    to: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")


class ResearchReport(BaseModel):
    """Structured research report output"""
    query: str = Field(..., description="Research query")
    answer: str = Field(..., description="Research answer")
    sources: List[Dict[str, Any]] = Field(..., description="Sources used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    methodology: str = Field(..., description="Research methodology")
    limitations: List[str] = Field(..., description="Limitations")


class StructuredOutputs:
    """
    Manages structured outputs with Pydantic validation
    """
    
    @staticmethod
    def validate_dossier(data: Dict[str, Any]) -> Dossier:
        """Validate and create dossier"""
        try:
            return Dossier(**data)
        except Exception as e:
            logger.error(f"Error validating dossier: {e}")
            raise ValueError(f"Invalid dossier format: {e}")
    
    @staticmethod
    def validate_email(data: Dict[str, Any]) -> EmailDraft:
        """Validate and create email draft"""
        try:
            return EmailDraft(**data)
        except Exception as e:
            logger.error(f"Error validating email: {e}")
            raise ValueError(f"Invalid email format: {e}")
    
    @staticmethod
    def validate_research_report(data: Dict[str, Any]) -> ResearchReport:
        """Validate and create research report"""
        try:
            return ResearchReport(**data)
        except Exception as e:
            logger.error(f"Error validating research report: {e}")
            raise ValueError(f"Invalid research report format: {e}")
    
    @staticmethod
    def create_dossier(
        title: str,
        summary: str,
        key_findings: List[str],
        sources: List[Dict[str, str]],
        recommendations: List[str]
    ) -> Dossier:
        """Create a validated dossier"""
        return Dossier(
            title=title,
            summary=summary,
            key_findings=key_findings,
            sources=sources,
            recommendations=recommendations
        )
    
    @staticmethod
    def create_email(
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> EmailDraft:
        """Create a validated email draft"""
        return EmailDraft(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc
        )

