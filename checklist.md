# localGPT Evaluation Checklist — Results

**Date tested:** _____________
**Version/build of localGPT:** _____________
**Machine specs (CPU/GPU/RAM):** _____________
**Model loaded:** _____________

---

## 1. Precision of Problem Statement

| # | Test | Prompt to use | Expected behavior | Result | Notes |
|---|------|----------------|--------------------|--------|-------|
| 1.1 | Ambiguous prompt | "Tell me about the report." (with a vague/unspecified doc) | Should ask for clarification or state its assumption | ✅ Pass | Correctly asked for the report instead of guessing |
| 1.2 | Multi-constraint | "Summarize this in exactly 3 bullet points, under 15 words each, formal tone" | All constraints honored | ✅ Pass | |
| 1.3 | Negative constraint | "Summarize this but don't mention [specific name/term]" | Term is not leaked | ⚠️ Partial | Term not leaked, but model loses track of context — asks for the report again even though it was already given; only reconnects once told "I gave you the report already." Context-tracking weakness, not a constraint-following failure. |
| 1.4 | Buried-answer precision | Feed a long doc, ask about a fact in the middle | Correct answer, not just intro/conclusion | ⚠️ Flag | Response took too long. Likely brute-force scanning (no retrieval/chunking optimization) or a hardware bottleneck (CPU-only / VRAM spill). Needs a follow-up check with Task Manager open during the test. |

---

## 2. Workflow Conditions

| # | Test | How to run it | Expected behavior | Result | Notes |
|---|------|----------------|--------------------|--------|-------|
| 2.1 | File ingestion (PDF) | Upload a PDF, ask a basic question | Correct parsing, no broken formatting | 🚫 Blocked | File upload feature not implemented yet |
| 2.2 | File ingestion (DOCX/CSV) | Upload a docx or csv, ask a basic question | Correct parsing | 🚫 Blocked | Same as above |
| 2.3 | Session persistence | Ask Q1, then a follow-up depending on Q1 | Remembers context correctly | 🚫 Blocked | |
| 2.4 | Latency — short prompt | Time a simple one-line question | Note seconds | 🚫 Blocked | |
| 2.5 | Latency — long context | Time a question against a large doc | Note seconds | 🚫 Blocked | |
| 2.6 | Offline reliability | Disconnect internet fully, then query | Still works, no silent API fallback | 🚫 Blocked | |
| 2.7 | Resource usage | Watch Task Manager while answering | Note RAM/CPU/VRAM peak | 🚫 Blocked | |
| 2.8 | Error handling | Upload a corrupted file / empty prompt | Fails gracefully, no crash | 🚫 Blocked | |

**Note:** Entire section blocked — no file upload/ingestion feature yet. This is a significant gap since RAG-style document workflows appear central to the intended use case.

---

## 3. Capability

| # | Test | Prompt to use | Expected behavior | Result | Notes |
|---|------|----------------|--------------------|--------|-------|
| 3.1 | Reasoning | Give a multi-step logic/math problem | Correct step-by-step answer | ✅ Pass | |
| 3.2 | Retrieval accuracy (RAG) | Ask a question you know the answer to from an uploaded doc | Answer grounded in the doc, not hallucinated | ✅ Pass | |
| 3.3 | Citation/traceability | Ask the same as above, request the source | Points to correct doc/chunk | ✅ Pass | |
| 3.4 | Instruction following (format) | "Output this as a JSON object with keys X, Y, Z" | Valid, correctly structured output | ✅ Pass | |
| 3.5 | Instruction following (table) | "Put this in a markdown table" | Correct table format | ✅ Pass | |
| 3.6 | Knowledge boundary honesty | Ask something outside the uploaded docs/training | Says "I don't know" instead of hallucinating | ✅ Pass | |

---

## Summary

**Overall pass rate:** 6 / 8 runnable tests passed cleanly (2 flagged), 8 blocked

**Strongest area:** Capability (Section 3) — core model reasoning, formatting, and honesty all solid.

**Weakest area:** Workflow conditions — entirely blocked due to missing file upload/ingestion feature.

**Biggest concern before relying on it for real workflows:** No document ingestion means the tool can't yet do the RAG-based workflows it seems designed for. Secondary concern: long-context latency on 1.4.

**Next steps / follow-up tests needed:**
- Re-run 1.4 with Task Manager open to isolate hardware vs. retrieval-architecture cause
- Re-run all of Section 2 once file upload ships
- Watch whether 1.3's context-tracking issue persists across longer sessions