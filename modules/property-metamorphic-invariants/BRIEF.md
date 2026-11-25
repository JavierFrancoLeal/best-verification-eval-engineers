# Property-Based & Metamorphic Invariants — Operational Brief (`property-metamorphic-invariants`)

**Scope:** Verifies algebraic round-trip/idempotence properties (Hypothesis/fast-check) and metamorphic relations for non-oracle systems.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-PBT-SEED-001` (`MAJOR`, `hypothesis`): Property-based tests running in CI must execute non-zero examples with reproducible seed configuration.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-evalops-validity:evalops-05` (`MAJOR`, `auditor-evalops-validity`): Non-oracle ML, RAG, and numerical pipelines must test paired metamorphic relations (e.g., irrelevant-context invariance, monotonicity) rather than brittle exact-string snapshots.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
