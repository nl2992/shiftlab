# B3+ goal: generalisable certified model switching

Branch: `research/b3-generalisation-icml`. Target venue: ICML main track.

Primary research question: can a budgeted sequential certification procedure make better
model-deployment decisions by accounting for the economic value of switching, the remaining
observation budget, and delayed labels?

Datasets held central: **spam**, **rialto**, **weather**. The other four B3 streams
(airlines, bank, elec2, criteo) are retained as safety checks only.

## Phase 0 record (complete, 2026-11-02)

### Reproduction of the original B3 result

Recomputed from `docs/promising_directions/results/b3/summary.json` without rerunning any
policy. Reduction is `(P0 - P3b) / P0` on mean net cost, primary setting (B = 200,
c_q = 0.05, c_s = 5, T = 2000).

| Stream | Episodes | P0 | P3b | Reduction | WIN | SAFE | Episode-level power |
|---|---:|---:|---:|---:|---|---|---|
| spam | 1 | 849.00 | 254.09 | 70.1% | yes | yes | LOW-POWER (seed bootstrap only) |
| rialto | 16 | 202.06 | 103.73 | 48.7% | yes | yes | episode bootstrap |
| weather | 3 | 504.00 | 475.77 | 5.6% | yes | yes | LOW-POWER (seed bootstrap only) |
| airlines | 50 | 776.80 | 781.40 | -0.6% | no | yes | episode bootstrap |
| bank | 8 | 419.38 | 428.19 | -2.1% | no | yes | episode bootstrap |
| elec2 | 4 | 389.50 | 397.58 | -2.1% | no | yes | LOW-POWER |
| criteo | 50 | 693.92 | 699.19 | -0.8% | no | yes | episode bootstrap |

Programme outcome recorded in `summary.json`: SUCCESS (WIN on weather, spam, rialto; no SAFE
failure). The three reported headline figures (70% / 49% / 6%) are confirmed to three
significant figures. The original records are unmodified.

### Stated limitation carried into B3+

Spam contributes **one** locked 2,000-event episode and weather **three**. Their intervals come
from a bootstrap over the 100 query-randomisation seeds, not over episodes, and the saved
summary labels them `low_power: true`. Query-seed replication is not episode-level evidence and
must not be presented as such. **Rialto (16 episodes) is the only properly powered real-data
testbed** and is therefore the principal robustness case, exactly as the B3 protocol states.
B3+ adds the Phase 3.3 shorter-horizon (1,000-event) slices as a robustness diagnostic for spam
and weather; those slices are not independent datasets.

### Test status

`uv run pytest -q tests/promising_directions/test_b3_real_data.py` -> **7 passed**.

The `Params` import failure named in the goal does not reproduce on this branch. `Params` is
defined at `scripts/promising_directions/b1_certified_switching.py:41`, and `b3_real_data.load_b1()`
(line 87) imports b1 pinned at commit `041bc26`, falling back to `git show` when the worktree file
differs. The pinned-source loader is therefore the mechanism that would surface such a failure:
it resolves `Params` from the pinned revision, not from the worktree. No implementation change
was required; nothing was modified to make the suite pass.

### Environment and provenance

- Python 3.12.2 (CPython), dependencies resolved by `uv` from the repository lock.
- Branch point: `e74fdc33`.
- B1 pinned commit for P3b: `041bc26`.
- Cached per-event frozen-pair losses: `docs/promising_directions/results/b3/losses/*.npz`
  (spam, rialto, weather, airlines, bank, elec2, criteo). B3+ reuses these, so no model is
  retrained and the loss streams are bit-identical to B3's.

## Phase progress

- [x] Phase 0 - preserve and reproduce the original B3 result
- [ ] Phase 1 - select the smallest worthwhile extension (candidates A, B, C)
- [ ] Phase 2 - establish methodological originality against P3b, P4, CAMS, Xu et al.
- [ ] Phase 3 - generalisation across S0-S5, alternative pairs, shorter horizons
- [ ] Phase 4 - compact benchmark (P0, P2, P3b, P6, cost-aware threshold comparator)
- [ ] Phase 5 - ablations and mechanism validation
- [ ] Phase 6 - paired statistical analysis at the correct level of uncertainty
- [ ] Phase 7 - ICML manuscript
