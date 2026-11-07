# Candidate registry v2 (append-only)

Required by `docs/research_success_criteria_v2.md` §6. One row per tested candidate; status uses the v2 outcome classes A–E.
Rows 1–14 re-classify existing evidence under v2, citing the original documents (numbers spot-checked where marked ✓;
otherwise as reported by the 2026-11-07 evidence surveys, not re-run). Earlier verdicts are not edited.

| # | candidate | option | strongest evidence (source) | evidence class | v2 class | next smallest step |
|---|---|---|---|---|---|---|
| 1 | **P2 — certified deployment under serial dependence (twin known-null inversion)** | B + C | certified ports exceed the marginal false-promotion bound on persistent twin streams (SMCS 0.428 [0.339,0.511], Xu 0.375, Choe–Ramdas 0.336 on appliances ✓); uncertified selectors promote on 0.720–0.908 (Model Picker) and 0.820–0.925 (CAMS) of nulls with harm up to +25.7 ✓; A5b controls in-class synthetic Markov nulls but fails K2 on bike_hour 0.058 [0.017,0.100] ✓ (`docs/sota_sprint/validation/twin_null_results.md`) | registered protocol, 5 UCI datasets × 20 splits; real streams previously used elsewhere — check | **B** | independent adversarial review (running); author-code comparators where feasible; untouched-data confirmation |
| 2 | P1 — RMM restart-mixture label-clock e-detector on certificate hosts | A | Amendment 5 family vs host −14.5 to −47.2, late vs Xu −14.6 to −30.3, Holm p < 1e-6 (`docs/sota_sprint/REPORT.md` §2) | registered synthetic; host restriction chosen after a 5-host test failed; real late-improvement test NOT_SUPPORTED | **B/C** | real late-improvement streams |
| 3 | E_srr / uncertified selectors cheapest but null-unsafe (cost-vs-safety inversion) | B | E_srr #1 on J (411.13) but promotes 100/100 on iid nulls; `wp1/late_metric_leaderboard.md` (branch `codex/sprint2-leaderboards`) | exposed real, low cluster count | **C** (fold into #1) | — |
| 4 | Fixed-sample binomial P6 vs anytime-valid P3b ("price of sequential validity") | B | P6 cheaper on 5/7 real streams (`docs/promising_directions/B3_PLUS_RESULTS.md` §6) | post-hoc, exposed | **C** (fold into #1) | frozen re-run on fresh streams |
| 5 | P7s settled-decision acquisition | A | label savings with identical decisions on 4 streams | frozen after inspecting streams; DISCERN prior art | **C/D** | — |
| 6 | Failure atlas mechanisms M1 (certification latency) / M2 (selector churn) | C | `docs/failure_atlas_v2_flq/results/REPORT.md` | fresh synthetic | **D** (fold into #1) | — |
| 7 | A5b Markov certificate | A (+ negative) | in-class synthetic control, loses power on real | fresh synthetic, reused real | **D** | — |
| 8 | PFA-SR misses a strong challenger on HuffPost (single-source real negative) | C | +289.91 [+193.64,+391.18] per 1000 events vs RMM (branch `codex/scoped-method-research-results-2026-11-06`) | frozen single-opening real, simulated label clock | **C** | persist per-event traces |
| 9 | Persistence information bound (ρ = 1 cap on α-safe gain) | D | `docs/sota_sprint/unknown_persistence_information_bound.md` (branch `research/continuation-2026-11-04`) | internal proof, unreviewed | **C/D** (candidate theory section of #1) | independent proof check |
| 10 | Calendar optimality under tight risk (Lane A) | D | 0 gap in 108 + 54 cells | lemmas elementary, unreviewed | **E** | literature audit |
| 11 | H2c Brier-guided betting | A | frozen G5 +0.086 / +0.094 (`docs/h2c_next/FROZEN_CONFIRMATION_RESULTS.md`); composition; gas reversal (novelty_validation 07 §3) | CONFIRMED synthetic, EXPLORATORY real | **D** (guide-alignment counterexample) | — |
| 12 | Joint acquisition+switching exact DP | D | ≤ 1.1 % gap, DP-implied (novelty_validation 07 §2) | exact toy | **D** | — |
| 13 | Decision-value track (monitoring → decision value) | C | confirmation CF-S1 failed, CF-S2 passed (branch `research/monitoring-to-decision-value-2026-10-30`) | frozen one-shot | **C** | — |
| 14 | RPOQ / Candidate J controllers | A | stopped; Hsu–Shekhar prior art | — | abandoned (non-novel) | — |
| 15 | **X3 MAG (margin-aligned guidance)** — new 2026-11-07 | A | synthetic MAG − H2c −0.003 to −0.0095; gas in-sample removes H2c delay (`discovery_v2_2026-11-07/X3_MAG_RESULTS.md`) | EXPLORATORY | **E** | frozen TLC run |
