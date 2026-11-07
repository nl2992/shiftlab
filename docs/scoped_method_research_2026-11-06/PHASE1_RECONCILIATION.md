# Phase 1 — reconcile prior results (2026-11-06)

**Checkout:** `codex/scoped-method-research-results-2026-11-06`; starting recovery checkpoint `b7d5316e`, follow-up regression quarantine `52d13248`.

## Direct verification

| Required observation | Verification and evidence | Status |
|---|---|---|
| E_rb and B2 match on 90 pilot episodes | Re-read 900 policy rows in `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/records.jsonl`; all 30 seed pairs in each of `F3_reversal_800`, `F4_recurrent`, `S_reversal_400` have exactly equal net cost for `E_rb:gated_deployment` and `B2`. | Verified |
| Never-switch beats E_rb in all three | Recomputed mean paired E_rb minus never-switch from those rows: +46.20, +34.53, +26.93, respectively. | Verified |
| Conventional SR/CUSUM has a different guarantee | `scripts/sota_sprint/fam_e.py` identifies the E-SR/E-CUSUM variants as ARL controls and labels their any-false-promotion guarantee `none`; that is incomparable to an anytime P(any false promotion) certificate. E_swcert, by contrast, uses union-bound alpha spending over repeated tests under its iid conditional null. | Verified |
| Direct front-loading plus E_rb was omitted in the earlier pilot | The later direct composition run exists (400 rows), but the manifest points to dirty source snapshot `469ee3c0...+dirty`; its protocol was not committed/checksummed before execution. `ECONOMIC_HEADROOM_DECISION_20261106.md` treats it as a development falsification, not preregistered evidence. | Earlier omission verified; later composition screen is weakly auditable |
| Adaptive-range correction changes prior provenance | `comparator_validity_audit_20261105.md` documents the predictability ordering defect, supersedes pre-fix tables, and directs corrected reruns. `FINAL_ASSESSMENT.md` says 130 runs / 411 policy entries are affected. Corrected tables must be used; superseded numerical results remain historical only. | Verified |
| No independent real-data confirmation of a new repair | `FINAL_ASSESSMENT.md` records one untouched chronological HuffPost test source with simulated 24-hour label release, but no validated frozen repair and no independent multi-source confirmation. The PFA-SR real replay is negative under that feedback contract. | Verified; do not describe that replay as new-method confirmation |

## Phase 2 evidence already available

The frozen synthetic economic matrix (`research/scoped_method/pilots/economic_headroom_matrix_20261106/`) uses fresh seeds and five prospectively specified cells. It compares never-switch; corrected Gated, DISCERN, Xu acquisition-only; E_rb/RMM; E_swcert; the cost-aware but uncertified economic replacement; and conventional E-SR. The run has 1,350 rows, exact cost-identity residual 0, 30 streams/cell, and raw/summary/manifest SHA-256 values recorded below.

| Target cell | Existing evidence | Interpretation |
|---|---|---|
| Worthwhile reversal `F3_reversal_1200` | E_swcert cost 402.34 vs never 378.83; paired +23.51 [14.34, 32.68]. E_rb 404.47 (+25.63 [16.91, 34.36]); RMM 410.77 (+31.93 [21.99, 41.87]). | Current risk-qualified methods do not exploit the economically worthwhile initial advantage well. |
| Same-size unfavorable reversal `F3_reversal_800` | E_swcert +44.25 [33.90,54.61] vs never; E_rb +40.10 [32.63,47.57]. The cost-aware reference is +64.32 [57.66,70.97]. | Adverse reversals impose large cost when deployment persists too long. |
| Conventional restart in target cell | Nominal E-SR costs 360.00 vs never 378.83 (−18.83 [−30.96,−6.71]) on the worthwhile reversal, but promotes on 30/30 null streams at nominal alpha .05. | Economic signal exists, but this operating point is not acceptable on the registered null. |
| Cost-aware reference | `economic_replacement` costs 383.00 vs never 378.83 (+4.17 [−3.44,11.78]) on the worthwhile reversal, but promotes on 28/30 null streams. | Its development economics do not qualify it as a safe feasible solution. |
| Label-scarce delayed persistent cell | E_rb vs Xu acquisition-only: −9.61 [−20.68,+1.46]; E_swcert: −9.38 [−21.19,+2.43]. | Suggestive only; both intervals include zero, with no ≥5-unit supported advantage. |

The oracle diagnostic is evaluator-only and not a feasible comparator. In `F3_reversal_1200`, the expected-oracle cost is about 294.70, so the gap from never-switch is about 84.13; raw per-seed `regret_expected_oracle` is policy-invariant as required. The oracle path is not available to any policy.

PFA-SR's earlier reversal screen is also adverse: it cost 389.67 (+17.90 [9.09,26.71]) on `F3_reversal_1200` and 401.60 (+60.20 [51.40,69.00]) on `F3_reversal_800`, although its development panel had a cross-host confound. It does not close this gap. Later matched-host confirmation did not establish reversal gains.

## Phase decision

The tested environments show an identifiable economic opportunity: oracle and nominal E-SR results indicate achievable savings in `F3_reversal_1200`, while the frozen safe panel does not realize them. They do **not** show that a new method is needed: an already published restart method might close the gap under an operating point that controls false promotion on the registered iid null. The next step is therefore one fixed-alpha independent calibration and, only if it passes, one frozen small evaluation of the existing E-SR method. No new mechanism is proposed yet.

## Source hashes

- Rollback/acquisition pilot: `records.jsonl` `23b7f27637887a6a429c8a23df0116a8c41151fa1415f9c4f1a0077c2c6b924d`; `summary.json` `21f75a9a096e0316370d31cbd867d52ce772b5c86c227129cab84107c1ca38a2`; `manifest.json` `6aa6a74af1ce194201800e1acd039e6b36b7bae698a3841bb65ab0545a871922`.
- Economic matrix: `records.jsonl` `da0624f02e7d1d103cc2278a09caa25d1949fa4f515affa8cd006fee4aef4aff`; `summary.json` `fb2940c1d7bc3717efe2dd1f11ebf9fa6aeb24276717006f50b7295f07f10c99`; `manifest.json` `5e2459ba1a96fa4d61c5bcfe6fb7d7ec43529032500cc16e0d9330d8974ba9b6`.
- Direct frontload+E_rb development screen: `records.jsonl` `a1a83a1de7d101ce6e89d58461715529cb243aea0474618a31dc36a7225a09f1`; `summary.json` `08ffb4ec158640df1a7fb8d3c8a640fff3fa852d0233a204bec4e8b12a50d56d`; `manifest.json` `dc70ee343843432f7130c5019df065b04cbd7d093fee14cbcc15101251dea74b`.
