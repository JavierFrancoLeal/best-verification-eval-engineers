# Wei-Lin Chiang — Blind Canon Dossier (`wei-lin-chiang`)

- **Canon Tier:** `PROVISIONAL_FRONTIER`
- **Orthogonal Axis:** Axis G — LLM-as-a-Judge Bias, Position Swapping & Benchmark Contamination
- **Mapped Clean-Room Rules:** `evalops-01 (INV-CHIANG-02)`, `evalops-02 (INV-CHIANG-01)`, `evalops-07 (INV-CHIANG-03)`

## Core Falsifiable Verification Principle
Automated LLM judges suffer from position bias, verbosity bias, and self-preference when evaluating their own model family. Valid EvalOps requires disjoint holdouts, cross-family judges with swapped slots, and domain-stratified human calibration.

## Primary Sources
- Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023, https://arxiv.org/abs/2306.05685.
- Yang, S., Chiang, W.-L., et al. (2023). Rethinking Benchmark and Contamination for Language Models like Rewritten Samples. https://arxiv.org/abs/2311.01964.
- Li, T., Chiang, W.-L., et al. (2025). Arena-Hard / Crowdsourced LLM Evaluation Calibration (UNVERIFIED_SOURCE).

## Usage Note
This dossier is stored offline under `docs/engineers/` for provenance and citation traceability only. Never roleplay this author as a persona; enforce the deterministic rules and Clean-Room `rules.yaml` predicates directly.
