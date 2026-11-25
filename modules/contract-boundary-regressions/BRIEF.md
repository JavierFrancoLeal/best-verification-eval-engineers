# Contract, Design-by-Contract & Negative Boundary Regressions — Operational Brief (`contract-boundary-regressions`)

**Scope:** Enforces Design-by-Contract preconditions/postconditions, API/schema contract tests, and mandatory negative auth/boundary regression tests.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-CON-REGRESS-001` (`BLOCKER`, `pytest`): All contract and boundary regression test suites must execute with zero failures and zero errors.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-test-integrity:testint-03` (`BLOCKER`, `auditor-test-integrity`): Changes to authentication, tenant isolation, input validation, or state-machine transitions must include negative/adversarial regression tests exercising rejection paths (401/403/400).
- `verification-eval:auditor-test-integrity:testint-04` (`BLOCKER`, `auditor-test-integrity`): PR diffs must not silently weaken existing Design-by-Contract assertions, postconditions, or expected-error invariants to make failing tests pass.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
