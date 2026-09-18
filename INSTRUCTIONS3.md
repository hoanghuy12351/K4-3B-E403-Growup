# INSTRUCTIONS3.md — Migrate Phase 1 AI Logic into `codebase2`

## 0. Purpose

The repository now has a new application structure on `main` under:

```text
codebase2/
├── agora-frontend/
└── backend/
```

The branch `feat/ai-diagnostic-engine` already contains the completed **Phase 1 deterministic diagnostic AI foundation** under the old:

```text
codebase/ai/
codebase/tests/ai/
```

`INSTRUCTIONS2.md` has NOT been implemented yet.

This task is ONLY a migration / port of everything completed **before Phase 2** into the new `codebase2` architecture.

Do NOT implement OpenAI, Gemini, NVIDIA NIM, or any other LLM integration in this task.

---

# 1. Branch and Git safety

Work only on:

```text
feat/ai-diagnostic-engine
```

First verify:

```bash
git branch --show-current
```

Expected:

```text
feat/ai-diagnostic-engine
```

Then fetch the latest remote state:

```bash
git fetch origin
```

The new `codebase2/` currently lives on `main`, so bring the latest `main` changes INTO the feature branch:

```bash
git merge origin/main
```

Important:

- merge `origin/main` into `feat/ai-diagnostic-engine`
- DO NOT merge the feature branch into `main`
- DO NOT checkout and edit `main`
- DO NOT force-push
- DO NOT rewrite history
- DO NOT delete the old Phase 1 implementation yet
- if a merge conflict occurs, preserve the new `codebase2/` from `main` and preserve the existing Phase 1 files in `codebase/ai/` for reference

After the merge, verify both exist:

```text
codebase/ai/
codebase2/
```

If `codebase2/` is already present on the feature branch, do not duplicate it.

---

# 2. Source of truth for this migration

The behavior to port is the existing implementation in:

```text
codebase/ai/
├── README.md
├── config.js
├── index.js
├── data/
│   └── vlearnAdapter.js
├── services/
│   ├── conceptExtractor.js
│   ├── misconceptionMiner.js
│   ├── questionGenerator.js
│   └── responseAnalyzer.js
├── prompts/
└── schemas/
```

and tests in:

```text
codebase/tests/ai/
├── vlearnAdapter.test.js
├── diagnosticPipeline.test.js
└── responseAnalyzer.test.js
```

Treat these files as the **behavioral reference**.

Do NOT simply move or copy JavaScript files into the Python backend.

Port the behavior into idiomatic Python while preserving:

- inputs
- outputs
- deterministic behavior
- validation rules
- evidence traceability
- bounded data access
- fallback-free Phase 1 behavior

---

# 3. New target architecture

All migrated AI/backend logic must live inside:

```text
codebase2/backend/
```

Recommended structure:

```text
codebase2/
└── backend/
    ├── app/
    │   ├── ai/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── pipeline.py
    │   │   │
    │   │   ├── data/
    │   │   │   ├── __init__.py
    │   │   │   └── vlearn_adapter.py
    │   │   │
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   ├── concept_extractor.py
    │   │   │   ├── misconception_miner.py
    │   │   │   ├── question_generator.py
    │   │   │   └── response_analyzer.py
    │   │   │
    │   │   ├── prompts/
    │   │   │   ├── concept-extraction.md
    │   │   │   ├── misconception-mining.md
    │   │   │   ├── question-generation.md
    │   │   │   └── response-analysis.md
    │   │   │
    │   │   └── schemas/
    │   │       └── diagnostic-question.schema.json
    │   │
    │   ├── config.py
    │   ├── main.py
    │   ├── models/
    │   ├── routers/
    │   ├── schemas/
    │   ├── services/
    │   └── utils/
    │
    └── tests/
        └── ai/
            ├── __init__.py
            ├── test_vlearn_adapter.py
            ├── test_diagnostic_pipeline.py
            └── test_response_analyzer.py
```

Small naming changes are acceptable if they better match the existing Python project.

Keep the Phase 1 AI domain grouped together.

Do NOT scatter the migrated implementation across unrelated `user_service.py`, database files, or frontend files.

---

# 4. Hard source-code boundary

For this task, create or modify application source only under:

```text
codebase2/
```

The old:

```text
codebase/
```

is **read-only reference** for this migration.

Do not add new logic to `codebase/`.

Do not delete `codebase/ai/` yet.

It must remain available until the Python migration has been verified.

---

# 5. Data boundary

The project already has local raw data at repository root:

```text
data/
```

This directory remains outside both `codebase/` and `codebase2/`.

Rules:

- treat `data/` as read-only
- do not move it into `codebase2`
- do not copy the raw VLearn pack
- do not modify raw CSV/PDF/transcript files
- do not commit raw data
- do not hard-code a local Windows absolute path
- locate the repository root dynamically
- the repository root should be identified by the presence of at least:
  - `data/`
  - `codebase2/`

The expected relevant local data still includes a VLearn pack with:

```text
tutor_turns.csv
DATA_DICTIONARY.md
transcript/
slides/
```

The adapter must discover the exact path instead of assuming the pack is always at one fixed nested location.

---

# 6. Important architecture decision

`codebase2/backend` is now Python.

Therefore:

```text
OLD:
Node / CommonJS deterministic Phase 1

NEW:
Python deterministic Phase 1
```

This is a behavioral port, not a language-preserving file move.

The migrated pipeline must NOT invoke Node.js subprocesses to reuse the old JS implementation.

Do not do:

```python
subprocess.run(["node", ...])
```

The new backend must implement the logic natively in Python.

---

# 7. What exactly must be migrated

The following Phase 1 capabilities must all exist in `codebase2/backend`.

## 7.1 Repository / dataset discovery

Equivalent to the old `findRepositoryRoot()` and VLearn path discovery.

Python should be able to start from a file inside:

```text
codebase2/backend/app/ai/
```

and find the root containing:

```text
data/
codebase2/
```

Return clear errors when the root or dataset cannot be found.

---

## 7.2 VLearn adapter

Port the behavior of:

```text
codebase/ai/data/vlearnAdapter.js
```

Responsibilities:

- discover VLearn files
- validate required resources
- expose dataset information
- stream or iterate over `tutor_turns.csv`
- normalize rows
- search historical student questions
- return bounded results
- search examples by concept

Recommended public Python methods:

```python
get_dataset_info()

search_student_questions(
    query=None,
    lecture_code=None,
    lecture_title=None,
    cohort_hint=None,
    limit=30,
)

get_question_examples_for_concept(
    concepts,
    limit=30,
)
```

Normalized historical question:

```python
{
    "turnId": "...",
    "lectureCode": "...",
    "lectureTitle": "...",
    "studentQuestion": "...",
    "askedAt": "...",
    "cohortHint": "...",
}
```

Preserve these camelCase external keys if necessary for parity with Phase 1.

Internally, Python functions may use snake_case.

---

# 8. CSV handling

Use Python standard library:

```python
csv
```

Prefer:

```python
csv.DictReader
```

and iterate row by row.

Do NOT load the entire CSV into memory just to find a small number of rows.

Maintain a configurable scan bound equivalent to:

```text
searchScanLimit = 15000
```

Maintain a hard result upper bound of approximately:

```text
100
```

unless a clear existing Phase 1 behavior says otherwise.

---

# 9. Concept extractor

Port the existing deterministic concept extraction behavior.

Input conceptually:

```python
{
    "sourceText": "...",
    "title": "...",
    "sourceId": "slide-12",
}
```

Output:

```python
{
    "topic": "...",
    "concepts": [...],
    "learningObjectives": [...],
    "sourceId": "...",
}
```

Requirements:

- deterministic
- no API call
- no embedding
- no external service
- same purpose as old `conceptExtractor.js`
- preserve basic Vietnamese + English token support
- preserve stop-word style filtering or an equivalent deterministic approach

Do not "improve" it into an LLM feature in this migration.

---

# 10. Misconception miner

Port the existing heuristic Phase 1 logic.

The current logic categorizes historical questions approximately as:

```text
distinction
definition
application
general
```

and creates evidence-backed possible misconception records.

Output should remain conceptually compatible:

```python
{
    "misconceptions": [
        {
            "id": "M001-...",
            "concept": "...",
            "statement": "...",
            "evidence": [
                {
                    "turnId": "...",
                    "excerpt": "..."
                }
            ],
            "evidenceCount": 3,
            "confidence": 0.65
        }
    ]
}
```

Important:

- retain evidence `turnId`
- cap evidence excerpts
- prevent duplicate evidence IDs
- do not claim a misconception is definitely true
- use wording such as "Possible historical confusion"
- remain deterministic

---

# 11. Question generator

Port the existing deterministic Phase 1 question generator.

Input:

```python
concept_context
misconceptions
source_context
```

Output must match the diagnostic question contract:

```python
{
    "id": "Q-...",
    "topic": "...",
    "concept": "...",
    "question": "...",
    "learningObjective": "...",
    "source": [
        {
            "type": "slide",
            "id": "..."
        }
    ],
    "options": [
        {
            "id": "A",
            "text": "...",
            "correct": True,
            "misconceptionId": None
        },
        {
            "id": "B",
            "text": "...",
            "correct": False,
            "misconceptionId": "M001"
        }
    ]
}
```

Do not introduce LLM generation.

The goal is parity with the old deterministic generator.

---

# 12. Diagnostic schema and runtime validation

Copy/adapt the existing Phase 1 JSON schema into:

```text
codebase2/backend/app/ai/schemas/diagnostic-question.schema.json
```

Also implement dependency-light runtime validation in Python.

Validation rules must include:

- required question fields exist
- question text is non-empty
- options are non-empty
- each option contains:
  - `id`
  - `text`
  - `correct`
  - `misconceptionId`
- exactly one option is correct
- correct option has:
  - `misconceptionId = None`
- output errors are clear and useful

Do not add a heavy JSON Schema package just for this migration unless already present.

---

# 13. Response analyzer

Port the deterministic response analyzer.

Input:

```python
{
    "question": {...},
    "responses": [
        {"optionId": "A"},
        {"optionId": "B"},
    ]
}
```

Output:

```python
{
    "totalResponses": 40,
    "correctRate": 0.675,
    "status": "uncertain",
    "misconceptionSignals": [
        {
            "misconceptionId": "M001",
            "count": 13,
            "ratio": 0.325
        }
    ],
    "recommendation": "..."
}
```

Initial thresholds must preserve Phase 1:

```text
correctRate >= 0.80
→ understood

0.60 <= correctRate < 0.80
→ uncertain

correctRate < 0.60
→ needs_attention
```

Keep thresholds centralized/configurable.

These thresholds are prototype rules, not scientifically validated claims.

---

# 14. High-level pipeline

Port:

```text
generateDiagnosticCheck()
```

into Python.

Recommended API:

```python
generate_diagnostic_check(
    teaching_context,
    options=None,
    adapter=None,
)
```

Expected flow:

```text
teaching context
      ↓
extract_concepts()
      ↓
VLearn adapter
      ↓
historical questions
      ↓
mine_misconceptions()
      ↓
generate_diagnostic_question()
      ↓
validate question
      ↓
return result
```

Result:

```python
{
    "context": {...},

    "historicalEvidence": {
        "matchedQuestions": 12
    },

    "misconceptions": [...],

    "questions": [...]
}
```

Preserve the externally visible result shape so later Phase 2 can build on it.

---

# 15. Public Python package API

Expose a small stable API from:

```text
codebase2/backend/app/ai/__init__.py
```

Recommended exports:

```python
create_vlearn_adapter
extract_concepts
mine_misconceptions
generate_diagnostic_question
analyze_responses
validate_diagnostic_question
generate_diagnostic_check
```

Avoid exposing internal helpers unless tests truly need them.

---

# 16. Configuration

Create AI-specific Phase 1 defaults in:

```text
codebase2/backend/app/ai/config.py
```

Preserve conceptual defaults:

```python
HISTORICAL_QUESTION_LIMIT = 30
QUESTION_COUNT = 1
SEARCH_SCAN_LIMIT = 15000

RESPONSE_THRESHOLDS = {
    "understood": 0.80,
    "uncertain": 0.60,
}
```

Do NOT put LLM/API/provider config here yet.

Do NOT add:

```text
OPENAI_API_KEY
GEMINI_API_KEY
NVIDIA_API_KEY
AI_PROVIDER
AI_MODE
```

Those belong to the later Phase 2 task.

---

# 17. Existing backend files

The current `codebase2/backend` is a scaffold.

Do not unnecessarily implement unrelated backend concerns such as:

```text
PostgreSQL
user authentication
users router
security
database models
Docker production setup
```

For this migration, prefer adding the isolated:

```text
app/ai/
```

package.

Only modify global backend files when required for test/import correctness.

Do not create a FastAPI route for the diagnostic pipeline yet.

Do not change:

```text
app/main.py
```

into a production server unless required by an existing non-AI task.

---

# 18. Frontend rule

Do NOT modify:

```text
codebase2/agora-frontend/
```

for this task.

The new Next.js/Electron frontend is not part of this migration.

There is no Phase 1 browser integration to preserve because the old AI foundation was not connected to the UI yet.

The target at the end is:

```text
codebase2 backend AI package
✅ migrated

frontend → AI backend
❌ not yet connected
```

---

# 19. Prompt files

The old Phase 1 contains prompt-boundary Markdown files for future LLM replacement.

Port them as documentation into:

```text
codebase2/backend/app/ai/prompts/
```

They must remain documentation only.

Do NOT call an LLM with them.

This preserves the intended future architecture without prematurely implementing `INSTRUCTIONS2`.

---

# 20. Tests — parity is mandatory

Port the old Node tests into Python.

Do not merely test "file exists".

Test behavior.

Use Python standard library `unittest` unless the repository already has a chosen test framework after merging `main`.

Preferred zero-dependency command:

```bash
python -m unittest discover -s codebase2/backend/tests -p "test_*.py"
```

The migrated tests must cover at minimum:

## VLearn adapter

- repository/data discovery works
- finds `tutor_turns.csv`
- finds transcript files
- finds slide PDFs
- search is bounded
- normalized result keys are correct

## Diagnostic pipeline

- concept extraction returns at least one concept
- misconception evidence retains `turnId`
- pipeline creates exactly one Phase 1 question
- generated question passes runtime validation

## Response analyzer

Given:

```text
2 wrong mapped to M001
1 correct
```

expect approximately:

```text
totalResponses = 3
correctRate = 0.333
status = needs_attention
M001 count = 2
M001 ratio = 0.667
```

---

# 21. Add one parity test against known Phase 1 behavior

Create at least one fixed deterministic fixture that demonstrates the new Python pipeline preserves the behavior contract of the old JS version.

Example context:

```text
Title:
Tokenization

Teaching text:
A token can be a word, part of a word, or a character.

Source:
slide-12
```

Validate:

```text
context generated
question generated
exactly one correct answer
valid source ID
schema valid
```

Do not require network access.

---

# 22. Data-dependent versus isolated tests

The VLearn adapter integration test may depend on the local ignored `data/` directory.

However, the rest of the unit tests should not all fail just because the raw data pack is unavailable in a CI clone.

Therefore separate:

```text
pure unit tests
```

from:

```text
local dataset integration test
```

If `data/` is unavailable:

- pure unit tests should still run
- dataset integration test may skip clearly with a reason

If the local project has `data/`, the adapter test should run normally.

Do not fabricate raw VLearn data into the repository.

Temporary tiny CSV fixtures created inside a test temp directory are allowed for parser unit tests.

---

# 23. No Phase 2 logic

This is the most important scope rule.

`INSTRUCTIONS2.md` has not been executed.

Do NOT implement any of the following now:

```text
OpenAI
Gemini
NVIDIA NIM
LLM provider abstraction
Responses API
Gemini Interactions API
chat/completions
API retry logic
LLM timeout logic
structured LLM output
LLM fallback mode
AI_PROVIDER
AI_MODE
provider smoke test
LLM CLI
```

The final migrated system must still be:

```text
100% deterministic
0 external AI API calls
0 API keys
```

---

# 24. Do not lose Phase 1 behavior

The migration is not an opportunity to rewrite the product concept.

Preserve:

```text
Slides / teaching content
        ↓
concept extraction
        ↓
historical VLearn questions
        ↓
possible misconception mining
        ↓
diagnostic question
        ↓
response analysis
```

Do not replace this with:

```text
generic quiz generator
```

The key product behavior remains:

```text
wrong answer
     ↓
misconceptionId
```

and historical evidence remains traceable through:

```text
turnId
```

---

# 25. Migration sequence

Codex should execute in this order.

### Step A — sync architecture

```text
fetch origin
merge origin/main into feat/ai-diagnostic-engine
verify codebase2 exists
```

### Step B — inspect references

Read:

```text
codebase/ai/
codebase/tests/ai/
codebase2/backend/
```

Do not edit yet until the mapping is understood.

### Step C — create Python AI package

Create:

```text
codebase2/backend/app/ai/
```

### Step D — port data adapter

Port repository discovery, VLearn discovery, bounded CSV retrieval.

### Step E — port deterministic services

Port:

```text
concept extractor
misconception miner
question generator
response analyzer
```

### Step F — port validation/schema

Port JSON schema + Python runtime validator.

### Step G — port high-level pipeline

Implement:

```python
generate_diagnostic_check(...)
```

### Step H — port tests

Create Python behavioral tests.

### Step I — run verification

Run all migrated tests.

### Step J — compare behavior

Confirm the new Python implementation retains the Phase 1 contract.

Then stop.

---

# 26. Suggested resulting tree

Expected relevant tree:

```text
codebase2/
├── agora-frontend/
│   └── ... existing new frontend unchanged
│
└── backend/
    ├── app/
    │   ├── ai/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── pipeline.py
    │   │   ├── data/
    │   │   │   ├── __init__.py
    │   │   │   └── vlearn_adapter.py
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   ├── concept_extractor.py
    │   │   │   ├── misconception_miner.py
    │   │   │   ├── question_generator.py
    │   │   │   └── response_analyzer.py
    │   │   ├── prompts/
    │   │   │   └── ...
    │   │   └── schemas/
    │   │       └── diagnostic-question.schema.json
    │   │
    │   └── ... existing backend scaffold
    │
    └── tests/
        └── ai/
            ├── __init__.py
            ├── test_vlearn_adapter.py
            ├── test_diagnostic_pipeline.py
            └── test_response_analyzer.py
```

---

# 27. README

Add:

```text
codebase2/backend/app/ai/README.md
```

or update `codebase2/backend/README.md` with a clearly isolated AI section.

Document:

- what was migrated
- that this is Phase 1 deterministic logic
- data location
- test command
- no LLM/API is used yet
- old `codebase/ai` is reference/legacy
- next phase is multi-provider LLM integration, but it is NOT part of this task

Do not rewrite the entire existing backend README unnecessarily.

---

# 28. Manual local smoke test

Add a minimal Python smoke script only if useful, under:

```text
codebase2/backend/scripts/
```

Example:

```text
diagnostic_smoke.py
```

It may call:

```python
generate_diagnostic_check(...)
```

with local teaching context.

Do not add networking.

Do not add LLM APIs.

A smoke script is optional if tests already provide a clear runnable demonstration.

---

# 29. Compatibility target for later Phase 2

Design the Python package so a future LLM implementation can replace/refine:

```text
concept extraction
misconception inference
question generation
```

without rewriting:

```text
VLearn retrieval
result schema
response analyzer
```

However, do not implement that abstraction beyond what is necessary for clean service boundaries.

The important thing is that later Phase 2 can be rewritten for Python rather than applying the old JS `INSTRUCTIONS2.md` blindly.

---

# 30. Important note about `INSTRUCTIONS2.md`

The existing `INSTRUCTIONS2.md` was written for the old Node `codebase/ai` architecture.

After this migration:

```text
DO NOT execute INSTRUCTIONS2.md as-is.
```

It must be adapted to:

```text
codebase2/backend/app/ai/
Python
```

before Phase 2 begins.

This migration task ends before doing that adaptation.

---

# 31. Definition of done

The migration is complete when:

- [ ] latest `origin/main` has been merged into `feat/ai-diagnostic-engine`
- [ ] `codebase2/` new architecture is preserved
- [ ] `codebase2/agora-frontend/` is unchanged
- [ ] old `codebase/ai/` remains available as reference
- [ ] Python `codebase2/backend/app/ai/` exists
- [ ] VLearn adapter is ported
- [ ] local `data/` remains read-only
- [ ] concept extractor is ported
- [ ] misconception miner is ported
- [ ] diagnostic question generator is ported
- [ ] response analyzer is ported
- [ ] diagnostic schema is ported
- [ ] runtime validator is ported
- [ ] `generate_diagnostic_check()` exists
- [ ] external result contract remains compatible with Phase 1
- [ ] Python behavioral tests exist
- [ ] pure tests pass without network
- [ ] local VLearn integration test passes when `data/` exists
- [ ] zero LLM API calls exist
- [ ] zero API provider code exists
- [ ] zero API keys are required
- [ ] no raw data is modified
- [ ] no source code is added outside `codebase2/` during the migration
- [ ] `main` is not modified directly

---

# 32. Verification commands

From repository root:

```bash
git branch --show-current
```

Expected:

```text
feat/ai-diagnostic-engine
```

Check the merge relationship:

```bash
git status
```

Then run Python tests:

```bash
python -m unittest discover -s codebase2/backend/tests -p "test_*.py"
```

If the project later standardizes on pytest and it is already configured, running pytest as an additional check is acceptable, but do not add it solely for this migration.

Check that no accidental LLM/provider implementation exists:

```bash
git diff --name-only origin/main...HEAD
```

Review all created/modified files.

---

# 33. Final report required from Codex

After finishing, report exactly these sections:

## Main sync

State whether `origin/main` was merged successfully and whether conflicts occurred.

## Migrated components

Map old → new, for example:

```text
codebase/ai/data/vlearnAdapter.js
→ codebase2/backend/app/ai/data/vlearn_adapter.py
```

Do this for all Phase 1 modules.

## Files created

List them.

## Files modified

List them.

## Test result

Report:

```text
tests run
passed
failed
skipped
```

If the VLearn test was skipped because `data/` was unavailable, state that explicitly.

## Phase parity

State what behavior was preserved.

## Not implemented

Explicitly state:

```text
No OpenAI integration
No Gemini integration
No NVIDIA NIM integration
No frontend integration
No realtime transcript
```

## Legacy status

Confirm that old `codebase/ai/` was not deleted.

Then STOP.

Do not begin Phase 2.
