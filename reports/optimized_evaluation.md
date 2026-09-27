# NovaBank Phase 10 Evaluation Report - Optimized / Development

**Generated:** 2026-09-27T21:47:15.684134
**Dataset Version:** v1
**Seed:** 42
**Mode:** offline
**Total Cases:** 158
**LLM Provider:** mock
**Embedding Model:** sentence-transformers/all-MiniLM-L6-v2

---

## Routing

| Metric | Value |
|--------|-------|
| Accuracy | 0.4367 |
| Total Evaluated | 158 |
| Correct | 69 |

### Per-Route Accuracy

| Route | Accuracy |
|-------|----------|
| BOTH | 0.1429 |
| RAG | 0.5714 |
| TOOL | 0.2267 |
| UNSUPPORTED | 0.9500 |

### Confusion Matrix

| Expected \ Predicted | BOTH | RAG | TOOL | UNSUPPORTED |
|---|---|---|---|---|
| **BOTH** | 1 | 4 | 2 | 0 |
| **RAG** | 0 | 32 | 2 | 22 |
| **TOOL** | 0 | 0 | 17 | 58 |
| **UNSUPPORTED** | 0 | 0 | 1 | 19 |

## Tools

| Metric | Value |
|--------|-------|
| Selection Accuracy | 0.2317 |
| Execution Success Rate | 0.2317 |
| Precision | 0.9048 |
| Recall | 0.2317 |
| F1 | 0.3689 |
| Tool-Evaluable Cases | 82 |

## RAG Retrieval

| Metric | Value |
|--------|-------|
| Hit@1 | 0.4110 |
| Hit@3 | 0.5068 |
| Hit@5 | 0.5068 |
| MRR | 0.4566 |
| RAG-Evaluable Cases | 73 |

## Response Quality

| Metric | Value |
|--------|-------|
| Grounding Rate | 1.0000 |
| Evaluable Cases | 138 |

## Safety

| Metric | Value |
|--------|-------|
| Safety Success Rate | 1.0000 |
| Customer Isolation Rate | 1.0000 |

## Latency

| Metric | Value (ms) |
|--------|-----------|
| Min | 1.69 |
| Mean | 18.55 |
| Median | 3.41 |
| p50 | 3.41 |
| p95 | 31.19 |
| Max | 961.82 |
| Count | 158 |

## Failures

Total failures: 106

### EVAL-0097 (ACCOUNT_DETAILS)
**Query:** What type of accounts do I have?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_accounts'], got=[]

### EVAL-0189 (ACCOUNT_DETAILS)
**Query:** Tell me about my NovaBank accounts.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_accounts'], got=[]

### EVAL-0030 (BANKING_POLICY)
**Query:** How do I report a lost debit card?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['10_fraud_and_security_policy.md', '05_credit_card_policy.md', '12_general_banking_faq.md']

### EVAL-0078 (BANKING_POLICY)
**Query:** What is the minimum balance requirement?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['06_savings_account_policy.md', '12_general_banking_faq.md']

### EVAL-0020 (BANKING_POLICY)
**Query:** What are the ATM withdrawal limits?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0069 (BANKING_POLICY)
**Query:** How can I update my KYC details?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0134 (BANKING_POLICY)
**Query:** What is the process for linking Aadhaar with my account?
- Route: expected=RAG, got=TOOL
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0187 (BANKING_POLICY)
**Query:** What is the NEFT transfer limit?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0114 (BANKING_POLICY)
**Query:** What is the minimum balance requirement?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['06_savings_account_policy.md', '12_general_banking_faq.md']

### EVAL-0001 (BANKING_POLICY)
**Query:** What is the process for linking Aadhaar with my account?
- Route: expected=RAG, got=TOOL
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0102 (BANKING_POLICY)
**Query:** What are the timings for RTGS transfers?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=[]

### EVAL-0015 (BANKING_POLICY)
**Query:** What is the minimum balance requirement?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['06_savings_account_policy.md', '12_general_banking_faq.md']

### EVAL-0112 (CATEGORY_SPENDING)
**Query:** How much did I spend on entertainment?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0093 (CATEGORY_SPENDING)
**Query:** How much have I spent on travel?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0004 (CATEGORY_SPENDING)
**Query:** How much did I spend on food?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0072 (CATEGORY_SPENDING)
**Query:** What is my total food delivery expenditure?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0075 (CATEGORY_SPENDING)
**Query:** Show me my healthcare expenses.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0188 (CATEGORY_SPENDING)
**Query:** What did I spend on shopping this month?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0043 (CATEGORY_SPENDING)
**Query:** What are my utility bill payments this month?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0100 (CATEGORY_SPENDING)
**Query:** Show me my education-related spending.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]
