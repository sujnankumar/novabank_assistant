"""
Conversation Memory Interface
=============================
Abstract interface establishing the contract for conversation memory storage.
Decouples orchestrator logic from underlying SQLite or database implementations.
"""

import abc
from typing import List, Optional
from app.memory.models import Conversation, Message


class ConversationMemory(abc.ABC):
    """Abstract interface defining required memory operations."""

    @abc.abstractmethod
    def create_conversation(
        self,
        customer_id: str,
    ) -> Conversation:
        """
        Creates and persists a new conversation session for the given customer.

        Parameters:
            customer_id (str): Trusted customer ID (e.g. 'CUST001').

        Returns:
            Conversation: The initialized conversation object.
        """
        pass

    @abc.abstractmethod
    def get_conversation(
        self,
        conversation_id: str,
        customer_id: str,
    ) -> Optional[Conversation]:
        """
        Retrieves a conversation scoped by both conversation_id and customer_id.

        Parameters:
            conversation_id (str): Unique conversation identifier.
            customer_id (str): Trusted customer ID.

        Returns:
            Optional[Conversation]: Conversation if found and customer matches; otherwise None.
        """
        pass

    @abc.abstractmethod
    def add_message(
        self,
        conversation_id: str,
        customer_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        thought_process: Optional[List[dict]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> Message:
        """
        Appends and persists a validated message turn to the conversation.

        Parameters:
            conversation_id (str): ID of the target conversation.
            customer_id (str): Trusted customer ID.
            role (str): 'user' or 'assistant'.
            content (str): Non-empty conversational message text.

        Returns:
            Message: The stored message with generated ID and sequence number.

        Raises:
            ConversationNotFoundError: If conversation does not exist.
            CustomerMismatchError: If conversation belongs to another customer.
            InvalidMessageError: If role is invalid or content is empty.
            MemoryStorageError: If storage operation fails.
        """
        pass

    @abc.abstractmethod
    def get_history(
        self,
        conversation_id: str,
        customer_id: str,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Retrieves message history for a conversation in chronological order.

        Parameters:
            conversation_id (str): ID of the target conversation.
            customer_id (str): Trusted customer ID.
            limit (int, optional): Maximum number of recent messages to return.

        Returns:
            List[Message]: Latest messages ordered from oldest to newest.

        Raises:
            ConversationNotFoundError: If conversation does not exist.
            CustomerMismatchError: If conversation belongs to another customer.
            MemoryStorageError: If storage operation fails.
        """
        pass

    @abc.abstractmethod
    def list_conversations(
        self,
        customer_id: str,
        limit: int = 50,
    ) -> List[dict]:
        """
        Retrieves all conversations belonging to the given customer.

        Parameters:
            customer_id (str): Trusted customer ID.
            limit (int): Maximum conversations to return (default 50).

        Returns:
            List[dict]: List of conversation summary dictionaries ordered by updated_at desc.
        """
        pass

    @abc.abstractmethod
    def delete_conversation(
        self,
        conversation_id: str,
        customer_id: str,
    ) -> bool:
        """
        Deletes a conversation and its messages for the given customer.

        Parameters:
            conversation_id (str): ID of the target conversation.
            customer_id (str): Trusted customer ID owning the conversation.

        Returns:
            bool: True if conversation was found and deleted; False otherwise.
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Releases any open database resources or connections."""
        pass
