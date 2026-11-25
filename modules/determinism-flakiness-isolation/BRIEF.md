# Determinism, Hermeticity & Flakiness Isolation — Operational Brief (`determinism-flakiness-isolation`)

**Scope:** Prevents wall-clock sleeps, unseeded randomness, shared global state, and non-deterministic async races in tests.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-FLK-NONDET-001` (`MAJOR`, `verify_cpu_scanner`): Forbid non-zero time.sleep/asyncio.sleep/time.Sleep, setTimeout without fake timers, and unseeded random.*/Math.random() in tests.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-test-integrity:testint-05` (`MAJOR`, `auditor-test-integrity`): Concurrency, retry, and distributed state tests must control virtual time, fault injection, and execution ordering deterministically.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
