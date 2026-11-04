# Sprint 2 (A5b × D2 × RMM): frozen specification

Registered on 2026-11-04 on branch `research/sprint2-a5b-d2-rmm`, created from `main` at de9aaaa (PR #14 merged).
The code is in [scripts/sota_sprint/bench2.py](../../scripts/sota_sprint/bench2.py) and
[risk_curves.py](../../scripts/sota_sprint/risk_curves.py).

## Contract and runner

* **Contract (unchanged):** T=2000, hard B=200, c_q=.05, c_s=5, paired streams, common simulator.
* **Runner:** `scripts/sota_sprint/screen.py`. It now has `--alpha` (the nominal level passed to every
  policy), and each record carries its `alpha`.

## Seeds

| use | seed base | size |
|---|---|---|
| Development | 2026110701 | 20 seeds per environment |
| Round-5 evaluation | 2026110801 | ≥ 100 seeds |
| Nulls | 2026110802 | ≥ 1000 seeds |
| Real replays | 2026110803 | — |

Every earlier seed base is development-exposed. The 14 real streams and the twin-null streams are
reused for development, as the brief authorises. New seeds on them measure run-to-run variability only.
They are not independent, unseen data.

## Evaluation tracks

The tracks are independent; historical verdicts are not changed.

* **Track E (economic):** J = loss + .05·labels + 5·switches. There is no risk ceiling.
* **Track R (risk-constrained):** targets R5–R30.
  * Each method's alpha is calibrated on development nulls (`RISK_NULLS`).
  * It is then evaluated on separate seeds over the same nulls and on `RISK_ALTS`.
  * Results are reported as cost–risk curves with a Pareto frontier.
  * These are empirical risk levels, not anytime-valid guarantees.
* **Track V (validity):** each method is scored only against the null it actually tests (`NULL_TESTED`):
  * V1: conditional advantage
  * V2: marginal stationary Markov
  * V3: economic non-improvement

## Candidates and registries

* **Mandatory candidates:** H1–H6, R1–R6, T1–T6 and P1–P6 ([candidates.json](candidates.json)).
* **Workstreams:** WP1 (RMM, real late improvement) and WP2 (dependence and economic validity).
* **Family modules:** `fam_h.py`, `fam_r.py`, `fam_t.py`, `fam_p.py`, `fam_e.py` (WP1) and `fam_f.py` (WP2).
  `registry.py` loads them automatically.
