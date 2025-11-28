"""
Chat Router - Chat session and message endpoints for AmaniQuery
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Depends, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["Chat"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatSessionCreate(BaseModel):
    """Create chat session request"""
    title: Optional[str] = None
    user_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Chat session response"""
    id: str
    title: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0


class ChatMessageCreate(BaseModel):
    """Create chat message request"""
    content: str
    role: str = "user"
    stream: bool = False
    attachment_ids: Optional[List[str]] = None


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: str
    session_id: str
    content: str
    role: str
    created_at: datetime
    token_count: Optional[int] = None
    model_used: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class FeedbackCreate(BaseModel):
    """Create feedback request"""
    message_id: str
    feedback_type: str  # "positive", "negative"
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response"""
    id: str
    message_id: str
    feedback_type: str
    comment: Optional[str] = None
    created_at: datetime


# =============================================================================
# DEPENDENCIES - State container to avoid global variable issues
# =============================================================================

class RouterState:
    """State container for router dependencies to avoid Python global variable issues"""
    chat_manager = None
    vision_storage = {}
    vision_rag_service = None
    rag_pipeline = None
    vector_store = None
    amaniq_v2_agent = None
    amaniq_v2_graph = None

# Single global instance
_state = RouterState()


def get_rag_pipeline():
    """Get RAG pipeline with lazy initialization fallback"""
    if _state.rag_pipeline is None:
        logger.warning("RAG pipeline not initialized via dependency injection, attempting lazy initialization")
        try:
            from Module4_NiruAPI.rag_pipeline import RAGPipeline
            _state.rag_pipeline = RAGPipeline()
            logger.info("RAG pipeline lazily initialized successfully")
        except Exception as e:
            logger.error(f"Failed to lazily initialize RAG pipeline: {e}")
            raise HTTPException(status_code=503, detail=f"RAG service not initialized: {e}")
    return _state.rag_pipeline


def get_chat_manager():
    """Get the chat manager instance"""
    if _state.chat_manager is None:
        logger.warning("Chat manager not initialized via dependency injection, attempting lazy initialization")
        try:
            from Module3_NiruDB.chat_manager import ChatDatabaseManager
            _state.chat_manager = ChatDatabaseManager()
            logger.info("Chat manager lazily initialized successfully")
        except Exception as e:
            logger.error(f"Failed to lazily initialize chat manager: {e}")
            raise HTTPException(status_code=503, detail=f"Chat service not initialized: {e}")
    return _state.chat_manager


def get_amaniq_v2_graph():
    """Get the AmaniQ v2 compiled graph directly (avoids global model issues)"""
    if _state.amaniq_v2_graph is None:
        logger.error("CRITICAL: AmaniQ v2 graph is None - this should never happen!")
        logger.error("The graph should have been initialized during API startup.")
        logger.error("Check API startup logs for initialization errors.")
        
        raise HTTPException(
            status_code=503, 
            detail="AmaniQ v2 graph not initialized. This is a critical system error. Please contact support."
        )
    
    return _state.amaniq_v2_graph
    

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from auth context if available"""
    try:
        auth_context = getattr(request.state, "auth_context", None)
        if auth_context and auth_context.user_id:
            return auth_context.user_id
    except Exception:
        pass
    return None


def verify_session_ownership(session_id: str, user_id: Optional[str], chat_manager) -> bool:
    """Verify that a session belongs to the specified user"""
    if not user_id:
        # If no user_id provided, allow access (for backward compatibility)
        return True
    
    session = chat_manager.get_session_with_user(session_id)
    if not session:
        return False
    
    return session.user_id == user_id


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(session: ChatSessionCreate, request: Request):
    """Create a new chat session"""
    chat_manager = get_chat_manager()
    
    try:
        # Get user_id from auth context if available
        user_id = get_current_user_id(request) or session.user_id
        
        session_id = chat_manager.create_session(session.title, user_id)
        session_data = chat_manager.get_session(session_id)
        return session_data
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(request: Request, limit: int = 50):
    """List chat sessions for the current user"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        return chat_manager.list_sessions(user_id, limit)
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        return []


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str, request: Request):
    """Get a specific chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request):
    """Delete a chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        chat_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def rename_chat_session(session_id: str, payload: Dict[str, str], request: Request):
    """Rename a chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        title = payload.get("title")
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
            
        chat_manager.update_session_title(session_id, title)
        session = chat_manager.get_session(session_id)
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def add_chat_message(session_id: str, message: ChatMessageCreate, request: Request):
    """Add a message to a chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if message.role == "user":
            # Check for vision data
            use_vision_rag = False
            session_images = []
            if _state.vision_rag_service and _state.vision_storage:
                session_images = _state.vision_storage.get(session_id, [])
                if session_images:
                    use_vision_rag = True
            
            if not use_vision_rag:
                get_rag_pipeline()  # Ensure rag_pipeline is initialized
            
            if message.stream:
                # Return streaming response
                return await _handle_streaming_message(
                    session_id, session, message, chat_manager,
                    use_vision_rag, session_images
                )
            else:
                # Return regular response
                return await _handle_regular_message(
                    session_id, session, message, chat_manager,
                    use_vision_rag, session_images
                )
        else:
            # Non-user message (e.g., system)
            attachments_data = _get_attachments(message.attachment_ids, session_id, chat_manager)
            
            msg_id = chat_manager.add_message(
                session_id=session_id,
                content=message.content,
                role=message.role,
                attachments=attachments_data
            )
            messages = chat_manager.get_messages(session_id, limit=1)
            return messages[-1] if messages else None
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_streaming_message(
    session_id: str, session, message: ChatMessageCreate, chat_manager,
    use_vision_rag: bool, session_images: list
):
    """Handle streaming message response"""
    # Process query
    if use_vision_rag:
        if _state.vision_rag_service is None or not hasattr(_state.vision_rag_service, "query"):
            raise HTTPException(status_code=503, detail="Vision RAG service not initialized")
        result = _state.vision_rag_service.query(
            question=message.content,
            session_images=session_images,
            top_k=3,
            temperature=0.7,
            max_tokens=1000,
            stream=True,
        )
        # Convert vision sources
        vision_sources = []
        for src in result.get("sources", []):
            vision_sources.append({
                "title": src.get("filename", "Image"),
                "url": "",
                "source_name": src.get("source_file", "Uploaded Image"),
                "category": "vision",
                "excerpt": f"Image similarity: {src.get('similarity', 0):.2f}",
            })
        result["sources"] = vision_sources
    else:
        # Use AmaniQ v2 graph directly for all non-vision queries (REQUIRED)
        logger.info("[Chat] Using AmaniQ v2 graph (System Brain)")
        try:
            # Get the AmaniQ v2 compiled graph directly
            graph = get_amaniq_v2_graph()
            
            # Get conversation history
            messages = chat_manager.get_messages(session_id, limit=5)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Build initial state for the graph - only include required fields
            initial_state = {
                "current_query": message.content,
                "original_question": message.content,
                "messages": conversation_history + [{"role": "user", "content": message.content}],
                "thread_id": session_id,
            }
            
            # Execute graph directly (THE BRAIN)
            config = {"configurable": {"thread_id": session_id}}
            final_state = await graph.ainvoke(initial_state, config=config)
            
            # Extract result from final state
            amaniq_result = {
                "answer": final_state.get("final_response", ""),
                "sources": final_state.get("citations", []),
                "confidence": final_state.get("response_confidence", 0.0),
                "persona": final_state.get("supervisor_decision", {}).get("persona"),
                "intent": final_state.get("intent"),
            }
            
            # Format for chat response
            result = {
                "answer": amaniq_result.get("answer", ""),
                "sources": amaniq_result.get("sources", []),
                "retrieved_chunks": len(amaniq_result.get("sources", [])),
                "model_used": f"AmaniQ-v2-{amaniq_result.get('persona', 'wanjiku')}",
                "structured_data": {
                    "confidence": amaniq_result.get("confidence", 0.0),
                    "persona": amaniq_result.get("persona"),
                    "intent": amaniq_result.get("intent"),
                },
                "answer_stream": None  # Non-streaming for now
            }
            logger.info(f"[Chat] AmaniQ v2 completed with confidence {amaniq_result.get('confidence', 0):.2f}")
        except Exception as e:
            # ONLY on error: Fall back to standard RAG pipeline
            logger.error(f"[Chat] AmaniQ v2 CRITICAL ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("[RAG] Emergency fallback to standard RAG pipeline")
            if _state.rag_pipeline is not None:
                result = _state.rag_pipeline.query_stream(
                    query=message.content,
                    top_k=3,
                    max_tokens=1000,
                    temperature=0.7,
                    session_id=session_id,
                )
            else:
                raise HTTPException(status_code=503, detail="No query service available")
    
    # Add user message
    attachments_data = _get_attachments(message.attachment_ids, session_id, chat_manager)
    chat_manager.add_message(
        session_id=session_id,
        content=message.content,
        role="user",
        attachments=attachments_data
    )
    
    # Auto-generate title if needed
    if not session.title or session.title == "New Chat":
        try:
            new_title = chat_manager.generate_session_title(session_id)
            logger.info(f"Auto-generated title: {new_title}")
        except Exception as e:
            logger.warning(f"Failed to auto-generate session title: {e}")
    
    async def generate_stream():
        full_answer = ""
        try:
            # Send sources first
            sources_data = {
                "type": "sources",
                "sources": result.get("sources", []),
                "retrieved_chunks": result.get("retrieved_chunks", 0),
                "model_used": result.get("model_used", "unknown")
            }
            yield f"data: {json.dumps(sources_data)}\n\n"
            
            # Stream the answer
            if "answer_stream" in result and result["answer_stream"] is not None:
                for chunk in result["answer_stream"]:
                    if isinstance(chunk, str):
                        content = chunk
                    elif hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        content = delta.content if hasattr(delta, 'content') else ""
                    elif hasattr(chunk, 'text'):
                        content = chunk.text
                    else:
                        content = ""
                    
                    if content:
                        full_answer += content
                        chunk_data = {"type": "content", "content": content}
                        yield f"data: {json.dumps(chunk_data)}\n\n"
            elif "answer" in result:
                content = str(result["answer"])
                full_answer = content
                chunk_data = {"type": "content", "content": content}
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Send completion
            completion_data = {
                "type": "done",
                "full_answer": full_answer,
                "structured_data": result.get("structured_data")
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            # Save assistant message
            if full_answer.strip():
                chat_manager.add_message(
                    session_id=session_id,
                    content=full_answer,
                    role="assistant",
                    token_count=result.get("retrieved_chunks", 0),
                    model_used=result.get("model_used", "unknown"),
                    sources=result.get("sources", [])
                )
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


async def _handle_regular_message(
    session_id: str, session, message: ChatMessageCreate, chat_manager,
    use_vision_rag: bool, session_images: list
):
    """Handle regular (non-streaming) message response"""
    if use_vision_rag:
        result = _state.vision_rag_service.query(
            question=message.content,
            session_images=session_images,
            top_k=3,
            temperature=0.7,
            max_tokens=1000,
        )
        # Convert vision sources
        vision_sources = []
        for src in result.get("sources", []):
            vision_sources.append({
                "title": src.get("filename", "Image"),
                "url": "",
                "source_name": src.get("source_file", "Uploaded Image"),
                "category": "vision",
                "excerpt": f"Image similarity: {src.get('similarity', 0):.2f}",
            })
        result["sources"] = vision_sources
        result["retrieved_chunks"] = result.get("retrieved_images", 0)
    else:
        # Use AmaniQ v2 agent for all non-vision queries (REQUIRED)
        logger.info("[Chat] Using AmaniQ v2 agent (System Brain)")
        try:
            # Get conversation history
            messages = chat_manager.get_messages(session_id, limit=5)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Execute AmaniQ v2 pipeline (THE BRAIN)
            amaniq_result = await _state.amaniq_v2_agent.chat(
                message=message.content,
                thread_id=session_id,
                message_history=conversation_history,
            )
            
            # Format for chat response
            result = {
                "answer": amaniq_result.get("answer", ""),
                "sources": amaniq_result.get("sources", []),
                "retrieved_chunks": len(amaniq_result.get("sources", [])),
                "model_used": f"AmaniQ-v2-{amaniq_result.get('persona', 'wanjiku')}",
                "structured_data": {
                    "confidence": amaniq_result.get("confidence", 0.0),
                    "persona": amaniq_result.get("persona"),
                    "intent": amaniq_result.get("intent"),
                }
            }
            logger.info(f"[Chat] AmaniQ v2 completed with confidence {amaniq_result.get('confidence', 0):.2f}")
        except Exception as e:
            # ONLY on error: Fall back to standard RAG pipeline
            logger.error(f"[Chat] AmaniQ v2 CRITICAL ERROR: {e}")
            logger.warning("[RAG] Emergency fallback to standard RAG pipeline")
            if _state.rag_pipeline is not None:
                result = _state.rag_pipeline.query(
                    query=message.content,
                    top_k=3,
                    max_tokens=1000,
                    temperature=0.7,
                    session_id=session_id,
                )
            else:
                raise HTTPException(status_code=503, detail="No query service available")
    
    # Add user message
    attachments_data = _get_attachments(message.attachment_ids, session_id, chat_manager)
    chat_manager.add_message(
        session_id=session_id,
        content=message.content,
        role="user",
        attachments=attachments_data
    )
    
    # Add assistant response
    chat_manager.add_message(
        session_id=session_id,
        content=result["answer"],
        role="assistant",
        token_count=result.get("retrieved_chunks", 0),
        model_used=result.get("model_used", "unknown"),
        sources=result.get("sources", [])
    )
    
    # Generate title if needed
    session = chat_manager.get_session(session_id)
    if session and not session.title:
        title = chat_manager.generate_session_title(session_id)
        chat_manager.update_session_title(session_id, title)
    
    messages = chat_manager.get_messages(session_id, limit=1)
    return messages[-1] if messages else None


def _get_attachments(attachment_ids: Optional[List[str]], session_id: str, chat_manager) -> Optional[List[Dict]]:
    """Retrieve attachment metadata from session messages"""
    if not attachment_ids:
        return None
    
    session_messages = chat_manager.get_messages(session_id)
    attachments_data = []
    for msg in session_messages:
        if msg.attachments:
            for att in msg.attachments:
                if att.get("id") in attachment_ids:
                    attachments_data.append(att)
    return attachments_data if attachments_data else None


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(session_id: str, request: Request, limit: int = 100):
    """Get messages for a chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return chat_manager.get_messages(session_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/attachments")
async def upload_chat_attachment(
    request: Request,
    session_id: str,
    file: UploadFile = File(...)
):
    """Upload a document attachment for a chat session"""
    chat_manager = get_chat_manager()
    
    if _state.vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    user_id = get_current_user_id(request)
    if not verify_session_ownership(session_id, user_id, chat_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
    
    # Validate file type
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        from Module4_NiruAPI.services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        result = processor.process_file(
            file_content=file_content,
            filename=file.filename,
            session_id=session_id
        )
        
        # Store chunks in vector store
        if result["chunks"]:
            collection_name = f"chat_session_{session_id}"
            processor.store_chunks_in_vector_store(
                chunks=result["chunks"],
                vector_store=_state.vector_store,
                collection_name=collection_name
            )
        
        # Store vision data if available
        vision_data = result.get("vision_data")
        if vision_data and vision_data.get("images"):
            if session_id not in _state.vision_storage:
                _state.vision_storage[session_id] = []
            _state.vision_storage[session_id].extend(vision_data["images"])
        
        return {
            "attachment": result["attachment"],
            "message": "File processed successfully",
            "vision_processed": vision_data is not None and vision_data.get("count", 0) > 0,
        }
        
    except Exception as e:
        logger.error(f"Error processing attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/sessions/{session_id}/vision-content")
async def get_vision_content(session_id: str, request: Request):
    """Get vision content for a session"""
    chat_manager = get_chat_manager()
    
    user_id = get_current_user_id(request)
    if not verify_session_ownership(session_id, user_id, chat_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_images = _state.vision_storage.get(session_id, [])
    
    content_list = []
    for img_data in session_images:
        content_list.append({
            "id": img_data.get("id"),
            "filename": img_data.get("metadata", {}).get("filename", ""),
            "file_path": img_data.get("file_path", ""),
            "type": img_data.get("metadata", {}).get("type", ""),
            "page_number": img_data.get("metadata", {}).get("page_number"),
            "source_file": img_data.get("metadata", {}).get("source_file", ""),
        })
    
    return {
        "session_id": session_id,
        "count": len(content_list),
        "content": content_list,
    }


@router.post("/feedback", response_model=FeedbackResponse)
async def add_feedback(feedback: FeedbackCreate, request: Request):
    """Add feedback for a chat message"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        
        feedback_id = chat_manager.add_feedback(
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            user_id=user_id
        )
        
        return FeedbackResponse(
            id=feedback_id,
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            created_at=datetime.utcnow()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    chat_manager = get_chat_manager()
    
    try:
        return chat_manager.get_feedback_stats()
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/share")
async def share_chat_session(session_id: str, request: Request, share_type: str = "link"):
    """Generate a shareable link for a chat session"""
    chat_manager = get_chat_manager()
    
    try:
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        share_link = f"/shared/{session_id}"
        
        return {
            "share_link": share_link,
            "session_title": session.title,
            "message_count": session.message_count,
            "share_type": share_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shared/{session_id}")
async def get_shared_session(session_id: str):
    """Get a shared chat session (public access)"""
    chat_manager = get_chat_manager()
    
    try:
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        messages = chat_manager.get_messages(session_id)
        
        return {
            "title": session.title,
            "created_at": session.created_at,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at,
                    "model_used": msg.model_used,
                    "sources": msg.sources,
                    "attachments": msg.attachments
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting shared session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
