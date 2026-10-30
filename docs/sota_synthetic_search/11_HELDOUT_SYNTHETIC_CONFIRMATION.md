# Held-out synthetic confirmation (part 1: G1 held-out pool)

**Frozen before running:** `configs/sota_search/frozen_finalists_v1.json` (committed in the same commit as this preamble). Finalists were selected on the development pool only; the held-out pool is evaluated **once** and nothing is re-tuned afterwards. The held-out pool has different shift magnitudes, onsets and schedules (recurrent, onset 500 and 1100) and fresh seeds (400 per world, seed block 5000).

Held-out worlds: concept recurrent δ=2.5, concept abrupt δ=1.2 (onset 1100), concept gradual δ=2.5 (ramp 400), subgroup recurrent δ=4, `cov_benign` recurrent δ=2.5, `cov_inform` gradual δ=1.5, `prior` abrupt δ=1.5 (onset 1100), null.

Decision rule: see the frozen file. Results are filled below after the single run.
