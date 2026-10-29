# Implementation readiness gate

**Recorded 2026-10-28, loop tick 11 (Phase F2).** This gate sets what the implementation agent
may start, what must happen first, and what stays blocked. It applies `FINAL_RESEARCH_PROPOSAL.md`.
The machine-readable version is `handoff.json`.

## Gate verdict

**READY for E1 and the contract groundwork. NOT READY for any confirmatory run (E2–E4)** until the
protocol freezes in Stage 1 are committed. No new algorithm development is authorised.

## Stage 0: may start immediately (no new seeds, no new data)

| ID | Task | Done when |
|---|---|---|
| T0.1 | **Machine-checked seed registry.** Parse every registered seed range from protocols, runners and manifests into one registry with an overlap checker, as a test that fails on any undisclosed overlap. Record the known overlaps (`54000000–54000029` ⊂ `54000000–54000499`; `20290000` blocks) as disclosed. | Registry and test committed; the check passes with the disclosures |
| T0.2 | **E1 independent verifier.** Recompute H1 (7.2014 [6.8845, 7.5512]; McNemar 100/0), H2 (17.47 / 20.61 / 14.73 / 7.20), H3 (0.86/0.76 and 0.94/0.91; EIA 10/10 median matches), H4 (+664.64 / +685.91 / +447.96 against +118.01 / +161.16 / 0; −1,148.46 against −143.76), the S2 null table and the WP4 tables from frozen artifacts with hash checks, using code independent of the original analysis scripts | All values match within recorded tolerances, or every mismatch is documented |
| T0.3 | **Lemma L check.** Deterministic test: for stored or synthetic labelled-loss sequences, the default `PredictableBoundMeanEProcess` wealth is identical across propensity sequences at ε = 0; PPI is shown to differ | Test committed |
| T0.4 | **Errata (new files, no history edits).** S2 seed block (`docs/gated_monitor_null_calibration_results.md:8` says 58300000; actual 58500000–58501999); stale "rollback not implemented" (`docs/methods_and_assumptions.md:126`); bibliography corrections (prior-art matrix §2); Claim B ratio correction | Erratum doc committed |
| T0.5 | **Target-Scout hash drift.** Run the historical `budgeted_promotion.py` (`8eada2f9…`) against the current one (`681a4e13…`) on the registered confirmation, or prove the change is logging-only | An equivalence record is committed, or non-equivalence is disclosed |
| T0.6 | **WP4 freeze LF/CRLF.** Re-hash frozen sources as stored in Git (LF) and add a portable verifier | Freeze check passes on a fresh checkout |
| T0.7 | **Arm-by-arm validity table** (theory obligation 2) for every arm, Xu and PPE included, with the reference-training channel | Doc committed and reviewed by Codex |
| T0.8 | **Lemma L write-up** with its applicability table and the local ε statement | Doc committed |

## Stage 1: protocol freezes (must be committed before any Stage 2 run)

| ID | Freeze | Required content |
|---|---|---|
| P1 | **E2 protocol** | Cells; H-B1a, H-B1b and H-B2 exact statistics; margins (−5 points for non-inferiority); McNemar power from development-set discordance (target ≥ 0.9); n per cell; seed block from the registry; Holm families; burst-class generators (i), (ii), (iii); held-out mechanism cells and the baseline predictor; stop rule on validity failure |
| P2 | **E3 protocol** | An executable timeline spec (trigger, certification start and completion, deployment, waiting); factors (response × rollback parity × coverage × onset × post-alarm reference); the "revert while certifying" arm; registered interaction contrasts; utility and resource accounting; all seeds analysed; a CPU smoke first |
| P3 | **E4 protocol** | The eligibility algorithm (exclusions; D/DF/NG/TI; coverage; ≥ 20 rehearsal procure events) frozen and hashed **before value inspection**; the development/locked split seed; four-clock contract; exclusion log; output and config exposure audit; per-path plus regional-cluster reporting; PPI included only with a validated delayed proxy |
| P4 | **Benchmark-value gate** | A spec for an external method (Comparecast or WATCH-style) implemented by a separate agent through the public interface only |

Each freeze needs: a protocol doc, a SHA-256 freeze record with a UTC time, and a Codex review of
the protocol (not of results) before execution.

## Stage 2: runs (each after its freeze)

| ID | Run | Limits |
|---|---|---|
| R2 | E2 | CPU; smoke on development seeds, then registered seeds |
| R3 | E3 | CPU smoke; **ask the user before any CUDA-scale run** |
| R4 | E4 | CPU; locked set opened once, after P3 |
| R5 | External-method gate | Through the public interface only |

## Blocked or rejected (do not implement)

| Item | Reason |
|---|---|
| RIVE, ASC, any unified monitor–certify–intervene algorithm | 2026-10-26 NO-GO stands |
| Any new Paper 1 monitoring mechanism (stratified, data-efficient, ADG, controller variants) | 2026-10-27 checkpoint B; all failed registered screens |
| Promotion method claims (path B) | Fails the combination test (OCS, HCPI, OPI, AnyRank, Digalakis, Zhang–Wu–Qian) |
| G1 bandit-feedback monitor, G3 intervention-validity theory, partial-identification monitor | Section-level at most; estimand unfixed; no evidence |
| Using CRSP, Upworthy or exposed EIA windows for new claims | Exposed test windows |
| Any new data download, including the post-freeze EIA pull | Deferred; needs explicit user confirmation of method and size |
| Rerunning frozen evaluations without a written verification reason | Standing constraint |

## Separately gated

**G4 theory pre-screen** (pencil and paper, no code). Stop if the minimax schedule is fixed or
uniform up to constants, or maps onto Geng–Bayraktar–Lai or Zhang–Cheung. Expected: stop.

## Unresolved blockers needing the user

1. Whether to approve CUDA-scale E3 after the smoke.
2. Whether, and when, to confirm the deferred post-freeze EIA pull: method (API key that you set,
   or a roughly 700 MB bulk file) and size.
3. Whether a GitLab mirror exists. Only `origin` (GitHub) is configured.
4. Pushing: 42+ local commits are unpublished, and local `main` diverges from `origin/main` by
   the PR #1 merge commit.
