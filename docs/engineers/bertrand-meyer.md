# Bertrand Meyer — Blind Canon Dossier (`bertrand-meyer`)

- **Canon Tier:** `LINDY_CANON`
- **Orthogonal Axis:** Axis C — Design by Contract (Preconditions, Postconditions, Invariants)
- **Mapped Clean-Room Rules:** `testint-04 (INV-MEYER-01)`

## Core Falsifiable Verification Principle
Every routine binds explicit caller preconditions, callee postconditions, and class/module invariants across both normal and exceptional exits. Silently weakening a postcondition assertion in a PR diff to make a test pass violates contract integrity.

## Primary Sources
- Meyer, B. (1997). Object-Oriented Software Construction (2nd ed.). Prentice Hall. ISBN 978-0-13-629155-8.

## Usage Note
This dossier is stored offline under `docs/engineers/` for provenance and citation traceability only. Never roleplay this author as a persona; enforce the deterministic rules and Clean-Room `rules.yaml` predicates directly.
