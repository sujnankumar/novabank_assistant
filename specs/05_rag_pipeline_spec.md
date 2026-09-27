# Phase 5 — RAG Pipeline Specification

## 1. Overview

### Project
AI-Powered Banking Customer Query Assistant

### Bank
NovaBank

### Phase
5 — RAG Pipeline

### Status
Planned

---

## 2. Purpose

This phase implements the Retrieval-Augmented Generation (RAG) retrieval pipeline for NovaBank's general banking knowledge.

The RAG pipeline must allow the future AI system to retrieve relevant information from the existing NovaBank Knowledge Base.

The pipeline will:

1. Load the existing Markdown knowledge-base documents.
2. Split documents into meaningful chunks.
3. Generate embeddings for each chunk.
4. Store embeddings in a local Qdrant vector collection.
5. Preserve document and section metadata.
6. Convert a user query into an embedding.
7. Retrieve the most relevant knowledge-base chunks.
8. Return structured retrieval results.

This phase implements **retrieval only**.

The RAG pipeline must NOT generate the final natural-language answer.

---

## 3. Dependencies

Phase 5 depends on:

- Phase 2 — Knowledge Base
- Phase 3 — Mock Banking APIs
- Phase 4 — Banking Tools

The primary input for this phase is the existing:

```text
knowledge_base/
```
directory.

The existing synthetic NovaBank banking data must NOT be used as RAG documents.

Customer-specific information such as:
- Account balances
- Transactions
- Customer profiles
- Personal details
- Loan eligibility for a particular customer

must continue to come from the Banking Tools.

---

## 4. RAG Responsibility

The system must maintain a clear separation:

```text
General Banking Knowledge
        ↓
       RAG
        ↓
Policy / Product / FAQ information


Customer-Specific Banking Information
        ↓
   Banking Tools
        ↓
Accounts / balances / transactions / eligibility
```

Examples of questions appropriate for RAG:
- What are the eligibility requirements for a home loan?
- What is NovaBank's fixed deposit policy?
- What are the rules for reporting a fraudulent transaction?
- What documents are required for a vehicle loan?
- How can I close my savings account?

Examples that must NOT be answered from the RAG knowledge base:
- What is my account balance?
- Show my recent transactions.
- Am I eligible for a loan?
- What is my account number?

Those require Banking Tools.

---

## 5. Knowledge Base Input

Use the existing NovaBank knowledge base.

Expected structure:

```text
knowledge_base/
├── 01_home_loan_policy.md
├── 02_personal_loan_policy.md
├── 03_education_loan_policy.md
├── 04_vehicle_loan_policy.md
├── 05_credit_card_policy.md
├── 06_savings_account_policy.md
├── 07_fixed_deposit_policy.md
├── 08_transaction_policy.md
├── 09_account_management_policy.md
├── 10_fraud_and_security_policy.md
├── 11_customer_service_policy.md
├── 12_general_banking_faq.md
└── metadata.json
```

Before implementation, inspect the actual knowledge-base structure and metadata.

Do not create replacement documents.

Do not rewrite the existing knowledge base.

Do not introduce real-bank policies.

---

## 6. Document Loading

Implement a document loader that:
- Loads `.md` files from the knowledge-base directory.
- Ignores unrelated files where appropriate.
- Reads UTF-8 Markdown content.
- Preserves the source filename.
- Preserves useful document metadata.
- Does not modify source documents.

The loader should return structured document objects.

Example:
```json
{
    "content": "...",
    "metadata": {
        "source": "01_home_loan_policy.md"
    }
}
```

If metadata exists in `metadata.json`, it should be preserved and associated with the relevant document.

---

## 7. Document Chunking

The Markdown documents must be split into smaller chunks before embedding.

Chunking must:
- Preserve semantic meaning.
- Prefer Markdown headings/sections as natural boundaries.
- Avoid splitting sentences unnecessarily.
- Preserve the source document.
- Preserve section information where available.

Use a configurable chunking strategy.

Required configuration:
```python
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
```

The implementation may use an appropriate text splitter, but the configuration must remain explicit and easy to modify.

The exact resulting number of chunks is data-dependent and must not be hardcoded.

---

## 8. Chunk Metadata

Every chunk must preserve metadata sufficient to identify its origin.

Minimum metadata:
```json
{
    "source": "01_home_loan_policy.md",
    "document_id": "01_home_loan_policy",
    "chunk_id": "01_home_loan_policy_chunk_001"
}
```

Where available, also preserve:
```json
{
    "section": "Eligibility Criteria"
}
```

Additional metadata may include:
- Document title
- Document type
- Section heading
- Chunk index

Do not store customer-specific data in chunk metadata.

---

## 9. Embedding Model

Use a local sentence-transformer embedding model.

Default model:
```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding model must:
- Run locally.
- Produce deterministic embeddings for the same input.
- Not require an external LLM API.
- Be configurable through application settings.

Do not use:
- OpenAI embeddings
- Anthropic embeddings
- Gemini embeddings
- Any paid external embedding API

unless explicitly approved in a future specification.

---

## 10. Embedding Generation

For every chunk:

```text
Chunk text
   ↓
Embedding model
   ↓
Vector representation
```

The pipeline must generate an embedding for each chunk.

The implementation must ensure that:
```text
number of embeddings == number of indexed chunks
```

No chunk may be silently skipped.

---

## 11. Qdrant Vector Store

Use Qdrant as the vector database.

The vector store must support:
- Adding document embeddings.
- Persisting the collection locally.
- Loading an existing collection.
- Similarity search.
- Returning chunk identifiers and metadata.

Recommended structure:

```text
qdrant_storage/
```

The collection and chunk payloads must be persisted in local storage mode in a reproducible format.

---

## 12. Vector Similarity

Use cosine similarity (`Distance.COSINE`).

```text
normalize embeddings
+
Distance.COSINE
```

The implementation must use the same normalization strategy for:
- Stored document embeddings.
- Query embeddings.

This ensures similarity scores are comparable.

---

## 13. Index Building

Provide a deterministic indexing operation.

Example:
```python
build_index()
```

The operation should:
- Load knowledge-base documents.
- Split documents into chunks.
- Generate embeddings.
- Build the Qdrant collection.
- Persist the collection.
- Persist chunk metadata and payloads.

Running the indexing operation again should rebuild the index consistently from the current knowledge base.

Do not append duplicate chunks to an existing index during a normal rebuild.

---

## 14. Query Embedding

For a user query:

```text
User query
    ↓
Embedding model
    ↓
Query vector
```

The same embedding model used during document indexing must be used for query embeddings.

---

## 15. Retrieval

Implement a retrieval function such as:

```python
retrieve(
    query: str,
    top_k: int = 5
)
```

The retrieval function must:
- Validate the query.
- Generate the query embedding.
- Search the Qdrant collection.
- Retrieve the top matching chunks.
- Return structured results.

Default:
```python
top_k = 5
```

`top_k` must be configurable.

---

## 16. Retrieval Result Schema

Each result should contain:

```json
{
    "chunk_id": "01_home_loan_policy_chunk_001",
    "content": "...",
    "score": 0.87,
    "metadata": {
        "source": "01_home_loan_policy.md",
        "document_id": "01_home_loan_policy",
        "section": "Eligibility Criteria"
    }
}
```

The exact score depends on the embedding model and query.

Do not hardcode or fabricate scores.

---

## 17. Result Ordering

Results must be returned in descending similarity order:

```text
Most relevant
      ↓
...
      ↓
Least relevant
```

The returned list must contain no duplicate chunk IDs.

---

## 18. Relevance Threshold

Implement an optional similarity threshold.

Example configuration:
```python
SIMILARITY_THRESHOLD = 0.35
```

The threshold must be configurable.

If threshold filtering is enabled:
```text
score >= threshold
```
results may be returned.

Results below the threshold should not be returned.

The system must not fabricate an answer when no relevant document is retrieved.

---

## 19. No-Result Behavior

If the query does not have sufficiently relevant information in the knowledge base, return:

```json
{
    "query": "...",
    "results": [],
    "retrieved": false
}
```

The retrieval layer must not generate a guessed answer.

The future answer-generation layer will decide how to communicate that information to the user.

---

## 20. RAG Pipeline API

Provide a clean Python interface for future phases.

Minimum interface:

```python
class RAGRetriever:

    def build_index(self) -> None:
        ...

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> list:
        ...
```

The exact implementation may use additional internal classes.

The public interface must remain simple.

---

## 21. Recommended Project Structure

Add a dedicated RAG package:

```text
app/
├── main.py
├── api/
├── repositories/
├── schemas/
├── services/
├── tools/
└── rag/
    ├── __init__.py
    ├── loader.py
    ├── chunker.py
    ├── embeddings.py
    ├── vector_store.py
    ├── retriever.py
    └── schemas.py
```

Supporting scripts:

```text
scripts/
└── build_rag_index.py
```

Persisted vector data:

```text
qdrant_storage/
```

Tests:

```text
tests/
├── test_rag_loader.py
├── test_rag_chunking.py
├── test_rag_embeddings.py
├── test_rag_vector_store.py
└── test_rag_retrieval.py
```

The exact structure may be adjusted if the existing project architecture requires it.

---

## 22. RAG Configuration

RAG configuration must be centralized.

At minimum:

```python
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

DEFAULT_TOP_K = 5

SIMILARITY_THRESHOLD = 0.35

KNOWLEDGE_BASE_DIR = "knowledge_base"
QDRANT_COLLECTION_NAME = "novabank_knowledge"
QDRANT_STORAGE_PATH = "qdrant_storage"
QDRANT_VECTOR_SIZE = 384
QDRANT_DISTANCE = "cosine"
```

Avoid hardcoding these values throughout the implementation.

---

## 23. Dependency Requirements

Add only the dependencies required for the RAG pipeline.

Expected dependencies include:
- `sentence-transformers`
- `qdrant-client`

An appropriate Markdown/text processing dependency may be used if necessary.

Do not introduce:
- LangChain
- LangGraph
- Agent frameworks
- LLM SDKs

unless explicitly required by this specification.

Keep the implementation lightweight and understandable.

---

## 24. Error Handling

The RAG pipeline must handle:

### Missing Knowledge Base
If the knowledge-base directory does not exist:
- Raise a clear configuration/file error.
- Do not silently create an empty knowledge base.

### Empty Documents
Empty Markdown files must not produce invalid embeddings.
- They should be skipped with a clear validation/logging message.

### Missing Vector Index
If retrieval is attempted before an index exists:
- Return a clear error indicating that the RAG index has not been built.
- Do not automatically create an index during every query.

### Invalid Query
Empty or whitespace-only queries must be rejected.

Example:
```text
""
"   "
```

### Invalid top_k
Values such as:
- `0`
- `-1`

must be rejected.

---

## 25. Determinism

Given:
- Same knowledge-base documents
- Same chunking configuration
- Same embedding model
- Same query

the retrieval pipeline should produce reproducible results.

The system must not use random retrieval behavior.

---

## 26. Testing Requirements

Create automated tests covering the entire pipeline.

### 26.1 Document Loader Tests
Test:
- Knowledge-base directory loading.
- Markdown file discovery.
- UTF-8 reading.
- Metadata association.
- Empty-document handling.
- Missing-directory handling.

### 26.2 Chunking Tests
Test:
- Documents are split into chunks.
- Chunk size configuration is respected.
- Chunk overlap is applied.
- Source metadata is preserved.
- Chunk IDs are unique.
- Section metadata is preserved where available.

### 26.3 Embedding Tests
Test:
- Embedding model loads successfully.
- Embeddings are generated for valid chunks.
- Embedding dimensions are consistent.
- Same text produces consistent embedding dimensions.

Do not require exact floating-point equality across different hardware environments.

### 26.4 Vector Store Tests
Test:
- Index creation.
- Index persistence.
- Index loading.
- Number of vectors matches number of chunks.
- Metadata persistence.
- Query search.

### 26.5 Retrieval Tests
Test known queries against the knowledge base.

Examples:
- What are the eligibility requirements for a home loan?
- What is the fixed deposit policy?
- How do I report a fraudulent transaction?
- What are the rules for a savings account?
- What are the requirements for a vehicle loan?

Verify that retrieved results come from relevant documents.

Do not require one exact chunk unless the knowledge base structure makes that deterministic.

### 26.6 No-Result Tests
Test queries that are outside the knowledge base.

Verify that:
```text
results == []
```
or the configured threshold behavior is correctly applied.

The system must not fabricate retrieved content.

### 26.7 Metadata Tests
Verify every returned result contains:
- Chunk ID
- Source
- Document ID
- Content
- Similarity score

where applicable.

### 26.8 Reproducibility Tests
Build the index and verify that:
- Chunk count remains consistent.
- Embedding dimensions remain consistent.
- Retrieval returns the same source documents for the same query under unchanged conditions.

---

## 27. Validation Script

Create:
```text
scripts/build_rag_index.py
```

The script must build the complete index.

It should provide clear output such as:

```text
Loading knowledge base...
Documents loaded: 12

Chunking documents...
Chunks created: <N>

Generating embeddings...
Embeddings generated: <N>

Building Qdrant collection...
Index vectors: <N>

Saving vector store...
Index saved successfully.
```

The exact chunk count must be discovered dynamically.

Do not hardcode an expected chunk count.

---

## 28. RAG Inspection Utility

Provide a simple way to inspect retrieval results for manual validation.

Example:
```python
results = retriever.retrieve(
    "What are the eligibility requirements for a home loan?",
    top_k=5
)
```

The output should make it easy to inspect:
- Source document
- Section
- Score
- Retrieved content

This is for development/evaluation only.

It must not generate an answer.

---

## 29. Phase Boundary

This phase MUST NOT implement:
- LLM answer generation
- Prompt templates
- Agent routing
- LangChain agents
- LangGraph
- Intent classification
- Conversation memory
- Chat API
- Jinja frontend
- Natural-language response generation
- Banking tool selection
- Customer-specific retrieval
- Real banking APIs
- External banking data

Those belong to later phases.

---

## 30. Important RAG/Data Separation Rule

The RAG pipeline must never treat the following as knowledge-base documents:
- `customers.json`
- `accounts.json`
- `transactions.json`
- `customer_profiles.json`

Customer-specific information must continue to be retrieved through Banking Tools.

The RAG pipeline is exclusively for the general NovaBank knowledge base.

---

## 31. Definition of Done

Phase 5 is complete only when:
- [ ] Existing knowledge-base Markdown files are loaded successfully.
- [ ] Documents are chunked with configurable size and overlap.
- [ ] Chunk metadata is preserved.
- [ ] Local embeddings are generated.
- [ ] Qdrant collection is created successfully.
- [ ] Qdrant collection and metadata are persisted.
- [ ] Existing collection can be loaded.
- [ ] Query embeddings use the same embedding model.
- [ ] Top-k similarity retrieval works.
- [ ] Results contain content, score, and metadata.
- [ ] Similarity threshold is configurable.
- [ ] No-result queries are handled safely.
- [ ] RAG tests pass.
- [ ] Existing Phase 3 tests still pass.
- [ ] Existing Phase 4 tests still pass.
- [ ] No LLM functionality is introduced.
- [ ] No agent functionality is introduced.
- [ ] No conversation memory is introduced.
- [ ] No frontend functionality is introduced.
- [ ] No customer-specific data is placed into the RAG index.
- [ ] The specification file is not modified during implementation.

---

## 32. Validation

After implementation, run:

```bash
pytest
```

All existing tests and all new RAG tests must pass.

Then run:

```bash
python scripts/build_rag_index.py
```

Verify that:
- All knowledge-base documents are discovered.
- Chunks are created.
- Embeddings are generated.
- Qdrant collection is created.
- Collection can be reloaded.
- Retrieval works for representative banking queries.
- No-result behavior works.
- Phase 3 APIs remain functional.
- Phase 4 Banking Tools remain functional.