# Development comparison: E_rb / RMM vs the matched two-sided e-SR — results

Protocol: [esr_vs_erb_dev_protocol.md](esr_vs_erb_dev_protocol.md), locked in commit `70a84679`
before the run. Machine-readable output: [esr_vs_erb_dev_results.json](esr_vs_erb_dev_results.json).
Raw records (gitignored): `outputs/sota_fidelity/esr_vs_erb_dev/records_{main,null}.jsonl` with
manifests. Main panel: seed base 2026120601, 100 seeds × 8 regimes × 19 policies. Null panel:
2026120602, 1000 seeds × 3 regimes. Evidence status: **development / post-development on exposed
synthetic families; not confirmatory.**

## Verdict under the locked decision rule

**The primary contrast is not favourable to E_rb.** Per-seed mean over 4 reversal regimes × 4 hosts
of J(E_rb:h) − J(two_sided_esr_label_clock): **+1.90, 95% t CI [−1.01, +4.80]**, p = 0.20,
n = 100 seed blocks. The upper limit is >= 0, so by the rule stated before the run, the track-A
statistic is not shown to beat a two-sided e-SR on the label clock. Any track-A claim must now rest
on a component the e-SR lacks, tested directly.

## Secondary contrasts (Holm-adjusted over 4)

| Contrast | Mean ΔJ | 95% CI | Holm p |
|---|---|---|---|
| S1 RMM − e-SR, reversal | +9.40 | [+6.36, +12.44] | 5e-8 |
| S2 RMM − e-SR, late (3 regimes) | −1.41 | [−3.44, +0.62] | 0.34 |
| S3 E_rb − e-SR, late | −1.41 | [−3.44, +0.62] | 0.34 |
| S4 E_rb − e-SR, F0_better | −18.66 | [−23.20, −14.13] | 4e-12 |

S2 and S3 are identical because E_rb and RMM produce identical episodes on every late-regime seed
and host (100/100). E_rb changes only the rollback path, which late regimes do not trigger. This
was checked, not assumed.

## Reading

1. **E_rb's reversal gain over RMM is reproduced, and the matched e-SR gets the same gain.** E_rb
   improves RMM by about 7.5 on reversal (S1 minus primary), consistent with the earlier
   post-development estimate of −6.65. The two-sided e-SR (component at every label, restart at
   switch, alpha/2 per side) gets there without E_rb's extra rollback detector, start grid, gate or
   alpha halving.
2. **The e-SR is not dominant.** On stationary improvement (F0_better), E_rb is cheaper by 18.7:
   the e-SR, at alpha/2 per side, promotes more slowly. On late regimes the difference is not
   resolved. This is a promotion-speed vs rollback trade-off, not a uniform win for either.
3. **On all four reversal regimes, never switching is cheaper than every valid adaptive method**
   (e.g. F3_reversal_800: never-switch 344.1, e-SR 391.9, E_rb:gated 388.4, RMM:gated 398.8). The
   earlier "E_rb reduces reversal cost" statements were relative to RMM, not to the do-nothing
   baseline. Under this contract the transient improvement does not pay for switching plus
   rollback. Any track-A paper needs regimes where reversal follows a long enough beneficial
   period, or must report this honestly.
4. **Null safety.** All valid policies pass the registered bound (Wilson upper <= 0.0936) on
   F0_null, V_null and V_worse at 1000 seeds; the largest rate is rmm:LRMD_k1 at 0.024 (upper 0.035).
   Two-sided e-SR: 0.007 / 0.007 / 0.000. **`esr_arl` is invalid** (promotion rate 1.000 / 0.999 /
   0.846): its low costs in the table come from always switching, and it is excluded from any
   comparison.

## Mean net cost by regime (selected policies; 100 seeds each)

| Policy | F0_better | F1_late_800 | V_late_600 | W_late_1000 | F3_rev_800 | S_rev_400 | V_rev_1000 | W_rev_700 |
|---|---|---|---|---|---|---|---|---|
| never switch | 419.9 | 391.5 | 406.7 | 406.0 | 344.1 | 312.5 | 359.2 | 339.8 |
| two-sided e-SR | 392.7 | 376.9 | 376.1 | 391.5 | 391.9 | 324.7 | 410.3 | 369.8 |
| e-SR, RMM bets, full alpha | 385.2 | 370.2 | 374.7 | 382.1 | 393.3 | 328.0 | 406.0 | 373.0 |
| Shekhar–Ramdas any-excl | 387.8 | 400.5 | 409.4 | 415.0 | 401.8 | 359.1 | 411.4 | 390.0 |
| river Page–Hinkley | 429.9 | 395.8 | 409.0 | 410.7 | 354.1 | 322.5 | 369.2 | 349.8 |
| rmm:LRMD_k1 | 379.4 | 370.1 | 369.5 | 382.9 | 394.0 | 340.9 | 404.8 | 379.3 |
| rmm:gated+RMM | 377.3 | 376.6 | 371.9 | 392.5 | 398.8 | 341.7 | 404.8 | 385.7 |
| E_rb:gated | 377.3 | 376.6 | 371.9 | 392.5 | 388.4 | 338.9 | 395.5 | 377.2 |
| E_rb:SMCS | 370.4 | 374.5 | 369.4 | 393.0 | 381.3 | 347.2 | 392.8 | 379.0 |

Per-regime and per-host contrasts in the JSON are exploratory and unadjusted.

## Assessment: pivot within track A

- **Stop** presenting E_rb's rollback statistic as the contribution: a published-construction e-SR
  matches it on reversal.
- **Continue only** with a directly tested component the e-SR lacks, and only if it pays against
  never-switch on reversal. Candidates: (a) economic gating of rollback/promotion on remaining
  horizon and the switch cost, since every valid method loses to never-switch on reversal;
  (b) faster stationary promotion without losing e-SR's rollback behaviour (the F0_better gap).
- **Track B (late change)** is unaffected by this result and is the stronger next candidate:
  RMM/E_rb vs e-SR is unresolved on late regimes (−1.41 [−3.44, +0.62]).

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel main --out outputs/sota_fidelity/esr_vs_erb_dev --workers 9
uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel null --out outputs/sota_fidelity/esr_vs_erb_dev --workers 9
uv run python scripts/sota_fidelity/esr_vs_erb_dev.py analyze --out outputs/sota_fidelity/esr_vs_erb_dev
```

Code: commit `70a84679` (protocol and runner); worktree clean at run start except gitignored outputs.
