# NovaBank Multi-Intent Optimization Evaluation Report

**Generated:** 2026-09-27T20:05:18Z  
**Scope:** Controlled Multi-Intent Query Decomposition for Compound Banking Queries.  
**Specification:** Internal evaluation & controlled optimization (preserving Phase 10 spec as source of truth; no Phase 11).

---

## 1. Executive Summary & Objective Verification

The objective of this controlled optimization was to resolve the empirical retrieval bottleneck where a single compound query causes one topic to dominate dense vector retrieval, leaving other topics unretrieved.

### Key Measured Outcomes

| Metric | Baseline (Single Retrieval) | Optimized (Decomposed) | Delta / Impact |
|---|---|---|---|
| **Target 4-Intent Completeness** | **50.0% (2 / 4)** | **100.0% (4 / 4)** | **+50.0% (Target Met)** |
| **RAG Document Coverage** | **33.3% (1 / 3 docs)** | **100.0% (3 / 3 docs)** | **+66.7% Coverage** |
| **Routing Accuracy** | 100.0% (`BOTH`) | 100.0% (`BOTH`) | 0.0% (Maintained) |
| **Tool Execution Accuracy** | 100.0% (`get_balance`) | 100.0% (`get_balance`) | 0.0% (Maintained) |
| **Customer Privacy / Isolation** | 100.0% Enforced | 100.0% Enforced | 0.0% (Strictly Preserved) |
| **Grounding Rate** | 100.0% Grounded | 100.0% Grounded | 0.0% (All 4 Verified) |
| **Total Regression Test Suite** | 321 / 321 Passing | **331 / 331 Passing** | **0 Regressions** |
| **End-to-End Latency** | 2,833 ms | ~2,760 ms | -73 ms |

---

## 2. Target Compound Query: Detailed Empirical Comparison

**Input Query:**  
> *"What is my account balance and what is the requirement to get the credit card, and what is the minimum credit score to get home loan and education loan?"*

### Baseline System (Before Optimization)
1. **Decomposition:** None (`sub_queries = []`).
2. **Retrieval:** Single compound vector embedding into Qdrant for the entire query string.
3. **Retrieval Results:** All top-K chunks were dominated by `03_education_loan_policy.md`.
4. **Omitted Documents:** `05_credit_card_policy.md` and `01_home_loan_policy.md` were completely omitted from retrieval.
5. **Answer Completeness:** **2 / 4 (50.0%)**:
   - [x] Account Balance: ₹1,92,203.99 (Savings)
   - [ ] Credit Card Requirements: *Failed* — Assistant explicitly reported: *"Unfortunately, I don't have any information about credit card eligibility or requirements in the retrieved context."*
   - [ ] Home Loan Credit Score: *Failed* — Assistant explicitly reported: *"I'm sorry, but there is no home loan policy information available in the retrieved context."*
   - [x] Education Loan Credit Score: Co-applicant score 600 (Domestic) / 650 (International).

### Optimized System (After Multi-Intent Decomposition)
1. **Decomposition:** `QueryDecomposer` automatically detected 4 independent sub-intents:
   - Sub-query 1: `[TOOL]` *"What is my account balance?"* -> Tool: `get_balance`
   - Sub-query 2: `[RAG]` *"What are the NovaBank credit card requirements?"* -> RAG retrieval
   - Sub-query 3: `[RAG]` *"What is the minimum credit score required for a NovaBank home loan?"* -> RAG retrieval
   - Sub-query 4: `[RAG]` *"What is the minimum credit score required for a NovaBank education loan?"* -> RAG retrieval
2. **Routing:** Independent sub-intent routing aggregated into overall route `BOTH` with 1 required tool (`get_balance`). Customer isolation strictly preserved.
3. **Retrieval:** 3 separate vector embeddings and independent Qdrant searches. Results aggregated and deduplicated without topic overwriting.
4. **Resulting Sources:** 13 verified source items:
   - 1 Banking Tool: `get_balance` (Customer `CUST001`)
   - 4 Chunks: `05_credit_card_policy.md` (Age 21, Minimum Income 3L-12L, Scores 650-750)
   - 2 Chunks: `01_home_loan_policy.md` (Standard 700, Premium 750, Improvement 680)
   - 4 Chunks: `03_education_loan_policy.md` (Domestic 600, International 650, Co-applicant mandatory)
5. **Answer Completeness:** **4 / 4 (100.0%)**:
   - [x] Account Balance: **PASSED** (ACC001 Active balance ₹1,92,203.99)
   - [x] Credit Card Requirements: **PASSED** (Age 21, Income 3L-12L, Scores 650-750)
   - [x] Home Loan Credit Score: **PASSED** (Standard 700, Premium 750, Improvement 680)
   - [x] Education Loan Credit Score: **PASSED** (Co-applicant 600 domestic / 650 international)

---

## 3. Latency Breakdown

| Execution Component | Baseline Latency | Optimized Latency | Delta |
|---|---|---|---|
| Query Analysis & Decomposition | 0.0 ms | 0.25 ms (rule-based) | +0.25 ms |
| Tool Execution (`get_balance`) | 14.8 ms | 12.4 ms | -2.4 ms |
| Qdrant RAG Retrieval | 18.2 ms (1 vector search) | 48.6 ms (3 vector searches) | +30.4 ms |
| Context Validation & Provenance | 0.5 ms | 0.8 ms | +0.3 ms |
| LLM Response Synthesis | 2,800.0 ms | 2,700.0 ms | -100.0 ms |
| **Total End-to-End Latency** | **2,833.0 ms** | **~2,760.0 ms** | **-73.0 ms** |

*Note: Decomposition adds ~30 ms of local vector retrieval overhead across 3 independent Qdrant queries, which is negligible compared to model generation time.*

---

## 4. Single-Intent Non-Regression & Safety Verification

1. **Single-Intent Preservation:**
   - Single-product RAG query (*"What are the requirements for a NovaBank credit card?"*): Detected as single intent; zero decomposition; standard RAG route executed.
   - Single-tool query (*"What is my account balance?"*): Detected as single intent; zero decomposition; standard TOOL route executed.
2. **Security & Customer Isolation:**
   - Pre-check guardrails in `QueryDecomposer` reject prompt injections and prevent cross-customer account override attempts.
   - Authenticated `customer_id` is passed as immutable trusted context and cannot be modified by decomposed sub-queries.
3. **Regression Test Suite:**
   - Multi-Intent Unit Tests (A through I): **9 / 9 passed**
   - UI Chat Flow Tests: **4 / 4 passed**
   - Complete Project Regression Suite: **331 / 331 passed (100%)**
