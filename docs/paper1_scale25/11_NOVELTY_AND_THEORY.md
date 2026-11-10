# 11 — Novelty, fidelity and theory: summary and classification (Workstreams C and E)

Written 2026-11-09. Sources: `05_BASELINE_FIDELITY.md` (+ `baseline_fidelity.csv`), `PRIOR_ART_AUDIT.md`, `NOVELTY_MATRIX.md`, `THEORETICAL_ANALYSIS.md` (+ `theory/`). Code: `scripts/paper1_scale25/baselines/`, `scripts/paper1_scale25/theory/`. Commits on `research/paper1-eqsdp-scale25-2026-11-09`: 0e1ba476 (paper-formula ports and parity tests), b094704c (fidelity audit and CSV); the prior-art, matrix, theory and this summary are in the final commit listed in the hand-off report.

## 1. Honest classification of the contribution

| candidate label | verdict | why |
|---|---|---|
| Novel algorithm / decision principle | **No** | Payback against a switching cost with a confidence bound is the Challenger's; one-step knowledge-gradient value of information with a delay and its multi-sample version are Frazier-Powell-Dayanik / Chick-Forster-Pertile; pending labels as uncertain futures are PRopagate and the batch-BO literature; the hard cutoff is finite-horizon value-of-information decay. E48/F60 contribute constants and a composition, not a principle. |
| Novel theory | **No** | No guarantee exists for EQSDp, E48, F60 or the cutoff. The exact DP is standard Bayes-adaptive MDP theory; the numerical structure it exhibits (complementarity of pending labels, state-dependent label deadline) is a finding about an instance family, not a theorem. |
| Novel integration (a problem formulation plus a controller) | **Plausible, weakly supported** | I found no published work with paid labels, delay, hard budget, reversible deployment, switching cost and finite horizon together (matrix: no other row has more than four of eight features). Each ingredient has a precedent and the absence of a hit is not proof. |
| Empirical improvement | **Real but small** | Doc 20: -0.39% of J on 7 fresh datasets, 7/7 negative; +0.38% against the strongest per-dataset reference; EQ+cut ties W+cut. The scale-25 target (2.5% certified) is about 9x this and is bounded by the headroom in doc 11. |
| Benchmark / fidelity contribution | **Yes, modest** | A 25-comparator panel on shared failures, with a transparent classification (0 of 14 source-faithful, 6 common-contract, 8 inspired heuristics), source-verified citations with several corrections, paper-formula ports with parity tests, a matched-cutoff wrapper, and an exact-DP reference solver. |
| Negative / diagnostic result | **Yes** | In the exact stationary model E48 hurts and F60 is neutral; the cutoff's effect changes sign with the change process; the package sits 5-7% (stationary) to about 17% (strong change) of J above the Bayes optimum. |

Safest paper framing today: a **problem formulation and benchmark with a strong heuristic baseline package and an exact reduced-DP reference**, not a new method. A method claim would require the package to beat the *equipped* panel on scale-25 data by an effect that survives the preregistered certificate, which v1 does not do.

## 2. Hand-off numbers

- **Fidelity classes (14 adapters):** source-faithful 0, common-contract adaptation 6 (UPF x2, CAMS, Model Picker, Online LLM Picker, ARW), inspired heuristic 8 (Qiu, Gong-Zhang x3, Challenger x2, Model Selector, variance-min IPW), not comparable 0.
- **Ports achieved (C2):** paper-formula Model Picker (recommend and sample action), CAMS stochastic branch (ungated and disagreement-gated), the `CutoffWrapper`, 14 passing tests, CPU smoke on `sf_311` (3 episodes x 2 seeds, plumbing only). Parity is paper-vs-repository-port (T2); the authors' code was not executed (needs user consent), so no entry reaches T1. Model Selector not ported (pool algorithm).
- **Source-side corrections:** Hara et al. is *Machine Learning* 113 (2024), not ACML only; Model Picker has no hard budget while CAMS has one; Model Picker's argmax deployment is the paper's own recommendation; Regol et al. used 7 datasets; Gong-Zhang's switching cost is an analogy, not a payback rule; venue strings for CAMS, Model Selector and Qiu et al. remain unverified.
- **Closest prior art:** Chick-Forster-Pertile 2017 (delayed-response sequential experiment with pipeline observations, finite horizon, switching cost, KG continuation set); The Challenger (payback with a confidence bound); Castellani-Schmitt-Hammer 2022 (delayed labels under drift with budget); Frazier-Powell 2010 (nonconcave value of information); Regol et al. 2025; CAMS and Model Picker.
- **E48 = KG with arrival delay; F60 = multi-sample KG (not a rollout in Bertsekas's sense); cutoff = finite-horizon decay of information value.** The combined problem is, as far as the search shows, not published; the package approximates a Bayes-adaptive DP with no stated gap.
- **DP approximation gaps** (T=160, B=24, d=8, c_s=2; exact or 6,000-episode paired Monte Carlo of the repository's own stack): stationary flat prior, EQ+cut is 4.8% of J above the optimum (J=48.5 vs 46.2); +E48 7.1%; +F60 4.7%; +both 7.0%. Hazard environments: strong change (p in {.2,.8}, h=.01): J=69.3 vs optimum 57.4 (17% of J; about half of the achievable gain realised); F60 -0.52 +- 0.11, E48 +0.36 +- 0.16, pair -0.34 +- 0.17, removing the cutoff -1.52 +- 0.13. Weak change: the optimum barely beats not buying labels and the controllers are worse than never switching.
- **Structure:** pending labels are complements at ambiguous evidence (value of another purchase 0.065 -> 0.111 with one pending) and substitutes at decisive evidence; the optimal label deadline is state-dependent (t about 110-150 of 160) and much later than the heuristic cutoff (t=64).

## 3. Continue / pivot / stop assessment (research-charter language)

- **Continue** the exact-DP line as a *reference and diagnostic*: it is cheap (seconds to minutes on CPU), validated against the repository's own code, and it reports headroom that the heuristic package leaves (5-17% of J in stylised worlds).
- **Pivot the Paper 1 claim** away from "E48/F60 are the mechanism" toward "matched cutoff + payback switching is a strong baseline package; the formulation, the panel and the DP reference are the contribution", unless a v2 controller (for example one that approximates this DP with an evidence model fitted on development data) beats the equipped panel in the preregistered scale-25 confirmation.
- **Do not stop**, but do not write a novelty claim stronger than "novel integration" and do not describe the cutoff or E48 as principled: the analysis does not support them in the exact model.
- **Risks:** the reduced-model gaps depend on unrealistic stylisation (known disagreement rate, tight budget, untuned controller parameters in reduced units); the E48 table and the real stack disagree in magnitude; the prior-art verdict rests on listing-level evidence for about half the rows.

## 4. Open work I did not do

Author-code parity runs (consent needed); a larger-budget DP (B ~ 80) with a vectorised VOI to match the real budget ratio; a controller that approximates the DP; fitting the DP's evidence model to scale-25 development data; reading the LISTING-level papers in full; searches for restless-bandit and real-options treatments.
