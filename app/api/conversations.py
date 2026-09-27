"""
Conversations API Router
========================
Endpoints for creating conversations and retrieving conversation history.
Phase 8 Implementation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_conversation_memory
from app.memory.config import MAX_HISTORY_MESSAGES
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
    MemoryStorageError,
)
from app.memory.interface import ConversationMemory
from app.schemas.conversation import (
    ConversationHistoryResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    CreateConversationRequest,
    MessageResponse,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List customer conversations",
    description="Retrieve list of conversations owned by the customer, ordered by most recent activity.",
    responses={
        200: {"description": "Customer conversation list ordered by recent activity"},
        422: {"description": "Validation error on customer_id"},
        500: {"description": "Storage failure"},
    },
)
def list_customer_conversations(
    customer_id: str = Query(..., description="Trusted customer ID owning the conversations"),
    limit: int = Query(default=50, ge=1, le=100, description="Max conversations to retrieve"),
    memory: ConversationMemory = Depends(get_conversation_memory),
) -> ConversationListResponse:
    """Retrieves all past conversations for a customer to display in the sidebar."""
    clean_cust_id = (customer_id or "").strip()
    if not clean_cust_id:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": {"code": "VALIDATION_ERROR", "message": "customer_id cannot be empty or whitespace only."}},
        )

    try:
        items = memory.list_conversations(customer_id=clean_cust_id, limit=limit)
        return ConversationListResponse(
            customer_id=clean_cust_id,
            conversations=[ConversationSummary(**item) for item in items],
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation session for a trusted customer.",
    responses={
        201: {"description": "Conversation created successfully"},
        422: {"description": "Validation error"},
        500: {"description": "Storage or internal failure"},
    },
)
def create_conversation(
    request: CreateConversationRequest,
    memory: ConversationMemory = Depends(get_conversation_memory),
) -> ConversationResponse:
    """Creates a new conversation session for the given customer."""
    try:
        conv = memory.create_conversation(customer_id=request.customer_id)
        return ConversationResponse(
            conversation_id=conv.conversation_id,
            customer_id=conv.customer_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
    except (ConversationNotFoundError, CustomerMismatchError, InvalidMessageError, MemoryStorageError):
        raise
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    description="Retrieve chronological message history for a conversation owned by the customer.",
    responses={
        200: {"description": "Chronological conversation history"},
        404: {"description": "Conversation not found or customer mismatch"},
        422: {"description": "Validation error on parameters"},
        500: {"description": "Storage failure"},
    },
)
def get_conversation_history(
    conversation_id: str = Path(..., description="Unique conversation identifier"),
    customer_id: str = Query(..., description="Trusted customer ID owning the conversation"),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=MAX_HISTORY_MESSAGES,
        description=f"Maximum messages to retrieve (1 to {MAX_HISTORY_MESSAGES})",
    ),
    memory: ConversationMemory = Depends(get_conversation_memory),
) -> ConversationHistoryResponse:
    """Retrieves chronological message history for a customer's conversation."""
    clean_cust_id = (customer_id or "").strip()
    if not clean_cust_id:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": {"code": "VALIDATION_ERROR", "message": "customer_id cannot be empty or whitespace only."}},
        )

    clean_conv_id = (conversation_id or "").strip()
    if not clean_conv_id:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found."}},
        )

    try:
        messages = memory.get_history(
            conversation_id=clean_conv_id,
            customer_id=clean_cust_id,
            limit=limit,
        )

        return ConversationHistoryResponse(
            conversation_id=clean_conv_id,
            customer_id=clean_cust_id,
            messages=[
                MessageResponse(
                    message_id=m.message_id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                    sequence_number=m.sequence_number,
                    sources=m.sources,
                    thought_process=m.thought_process,
                    execution_time_ms=m.execution_time_ms,
                )
                for m in messages
            ],
        )
    except (ConversationNotFoundError, CustomerMismatchError, InvalidMessageError, MemoryStorageError):
        raise
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete conversation",
    description="Delete a conversation and its messages owned by the customer.",
    responses={
        200: {"description": "Conversation deleted successfully"},
        404: {"description": "Conversation not found or customer mismatch"},
        422: {"description": "Validation error"},
        500: {"description": "Storage failure"},
    },
)
def delete_conversation(
    conversation_id: str = Path(..., description="Unique conversation identifier"),
    customer_id: str = Query(..., description="Trusted customer ID owning the conversation"),
    memory: ConversationMemory = Depends(get_conversation_memory),
):
    """Deletes a conversation owned by the customer from memory."""
    clean_cust_id = (customer_id or "").strip()
    if not clean_cust_id:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": {"code": "VALIDATION_ERROR", "message": "customer_id cannot be empty or whitespace only."}},
        )

    clean_conv_id = (conversation_id or "").strip()
    if not clean_conv_id:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found."}},
        )

    try:
        deleted = memory.delete_conversation(conversation_id=clean_conv_id, customer_id=clean_cust_id)
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": {"code": "CONVERSATION_NOT_FOUND", "message": "Conversation not found or customer mismatch."}},
            )
        return {"status": "ok", "message": "Conversation deleted successfully."}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
        )
