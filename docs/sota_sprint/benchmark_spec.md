# SOTA sprint: frozen benchmark specification (Agent E)

Registered 2026-11-03 on branch `research/sota-sprint-24` (from `origin/main` 2171689) before any
sprint run. Code: [scripts/sota_sprint/bench.py](../../scripts/sota_sprint/bench.py).

* Contract: T=2000, hard B=200, c_q=.05, c_s=5, alpha=.05, release-before-act, delay >= 1, common
  simulator `scripts/promising_directions/sota/simulator.py`. J = loss + .05 labels + 5 switches.
* Paired streams: synthetic seed s of regime R = `SeedSequence([seed_base, sha(R), s])`; every policy
  replays the same stream with a private generator.
* Development screening: seed base 2026110501 (unused before), 20 seeds per environment, environments
  from `DEV_ENVS` only (Atlas v2 F0-F9 + sprint additions S_* + budget variants `@B100`, `@B400`).
* Validation (registered later, before any validation run): fresh seed base, 100 paired seeds, the
  Atlas v2 V_* regimes plus new instances; null safety additionally on >= 500 null seeds.
* Null-safety bound: promotion rate <= .0936 on every null regime incl. rho=.8 and rho=.95 Markov
  nulls (Atlas v2 Amendment 2). 20-seed rates are screening diagnostics, not evidence of safety.
* Comparators: `CERTIFIED_PUBLISHED` (strongest certified class, chosen per regime on the same seeds),
  `UNCERTIFIED_PUBLISHED`, internal earlier candidates (QSG, QSG-env8, FLQ, RMM, LRMD, P7s; never
  counted as published SOTA), controls. Author-faithful status per method is in
  `docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md`; every row here is a
  common-contract port unless stated.
* Primary statistic: paired Delta J = J(candidate) - J(comparator), 95% t-interval over seeds.
* Runner/analysis: `scripts/sota_sprint/screen.py`, `scripts/sota_sprint/analyze.py`.
