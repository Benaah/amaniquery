"""
SMS Router - SMS webhook and gateway endpoints for AmaniQuery
"""
from fastapi import APIRouter, HTTPException, Request, Form
from loguru import logger

router = APIRouter(tags=["SMS Gateway"])


# =============================================================================
# DEPENDENCIES
# =============================================================================

_sms_pipeline = None
_sms_service = None


def configure_sms_router(sms_pipeline=None, sms_service=None):
    """Configure the SMS router with required dependencies"""
    global _sms_pipeline, _sms_service
    
    _sms_pipeline = sms_pipeline
    _sms_service = sms_service


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/sms-webhook")
async def sms_webhook(
    request: Request,
    from_: str = Form(..., alias="from"),
    to: str = Form(...),
    text: str = Form(...),
    date: str = Form(None),
    id_: str = Form(None, alias="id"),
    linkId: str = Form(None),
    networkCode: str = Form(None)
):
    """
    Africa's Talking SMS Webhook
    
    Receives incoming SMS messages and sends intelligent responses.
    This endpoint is called by Africa's Talking when an SMS is received.
    
    **How it works:**
    1. User sends SMS to your Africa's Talking shortcode/number
    2. Africa's Talking forwards the SMS to this webhook
    3. AmaniQuery processes the query using RAG pipeline
    4. Response is sent back via SMS (max 160 characters)
    
    **Example SMS queries:**
    - "What is the Finance Bill about?"
    - "Latest news on housing"
    - "Constitution Article 10"
    
    **Setup:**
    1. Sign up at https://africastalking.com
    2. Get API key and username
    3. Set environment variables: AT_USERNAME, AT_API_KEY
    4. Configure webhook URL in Africa's Talking dashboard
    """
    if _sms_pipeline is None or _sms_service is None:
        logger.error("SMS services not initialized")
        return {"status": "error", "message": "SMS service unavailable"}
    
    try:
        # Parse incoming SMS
        phone_number = _sms_service.format_kenyan_phone(from_)
        query_text = text.strip()
        
        logger.info(f"📱 Incoming SMS from {phone_number}: {query_text}")
        
        # Detect language (basic detection)
        language = "sw" if any(word in query_text.lower() for word in ["nini", "habari", "tafadhali", "je"]) else "en"
        
        # Process query through SMS-optimized RAG
        result = _sms_pipeline.process_sms_query(
            query=query_text,
            language=language,
            phone_number=phone_number
        )
        
        response_text = result["response"]
        
        # Send SMS response
        if _sms_service.available:
            send_result = _sms_service.send_sms(phone_number, response_text)
            
            if send_result.get("success"):
                logger.info(f"✓ SMS sent to {phone_number}")
                return {
                    "status": "success",
                    "message": "Response sent",
                    "response_text": response_text,
                    "query_type": result.get("query_type"),
                    "message_id": send_result.get("message_id")
                }
            else:
                logger.error(f"Failed to send SMS: {send_result.get('error')}")
                return {
                    "status": "error",
                    "message": "Failed to send response",
                    "error": send_result.get("error")
                }
        else:
            logger.warning(f"SMS service unavailable. Would send: {response_text}")
            return {
                "status": "success",
                "message": "Query processed (SMS sending disabled)",
                "response_text": response_text,
                "query_type": result.get("query_type")
            }
            
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/sms-send")
async def send_sms_manual(phone_number: str, message: str):
    """
    Send SMS manually (for testing)
    
    **Parameters:**
    - phone_number: Recipient phone number (+254XXXXXXXXX)
    - message: SMS message text (max 160 characters recommended)
    
    **Example:**
    ```
    POST /sms-send
    {
        "phone_number": "+254712345678",
        "message": "Finance Bill 2025 aims to raise revenue through new taxes."
    }
    ```
    """
    if _sms_service is None:
        raise HTTPException(
            status_code=503, 
            detail="SMS service not initialized. Please restart the FastAPI server."
        )
    
    if not _sms_service.available:
        error_detail = "SMS service not available"
        if hasattr(_sms_service, 'test_mode') and _sms_service.test_mode:
            error_detail += " (test mode is enabled)"
        elif hasattr(_sms_service, 'use_direct_api') and _sms_service.use_direct_api:
            error_detail += " (using direct API fallback)"
        else:
            error_detail += ". Check AT_USERNAME and AT_API_KEY environment variables."
        
        raise HTTPException(status_code=503, detail=error_detail)
    
    try:
        formatted_phone = _sms_service.format_kenyan_phone(phone_number)
        result = _sms_service.send_sms(formatted_phone, message)
        
        if result.get("success"):
            return {
                "status": "success",
                "phone_number": formatted_phone,
                "message": message,
                "message_id": result.get("message_id"),
                "cost": result.get("cost")
            }
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to send SMS: {error_msg}")
            if "SSL" in str(error_msg) or "Connection" in str(error_msg):
                raise HTTPException(
                    status_code=503,
                    detail=f"Network error: {error_msg}"
                )
            raise HTTPException(status_code=500, detail=f"Failed to send SMS: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending manual SMS: {e}")
        error_str = str(e)
        if "SSL" in error_str or "Connection" in error_str:
            raise HTTPException(status_code=503, detail=f"Network error: {error_str}")
        raise HTTPException(status_code=500, detail=f"Internal error: {error_str}")


@router.get("/sms-query")
async def sms_query_preview(query: str, language: str = "en"):
    """
    Preview SMS response without sending
    
    Test what response would be sent via SMS for a given query.
    Useful for testing before deploying webhook.
    
    **Parameters:**
    - query: Question to ask
    - language: Response language ('en' or 'sw')
    """
    if _sms_pipeline is None:
        raise HTTPException(status_code=503, detail="SMS pipeline not initialized")
    
    try:
        result = _sms_pipeline.process_sms_query(
            query=query,
            language=language
        )
        
        return {
            "query": query,
            "response": result["response"],
            "character_count": len(result["response"]),
            "within_sms_limit": len(result["response"]) <= 160,
            "query_type": result.get("query_type"),
            "sources": result.get("sources", []),
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error previewing SMS query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
