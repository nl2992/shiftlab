# RPOQ S3: exact structure test, results

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Protocol:** [`rpoq_s3_structure_protocol_v1.md`](rpoq_s3_structure_protocol_v1.md) (criteria frozen before the run).

| Label | Value |
|---|---|
| Work type | Exact dynamic programme, synthetic toy instance, no real data |
| Evidence level | Registered run of the frozen protocol, plus one descriptive follow-up (marked) |
| Claim level | **None.** Registered verdict: structure criterion failed |
| Instance | `T=10` (changed once from 12 for compute, recorded in the protocol), `d=2`, `alpha=0.2`, bet fraction 0.5, grid {0.25, 0.5, 0.75, 1} |
| Artifacts | `outputs/rpoq_s3_structure_v1/results.json`; code `src/shiftlab/dive/rpoq_exact.py`; tests `tests/test_rpoq_exact.py` (6 pass, including exact-vs-independent-simulation agreement) |

## Registered results

| Budget B | Power: optimal | Best constant table | Gap | Neyman/ASI table | Always q=1 | Null alarm (optimal) | Monotone groups |
|---|---|---|---|---|---|---|---|
| 2 | 0.0007 | 0.0002 | +0.0006 | 0.0001 | 0.0000 | 0.0003 | 123/162 (0.76) |
| 3 | 0.0330 | 0.0063 | +0.0266 | 0.0043 | 0.0000 | 0.0094 | 191/304 (0.63) |
| 4 | 0.3684 | 0.3559 | +0.0125 | 0.1201 | 0.3164 | 0.0625 | 251/428 (0.59) |
| 6 | 0.3867 | 0.3559 | +0.0307 | 0.2740 | 0.3164 | 0.0677 | 269/622 (0.43) |

- **C0 (validity): pass.** Exact null alarm probability is at most 0.0677 for the optimal policy and at most 0.0625 for every constant table, against `alpha = 0.2`.
- **C1 (structure): FAIL.** The monotone fraction is 0.43 to 0.76 at every budget, below the 0.90 bar.
- **C2 (adaptivity value): pass at B=3 and B=6** (gaps +0.0266 and +0.0307, bar 0.02). At B=4 the gap is +0.0125.

## Registered decision

Per the protocol's decision table, C0 pass with C1 failing is **"No compact structure. Stop. Keep Options 1 and 2 as separate results."** The adaptive-policy claim is stopped. The pass on C2 does not rescue it, because an optimum with no compact description cannot be used as a policy class.

## Descriptive follow-up (exploratory, not decision-bearing)

Splitting the same groups by context (`t` from 3 to 8, B=4):
- Context B (uninformative proxy): monotone in wealth in 167 of 167 groups.
- Context A (informative proxy): monotone in 0 of 167. The optimal propensity steps down 1.0, 0.75, 0.5, 0.25 as wealth rises, then jumps back to 1.0 above W of about 1.48. That is a banded pattern with several thresholds. It may partly reflect the discrete wealth lattice produced by the binary contrast and fixed-fraction bet, so it is not evidence about continuous-valued problems.

I did not relax C1 after seeing this. A banded-threshold hypothesis would have to be registered as a new protocol on a fresh instance, and it would start as exploratory since it was suggested by these results.

## Other observations (descriptive)

- The Neyman/ASI allocation shape performed badly here (0.120 at B=4 against 0.356 for the best constant table). The best constant table queried always in context A and rarely in B, the opposite of Neyman's ordering. That suggests variance-reduction allocation is the wrong target in this instance, where wealth growth rather than estimator variance drives power. This is one instance, not a general claim.
- Power does not rise from B=4 to B=6 for any constant table, so the budget stops binding for them. The optimal policy still gains (+0.0183).
- Power at B=2 is near zero by construction (two labels cannot reach the threshold), so C2 there is uninformative.

## Limitations

Binary contrast; known alternative; bet fraction fixed rather than optimised; a single parameter set; `T=10`; the alternative law is assumed known to the optimiser, so the optimum is an oracle upper bound and not an implementable policy.

## Consequence for the goal "verify on synthetic and real data, beating known benchmarks"

Not met. The synthetic structure gate failed, so there is no implementable policy to take to a real-data replay. Separately, no real-data replay is possible in this session without a data decision (see the final report: licensed CRSP archives, public repository, external dataset hosts unreachable).
