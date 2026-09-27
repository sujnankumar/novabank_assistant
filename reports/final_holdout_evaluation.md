# NovaBank Phase 10 Evaluation Report - Optimized / Holdout

**Generated:** 2026-09-27T22:54:36.324610
**Dataset Version:** v1
**Seed:** 42
**Mode:** offline
**Total Cases:** 42
**LLM Provider:** mock
**Embedding Model:** sentence-transformers/all-MiniLM-L6-v2

---

## Routing

| Metric | Value |
|--------|-------|
| Accuracy | 0.6190 |
| Total Evaluated | 42 |
| Correct | 26 |

### Per-Route Accuracy

| Route | Accuracy |
|-------|----------|
| BOTH | 0.0000 |
| RAG | 0.6667 |
| TOOL | 0.5500 |
| UNSUPPORTED | 1.0000 |

### Confusion Matrix

| Expected \ Predicted | BOTH | RAG | TOOL | UNSUPPORTED |
|---|---|---|---|---|
| **BOTH** | 0 | 2 | 0 | 0 |
| **RAG** | 0 | 10 | 0 | 5 |
| **TOOL** | 0 | 0 | 11 | 9 |
| **UNSUPPORTED** | 0 | 0 | 0 | 5 |

## Tools

| Metric | Value |
|--------|-------|
| Selection Accuracy | 0.4091 |
| Execution Success Rate | 0.4091 |
| Precision | 0.6923 |
| Recall | 0.4091 |
| F1 | 0.5143 |
| Tool-Evaluable Cases | 22 |

## RAG Retrieval

| Metric | Value |
|--------|-------|
| Hit@1 | 0.5000 |
| Hit@3 | 0.6000 |
| Hit@5 | 0.6000 |
| MRR | 0.5500 |
| RAG-Evaluable Cases | 20 |

## Response Quality

| Metric | Value |
|--------|-------|
| Grounding Rate | 1.0000 |
| Evaluable Cases | 37 |

## Safety

| Metric | Value |
|--------|-------|
| Safety Success Rate | 1.0000 |
| Customer Isolation Rate | 1.0000 |

## Latency

| Metric | Value (ms) |
|--------|-----------|
| Min | 1.56 |
| Mean | 22.60 |
| Median | 16.25 |
| p50 | 16.25 |
| p95 | 53.92 |
| Max | 106.61 |
| Count | 42 |

## Failures

Total failures: 23

### EVAL-0176 (BANKING_POLICY)
**Query:** What are the charges for not maintaining minimum balance?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['06_savings_account_policy.md', '12_general_banking_faq.md']

### EVAL-0146 (BANKING_POLICY)
**Query:** What are the rules for fixed deposits?
- RAG: expected=['09_account_management_policy.md', '12_general_banking_faq.md'], got=['07_fixed_deposit_policy.md', '12_general_banking_faq.md']

### EVAL-0074 (CATEGORY_SPENDING)
**Query:** How much went to bills this month?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0161 (CATEGORY_SPENDING)
**Query:** What is my total food delivery expenditure?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0157 (CHECK_BALANCE)
**Query:** How much money is in my account?
- Tools: expected=['get_balance'], got=['get_accounts']

### EVAL-0109 (CREDIT_CARD_INFORMATION)
**Query:** What are the eligibility criteria for your credit cards?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['05_credit_card_policy.md'], got=[]

### EVAL-0014 (CREDIT_CARD_INFORMATION)
**Query:** What credit cards do you offer?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['05_credit_card_policy.md'], got=[]

### EVAL-0095 (CUSTOMER_PROFILE)
**Query:** Update my communication preference to WhatsApp.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_customer_details'], got=[]

### EVAL-0037 (FD_INFORMATION)
**Query:** What FD options are available?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['07_fixed_deposit_policy.md'], got=[]

### EVAL-0042 (GENERAL_BANKING_QUERY)
**Query:** What services does NovaBank provide?
- RAG: expected=['12_general_banking_faq.md'], got=[]

### EVAL-0174 (GENERAL_BANKING_QUERY)
**Query:** Good morning, can I speak to someone?
- RAG: expected=['12_general_banking_faq.md'], got=[]

### EVAL-0041 (GENERAL_BANKING_QUERY)
**Query:** Tell me something about banking.
- RAG: expected=['12_general_banking_faq.md'], got=[]

### EVAL-0151 (LOAN_ELIGIBILITY)
**Query:** Check if I can get a two-wheeler loan.
- Route: expected=BOTH, got=RAG
- Tools: expected=['check_loan_eligibility'], got=[]

### EVAL-0066 (LOAN_ELIGIBILITY)
**Query:** Would I qualify for an education loan?
- Route: expected=BOTH, got=RAG
- Tools: expected=['check_loan_eligibility'], got=[]

### EVAL-0048 (MERCHANT_SPENDING)
**Query:** Show me my IRCTC transactions.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transactions'], got=[]

### EVAL-0031 (MERCHANT_SPENDING)
**Query:** Show me all my Flipkart purchases.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transactions'], got=[]

### EVAL-0025 (MONTHLY_SPENDING)
**Query:** Show me month-wise spending for the last 3 months.
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0193 (MONTHLY_SPENDING)
**Query:** What was my total spending in August?
- Route: expected=TOOL, got=UNSUPPORTED
- Tools: expected=['get_transaction_summary'], got=[]

### EVAL-0088 (SAVINGS_INFORMATION)
**Query:** What savings account options do you have?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['06_savings_account_policy.md'], got=[]

### EVAL-0039 (SAVINGS_INFORMATION)
**Query:** What are the features of your savings accounts?
- Route: expected=RAG, got=UNSUPPORTED
- RAG: expected=['06_savings_account_policy.md'], got=[]
