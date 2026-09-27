# Phase 9 — Jinja UI Specification

## 1. Overview

### 1.1 Purpose

Implement a browser-based user interface for the NovaBank AI Banking Customer Query Assistant using:

- FastAPI
- Jinja2 templates
- HTML
- CSS
- Vanilla JavaScript

The UI must consume the existing Phase 8 REST API.

The UI must NOT implement banking logic, agent routing, RAG, conversation memory, or direct database access.

### 1.2 Primary Goal

Provide a simple browser-based chat interface through which a user can:

1. Enter/select a customer ID.
2. Create a conversation.
3. Ask banking questions.
4. Receive assistant responses.
5. Continue multi-turn conversations.
6. View conversation history.
7. See basic source/provenance information when available.
8. Handle loading and error states.

The UI is an interface layer only.

### 1.3 Architecture

The final flow must be:

```text
Browser
   ↓
Jinja UI
   ↓
FastAPI
   ↓
Phase 8 REST API
   ↓
Phase 7 Conversation Memory
   ↓
Phase 6 Banking Orchestrator
   ├── Phase 4 Banking Tools
   └── Phase 5 Qdrant RAG
```

The browser must NOT communicate directly with:

- SQLite
- Qdrant
- Banking APIs
- Banking Tools
- LangGraph
- LLM providers

---

## 2. Scope

### 2.1 In Scope

Phase 9 implements:

- Jinja2 template setup.
- Browser chat page.
- HTML structure.
- CSS styling.
- Vanilla JavaScript chat logic.
- Customer ID input.
- Conversation creation.
- Sending chat messages.
- Displaying assistant responses.
- Loading conversation history.
- Conversation continuity.
- Loading states.
- Error states.
- Basic source/provenance display.
- Responsive layout.
- Static asset serving.
- UI tests.
- Regression testing for Phases 3–9.

### 2.2 Out of Scope

Do NOT implement:

- React.
- Next.js.
- Vue.
- Angular.
- WebSockets.
- Streaming responses.
- Authentication.
- User registration.
- OAuth.
- JWT.
- Password management.
- Admin dashboard.
- Banking business logic.
- Direct SQLite access from browser.
- Direct Qdrant access.
- Direct LLM access.
- New banking tools.
- New RAG functionality.
- Voice interface.
- File upload.
- Payment functionality.
- Production deployment.
- Mobile application.
- Phase 10 evaluation/optimization functionality.

---

## 3. Technology Requirements

Use:

- FastAPI
- Jinja2
- HTML5
- CSS3
- Vanilla JavaScript

Do NOT introduce a frontend framework.

Do NOT introduce a frontend build system unless absolutely required by the existing project.

The UI should work without:

- npm
- Node.js frontend tooling
- React
- Vite
- Webpack

The objective is a lightweight server-rendered interface.

---

## 4. Existing API Integration

The UI must consume the existing Phase 8 endpoints.

Available API:

- `POST /api/conversations`
- `POST /api/chat`
- `GET  /api/conversations/{conversation_id}`
- `GET  /api/health`

The UI must not duplicate API functionality.

---

## 5. Recommended Project Structure

Add:

```text
app/
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
```

If the project already contains equivalent template/static directories, reuse them.

Do not create duplicate directories.

The existing FastAPI application should serve:

```text
/
```

as the main UI page.

---

## 6. Main UI Route

Implement:

```http
GET /
```

The route must render:

```text
templates/index.html
```

using Jinja2.

Example:

```text
Browser
   ↓
GET /
   ↓
FastAPI
   ↓
Jinja2
   ↓
index.html
```

The route should not perform banking operations.

It should only render the UI.

---

## 7. Page Layout

The main page should contain:

```text
┌─────────────────────────────────────────────┐
│               NovaBank AI                   │
│        Banking Customer Assistant            │
├─────────────────────────────────────────────┤
│                                             │
│ Customer ID: [ CUST001       ] [New Chat]   │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ User                                        │
│ What is my account balance?                 │
│                                             │
│ Assistant                                   │
│ Your current balance is ...                 │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ [ Type your message...              ] [Send]│
└─────────────────────────────────────────────┘
```

The exact visual design is flexible.

The following functional elements are required:

- Application title.
- Customer ID input.
- New conversation button.
- Conversation/chat area.
- Message input.
- Send button.
- Loading indication.
- Error indication.

---

## 8. Customer ID

The UI must provide a customer ID input.

Example:

```text
Customer ID
[CUST001]
```

For the prototype, customer IDs may be manually entered.

No authentication is implemented in Phase 9.

The UI must not pretend that this field represents authenticated identity.

The selected customer ID must be used when calling:

- `POST /api/conversations`
- `POST /api/chat`
- `GET /api/conversations/{conversation_id}`

---

## 9. Conversation State

The browser must maintain the current:

- `customer_id`
- `conversation_id`

for the active conversation.

Recommended JavaScript state:

```javascript
const state = {
    customerId: null,
    conversationId: null,
    messages: []
};
```

The exact implementation may differ.

The state must not contain:

- API keys
- passwords
- credentials
- internal agent state
- raw tool results

---

## 10. Creating a Conversation

When the user clicks:

```text
New Chat
```

the UI must:

1. Validate customer ID.
2. Call:
   ```http
   POST /api/conversations
   ```
   with:
   ```json
   {
     "customer_id": "CUST001"
   }
   ```
3. Receive the new `conversation_id`.
4. Store the conversation ID in browser state.
5. Clear the current message display.
6. Update the UI to show the new conversation.
7. Enable message input.

The UI must not generate conversation IDs itself.

The API remains responsible for conversation creation.

---

## 11. Sending a Message

When the user submits:

> "What is my balance?"

the UI must call:

```http
POST /api/chat
```

with:

```json
{
  "conversation_id": "conv_123",
  "customer_id": "CUST001",
  "message": "What is my balance?"
}
```

The UI must use the conversation ID returned by the API.

---

## 12. Message Display

When the user sends a message:

- Display the user message immediately.
- Disable the send control while waiting.
- Show a loading indicator.
- Send the API request.
- Receive the response.
- Display the assistant response.
- Remove the loading indicator.
- Re-enable the send control.

Example:

**User:**
> What is my balance?

**Assistant:**
> Your current account balance is INR 192,203.99.

The UI must clearly distinguish user and assistant messages.

---

## 13. Empty Message Handling

Do not send empty messages.

Reject:

```text
""
```

and:

```text
"     "
```

on the client side.

Display a simple validation message.

The API remains responsible for server-side validation as well.

Client-side validation must never replace API validation.

---

## 14. Conversation History

When an existing conversation is loaded, the UI must call:

```http
GET /api/conversations/{conversation_id}?customer_id=CUST001
```

and render the returned messages.

The API remains the source of truth.

The UI must not reconstruct conversation history from local assumptions.

---

## 15. Browser Persistence

The active conversation may be persisted using:

```text
localStorage
```

if useful.

Recommended stored state:

- `novabank_customer_id`
- `novabank_conversation_id`

Do NOT store:

- API credentials.
- Authentication tokens.
- Passwords.
- Internal agent state.
- Raw tool results.

Conversation message content should not be unnecessarily persisted in localStorage because the server-side Phase 7 memory is the authoritative conversation history.

If localStorage is used, it should primarily preserve the active identifiers.

---

## 16. Page Reload Behavior

After refreshing the browser:

- Read stored customer ID and conversation ID if available.
- If both are available:
  - request conversation history from the API.
  - render the history.
- If the conversation is unavailable:
  - clear stale conversation state.
  - allow the user to create a new conversation.
- Do not silently create a new conversation unless explicitly intended by the UI flow.

---

## 17. New Chat Behavior

Clicking:

```text
New Chat
```

must start a separate conversation.

The previous conversation must remain stored in the backend.

The UI must:

- Create a new conversation.
- Replace the active conversation ID.
- Clear the visible chat area.
- Keep the selected customer ID.
- Focus the message input.

Do not delete the previous conversation.

---

## 18. API Response Handling

The UI must use the response structure from Phase 8.

For chat responses, display the primary assistant response.

For example:

```json
{
  "conversation_id": "conv_123",
  "customer_id": "CUST001",
  "message": "Your current balance is INR 192,203.99.",
  "route": "TOOL",
  "sources": [
    {
      "type": "tool",
      "name": "get_balance"
    }
  ]
}
```

The UI should display:

> Your current balance is INR 192,203.99.

Optionally display a small source indicator such as:

> Source: Banking Tool — get_balance

For RAG:

> Source: NovaBank Knowledge Base

Do not display raw internal metadata.

---

## 19. Source / Provenance Display

If the API provides safe source information, the UI may display it.

Examples:

- `Source: Banking Tool`
- `Source: NovaBank Knowledge Base`
- `Sources: Banking Tool + NovaBank Knowledge Base`

The UI must NOT display:

- tool arguments
- Qdrant IDs
- vector scores
- internal node names
- system prompts
- raw retrieved chunks
- internal LangGraph state

The source display must remain simple and user-friendly.

---

## 20. Error Handling

The UI must gracefully handle API errors.

Possible responses include:

- `422 Validation Error`
- `404 Conversation Not Found`
- `500 Internal Server Error`

The user should see a friendly message.

Example:

> Unable to process your request. Please try again.

For conversation-not-found:

> This conversation is no longer available. Please start a new chat.

Do not display:

- Python tracebacks
- SQLite errors
- internal file paths
- stack traces
- internal exception classes
- API keys
- system prompts

---

## 21. Network Error Handling

Handle cases where:

- API server is unavailable.
- Request times out.
- Browser cannot connect.
- Response is invalid JSON.

Example message:

> Unable to connect to the NovaBank assistant. Please check that the server is running and try again.

The UI must restore the send button after a failed request.

---

## 22. Loading State

While waiting for `/api/chat`:

- Disable Send.
- Prevent duplicate submissions.
- Display a loading indicator.

Example:

> Assistant is thinking...

After the response:

- Remove the loading indicator.
- Re-enable Send.

The loading state must also be cleared if the request fails.

---

## 23. Keyboard Interaction

The chat input should support:

- `Enter` → Send message

Recommended:

- `Shift + Enter` → New line

Do not submit multiple requests from a single key press.

---

## 24. Auto Scrolling

After adding a new message, scroll the chat container to the latest message.

The user should always see the newest conversation turn.

Do not continuously force-scroll if the user is manually reading older messages.

---

## 25. Responsive Design

The UI must work reasonably on:

- Desktop.
- Laptop.
- Tablet.
- Mobile-sized browser windows.

Use responsive CSS.

Avoid fixed layouts that break at smaller widths.

No external CSS framework is required.

---

## 26. Visual Design

The UI should look like a clean banking assistant rather than a raw developer interface.

Suggested visual hierarchy:

```text
NovaBank AI
Banking Customer Assistant

Customer ID
Conversation

Chat messages

Message input
Send
```

Use:

- clear typography
- readable spacing
- distinguishable message bubbles
- clear buttons
- visible focus states
- appropriate contrast

Do not spend excessive implementation effort on animations.

Functionality has priority over visual complexity.

---

## 27. Accessibility

The UI should include:

- semantic HTML.
- labels for inputs.
- accessible buttons.
- keyboard navigation.
- visible focus states.
- meaningful error messages.
- appropriate ARIA attributes where useful.

The message input must have an associated label or accessible name.

Buttons must have meaningful text or accessible labels.

---

## 28. Security

The UI must preserve backend security boundaries.

Never trust the frontend as an authorization mechanism.

The backend remains responsible for customer/conversation isolation.

Do not place secrets in:

- HTML.
- JavaScript.
- CSS.
- Jinja variables.
- localStorage.

Do not expose:

- LLM API keys.
- database credentials.
- Qdrant credentials.
- internal configuration secrets.

---

## 29. Jinja Responsibilities

Jinja should primarily be used for:

- Rendering the initial page.
- Providing static application information.
- Loading template structure.

Do NOT use Jinja to execute banking operations.

Do NOT put banking data access inside templates.

Do NOT embed database queries in templates.

The chat interactions should happen through the Phase 8 REST API.

---

## 30. JavaScript Responsibilities

JavaScript should handle:

- UI state.
- API calls.
- Message rendering.
- Loading state.
- Error handling.
- Conversation identifiers.
- History loading.
- New conversation behavior.

JavaScript must NOT contain:

- Banking business logic.
- Banking credentials.
- RAG logic.
- Agent routing.
- Database logic.
- LLM logic.

---

## 31. API Base URL

The UI should use the same FastAPI application by default.

Prefer relative URLs:

- `/api/conversations`
- `/api/chat`
- `/api/health`

rather than hardcoding:

```text
http://localhost:8000
```

This allows the application to work when deployed under a different host.

---

## 32. Health Indicator

The UI may optionally check:

```http
GET /api/health
```

to determine whether the backend is available.

If implemented, display a simple status such as:

> ● Connected

or:

> ● Backend unavailable

Do not poll continuously.

A single check during page initialization is sufficient.

---

## 33. Static Files

Mount the static directory through FastAPI/Starlette.

Expected paths:

- `/static/css/style.css`
- `/static/js/app.js`

The implementation must use FastAPI's existing static-file conventions.

---

## 34. Template Setup

Configure Jinja2 using FastAPI's supported template mechanism.

The main page should be rendered through a template response.

Do not generate HTML strings directly inside Python route handlers.

---

## 35. Testing

Phase 9 must include UI/API integration tests.

Recommended:

```text
tests/
├── test_ui.py
├── test_ui_chat_flow.py
└── test_ui_errors.py
```

Use the existing test framework and conventions.

---

## 36. UI Route Tests

Test:

```http
GET /
```

Verify:

- HTTP 200.
- HTML response.
- expected page title/content.
- main chat elements exist.
- CSS/JS assets are referenced correctly.

---

## 37. Static Asset Tests

Verify:

- `/static/css/style.css`
- `/static/js/app.js`

are accessible.

Expected:

```text
HTTP 200
```

where applicable.

---

## 38. Chat Flow Tests

Test the complete browser-facing flow at the API/UI boundary:

```text
GET /
    ↓
Create conversation
    ↓
Send message
    ↓
Receive response
    ↓
Retrieve history
    ↓
Render continuation
```

Verify that the existing Phase 8 APIs are used.

---

## 39. Multi-Turn UI Test

Simulate:

**User:**
> Tell me about home loans.

**Assistant:**
> ...

**User:**
> What are the eligibility requirements?

**Assistant:**
> ...

Verify that:

- the same conversation ID is used.
- both messages are displayed.
- Phase 7 memory remains responsible for context.
- Phase 5 RAG remains responsible for policy retrieval.

---

## 40. Banking Tool UI Test

Simulate:

> What is my balance?

Verify that:

- request reaches `/api/chat`.
- response is displayed.
- UI does not directly call banking tools.

---

## 41. Error UI Tests

Test:

- invalid customer ID.
- missing conversation.
- API 500.
- network failure where practical.
- invalid API response.

Verify that:

- a friendly error is displayed.
- stack traces are not shown.
- Send becomes usable again.

---

## 42. Security Tests

Verify:

- no credentials appear in generated HTML.
- no API keys appear in JavaScript.
- no database paths are exposed.
- no raw internal tool arguments are rendered.
- customer ID remains explicitly supplied to API calls.
- backend ownership checks remain enforced.

---

## 43. Regression Testing

After Phase 9 implementation, run:

```text
Phase 3 tests
+
Phase 4 tests
+
Phase 5 tests
+
Phase 6 tests
+
Phase 7 tests
+
Phase 8 tests
+
Phase 9 tests
```

All previous tests must continue passing.

The UI must not modify the behavior of:

- Banking APIs.
- Banking Tools.
- Qdrant RAG.
- LangGraph orchestration.
- Conversation Memory.
- Chat API.

---

## 44. No Phase 10 Functionality

Do NOT implement:

- automated evaluation datasets.
- LLM-as-judge.
- retrieval evaluation.
- response-quality scoring.
- latency benchmarking.
- prompt optimization.
- model comparison.
- RAG optimization.
- automated performance tuning.

Those belong to Phase 10.

---

## 45. Recommended Final Architecture

After Phase 9:

```text
                        Browser
                           │
                           ▼
                  ┌────────────────┐
                  │   Jinja UI     │
                  │ HTML/CSS/JS    │
                  └───────┬────────┘
                          │
                    REST API calls
                          │
                          ▼
                  ┌────────────────┐
                  │    FastAPI     │
                  │   Phase 8 API  │
                  └───────┬────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ MemoryOrchestrator │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ BankingOrchestrator│
                │     LangGraph      │
                └─────────┬──────────┘
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
          Banking Tools           RAG
                 │                 │
                 ▼                 ▼
         Mock Banking APIs       Qdrant
                 │                 │
                 └────────┬────────┘
                          ▼
                       Response
                          │
                          ▼
                   SQLite Memory
```

---

## 46. Responsibility Boundaries

The final system must maintain:

```text
Jinja UI
    = browser interface

FastAPI
    = HTTP API + validation

Conversation Memory
    = conversation persistence + history

MemoryOrchestrator
    = memory-aware execution

LangGraph / BankingOrchestrator
    = routing + orchestration

Banking Tools
    = customer-specific banking operations

Mock Banking APIs
    = banking data/business logic

RAGRetriever
    = knowledge retrieval

Qdrant
    = vector storage/retrieval

LLM
    = reasoning + response generation
```

The frontend must not duplicate backend responsibilities.

---

## 47. Definition of Done

Phase 9 is complete only when all of the following are true.

### UI
- [ ] Jinja2 templates implemented.
- [ ] Main chat page implemented.
- [ ] Customer ID input implemented.
- [ ] New conversation button implemented.
- [ ] Chat message display implemented.
- [ ] Message input implemented.
- [ ] Send functionality implemented.
- [ ] Loading state implemented.
- [ ] Error state implemented.
- [ ] Responsive layout implemented.
- [ ] Basic accessibility implemented.

### API Integration
- [ ] UI calls `POST /api/conversations`.
- [ ] UI calls `POST /api/chat`.
- [ ] UI calls `GET /api/conversations/{conversation_id}`.
- [ ] UI optionally uses `/api/health`.
- [ ] Conversation ID is maintained correctly.
- [ ] Customer ID is maintained correctly.
- [ ] Multi-turn conversations work.
- [ ] History loading works.
- [ ] New conversations work.

### Security
- [ ] No secrets exposed in frontend.
- [ ] No direct database access.
- [ ] No direct Qdrant access.
- [ ] No direct LLM access.
- [ ] No banking logic in frontend.
- [ ] Backend security boundaries remain authoritative.

### Testing
- [ ] Main UI route tests pass.
- [ ] Static asset tests pass.
- [ ] Chat flow tests pass.
- [ ] Multi-turn tests pass.
- [ ] Error tests pass.
- [ ] Security tests pass.
- [ ] Full regression suite passes.

### Scope
- [ ] No React.
- [ ] No Next.js.
- [ ] No WebSockets.
- [ ] No authentication.
- [ ] No Phase 10 evaluation functionality.

---

## 48. Phase 9 Success Criteria

A user must be able to open:

```text
http://localhost:8000/
```

and interact with the NovaBank assistant entirely through the browser.

The complete workflow must be:

```text
Open UI
   ↓
Enter customer ID
   ↓
New Chat
   ↓
Ask:
"What is my balance?"
   ↓
Assistant response appears
   ↓
Ask:
"What about my recent transactions?"
   ↓
Assistant uses conversation context
   ↓
Ask:
"What are the home loan eligibility requirements?"
   ↓
Assistant retrieves policy through RAG
   ↓
Refresh browser
   ↓
Conversation history is restored
```

The UI must remain a thin presentation layer over the existing Phase 8 REST API.