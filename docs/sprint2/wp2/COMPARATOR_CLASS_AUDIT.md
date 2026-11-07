# WP2 comparator-class audit

**Date:** 2026-11-04. This is a post-run sensitivity; the registered protocol and raw records are preserved.

## Class correction

The historical Panel P lists 11 “certified ports.” They are not 11 published certificate methods. The set consists of the six ports in `bench.CERTIFIED_PUBLISHED` plus the Xu acquisition + ShiftLab-certificate composite, two Choe–Ramdas ports, and two ShiftLab QCE ports. The common-contract implementations are adapters; none should be described as a complete author-native deployment without further fidelity evidence. Xu is an acquisition adapter whose paired-loss test is supplied by ShiftLab. The Choe–Ramdas entries are local ports, not author code. The QCE entries are ShiftLab variants.

The strict sensitivity at `strict_published_20261104/` reruns the registered pooled analyses using exactly the six ports in `bench.CERTIFIED_PUBLISHED`. It retains the other adapters as descriptive rows, excluded from the V1/powered pool. No new experiment was run; this is a post-development reanalysis of the same exposed runs, with same-sample pooling and selection.

## Strict-pool results

- H1a: 4 of 6 strict-pool ports meet the tested dependent-twin promotion condition; the stated threshold is 5, so it fails.
- H2: pooled first-promotion `adv_rest` is 0.0122 [0.0067, 0.0177]; this strict-pool criterion passes.
- H4: the mean-reverting `pi_EI` estimate is 0.4941 [0.4325, 0.5581], below its registered lower-bound target; H4 fails.
- H6a is monotone over the tested horizons at all three delay multipliers; H6b fails its A5b safety condition.

These are conditional/marginal/economic estimands defined by WP2, not theorem guarantees. They do not establish generalization to unseen data or author-native reproduction. See `protocol.md`, `BENCHMARK.md`, and `DECISION_FLAG_AUDIT.md` for the original definitions and implementation audit.

## Reproduction

```sh
uv run python scripts/sota_sprint/wp2_analyze.py --strict-published-dir docs/sprint2/wp2/strict_published_20261104
```
