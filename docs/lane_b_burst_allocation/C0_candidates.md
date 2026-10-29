# C0: candidate acquisition-and-switching mechanisms (Lane B, phase C)

**Date:** 2026-10-29. **Gate:** C0 (`LANE_CONTROL.md`, phase C). **Status:** a design memo only. No
code, experiment, theorem, novelty or efficacy claim. Nothing here has passed a Codex screen. Every
theorem statement below is a *target* with a kill route. External papers not already audited in the
repository are named from memory and marked **(unverified)**. They are audit obligations, not citations.

**Read for this memo:** `AGENTS.md`; `docs/research_charter.md` (head);
`docs/budgeted_switching_research_goals.md` (all checkpoints through "G1 structural reduction
2026-10-29"); `docs/switching_problem_v1.md`; `docs/switching_novelty_delta_v1.md`; the titles and
decisions of all 54 `docs/switching_*_{audit,prior,screen}_v1.md` files, as summarised in those two
files; `switching_reversal_budget_frontier_candidate_v1.md`;
`switching_first_promotion_decomposition_v1.md`; `LANE_CONTROL.md` (phase C);
`CODEX_REVIEW_1.md`; `B1_corrective_check.md`; `B0_prior_art.md` (head); `R2_dev_measurements.md`;
`docs/research_refinement_v1/stage1/STAGE2_RESULTS.md`;
`papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`. I also inspected the
code paths `e2_acquisition_pacing._plan`, `e3_intervention_factorial`, `integrated_pipeline`
scenario list, `data/synthetic/generators.py` (recurring patterns), `contract/harness_v2.py` and
`interface_v2.Switcher`.

## Summary verdict (ranked)

| Rank | Candidate | Verdict | Novelty risk | Main reason it may die |
|---|---|---|---|---|
| 1 | **C1 Recurrence-locked switching (RLS)**: anticipatory switching at predicted regime boundaries, with acquisition that localises boundaries and certification by a phase-stratified e-process | **Conditional survivor**: send it to the Codex screen | Medium-high | (i) Its separation is against the class of "post-change-evidence-required" policies; a reviewer may call that class a straw man. (ii) When the phase is visible in public covariates it reduces to calendar stratification (an established composition). (iii) On the frozen real tasks no win is expected (see constraint K4). |
| 2 | **C2 Split-clock switching (SCS)**: a fast biased surrogate label for rollback and a slow gold label for certification | **Survives only under a changed information structure**; it is not runnable on the frozen tasks | High | It probably reduces to controlled sensing with delay-shifted channel costs, plus PPI-style calibration (the repo already runs delayed PPI) |
| 3 | **C3 Harm-budgeted provisional deployment (HBPD)** | **Discarded** | n/a | A symmetry argument (below) shows that common labels make speculative deployment a zero-sum transfer of loss between the "gain" and "harm" worlds. It is a change of risk preference, not an algorithmic separation; it also overlaps conservative bandits and canary testing. |

**Bottom line.** Under the frozen information structure (one common label stream, action-independent
outcome law, fixed delay), I found no mechanism that is clearly outside the audited prior art *and*
yields a non-additive separation *and* can win on the frozen real tasks. C1 is the only candidate
with a crisp, falsifiable, non-additive separation, and it gets that separation by exploiting
*temporal predictability* (recurrence), not the decoupling of information from deployment itself.
If C1 fails the Codex screen or its kill criteria, the honest outcome is the pivot memo in the last
section: the decoupling is precisely what makes the problem decompose into prior art.

---

## Binding constraints found while screening (they apply to every candidate)

**K1. With one common label stream, acquisition is timing only.** A query reveals `Z_t` whatever is
deployed, and the outcome law does not depend on the action. So the only acquisition choice is
*when* to query, and maybe at which covariate. Lane A's audits close generic timing:
- Geng–Bayraktar–Lai (finite sampling rights);
- Chandar–Tchamkerten scout/confirm;
- Li et al. (usage-constrained sensing and stopping);
- Hampson–Jennison (delayed group-sequential designs);
- Huang et al. (channel allocation collapses to a single stream).

A surviving acquisition rule must therefore exploit *structure in time* (C1) or a *second channel* (C2).

**K2. Global false-promotion risk is absorbed at the first promotion**
(`switching_first_promotion_decomposition_v1.md`). Everything after the first promotion is a
single-law delayed POMDP, which is closed by Subramanian et al. (JMLR 2022) and Bayraktar–Ludkovski.
A candidate cannot claim novelty from post-promotion rollback planning as such.

**K3. Information symmetry (derived here; elementary).** Take Lane A's worlds `P+` and `P-`: they are
identical before `nu`, with paired gain `+Delta` or `-Delta` from `nu` on. Couple the private coins.
Until the first post-`nu` label is released, the action laws coincide. Let `w` be the time until
decisive post-`nu` evidence arrives (`w >= d`), and let `D` be the expected number of rounds in
`[nu, nu+w)` on which the candidate is deployed. Then the excess loss in `P+` is `Delta(w-D)` and the
harm in `P-` is `Delta D`, so their sum is `Delta w` for **every** policy. Deploying earlier only
moves loss between the two worlds. Hence decoupling plus reversibility alone cannot give a minimax
gain. A gain must come from:
- **predictability**: the boundary time is forecastable from the past, which breaks the coupling
  (C1);
- **faster evidence**: a lower-delay channel shrinks `w` (C2);
- **asymmetric priors or costs**: a Bayes reweighting (C3, discarded).

This explains Lane A's finding that adaptive timing had no value in six geometric-dwell HMM cells.
With geometric dwell the boundary hazard is constant, so the past does not predict the boundary.

**K4. The frozen real tasks barely discriminate switching methods.** The figures below are
back-of-envelope, from development aggregates in `R2_dev_measurements.md`. They use a Gaussian
oracle-alternative approximation `KL ~ mu^2/(2 sd^2)`. That is the best case for any likelihood-ratio
test; range-based betting e-processes do worse.

| Task | Signal on disagreement rounds | Implied KL per label | Labels to certify at `alpha=.05` (`log 20 / KL`) | Disagreement rounds available | Consequence |
|---|---|---|---|---|---|
| Binance | `mu/sd = 0.00135/0.0366 ~ 0.037` | `~6.8e-4` | `~4,400` | 3,428 | Even certifying the average gain is infeasible |
| OPSD, whole window | `mu/sd ~ 0.044` | small | infeasible | 161 | Average gain cannot be certified |
| OPSD, half-split | means `-0.052` and `+0.064` (`|mu|/sd ~ 0.4`) | `~0.08` | `~35` | ~80 per half | One sign change is detectable |

So:
- On **Binance**, every alpha-controlled switching method will almost always abstain. Methods can
  differ only in query spend, which is classical futility stopping.
- **OPSD** looks like a single-change instance, where the relevant competitor is a classical
  e-detector plus a threshold/rollback composition.

The user's requirement (b) "real-data wins over the strongest baselines" is therefore close to
unattainable on the frozen tasks for *any* mechanism. This is a property of the tasks, not of
the candidates. It should be stated before any C1–C4 work, so that a futility-only query saving is
not later presented as a switching win.

---

## C1. Recurrence-locked switching (RLS)

### C1.1 Algorithm sketch

**Model family `F(L, sigma, Delta, d, B, c, k, alpha)`** (evaluator side):
- **Policies and loss.** Two frozen policies. On disagreement rounds `Z_t` lies in `[-1, 1]` with
  mean `+Delta` in "good" segments (the candidate is better) and `-Delta` in "bad" segments.
- **Segments.** Good and bad segments alternate. Dwell lengths are `L_j = L + xi_j`, with `xi_j`
  independent, `|xi_j| <= sigma` or another declared dispersion, and an unknown offset `phi`.
- **Covariates.** `X_t` carries no phase information. This is essential; otherwise the problem is
  contextual stratification.
- **Feedback and costs.** Fixed delay `d`. The pathwise cap `B` is charged at request time. Costs are
  `c` per query and `k` per switch.
- **Risk.** Lane A's global any-promotion contract under the event-time conditional null.

**Learner state:**
1. A posterior (or particle/grid belief) over `(L, phi)` and the dispersion, updated from released
   labels only. Its size is `O(L_max^2)` on a grid, or `O(L)` if `L` is known.
2. The pending-query list (request times, unreleased outcomes hidden).
3. The remaining rights `q` and a verification reserve `R_v`.
4. A phase-stratified e-process `W_t`. Each queried round is assigned a stratum `s_t` in
   {predicted-good, predicted-bad, boundary-probe} *at request time* from the posterior. `W` bets only
   on predicted-good, non-probe labels: `W_t = prod (1 + lambda_s Z_s)`, with `lambda_s` predictable.
   It updates at release time (fixed ordered delay).
5. A certified flag, the deployed action, and a recurrence-consistency e-detector on the residuals
   `Z_s - mu_hat(s_s)` (two-sided; economic only).

**Acquisition rule (boundary-localising, pending-aware):**
- **Pre-certification.** Query predicted-good mid-segment disagreement rounds (the cleanest evidence
  for `W`), plus `m_j` probe queries per upcoming boundary.
- **Probes.** Probes follow a probabilistic-bisection (Horstein-type) rule. Query at the posterior
  median of the next boundary time, and do not re-probe a posterior quantile while an earlier probe
  of it is pending.
- **Across boundaries.** Because boundaries share `(L, phi)`, the answer from a probe at boundary `j`
  (released `d` later, before boundary `j+1` when `d < L`) sharpens the prediction of boundary `j+1`.
- **Post-certification.** Only probes plus sparse mid-segment verification queries at rate `r_v`.
- **Budget.** `m_j = min(m_max, (q - R_v) / (remaining boundaries))`. `R_v` is fixed at the start,
  so verification never starves. A query that would overdraw is refused (the harness rule).

**Deployment and switch rule:**
- Keep the incumbent until `W_t >= 1/alpha`. This is the only promotion gate, so the global
  any-promotion guarantee is inherited verbatim.
- After certification, deploy the candidate on predicted-good segments. Switch at
  `tau_j* = argmin_tau E_post[Delta |tau - b_j|]`, the posterior median of boundary `j`, *without
  waiting for post-boundary labels*. Skip a segment if `Delta_hat * L_hat_j <= 2k`.
- **Fallback.** If the consistency e-detector crosses, recurrence has broken. Drop to detection
  mode (the safe composition baseline below) until the consistency test recovers. Fallback is
  economic only: rollback is not risk-constrained under the global contract.

**Current-regime value** is justified by the *declared recurrence model plus verification*. Lane A's
contract permits this route ("current-regime evidence from post-change data **or** a forecast model
under explicit persistence assumptions"). `W` is never presented as current-value evidence.

### C1.2 Why this is not prior art X

See the master table below (column C1). In short:
- It is not a timing rule for an unknown single onset (Geng, Chandar–Tchamkerten, Lau–Tay).
- It is not restart/detection (e-detector, DAL, CUSUM).
- It is not a known-model POMDP planner (Bayraktar–Ludkovski, RC-POMDP, sequence form).
- Its separation is from the class all of those occupy: policies that switch only after post-change
  evidence.

The closest **unaudited** threats are:
- **(a)** label-efficient Hedge over periodic *schedule experts* (Herbster–Warmuth tracking with
  structured experts, plus Cheng's label-efficient batching) (unverified as a specific paper);
- **(b)** active change-point localisation (e.g. Hayashi, Kawahara and Kashima, "Active change-point
  detection", ACML 2019) (unverified);
- **(c)** probabilistic bisection theory (Horstein; Burnashev–Zigangirov; Waeber–Frazier–Henderson)
  (unverified);
- **(d)** explicit-duration / semi-Markov regime switching and planning (unverified);
- **(e)** seasonal/periodic change detection (unverified).

If (a) attains RLS's rate, or (b)+(c) already give the delayed cross-recurrence localisation bound,
discard C1.

### C1.3 Theorem target (T-RLS)

**Assumptions.** The family `F` above with `S = T/L` boundaries. Fixed delay `d < L`. Per-label
divergence between segment laws is at least `kappa`. A noisy-bisection channel with capacity
constant `C(Delta) > 0`. Constant `X`.

- **(a) Price of post-change evidence (easy direction).** Let `D_post` be the policies whose every
  switch at segment `j` is preceded by at least one *released* label requested inside segment `j`.
  This class includes every detection/restart composition audited by Lane A: SRR e-detectors plus a
  threshold, DAL, CUSUM rollback, scout/confirm, Lau–Tay and Geng-type rules. For every `pi` in
  `D_post`,
  `Regret_F(pi) >= (S-1) * Delta * (d + E[gap to the first in-segment query]) - S*k`.
  An oblivious query rate `r = B/T` gives a gap of order `1/(2r)`.
- **(b) RLS upper bound.**
  `Regret_F(RLS) <= S*k + Delta*S*(C1*sigma + C2*L*rho^{M})
  + Delta*T_cert + c*B + Delta*N_break*(d + n_v/r_v)`,
  where:
  - `M` is the cumulative number of probes, so the bisection error decays geometrically in probes
    shared across boundaries;
  - `T_cert` is the calendar certification time,
    `~ d + log(1/alpha)/kappa` labels at the pre-certification rate, accumulated over good segments;
  - `N_break` counts recurrence breaks.

  The certification cost is paid **once**, not per boundary.
- **(c) Matching lower bound over all policies (target).** Any alpha-feasible policy pays
  `Omega(S*Delta*min(sigma, d))` (boundary jitter that pre-boundary labels cannot resolve, by the
  coupling in K3 restricted to the jitter window). It also pays
  `Omega(log(L/sigma)/C(Delta))` probes and the Lane A certification floor. RLS is then
  minimax-optimal up to constants for `sigma <= d`. Its advantage over `D_post` is
  `Theta(S*Delta*(d + 1/(2r) - C*sigma)_+)`, **linear in the number of recurrences**.
- **(d) Best-of-both-worlds (target).** If recurrence breaks `N_break` times, RLS loses at most
  `O(N_break*Delta*(d + n_v/r_v))` relative to the safe detection composition.
- **Phase transition.** Anticipation pays iff `sigma < d + 1/(2r) + n_det/r`. For geometric dwell,
  `sigma ~ L` and the gain vanishes. This is consistent with Lane A's HMM cells, so it is a
  prediction, not a rescue.

**Baseline class separated:** `D_post`. **Simplest instance:**
- `sigma = 0`;
- `T = 2400`, the E2 monitored horizon;
- `L = 300`, the E2 `burst_iii` default: bursts of length 300 with period 600 and onset uniform on
  `[200, 600]`;
- `d = 20`, `B = 120`, `alpha = 0.05`, `k = 1`.

Bound (a) gives at least `Delta*(20 + ~10)` per boundary over about 7 boundaries for every `D_post`
policy. RLS should pay about `k` per boundary once `(L, phi)` is localised.

**What would falsify T-RLS:**
- the schedule-expert baseline matches RLS's rate;
- the jitter lower bound in (c) is not attainable with delayed probes;
- reviewers reject `D_post` as the comparator class. Lane A's contract itself favours post-change
  evidence, so this is a real risk.

### C1.4 Baselines and a one-day synthetic test

**Baselines.** All get the same `B`, `d`, `c`, `k`, the same alpha and the same harness. All are
learner-side only.
1. Continue (never switch).
2. The safe composition: SRR all-onset e-detector gate, then economic rollback by an e-detector or
   CUSUM on post-promotion labels, with the query rate tuned on dev (Lane A's
   `switching_safe_composition_boundary_v1.md`).
3. A DAL-style calendar adapter (`switching_dal_translation_screen_v1.md`).
4. A scout/confirm responsive query with the same gate (Chandar–Tchamkerten adaptation).
5. Cheng-style label-efficient batched shrinking dartboard with a delay buffer (no alpha gate;
   report its false promotions).
6. **Label-efficient Hedge over periodic schedule experts** on a `(L, phi)` grid with lazy switching.
   This is the killer baseline, and it gets the same gate.
7. Calendar/context-stratified switching (real data only).
8. The evaluator oracle (reference only).

**Platform.** A thin synthetic adapter feeds `PublicEvent`s with constant `x` into `run_monitor_v2`,
which already provides request-time reservation, delay, pending accounting, `Switcher.choose`, net
utility and `null_round` false-promotion counting. Segment plans come from `e2_acquisition_pacing._plan`
with kind `burst_iii`, reinterpreted as candidate-better segments, plus a jitter wrapper.

**Cells:**
- `sigma in {0, d/4, d, L/2}`;
- `d in {2, 20}`;
- `B in {60, 120, 240}`;
- `k in {0.5, 2}` in units of `Delta`;
- a non-recurrent control (E2 `b1`: one late onset);
- a global-null control (mean `-Delta` everywhere, and boundary mean 0).

Use 200 seeds per cell from a **new** dev block registered in `configs/seed_registry.yaml` before any
run (the existing `lane_b_toy_development` block has an overflow history). CPU only, minutes per cell.

**Real smoke (development windows only).** OPSD and Binance through harness v2. Predicted beforehand:
- OPSD: RLS falls back to detection and ties baseline 2. The stratified baseline ties RLS.
- Binance: no promotions by any method.

**Kill criteria (freeze before running):**
- **K-a.** In `sigma in {0, d/4}` with `d = 20`, the paired net-utility gain of RLS over the best of
  baselines 2–6 must have a 95% lower bound `> 0.25*Delta*d*S`. Otherwise discard.
- **K-b.** If baseline 6 reaches at least 90% of RLS's gain over baseline 2 in those cells, RLS
  reduces to experts over schedules. Discard.
- **K-c.** In the `sigma = L/2` and non-recurrent controls, RLS must not lose more than 2 SE to
  baseline 2 (best-of-both-worlds check).
- **K-d.** Null control: the exact one-sided upper bound on false promotion must be `<= alpha`.
- **K-e.** If OPSD dev shows RLS below baseline 2 by more than 2 SE, the fallback is broken. Fix it
  once, then stop.

A tie on real data is **expected**. It means requirement (b) on real data is not met; it does not
mean C1 failed.

### C1.5 Novelty risk: medium-high

- The coupling of anticipatory deployment with boundary-localising acquisition and one-time
  stratified certification is not in any audited source.
- Each ingredient is classical: stratified e-processes, probabilistic bisection, and switching on a
  forecast.
- The theorem's substance would be (b) plus (c) under delay. That is a modest theory contribution
  even if it holds.
- Real-data relevance on the frozen tasks is weak (K4, and OPSD's phase is calendar-visible).

---

## C2. Split-clock switching (SCS): delay-heterogeneous channels

### C2.1 Algorithm sketch

**Changed information structure (required).**
- Each round offers two paid observations of the same paired outcome:
  - a **fast surrogate** `S_t` (delay `d_f`, cost `c_f`, bias `|E[S_t - Z_t | H_t]| <= b`, with
    `b` unknown but calibratable);
  - the **gold** label `Z_t` (delay `d_g > d_f`, cost `c_g`).
- Both channels reveal both policies' losses whatever is deployed. This keeps the decoupling and
  restores a genuine channel choice, unlike K1.
- One pathwise cap on combined cost, reserved at request time.

**State:**
- two pending pipelines;
- the remaining budget;
- a gold-only promotion e-detector (or a bias-robust surrogate e-process betting on `S - b_hat_+`,
  with `b_hat_+` an upper confidence bound from paired calibration);
- a surrogate CUSUM/e-detector for rollback;
- a confidence sequence for `b` from rounds where both channels are bought;
- the deployed action.

**Acquisition:**
- Pre-promotion: gold, plus surrogate scouting.
- Post-promotion: surrogate for rollback, plus a calibration rate `r_cal` of paired buys.
- The channel for each phase is chosen by the delay-information index
  `j* = argmin_j [d_j + n_j(beta)*c_j*T/B_j]`.

**Deployment:**
- Promote only on the gold, or bias-robust, e-detector crossing. This keeps the global
  any-promotion contract.
- Roll back on surrogate evidence. This is economic, with no alpha needed.
- Re-promotion uses fresh gold evidence, with summable alpha or online fallback (Tian–Ramdas).

### C2.2 Why this is not prior art X

See the master table (column C2). Its distinguishing feature is **channel delay heterogeneity
coupled to deployment state**: the fast channel for unconstrained rollback, the slow channel for
alpha-constrained promotion. The closest threats are:
- Prabhu et al. and Huang et al. controlled sensing (channel choice, but immediate observations);
- multi-fidelity best-arm identification (unverified);
- prediction-powered and surrogate-index inference with delayed outcomes (unverified for the
  sequential case; the repo already contains delayed-PPI studies);
- Lau–Tay (sampling-mode costs).

If a delay-adjusted controlled-sensing index already gives the frontier, discard.

### C2.3 Theorem target (T-SCS)

Take recurrent reversals, the K3 coupling, per-label divergences `kappa_f` and `kappa_g`, and bias
`b < Delta/2`.
- **(a)** Every gold-only policy pays at least `(1-beta)*Delta*(d_g + gap_g)` per reversal.
- **(b)** SCS pays at most `Delta*(d_f + n_f(beta)/r_f) + O(calibration)` per reversal.
- **(c)** The state-dependent channel index is optimal among channel-stationary allocations.

The separation is `Theta(S*Delta*(d_g - d_f))` when `kappa_f/c_f` is within a constant of
`kappa_g/c_g`. The baseline class is single-channel and state-independent channel policies. The
simplest instance is `d_f = 1`, `d_g = 20`, `b = 0`, with surrogate noise twice the gold noise, under
E3's post-promotion reversal profile.

**Main falsifier:** (c) may be a one-line Lagrangian/index argument identical to delay-shifted
controlled sensing.

### C2.4 Baselines, test and kill

**Baselines:**
- gold-only safe composition;
- surrogate-only (invalid for promotion; report its false promotions);
- the repo's delayed evidence-directed PPI monitor as a combined-channel baseline;
- a stationary controlled-sensing index policy that never conditions the channel on deployment;
- continue.

**Test.** The synthetic surrogate is the latent score plus extra noise, evaluator-generated, on
E3-style streams. This needs a two-channel extension to harness v2, about half a day.

**Kill:**
- the gain over the stationary index policy has a 95% lower bound `<= 0.25*Delta*(d_g - d_f)` per
  reversal; or
- the PPI baseline matches SCS.

The frozen real tasks have no surrogate channel. A real test needs a **new task spec and freeze**:
for example, OPSD partial-day actual load (A-R3b removed the hour-07 early-information lag), or
Binance sub-hourly klines (fetch permitted by the user). That breaks the "frozen tasks" requirement.

### C2.5 Novelty risk: high

The delay-heterogeneity axis is plausibly under-studied. The mechanism itself, though, is a channel
index plus calibration, and it needs a new data contract.

---

## C3. Harm-budgeted provisional deployment (HBPD): discarded

**Sketch.**
- Replace "no promotion under the null" by the anytime harm budget
  `P(exists t: sum_{s<=t} [l_s(A_s) - l_s(0)] + k*switches > h) <= alpha`. Track it with a
  Horvitz–Thompson confidence sequence on common labels; this is unbiased whatever is deployed,
  which is the decoupling.
- Reserve `d*l_max` for the unobserved pending window.
- Deploy provisionally whenever the slack covers the worst-case unobservable harm plus `2k`.
- Promote permanently only on an alpha-certificate.

**Why discarded.**
1. **Symmetry (K3).** Over `{P+, P-}`, every policy satisfies `R+ + H- = Delta*w`. Provisional
   deployment shifts loss from `P+` to `P-`. Its harm-detection confidence sequence needs the same
   `log(1/alpha)/kappa` labels as certification, so there is no minimax gain. Gains appear only
   under an asymmetric prior or asymmetric `Delta`, where an alpha-gated rule with a larger alpha
   reaches the same operating point.
2. **Contract change.** It violates the repository's G1 risk event: any `0 -> 1` switch under the
   null is a false promotion. Lane A's comparisons would become incommensurable.
3. **Prior art.** Conservative bandits (Wu et al. 2016; Kazerouni et al. 2017; Garcelon et al.
   2020) and anytime-valid canary/regression testing (Lindon et al. 2022, Netflix) (all unverified
   here) already pair a baseline-relative budget with exploration or rollout plus anytime rollback.
   With common labels the "play the baseline to learn it" cost vanishes, which makes HBPD *easier*
   than conservative bandits, not newer.

**Kept as a note.** HBPD answers E3's "certification delay costs utility below the crossover" only
by changing the risk preference. That is a scoping decision for the user, not a method.

---

## Master "why not prior art X" table

One row per route recorded as rejected or established in `budgeted_switching_research_goals.md`,
`switching_novelty_delta_v1.md` and the Lane B documents. Cells say why the candidate is not that
route. "Uses" means the route is credited and embedded, not claimed.

| # | Route / source (status) | C1 RLS | C2 SCS | C3 HBPD (discarded) |
|---|---|---|---|---|
| 1 | Restricted batch certificate, elementary composition (rejected) | Certification is one ingredient; the claim is anticipatory switching | Certificate is gold-only; claim is channel/state coupling | n/a |
| 2 | Yang et al. multi-batched delay reduction | No batching claim; delay enters via the bisection pipeline | No batching claim | n/a |
| 3 | Quanrud–Khashabi delayed updates | Uses ordered release updates; not claimed | Same | Same |
| 4 | Chick–Forster–Pertile delayed one-shot adoption | Repeated recurrent switching; gain comes from forecasting boundaries | Repeated reversals with two channels | One-shot adoption differs; discarded anyway |
| 5 | Established-ingredient reference (Lane A) | Becomes baseline 2 | Gold-only baseline | n/a |
| 6 | Budget–delay–pulse lower bound; Chandar–Tchamkerten Lemma 1 and scout/confirm | Lower bound assumes unforecastable onset; C1 targets forecastable boundaries. Scout/confirm is baseline 4 | Bound is per channel; C2 shrinks `w` via `d_f` | Bound unchanged |
| 7 | Geng–Bayraktar–Lai sampling rights | Geometric-prior single change; C1 is recurrent with forecastable boundaries | Single channel | n/a |
| 8 | One-step VOI with pending labels (rejected) | Not VOI; a bisection plus certification schedule | Index, not VOI | n/a |
| 9 | Threshold-reaching batch rollout (rejected) | Not rollout | Not rollout | n/a |
| 10 | Recurrent two-state information state plus global betting (supporting) | Geometric-dwell HMM is the `sigma ~ L` limit where C1 predicts no gain | Same contract, extra channel | n/a |
| 11 | Fixed reserves; exact Bellman planner | `R_v` reserve is bookkeeping; gain is not from the reserve | Not a reserve claim | n/a |
| 12 | Randomised calibrated tests; risk frontier | Uses a fixed e-process for scalability; randomised gate is an optional upgrade | Same | Changes the risk event |
| 13 | Optimised cohort/test design | Stationary terminal test; C1 is recurrent anticipation | Stationary | n/a |
| 14 | Prudent-Banker; Osogami robust POMDP; risk-budget Bellman (rejected) | Model-light learner, not a robust planner | Not a planner | Harm budget resembles a delay-aware safety threshold; another reason to discard |
| 15 | Movement-compatible channel / transport coupling (rejected) | No query–deployment coupling of marginals | Channel is chosen by deployment state, not marginal movement; must show it is not a reparametrisation | n/a |
| 16 | Causal sequence-form reference (Koller–Pfeffer) | Oracle only for small cells | Same | n/a |
| 17 | Gong–Zhang paid observation (ICML 2026) | Immediate feedback, fixed comparator; no forecastable recurrence | One observation price; no delay heterogeneity | Different risk event |
| 18 | Lau–Tay observation-switching QCD | Single permanent change; ARL | Sampling-mode costs, not delays; closest audited prior for C2 | n/a |
| 19 | Safe-test composition (e-process, predictable schedule, summable alpha) | Uses it (stratified version); it is not the claim | Uses it for gold | Replaced; discarded |
| 20 | Dynamic indicator-switching regret (2609.30556) | Full information, reactive; C1 beats reactive trackers only via forecastable boundaries | Single channel | n/a |
| 21 | Pan et al. iROBD delayed switching costs | Reactive competitive ratio; no recurrence forecasting | No channels | n/a |
| 22 | Current-regime non-identifiability | Respected: an explicit recurrence model plus verification is the declared forecast route | Rollback uses current surrogate evidence | Respected |
| 23 | Cheng et al. hard-budget switching | Becomes baseline 5; fixed comparator | Single channel | n/a |
| 24 | Prabhu et al. controlled sensing | Single stream | **Main threat**: channel choice; C2 differs only via delays coupled to deployment state | n/a |
| 25 | Helmeczi CPOMDP; Wen et al. probability risk | Not a planner | Not a planner | n/a |
| 26 | Noisy delay-budget-safety KL bound | Gives C1's certification floor (embedded in the T-RLS(c) target) | Per-channel version embedded | n/a |
| 27 | Wen–Xia–Yu risk games | Not a game solver | Same | n/a |
| 28 | SRR e-detector all-onset mixture | Baseline 2; C1 replaces onset mixing by forecasting | Gold gate | n/a |
| 29 | Uniform query plus mixture (rejected, inert) | Weak baseline, superseded by 2 | Same | n/a |
| 30 | Reyzin–Saha–Wu costly observations (UAI 2026) | Immediate, fixed expert | Per-round cost; no delay asymmetry | n/a |
| 31 | Li et al. active two-sample testing | IID pool; terminal | Same | n/a |
| 32 | Known-onset LP; randomised alpha spending | References only | Same | n/a |
| 33 | Threshold-and-hold decomposition | C1 attacks its crossing-delay term by forecasting | C2 attacks it via `d_f` | Attacked by risk change; discarded |
| 34 | Unknown-onset mixture KL (non-result) | n/a | n/a | n/a |
| 35 | Huang et al. UCB-CuSum | Channel collapse acknowledged (K1) | Restores a second channel; immediate sensing there | n/a |
| 36 | Ryabchenko capacity with delays | Concurrent-capacity bound, fixed comparator | Single channel | n/a |
| 37 | DAL plus its translation | Becomes baseline 3; restart class is inside `D_post` | Single channel | n/a |
| 38 | Fixed-calendar e-detector bound | Baseline term | Same | n/a |
| 39 | Khonji CC-POMDP FPTAS | Not a planner | Same | n/a |
| 40 | Monotone promotion class (Lovejoy MLR/TP2) | Stratified positive-only bet is monotone, so risk is inherited; not claimed | Same | n/a |
| 41 | RAO*; Vershinin non-homogeneous costs | Not risk search; cost-aware discrimination is not the claim | Vershinin is closest for per-cost channel choice; delays absent there | n/a |
| 42 | Rangi–Franceschetti feedback graphs | Free action-induced feedback | Same | n/a |
| 43 | Ferrari–Zhao–Scaglione finite-horizon sensing | Static; posterior thresholds | Resource selection without delays | n/a |
| 44 | Hardwick–Stout response-adaptive with switching | Allocation switches, not deployment | Same | n/a |
| 45 | Episode composition; adaptive timing showed no value in six HMM cells | Explained by K3 (geometric dwell); C1 predicts a gain only for `sigma << d` | n/a | n/a |
| 46 | Bayraktar–Ludkovski HMM optimal switching | Known-model Markov regimes; C1 is a learner for forecastable (non-geometric) recurrence with paid delayed labels. Must check explicit-duration extensions | n/a | n/a |
| 47 | Li et al. usage-constrained testing; reduction boundary | Stationary one-shot | Expected sensor usage, immediate | n/a |
| 48 | Robust FSC; static null mixtures; FSC risk recursion | Not a compression claim | Same | n/a |
| 49 | Belief-grid compression; posterior alias | `(L, phi)` grid is a learner belief, not a risk state; risk is carried by `W` | n/a | n/a |
| 50 | Banerjee–Liu–How two-threshold control | Reactive thresholds | Single sensor | n/a |
| 51 | Posch–Bauer conditional risk recycling | Optional alpha recycling for re-certification | Same | n/a |
| 52 | Positive-prefix futility; delayed group-sequential designs | Futility is not the claim (and K4 warns about futility-only real-data "wins") | Same | n/a |
| 53 | POSG equivalence; two-law duality | Not a solver | Same | n/a |
| 54 | Managoli–Prabhakaran finite-memory testing | Not a memory claim | Same | n/a |
| 55 | RC-POMDP (Ho et al.) | No risk-budget state | Same | Harm budget as state resembles RC-POMDP admissible cost |
| 56 | Schur–Lago–Fiez two-phase costly bandits | Stationary; C1 is recurrent | Stationary | n/a |
| 57 | Kapoor–Nair Markov state sensing | Sensing reveals the state, single law, no delay; must check whether duration-aware sensing is covered | No delayed channels | n/a |
| 58 | IID delayed terminal count test | Subroutine at most | Same | n/a |
| 59 | Subramanian delayed-POMDP information state | Pending queue is bookkeeping; not claimed | Same | n/a |
| 60 | Alias scaling; paired-copy compact screen | n/a | n/a | n/a |
| 61 | Saha–Ramdas adaptive robust tests | Validity of the predictable stratified bet follows from this kind of result; not claimed | Bias-robust surrogate bet resembles robust LR testing; not claimed | n/a |
| 62 | Adusumilli tests after sequential experiments | Asymptotic power envelope; comparison only | Same | n/a |
| 63 | Lu et al. GAIF; Tian–Ramdas online FWER | Fallback usable for re-certification; not claimed | Same | n/a |
| 64 | Feng et al. SRGP model modification | Approval tests; no forecasting | Same | n/a |
| 65 | Malek et al. sequential MHT allocation | Not multiple candidates | Same | n/a |
| 66 | Ao et al. average-budget allocation | Hard cap; not a knapsack claim | Same | n/a |
| 67 | Reversal budget split; first-promotion decomposition | Respected (K2); C1's gain is pre- and post-promotion timing, not the split | Channel split is by phase; must show it is not a `(B_P, B_R)` split with different prices. **Real risk** | n/a |
| 68 | Lane B: DE-CuSum / on-off / RDE-CUSUM | Statistic-driven on-off; no forecasting | Single channel | n/a |
| 69 | Lane B: DISCERN gating / predictable routing | Disagreement gating used and credited | Same | n/a |
| 70 | Lane B: Zhang–Cheung inventory reserving | Reserve is not the claim | Same | n/a |
| 71 | Lane B W-B1: evidence-responsive SPRT-stop; randomised oblivious mixtures | C1's probes are time-responsive, not evidence-responsive. Must still beat randomised schedule mixtures (baseline 6 covers this) | n/a | n/a |
| 72 | Lane B minimax screening frontier (duplicate of Lane A) | Not a screening frontier | n/a | n/a |
| 73 | Exit ledger: stratification = composition; intensity; anchor; gating; temporal budget = Paper 3 | **Threat**: with a public phase, C1 equals stratification. C1 claims only the latent-phase case | Not stratification | n/a |
| 74 | Gafni; Challenger; Drift2Act; Lindon–Kallus | Reactive tracking / irreversible adoption / window audit / asymptotic CS; none forecasts recurrence | Single channel | Drift2Act-style capped audits relate to harm accounting; discarded anyway |
| 75 | Repo delayed PPI / evidence-directed PPI studies | Not proxy-based | **Threat**: PPI already combines surrogate and gold; C2 must beat it as a baseline | n/a |

---

## Handoff observation for Lane A (not a Lane B candidate; it would duplicate Lane A's active G1 line)

For policies whose promotion event is monotone in the potential tape, Lane A's reduction makes the
worst causal null equal to IID `Ber(1/2)`. The Lagrangian of
`min E_alt[cost] + mu * P_IID(promote)` is then a single POMDP on the hidden state space
`S_alt ∪ {N}`. `N` is absorbing, emits `Ber(1/2)`, has prior mass `mu`, and is charged 1 at the
first promotion. Equivalently, the extra risk-relevant memory is one likelihood-ratio coordinate,
which resolves the posterior-alias counterexample.

There is a caveat. In the emission-MLR order bad < N < good, the lifted transition matrix is **not
TP2**: the minor on rows (bad, N), columns (N, good) equals `-q`. So Lovejoy-type monotonicity of
the lifted optimum is not automatic. This may be why monotonicity held numerically in 576 cells but
fails for signed future values. A proof of when the lifted optimum is monotone would make the oracle
for that class polynomial. This belongs in Lane A's queue.

## Pivot memo (if C1 dies at the Codex screen or K-a/K-b)

The decoupling of information from deployment is what makes the frozen structure decompose:
- action-independent observation leaves acquisition as single-stream timing (K1);
- the absorbing first-promotion risk leaves post-promotion as a single-law POMDP (K2);
- symmetry leaves no minimax room for earlier deployment (K3).

Information structures that could admit a contribution, in rough order of fit to the charter:
1. **Delay-heterogeneous channels** (C2): fast weak versus slow strong labels of the same outcome.
2. **Partially selective labels**: some outcomes are observable only under the deployed policy's
   action (lending or credit style). Deployment then carries information value, which re-couples
   exploration and switching.
3. **Many candidates selected from the same labels** (the Paper 2 question): selection plus
   certification reuse.
4. **Forecastable regime structure without public phase** (C1's family). Its theory may stand alone,
   but it needs a real dataset whose recurrence is latent rather than calendar-visible.

None of these fits the frozen OPSD or Binance contracts without a new task freeze. K4 also implies
that a different real dataset, with per-label SNR high enough to certify within budget, is needed
for any real-data switching win.

**Next step for Lane B:** a Codex methodology screen of C1 alone (and of C2 conditional on the user
accepting a new information structure). Ask specifically:
- whether `D_post` is a legitimate comparator class;
- whether label-efficient Hedge over schedules or active change-point localisation already gives
  T-RLS(b);
- whether K3 and K4 are correct.

No code is written before that screen.
