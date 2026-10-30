# 09 Frozen confirmation (2026-10-30)

## 1. Statement

**No frozen confirmation was run in this programme.** No candidate met its registered development POSITIVE rule, so no confirmation was authorised. Paths are relative to `docs/promising_directions/`.

| Candidate | Registered development decision | Source | Confirmation authorised? |
|---|---|---|---|
| A1 joint planner J vs best calendar C* (Lane A) | KILL (max relative gap 0.003645 primary, 0.008741 primary+secondary, against the 0.05 and 0.10 thresholds) | `results/a1/summary.json`; `04_EXACT_ORACLE_SEPARATION.md` | No; joint-method claim closed |
| B1 P3 certified switching (Lane B) | Q1 MIXED (max 3.5% reduction vs the 10% bar); Q2 NOT SUPPORTED | `results/b1/summary.json` `decisions` | No |
| B2 P3b propensity-capped certified switching | Q1 MIXED (10.20%, 9.65%, 7.88%, 7.67% reductions; passes all criteria only in B200_cs5) | `results/b2/summary.json` `decisions`; `results/b2/NOTES.md` | No; `RESEARCH_LEDGER.md` records "No confirmation authorised" |

Valid-but-not-positive: B1 and B2 validity checks passed (0/500 false promotions in W2 and W4, Clopper-Pearson 95% upper bound 0.005974 <= alpha 0.05; `results/b1/summary.json`, `results/b2/summary.json`). Validity of the test does not make the efficacy rule POSITIVE.

Nothing in this programme may be described as confirmatory. A1, B1 and B2 are development studies by registration (`protocols/A1-exact-separation.md`, `protocols/B1-certified-switching.md`, `protocols/B2-propensity-cap.md`). B2 is development round 2 informed by B1 diagnostics.

## 2. Inherited frozen confirmations (not produced here)

| Confirmation | Commits / data | Verified status | What was verified | Limits |
|---|---|---|---|---|
| H2c G5 | Code `60930a4`; preregistration `e164d63`; results `44119c6`; per-seed parquet sha256 `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7`; cells CSV sha256 `81c8e39d6afc29ce88a62a28d42395d11cc3661af2ff538e0978c0e04c1877b6` | Analysis level VERIFIED (rerun of `scripts/sota_search/g5_confirmation_analysis.py` on the stored parquet reproduces reported numbers). Simulation level PARTIAL: one cell (subgroup_failure/concept2, N=600, different seeds) re-run, H2c 0.330 / 0.617 vs frozen 0.342 / 0.627, MC-consistent; full simulation not re-run; no manifest in repo (NOT FOUND) (`06_H2C_AND_HG_REPRODUCTION.md` section 2) | Advantage vs better comparator +0.086 [0.059, 0.113] at 10%, +0.094 [0.063, 0.125] at 20%; power 0.382 / 0.640; benign FAR 0.067 at 20%; null FAR max <= 0.027; harm cells won 13/14 and 14/14 | Nominal cost effectively known; fixed delay 5; one generator family; no comparator is a verified published reproduction; cost-null validity DOC-ONLY with no supermartingale unit test; H2c reduces exactly to discounted Kelly with a substituted moment ratio (`01_EVIDENCE_MATRIX.md` Lane B) |
| HG e15 | Code `scripts/gap/e15_confirm.py`; data `outputs/gap_closure/e15_confirm/perseed.parquet` at `8552911`; no hash recorded in the audit | Analysis VERIFIED (recomputed 0.0288 / 0.0518; Holm p 0.004 / 0.003; family size 10); simulation DOC-ONLY, not re-run (`06_H2C_AND_HG_REPRODUCTION.md` section 3) | +0.029 [0.012, 0.046] and +0.052 [0.020, 0.090] over 21 worlds (400 seeds harm, 1000 null) | "Harm reduction ~21/24" is a MISMATCH: raw units averaged over all worlds including null; harm worlds only about 15% / 25% relative (-28.9 / -33.9 raw). HG invalid under dependent outcomes (FAR up to .23). HG not better than PH/CUSUM (-0.066 / -0.110). HG beat the parent (+0.050 / +0.131) but not ONS or plain discounting (`01_EVIDENCE_MATRIX.md` Lane C) |

Both are synthetic. The Gas replay (D2) reverses the synthetic H2c gain (see `10_REAL_DATA_RESULTS.md`).

## 3. What a confirmation of P3b would require if anyone reopens it

Prerequisites are stated here as requirements derived from the registered B2 protocol and the repository rules; this programme did not run any of them.

1. **Structurally distinct generator.** `protocols/B2-propensity-cap.md` states that a positive result would authorise only a separately registered confirmation on a structurally distinct generator family. B1 and B2 share one generator (four worlds W1-W4, tau=600, disagreement 0.25, fixed delay 5). The new generator must differ in structure, for example in the loss-difference law, disagreement process, delay law, and dependence, not only in seeds or parameters.
2. **Fresh seeds.** Seed bases 20261031 (B1) and 20261101 (B2) are consumed; also any seed used while building the new generator.
3. **Registration before running.** Hypothesis, primary metric, BEST definition, decision thresholds, information budgets, test windows and analysis code hashed and committed before the first confirmation run. Keep tuning separate from final evaluation (`AGENTS.md`).
4. **Gate not currently met.** P3b did not meet the B2 POSITIVE rule (Q1 MIXED), so a confirmation would need a documented decision to reopen, because the registered path to confirmation (a development POSITIVE) was not reached. A confirmation cannot be presented as following from B2.
5. **Strongest baselines, including the missing ones.** BEST in B1/B2 is only the best of {P0, P1, P2}. A confirmation needs at least the missing comparators of `07_MATCHED_BASELINE_COMPARISONS.md` section 3: CAMS-style disagreement acquisition with a non-certifying switching rule, an e-detector (SR/CUSUM) paired trigger, an economic retraining rule, state-independent adaptive acquisition, and standalone always-query and immediate-deploy rows. It also needs any comparators added by the adversarial review (`11_ADVERSARIAL_REVIEW.md`; not read for this file).
6. **Matched information.** Same budget B, delay, query and switch costs, and label-availability regime for every policy, with delayed and selectively sampled feedback represented explicitly. P4's known-hazard assumption must be labelled as a plug-in if reused.
7. **Validity evidence.** Exact-null unit test on a boundary null (E[D]=0) with the P3b cap (the B2 protocol requires it; it exists as `test_p3b_boundary_null_false_promotion_rate` and passed at `041bc26`, but the rate is not saved as an artifact, so a confirmation should save it), plus a dependence check: the argument in `05_PAIRED_CERTIFICATION_THEORY.md` is a fixed-delay conditional-null argument and is not independently reviewed, and related monitors fail under dependence (HG FAR up to .23).
8. **Pre-stated reporting.** Report W3-type reversal losses and W4-type benign losses per world (B2 showed +14.29% and +10.02% against BEST at B400_cs20), not only the world average; include continue / pivot / stop language with the result.
9. **Hardware and runtime.** CPU-sized runs sufficed in development (B1 22.28 s, B2 5.93 s; `results/b1/summary.json`, `results/b2/summary.json`); no large sweeps are needed.
