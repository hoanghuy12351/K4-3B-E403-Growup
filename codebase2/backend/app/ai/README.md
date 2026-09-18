# Growup deterministic diagnostic AI

This package is the Python migration of the Phase 1 logic in legacy `codebase/ai/`, extended in Phase 2 with server-side LLM providers. It has no frontend integration or diagnostic HTTP route.

The package finds the repository root from `data/` and `codebase2/`, then reads the existing VLearn pack in place. CSV searches use `csv.DictReader`, stream rows, and have configurable scan and result bounds. Historical student text is untrusted evidence, retained only as short excerpts with anonymized turn IDs.

The pipeline is teaching content → deterministic concept seed → historical question retrieval → one optional structured LLM request → local grounding validation → reviewable diagnostic question. Response aggregation remains separate and deterministic.

`AI_MODE=deterministic` uses Phase 1 only and needs no API key. `AI_MODE=llm` requires the selected provider configuration and raises a typed error on failure. `AI_MODE=hybrid` tries the selected provider and falls back to Phase 1 only when `AI_FALLBACK_TO_DETERMINISTIC=true`; the result records `fallbackUsed` and a safe `fallbackReason`.

Supported server-only provider families are OpenAI (Responses API), Gemini (Interactions API), and NVIDIA NIM (OpenAI-compatible chat completions or explicitly configured Responses API). Configure models and credentials in the backend environment using `.env.example`; never put credentials in frontend variables. Implemented provider adapters are covered by mocks only. No real-credential smoke test has been run by this implementation.

Run tests from the repository root:

```powershell
python -m unittest discover -s codebase2/backend/tests -p "test_*.py"
```

For a deterministic local demonstration:

```powershell
python codebase2/backend/scripts/diagnostic_cli.py --mode deterministic --title "Tokenization" --text "A token can be a word, part of a word, or a character." --source-id "slide-test"
```

After explicitly configuring a real server-side credential, smoke-test only the selected provider:

```powershell
python codebase2/backend/scripts/llm_smoke_test.py --provider openai
```

Pydantic is the runtime source of truth for LLM output. Semantic validation rejects invented evidence/source IDs, broken misconception mappings, duplicate IDs, and non-single-correct questions. External evidence is limited to bounded `turnId` and `studentQuestion` fields. The system cannot prove pedagogical quality automatically, so lecturer review remains required.
