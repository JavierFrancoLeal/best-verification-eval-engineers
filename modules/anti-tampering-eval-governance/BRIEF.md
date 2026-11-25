# Anti-Tampering, Separation of Powers & CI Gate Governance — Operational Brief (`anti-tampering-eval-governance`)

**Scope:** Blocks CI continue-on-error bypasses, untracked test skips, zeroed coverage/mutation thresholds, write-enabled auditors, and self-approval tampering.

## Deterministic Rules (`TOOL_VERIFIED`)
- `VER-GOV-SKIP-001` (`MAJOR`, `verify_cpu_scanner`): Skipped tests (@pytest.mark.skip, it.skip, t.Skip) require both an issue ticket (#123/KEY-1) and YYYY-MM-DD expiry; CI continue-on-error: true requires a downstream steps.<id>.outcome gate.
- `VER-GOV-TAMPER-001` (`BLOCKER`, `verify_cpu_scanner`): Forbid --passWithNoTests, --no-cov, || true exit masking, fail_under=0, zeroed coverage/Stryker thresholds, >3 suppression pragmas, sys.exit(0) in tests, and write/edit tools in Clean-Room AUDITOR.md.

## Semantic Invariants (`STATIC_LLM_INFERRED`)
- `verification-eval:auditor-test-integrity:testint-07` (`BLOCKER`, `auditor-test-integrity`): Builder agents must not modify test oracles, fixtures, validators, or CI gates in the same diff to manufacture a passing verdict without independent review.
- `verification-eval:auditor-evalops-validity:evalops-04` (`BLOCKER`, `auditor-evalops-validity`): Builder or prompt-tuning agents must not edit holdout manifests, grader rubrics, or evaluation thresholds to inflate benchmark scores.

## Escalation & Gate
- Missing required runner evidence (`tests_executed == 0`) -> `exit 3` (`UNVERIFIED_MISSING_TOOL`, `ITERATE`).
- Any `BLOCKER` -> `REJECT`; any `MAJOR` -> `ITERATE`; zero `BLOCKER`/`MAJOR` -> `SHIP`.
- Load `VERIFY.md` for full Draft 2020-12 schema and primary sources.
