# Phase 4 — Banking Tools Specification

## 1. Overview

### Project
AI-Powered Banking Customer Query Assistant

### Bank
NovaBank

### Phase
4 — Banking Tools

### Status
Planned

---

## 2. Purpose

This phase converts the existing Phase 3 Mock Banking APIs into a set of structured, callable banking tools.

The tools provide a clean interface for future AI agents to access customer-specific banking information and perform deterministic banking operations.

The tools must:
- Wrap the existing Phase 3 banking API functionality.
- Accept structured inputs.
- Return structured outputs.
- Preserve customer data isolation.
- Handle API errors consistently.
- Contain no LLM or agent logic.
- Be deterministic.
- Be independently testable.

Phase 4 is an integration/tool layer only.

---

## 3. Dependencies

Phase 4 depends on:
- Phase 1 — Synthetic Data
- Phase 2 — Knowledge Base
- Phase 3 — Mock Banking APIs

The Phase 3 API is the source of truth for customer-specific banking data.

Do not directly access JSON data files from the tools layer when an equivalent Phase 3 API endpoint exists.

---

## 4. Architecture

The architecture should follow:

```text
Future Agent / Orchestrator
          |
          v
     Banking Tools
          |
          v
   Phase 3 Banking APIs
          |
          v
    Service / Repository
          |
          v
   Synthetic JSON Data
```

Phase 4 must NOT implement the future agent/orchestrator.

---

## 5. Tool Design Principles

### 5.1 Structured Inputs

Tools must accept explicit typed parameters.

Example:
```python
get_balance(customer_id: str)
```

Do not accept arbitrary natural-language queries such as:
```python
get_balance("How much money do I have?")
```

Natural-language interpretation belongs to a future agent/orchestrator.

### 5.2 Structured Outputs

Tools must return structured Python objects/dictionaries rather than natural-language responses.

Example:
```json
{
  "customer_id": "CUST001",
  "account_id": "ACC001",
  "balance": 125000.00,
  "currency": "INR"
}
```

The tool must NOT generate responses such as:
> Your current balance is ₹1,25,000.

Natural-language response generation belongs to a later phase.

### 5.3 No LLM Logic

Phase 4 must NOT contain:
- OpenAI calls
- Anthropic calls
- Gemini calls
- LangChain agents
- LangGraph agents
- Prompt templates
- LLM-based intent detection
- Natural-language reasoning

### 5.4 No RAG Logic

Phase 4 must NOT implement:
- Embeddings
- FAISS
- Vector databases
- Semantic search
- Document retrieval

Policy and general banking knowledge will be handled by the RAG pipeline in Phase 5.

### 5.5 Customer Data Isolation

Every customer-specific tool must require a `customer_id`.

A customer must never be able to retrieve another customer's:
- Personal information
- Accounts
- Balances
- Transactions
- Loan eligibility information

The tool layer must rely on the Phase 3 API's customer isolation behavior.

---

## 6. Tool Location

Create a dedicated tools package:

```text
app/
└── tools/
    ├── __init__.py
    ├── banking_tools.py
    └── schemas.py
```

Tests should be placed under:

```text
tests/
├── test_banking_tools.py
└── test_banking_tool_security.py
```

The exact internal organization may be adjusted if necessary, but the separation between tools and Phase 3 API routes must be preserved.

---

## 7. API Communication

The Banking Tools must use the existing Phase 3 API contracts rather than duplicating business logic.

Preferred flow:

```text
Tool
 ↓
Phase 3 API endpoint
 ↓
Service
 ↓
Repository
 ↓
JSON data
```

The tool layer should therefore act as an adapter around the existing API.

Do not duplicate:
- Customer lookup logic
- Balance calculation logic
- Transaction filtering logic
- Transaction summary logic
- Loan eligibility rules
- Product data logic
- Interest-rate logic

Those rules already belong to Phase 3.

---

## 8. Required Banking Tools

Phase 4 must implement the following tools.

### 8.1 get_customer_details

#### Purpose
Retrieve basic customer information.

#### Input
`customer_id: str`

#### API Mapping
`GET /api/customers/{customer_id}`

#### Output
Return the structured customer response provided by the API.

Example:
```json
{
  "customer_id": "CUST001",
  "name": "...",
  "email": "...",
  "phone": "...",
  "date_of_birth": "...",
  "address": "..."
}
```

Do not expose fields that are not returned by the Phase 3 API.

### 8.2 get_customer_profile

#### Purpose
Retrieve the customer's banking profile.

#### Input
`customer_id: str`

#### API Mapping
`GET /api/customers/{customer_id}/profile`

#### Output
Return the structured profile response.

### 8.3 get_accounts

#### Purpose
Retrieve all accounts belonging to a customer.

#### Input
`customer_id: str`

#### API Mapping
`GET /api/accounts/{customer_id}`

#### Output
Return the structured account list.

### 8.4 get_balance

#### Purpose
Retrieve the customer's account balance information.

#### Input
`customer_id: str`

#### API Mapping
`GET /api/accounts/{customer_id}/balance`

#### Output
Return the structured balance response.

The tool must not calculate or modify balances independently.

### 8.5 get_transactions

#### Purpose
Retrieve customer transactions with supported filters.

#### Inputs
- `customer_id: str`
- `limit: int = 50`
- `offset: int = 0`
- `transaction_type: str | None = None`
- `category: str | None = None`
- `merchant: str | None = None`
- `start_date: str | None = None`
- `end_date: str | None = None`

#### API Mapping
`GET /api/accounts/{customer_id}/transactions`

#### Supported Filters
The tool must expose the filtering capabilities supported by Phase 3:
- Pagination
- Transaction type
- Category
- Merchant
- Start date
- End date

#### Output
Return structured transaction data.

Do not convert the transaction list into natural language.

### 8.6 get_transaction_summary

#### Purpose
Retrieve a summarized view of customer transactions.

#### Inputs
- `customer_id: str`
- `start_date: str | None = None`
- `end_date: str | None = None`

#### API Mapping
`GET /api/accounts/{customer_id}/transactions/summary`

#### Output
Return the structured transaction summary from the API.

The summary may include information such as:
- Total credits
- Total debits
- Category spending

Do not independently recalculate values in the tool.

### 8.7 list_loans

#### Purpose
Retrieve available NovaBank loan products.

#### Inputs
Optional filters may be supported if already available through the Phase 3 API.
- `loan_type: str | None = None`

#### API Mapping
`GET /api/loans`

#### Output
Return the structured loan catalog.

### 8.8 get_loan_details

#### Purpose
Retrieve details for a specific loan.

#### Input
`loan_id: str`

#### API Mapping
`GET /api/loans/{loan_id}`

#### Output
Return the structured loan details.

### 8.9 check_loan_eligibility

#### Purpose
Check whether a customer satisfies the deterministic eligibility rules for a specific loan.

#### Inputs
- `customer_id: str`
- `loan_id: str`
- `requested_amount: float`

#### API Mapping
`POST /api/loans/check-eligibility`

#### Output
Return the structured eligibility response from the API.

Example structure:
```json
{
  "eligible": true,
  "customer_id": "CUST001",
  "loan_id": "LOAN001",
  "requested_amount": 500000,
  "reasons": []
}
```

The tool must not make its own eligibility decision.

The Phase 3 API remains the source of truth for eligibility rules.

### 8.10 list_products

#### Purpose
Retrieve available NovaBank banking products.

#### Inputs
Optional product-type filtering may be supported if available through the Phase 3 API.
- `product_type: str | None = None`

#### API Mapping
`GET /api/products`

#### Output
Return the structured product list.

### 8.11 get_interest_rates

#### Purpose
Retrieve current simulated NovaBank interest rates.

#### Inputs
Optional product-type filtering may be supported if available.
- `product_type: str | None = None`

#### API Mapping
`GET /api/interest-rates`

#### Output
Return structured interest-rate information.

---

## 9. Tool Registry

Provide a single way to access all available banking tools.

Example:
```python
BANKING_TOOLS = [
    get_customer_details,
    get_customer_profile,
    get_accounts,
    get_balance,
    get_transactions,
    get_transaction_summary,
    list_loans,
    get_loan_details,
    check_loan_eligibility,
    list_products,
    get_interest_rates,
]
```

The registry must contain only Phase 4 banking tools.

Do not register agents, RAG retrievers, or LLM functions in this phase.

---

## 10. Tool Metadata

Each tool should have clear metadata that will allow a future agent framework to discover what the tool does.

At minimum, each tool must have:
- Tool name
- Description
- Input parameters
- Parameter types
- Required/optional parameters
- Return structure

Example:
```json
{
    "name": "get_balance",
    "description": "Retrieve the account balance for a NovaBank customer.",
    "parameters": {
        "customer_id": {
            "type": "string",
            "required": true
        }
    }
}
```

The implementation may use Python type hints and docstrings instead of manually maintaining metadata if those can be consumed by future agent tooling.

Do not introduce a specific agent framework solely for metadata generation.

---

## 11. Error Handling

Tools must provide predictable error behavior.

At minimum, handle:

### Customer Not Found
If the API returns a customer-not-found error:
> Customer not found

The tool must preserve a structured error representation.

### Loan Not Found
If the requested loan does not exist, return the API error in structured form.

### Invalid Input
Examples:
- Invalid customer ID
- Invalid loan ID
- Negative requested loan amount
- Invalid pagination values
- Invalid date parameters

Invalid input must not silently produce incorrect results.

### API Errors
If the underlying Phase 3 API is unavailable or returns an error, the tool must not fabricate a successful response.

Return a structured error.

Example:
```json
{
  "success": false,
  "error": {
    "type": "api_error",
    "message": "Banking API unavailable"
  }
}
```

The exact error schema may follow the existing Phase 3 API conventions if one already exists.

---

## 12. Success Response Convention

Where practical, tools should use a consistent structured result.

Example:
```json
{
  "success": true,
  "data": {
    "...": "..."
  }
}
```

Errors:
```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "Invalid customer_id"
  }
}
```

If the existing Phase 3 API already defines a response convention, preserve it rather than introducing unnecessary duplication.

The important requirement is that callers receive structured results and can distinguish success from failure.

---

## 13. Security Requirements

The tools must not:
- Accept a customer ID from one customer and return another customer's data.
- Allow customer ID manipulation to bypass Phase 3 isolation.
- Modify synthetic customer data.
- Expose internal repository paths.
- Expose filesystem implementation details.
- Fabricate missing customer information.

Security tests must verify that:
- `CUST001` → `CUST001` data
- `CUST002` → `CUST002` data
- `CUST001` cannot retrieve `CUST002` data by manipulating tool parameters

---

## 14. Determinism

Given the same:
- customer_id
- loan_id
- filters
- requested amount

and unchanged Phase 3 data, the tool must produce the same result.

No randomness is permitted.

No external banking service calls are permitted.

No LLM calls are permitted.

---

## 15. Testing Requirements

Create automated tests for all banking tools.

Minimum coverage:

### Customer Tools
- `get_customer_details`
- `get_customer_profile`

Test:
- Valid customer
- Invalid customer
- Response structure

### Account Tools
- `get_accounts`
- `get_balance`

Test:
- Valid customer
- Invalid customer
- Correct API mapping
- Response structure

### Transaction Tools
- `get_transactions`
- `get_transaction_summary`

Test:
- Pagination
- Transaction type filtering
- Category filtering
- Merchant filtering
- Date filtering
- Summary retrieval
- Invalid customer

### Loan Tools
- `list_loans`
- `get_loan_details`
- `check_loan_eligibility`

Test:
- Valid loan
- Invalid loan
- Valid eligibility request
- Ineligible request
- Invalid requested amount
- Invalid customer

### Product Tools
- `list_products`
- `get_interest_rates`

Test:
- Successful retrieval
- Filtering where supported
- Response structure

### Security Tests
Verify:
- Customer isolation
- No cross-customer data leakage
- Invalid customer IDs cannot access another customer's data
- Tools do not bypass the Phase 3 API layer

### Error Tests
Test:
- API error
- Validation error
- Not-found error
- Invalid parameters

---

## 16. Mocking Strategy

Tests must not depend on an externally running banking server.

Use mocked HTTP/API responses where appropriate.

Tests should verify that tools:
- Construct the correct API request.
- Pass the correct parameters.
- Correctly parse successful responses.
- Correctly handle API errors.

The implementation should make the API client easy to mock.

---

## 17. Code Quality Requirements

The implementation must:
- Use Python type hints.
- Use clear function names.
- Use docstrings for tools.
- Keep tools small and focused.
- Avoid duplicated business logic.
- Avoid unnecessary dependencies.
- Follow the existing project structure.
- Reuse existing Phase 3 schemas where practical.
- Keep tool logic separate from API route logic.

Do not refactor unrelated Phase 3 code unless required for tool integration.

---

## 18. Phase Boundary

This phase MUST NOT implement:
- LLM integration
- Prompt engineering
- Intent classification
- RAG retrieval
- Embeddings
- FAISS/vector database
- Agents
- LangChain
- LangGraph
- Conversation memory
- Chat API
- Jinja UI
- Frontend
- Natural-language response generation
- Real banking API integration

Those belong to later phases.

---

## 19. Expected Project Structure

After Phase 4, the relevant structure should resemble:

```text
app/
├── main.py
├── api/
│   ├── customers.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── loans.py
│   └── products.py
├── repositories/
│   └── json_repository.py
├── schemas/
│   ├── customer.py
│   ├── account.py
│   ├── transaction.py
│   ├── loan.py
│   └── product.py
├── services/
│   ├── customer_service.py
│   ├── account_service.py
│   ├── transaction_service.py
│   ├── loan_service.py
│   └── product_service.py
└── tools/
    ├── __init__.py
    ├── banking_tools.py
    └── schemas.py

tests/
├── test_customers.py
├── test_accounts.py
├── test_transactions.py
├── test_loans.py
├── test_products.py
├── test_security_isolation.py
├── test_docs.py
├── test_banking_tools.py
└── test_banking_tool_security.py
```

The exact filenames may differ if the existing project architecture requires it, but the separation of concerns must remain.

---

## 20. Definition of Done

Phase 4 is complete only when:
- [ ] All required banking tools are implemented.
- [ ] Tools use the Phase 3 API contracts.
- [ ] No Phase 3 business logic is duplicated.
- [ ] Tools return structured results.
- [ ] Tools handle errors consistently.
- [ ] Customer data isolation is preserved.
- [ ] Tool metadata/descriptions are available.
- [ ] All automated tests pass.
- [ ] Security tests pass.
- [ ] No LLM functionality is introduced.
- [ ] No RAG functionality is introduced.
- [ ] No agent/orchestrator functionality is introduced.
- [ ] No frontend functionality is introduced.
- [ ] Existing Phase 3 tests still pass.
- [ ] Phase 3 behavior remains unchanged.
- [ ] The specification file is not modified during implementation.

---

## 21. Validation

After implementation, run:

```bash
pytest
```

All existing Phase 3 tests and all new Phase 4 tests must pass.

Also verify that the Phase 3 API still starts successfully and that its existing endpoints remain functional.

The implementation report must include:
- Files created/modified.
- Banking tools implemented.
- API endpoints mapped to each tool.
- Test count.
- Test results.
- Security test results.
- Any deviations from this specification.

If there are deviations, explicitly document them instead of silently changing the specification.
