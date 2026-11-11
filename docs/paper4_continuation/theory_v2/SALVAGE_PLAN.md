# Salvage plan: the price of causal safety in mixing chains (locked before new work)

**Locked:** 2026-11-11, at commit `b9506dd4`, before any work under this plan. Outcomes are main-track only
(`AGENTS.md` publication-outcome rule). Falsified sub-claims are evidence, not findings.

## Why the earlier decision was wrong

The previous target (relative premium bounded away from 0 as B → ∞, analysed at t = 1) tested the label-rich limit
in the one degenerate chain where a single label reveals the whole future. Committed data for mixing chains
(t = 3/4, 9/10) show the relative premium ρΓ = Γ/(C₀ − V*_IID) **flat in the horizon T** at fixed budget, at
0.25–0.63 (see `PUBLICATION_DECISION.md`, "Reopened").

## Candidate main result (two regimes)

Setting: symmetric stationary anti-persistent chain, t01 = t10 = t ∈ (1/2, 1), r = 2t − 1, emissions (e, 1 − e),
prior 1/2, any c, k ≥ 0 in the stated ranges, α ≤ 1/2.

- **S-1 (mixing ⇒ the premium persists).** For odd delay d and an explicit parameter region, there is an explicit
  c(t, e, d, α) > 0 with ρΓ(T, B, α) ≥ c for every horizon T ≥ T₀ and every budget B in the label-scarce range
  B ≤ B̄(α, e, t) (stated explicitly). Proof route: (i) at B = 1, ρΓ is α-free and has a closed form from N1/SP1;
  show it is bounded below uniformly in T. (ii) for general B, lower-bound V*_causal with an explicit adaptive null
  (a dual certificate: the null plays p = 0 where the alternative's next-label probability is ≤ 1/2, as in Lemma A),
  and lower-bound VOI_IID with an explicit IID policy; uniformity in T should come from mixing (information decays
  like r^j, so the problem splits into near-independent windows).
- **S-2 (degenerate contrast).** t = 1: ρΓ → 0 as T → ∞ at fixed B (Thm A), and sup_T ρΓ → 0 as B → ∞ (Thm V).
  These exist; they need an independent review.
- **Interpretation.** The price of causal safety is a constant fraction of the value of information whenever
  information decays (mixing) and labels are scarce. It vanishes only when one label reveals the future (t = 1) or
  labels are abundant (consistent with zero asymptotic exponent gaps for adaptive adversaries).

## Work, owners and compute (≤ 4 concurrent processes; numerics at 2 workers)

| Step | Owner | Output |
|---|---|---|
| P1 Prove S-1: B = 1 uniform-in-T bound first, then general-B lower bound | Opus prover (1 process) | `MIXING_PREMIUM_THEOREM.md`, `scripts/.../wpM_*.py` |
| P2 Independent review of Thm A, Thm V, Lemma A, Prop P | fresh Opus reviewer (1 process) | `REVIEW_GENERAL_B.md` |
| P3 Certified horizon-extension numerics: t ∈ {2/3, 3/4, 9/10}, d ∈ {1, 3}, B ∈ {1, 2, 3, 4}, T up to 16 (B ≤ 2) and 12 (B = 3, 4), α ∈ {1/20, 1/10, 1/4}, c = k = 0 plus k = 1/50 | Sonnet builder (2 workers) | `MIXING_SCALING.md`, `results/wpM_scaling_*.json` |
| P4 Novelty of the two-regime statement (finite-horizon / mixing price of robustness vs asymptotic zero gap) | Opus reviewer with HKUSTDial deep-research | `PRIOR_ART_TWO_REGIME.md` |
| P5 Independent correctness review of whatever P1 proves | fresh Opus reviewer | `REVIEW_MIXING.md` |

## Success criteria (stated now; applied by the lead after P1–P5)

- **GO (main-track theory candidate):** S-1 PROVED for general B in an explicit label-scarce range and an explicit
  open set of t < 1, uniform in T; independent review accepts it (corrections allowed); S-2 accepted by review; P3
  numerics consistent (no certified cell below the proved bound); P4 finds no prior statement of the two-regime
  result.
- **CONDITIONAL GO (one obligation):** S-1 PROVED and reviewed for B = 1 and B = 2 (uniform in T), S-2 reviewed, P3
  shows ρΓ flat in T for B ≤ 4 in all three t values; the single obligation is the general-B lower bound.
- **NO-GO:** P3 shows ρΓ → 0 in T at fixed B for t < 1 (certified decrease beyond T = 12 by more than half in every
  family), or a certified counterexample to S-1 at B = 1 or B = 2, or P4 finds the two-regime result already
  published.
- If none applies cleanly, the lead reports the exact state and the remaining obligation; no outcome is softened.

## Erratum (2026-11-11, after P4; criteria unchanged)

The "Interpretation" line "consistent with zero asymptotic exponent gaps for adaptive adversaries" is withdrawn.
P4 (`PRIOR_ART_TWO_REGIME.md`) read Modak et al. in full: their converses use i.i.d. adversaries with both hypotheses
worst-case convex sets; our alternative is a single fixed hidden-Markov law, for which the adaptive null halves the
exponent on fixed schedules (cf. Lemma A; Grünwald–de Heide–Koolen RIPr). The label-rich vanishing in S-2 is a
t = 1 statement (Thm A/V), not an asymptotic-exponent corollary. P4's novelty conditions for S-1 are added to the
GO criterion's "no prior statement" clause: uniform in T, valid for the adaptive (re-timing) learner, explicit
dependence on r, and not a consequence of first-order controlled-sensing exponents.
