# RPOQ S1: problem statement and fatal-flaw audit

**Branch:** `research/rpoq-s1-fatal-flaw-audit` (cut from `main` at `ec42a2d`)
**Date:** 2026-10-29
**Plan:** [`rpoq_plan_v1.md`](rpoq_plan_v1.md), stage S1 of S1–S6.

| Label | Value |
|---|---|
| Programme | RPOQ: resolved-prefix optimal querying |
| Stage | S1, fatal-flaw audit |
| Work type | Audit and problem statement. No code, no runs, no data touched. |
| Claim level | None. This is a hypothesis check, not a method claim. |
| Evidence base | Repo record only (documents named below). No proof re-derived, no code run. |
| Source status | Hampson–Jennison (2013): [UNVERIFIED-THIS-SESSION]. The repo's audit records a full-manuscript read, but fetching it here failed (doi.org and Wiley are outside the session's network allowlist). Other external sources were not re-read. |
| Decision owner | The user signs off the verdict below. |

## 1. Problem (one page)

Events `t = 1..T`. Before the outcome, the learner sees context `X_t`, chooses a predictable query propensity `q_t ∈ [q_min, 1]` and a bounded proxy `H_t`, then draws an independent query coin `Q_t ~ Bernoulli(q_t)`. The target is the bounded paired decision-cost contrast `Z_t` with `|Z_t|, |H_t| ≤ M`.

- **Increment.** `X_t = H_t + Q_t (Z_t − H_t) / q_t`, with `|X_t| ≤ B_t = M(2/q_t − 1)`.
- **Null.** `E[Z_t | G_t] ≤ 0`, where `G_t` is the full event-time history (the stronger eventwise conditional null, not a running-mean null).
- **Delay.** A queried label for event `t` arrives at `t + D_t`. `D_t` is fixed, independent or outcome-dependent (three cases). The learner updates wealth only through the contiguous resolved prefix.
- **Budget.** Pathwise cap `ΣQ_t ≤ B`, with pending queries counted at issue.
- **Admissible class.** Policies whose `q_t` and `H_t` are measurable with respect to information the learner actually holds at decision time.
- **Open object.** The optimal admissible policy needs an *alternative model* to define power or value. Without one, "optimal" is undefined.

All of this restates [`delayed_event_prefix_validity.md`](delayed_event_prefix_validity.md). Nothing here is new yet.

## 2. Fatal-flaw checks

### Check (i): no low-dimensional structure in the optimal policy — **open, decided at S3**
Cannot be settled by reading. The S3 test (monotone threshold in wealth, budget and pending queue) is the answer. One caution: with a known alternative, this is a Bayesian active sequential test with costly delayed sampling, and a threshold structure there would likely already be known (Naghshvar–Javidi; Chick–Forster–Pertile; Hampson–Jennison). So even a positive S3 may not be a novelty result on its own.

### Check (ii): sufficiency of the statistic under informative delay — **real risk, partly confirmed**
- Under fixed or outcome-independent delay, `(wealth, pending queue, remaining budget)` plus the predictable bet-size inputs is plausibly sufficient for the value function. This is a conjecture to verify at S3, not a result.
- Under outcome-dependent delay, *which labels have or have not arrived* is informative about the alternative. The learner may legitimately use it to choose `q_t` (it is past information), but the e-process ignores it, so the belief state is larger than the e-process state. The compact statistic does not carry over without an argument.
- Consequence: the compact solver is credible for the independent-delay case. For informative delay, plan for a counterexample showing the state must grow.

### Check (iii): prior art already covers the structure — **partly yes, not fully closed**
- **The validity half is already in the repo.** Any policy measurable with respect to held information is `G_t`-predictable, provided the current event's delay is not used. So the "admissibility theorem" of the plan is largely [`delayed_event_prefix_validity.md`](delayed_event_prefix_validity.md). What would be new is the characterisation of the *failure boundary* (counterexamples where the delay signal is used), not the positive result.
- **The optimisation half overlaps** the sources already recorded in `switching_positive_prefix_prior_art_audit_v1.md`: Hampson–Jennison (delayed group-sequential tests with backward-induction optimal design, pending responses and sampling cost), Naghshvar–Javidi (active sequential hypothesis testing by dynamic programming) and Chick–Forster–Pertile (Bayesian delayed sequential experimentation). The repo's primary-text audit says these do not cover the ShiftLab causal conditional null, a hard pathwise cap with hidden pending labels, or a PPI e-process. The repo itself calls those mismatches "obligations, not novelty".
- **No paper found that already contains the exact result** (anytime-valid PPI e-process, continuous predictable `q_t`, bound coupling `B_t = M(2/q_t − 1)`, delayed hard cap, optimal policy). I did not search beyond the repo's recorded audits this session, so this is absence of a known match, not evidence of absence.

## 3. What the delta could be, stated narrowly

The coupling between `q_t` and the increment bound `B_t = M(2/q_t − 1)` makes the growth-rate trade-off in `q_t` explicit and closed-form, which gives a non-myopic problem with delay and a hard cap. The repo's evidence-directed rule is the *myopic* version of this. The candidate delta is therefore: **the non-myopic optimal policy inside the valid class, with a proof of its structure and a measured gap to the myopic and uniform rules.**

This is at best a (b) or (a) result in the user's terms: a structured-special-case or an addition to an existing monitor. It is not a new general algorithm.

## 4. Verdict

**CONTINUE WITH GUARDRAILS, low-to-moderate confidence.** Reasons to continue: no known paper contains the exact combination, the myopic rule has a measured, explained failure (17-point loss at early, strong harm; −0.17-point macro difference, from `delayed_ppi_fixed12_dose_onset_grid_results.md`), and S3 is a cheap decisive test. Reasons for caution: the validity theorem is already in the repo, and the optimisation half overlaps established sequential-design results.

**Re-scoping of S2 (needs sign-off).** Replace "prove admissibility validity" with "catalogue the failure boundary": delay-signal use, selective omission of pending labels, and proxy/action-pair switching, each with a counterexample. The positive validity statement stays a citation of the existing note.

**Abandon trigger.** If a source is found that already gives the optimal policy structure for this problem, name it here and stop (per the plan's ABANDON rule).

## 5. Next step

S3 first, ahead of any S2 write-up: solve the smallest instance exactly (iid contrast, fixed delay, known alternative, `q` on a finite grid, budget `B ≤ 4`) with the existing decomposition solver and check threshold structure. Pre-register the success criterion before running it. This needs your approval because it adds code.
