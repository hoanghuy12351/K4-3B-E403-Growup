# Growup AI diagnostic foundation

This folder is a deterministic, server-side-ready foundation for the classroom diagnostic flow. It does not call an LLM, alter the existing demo UI, or require an API key.

`generateDiagnosticCheck()` prepares one question before a lecturer interrupts a lesson. It extracts concepts from supplied slide text, finds bounded historical VLearn questions, groups possible historical confusion patterns with short evidence excerpts, and creates a reviewable question. The lecturer-facing application remains responsible for review and publishing.

The VLearn adapter finds `data/` by walking up from this folder, so it does not use a fixed computer path. It streams the CSV for searches and exposes only anonymized turn IDs and the fields needed by the pipeline. Student-authored text remains untrusted data; no content is executed or rendered by this module.

Run the lightweight checks from the repository root:

```powershell
node --test codebase/tests/ai/*.test.js
```

The schema is stored in `schemas/diagnostic-question.schema.json`; `validateDiagnosticQuestion()` is the dependency-free runtime validation used in Phase 1. The prompt files document future LLM replacement boundaries only.
