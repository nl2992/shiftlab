# B2 registered protocol: B1 rerun with a propensity-matched bet cap (single frozen change)

Registered 2026-10-30 after B1 (commit `d2e6574`), before execution. This is development round 2.
The change was motivated by B1's post-hoc diagnostic. A positive result here is therefore *not*
confirmation. It would authorise only a separately registered confirmation on a structurally
distinct generator family.

## Single change relative to B1

- Everything follows `protocols/B1-certified-switching.md` and the B1 implementation
  (`scripts/promising_directions/b1_certified_switching.py` at `d2e6574`).
- The exceptions are listed below.

1. **New policy P3b.** It is P3 with the bet cap `lambda_t in [0, p_t/2]`, where `p_t` is the query
   propensity issued for event `t` (on a disagreement event). B1 used the cap `p_min/2`. The
   nonnegativity of `1 + lambda_t Z_t` still holds, since `|Z_t| <= 1/p_t`, and the
   supermartingale argument of `05_PAIRED_CERTIFICATION_THEORY.md` is unchanged. Rollback
   uses the same cap.
2. **Retained policies.** P0, P1, P2 and P3 run unchanged, with B1's P3 kept as a reference. P2's
   bet cap is checked and reported as follows.
   - If P2's cap is below its own propensity-matched value `rate/2`, P2b is also run with that
     cap. In that case BEST is taken over {P0, P1, P2, P2b}.
   - This keeps the incumbent-alarm baseline equally equipped.
3. **P4.** P4 is dropped, since Q2 is closed by B1.
4. **Seeds.** Seeds are fresh: `--seed-base 20261101`, 500 per cell. The worlds, B, c_s, c_q,
   delay, alpha and p_min are unchanged.

## Decision rule (Q1, unchanged from B1, applied to P3b)

- **POSITIVE.** All of the following hold:
  - P3b reduces the world-averaged mean net cost versus BEST by at least 10%, in every (B, c_s).
  - The paired CI excludes 0 in every (B, c_s).
  - No world is more than 10% worse than BEST in that world.
- **NEGATIVE.** P3b is no better than BEST in at least half the settings.
- **MIXED.** Anything else.

## Validity

The P3b false-promotion frequency in W2 and W4 must be at most alpha, judged by the one-sided
95% Clopper-Pearson bound. The exact-null unit test is repeated with the new cap. It must use a
boundary null (`E[D] = 0`), not only the slack worlds.
