"""
SQLite Conversation Memory Implementation
==========================================
Persistent SQLite storage for NovaBank conversation sessions and message history.
Enforces customer isolation, conversation integrity, deterministic ordering, and
bounded chronological history retrieval.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import List, Optional, Union
import uuid

from app.memory.config import CONVERSATION_DB_PATH, MAX_HISTORY_MESSAGES
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
    MemoryStorageError,
)
from app.memory.interface import ConversationMemory
from app.memory.models import Conversation, Message


class SQLiteConversationMemory(ConversationMemory):
    """SQLite-backed conversation memory implementation."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        max_history: int = MAX_HISTORY_MESSAGES,
    ):
        self.db_path = str(db_path or CONVERSATION_DB_PATH)
        self.max_history = max_history

        # Ensure directory exists for file-backed databases
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Establishes a connection configured with row factory and foreign keys."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to connect to SQLite database: {e}") from e

    def _init_db(self) -> None:
        """
        Idempotently initializes the database schema, constraints, and indexes.
        Safe to call repeatedly without wiping or resetting existing data.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 1. conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        customer_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)

                # 2. messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        customer_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        sequence_number INTEGER NOT NULL,
                        sources TEXT,
                        thought_process TEXT,
                        execution_time_ms REAL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
                        CHECK (role IN ('user', 'assistant')),
                        CHECK (length(trim(content)) > 0),
                        UNIQUE (conversation_id, sequence_number)
                    );
                """)

                # Backward-compatible migrations for existing SQLite tables
                cursor.execute("PRAGMA table_info(messages);")
                columns = [row["name"] for row in cursor.fetchall()]
                if "sources" not in columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN sources TEXT;")
                if "thought_process" not in columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN thought_process TEXT;")
                if "execution_time_ms" not in columns:
                    cursor.execute("ALTER TABLE messages ADD COLUMN execution_time_ms REAL;")

                # 3. Required indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conv_seq
                    ON messages(conversation_id, sequence_number);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conv_created
                    ON messages(conversation_id, created_at);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_customer
                    ON conversations(customer_id);
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Database schema initialization failed: {e}") from e

    def initialize_db(self) -> None:
        """Public alias for idempotent schema initialization."""
        self._init_db()

    def create_conversation(self, customer_id: str) -> Conversation:
        """
        Creates and persists a new conversation session for the given customer.
        """
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            raise CustomerMismatchError("A valid, non-empty customer_id is required.")

        clean_customer_id = customer_id.strip()
        conv_id = f"conv_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO conversations (conversation_id, customer_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?);
                    """,
                    (conv_id, clean_customer_id, now, now),
                )
                conn.commit()

            return Conversation(
                conversation_id=conv_id,
                customer_id=clean_customer_id,
                created_at=now,
                updated_at=now,
            )
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to create conversation: {e}") from e

    def get_conversation(
        self,
        conversation_id: str,
        customer_id: str,
    ) -> Optional[Conversation]:
        """
        Retrieves a conversation scoped by both conversation_id and customer_id.
        Returns None if not found or if customer_id does not match.
        """
        if not conversation_id or not customer_id:
            return None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT conversation_id, customer_id, created_at, updated_at
                    FROM conversations
                    WHERE conversation_id = ? AND customer_id = ?;
                    """,
                    (conversation_id.strip(), customer_id.strip()),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                return Conversation(
                    conversation_id=row["conversation_id"],
                    customer_id=row["customer_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to retrieve conversation: {e}") from e

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
        """
        # Validate inputs
        if not role or role not in ("user", "assistant"):
            raise InvalidMessageError(f"Invalid message role '{role}'. Role must be 'user' or 'assistant'.")

        if not isinstance(content, str) or not content.strip():
            raise InvalidMessageError("Message content cannot be empty or whitespace only.")

        clean_conv_id = (conversation_id or "").strip()
        clean_cust_id = (customer_id or "").strip()

        if not clean_conv_id:
            raise ConversationNotFoundError("A valid conversation_id is required.")
        if not clean_cust_id:
            raise CustomerMismatchError("A valid customer_id is required.")

        clean_content = content.strip()
        now = datetime.now(timezone.utc).isoformat()
        msg_id = f"msg_{uuid.uuid4().hex[:16]}"

        sources_json = json.dumps(sources) if sources is not None else None
        thought_json = json.dumps(thought_process) if thought_process is not None else None
        exec_ms_val = float(execution_time_ms) if execution_time_ms is not None else None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verify conversation exists and customer ownership
                cursor.execute(
                    "SELECT customer_id FROM conversations WHERE conversation_id = ?;",
                    (clean_conv_id,),
                )
                conv_row = cursor.fetchone()

                if conv_row is None:
                    raise ConversationNotFoundError(f"Conversation '{clean_conv_id}' not found.")

                if conv_row["customer_id"] != clean_cust_id:
                    raise CustomerMismatchError(
                        f"Customer '{clean_cust_id}' does not match conversation owner '{conv_row['customer_id']}'."
                    )

                # Determine next sequence number atomically
                cursor.execute(
                    "SELECT COALESCE(MAX(sequence_number), 0) + 1 AS next_seq FROM messages WHERE conversation_id = ?;",
                    (clean_conv_id,),
                )
                seq_row = cursor.fetchone()
                sequence_number = seq_row["next_seq"]

                # Insert message
                cursor.execute(
                    """
                    INSERT INTO messages (
                        message_id, conversation_id, customer_id, role, content, created_at, sequence_number,
                        sources, thought_process, execution_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        msg_id,
                        clean_conv_id,
                        clean_cust_id,
                        role,
                        clean_content,
                        now,
                        sequence_number,
                        sources_json,
                        thought_json,
                        exec_ms_val,
                    ),
                )

                # Update conversation updated_at
                cursor.execute(
                    "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?;",
                    (now, clean_conv_id),
                )

                conn.commit()

            return Message(
                message_id=msg_id,
                conversation_id=clean_conv_id,
                customer_id=clean_cust_id,
                role=role,
                content=clean_content,
                created_at=now,
                sequence_number=sequence_number,
                sources=sources,
                thought_process=thought_process,
                execution_time_ms=exec_ms_val,
            )
        except (ConversationNotFoundError, CustomerMismatchError, InvalidMessageError):
            raise
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to add message to conversation: {e}") from e

    def get_history(
        self,
        conversation_id: str,
        customer_id: str,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Retrieves message history for a conversation in chronological order.
        Returns the latest `limit` messages (defaults to self.max_history).
        """
        clean_conv_id = (conversation_id or "").strip()
        clean_cust_id = (customer_id or "").strip()

        if not clean_conv_id:
            raise ConversationNotFoundError("A valid conversation_id is required.")
        if not clean_cust_id:
            raise CustomerMismatchError("A valid customer_id is required.")

        effective_limit = self.max_history if limit is None else limit
        if effective_limit <= 0:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Verify conversation exists and verify customer ownership
                cursor.execute(
                    "SELECT customer_id FROM conversations WHERE conversation_id = ?;",
                    (clean_conv_id,),
                )
                conv_row = cursor.fetchone()

                if conv_row is None:
                    raise ConversationNotFoundError(f"Conversation '{clean_conv_id}' not found.")

                if conv_row["customer_id"] != clean_cust_id:
                    raise CustomerMismatchError(
                        f"Customer '{clean_cust_id}' is not authorized to access conversation '{clean_conv_id}'."
                    )

                # Query latest N messages and order chronologically (oldest to newest)
                cursor.execute(
                    """
                    SELECT message_id, conversation_id, customer_id, role, content, created_at, sequence_number,
                           sources, thought_process, execution_time_ms
                    FROM (
                        SELECT message_id, conversation_id, customer_id, role, content, created_at, sequence_number,
                               sources, thought_process, execution_time_ms
                        FROM messages
                        WHERE conversation_id = ? AND customer_id = ?
                        ORDER BY sequence_number DESC
                        LIMIT ?
                    )
                    ORDER BY sequence_number ASC;
                    """,
                    (clean_conv_id, clean_cust_id, effective_limit),
                )
                rows = cursor.fetchall()

                messages = []
                for r in rows:
                    raw_sources = r["sources"]
                    parsed_sources = None
                    if raw_sources:
                        try:
                            parsed_sources = json.loads(raw_sources)
                        except (ValueError, TypeError):
                            parsed_sources = None

                    raw_thought = r["thought_process"]
                    parsed_thought = None
                    if raw_thought:
                        try:
                            parsed_thought = json.loads(raw_thought)
                        except (ValueError, TypeError):
                            parsed_thought = None

                    raw_exec_time = r["execution_time_ms"]
                    exec_time = float(raw_exec_time) if raw_exec_time is not None else None

                    messages.append(
                        Message(
                            message_id=r["message_id"],
                            conversation_id=r["conversation_id"],
                            customer_id=r["customer_id"],
                            role=r["role"],
                            content=r["content"],
                            created_at=r["created_at"],
                            sequence_number=r["sequence_number"],
                            sources=parsed_sources,
                            thought_process=parsed_thought,
                            execution_time_ms=exec_time,
                        )
                    )
                return messages
        except (ConversationNotFoundError, CustomerMismatchError):
            raise
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to retrieve conversation history: {e}") from e

    def list_conversations(self, customer_id: str, limit: int = 50) -> List[dict]:
        """
        Retrieves all conversations belonging to the given customer ordered by updated_at desc.
        Computes conversation title from first user query and message counts.
        """
        clean_cust_id = (customer_id or "").strip()
        if not clean_cust_id:
            return []

        effective_limit = max(1, min(limit, 100))

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Clean up any abandoned empty conversations (0 messages) for this customer
                cursor.execute(
                    """
                    DELETE FROM conversations 
                    WHERE customer_id = ? 
                      AND conversation_id NOT IN (
                          SELECT DISTINCT conversation_id FROM messages WHERE customer_id = ?
                      );
                    """,
                    (clean_cust_id, clean_cust_id),
                )

                cursor.execute(
                    """
                    SELECT 
                        c.conversation_id,
                        c.customer_id,
                        c.created_at,
                        c.updated_at,
                        COUNT(m.message_id) AS message_count,
                        (
                            SELECT content 
                            FROM messages m1 
                            WHERE m1.conversation_id = c.conversation_id 
                              AND m1.role = 'user' 
                            ORDER BY m1.sequence_number ASC 
                            LIMIT 1
                        ) AS first_user_query,
                        (
                            SELECT content 
                            FROM messages m2 
                            WHERE m2.conversation_id = c.conversation_id 
                            ORDER BY m2.sequence_number DESC 
                            LIMIT 1
                        ) AS last_message
                    FROM conversations c
                    INNER JOIN messages m ON c.conversation_id = m.conversation_id
                    WHERE c.customer_id = ?
                    GROUP BY c.conversation_id
                    HAVING COUNT(m.message_id) > 0
                    ORDER BY c.updated_at DESC
                    LIMIT ?;
                    """,
                    (clean_cust_id, effective_limit),
                )
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    raw_title = r["first_user_query"]
                    if raw_title:
                        title = raw_title.strip()
                        if len(title) > 42:
                            title = title[:39] + "..."
                    else:
                        title = "New Conversation"

                    results.append({
                        "conversation_id": r["conversation_id"],
                        "customer_id": r["customer_id"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "title": title,
                        "message_count": r["message_count"],
                        "last_message": r["last_message"],
                    })
                return results
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to list conversations: {e}") from e

    def delete_conversation(self, conversation_id: str, customer_id: str) -> bool:
        """
        Deletes a conversation and its messages for the given customer.
        Returns True if deleted, False if conversation does not exist or customer mismatch.
        """
        clean_conv_id = (conversation_id or "").strip()
        clean_cust_id = (customer_id or "").strip()
        if not clean_conv_id or not clean_cust_id:
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT customer_id FROM conversations WHERE conversation_id = ?;",
                    (clean_conv_id,),
                )
                row = cursor.fetchone()
                if row is None or row["customer_id"] != clean_cust_id:
                    return False

                cursor.execute("DELETE FROM messages WHERE conversation_id = ?;", (clean_conv_id,))
                cursor.execute("DELETE FROM conversations WHERE conversation_id = ?;", (clean_conv_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            raise MemoryStorageError(f"Failed to delete conversation: {e}") from e

    def close(self) -> None:
        """No persistent background connection pool needed; connections are managed per transaction."""
        pass
