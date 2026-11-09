# 05 — Baseline fidelity audit and source-faithful ports (Workstream C)

Written 2026-11-09 on `research/paper1-eqsdp-scale25-2026-11-09`. Machine-readable table: `baseline_fidelity.csv` (18 rows: the 14 adapters A01-A14 and four new paper-formula ports P01-P04). Code: `scripts/paper1_scale25/baselines/` (`paper_ports.py`, `test_paper_ports.py`, `smoke_sf311.py`, `build_fidelity_csv.py`).

This audit builds on `docs/qsg_methods_search/sota_expansion/02_BASELINE_FIDELITY.md` (code-side audit of information discipline, budgets and costs, which I re-read and do not repeat) and `01_PRIOR_ART_AUDIT.md`. What is new is (i) source-side verification of every citation this session, (ii) a re-classification into the four requested classes, (iii) paper-formula ports of Model Picker and CAMS with parity tests against the repository ports, (iv) the matched-cutoff wrapper and the list of baselines to equip.

## 1. What was verified this session, and how

"Verified" means the page named was opened on 2026-11-09 with the fetch tool (arXiv abs/HTML/PDF, PMLR, GitHub repository page). The fetch tool summarises pages with a small model, so statements are checked against those summaries and, where I extracted PDF text with `pdftotext` (Model Picker, Gong-Zhang, Chick-Forster-Pertile), against the text itself. Nothing was downloaded into the repository and **no third-party code was executed**: running the authors' code needs a clone and execution of untrusted code, which I treated as needing the user's go-ahead (the repo ledger says the same). So no entry reaches tier T1 (author-code parity). Consequences are stated per row.

Corrections to earlier repo documents found while verifying:

| item | earlier statement | verified this session |
|---|---|---|
| Hara et al. venue | "ACML 2024 / Machine Learning 2024" | The journal record is *Machine Learning* vol. 113 (2024), doi 10.1007/s10994-024-06603-1. The authors' repository README says ACML 2024 (the journal track). Repo `sato9hara/active-model-selection`, MIT licence. The paper itself was not opened. |
| Model Picker budget | "budget as expected proportion" (in other audits' summaries of this family) | The paper has **no** hard budget; only the author code's *recording* is gated. CAMS **does** have a native hard budget ($C_t \le b$ in Figure 1). |
| Model Picker recommendation | adapter "replaces" the paper's deployment by argmax | Algorithm 1 itself outputs the recommendation $\hat I_t=\arg\max_i w_{t,i}$ and separately *samples* $I_t \sim w_t$ for the prediction. The adapter deploys the paper's recommendation, so it is closer to the source than stated. The sampled action is the infeasible one (section 4). |
| Regol et al. | "6 datasets" | arXiv and PMLR abstracts say 7 datasets. |
| Gong-Zhang | "abstract only" | Full text located: Algorithm 1 (EXP4-style paid-observation algorithm), Algorithm 2 (meta-controller over free-budget regimes). Switching costs are used as an analogy/technique, not as a deployment payback rule. Confirms the adapter is not the paper's algorithm. |
| Venues for CAMS (NeurIPS 2024), Model Selector (AISTATS 2025), Qiu (ICML 2026) | taken from the repo ledger | arXiv pages list no venue (Qiu: "v2 is listed as ICML 2026"). These venue strings remain **unverified** here. PMLR confirmed: Karimi (AISTATS 2021, PMLR 130), Regol (ICML 2025, PMLR 267), Gong-Zhang (ICML 2026, PMLR 306). |

## 2. Classification of the 14 published-method adapters

Classes (my definitions, stricter than "has a unit test"):
- **source-faithful**: decision and query rules and constants as printed in the paper; only declared feedback-model adaptations (delay, hard cap).
- **common-contract adaptation**: the paper's core estimator or rule is retained and recognisable, but state space, forecaster, acquisition or deployment is replaced to fit two frozen models, delayed paid labels, switch cost and a hard budget.
- **inspired heuristic**: the decision rule is not the paper's; only an idea or the name is borrowed.
- **not comparable**: the problem cannot be mapped onto the contract (none assigned; the heuristic class already carries that caveat).

| id | registry names | class | one-line reason |
|---|---|---|---|
| A01 | qiu_delayed_movement | inspired heuristic | OCO dynamic-regret learner replaced by a hand-set fixed-share Hedge |
| A02 | gong_zhang_paid_obs | inspired heuristic | source has no payback rule; discounted IW point-estimate payback is a repo invention |
| A03, A04 | gongT_w100_m10, gongT_w800_m20 | inspired heuristic | A02 with a dev-tuned window and margin (grid 16) |
| A05, A06 | upf_d0.95_m50, upf_d0.8_m50 | common-contract adaptation | Eq. 16-20 delta-quantile recursion retained; forecaster, cells, reversibility replaced |
| A07, A08 | chalgse_l1.0_g0.2, chalgse_l0.9_g0.3 | inspired heuristic | Hoeffding-bound payback idea; GSE/OSE/LSE and learning curves not implemented |
| A09 | cams_adapter | common-contract adaptation | query and update arithmetic from the author code; constant policies only, so the contextual method is absent |
| A10 | model_selector_causal | inspired heuristic | pool algorithm replaced by a record gate; reduces to paced disagreement sampling |
| A11 | model_picker_adapter | common-contract adaptation | Algorithm 1 arithmetic; delayed IW update; hard cap; deploys the paper's recommendation |
| A12 | online_llm_picker | common-contract adaptation | formulas from the paper; 0/1 loss, `eps` ours, degenerate at two models |
| A13 | variance_min_ipw | inspired heuristic | score ported, estimator replaced (HT for LURE); "NOT the published method" |
| A14 | han_arw_label_clock | common-contract adaptation | adaptive-window estimator ported from printed equations; deployment mapping ours, margin 0 |

**Counts: source-faithful 0, common-contract adaptation 6, inspired heuristic 8, not comparable 0.** None of the 14 is source-faithful, so the panel supports the claim "beats strong tuned heuristics and adapted published rules", never "beats Qiu / Gong-Zhang / CAMS / ...". Naming rule from the repo ledger stays: results are written "Qiu-style Hedge adapter", "UPF-style (T3) adapter", etc. The new ports P01-P04 below are source-faithful for the rules they implement.

Hyperparameter search spaces and selection rules (from `sota_extra.py`, unchanged): `gongT` 16 configs (W in {100,200,400,800} x margin in {0,5,10,20}); `upf` 9 (delta in {.5,.8,.95} x m in {50,100,200}); `chalgse` 12 (lambda in {1,.97,.9} x gamma in {.1,.2,.3,.45}); synthetic-dev winners were selected in-sample on the D3 seeds; real-dev winners on the 14 exposed pilot streams (several at the grid edge: `gongT_w800_m20`, lambda .97 for the hurdle families). Every other adapter runs at one default. **Tuning asymmetry:** three adapter families (six of the 14 rows: A03-A08) get dev tuning with 9-16 configs, the other eight rows run one default, and the internal controls get 12-20 configs. The panel is therefore not "equally tuned"; the safe reading is that the strongest per-dataset reference is a *tuned internal control or tuned family member* on most datasets (doc 20 found W+cut, model_picker, online_llm_picker and econF as strongest references per dataset).

## 3. Source-side findings that change how a comparator should be described

1. **Model Picker (Karimi et al.).** Algorithm 1: $\eta_t=\sqrt{\ln k/(2t)}$, $w_t \propto \exp(-\eta_t L_{t-1})$, recommend $\arg\max w_t$, act by $I_t\sim w_t$, $q_t=\max\{v(p_t,w_t),\eta_t\}$ if $v\neq 0$ else 0, $v=\max_c \langle w,\ell^c\rangle(1-\langle w,\ell^c\rangle)$, $L_t=L_{t-1}+\ell_t Q_t/q_t$. Theorem 1: expected regret $\le 2\sqrt{2T\ln k}$. Theorem 2: expected queries $\le 5\sqrt{T\ln k}+2L^*_T$ under stated conditions. The author-code arithmetic as described by the fetch tool matches (eta_0 = sqrt(ln M / 2), eta_t = eta_0/sqrt(t), posterior with min-shift, floor `max(u, eta_t)`, IW update, posterior sampling, budget only gates recording). The repo port `model_picker.py` agrees with all of it.
2. **CAMS (Liu et al.).** Figure 1 and Eq. 4: stochastic branch uses $\eta_t=\sqrt{\ln|\Pi^*|/t}$ and deterministic argmax recommendation; $z_t=\max\{1/\sqrt t,\ \mathfrak E(\hat y_t,w_t)\}$ with $\mathfrak E=\frac1c\sum_{y:\bar\ell^y\in(0,1)}\bar\ell^y\log_c(1/\bar\ell^y)$; a label is bought only while $C_t\le b$. Three gaps between paper and the repository port (which follows the author code): (a) learning rate $\sqrt{P/t}$ in code vs $\sqrt{\ln m/t}$ in the paper (ratio $\sqrt{2/\ln 2}\approx1.70$ for two policies); (b) the code returns 0, hence no query and no exploration floor, in the agreement region and whenever a class mass rounds to 0 at 6 decimals, whereas the paper floors at $1/\sqrt t$ in every round; (c) the paper's $\mathfrak E$ skips classes with $\bar\ell\in\{0,1\}$, the code returns 0 as soon as one class has zero mass. Tests assert (a) and (c); (b) is by construction. For two classes $\mathfrak E$ equals the repo's `weighted_entropy_query` (tested).
3. **Gong-Zhang.** Regret with paid observations and a free-observation budget; Algorithm 2 selects between algorithms by comparing the budget with thresholds. No deployment, no delay, no payback. The adapter is a different algorithm using the name.
4. **The Challenger.** The v2 abstract's headline algorithm is a sequential evaluation using *local learning-curve trends* (LSE); GSE (Hoeffding half-width) and OSE are baselines inside that paper. The adapter ports the stopping idea only.
5. **UPF.** Code: none. The PMLR page links only the proceedings metadata repository. Parity can only be T2.

## 4. C2: source-faithful ports and their parity evidence

Implemented in `scripts/paper1_scale25/baselines/paper_ports.py` against the same `Policy` interface as the sota_extra policies (`predict`, `request_labels`, `observe`, `state_dict`, `load_state_dict`; labels arrive through `observe` after `delay`, importance weights are the frozen issue-time probability):

| id | class | what it is |
|---|---|---|
| P01 `mp_paper_recommend` | source-faithful | Algorithm 1 with the paper's recommendation deployed (incumbent on exact ties, ours) |
| P02 `mp_paper_sample` | source-faithful | Algorithm 1 acting by $I_t\sim w_t$ exactly as printed |
| P03 `cams_paper` | source-faithful, constant policies | CAMS stochastic branch, $z_t$ floor in agreement too |
| P04 `cams_paper_gated` | common-contract adaptation | P03 buying only on disagreement events |
| `*_H1100` | wrapper | each of the above with the matched cutoff |

**Parity evidence (14 tests, all pass; command `python -m pytest scripts/paper1_scale25/baselines/test_paper_ports.py -q`).** This is a *paper-versus-repository-port* cross-check, tier T2:
- the paper formulas (transcribed from the paper this session, independently of the repo port) reproduce the repo port's $\eta_t$, $w_t$ and $q_t$ to 1e-12 over random inputs for $k\in\{2,4,5,8\}$, $|C|\in\{2,3,4\}$;
- replaying the repo's `ModelPickerNative` run with its own query indicators through the paper formulas reproduces its posterior log, query-probability log and final importance-weighted losses;
- hand-computed toy: $k=2$, predictions (0,1), uniform $w$ gives $v=.25$ and $\eta_1=\sqrt{\ln 2/2}$; agreement region gives $q=0$;
- an identification sanity check (20 runs, 4 models, accuracies .70-.90): the best model has the smallest estimated loss in at least 17 of 20 runs (a plausibility check of Theorem-level behaviour, not a proof);
- CAMS: $\mathfrak E$ equals the repo's entropy-style score for two classes; the documented paper-versus-code gaps are asserted.

**What parity does not establish.** The authors' own code was not run. The only evidence about the author code is the fetch tool's description of `model_picker.py` (formulas match the port). The `vendor_sota/` directory is still empty, so the five inherited author-parity tests keep skipping. To reach T1 one would (with the user's go-ahead) clone `DS3Lab/online-active-model-selection` and `xuefeng-cs/Contextual-Active-Model-Selection` into `vendor_sota/` at pinned commits and run their small datasets. I did not claim T1 and did not substitute anything for it. Model Selector was not ported: its pool algorithm needs a target-event interface the simulator does not offer (it can label only the current event), and the repo's native pool port already exists.

**CPU smoke (plumbing only, descriptive).** registered `sf_311` window, episodes 0, 2, 4 x policy seeds 0, 1 (6 runs per row), T=2000, B=200, delay 100, c_q=.05, c_s=5, via `trace_run.run_policies` (checksum-validated sealed arrays). The window is development-exposed; nothing here is evidence of method quality. Command: `python scripts/paper1_scale25/baselines/smoke_sf311.py`; rows in `smoke_sf311_results.csv`.

| policy | net | loss | labels | switches |
|---|---|---|---|---|
| model_picker_adapter (inherited) | 472.5 | 460.5 | 73 | 1.7 |
| cams_adapter (inherited) | 479.8 | 458.2 | 200 | 2.3 |
| EQSDp arm R / Wald .98/.3 (no cutoff) | 476.3 | 461.3 | 200 | 1.0 |
| mp_paper_recommend | 476.4 | 461.3 | 69 | 2.3 |
| mp_paper_sample | **1158.9** | 457.2 | 69 | **139.7** |
| cams_paper | 477.5 | 457.5 | 134 | 2.7 |
| cams_paper_gated | 471.7 | 458.0 | 108 | 1.7 |
| mp_paper_recommend_H1100 | 475.6 | 461.3 | 52 | 2.3 |
| mp_paper_sample_H1100 | 1280.4 | 464.5 | 52 | 162.7 |
| cams_paper_H1100 | 476.1 | 457.5 | 105 | 2.7 |
| cams_paper_gated_H1100 | 470.6 | 458.0 | 86 | 1.7 |

Observations (six runs each; differences of a few net units are noise): the source action rule of Model Picker is cost-infeasible under c_s=5 (about 140 switches, net 2.4x higher), which is why every published selector needs a deployment layer to enter this comparison; the paper's CAMS rule buys 134 labels including agreement events (the gated version buys 108); the matched cutoff removes 15-30 labels and does not change the loss for these acquisition-heavy selectors.

## 5. Which baselines should be equipped with the matched cutoff, and how

**Why.** The frozen method is a package: EQSDp plus a hard label cutoff plus E48/F60. Doc 18 showed that W+cut ties EQ+cut, so an unequipped comparator is compared against a package whose main ingredient it was denied. A fair reference for a 2.5% claim must be the best of {raw, cutoff-equipped} per comparator, chosen on development data.

**Cutoff definition (identical to the frozen method).** No purchase when `t + delay > T - H`, H = 1100 for T = 2000 (a fraction .55 of T for streams of other lengths, fixed before the dev run). Primary comparison: the same H for all. Sensitivity: H tuned per family on development data only, reported separately.

**Mechanism.** `CutoffWrapper(inner, T, delay, H)` in `paper_ports.py`: ask the inner policy first (its RNG stream and paced counters stay aligned with the uncut run, as the search60 compositor does), then veto a granted request that falls after the cutoff; `inner.pending` is decremented on a veto (the EQSD family keeps that counter). It is inert for H very negative (tested bit-for-bit) and blocks all late purchases for finite H (tested).

| comparator group | equip? | safe with the wrapper? |
|---|---|---|
| wald, hoef, smarg, dwell, econF, economic_replacement, chalgse (EQSD-style: A07, A08 and the controls) | **yes, required** | yes (pending counter repaired). `s2wald_*_H*` already exist for Wald only; generalise to the other families through the wrapper |
| gongT, qiu (A01-A04; paced) | yes | yes (request-time state is only the event-based pacer) |
| upf (A05, A06) | yes | yes; note the cutoff also removes its forecaster's late data |
| cams, model_picker, online_llm_picker, variance_min, han_arw (A09, A11-A14) | yes: they spend labels all stream | yes |
| model_selector_causal (A10) | yes, but needs a port-specific fix | **no**: the record is popped from `pool` at request time, so a vetoed request would consume an eligible record without a label; re-insert on veto |
| EQSDp arm R / arm B (no cutoff), `CONTROL_never_switch` | arm R/B are the unequipped parents: keep as ablations | n/a |

**Reporting rule.** Keep three columns per comparator: raw, +cutoff, best-of (selected on dev). The reference for any certified improvement is the per-dataset best-of over the whole panel, never the raw column alone. The ledger statement "strongest reference is W+cut on 4/7 fresh datasets" (doc 20) is the reason.

## 6. Other fairness issues carried over, unchanged

- Public `delay` is an input to A01-A06 and Xu; the frozen method does not use it (mild asymmetry in the comparators' favour).
- Three adapters are tuned on pilot data that is exposed; selection is in-sample on dev, not a test.
- Grid-edge winners (`gongT` W=800, lambda .97) mean the grids may be truncated; extend before the final panel if budget allows.
- `T % m == 0` is required by the UPF adapter; a stream of length not a multiple of m crashes it (scale-25 streams of other lengths need a guard).
- `run_metrics` does not export `refused_requests`; the new policies stop requesting at zero budget, so they cannot show refusals, but the field should be exported before any confirmatory run.

## 7. Open items

1. T1 author-parity (needs the user's go-ahead to clone and run `DS3Lab/online-active-model-selection`, `xuefeng-cs/Contextual-Active-Model-Selection`, `RobustML-Lab/model-selector`, `sato9hara/active-model-selection` at pinned commits).
2. Verify the venue strings marked unverified in section 1; open Hara et al. itself.
3. A Model Selector pool-faithful port needs either a batch-labelling simulator mode or an offline pool experiment outside the stream contract.
4. CAMS with contextual policies needs features; the scale-25 datasets that expose features could host it, which would make CAMS the one comparator exercised on its native problem.
