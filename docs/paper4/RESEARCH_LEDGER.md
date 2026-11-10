# Paper 4 research ledger

Branch `research/paper4-antitone-frontier-2026-11-09`. `origin/main` at `8af33afe`. Base `f8878053`.
Environment: macOS arm64, Python 3.12.2, scipy 1.18.1 (HiGHS), numpy 2.5.4, uv 0.12.23.
Model routing: Opus 5.5 plans and verifies; Sonnet subagents build. Every build is re-verified on Opus.

## CP1 — setup and record (2026-11-09)

The required reading is present on the branch, except two docs that are on `origin/main`:
`switching_monotone_risk_ccpomdp_reduction_v1.md` (`c07e6f16`) and
`switching_monotone_restriction_counterexample_v1.md` (`8ca9046a`). The failure record has been reconstructed:
- value-sensitive pruning: NO-GO (`../risk_preserving_approx/PAPER4_VALUE_SHIELD_DECISION_V1.md`);
- the inversion-frontier verifier reduces to Krale et al. NeurIPS 2025 (`../risk_preserving_approx/PAPER4_G1_NOVELTY_REDUCTION_V1.md`);
- Candidates A–H in `../risk_preserving_approx/`.

## CP2 — identity audit (§9). NUMERICALLY VERIFIED; PRIOR ART

`scripts/research_risk_approx/check_negative_influence_identity.py` gives three-way exact agreement
(recursion, endpoint-strategy brute force, IID plus premium) on all 276 events. The randomisation
counterexample is 3/4 versus 1/2. Command:
`uv run --no-sync python scripts/research_risk_approx/check_negative_influence_identity.py`.

## CP3 — WP1 structural parameter. STOP for the verifier-centred theorem

Existing artifacts show the exact verifier needs 56 (T=8) and 72 (T=10) product states. The LP carries
3,869 and 13,421 learner variables, and the reference also has 4,973 and 13,790 opponent sequences.
Verification is not the bottleneck. See `theory/01_structural_theorem_audit.md` §3.

## CP4 — PIVOT to Frontier-Cut Generation. Correctness PROVED

The proof is in `theory/01_structural_theorem_audit.md` §4. The protocol was registered before code:
`experiments/protocols/FCG_DEV_PROTOCOL_V1.md`.

## CP5 — FCG v1 development screen. G-correct and G-demo pass; computational advantage absent

Result: `experiments/results/fcg_dev_v1.json`. Builder: Sonnet subagent. Re-verified on Opus.
- `pytest tests/paper4`: 4 passed, re-run independently.
- The final `U` equals the reference's `calibrated_total_cost` exactly (Fraction) on C1–C6. This
  cross-checks two different computations: cutting planes and the full sequence-form LP.
- Anti-persistent cells: the IID optimum has robust risk 1/5. Cuts reach the exact `V*` and beat
  IID+repair by 0.0082 (C2, 8 cuts), 0.0146 (C3, 13 cuts) and 0.0147 (C6, 22 cuts).
- Fresh-process timing at T=8: reference 1.37 s / 1.76 s; FCG 2.80 s / 6.31 s. FCG's build alone
  (2.5–2.7 s) exceeds the reference's whole run.

Builder deviation, accepted after review. Root repair is done in realization space
(`q x_raw + (1-q) x_safe`). The repo's `mix_with_never_promote` is documented for *deterministic*
plans. On stochastic LP policies with activation < 1 it returns a behavioural policy that is not the
intended lottery (C2 raised risk 280952/2779205 > 1/10). Existing callers re-verify exact risk and
evaluate cost directly, so no saved result is invalid. The latent hazard is recorded here. Historical
code is unchanged.

Decision: CONTINUE to the v2 scale screen (`experiments/protocols/FCG_SCALE_PROTOCOL_V2.md`), which
uses a float inner loop with exact certification only at the end, on T=10, d=2.

## CP6 — FCG v2 scale screen (2026-11-10): correct, faster at T=10, but cuts never exercised there

Results:
- `experiments/results/fcg_scale_v2.json` (driver, separate processes);
- `fcg_scale_v2_run1_serialization_failure.json` (preserved: exact L exceeded Python's 4,300-digit
  int-to-string limit after the computation finished);
- `fcg_scale_v2_addendumA_s3.json`. S3 was registered after the S2 premise failed and before it was run.

Re-verified on Opus: `pytest tests/paper4` 6 passed, ruff clean. Every `U` equals the reference exactly,
risk is 1/10, and the gap is at most 4e-14.

FCG-fast against the reference: S1 37.6 s vs 69.5 s; S2 53.8 s vs 71.0 s; S3 44.4 s vs 65.3 s; C6 2.26 s vs 1.93 s.
All T=10 cells were IID-safe, so there were 0 cuts. The speed-up is the Candidate B route, engineered faster.
Reference run-to-run noise is about 20% (S1: 56.7 vs 69.5 s).

Decision: **NO-GO — Prior art** (main track). FCG-fast is retained as an exact certified solver.
See `publication/PUBLICATION_DECISION.md` and `experiments/04_scaling_and_comparators.md`.
