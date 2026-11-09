# 10 — EQSDp-JointBayes: method search plan (locked before any candidate is run)

Written 2026-11-08 on `research/paper1-eqsdp-foundation-2026-11-08`, after 00–03.

This adopts the user-supplied direction ("Paper 1: reassessment", 2026-11-08):
- keep EQSDp's reversible, confidence-bound economic switching;
- look for extra savings through mechanisms tuned Wald does not implement: jointly pricing a label purchase, waiting, switching now, and reversing later.

Nothing here is a result.

## 1. Prior evidence this plan must respect (not re-run under new names)

| Source | Finding | Consequence |
|---|---|---|
| SAES Phase 1 (`docs/qsg_methods_search/SAES_PHASE1.md`) | +100% *free* labels are worth only 5.3 units to tuned Wald (+50%: 3.8) | Label timing alone (C1) has a ceiling below the ~8.7 units a 2% gain needs. C1 must win through *decisions*, not fees. |
| Lane A (`research/shiftlab-promising-directions-2026-10-30`) | Under tight promotion-risk limits a fixed calendar is exactly optimal; joint planner gains only 0.7–1.2% at α=.10, B=4 | Joint acquisition+switching has small *proven* gaps in the risk-constrained version. Our contract is unconstrained-cost, so this is not a refutation, but it bounds expectations. |
| Next-method screen (`NEXT_METHOD_RESULTS.md`) | 12 mechanisms tie or lose to tuned Wald. Among them: D1 ambiguity bursts (−0.75, tie), BOCPD (A5/A5b/F), asymmetric hysteresis (B1), ESS-Wald (E, −0.81, best robust) | Do not repeat these as standalone modules. E (dependence) is the only one with a real-stream signal, which is why module G is admissible. |
| Oracle diagnostic | An evaluator-side restart at the change time gains 11.7 units | The headroom is in *when the better model is deployed*, not in label fees. |
| 03_MEASURE_RESULTS (nine datasets) | Arm R: false promotion .676 vs Wald λ.97 .521; switches 1.34 vs 1.10; time to correct action 209 vs 187 (GZ paid-obs) | Concrete residual failures: false promotion and late adoption. These are the targets for C2/C5. |

## 2. Data, splits and baselines

- **Development data:** the nine datasets in `00_SCOPE.md`, with their registered episodes. These are exposed and selected on outcome, which is recorded in 00.
  - Within development, episodes are split by parity: **even episodes = search/tuning**, **odd episodes = selection check**.
  - Every candidate *and* every baseline is tuned on even episodes only. Winners are compared on odd episodes.
- **Synthetic sanity family:** the C3 change/guard family on dev seeds 2026110901 (already used). It is only a regression check that nothing breaks; not used for selection.
- **Confirmation data (reserved, built only after freezing):** later chronological periods of the same nine sources, after each registration window ends. These are fetched and sealed by the existing `c4_build.py` contract only *after* the candidate is frozen, then opened once.
- **Baselines, tuned with the same effort as candidates** on even episodes:
  - EQSDp arm R;
  - the Wald family λ ∈ {.9,.95,.97,.98,.99} × γ ∈ {.1,.2,.3,.5};
  - scaled margin;
  - econF;
  - ESS-Wald (E);
  - GZ-RD, UPF-style, Challenger-style;
  - a deadline-aware label schedule and a PAVE-style pacing rule if they port cleanly.
  - The **reference baseline** is the best of these on even episodes (equal-dataset mean J).
- **Contract unchanged:** B=200, c_q=.05, c_s=5, T=2000, 10 policy seeds. Each candidate is a new policy added to the existing simulator. The frozen EQSDp code is not modified.

## 3. Metrics (all reported, every run)

- Total cost improvement: (J_ref − J_new)/J_ref.
- Accuracy difference: (L_new − L_ref)/T.
- Plus the 01 measures: harm vs the frozen incumbent, capture, wrong exposure, time to correct action, false promotion, switches, label efficiency, terminal correctness.
- And: label count, decision delay and runtime.
- Pareto frontier of (J, L/T).

## 4. Stages and gates

Effects are graded, not hard-gated (fair-evaluation standard), apart from the stop rules below.

**Stage 0 — headroom (diagnostic, evaluator-side).** On the nine, even episodes, decompose arm R's and tuned Wald's regret over the best fixed model into five parts:
1. late adoption: loss on challenger-better episodes before first deployment;
2. false promotion: loss and switch costs on not-better episodes;
3. reversal churn;
4. label spend;
5. switch spend.

Also measure the free-label ceiling on the nine, by running arm R and tuned Wald at B=400.

**Stop rule:** a module whose target component is worth less than 0.5% of J_ref is not built.

**Stage 1 — single components** (each a minimal policy on top of arm R; matched seeds; even episodes):
- C1 = A + C: decision-reachability label gating plus a budget shadow price;
- C2 = E + D: persistent-advantage belief plus reversal option value;
- C5 = F: risk-aware early adoption plus conservative reversal.
- B (pending-label VOI) is built only inside C3.
- Each comes with a simple control that isolates its mechanism. For example, C1 vs the same label count on a fixed calendar, and C2 vs Wald with a raised hurdle that matches its promotion rate.
- **Continue** a component if the paired Δ vs the reference baseline on even episodes is < 0 with a CI excluding 0, or if it is at least −0.5% with a clear mechanism signal on its target component.

**Stage 2 — combinations by constrained Bayesian optimisation.**
- Run only if at least one Stage-1 component continues.
- Use BoTorch, if installable, on modules {A,B,C,D,E,F,G,H} × continuous parameters. If it isn't installable, use a GP/TPE surrogate and say so.
- The acquisition is the expected constrained improvement per unit compute, with δ = 0.5% and ε = 0.1 pp accuracy.
- C3 (C1 + C2 + B) must beat C1 and C2 individually to be kept.
- Runs use a budget ladder: small screens, then larger paired replications.

**Stage 3 — selection check.**
- The best candidate and the re-tuned reference baseline are run once on odd episodes.
- Report Δ J (%), Δ L (pp), and the full measures.
- Freeze if Δ J < 0 with a CI excluding 0 and Δ L ≤ 0.1 pp.

**Stage 4 — fresh chronological confirmation.**
- Write the protocol, build the sealed confirmation data, register it, and open it once.
- **Primary:** frozen candidate vs the frozen reference baseline on the nine later periods; dataset-level t-test plus sign majority (as in protocol 10).
- **Target for the central claim:** ≥ 2% cost reduction at ≤ 0.1 pp accuracy loss. A smaller confirmed gain is reported at its graded size.

**Stage 5 (theory, in parallel, optional):**
- An exact dynamic program for a small model: two models, disagreement-only evidence, delay d, budget B, reversible switching.
- Characterise when pending labels or remaining budget change the optimal action, given the same Wald statistic.
- Use the DP as an oracle for the approximate controller.

## 5. Stop / pivot

- **Stage 0 shows < 0.5% headroom in every component:** stop the method search. Paper 1 is then the nine-dataset EQSDp result plus the measures (00–03).
- **No Stage-1 component continues:** same as above, plus a negative-results section.
- **Stage 3 fails:** report it, and do not open the confirmation data.
