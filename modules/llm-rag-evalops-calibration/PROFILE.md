---
name: llm-rag-evalops-calibration
description: >-
  Prevents holdout leakage, same-family LLM-judge self-preference bias, unadjusted noisy-judge prevalence, and uncalibrated accuracy overclaims.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-evalops-validity"
---

# LLM, RAG & Agent EvalOps Statistical Calibration (`llm-rag-evalops-calibration`)

## When To Use
- PRs modifying LLM/RAG evaluation scripts, prompt-tuning loops, LLM-as-a-Judge rubrics, or benchmark accuracy reports.
- Validating Layer 2 holdout calibration (Rogan-Gladen / Lang-Reiczigel / Wilson 95% CI).

## Do Not Use When
- Deterministic unit test AST issues unrelated to AI evaluation (route to assertion-mutation-strength).

## Required Inputs
- Tier A verify_cpu_scanner.sarif (VER-EVAL-UNCAL-001).
- Eval scripts, judge prompt templates, and holdout calibration manifests.

## Execution & Audit Workflow
1. Run tools/verify_cpu_scanner.py to flag uncalibrated production accuracy claims (VER-EVAL-UNCAL-001).
2. Invoke auditor-evalops-validity (evalops-01, evalops-02, evalops-03, evalops-06, evalops-07) to audit holdout separation, cross-family position-swapped judges, and Rogan-Gladen prevalence adjustment.
3. Require explicit Layer 1 synthetic vs. Layer 2 calibrated holdout labeling.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
