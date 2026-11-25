# Test Execution & Coverage Oracles — Operational Brief (`test-execution-oracles`)

**Scope:** Enforces fail-closed test runner execution (tests_executed > 0), JUnit XML leaf recomputation, and line/branch coverage floors.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-EXE-NONZERO-001` (`BLOCKER`, `eval_ingest`): JUnit XML must parse cleanly without DOCTYPE/ENTITY and report tests_executed > 0 with failed == 0 and errors == 0.
- `VER-EXE-COVFLOOR-001` (`MAJOR`, `coverage_py`): Line coverage >= 80%, branch coverage >= 75%, and excluded_ratio <= 5%.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-test-integrity:testint-02` (`MAJOR`, `auditor-test-integrity`): Unit tests must exercise the real system under test rather than mocking the SUT method itself and asserting mocked outputs.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
