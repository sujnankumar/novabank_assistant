"""
Chat API Router
===============
Endpoint for sending conversational queries to the NovaBank assistant.
Integrates with Phase 7 MemoryOrchestrator and Phase 6 BankingOrchestrator.
Phase 8 Implementation.
"""

from typing import TYPE_CHECKING
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_memory_orchestrator
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
    MemoryStorageError,
)
from app.schemas.chat import ChatRequest, ChatResponse

if TYPE_CHECKING:
    from app.memory.memory_orchestrator import MemoryOrchestrator

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a conversational banking query to the assistant within an existing session.",
    responses={
        200: {"description": "Assistant response successfully generated and persisted"},
        404: {"description": "Conversation not found or customer mismatch"},
        422: {"description": "Invalid message or malformed input"},
        500: {"description": "Internal error or memory failure"},
    },
)
def chat(
    request: ChatRequest,
    orchestrator: "MemoryOrchestrator" = Depends(get_memory_orchestrator),
) -> ChatResponse:
    """Processes a conversational turn within the specified customer session."""
    import logging
    import time
    logger = logging.getLogger("novabank.chat")
    
    logger.info(
        f"==> [CHAT RECEIVED] Customer: {request.customer_id} | Conversation: {request.conversation_id} | Query: {request.message[:80]!r}"
    )
    t0 = time.time()
    try:
        output = orchestrator.run_conversation(
            conversation_id=request.conversation_id,
            customer_id=request.customer_id,
            query=request.message,
        )
        elapsed = time.time() - t0
        logger.info(
            f"<== [CHAT COMPLETED] Route: {output.get('route')} | Elapsed: {elapsed:.2f}s | Response length: {len(output.get('response', ''))}"
        )
        return ChatResponse(
            conversation_id=request.conversation_id,
            customer_id=request.customer_id,
            message=output.get("response", ""),
            route=output.get("route"),
            sources=output.get("sources"),
            thought_process=output.get("thought_process", []),
            execution_time_ms=round(elapsed * 1000, 1),
        )
    except (ConversationNotFoundError, CustomerMismatchError, InvalidMessageError, MemoryStorageError) as known_err:
        logger.warning(f"[CHAT] Known validation error: {known_err}")
        raise
    except Exception as exc:
        logger.exception(f"[CHAT ERROR] Unexpected failure processing query: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )
