# 01 — Repository audit and initial state (P0)

Written 2026-11-09. Branch `research/paper1-eqsdp-scale25-2026-11-09`, cut from
`research/paper1-eqsdp-foundation-2026-11-08` at 5bda4e73, which was the verified origin HEAD at the time. The
foundation branch and its frozen evidence (docs 00–20) are not modified. A machine-readable copy of
this audit is in `01_initial_state.json`.

## 1. Frozen method and evidence

| item | value | source |
|---|---|---|
| method v1 (frozen) | EQSDp λ.98 γ.3, reversible, cutoff H=1100, plus E48 (arrival_discount .5, lookahead 50, hazard .002) and F60 (bundle 2, horizon 100, hazard .002). Search60 spec `P2_K2__E48_F60` | doc 19 §1 |
| parent | `s2armr_H1100` | doc 18 |
| contract | T=2000, B=200, c_q=.05, c_s=5, delay 100, 10 policy seeds | doc 19 |
| fresh confirmation | K=7 eligible (oakland ineligible, montgomery excluded), 547 episodes. H1/H2/H3 pass: −0.391% / −0.387% / −0.389%, 7/7 negative | doc 20, `fresh_results/summary.json`, recomputed independently |
| vs strongest per-dataset reference on fresh data | mean +0.377% reduction (range −0.09% kc to +0.81% dallas). The strongest reference is W+cut on 4/7 datasets, model_picker (austin), online_llm_picker (dc) and econF_mo5_m0 (kc) on the rest | computed from `fresh_results/mean_J_by_dataset_policy.csv` |
| vs unequipped arm R | +1.0% to +2.4% (mean 1.6%). This is a weak reference; it is not usable as the 2.5% reference | same |
| matched parents | EQ+cut and W+cut are tied (23.104 vs 23.103), so no EQSDp-over-Wald claim | doc 20 |

Failed paths, all kept in the record: the Stage 2 BoTorch winner failed its odd-episode check (14); R1–R3 and R2-roll failed recovery (17); JointBayes C1's p_cross gate is change-blind (15).

## 2. Headroom ceiling (the binding constraint for the 2.5% target)

Doc 11 (Stage 0, nine datasets, even episodes) gives the regret of the strongest reference over the best *fixed* model, as % of J_ref:
- late adoption 2.35–2.65;
- false promotion plus churn 0.85–1.16;
- label fee 1.84;
- unavoidable adoption switch 0.76;
- **total 6.1**.
- The decision value of doubling free labels is only 0.23–0.32%.
- Per dataset, the total ranges from 3.4% (austin) to 11.3% (dc). It is concentrated in late adoption on sf and dc.

**Implication.**
- With the union-bound design of the brief (α_i = .05/(i(i+1)); α_25 ≈ 7.7e-5, z ≈ 3.8), a cohort lower bound ≥ 2.5% needs per-dataset point reductions of roughly 3.5% or more.
- The per-dataset SE from fresh data is about 0.2–0.3% of J. This is an estimate, and `09_STATISTICAL_CERTIFICATION.md` replaces it with a computed power analysis.
- That is more than half of all avoidable regret against a hindsight oracle, and about 9× the confirmed v1 effect.
- v1 cannot reach the target. A v2 would have to recover late adoption, the largest component, and only datasets with large late-adoption regret can contribute.
- Changing the cost contract to enlarge relative effects is not permitted (brief §9); contract sensitivity is reported only as a sensitivity analysis.

## 3. Assets

- **C4 source recipes:** 45 in `scripts/qsg_methods_search/c4_sources/`, with 44 build records in `docs/qsg_methods_search/c4_builds/`.
- **Sealed registered windows:** 27 in `<main checkout>/data/c4_sealed/`. austin_animal is excluded by audit. These are batch 1, batch 2 and batch F, and all are opened, hence development-exposed.
- **Fresh-window builds:** 8 under the foundation worktree, `data/c4_sealed/*__fresh.npz`. The 7 eligible ones are now opened and development-exposed.
- **Dev-tier synthetic/real streams:** airlines, criteo and weather (doc 12, tier D).
- **Panel:** 25 comparators (14 adapters + 11 controls, `analyze_all.py`). Every one is class B/C. None is source-faithful; see `docs/qsg_methods_search/sota_expansion/02_BASELINE_FIDELITY.md`.
- **Infrastructure:** search60 compositor plus 60 modules; `eval60.py` fast harness; `fresh_confirm_run.py` / `fresh_confirm_analyze.py`; `c4_build.py --window --tag`.
- **Hardware:** 16 CPU workers are used by existing runners, and there is an RTX 4060 Laptop GPU (8 GB). The simulator is CPU-bound and per-event sequential, so the GPU is useful only for model fitting or learned controllers.

## 4. Data-window design for scale-up

Every dataset gets a **development window** and a later, unopened **confirmation window** from the same recipe.
- For the 27 registered sources, the development window is the registered C4 window, which has already been opened.
- For the 7 fresh sources, the 2025–26 window is now development as well, so their confirmation needs a third period. That period may not exist yet (the 2026-07-01 settling cap), in which case those sources cannot be confirmed now.
- For new sources, development is an earlier period and confirmation a later one, both defined mechanically before any build.

This is Design A of the brief (preselected cohort confirmation) with the Design B union bound used for multiplicity across confirmation attempts. See `07_CONFIRMATION_PROTOCOL.md` when written.
