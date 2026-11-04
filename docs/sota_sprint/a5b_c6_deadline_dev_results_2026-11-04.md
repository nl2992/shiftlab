# A5b + C6 deadline-value acquisition: development result

**Status: closed as a current method lead.** This was a 30-seed development pilot, not
validation or confirmation, and it does not establish a novelty or SOTA claim.

## Protocol and provenance

The frozen [protocol](a5b_c6_deadline_dev_protocol_2026-11-04.md) tested the existing C6
deadline-value acquisition controller with A5b's unchanged gap-aware Markov SUI evidence.
It used the same hard delayed-label contract and five policy comparators across eight registered
regimes. The paired development seed block was `[7701000, 7701030)` (30 streams per regime),
for 1,200 policy-stream rows total. No parameter was tuned on this block.

The successful run wrote its manifest and raw rows before the final console summary raised a
Windows `cp1252` `UnicodeEncodeError` while printing the Chinese workspace path. The saved results
are complete: `records.jsonl` has 1,200 rows and 240 unique `(seed, regime, method)` keys. The
runner SHA256 is `90e12317a3d036f77d59f6684e1b0a997d38a5fc4828467b9f05ff6eb7cfb394`, matching
the runner hash in the frozen manifest's `source_hashes`. The protocol SHA256 at execution was
`8e6852ce1bf5055d19afcc86a0e30284d884946d5551fb0b8301a7e9b42f2487`. The output summary records
manifest digest `f447ed2e06f75982cd309e86a7955151e9652d705484ae2ce9f71c9c9544927d`.

Raw, local-only artifacts are under
`outputs/sota_sprint/a5b_c6_deadline_dev_2026-11-04/attempt02/` (`manifest.json`,
`records.jsonl`, `summary.json`, and `summary.md`). The earlier failed development attempt and
its manifest are preserved separately; the seed block was not inspected for outcome metrics
before the interface correction and successful run.

## Registered cost rule

The candidate advances only if it lowers equal-cell mean paired net cost against A5b on the four
delayed/late alternatives, has a paired interval below zero, has no target cell whose upper paired
cost increase exceeds `+0.01` per event, and shows no implementation or null-pattern issue.
Negative deltas favor the candidate.

| Regime | Candidate − A5b net cost [95% paired CI] | Labels (candidate mean) | Promotions (candidate rate) |
|---|---:|---:|---:|
| `F6_delay400_better` | +17.765 [+8.744, +26.786] | 152.6 | 0.500 |
| `S_delay800_better` | +1.272 [−0.273, +2.816] | 192.8 | 0.800 |
| `F1_late_800` | −7.283 [−8.259, −6.308] | 70.3 | 0.067 |
| `V_late_600` | +6.727 [−2.200, +15.653] | 53.8 | 0.000 |

The equal-cell mean paired delta is approximately **+4.620 per event**, so the treatment is
worse overall. Only one of four target cells favors it, and two cells have upper confidence
bounds well above the registered `+0.01` guard. The cost rule fails decisively.

The additional `F9_bursty_better` cell is also unfavorable: `+32.643` `[+19.307, +45.980]`.
Candidate false-promotion frequencies were 0/30 in each of `F0_null`, `F5_dep_null_r8`, and
`F5_dep_null_r95`. These small-sample frequencies are diagnostic only; they are not evidence of
validity. C6 alone is misspecified on the dependent-null cells and had observed promotion rates
0.100 and 0.233 at rho 0.8 and 0.95, respectively.

## Decision

Close this A5b+C6 composition as a method lead and do not tune C6 on these seeds. The unchanged
A5b evidence construction preserves the stated class-scoped guarantee only under its assumptions;
the simulation does not prove that result. C6's acquisition ingredients are existing work, and
this pilot supplies no empirical cost advantage to motivate a validation run. Keep the result as
negative evidence. The broader research goal remains open; prioritize source-to-claim completion
and identification of an admissible real stream with observed release times, as described in the
[research direction checkpoint](research_direction_2026-11-04.md).
