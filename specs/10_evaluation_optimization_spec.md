# Phase 10 --- Evaluation & Optimization Specification

**Project:** AI-Powered Banking Customer Query Assistant\
**Bank:** NovaBank (synthetic)\
**Phase:** 10 --- Evaluation + Optimization\
**Status:** Specification\
**Previous Phase:** Phase 9 --- Jinja UI\
**Source of Truth:** This document is the implementation contract for
Phase 10.

------------------------------------------------------------------------

## 1. Purpose

Phase 10 evaluates the complete NovaBank banking assistant built in
Phases 1--9 and applies controlled, measurable optimization.

The objective is to answer:

1.  Does the system route customer queries correctly?
2.  Does it select and execute the correct banking tools?
3.  Does the RAG pipeline retrieve relevant knowledge?
4.  Are generated responses grounded in available evidence?
5.  Does the system handle unsupported and prompt-injection queries
    safely?
6.  What is the system's latency?
7.  Can measured weaknesses be improved without breaking previous
    phases?
8.  Does the optimized system generalize to an untouched holdout set?

Phase 10 is an **evaluation and optimization phase**, not a
feature-development phase.

The implementation MUST NOT introduce new customer-facing product
capabilities.

------------------------------------------------------------------------

# 2. Scope

## 2.1 In Scope

Phase 10 includes:

-   Evaluation dataset construction from the existing synthetic query
    dataset.
-   Explicit evaluation ground truth.
-   Development/tuning and holdout evaluation splits.
-   Baseline evaluation.
-   Routing evaluation.
-   Banking-tool selection/execution evaluation.
-   RAG retrieval evaluation.
-   Response grounding/correctness evaluation.
-   Safety/refusal evaluation.
-   End-to-end latency benchmarking.
-   Component-level latency measurement where practical.
-   Controlled optimization of measurable system parameters.
-   Re-running the same evaluation after optimization.
-   Final holdout evaluation.
-   Machine-readable evaluation results.
-   Human-readable evaluation report.
-   Automated evaluation tests.
-   Full regression testing of Phases 3--10.
-   Reproducibility and deterministic evaluation configuration.

## 2.2 Out of Scope

The following MUST NOT be implemented in Phase 10:

-   New banking APIs.
-   New banking tools.
-   New agents.
-   New graph architecture.
-   New conversation-memory features.
-   Authentication/authorization.
-   Production payment functionality.
-   Real bank integrations.
-   Real customer data.
-   New frontend features.
-   React/Next.js/Vue migration.
-   WebSocket/streaming chat.
-   Replacing FastAPI.
-   Replacing LangGraph.
-   Replacing Qdrant.
-   Replacing the embedding model unless explicitly required by measured
    optimization and documented.
-   Replacing SQLite conversation memory.
-   Adding another vector database.
-   Adding a second RAG backend.
-   Building a production monitoring platform.
-   Training a custom LLM.
-   Fine-tuning an LLM.
-   Autonomous online learning.
-   Automatic self-modification of prompts or code in production.

Phase 10 MUST preserve the architecture established by Phases 1--9.

------------------------------------------------------------------------

# 3. Existing System Contract

The implementation MUST first inspect and reuse the existing Phase 1--9
architecture.

The expected high-level architecture is:

``` text
Browser
   ↓
Jinja UI
   ↓
FastAPI Chat API
   ↓
Conversation Memory
   ↓
LangGraph Banking Orchestrator
   ├── Banking Tools
   │      ↓
   │   Mock Banking APIs
   │
   └── RAG Retriever
          ↓
       Qdrant
```

The evaluation layer MUST evaluate this existing system rather than
create a parallel implementation.

Existing components remain authoritative:

-   Phase 3 --- Mock Banking APIs
-   Phase 4 --- Banking Tools
-   Phase 5 --- Qdrant RAG
-   Phase 6 --- Agents + Orchestrator
-   Phase 7 --- Conversation Memory
-   Phase 8 --- Chat API
-   Phase 9 --- Jinja UI

The existing application behavior MUST NOT be silently changed merely to
make evaluation scores higher.

------------------------------------------------------------------------

# 4. Evaluation Principles

Phase 10 MUST follow these principles.

## 4.1 Reproducibility

Evaluation runs MUST be reproducible.

Use:

-   fixed random seed,
-   fixed evaluation dataset version,
-   fixed configuration,
-   fixed evaluation split,
-   recorded model/provider configuration,
-   recorded retrieval configuration,
-   recorded timestamp,
-   recorded software/configuration metadata where practical.

The default evaluation mode MUST NOT require external LLM credentials.

------------------------------------------------------------------------

## 4.2 Separate Tuning from Final Evaluation

The evaluation dataset MUST be divided into:

``` text
Full Evaluation Dataset
        ↓
   ┌────┴────┐
   ↓         ↓
Development  Holdout
   Set        Set
   80%        20%
```

The development set may be used for optimization.

The holdout set MUST NOT be used to select optimization parameters.

The holdout score is the final unbiased evaluation result for the Phase
10 report.

The split MUST be deterministic.

A fixed seed MUST be recorded.

Where possible, the split SHOULD preserve intent distribution using
deterministic stratification.

If an intent has too few samples for normal stratification, the
implementation MUST handle it deterministically and record the resulting
distribution.

------------------------------------------------------------------------

# 5. Evaluation Dataset

## 5.1 Existing Dataset

The primary source is the existing Phase 1 synthetic customer-query
dataset:

``` text
data/customer_query_logs.txt
data/query_labels.json
data/processed_queries.json
```

The implementation MUST inspect the actual existing schema before
constructing evaluation cases.

The evaluation MUST NOT invent labels that conflict with the existing
dataset.

------------------------------------------------------------------------

## 5.2 Evaluation Case Format

Create a versioned evaluation-case representation.

Recommended location:

``` text
evaluation/
├── evaluation_cases.json
├── route_mapping.json
├── retrieval_ground_truth.json
└── config.json
```

An evaluation case SHOULD contain:

``` json
{
  "case_id": "EVAL-0001",
  "query": "What is my account balance?",
  "intent": "balance_inquiry",
  "customer_id": "CUST001",
  "expected_route": "TOOL",
  "expected_tools": ["get_balance"],
  "expected_sources": [],
  "category": "customer_specific"
}
```

The exact fields MAY be adapted to the existing dataset, but the
evaluation representation MUST be explicit and machine-readable.

------------------------------------------------------------------------

# 6. Ground Truth

Ground truth MUST be explicit.

The implementation MUST NOT evaluate correctness by assuming that
whatever the system produced is correct.

## 6.1 Intent Ground Truth

Existing Phase 1 intent labels remain the source for intent ground
truth.

The implementation MUST preserve the original intent labels.

------------------------------------------------------------------------

## 6.2 Route Ground Truth

The existing 19 intent labels are not automatically equivalent to the
Phase 6 route labels:

``` text
TOOL
RAG
BOTH
CLARIFICATION
UNSUPPORTED
```

Therefore, Phase 10 MUST create an explicit versioned mapping:

``` text
intent → expected route
```

Example:

``` json
{
  "balance_inquiry": "TOOL",
  "transaction_history": "TOOL",
  "loan_requirements": "RAG",
  "balance_and_home_loan_question": "BOTH"
}
```

The actual mapping MUST be based on the real Phase 1 intents and the
Phase 6 routing contract.

Unmapped intents MUST NOT silently receive a default route.

Unmapped intents MUST produce an evaluation validation error.

------------------------------------------------------------------------

## 6.3 Tool Ground Truth

For customer-specific tool queries, define the expected banking tool(s).

Examples:

``` text
balance inquiry → get_balance
transaction history → get_transactions
loan details → get_loan_details
customer profile → get_customer_profile
```

The implementation MUST use the actual Phase 4 tool names.

Tool execution correctness MUST distinguish:

1.  Correct tool selected.
2.  Tool executed successfully.
3.  Correct customer scope used.
4.  Valid structured result returned.

------------------------------------------------------------------------

## 6.4 RAG Ground Truth

RAG evaluation requires expected relevant knowledge documents.

Ground truth SHOULD identify the relevant KB document(s), not raw vector
IDs.

Example:

``` json
{
  "case_id": "EVAL-0031",
  "expected_documents": [
    "05_credit_card_policy.md"
  ]
}
```

Where an intent legitimately maps to multiple documents, multiple
documents MAY be listed.

The implementation MUST NOT use Qdrant internal point IDs as evaluation
ground truth.

------------------------------------------------------------------------

## 6.5 Response Ground Truth

Exact string matching MUST NOT be the primary response-quality metric.

Banking responses can be phrased differently while remaining correct.

Response evaluation MUST focus on:

-   evidence/grounding,
-   required facts,
-   unsupported-claim behavior,
-   refusal behavior where applicable,
-   source provenance where required.

------------------------------------------------------------------------

# 7. Evaluation Categories

The evaluation suite MUST cover at least these categories:

``` text
1. Routing
2. Tool selection
3. Tool execution
4. RAG retrieval
5. Response grounding
6. Safety / refusal
7. End-to-end behavior
8. Latency
```

------------------------------------------------------------------------

# 8. Routing Evaluation

## 8.1 Metric

Calculate:

``` text
Route Accuracy =
correct predicted routes / total evaluated routes
```

Supported routes:

``` text
TOOL
RAG
BOTH
CLARIFICATION
UNSUPPORTED
```

Also produce a confusion matrix.

Example:

``` text
Expected → Predicted

             TOOL  RAG  BOTH  CLAR  UNSUP
TOOL
RAG
BOTH
CLARIFICATION
UNSUPPORTED
```

The report MUST show per-route counts.

------------------------------------------------------------------------

# 9. Banking Tool Evaluation

## 9.1 Tool Selection Accuracy

Calculate:

``` text
Tool Selection Accuracy =
correct expected tool selection / tool-evaluable cases
```

For multi-tool queries, comparison MUST account for the expected tool
set.

Set comparison SHOULD use:

``` text
precision
recall
F1
```

where appropriate.

------------------------------------------------------------------------

## 9.2 Tool Execution

Validate:

-   expected tool exists,
-   tool was called,
-   customer ID was correctly scoped,
-   tool returned a structured result,
-   no unauthorized customer data was accessed,
-   execution errors were handled correctly.

The evaluator MUST NOT inspect raw JSON data as a replacement for tool
execution.

------------------------------------------------------------------------

# 10. RAG Evaluation

Phase 5 uses:

``` text
Qdrant
Collection: novabank_knowledge
Embedding:
sentence-transformers/all-MiniLM-L6-v2
Dimensions: 384
Distance: cosine
```

The evaluation MUST use the existing RAGRetriever interface.

It MUST NOT directly implement an alternative retrieval algorithm just
for evaluation.

------------------------------------------------------------------------

## 10.1 Hit@K

Calculate:

``` text
Hit@K =
queries where at least one relevant document appears in top K
/
total RAG-evaluable queries
```

At minimum report:

``` text
Hit@1
Hit@3
Hit@5
```

------------------------------------------------------------------------

## 10.2 Mean Reciprocal Rank

For each query:

``` text
RR = 1 / rank_of_first_relevant_document
```

If no relevant document is retrieved:

``` text
RR = 0
```

Then:

``` text
MRR = mean(RR)
```

------------------------------------------------------------------------

## 10.3 Retrieval Failure Analysis

The evaluation report MUST include examples of failed retrievals.

For each selected failure, report:

-   query,
-   expected document,
-   retrieved documents,
-   retrieval rank,
-   relevant failure category if identifiable.

Do not expose raw vector internals in the user-facing UI.

------------------------------------------------------------------------

# 11. Response Grounding Evaluation

The system's response MUST be evaluated against the evidence available
to the system.

The evaluator SHOULD check:

### For TOOL responses

-   response uses tool-provided facts,
-   no unsupported customer-specific facts are introduced,
-   customer ID scope is correct.

### For RAG responses

-   response is supported by retrieved KB content,
-   source provenance exists when expected,
-   unsupported policy claims are avoided.

### For BOTH responses

-   customer-specific claims come from tools,
-   policy/general claims come from RAG,
-   the two evidence types are not confused.

### For unsupported queries

-   system does not fabricate an answer,
-   system uses the expected unsupported/refusal behavior.

------------------------------------------------------------------------

# 12. Response Evaluation Modes

Two evaluation modes are permitted.

## 12.1 Deterministic Evaluation --- Required

The core test suite MUST work without an external LLM.

Deterministic checks SHOULD include:

-   expected route,
-   expected tools,
-   expected source document,
-   provenance presence,
-   required factual fields,
-   refusal behavior,
-   unsupported-claim indicators where deterministic detection is
    practical.

------------------------------------------------------------------------

## 12.2 Optional LLM-as-Judge

An optional LLM-as-judge MAY be implemented for richer response-quality
evaluation.

It MUST:

-   be disabled by default,
-   require explicit configuration,
-   never be required for unit tests,
-   use a configurable provider/model,
-   record model/provider information in the report,
-   use a structured JSON scoring format,
-   evaluate only supplied evidence and response,
-   not be treated as absolute ground truth.

Suggested dimensions:

``` text
groundedness
relevance
completeness
safety
```

Scores MUST NOT replace deterministic correctness metrics.

The judge prompt MUST explicitly instruct the judge not to reward
unsupported claims.

------------------------------------------------------------------------

# 13. Safety Evaluation

Phase 10 MUST evaluate at least:

## 13.1 Prompt Injection

Examples should include attempts to:

-   override system instructions,
-   request hidden prompts,
-   request internal tool information,
-   force unauthorized customer access,
-   bypass routing/security controls.

Metric:

``` text
Safety Success Rate =
correctly handled safety cases / total safety cases
```

------------------------------------------------------------------------

## 13.2 Customer Isolation

Evaluation MUST verify that:

``` text
customer A query → customer A data only
customer B query → customer B data only
```

The user query MUST NOT be allowed to override the trusted customer
identity supplied by the application layer.

------------------------------------------------------------------------

## 13.3 Hallucination / Unsupported Claims

Include cases where the available system evidence does not support the
requested claim.

The expected behavior is to:

-   refuse,
-   clarify,
-   or state that the information is unavailable,

rather than fabricate an answer.

------------------------------------------------------------------------

# 14. End-to-End Evaluation

The final evaluation SHOULD exercise the real Phase 7/8 flow:

``` text
query
 ↓
MemoryOrchestrator
 ↓
BankingOrchestrator
 ↓
Tools / RAG
 ↓
response
 ↓
memory persistence
```

Where practical, use the Phase 8 Chat API path rather than bypassing
application layers.

The evaluator MUST NOT create a parallel implementation of the
application logic.

------------------------------------------------------------------------

# 15. Latency Benchmarking

Phase 10 MUST measure system latency.

At minimum measure:

``` text
End-to-end latency
```

Where instrumentation is practical, also measure:

``` text
routing latency
tool execution latency
RAG retrieval latency
response generation latency
memory latency
```

------------------------------------------------------------------------

## 15.1 Required Statistics

Report:

``` text
min
mean
median
p50
p95
max
```

For latency distributions with sufficient samples.

At minimum, p50 and p95 MUST be reported.

------------------------------------------------------------------------

## 15.2 Benchmark Conditions

Benchmark configuration MUST record:

-   number of queries,
-   dataset split,
-   LLM mode/provider,
-   embedding model,
-   Qdrant mode,
-   retrieval top-k,
-   machine/runtime information where practical,
-   warm/cold condition if applicable.

The report MUST distinguish:

``` text
cold start
warm run
```

when both are measured.

Latency numbers MUST NOT be presented as production SLA guarantees.

------------------------------------------------------------------------

# 16. Baseline Evaluation

Before optimization, run a baseline evaluation.

The baseline MUST capture the current system configuration.

Recommended artifact:

``` text
reports/baseline_evaluation.json
reports/baseline_evaluation.md
```

The baseline report MUST contain:

-   configuration,
-   dataset version,
-   split information,
-   routing metrics,
-   tool metrics,
-   RAG metrics,
-   response metrics,
-   safety metrics,
-   latency metrics,
-   failures/examples,
-   timestamp.

The baseline MUST be preserved before optimization changes are applied.

------------------------------------------------------------------------

# 17. Optimization Strategy

Optimization MUST be evidence-driven.

Do not modify parameters merely because they appear theoretically
better.

Potential optimization targets include:

### RAG

-   top-k,
-   retrieval settings,
-   chunk size/overlap if supported by the existing design,
-   retrieval filtering,
-   query handling.

### Routing

-   classification prompt,
-   routing thresholds,
-   clarification threshold,
-   deterministic routing rules where already supported.

### Response Generation

-   prompt wording,
-   grounding instructions,
-   source-use instructions.

### Performance

-   unnecessary repeated retrieval,
-   unnecessary tool calls,
-   redundant computation,
-   configuration-level performance improvements.

Optimization MUST preserve existing architecture unless a measured issue
requires an architectural change.

------------------------------------------------------------------------

# 18. Optimization Rules

Every optimization candidate MUST have:

``` text
1. Hypothesis
2. Parameter/configuration changed
3. Reason for change
4. Development-set evaluation
5. Comparison with baseline
6. Regression check
7. Decision
```

Example:

``` text
Hypothesis:
Increasing RAG top-k from 3 to 5 may improve retrieval recall.

Change:
top_k = 5

Evaluate:
development set

Measure:
Hit@1, Hit@3, Hit@5, MRR, latency

Decision:
retain only if the measured trade-off is acceptable and no regression occurs.
```

The implementation MUST NOT automatically modify source code based on
evaluation results without explicit deterministic rules.

------------------------------------------------------------------------

# 19. Holdout Evaluation

After optimization decisions are finalized:

``` text
Development set
    ↓
Optimization
    ↓
Freeze configuration
    ↓
Holdout set
    ↓
Final evaluation
```

The holdout set MUST NOT influence parameter selection.

The final report MUST clearly distinguish:

``` text
Baseline / Development
Optimized / Development
Optimized / Holdout
```

If the implementation accidentally uses holdout results during
optimization, this MUST be reported as an evaluation-integrity failure.

------------------------------------------------------------------------

# 20. Regression Requirements

Phase 10 MUST run all existing regression tests.

Expected minimum:

``` text
Phase 3 tests
Phase 4 tests
Phase 5 tests
Phase 6 tests
Phase 7 tests
Phase 8 tests
Phase 9 tests
Phase 10 tests
```

No previous phase may regress.

The final report MUST provide:

``` text
total passed
total failed
warnings
skipped
```

Any failure MUST be investigated.

A Phase 10 implementation MUST NOT be marked complete if existing
functionality is broken.

------------------------------------------------------------------------

# 21. Required Project Structure

A recommended structure is:

``` text
evaluation/
├── __init__.py
├── evaluation_cases.json
├── route_mapping.json
├── retrieval_ground_truth.json
└── config.json

app/
└── evaluation/
    ├── __init__.py
    ├── models.py
    ├── dataset.py
    ├── metrics.py
    ├── evaluators.py
    ├── runner.py
    ├── benchmark.py
    └── judge.py

scripts/
├── run_evaluation.py
├── run_benchmark.py
└── run_optimization.py

reports/
├── baseline_evaluation.json
├── baseline_evaluation.md
├── optimized_evaluation.json
├── optimized_evaluation.md
└── final_holdout_evaluation.json

tests/
├── test_evaluation_dataset.py
├── test_evaluation_metrics.py
├── test_evaluators.py
└── test_benchmark.py
```

The implementation MAY adapt filenames if the existing project structure
makes another organization more appropriate, but responsibilities MUST
remain equivalent.

------------------------------------------------------------------------

# 22. Evaluation Configuration

Create a centralized configuration.

Example:

``` python
EVALUATION_SEED = 42

DEV_RATIO = 0.80
HOLDOUT_RATIO = 0.20

RAG_EVAL_TOP_K = [1, 3, 5]

MAX_EVALUATION_CASES = None

ENABLE_LLM_JUDGE = False

BENCHMARK_WARMUP_RUNS = 1
BENCHMARK_RUNS = 3
```

Actual values MAY be adjusted based on the existing project.

Configuration MUST NOT be scattered across evaluation scripts.

------------------------------------------------------------------------

# 23. Machine-Readable Result Format

Evaluation results MUST be saved in JSON.

Recommended structure:

``` json
{
  "metadata": {
    "phase": 10,
    "seed": 42,
    "dataset_version": "v1",
    "mode": "offline"
  },
  "routing": {
    "accuracy": 0.0,
    "confusion_matrix": {}
  },
  "tools": {
    "selection_accuracy": 0.0,
    "execution_success_rate": 0.0
  },
  "rag": {
    "hit_at_1": 0.0,
    "hit_at_3": 0.0,
    "hit_at_5": 0.0,
    "mrr": 0.0
  },
  "response": {
    "grounding_rate": 0.0
  },
  "safety": {
    "success_rate": 0.0
  },
  "latency_ms": {
    "mean": 0.0,
    "p50": 0.0,
    "p95": 0.0,
    "max": 0.0
  }
}
```

The implementation MAY extend this structure.

------------------------------------------------------------------------

# 24. Human-Readable Report

Generate a Markdown report containing:

## Executive Summary

-   baseline results,
-   optimized results,
-   holdout results,
-   major findings.

## Dataset

-   total cases,
-   development cases,
-   holdout cases,
-   intent distribution.

## Routing

-   accuracy,
-   confusion matrix,
-   failure analysis.

## Tools

-   selection accuracy,
-   execution success,
-   failures.

## RAG

-   Hit@1,
-   Hit@3,
-   Hit@5,
-   MRR,
-   retrieval failures.

## Response Quality

-   deterministic grounding results,
-   optional judge results if enabled.

## Safety

-   injection handling,
-   customer isolation,
-   unsupported-query handling.

## Performance

-   latency statistics,
-   benchmark conditions.

## Optimization

For each optimization:

``` text
Hypothesis
Before
Change
After
Trade-offs
Decision
```

## Holdout

Clearly identify final holdout results.

## Regression

List all test results.

------------------------------------------------------------------------

# 25. Testing Requirements

Phase 10 MUST include automated tests for:

### Dataset

-   evaluation dataset loads,
-   required fields exist,
-   IDs are unique,
-   source queries exist,
-   route mappings are complete,
-   no duplicate query leakage between dev and holdout.

### Splitting

-   deterministic split,
-   fixed seed,
-   expected ratio,
-   no overlap.

### Metrics

Test known synthetic examples for:

-   accuracy,
-   precision,
-   recall,
-   F1,
-   Hit@K,
-   MRR,
-   latency statistics.

### Routing Evaluator

-   correct route,
-   incorrect route,
-   confusion matrix.

### Tool Evaluator

-   single expected tool,
-   multi-tool case,
-   missing tool,
-   incorrect tool.

### RAG Evaluator

-   relevant document at rank 1,
-   relevant document at rank 3,
-   relevant document absent,
-   multiple relevant documents.

### Safety Evaluator

-   prompt injection handled,
-   customer isolation,
-   unsupported request handling.

### Benchmark

-   latency collection,
-   percentile calculation,
-   warm-up behavior,
-   report generation.

### Integration

-   evaluation can invoke the existing orchestrator,
-   evaluation can use existing RAG,
-   evaluation can use existing tools,
-   existing application tests continue to pass.

------------------------------------------------------------------------

# 26. Offline Test Requirement

The normal Phase 10 test suite MUST work without:

-   OpenAI API keys,
-   Anthropic API keys,
-   Gemini API keys,
-   Groq API keys,
-   internet access.

Use the existing deterministic/offline LLM behavior where appropriate.

Optional LLM-as-judge tests MUST be isolated and skipped unless
explicitly enabled.

------------------------------------------------------------------------

# 27. Dependency Rules

Do not introduce unnecessary dependencies.

Before adding a dependency:

1.  Check whether the project already provides equivalent functionality.
2.  Prefer Python standard-library functionality for simple metrics.
3.  Document any new dependency.
4.  Ensure the dependency does not break existing phases.

Do not introduce another vector database or another orchestration
framework.

------------------------------------------------------------------------

# 28. Security and Privacy

All evaluation data MUST remain synthetic.

Do not introduce:

-   real customer information,
-   real bank account numbers,
-   real financial records,
-   API secrets,
-   production credentials.

Evaluation reports MUST NOT expose:

-   API keys,
-   environment secrets,
-   raw internal prompts unless intentionally included for debugging,
-   raw database credentials,
-   private configuration secrets,
-   unnecessary customer data.

Customer IDs may be used because they are synthetic.

------------------------------------------------------------------------

# 29. Failure Handling

Evaluation failures MUST be explicit.

Examples:

``` text
ERROR: Missing route mapping for intent "..."
ERROR: Evaluation case has unknown tool "..."
ERROR: Retrieval ground truth references missing document
ERROR: Development/holdout overlap detected
ERROR: Baseline result unavailable
```

Do not silently skip invalid evaluation cases.

Invalid evaluation configuration MUST fail fast.

------------------------------------------------------------------------

# 30. Reproducibility Metadata

Every evaluation report SHOULD record:

``` text
phase
timestamp
evaluation seed
dataset version
number of cases
development size
holdout size
LLM provider/model
embedding model
Qdrant collection
retrieval top-k
configuration values
software/dependency versions where practical
```

Secrets MUST NEVER be recorded.

------------------------------------------------------------------------

# 31. Optimization Acceptance Criteria

An optimization may be retained only when:

1.  The change has a documented hypothesis.
2.  The development-set metric improves or a documented trade-off is
    justified.
3.  No critical safety regression occurs.
4.  No previous-phase regression occurs.
5.  Latency does not materially degrade without justification.
6.  The optimized configuration is reproducible.
7.  The change does not violate the Phase 1--9 architecture contract.

The final holdout evaluation MUST be performed only after the
configuration is frozen.

------------------------------------------------------------------------

# 32. Definition of Done

Phase 10 is complete only when all of the following are true:

### Evaluation Dataset

-   [ ] Existing 200 synthetic query records are successfully consumed.
-   [ ] Evaluation cases are versioned.
-   [ ] Intent ground truth is preserved.
-   [ ] Route mappings are explicit.
-   [ ] Tool ground truth is explicit where applicable.
-   [ ] RAG document ground truth is explicit where applicable.
-   [ ] Development/holdout split is deterministic.
-   [ ] No development/holdout leakage exists.

### Evaluation

-   [ ] Routing accuracy implemented.
-   [ ] Routing confusion matrix implemented.
-   [ ] Tool selection evaluation implemented.
-   [ ] Tool execution evaluation implemented.
-   [ ] RAG Hit@1 implemented.
-   [ ] RAG Hit@3 implemented.
-   [ ] RAG Hit@5 implemented.
-   [ ] RAG MRR implemented.
-   [ ] Response grounding evaluation implemented.
-   [ ] Safety/refusal evaluation implemented.
-   [ ] Customer-isolation evaluation implemented.
-   [ ] End-to-end latency benchmark implemented.
-   [ ] p50 and p95 latency reported.

### Optimization

-   [ ] Baseline configuration captured.
-   [ ] Baseline results captured.
-   [ ] Optimization candidates evaluated on development data.
-   [ ] Optimization decisions documented.
-   [ ] Final configuration frozen.
-   [ ] Holdout evaluated only after optimization.
-   [ ] Final holdout results reported.

### Quality

-   [ ] Optional LLM-as-judge is disabled by default.
-   [ ] Offline deterministic evaluation works without external API
    keys.
-   [ ] No unnecessary dependencies added.
-   [ ] No real customer data introduced.
-   [ ] No new product features introduced.

### Regression

-   [ ] Phase 3 tests pass.
-   [ ] Phase 4 tests pass.
-   [ ] Phase 5 tests pass.
-   [ ] Phase 6 tests pass.
-   [ ] Phase 7 tests pass.
-   [ ] Phase 8 tests pass.
-   [ ] Phase 9 tests pass.
-   [ ] Phase 10 tests pass.

### Reports

-   [ ] Baseline JSON generated.
-   [ ] Baseline Markdown generated.
-   [ ] Optimized results generated.
-   [ ] Final holdout results generated.
-   [ ] Failures are documented.
-   [ ] Reproducibility metadata is recorded.

------------------------------------------------------------------------

# 33. Required Final Implementation Report

After implementation, report:

1.  Files created.
2.  Files modified.
3.  Evaluation dataset size.
4.  Development/holdout split.
5.  Route mapping summary.
6.  Baseline metrics.
7.  Optimized metrics.
8.  Final holdout metrics.
9.  Optimization changes.
10. Retrieval metrics.
11. Tool metrics.
12. Safety metrics.
13. Latency metrics.
14. Number of Phase 10 tests.
15. Full regression test count.
16. Failures/warnings.
17. Dependency changes.
18. Confirmation that this specification was not modified.
19. Confirmation that no Phase 11/new product functionality was
    implemented.

------------------------------------------------------------------------

# 34. Implementation Constraints for Antigravity

Before implementation:

1.  Inspect the existing Phase 1--9 codebase.
2.  Inspect the existing synthetic datasets.
3.  Inspect the existing RAG, tools, orchestrator, memory, API, and UI
    implementations.
4.  Identify the actual 19 intent labels.
5.  Build the route mapping from the real labels.
6.  Reuse existing interfaces.
7.  Do not rewrite previous phases.
8.  Do not modify this specification.
9.  Do not invent missing ground truth silently.
10. If a required ground-truth mapping cannot be derived safely from the
    existing project, fail validation and report the missing mapping
    rather than guessing.

During implementation:

-   Keep evaluation code isolated.
-   Keep the normal application behavior unchanged unless an
    optimization is explicitly accepted.
-   Keep evaluation deterministic by default.
-   Keep LLM-as-judge optional.
-   Preserve Qdrant as the only vector database.
-   Preserve LangGraph as the orchestrator.
-   Preserve SQLite as conversation memory.
-   Preserve FastAPI and Jinja UI.
-   Do not add authentication.
-   Do not add production integrations.

After implementation:

1.  Run Phase 10 tests.
2.  Run the complete Phase 3--10 regression suite.
3.  Run baseline evaluation.
4.  Run development optimization.
5.  Freeze the final configuration.
6.  Run holdout evaluation.
7.  Generate reports.
8.  Verify the specification has not changed.
9.  Confirm no out-of-scope features were introduced.

------------------------------------------------------------------------

# 35. Phase Boundary

The project roadmap ends with Phase 10.

``` text
Phase 1   Synthetic Data          ✅
Phase 2   Knowledge Base          ✅
Phase 3   Mock Banking APIs       ✅
Phase 4   Banking Tools           ✅
Phase 5   Qdrant RAG              ✅
Phase 6   Agents + Orchestrator   ✅
Phase 7   Conversation Memory     ✅
Phase 8   Chat REST API           ✅
Phase 9   Jinja UI                ✅
Phase 10  Evaluation + Optimization ← CURRENT
```

Phase 10 MUST NOT create a new feature phase.

The goal is to produce a measured, reproducible, optimized,
regression-safe final version of the existing NovaBank banking
assistant.
