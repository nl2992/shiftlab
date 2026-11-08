# 03 — Experiment protocol: SOTA comparator expansion

Written 2026-11-08 and committed **before** any comparator other than arm B, tuned Gong–Zhang-style,
Qiu-style, arm A, Wald λ=.9, econF and never-switch was run on the nine datasets. Those seven
already have records from the C4 opening (`outputs/qsg_methods_search/c4_confirm/`).

## 1. Status of the evidence (what kind of comparison this is)

- **EQSDp arm B is frozen**: `EQSDp_l0.9_g0.2`, frozen since `10ba0237`, and not changed here.
- **The nine datasets are the original C4 batch 1** (`c4_registration.json`, seed base
  2026111201, 10 policy seeds per episode). Batch 2 (7 datasets) is not mixed in. It is reported
  only in its own section of `c4_results.md`.
- The nine were opened once, on 2026-11-08, for the arm B vs tuned Gong–Zhang-style claim, and their
  results then informed later decisions (the batch-2 source pool). **Every new comparison on them
  is therefore labelled *retrospective*.**
  - It is out-of-sample in the narrow sense that neither EQSDp's parameters nor any comparator's
    tuning uses these nine streams.
  - It is not a pre-registered confirmation.
  - Independent confirmation needs fresh data (see 09).
- The synthetic panel uses fresh seeds (base 2026111501, never used before) on the C3 14-regime
  family. It is post-confirmation and exploratory: the C3 and P1 seeds are spent, and the family
  itself was used for development.

## 2. Contract (shared by every policy)

The contract is enforced by `simulator.run_episode`, the same for every policy:

- T = 2000 events, two models, model 0 deployed initially;
- hard budget B = 200 labels, c_q = 0.05 per label, c_s = 5 per switch;
- dataset-specific constant label delay d, a public contract parameter (passed to every
  constructor);
- labels reach a policy only through released feedback after d rounds.

The primary metric is J = Σ loss + c_q N_q + c_s N_s, per episode, averaged over the 10 policy
seeds. `run_metrics` asserts the budget.

## 3. Comparator panel

Registry: `scripts/qsg_methods_search/sota_extra.py`.

**Fixed comparators**, run at their registered defaults:
- S1/S2 untuned: `gong_zhang_paid_obs`, `qiu_delayed_movement`.
- S4: `model_picker_adapter`.
- S5: `model_selector_causal`.
- S6: `cams_adapter`.
- S7: `discern_style`, `discern_style+QCE+front`, `discern_design_floor`,
  `discern_design_floor+front`.
- S8: `SMCS+retain-incumbent`, `SMCS+QCE+front`.
- S9: `xu_acquisition_only`, `xu+front_only`.
- S10: `gated_deployment` (Karampatziakis-style certificate), `gated_adaptive_range`,
  `gated_adaptive_range+front` (MOPE adaptive range).
- Restartable sequential monitoring: `two_sided_esr_label_clock`, `esr_rmmbets_fullalpha`
  (Shin–Ramdas–Rinaldo e-SR), `shekhar_ramdas_rcs_t3_anyexcl`.
- Others: `han_arw_label_clock`, `online_llm_picker`, `variance_min_ipw`, `QSG` (internal
  certified), `economic_replacement`, `CONTROL_never_switch`.

The certified methods use α = 0.05. α is fixed by their guarantee and is not tuned.

**Tunable families** (one configuration chosen per family):

| family | grid | synthetic-dev selection (pre-existing) |
|---|---|---|
| S1 `gongT` (Gong–Zhang-style, tuned) | W ∈ {100,200,400,800} × m ∈ {0,5,10,20} | `gongT_w100_m10` (D3) |
| S3 `upf` (Regol-UPF-style T3) | δ ∈ {.5,.8,.95} × m ∈ {50,100,200} | `upf_d0.95_m50` (P1) |
| S11 `wald` (Wald LCB hurdle) | λ ∈ {.9,.95,.97} × γ ∈ {.05,.1,.2,.3} | `wald_l0.9_g0.2` (P1) |
| `hoef` (Hoeffding LCB) | λ ∈ {.9,.95,.97} × γ ∈ {.1,.2,.3,.45} | `hoef_l0.9_g0.45` (P1) |
| S12 `smarg` (horizon-scaled margin) | λ ∈ {.9,.95,.97} × κ ∈ {.05,.1,.2,.3} | `smarg_l0.9_k0.2` (P1) |
| S12 `dwell` (k-streak) | λ ∈ {.9,.95,.97} × k ∈ {3,5,10,20} | `dwell_l0.9_s5` (P1) |
| S12 `econF` (front-loaded economic) | min_obs ∈ {5,10,15,25,40} × margin ∈ {0,5,10,20} | `econF_mo5_m5` (D1) |

| Challenger-style `chalgse` (added after the prior-art audit, before the nine-dataset run) | λ ∈ {1, .97, .9} × γ ∈ {.1,.2,.3,.45}, irreversible Hoeffding payback | none; nominal default `chalgse_l1.0_g0.2` (undiscounted, as in the source) |

`chalgse` follows the GSE rule of Digalakis Jr et al. (arXiv 2512.18390), the closest published
payback-with-confidence-bound rule: `ChallengerGSE` in `hurdles.py`, a common-contract
adaptation. Its development records are in `dev_chalgse/` (same streams and seeds). Selection reads
both development record files.

The λ = .97 rows are new grid points. They give the Wald/Hoeffding/margin/dwell families the
longer memory that real streams are known to prefer (M5). This strengthens the baselines and
makes the comparison harder for arm B.

**Mechanism ablation** (descriptive; added before the nine-dataset run): `EQSDp_l0.9_g0.5`. This
is arm B with the switching hurdle at the posterior median (a point estimate). Evidence, discounting,
pacing and payback are identical, so it isolates the confidence-bound component on real data.

## 4. Development-only tuning (real streams)

- **Development set**: the 14 exposed C4-0 pilot streams (Atlas v2: rialto, spam, weather,
  openml_ldpa, uci_occupancy, airlines, bank, elec2, criteo; Sprint: metro, beijing_pm25,
  bike_hour, appliances, household_power). All 230 episodes, 5 policy seeds, seed base 2026111401.
  None of these sources overlaps the nine (different organisations and tasks; the nine were built
  later by `c4_build.py`).
- **Selection rule**: for each family, choose the configuration with the lowest
  **equal-stream-weight mean J** over the 14 streams (the mean of per-stream mean J).
- **Evaluation**: both the real-dev-selected configuration ("RD") and the pre-existing
  synthetic-dev-selected configuration ("SD") go to the nine. If they coincide, it is one entry.
- **Arm B is not retuned.** Tuning the baselines on real development streams while arm B keeps
  its synthetic-chosen parameters favours the baselines. That is intended.

## 5. Analysis (`scripts/qsg_methods_search/analyze_sota.py`)

Per dataset k and comparator c, the episode-level Δ_e = (seed-mean J of arm B) − (seed-mean J of c).

- **Per dataset**: mean Δ, the percentage of c's mean J, and a two-sided 95% episode-bootstrap CI
  (2,000 resamples, rng seed 0). A dataset "favours arm B" if its upper CI limit is < 0.
- **Pooled (primary for the verdict)**: the equal-dataset-weight mean of the nine per-dataset
  mean Δ.
  - CI: stratified episode bootstrap (resample episodes within each dataset), 2,000 resamples.
  - p-value: two-sided bootstrap p (2 × the smaller tail fraction, floored at 1/2000).
  - Holm-adjust over all comparators in the nine-dataset panel.
  - Also the sign count over datasets and the exact two-sided sign-test p.
- **Dataset-level robustness**: a one-sample t-test across the nine dataset means (between-dataset
  variation). It is reported alongside, not used for the verdict.
- **Secondary (descriptive)**:
  - labels used, switches, switching cost (5 × switches), prediction loss;
  - promotion rate on episodes whose evaluator-side mean gain is < 0 (challenger worse in
    hindsight: "false promotion");
  - mean first-deploy round on episodes with gain > 0 (decision delay);
  - Δ split by evaluator-side episode type (gain > 0 / ≤ 0).
  - Evaluator-side quantities are used only for this split, never by any policy.

## 6. Verdict rule (per comparator, on the nine)

- **WIN**: Holm-adjusted pooled p < 0.05 with Δ < 0, **and** at least 6 of 9 dataset means are
  negative.
- **LOSS**: Holm-adjusted pooled p < 0.05 with Δ > 0, and at least 6 of 9 positive.
- **COMPETITIVE**: neither of the above.
- **NOT COMPARABLE** overrides the cost verdict where the comparator is a certified method
  (false-promotion control at α) or its native objective is not net deployment cost. The cost
  difference is still reported as "cost Δ under a different guarantee class". An uncertified
  arm B is never said to dominate a certified method.
- **NOT VERIFIED**: no runnable implementation, or results not reproducible.
- **Size grade** (fair-evaluation standard), attached to every WIN or LOSS:
  - negligible: < 1% of the comparator's cost;
  - small: 1–3%;
  - meaningful: 3–10%;
  - substantial: ≥ 10%.

A WIN is reported against the **adapter**. It is never reported against the native published
method unless the fidelity class is A (`02_BASELINE_FIDELITY.md`).

## 7. Reproducibility check

Arm B, `gongT_w100_m10` and `qiu_delayed_movement` in the new nine-dataset run must reproduce the
C4 records (`c4_confirm/records.jsonl`) exactly: the same seed base, the same rng derivation and the
same code. Any mismatch is reported and blocks the nine-dataset section until explained.

## 8. Synthetic panel (exploratory)

- Seed base 2026111501, 50 seeds, the 14 C3 regimes, `run_atlas_v2.py --extra sota_extra`.
- Policies: arm B, arm A, every fixed comparator, and the SD configurations. RD configurations are
  added in a second pass once known, with the same seeds.
- Metrics: family-mean J (equal regime weight); paired t over seeds with Holm; expected-oracle
  regret; null/worse promotion; switches on null.

## 9. Commands

```bash
cd scripts/qsg_methods_search
OPENBLAS_NUM_THREADS=1 ../../.venv/Scripts/python.exe sota_nine.py dev --out ../../outputs/qsg_methods_search/sota_expansion/dev --workers 14
../../.venv/Scripts/python.exe analyze_sota.py select ../../outputs/qsg_methods_search/sota_expansion/dev/records.jsonl > ../../outputs/qsg_methods_search/sota_expansion/nine_policies.txt
OPENBLAS_NUM_THREADS=1 ../../.venv/Scripts/python.exe sota_nine.py nine --policies ../../outputs/qsg_methods_search/sota_expansion/nine_policies.txt --out ../../outputs/qsg_methods_search/sota_expansion/nine --workers 20
../../.venv/Scripts/python.exe analyze_sota.py nine ../../outputs/qsg_methods_search/sota_expansion/nine/records.jsonl
```
