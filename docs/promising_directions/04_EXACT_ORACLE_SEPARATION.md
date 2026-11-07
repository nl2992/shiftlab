# 04 Exact oracle separation (Lane A, gates A1–A2)

Decision: **Lane A closed for a joint-acquisition method claim (registered KILL).** This is a
development kill test on a known-model synthetic grid. It is not a confirmatory study.

## What was tested and why this comparator

Proposition A0 (`03_FORMAL_PROBLEM_AND_INFORMATION_CONTRACT.md` §4) shows the following. With
public randomness, history-adaptive acquisition plus optimal switching is the same policy class
as the joint planner. So the only information-matched separation is the adaptivity gap in
acquisition timing. Registered protocol `protocols/A1-exact-separation.md` (commit `0d03912`,
sha256 `35b0db11…edc64`) compares:

- J: the exact joint planner, `FirstPromotionDecomposedGame`, calibrated total cost.
- C*: the best fixed calendar of at most B query slots with exactly optimised, risk-constrained
  switching, `CalendarOpportunityGame`.

Both use the same exact two-law game: causal-null false-promotion risk at most alpha with
root-mixture calibration, a pathwise budget B, release delay d, and reversible promotion.

Solver: branch `research/risk-preserving-switching-approx-2026-10-29` at
`2bd2e8e41639073c8d22ffb17ef0bcc68111e321`. The runner verified that both pinned files were
clean and recorded their hashes. Runner: `scripts/promising_directions/a1_exact_separation.py`.

## Results (verified by recomputing every gap from the exact rationals in the JSONL)

| Part | Cells | J ≤ C* violations | Cells with gap > 0 | Max relative gap | Location of max |
|---|---|---|---|---|---|
| Sanity | 2 + 3 checks | 0 | — | — | Reproduced 22083523/7812500 and the T8_B4 gap 6744087/781250000 exactly |
| Primary (d=2) | 144/144 | 0 | 8 | 0.3645% (10787546091/2959163041129) | T=8, B=4, transition 1/20, emissions (1/50, 49/50), alpha 1/10, cs 1/10 |
| Secondary (d=1) | 144/144 (one transient MemoryError cell re-run alone; gap 0) | 0 | 15 | 0.8741% | T=8, B=4, same parameters |
| Adversarial (T=6, B=3, d=2, 200 random instances, seed 20261030) | 200/200 | 0 | 0 | 0 | — |

Mechanical decision rule:
- No cell reached g ≥ 0.05 or g ≥ 0.10.
- No (B, d, transition, emission, alpha, cs) slice increased monotonically in T by more than 0.01.
- The rule therefore returns **KILL** for both the primary set and the primary-plus-secondary set.

Wall clock: about 27 minutes on 2 workers.

Artifacts are in `results/a1/`. Their sha256 values:

| File | sha256 |
|---|---|
| sanity.json | `d619ce4a…1d2d` |
| primary.jsonl | `1ddbfae7…6d3d` |
| secondary.jsonl | `bcc66db3…4914` |
| adversarial.jsonl | `ab72d158…afd2` |
| summary.json | `5e121765…a5b2` |

Disclosed deviations:
- Calendars range over slots 1..T−d, which matches the source runner. A slot released after the
  horizon cannot help, and this was checked to equal 1..T at T=6.
- The adversarial emission grid was not fully specified in the protocol. It was fixed to
  {11/20, 3/5, 7/10, 4/5, 9/10, 19/20, 49/50}.
- Outputs are under `docs/` because `results/` is gitignored.

## Interpretation

- Nonzero gaps appear only when B=4, persistence is high (transition 1/20) and the signal is
  near-perfect. This matches the earlier T8_B4 cells. A calendar that may skip slots, combined
  with exact risk-constrained switching, recovers more than 99.1% of the joint value in every
  tractable cell. The X2 result (no risk constraint, at most 1.1%) points the same way.
- A2 theory gate: the gap that exists is the timing adaptivity gap of a known-model POMDP. Its
  existence is explained by standard belief-state DP and the adaptivity-gap literature
  (`02_LITERATURE_AND_NOVELTY_AUDIT.md`). Its size is below the programme's practical threshold.
  A separation theorem for a growing family would need gaps that grow with T. None was observed
  for T = 6..8.

## Limitations (not resolved)

- Exact solves are limited to T ≤ 8. The test does not exclude a gap that grows slowly beyond
  this range, such as one logarithmic in T.
- There is one model family: a two-regime symmetric chain, one challenger, and fixed delay.
- J is an LP optimum whose policy cost was recovered exactly. It is not independently
  dual-certified here, although the source branch certifies T8 d=1 to within 4.8e-12.
- Objective-misaligned acquisition (Proposition A0(iv)) was not tested, because it is a known
  VOI effect.

Per the controller: "IF no nontrivial joint-versus-separable separation survives equal
information, THEN stop the joint-method claim and continue with scoped paired-certification
research." Lane A3, the scalable approximation, is not entered.
