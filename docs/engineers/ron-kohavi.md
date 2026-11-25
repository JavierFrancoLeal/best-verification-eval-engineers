# Ron Kohavi — Blind Canon Dossier (`ron-kohavi`)

- **Canon Tier:** `LINDY_CANON`
- **Orthogonal Axis:** Axis E — Statistical Evaluation, Holdout Rigor & Noisy-Instrument Calibration
- **Mapped Clean-Room Rules:** `evalops-03 (INV-KOHAVI-02)`, `evalops-06 (INV-KOHAVI-01)`

## Core Falsifiable Verification Principle
Point estimates on small samples hide massive uncertainty (e.g., 90% on n=20 spans down to 69.9% under Wilson 95% CI). Noisy evaluators (Se < 1, Sp < 1) bias raw prevalence estimates unless adjusted via Rogan-Gladen / Lang-Reiczigel intervals.

## Primary Sources
- Kohavi, R. (1995). A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection. IJCAI 1995, https://www.ijcai.org/Proceedings/95-2/Papers/016.pdf.
- Kohavi, R., Tang, D., & Xu, Y. (2020). Trustworthy Online Controlled Experiments. Cambridge University Press. ISBN 978-1-108-72426-5.
- Rogan, W. J. & Gladen, B. (1978). Estimating Prevalence from the Results of a Screening Test. Am J Epidemiol, doi:10.1093/oxfordjournals.aje.a112510.

## Usage Note
This dossier is stored offline under `docs/engineers/` for provenance and citation traceability only. Never roleplay this author as a persona; enforce the deterministic rules and Clean-Room `rules.yaml` predicates directly.
