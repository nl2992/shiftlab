# B2 results notes (development round 2; not confirmatory)

Protocol `protocols/B2-propensity-cap.md`, seed-base 20261101,
500 seeds per cell, 2 workers. Command:
`python scripts/promising_directions/b1_certified_switching.py --b2 --seed-base 20261101 --seeds 500 --workers 2 --out-dir docs/promising_directions/results/b2`

- P3b = P3 with per-event bet cap lambda_t <= q_t/2 (q_t = issued propensity); rollback shares the cap. P4/P4w dropped.
- P2 cap check: kelly_cap = 3.0 vs propensity-matched rate/2 = B/(2T) = 0.05 (B=200), 0.10 (B=400).
  The cap is not lower (it is 30-60x looser), so P2b was not added; BEST is over {P0, P1, P2}.
- B1 reproducibility: default-mode rerun (seed-base 20261031) matches B1 summary.json exactly
  after removing `meta` (created_utc, runtime, repo_head are volatile) and all per_seed arrays bit-for-bit.
  The raw file sha256 cannot equal the registered one because of those meta fields.
- Q1 (mechanical): MIXED. P3b passes all three criteria only in B200_cs5; it misses the 10% bar
  in the other three settings (9.65%, 7.9%, 7.7%) and in B400_cs20 W3 (+14.3%) and W4 (+10.0%) it is more than 10% worse than BEST.
- Validity: P3b (and P3) false-promotion 0/500 in W2 and W4 everywhere (CP95 upper 0.006 <= alpha).
- Selection caveat: development round informed by B1 diagnostic; a positive would not be confirmation.
