# NovaBank Transaction Query Evaluation Report

**Evaluation Date:** 2026-09-28T02:50:12.848017  
**Total Test Cases:** 27  

---

## 1. Summary Metrics

| Metric | Accuracy (%) | Target | Status |
|---|---|---|---|
| **Limit Extraction Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Date-Range Extraction Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Category Extraction Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Combined Parameter Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Tool Selection Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Filtering Correctness Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Customer Isolation Accuracy** | 100.0% | 100.0% | ✅ Met |
| **Empty Result Handling Accuracy** | 100.0% | 100.0% | ✅ Met |

---

## 2. Test Case Breakdown

| Case ID | Test Case Name | Limit | Category | Date Range | Result |
|---|---|---|---|---|---|
| TXN-001 | Default limit recent transactions | 5 | None | None to None | ✅ |
| TXN-002 | Explicit limit: 8 recent transactions | 8 | None | None to None | ✅ |
| TXN-003 | Explicit limit: 20 recent transactions | 20 | None | None to None | ✅ |
| TXN-004 | Explicit limit: 3 recent transactions | 3 | None | None to None | ✅ |
| TXN-005 | Explicit limit: 10 transactions | 10 | None | None to None | ✅ |
| TXN-006 | Relative date: this month | 5 | None | 2026-09-01 to 2026-09-28 | ✅ |
| TXN-007 | Relative date: last month (previous calendar month) | 5 | None | 2026-08-01 to 2026-08-31 | ✅ |
| TXN-008 | Relative date: this year | 5 | None | 2026-01-01 to 2026-09-28 | ✅ |
| TXN-009 | Relative date: last year | 5 | None | 2025-01-01 to 2025-12-31 | ✅ |
| TXN-010 | Specific month: August (resolved to 2026) | 5 | None | 2026-08-01 to 2026-08-31 | ✅ |
| TXN-011 | Specific month and year: December 2025 | 5 | None | 2025-12-01 to 2025-12-31 | ✅ |
| TXN-012 | Explicit date range: June to August | 5 | None | 2026-06-01 to 2026-08-31 | ✅ |
| TXN-013 | Category filter: Food | 5 | Food | None to None | ✅ |
| TXN-014 | Category filter: Travel | 5 | Travel | None to None | ✅ |
| TXN-015 | Combined: limit 10 + category Food + this month | 10 | Food | 2026-09-01 to 2026-09-28 | ✅ |
| TXN-016 | Combined: limit 8 + last month | 8 | None | 2026-08-01 to 2026-08-31 | ✅ |
| TXN-017 | Combined: limit 10 + category Travel + in August | 10 | Travel | 2026-08-01 to 2026-08-31 | ✅ |
| TXN-018 | Combined: limit 20 + category Shopping + last year | 20 | Shopping | 2025-01-01 to 2025-12-31 | ✅ |
| TXN-019 | Empty result handling: unrecorded category/date | 5 | Insurance | 2025-08-01 to 2025-08-31 | ✅ |
| TXN-020 | Safety limit capping: 10,000 transactions capped to 100 | 100 | None | None to None | ✅ |
| TXN-021 | Customer isolation enforcement | 5 | None | None to None | ✅ |
| TXN-022 | Multi-intent: Balance + 8 transactions | 8 | None | None to None | ✅ |
| TXN-023 | Exact case: recent 6 food transactions | 6 | Food | None to None | ✅ |
| TXN-024 | Exact case: recent 7 transactions | 7 | None | None to None | ✅ |
| TXN-025 | Exact case: transactions that i spent on food | 5 | Food | None to None | ✅ |
| TXN-026 | Exact case: money spent on food summary | 5 | Food | None to None | ✅ |
| TXN-027 | Exact case: 10 food transactions this month | 10 | Food | 2026-09-01 to 2026-09-28 | ✅ |

---

## 3. Architecture & Security Invariants Verified

1. **Filtering Pipeline Ordering:**
   - Filters are applied strictly in the deterministic sequence:
     `ALL CUSTOMER TRANSACTIONS` $\rightarrow$ `DATE FILTER` $\rightarrow$ `CATEGORY FILTER` $\rightarrow$ `ACCOUNT FILTER` $\rightarrow$ `SORT DESCENDING` $\rightarrow$ `LIMIT` $\rightarrow$ `RETURN`.
   - Verified that slicing by limit never truncates valid records prior to category or date evaluation.

2. **Customer Isolation:**
   - `customer_id` is supplied solely by authenticated server session context.
   - User inputs or prompts attempting to inject `CUST002` while authenticated as `CUST001` are blocked without data leakage.

3. **Dynamic Response Generation:**
   - The assistant renders a clean GitHub Flavored Markdown table (`| Date | Description | Category | Amount | Type |`).
   - No hardcoded row slices (`[:5]`) exist in response synthesis; limit is dynamic and derived deterministically from the user query.
   - Over-limit requests (>100) are capped cleanly at `MAX_TRANSACTION_LIMIT` with explanatory user notes.
