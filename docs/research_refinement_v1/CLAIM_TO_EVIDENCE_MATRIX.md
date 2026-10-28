# Claim-to-evidence matrix

**Recorded 2026-10-28, loop tick 11 (Phase F2).** This matrix extends, and does not replace,
`papers/shiftguard_unified/claim_evidence_map_v1.md` (C1–C12). Every manuscript-level claim in
`FINAL_RESEARCH_PROPOSAL.md` is mapped to its evidence, its status, and what would change it.

**Status values:**
- **E-dev**: established on frozen development evidence;
- **E-conf**: established on frozen confirmatory evidence;
- **E-pub**: published result, credited;
- **Lemma**: exact identity, proof to be written;
- **Hyp**: registered hypothesis, untested;
- **Desc**: descriptive or post hoc;
- **Withdrawn**.

## Claims kept

| ID | Claim (exact strength) | Evidence (artifact) | Status | Lead / Codex verification | What would change it |
|---|---|---|---|---|---|
| K1 | Distributional change, predictive degradation and paired decision harm are distinct estimands; a shift alarm alone is not decision harm | Claim map C1; synthetic profiles; S3/WP4 panels kept separate | E-dev | Codex R1 and R2: no objection | A generator where they provably coincide would not refute it. The claim is a distinction, not a universal theorem. |
| K2 | Gated HT against correctly bounded uniform PPI: registered post-onset best-fixed-stake growth ratio 7.20 [6.88, 7.55] at `r = 0.20`; exact McNemar 100/0 (`p = 7.9e-31`) at `r = 0.05`; comparable spend (118.1/114.1 labels; 177.3/170.9 dollars) | `outputs/gated_monitor_compare/analysis/decision.json`, `summary.csv`; `docs/gated_monitor_comparison_results.md` | E-dev (S3 is development) | Codex R1 and R2 artifact checks match | T0.2 mismatch; H-B1 failure on fresh seeds |
| K3 | The gating economics are DISCERN's (Θ(1/ρ), Thm 9 and Cor. 10; §6.4 head-to-head, Table 3: 2,098 / 2,845 / 1,948.5 / 70 median labels). ShiftLab replicates them under decision costs, finite reserves and non-stationary incumbents. | arXiv 2609.17560 (primary PDF, Codex R2) | E-pub (credited) plus replication pending H-B1 | Codex R2 checked the PDF | — |
| K4 | G1's analytic growth prediction is within a factor of two at all four budgets (18 / 18 / 15 / 7.5 against 17.47 / 20.61 / 14.73 / 7.20) | Same as K2 | E-dev, pre-registered | Codex R1 and R2 | T0.2 mismatch |
| K5 | Development observation: fixed gating ≥ paced in S3 `harmful_adaptation` (0.86/0.76 default mixture, 0.94/0.91 GRAPA, `r = 0.10`) and on EIA injected harm (fixed matches the full-feedback median delay in 10/10 detectable cells at each `r ∈ {0.05, 0.10, 0.20}`) | S3 summary; `outputs/eia_real_data_validity/injected.csv` | E-dev, Desc (no paired uncertainty) | Codex R2 re-checked `injected.csv` | H-B2 (burst classes) supersedes it; it holds only for burst class (i) |
| K6 | In the frozen integrated state machines, `q1_fallback` beats `full_pipeline` by 5.63× (boundary harm) and 4.26× (monitor-aligned adaptation). Recurring regimes: +447.96 against 0. Reversal: −1,148.46 against −143.76 (8.0× worse). **The arms differ in response latency, coverage and rollback.** | `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv`; stage constants at `src/shiftlab/dive/integrated_pipeline.py:39–40` | Desc, post hoc (outside the frozen 22-test family) | Lead and Codex verified the numbers and confounds | H-B3 / E3 decides what governs the ranking |
| K7 | Lemma L: for zero-anchor HT with fixed-fraction stakes at ε = 0, wealth after given ordered labelled losses is propensity-free, including the fixed-weight mixture. It fails for PPI and does not cover adaptive engines. A pathwise identity, not a validity theorem. | `REFINEMENT_ROUND_2.md` §3; engine `src/shiftlab/dive/eprocess.py:154` | Lemma | Codex R2: "correct"; PPI counterexample checked numerically | T0.3 test failure (an implementation finding) |
| K8 | Null calibration: S2 has a per-arm simultaneous Bonferroni exact upper bound ≤ 5% (2,000 streams per cell; seeds 58500000–58501999). WP4 has 68/68 per-path orientation cells at 0/1,000 (a conservative all-cell bound of about 0.72%). | `outputs/gated_monitor_null/`; `outputs/eia_real_data_validity/null_cells.csv` | E-dev (Monte Carlo calibration, not proof) | Lead verified the S2 seeds from parquet; Codex verified the WP4 bound | T0.2 failure; new arms need their own calibration |
| K9 | Negative screens: the stratified candidate equals the subgroup composition (4.4e-16; ratio ≤ 1.000 against 1.5); the data-efficient controller had 55% against 100% detection **against an onset-informed late-prior baseline**; the ADG anchor ≤ 1.23× against 1.5×; the integrated controller is inert | WP2, WP3 and ADG results docs; claim map C6 and C12 | E-dev (prescreens) | Inventory A2; lead corrected the WP3 baseline description | — (kept as negative results) |
| K10 | Held-out EIA authorities (eligible after the frozen gate): orientation nulls hold, and fixed gating replicates full-feedback delay | — | Hyp (H-B4) | — | P3 freeze, then R4 |
| K11 | Burst-class pacing pattern: fixed non-inferior in (i) and (iii), paced better in (ii) | — | Hyp (H-B2) | — | R2 |
| K12 | Revert-versus-promote crossover depends on post-alarm reference deterioration | — | Hyp (H-B3) | — | R3 |
| K13 | The contract hosts an externally implemented method without evaluator access | — | Hyp (benchmark-value gate) | — | R5 |

## Claims withdrawn or rejected (keep visible)

| ID | Claim | Why withdrawn | Where |
|---|---|---|---|
| W1 | "Claim A: rankings are governed by two quantities; novel mechanisms add nothing" | Overgeneral (Codex R1 F5) | `ADVERSARIAL_REVIEW_1.md` |
| W2 | Proposition S's corollary: evidence and delay are set by the number of post-onset informative labels | Algebra does not support it (Codex R1 F2; ±C counterexample) | same |
| W3 | Strong-signal regime makes low `q` costly (tick-5 derivation) | Wrong; per-label growth is q-invariant in both regimes (tick-6 numerical check) | `COMPETING_RESEARCH_DIRECTIONS.md` §0 |
| W4 | H4 shows that reference safety governs intervention rankings | Confounded by stage timing and rollback asymmetry (Codex R1 F4) | `ADVERSARIAL_REVIEW_1.md` |
| W5 | DISCERN is theory-only and its gating has not been benchmarked | False; §6.4 benchmarks it (Codex R1 F3, R2) | same |
| W6 | "4–6× on three profiles" | Arithmetic error; it is 5.63× and 4.26× on two | `ADVERSARIAL_REVIEW_2.md` |
| W7 | "Fixed-rate gating detects no later than paced" (unrestricted) | Overclaim; reserve exhaustion under harmless pre-onset bursts (Codex R2) | same |
| W8 | The current-context null `E[· \| F_{t−1}, X_t]` | Not the charter null; the controls violate it (Codex R1 F1) | same |
| W9 | Novel unified algorithm; costed promotion method; bandit-feedback harm monitor; intervention-validity theory | Fail the combination test or have no evidence | Prior-art matrix §1, B2 |
| W10 | Held-out authorities form a second task | Same task, new paths (Codex R2) | `ADVERSARIAL_REVIEW_2.md` |

## Cross-claim restrictions (in addition to claim map v1)

- Never call S3 or WP4 confirmatory. Confirmation comes only from registered fresh-seed E2–E4.
- Never pool authorities as independent deployments, or query replicates as independent paths.
- Report absolute reference risk alongside relative harm.
- The PPE gated alias is an algebraic alias, not an independent method win.
- "Coupled replay", not "identical feedback", whenever acquisition rules differ.
