# Assertion & Mutation Fault-Detection Strength — Operational Brief (`assertion-mutation-strength`)

**Scope:** Eliminates assertion-free tests, tautological constant assertions, exception-swallowing handlers, and low mutation kill rates.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-TAU-NOASSERT-001` (`BLOCKER`, `verify_cpu_scanner`): Every test function/block must contain at least one executable assertion, expected-exception context, or assertion-bearing helper call.
- `VER-TAU-CONST-001` (`BLOCKER`, `verify_cpu_scanner`): Forbid constant-true assertions (assert True, expect(true).toBe(true)), reflexive x == x checks, and len(x) >= 0 tautologies.
- `VER-TAU-SWALLOW-001` (`BLOCKER`, `verify_cpu_scanner`): Forbid broad except Exception: pass, bare except: ..., and empty catch {} blocks inside test functions.
- `VER-MUT-SCORE-001` (`MAJOR`, `mutmut`): Diff-scoped mutation kill score >= 65% with zero Pending mutants in Stryker/mutmut/Gremlins reports.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-test-integrity:testint-01` (`BLOCKER`, `auditor-test-integrity`): Test oracles must derive expected outcomes from independent specifications rather than duplicating the SUT's implementation formula.
- `verification-eval:auditor-test-integrity:testint-06` (`MAJOR`, `auditor-test-integrity`): Assertions on critical state transitions must verify output state and side effects strongly enough to kill boundary/relational mutants.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
