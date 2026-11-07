# Implementation: Han, Huang & Wang adaptive rolling window (ARW)

Status: implemented 2026-11-06. Not yet reviewed by the lead session and not yet in any
comparator pool (no edit to `bench.py` or `suite.py` was made).

## Files

- `scripts/promising_directions/sota/competitors/han_arw.py` (core and adapter)
- `tests/sota_fidelity/test_han_arw.py`
- decision record: `LEDGER.md` (Han entry), `specs/han_rolling_window.md`, `checks/han_rolling_window.md`

## What was built

| Piece | Tier | Source |
|---|---|---|
| `window_statistics`, `variance_proxy`, `bias_proxy`, `arw_window` | T2 | arXiv v2 Eq. (3.1)-(3.8), Alg. 1 / PMLR Eq. (1)-(8), Alg. 1 |
| `pairwise_compare` (two-model tournament = one match) | T2 | Alg. 2 (Alg. 3 with m=2 is one Alg. 2 call) |
| `HanARWDeploymentAdapter` | T3 | label-clock mapping; name it "label-clock ARW, common-contract adapter (T3)", never "Han et al." |

Written from the printed equations only (the ARW repo has no licence). Not compared numerically
against the author code; no paper table was reproduced (Tables 1 to 4 need the author's generators).

Constant sets: `theory` (default; M=b-a, d'=delta/(3t); delta=0.05 nominal) and `paper_experiments`
(M=0, d'=0.1). Tie rule: `paper` (Alg. 2, `<=0` -> incumbent) default; `code` (`<0`).

Adapter: one period per delivered label (B_j=1, delivery order), u = l_incumbent - l_candidate from
`ReleasedFeedback.model_losses` as delivered; pacer = shared `PacedDisagreementAcquisition`; deploy
the candidate iff the selected-window mean gap exceeds `margin` (default 0, the paper has none);
incumbent before any label; memoryless, so it can roll back. No false-promotion guarantee.

## Deviations (full list in the module docstring)

1. Tie rule default = paper (code rule selectable).
2. Negative round-off variance clamped to 0.
3. Window minimiser = smallest k within 1e-12 of the minimum (paper: "any").
4. Local numpy Generator; no tournament, no global reseeding.
5. B_j >= 1 enforced (raises instead of NaN).
6. T3: B_j=1 label clock instead of calendar periods; delayed labels attributed to delivery position
   (estimand lags the true current gap by the delay; the paper has no delay term); pacer-gated
   disagreement queries mean u in {-1,+1} (gap conditional on disagreement; same sign as the
   unconditional gap), propensities ignored (no IPW), so the paper's i.i.d. batch assumption fails;
   optional margin is an extension.

## Findings worth keeping (derived and tested, not from the paper)

- `paper_experiments` on the B_j=1 label clock is degenerate: M=0 gives psi(B=1)=0, so k=1 has
  criterion 0, the global minimum, and the rule always uses the single newest label. The paper's
  experiments had B_j >= 2, so this regime of the constants was never exercised there.
- `theory` on the label clock has a very large lower-order term (8 M log(2/d') / (3(B-1)), M=2):
  window shrinking never triggered in a 60-label stationary or 140-label change test, so it behaves
  as a whole-history mean until much more data. It does shrink on batch data (B_j=100 test).
- With switch cost 5 and no margin the unmodified rule churns (see smoke table).

## Tests

`uv run pytest tests/sota_fidelity/test_han_arw.py -q` -> 20 passed (0.8 s). `uvx ruff check` on both
files: clean. Coverage: hand-computed 3-point window selection for both constant sets (psi, phi,
k_hat), hand-computed positive bias proxy, vectorised vs scalar reference on random batches,
stationary iid -> longest window (>= 47/50 seeds, both sets), abrupt change -> post-change window
(40 seeds), tie rule paper vs code and margin, adapter smoke on null and reversal streams (budget,
delay, determinism, incumbent before first label, future-perturbation causality, state round trip,
promote-then-rollback on a 0.8 -> 0.2 reversal).

## SMOKE table (5 seeds, NOT evidence)

Descriptive smoke only: 5 seeds, contract T=2000, B=200, cq=0.05, cs=5, regime delay 100, stream
seeds from `SeedSequence([20260, hash(regime), seed])`, metrics from `suite.run_metrics`. No
hypotheses, thresholds or tuning were locked; do not cite as a result. `final` = mean final
deployed model (1 = candidate). frac_on_wrong is 0 on F0_null by construction (true gain 0).

| Regime | Policy | net | labels | switches | ever promote | frac on wrong | final |
|---|---|---|---|---|---|---|---|
| F0_null | ARW theory | 472.2 | 200 | 21.4 | 1.0 | 0.000 | 0.6 |
| F0_null | ARW theory, code tie | 481.6 | 200 | 22.8 | 1.0 | 0.000 | 0.8 |
| F0_null | ARW paper_experiments | 820.0 | 199 | 92.6 | 1.0 | 0.000 | 0.6 |
| F0_null | never_switch | 359.6 | 0 | 0.0 | 0.0 | 0.000 | 0.0 |
| F0_better | ARW theory | 415.4 | 200 | 17.4 | 1.0 | 0.116 | 1.0 |
| F0_better | ARW theory, code tie | 400.2 | 199 | 13.8 | 1.0 | 0.108 | 1.0 |
| F0_better | ARW paper_experiments | 798.2 | 200 | 86.6 | 1.0 | 0.413 | 0.6 |
| F0_better | never_switch | 420.0 | 0 | 0.0 | 0.0 | 1.000 | 0.0 |
| F3_reversal_800 | ARW theory | 473.6 | 200 | 19.2 | 1.0 | 0.553 | 0.0 |
| F3_reversal_800 | ARW theory, code tie | 468.4 | 200 | 17.0 | 1.0 | 0.573 | 0.2 |
| F3_reversal_800 | ARW paper_experiments | 755.2 | 200 | 82.0 | 1.0 | 0.366 | 0.4 |
| F3_reversal_800 | never_switch | 346.0 | 0 | 0.0 | 0.0 | 0.400 | 0.0 |

Reading (descriptive): on the null stream every ARW variant promotes in all 5 seeds (as expected for
a rule with no test) and switches 20 to 90 times at cs=5, far above never_switch in net cost; on the
better stream theory-ARW beats never_switch on net (415 vs 420, within seed noise at n=5);
paper_experiments is dominated by churn. Sign of the pattern is consistent with "no false-promotion
guarantee"; magnitude is not established.

Reproduction: the script is at
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/han_smoke.py`
(run `uv run python <path>` from the repo root; it imports `suite.run_metrics`, `regimes`, and
`han_arw`, and edits nothing). Code version: working tree on branch
`claude/shiftlab-methods-strategy-dba13e`, uncommitted.

## Continue / pivot / stop

Continue to review. Before ARW enters a pool: lock a margin policy (or report it unmodified as a
"no switch control" baseline), decide whether `paper_experiments` is reported at all given its
label-clock degeneracy, and keep it labelled T3 with no validity claim.
