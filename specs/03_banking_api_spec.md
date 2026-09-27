# Phase 3 — Mock Banking API Specification

**Project:** AI-Powered Banking Customer Query Assistant  
**Bank:** NovaBank  
**Phase:** 3 — Mock Banking APIs  
**Status:** Specification  
**Development Method:** Spec-Driven Development  

---

## 1. Purpose

This specification defines the Mock Banking API layer for the NovaBank AI Banking Assistant.

The API layer provides controlled access to the existing synthetic banking data.

The APIs will later be consumed by Banking Tools, Loan Tools, Customer Insights Tools, and Agents.

The API layer MUST NOT use an LLM to generate or determine factual banking data.

All customer-specific information must come from the structured synthetic data.

---

## 2. Existing Data Sources

The API implementation must use the existing datasets:

```text
data/
├── customers.json
├── accounts.json
├── transactions.json
├── loans.json
├── products.json
└── customer_profiles.json
```

These files are the source data for this phase.

Do not create a second conflicting source of truth.

Do not hardcode customer balances, transactions, loan products, or customer profiles inside route handlers.

---

## 3. Technology Requirements

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn

### Data Access

For the MVP, the APIs may read the existing JSON datasets through a service/repository layer.

Do NOT introduce a database migration in this phase unless required by the existing project architecture.

The API implementation should make the data-access layer modular so that SQLite/PostgreSQL/MongoDB can be introduced later without rewriting the API routes.

---

## 4. API Base URL

Local development:
```text
http://localhost:8000
```

API prefix:
```text
/api
```

All banking endpoints must use the `/api` prefix.

---

## 5. API Design Principles

The following principles are mandatory:

- Customer-specific data must only be returned for the requested customer.
- A customer must never be able to access another customer's account or transaction data through an ID mismatch.
- All IDs must be validated.
- Unknown customers must return an appropriate HTTP error.
- Missing accounts must return an appropriate HTTP error.
- The API must never fabricate financial values.
- Balances must come from structured account data.
- Transactions must come from structured transaction data.
- Loan information must come from `loans.json`.
- Banking product information must come from `products.json`.
- Customer profile information must come from `customer_profiles.json`.
- Financial values must be returned as structured data.
- The API must not contain LLM logic.
- The API must not contain agent-routing logic.
- The API must not perform RAG.
- Business logic should be placed in service/repository modules rather than directly inside route handlers.

---

## 6. API Endpoints

The following endpoints must be implemented:

- `GET  /api/customers/{customer_id}`
- `GET  /api/customers/{customer_id}/profile`
- `GET  /api/accounts/{customer_id}`
- `GET  /api/accounts/{customer_id}/balance`
- `GET  /api/accounts/{customer_id}/transactions`
- `GET  /api/accounts/{customer_id}/transactions/summary`
- `GET  /api/loans`
- `GET  /api/loans/{loan_id}`
- `POST /api/loans/check-eligibility`
- `GET  /api/products`
- `GET  /api/interest-rates`

---

## 7. GET /api/customers/{customer_id}

### Purpose
Return basic information about a synthetic NovaBank customer.

### Example Request
```http
GET /api/customers/CUST001
```

### Success Response
```json
{
  "customer_id": "CUST001",
  "name": "Synthetic Customer",
  "age": 28,
  "gender": "Male",
  "city": "Mangalore",
  "occupation": "Software Engineer",
  "monthly_income": 75000,
  "credit_score": 765,
  "consent": true
}
```

The exact fields must match the existing `customers.json` schema.

### Errors
If the customer does not exist:

**404 Not Found**

Example:
```json
{
  "detail": "Customer not found"
}
```

---

## 8. GET /api/customers/{customer_id}/profile

### Purpose
Return the customer's profile and personalization-related information.

### Data Source
`data/customer_profiles.json`

### Example Request
```http
GET /api/customers/CUST001/profile
```

### Expected Response
Return the profile associated with the requested customer.

The response must not return another customer's profile.

### Errors
- **Unknown customer:** `404 Not Found`
- **Profile missing:** `404 Not Found`

---

## 9. GET /api/accounts/{customer_id}

### Purpose
Return all accounts belonging to a customer.

### Example Request
```http
GET /api/accounts/CUST001
```

### Response
```json
{
  "customer_id": "CUST001",
  "accounts": [
    {
      "account_id": "ACC001",
      "customer_id": "CUST001",
      "account_type": "Savings",
      "balance": 82450.50,
      "currency": "INR",
      "status": "ACTIVE",
      "opened_date": "2024-01-15"
    }
  ]
}
```

The exact account fields must follow `accounts.json`.

### Rules
- Return only accounts belonging to the requested customer.
- Do not return accounts belonging to another customer.
- If the customer does not exist, return `404`.
- If the customer exists but has no accounts, return an empty account list.

---

## 10. GET /api/accounts/{customer_id}/balance

### Purpose
Return the current account balance information.

### Example Request
```http
GET /api/accounts/CUST001/balance
```

### Response
```json
{
  "customer_id": "CUST001",
  "accounts": [
    {
      "account_id": "ACC001",
      "account_type": "Savings",
      "balance": 82450.50,
      "currency": "INR",
      "status": "ACTIVE"
    }
  ],
  "total_balance": 82450.50,
  "currency": "INR"
}
```

If the customer has multiple active accounts, calculate the total only from the actual account balances.

Do not ask an LLM to calculate or generate the balance.

### Rules
- Only active accounts should contribute to `total_balance`.
- The underlying account balances must come directly from the structured data.
- Do not modify balances.
- Do not generate random values.

---

## 11. GET /api/accounts/{customer_id}/transactions

### Purpose
Return transaction history for a customer.

### Example Request
```http
GET /api/accounts/CUST001/transactions
```

### Optional Query Parameters
- `limit`
- `offset`
- `transaction_type`
- `category`
- `merchant`
- `start_date`
- `end_date`

**Examples:**
```http
GET /api/accounts/CUST001/transactions?limit=5
```

```http
GET /api/accounts/CUST001/transactions?category=Food
```

```http
GET /api/accounts/CUST001/transactions?start_date=2026-09-01&end_date=2026-09-24
```

### Response
```json
{
  "customer_id": "CUST001",
  "transactions": [
    {
      "transaction_id": "TXN001",
      "customer_id": "CUST001",
      "account_id": "ACC001",
      "date": "2026-09-20",
      "type": "DEBIT",
      "amount": 1299.00,
      "merchant": "Amazon",
      "category": "Shopping",
      "description": "Online purchase",
      "status": "SUCCESS"
    }
  ],
  "count": 1
}
```

### Rules
- Return only transactions belonging to the requested customer.
- Verify that the transaction's account belongs to the same customer.
- Default ordering should be newest transaction first.
- `limit` must have a reasonable maximum.
- Invalid date ranges must return a validation error.
- Invalid customer IDs must return `404`.

---

## 12. GET /api/accounts/{customer_id}/transactions/summary

### Purpose
Provide a summary of customer transactions.

This endpoint is intended to support the future Customer Insights Agent.

### Example Request
```http
GET /api/accounts/CUST001/transactions/summary
```

### Optional Query Parameters
- `start_date`
- `end_date`

### Response
```json
{
  "customer_id": "CUST001",
  "period": {
    "start_date": "2026-09-01",
    "end_date": "2026-09-24"
  },
  "total_credits": 85000.00,
  "total_debits": 12450.00,
  "transaction_count": 18,
  "category_spending": {
    "Food": 3200.00,
    "Shopping": 4500.00,
    "Travel": 1800.00,
    "Entertainment": 950.00
  }
}
```

The exact values must be calculated from the transaction dataset.

The API must not invent summary values.

---

## 13. GET /api/loans

### Purpose
Return available NovaBank loan products.

### Example Request
```http
GET /api/loans
```

### Optional Query Parameter
- `loan_type`

**Example:**
```http
GET /api/loans?loan_type=Home Loan
```

### Response
```json
{
  "loans": [
    {
      "loan_id": "LOAN001",
      "loan_name": "NovaBank Home Loan",
      "loan_type": "Home Loan",
      "minimum_amount": 500000,
      "maximum_amount": 10000000,
      "interest_rate": 8.5
    }
  ]
}
```

The complete fields may be returned according to the existing `loans.json` schema.

---

## 14. GET /api/loans/{loan_id}

### Purpose
Return detailed information about a specific loan product.

### Example Request
```http
GET /api/loans/LOAN001
```

### Response
Return the corresponding loan product from `loans.json`.

### Errors
- **Unknown loan:** `404 Not Found`

---

## 15. POST /api/loans/check-eligibility

### Purpose
Perform a deterministic simulated loan eligibility check using customer information and loan eligibility rules.

This is a demonstration-only eligibility system.

It is NOT a real lending decision.

### Request
```json
{
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "requested_amount": 1500000
}
```

### Eligibility Inputs

Use:

**Customer:**
- age
- monthly income
- credit score

**Loan:**
- minimum income
- minimum credit score
- minimum age
- maximum age
- minimum amount
- maximum amount

### Response — Eligible
```json
{
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "eligible": true,
  "requested_amount": 1500000,
  "reasons": [
    "Minimum income requirement satisfied",
    "Minimum credit score requirement satisfied",
    "Age requirement satisfied",
    "Requested amount is within the permitted range"
  ],
  "disclaimer": "This is a simulated eligibility result for demonstration purposes and is not a real lending decision."
}
```

### Response — Not Eligible
```json
{
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "eligible": false,
  "requested_amount": 1500000,
  "reasons": [
    "Credit score is below the minimum required score"
  ],
  "disclaimer": "This is a simulated eligibility result for demonstration purposes and is not a real lending decision."
}
```

### Rules
- Eligibility must be deterministic.
- The LLM must NOT determine eligibility.
- The API must not claim that the result represents actual banking approval.

---

## 16. GET /api/products

### Purpose
Return available NovaBank banking products.

### Data Source
`data/products.json`

### Optional Query Parameter
- `product_type`

**Examples:**
```http
GET /api/products?product_type=Savings
GET /api/products?product_type=Credit Card
```

Return structured product information.

---

## 17. GET /api/interest-rates

### Purpose
Return current synthetic NovaBank interest rates from the structured product data.

### Optional Query Parameters
- `product_type`

**Examples:**
```http
GET /api/interest-rates
GET /api/interest-rates?product_type=Home Loan
```

The API must retrieve rates from the existing structured datasets.

It must not contain independently hardcoded rates that could conflict with `loans.json` or `products.json`.

---

## 18. HTTP Status Codes

Use appropriate HTTP status codes:
- `200 OK`
- `201 Created` — only if a future endpoint creates data
- `400 Bad Request`
- `404 Not Found`
- `422 Unprocessable Entity`
- `500 Internal Server Error`

For this phase, the primary successful response is:
- `200 OK`

Use:
- `404` when a requested customer, account, loan, or product does not exist.
- `422` for invalid request parameters or invalid Pydantic request data.

---

## 19. Error Response Format

Use a consistent error structure.

Example:
```json
{
  "detail": "Customer not found"
}
```

Do not expose stack traces or internal implementation details to API consumers.

---

## 20. Data Access Architecture

Do not place all data-access logic inside `main.py`.

Use a layered structure similar to:

```text
app/
├── main.py
│
├── api/
│   ├── customers.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── loans.py
│   └── products.py
│
├── services/
│   ├── customer_service.py
│   ├── account_service.py
│   ├── transaction_service.py
│   ├── loan_service.py
│   └── product_service.py
│
├── repositories/
│   └── json_repository.py
│
└── schemas/
    ├── customer.py
    ├── account.py
    ├── transaction.py
    ├── loan.py
    └── product.py
```

The exact structure may be adapted to the existing project, but separation of concerns must be maintained.

---

## 21. Pydantic Schemas

Use Pydantic models for API request and response validation.

At minimum define schemas for:
- `Customer`
- `CustomerProfile`
- `Account`
- `Transaction`
- `TransactionSummary`
- `LoanProduct`
- `LoanEligibilityRequest`
- `LoanEligibilityResponse`
- `BankingProduct`
- `InterestRate`

Avoid returning arbitrary dictionaries where a well-defined response schema is appropriate.

---

## 22. Customer Data Isolation

This is a critical requirement.

For every customer-specific endpoint:
- `/api/customers/{customer_id}`
- `/api/accounts/{customer_id}`
- `/api/accounts/{customer_id}/balance`
- `/api/accounts/{customer_id}/transactions`
- `/api/accounts/{customer_id}/transactions/summary`

the implementation must filter data by the requested `customer_id`.

For transactions, **BOTH** conditions must be satisfied:
```text
transaction.customer_id == requested_customer_id
```
and:
```text
transaction.account_id belongs to requested_customer_id
```

If these conditions are inconsistent, the transaction must not be returned.

---

## 23. No LLM Dependency

Phase 3 must work without any LLM API key.

The following must work completely offline:
- `GET  /api/customers/...`
- `GET  /api/accounts/...`
- `GET  /api/accounts/.../balance`
- `GET  /api/accounts/.../transactions`
- `GET  /api/accounts/.../transactions/summary`
- `GET  /api/loans`
- `GET  /api/loans/...`
- `POST /api/loans/check-eligibility`
- `GET  /api/products`
- `GET  /api/interest-rates`

This is important because the API layer must remain deterministic.

---

## 24. API Documentation

FastAPI's automatic documentation must be enabled.

The following should work:
- `/docs`
- `/redoc`

Each endpoint should have:
- summary
- description
- request schema
- response schema
- error responses

---

## 25. Testing Requirements

Create automated tests for the API layer.

Use pytest and FastAPI's test client.

At minimum test:

### Customer API
- Existing customer returns 200.
- Unknown customer returns 404.

### Account API
- Existing customer returns correct accounts.
- Unknown customer returns 404.
- Accounts belong to requested customer.

### Balance API
- Existing customer returns correct balance.
- Balance is derived from account data.
- Unknown customer returns 404.

### Transaction API
- Existing customer returns transactions.
- Transactions belong to requested customer.
- Account/customer relationship is respected.
- Limit works.
- Category filtering works.
- Date filtering works.
- Unknown customer returns 404.

### Transaction Summary
- Total credits are calculated correctly.
- Total debits are calculated correctly.
- Category totals are correct.

### Loan API
- Loan list works.
- Loan lookup works.
- Unknown loan returns 404.

### Loan Eligibility
- Eligible customer returns `eligible=true`.
- Ineligible customer returns `eligible=false`.
- Income rules work.
- Credit score rules work.
- Age rules work.
- Loan amount limits work.
- Unknown customer returns 404.
- Unknown loan returns 404.

### Product API
- Product listing works.
- Product filtering works.

### Interest Rate API
- Rates match structured data.

---

## 26. Acceptance Criteria

Phase 3 is considered COMPLETE only when all of the following are true:

### API functionality
- [ ] All specified endpoints are implemented.
- [ ] All endpoints return structured JSON.
- [ ] Pydantic schemas are used.
- [ ] Appropriate HTTP status codes are used.
- [ ] Errors are handled consistently.

### Data integrity
- [ ] APIs use the existing synthetic datasets.
- [ ] No customer-specific data is hardcoded.
- [ ] No balances are fabricated.
- [ ] No transactions are fabricated.
- [ ] Loan data matches `loans.json`.
- [ ] Product data matches `products.json`.

### Security/data isolation
- [ ] Customer data is isolated.
- [ ] Transaction/customer relationships are validated.
- [ ] Another customer's data cannot be returned by changing an ID.
- [ ] No real financial information is introduced.

### Architecture
- [ ] Routes are separated from business logic.
- [ ] Data access is separated from route handlers.
- [ ] Pydantic schemas are used.
- [ ] API implementation does not depend on an LLM.

### Testing
- [ ] Automated tests exist.
- [ ] All tests pass.
- [ ] Error cases are tested.
- [ ] Eligibility rules are tested.
- [ ] Transaction filtering is tested.

### Documentation
- [ ] `/docs` works.
- [ ] `/redoc` works.
- [ ] Endpoint descriptions are available.

---

## 27. Explicit Non-Goals

The following must NOT be implemented during Phase 3:
- No LLM integration.
- No LangChain.
- No LangGraph.
- No agents.
- No agent orchestration.
- No RAG.
- No embeddings.
- No FAISS.
- No vector database.
- No conversation memory.
- No chatbot logic.
- No Jinja frontend.
- No frontend JavaScript.
- No authentication system.
- No real banking API integration.
- No real financial services.
- No real customer data.

These belong to later phases.

---

## 28. Future Consumers

The APIs created in this phase will later be consumed by tools.

**Example:**
```text
User
 ↓
Orchestrator
 ↓
Banking Agent
 ↓
get_balance()
 ↓
GET /api/accounts/{customer_id}/balance
 ↓
Structured API response
 ↓
LLM response generation
```

**Another example:**
```text
User
 ↓
Customer Insights Agent
 ↓
calculate_category_spending()
 ↓
GET /api/accounts/{customer_id}/transactions/summary
 ↓
Structured transaction data
 ↓
LLM response
```

**Loan example:**
```text
User
 ↓
Loan Agent
 ↓
check_loan_eligibility()
 ↓
POST /api/loans/check-eligibility
 ↓
Deterministic eligibility result
 ↓
LLM explains result
```

---

## 29. Implementation Rule

When implementing this specification:
1. Read this entire specification first.
2. Inspect the existing project and existing data files.
3. Do not modify the synthetic datasets unless a genuine data-integrity issue is discovered.
4. Do not modify the knowledge base.
5. Do not implement later phases.
6. Implement only Phase 3.
7. Write automated tests.
8. Run all tests.
9. Fix failures.
10. Verify the APIs manually through `/docs`.
11. Report exactly what was implemented and tested.

Do not silently change API contracts defined in this specification.

If an implementation detail is ambiguous, choose the simplest implementation that satisfies the specification without adding unnecessary dependencies or architecture.

---

## 30. Definition of Done

Phase 3 is complete when:

```text
Synthetic Data
      ↓
Mock Banking APIs
      ↓
All tests passing
      ↓
API documentation working
      ↓
Data isolation verified
      ↓
Loan eligibility verified
      ↓
Transaction summaries verified
```

At completion, provide:
- Implemented endpoint list.
- Project files created/modified.
- Test count.
- Test results.
- Example API requests/responses.
- Any deviations from this specification.
- Confirmation that no Phase 4+ functionality was implemented.
