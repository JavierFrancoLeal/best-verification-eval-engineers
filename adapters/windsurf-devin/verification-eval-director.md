# Verification & EvalOps Director (`verification-eval`, v1.2.0)

Apply this rule on PRs touching tests, CI workflows, coverage/mutation configs, or LLM/RAG eval harnesses.

1. Run `.windsurf/skills/verification-director/tools/verify_cpu_scanner.py --target . --sarif-out verify_cpu_scanner.sarif`.
2. Ingest JUnit XML, coverage, and mutation evidence via `.windsurf/skills/verification-director/tools/eval_ingest.py` (`exit 3` fail-closed on missing/zero-test evidence).
3. Escalate semantic test theater or eval validity defects to strictly read-only Clean-Room auditors (`auditor-test-integrity`, `auditor-evalops-validity`).
4. Never weaken tests, thresholds, or `rules.yaml` to manufacture `SHIP`. Emit `Verdict Envelope v1.2.0`.
