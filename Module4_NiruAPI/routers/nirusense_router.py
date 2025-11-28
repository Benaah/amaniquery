"""
NiruSense Health Check Router
Provides health status and metrics for the NiruSense processing pipeline
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os

router = APIRouter(prefix="/nirusense", tags=["NiruSense"])

@router.get("/health")
async def nirusense_health():
    """
    Get NiruSense processing pipeline health status.
    Checks Redis, PostgreSQL, Qdrant, and agent status.
    """
    try:
        from Module9_NiruSense.processing.health import health_checker
        health_status = await health_checker.get_overall_health()
        
        # Return 503 if unhealthy
        if health_status["status"] == "unhealthy":
            return JSONResponse(
                status_code=503,
                content=health_status
            )
        
        return health_status
    except ImportError as e:
        return {
            "status": "unavailable",
            "error": "NiruSense module not properly configured",
            "details": str(e)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

@router.get("/health/redis")
async def nirusense_health_redis():
    """Check NiruSense Redis connection"""
    try:
        from Module9_NiruSense.processing.health import health_checker
        return await health_checker.check_redis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/postgres")
async def nirusense_health_postgres():
    """Check NiruSense PostgreSQL connection"""
    try:
        from Module9_NiruSense.processing.health import health_checker
        return await health_checker.check_postgres()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/qdrant")
async def nirusense_health_qdrant():
    """Check NiruSense Qdrant connection"""
    try:
        from Module9_NiruSense.processing.health import health_checker
        return await health_checker.check_qdrant()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/agents")
async def nirusense_health_agents():
    """Check NiruSense agent status"""
    try:
        from Module9_NiruSense.processing.health import health_checker
        return await health_checker.check_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def nirusense_metrics():
    """Get NiruSense processing metrics"""
    try:
        from Module9_NiruSense.processing.monitoring import metrics
        return metrics.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def nirusense_status():
    """Get NiruSense configuration and status"""
    try:
        from Module9_NiruSense.processing.config import settings
        
        return {
            "service": "NiruSense",
            "enabled": os.getenv("ENABLE_NIRUSENSE", "false").lower() == "true",
            "agents": {
                "total": 9,
                "enabled": [
                    "language_identifier",
                    "slang_decoder",
                    "topic_classifier",
                    "entity_extractor",
                    "sentiment_analyzer",
                    "emotion_detector",
                    "bias_detector",
                    "summarizer",
                    "quality_scorer"
                ]
            },
            "models": {
                "embedding": settings.MODEL_EMBEDDING,
                "language": settings.MODEL_LANGUAGE,
                "slang": settings.MODEL_SLANG,
                "topic": settings.MODEL_TOPIC,
                "ner": settings.MODEL_NER,
                "sentiment": settings.MODEL_SENTIMENT,
                "emotion": settings.MODEL_EMOTION,
                "summarizer": settings.MODEL_SUMMARIZER
            },
            "configuration": {
                "redis_stream": settings.REDIS_STREAM_KEY,
                "qdrant_collection": settings.QDRANT_COLLECTION,
                "parallel_agents": settings.ENABLE_PARALLEL_AGENTS,
                "max_text_length": settings.MAX_TEXT_LENGTH
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
