# NovaBank AI-Powered Banking Customer Query Assistant 🏦

An enterprise-grade, conversational AI platform designed to deliver safe, grounded, context-aware banking assistance for modern digital banking.

Built with **Zero Hallucination for Financial Facts**, strict customer data isolation, hybrid execution (Deterministic Tools + Semantic RAG), and multi-turn stateful memory management.

---

## 🚀 Key Highlights & Capabilities

- **Deterministic Financial Actions**: LLMs never guess or fabricate balances, transactions, account numbers, or loan records. All financial data is fetched via deterministic repository tools with referential integrity.
- **Strict Customer Isolation**: Multi-tenant session state and tool executions are tied to validated customer context (`CUST001`–`CUST010`), preventing cross-customer leakage.
- **Grounded Policy RAG**: Bank policy questions (e.g. loan eligibility, interest rates, security guidelines) are answered using Qdrant vector retrieval with cited sources.
- **Hybrid Multi-Intent Execution**: Queries requiring both transactional knowledge and bank policy (e.g., *"What is my balance and what are your home loan interest rates?"*) are handled concurrently via a hybrid routing graph.
- **Interactive Web Interface**: Clean, responsive UI with customer switching, quick actions, conversation history, and source attribution badges.
- **Enterprise Evaluation Framework**: Comprehensive offline evaluation suite measuring routing accuracy, grounding, retrieval precision, and answer correctness.

---

## 🏛️ System Architecture

```text
User Browser / UI
       │  (REST / JSON)
       ▼
 FastAPI Service (/api/chat, /api/conversations)
       │
       ▼
 Memory Orchestrator (SQLite conversation persistence)
       │
       ▼
 Banking Orchestrator & Intent Router
    ├── Tool Execution Agent (Accounts, Loans, Transactions, Customers)
    └── RAG Policy Retriever (Qdrant Vector Database, MiniLM-L6-v2)
       │
       ▼
 Grounded Response Synthesizer (OpenRouter / OpenAI / Rule-based Fallback)
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Agent Orchestration**: LangGraph / LangChain Core stateful orchestration
- **Vector Search & Embeddings**: Qdrant (`qdrant-client`), Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Memory & Storage**: SQLite, JSON repositories
- **Frontend**: Jinja2 Templates, HTML5, Vanilla CSS, Vanilla JavaScript
- **Testing & Evaluation**: Pytest, automated benchmark suites

---

## 📦 Project Structure

```
├── app/
│   ├── agents/          # Orchestrator, Router, and LLM synthesis
│   ├── api/             # FastAPI routing endpoints (chat, accounts, loans, etc.)
│   ├── evaluation/      # Metrics and evaluation logic
│   ├── memory/          # SQLite persistence & multi-turn memory models
│   ├── rag/             # Document loader, chunker, embeddings, Qdrant store
│   ├── repositories/    # Data access layer for accounts, loans, transactions
│   ├── schemas/         # Pydantic data schemas
│   ├── services/        # Business logic services
│   ├── static/          # CSS stylesheets and client JavaScript
│   ├── templates/       # Jinja2 web UI templates
│   └── tools/           # Banking tools callable by the orchestrator
├── data/                # Synthetic banking dataset (accounts, transactions, loans)
├── evaluation/          # Evaluation test cases, ground truth, and routing mapping
├── knowledge_base/      # Bank policy documents (markdown) & metadata
├── reports/             # Benchmark results and evaluation reports
├── scripts/             # Data generation, RAG indexing, evaluation runners
├── specs/               # Engineering specifications
├── tests/               # Test suites (unit, integration, API, security, UI)
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables configuration template
```

---

## ⚙️ Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/sujnankumar/novabank_assistant.git
cd novabank_assistant
```

### 3. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update `.env` with your API configuration:
- Set `LLM_PROVIDER=openrouter` (or `openai` / `mock`)
- Add your `LLM_API_KEY`

### 5. Build RAG Vector Index
Generate the Qdrant vector index from the bank policy documents:
```bash
python scripts/build_rag_index.py
```

### 6. Run the Application
Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
Open your browser at `http://127.0.0.1:8000` to interact with the NovaBank assistant.

---

## 🧪 Testing & Evaluation

### Run Test Suite
```bash
pytest
```

### Run Evaluation Suite
```bash
python scripts/run_evaluation.py
```

### Run Performance Benchmarks
```bash
python scripts/run_benchmark.py
```

---

## 📄 License
MIT License.
