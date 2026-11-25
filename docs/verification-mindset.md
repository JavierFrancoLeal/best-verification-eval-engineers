# Verification & EvalOps Mindset (`docs/verification-mindset.md`)

`best-verification-eval-engineers` (`suite_id: verification-eval`, `ECOSYSTEM_CONTRACT v1.2.0`) uses **conjunctive-gate verification** — zero persona roleplay, zero `Q_total` averaging, and strict separation between **Tier A/B deterministic CPU execution** and **Clean-Room cross-model semantic auditing**.

## Epistemic Loop Across Seven Orthogonal Axes
1. **Oracle & Fault Sensitivity (Axes A–D):** Offutt's RIPR mutation coupling, Hughes's stateful property shrinking, Meyer's Design-by-Contract invariants, and Chen's Metamorphic Relations for non-oracle systems.
2. **Hermetic Replayability (Axis F):** Wilson's Deterministic Simulation Testing ensures every defect reproduces bit-for-bit from a seed without wall-clock races.
3. **Statistical & Adversarial Validity (Axes E & G):** Kohavi's finite-sample inference (extended with Rogan–Gladen / Lang–Reiczigel noisy-judge calibration), Chiang's LLM-as-a-Judge bias/contamination controls, and Baker's anti-reward-hacking Separation of Powers.

## Blind-Selected Canon (8 Authorities)

| Slug | Engineer | Tier | Axis | Primary Anchors | Mapped Semantic Rules |
|---|---|---|---|---|---|
| `jeff-offutt` | Jeff Offutt | `LINDY_CANON` | A — Mutation & RIPR Oracles | Ammann & Offutt (2017, ISBN 978-1-107-17201-2); TOSEM 1992/1996 | `testint-01`, `testint-02`, `testint-06` |
| `john-hughes` | John Hughes | `LINDY_CANON` | B — Property & Stateful Testing | Claessen & Hughes (ICFP 2000); Hughes (LNCS 9600, 2016) | `testint-03` |
| `bertrand-meyer` | Bertrand Meyer | `LINDY_CANON` | C — Design by Contract | Meyer (OOSC2, 1997, ISBN 978-0-13-629155-8) | `testint-04` |
| `tsong-yueh-chen` | Tsong Yueh Chen | `LINDY_CANON` | D — Metamorphic Testing | Chen et al. (1998); Xie & Chen (JSS 2011) | `evalops-05` |
| `ron-kohavi` | Ron Kohavi | `LINDY_CANON` | E — Statistical Eval & Calibration | Kohavi (IJCAI 1995); Kohavi, Tang & Xu (2020) | `evalops-03`, `evalops-06` |
| `will-wilson` | Will Wilson | `LINDY_CANON` | F — Deterministic Simulation | Zhou & Wilson (FoundationDB, SIGMOD 2021) | `testint-05` |
| `wei-lin-chiang` | Wei-Lin Chiang | `PROVISIONAL_FRONTIER` | G — LLM Judge & Contamination | Zheng et al. (NeurIPS 2023); Yang et al. (2023); Li et al. (`UNVERIFIED_SOURCE`) | `evalops-01`, `evalops-02`, `evalops-07` |
| `bowen-baker` | Bowen Baker | `PROVISIONAL_FRONTIER` | G — Anti-Reward-Hacking | Baker et al. (2025, `UNVERIFIED_SOURCE`) | `testint-07`, `evalops-04` |

## Mandatory Elimination Audit (9 Rejected Candidates)

| Candidate | Primary Fame Area | Failed Gate(s) | Concrete Rejection Rationale |
|---|---|---|---|
| Kent Beck | TDD (*By Example*, 2002), XP, xUnit | FalsifiableYield, Orthogonality | TDD is an authoring sequence unobservable in a static PR diff and supplies no formal oracle-adequacy predicate; subsumed by Offutt and Hughes. |
| Robert C. Martin | *Clean Code* (2008), "Three Laws of TDD" | SkinInTheGame, FalsifiableYield | Popularized stylistic guidelines rather than empirically validated verification engines or statistical evaluation systems; yields subjective aesthetics. |
| Martin Fowler | "Mocks Aren't Stubs" (2007), Test Pyramid | SkinInTheGame, FalsifiableYield | Influential taxonomy author, but the Test Pyramid is a descriptive portfolio metaphor rather than a falsifiable PR-diff invariant. |
| C. A. R. Hoare | Hoare Logic (CACM 1969), CSP | FalsifiableYield, Orthogonality | Deductive `P{Q}R` derivations require formal proof assistants rather than polyglot PR-diff predicates; Meyer operationalized executable contracts on Axis C. |
| Gleb Bahmutov | Cypress.io E2E automation | Lindy, FalsifiableYield, Orthogonality | Tied overwhelmingly to a single browser runner; fails language-agnostic Lindy verification abstraction. |
| Hamel Husain | Applied AI eval workshops & courses | Lindy, SkinInTheGame | Practitioner educator/consultant rather than originator of peer-reviewed measurement systems or calibration proofs; subsumed by Kohavi, Chiang, and Baker. |
| K. Rustan M. Leino | Dafny, Spec#, Boogie, ESC/Java | Orthogonality, FalsifiableYield | Overlaps Axis C while relying on verification-aware languages and SMT discharge rather than universal non-AST PR auditing on mainstream repos. |
| Mark Harman | Mutation survey (TSE 2011), Meta Sapienz & ACH (`UNVERIFIED_SOURCE`) | Orthogonality | World-class industrial mutation work, but overlaps Axis A with Offutt (who originates RIPR and sufficient mutant operators). |
| Darko Marinov | Flaky tests (FSE 2014), NonDex, iDFlakies | Orthogonality | Pioneered post-hoc JVM flaky-test detection, but overlaps Axis F with Wilson's language-agnostic Deterministic Simulation invariant. |

## Deep Dossiers (Loaded Offline Only)
Full primary-source dossiers live under `docs/engineers/*.md` and are intentionally excluded from default active agent context (`<= 25.6 KB` budget).
