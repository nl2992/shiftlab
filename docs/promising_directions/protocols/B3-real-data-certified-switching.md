# B3 registered protocol: certified switching on real-world chronological streams

Registered 2026-11-01 before execution, after the admissibility audits (`a2bd14a`). Locked
windows were not read during the audits: the auditors truncated every stream at 60% before
parsing labels.

Status: first real-data evaluation of the B2 candidate. Most streams are unexposed; the two
partly exposed streams are labelled as such.

## Fixed method, no tuning

- **Candidate.** P3b: the disagreement-gated paired e-process with structural zeros and a
  propensity-matched bet cap.
- **Code.** Exactly the implementation in `scripts/promising_directions/b1_certified_switching.py`
  at commit `041bc26`.
- **Parameters.** alpha = 0.05, p_min = 0.05, and B2's betting settings.
- **Rollback.** By the mirrored test, as in B2.
- **Changes allowed.** Only the stream input changes. Real per-event 0/1 losses `l0`, `l1` of the
  frozen pair replace the simulator's draws. No parameter of the candidate may change.

## Streams, frozen pairs, splits

The pairs were selected on dev windows by the audits' pre-stated rule (`15_*.md`, `15b_*.md`).
Training uses train-only preprocessing, exactly as in the archived audit code
(`results/realdata_audit/scripts/`).

| Stream | Source / status | Frozen pair (incumbent \| challenger) | Train / dev / locked rows | Delay d |
|---|---|---|---|---|
| airlines | OpenML 1169, unexposed | LR on first 15% \| HGB on 15–30% | [0, 161814) / [161814, 323629) / [323629, 539383) | 100 |
| weather | Elwell–Polikar, unexposed | LR 0–15% \| HGB 0–30% | [0, 5447) / [5447, 10895) / [10895, 18159) | 1 |
| spam | Katakis, unexposed | LR 0–15% \| LR 15–30% | [0, 2797) / [2797, 5594) / [5594, 9324) | 50 |
| bank | UCI 222, unexposed | LR 0–15% \| LR 15–30% | [0, 12356) / [12356, 24712) / [24712, 41188) | 100 |
| rialto | class 0 vs rest, unexposed | LR 0–15% \| HGB 0–30% | [0, 24675) / [24675, 49350) / [49350, 82250) | 100 |
| elec2 | partly exposed | pair B (`15_*.md`) | audit splits; locked window restricted to rows ≥ 36,250 (unread by earlier work) | 48 |
| criteo click | partly exposed (label-maturity counts only) | pair B, click label (`15_*.md`) | audit splits | 100 |

Notes on the delay column:

- Each delay is the audit's proposed delay, capped at 100 events so that it fits a
  2,000-event episode.
- All delays are imposed. None of these streams has an auditable release contract.

Excluded streams:

- outdoor: no eligible pair.
- noaa: the next-hour label is not point-in-time.
- gas: exposed.
- folktables and WILDS: not event streams.

## Episodes

- Each locked window is divided into K non-overlapping episodes of 2,000 consecutive events.
  K = min(50, floor(L / 2000)), where L is the locked length. Episode i starts at
  `locked_start + i * floor(L / K)`.
- Each episode starts deployed on the incumbent.
- Each episode runs 100 query-randomisation seeds. The seeds are shared across policies, giving
  paired comparisons.
- Primary setting: budget B = 200 labels per episode (10%), c_q = 0.05, c_s = 5.
- Sensitivity settings: c_s = 20, and B = 400.

## Policies

| Policy | Rule | Role |
|---|---|---|
| P0 | Never switch | Deployable |
| P1 | Always challenger (one switch at t = 1) | **Hindsight reference**: choosing it requires knowing that the challenger is better |
| P2 | Incumbent-alarm switching, as in B2 | Deployable. Its nominal is the incumbent's dev error from the audit JSON plus 0.05. |
| P3b | Candidate | — |
| P6 | Fixed-sample paired batch test (rule below) | Deployable |

P6 rule:

- Query disagreements with P3b's pacing until 50 disagreement labels have been released, or the
  budget runs out.
- Run a one-sided exact binomial test at alpha = 0.05 of H0: P(challenger correct |
  disagreement) <= 1/2.
- Promote if H0 is rejected. Never roll back.
- P6's validity assumes exchangeable disagreement outcomes. That assumption is stated, not
  guaranteed.

## Metrics

- **Net cost per episode.** Deployment 0/1 loss + c_q × labels + c_s × switches, averaged over
  seeds.
- **Dataset mean.** The mean of the episode net costs.
- **Paired differences.**
  - K ≥ 5: 95% CI from a bootstrap over episodes (2,000 resamples).
  - K < 5: 95% CI from a seed-level bootstrap, and the result is labelled LOW-POWER.
- **Also reported:**
  - promotions, rollbacks and labels used;
  - headroom capture `(P0 − P3b) / (P0 − min(P0, P1))`, where the denominator is positive;
  - P3b versus P6;
  - P3b versus P1.

## Decision rules (primary setting, fixed now)

**Per dataset.**

- **WIN** requires both of the following:
  - The 95% CI of `P3b − P0` lies entirely below 0.
  - `mean(P3b) <= mean(P2)`.
- **SAFE** requires `mean(P3b) <= mean(P0) + mean P3b query spend + 0.02 × mean(P0)`. This
  means certified switching costs no more than never-switching plus the price of its labels and
  a 2% margin.

**Programme.**

| Outcome | Condition |
|---|---|
| SUCCESS | WIN on at least 3 streams and SAFE on every stream |
| PARTIAL | WIN on 1–2 streams, or SAFE fails on exactly one stream |
| FAIL | Otherwise |

The sensitivity settings are reported but do not change the decision.

## Execution rules

- **Smoke tests use dev windows only.** The locked windows are read once, by the registered
  run.
- **Detached run.** The run is a single detached OS process. It is resumable through
  per-episode JSONL and writes a checkpoint per stream.
- **Failure handling.** A stream that fails is recorded and is not re-tuned.
