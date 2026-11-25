---
name: property-metamorphic-invariants
description: >-
  Verifies algebraic round-trip/idempotence properties (Hypothesis/fast-check) and metamorphic relations for non-oracle systems.
license: MIT
compatibility: Python 3.9+ stdlib CPU tools; integrates with pytest, vitest, jest, go test.
metadata:
  schema_version: "1.2.0"
  judgment_schema: "VERIFY.md"
  suite_id: "verification-eval"
  author: "Trasunto / best-verification-eval-engineers"
  clean_room_auditor: "auditor-evalops-validity"
---

# Property-Based & Metamorphic Invariants (`property-metamorphic-invariants`)

## When To Use
- Auditing parsers, serializers, financial arithmetic, state machines, or ML/RAG pipelines lacking exact single-answer oracles.
- Verifying seeded shrinking and metamorphic invariance checks.

## Do Not Use When
- Simple CRUD schema validation without algebraic or non-oracle behavior (route to contract-boundary-regressions).

## Required Inputs
- Property-based test suites (Hypothesis, fast-check, rapid) and metamorphic test definitions.
- Tier B JUnit XML confirming property suites executed with non-zero examples.

## Execution & Audit Workflow
1. Verify deterministic seeding (@seed / derandomize=True or fast-check seed) so failing counterexamples reproduce in CI.
2. Check that serializers/parsers/state machines assert algebraic invariants (round-trip, commutativity, monotonicity, idempotence).
3. Invoke auditor-evalops-validity (evalops-05) on non-oracle ML/RAG/LLM code to ensure diverse paired metamorphic relations.

## Verdict & Severity Criteria
- **BLOCKER (`REJECT`):** Any deterministic or Clean-Room `BLOCKER` finding forces `REJECT` (non-compensable).
- **MAJOR (`ITERATE`):** Any unresolved `MAJOR` finding or `UNVERIFIED_MISSING_TOOL` condition prohibits `SHIP`.
- **MINOR (`SHIP` with advisory):** Advisory findings logged without blocking merge.

## Guardrails
- Enforce single-root-cause deduplication per `file:line`.
- Never dilute `MAJOR` findings via score averaging (`score_heuristic: null`).
- Respect Separation of Powers: builder agents must not modify verification oracles or `rules.yaml`.
