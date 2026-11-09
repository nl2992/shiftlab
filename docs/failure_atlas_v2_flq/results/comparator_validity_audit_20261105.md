# Failure Atlas v2 comparator validity audit (2026-11-05)

## Findings

An independent internal model review identified a predictability defect in
`GatedAdaptiveRange` (`scripts/failure_atlas_v2_flq/strong_hosts.py`). The adapter stored the
event-specific MOPE range after calling the base `request_labels`. The base call can synchronously
flush an unqueried disagreement or an agreement, so those increments used the fallback
`1/p_min`. Queried disagreements normally waited for feedback and used the stored `1/q` range.
For `q > p_min`, the bet set could therefore depend on the current query draw, contrary to the
registered predictable-bet construction.

The base certificate now exposes a hook after the issue-time propensity is computed and before the
query draw, `note_event`, or queue flush. `GatedAdaptiveRange` stores `max(1/q, 2)` for a disagreement
and `2` for an agreement there. Pending ranges are included in `state_dict`/`load_state_dict`.
`tests/test_atlas_v2_qce.py::test_gated_adaptive_range_is_set_before_immediate_flush` covers queried and
unqueried branches at the same q, agreement, an unqueried event blocked behind delayed feedback,
and restoring a pending request from a checkpoint.

The checked-in pre-correction synthetic and real validation tables are archived with a
`superseded_pre_wmaxfix` suffix. The corrected registered seed schedule is being replayed at the
paths in Protocol Amendment 3. Until the reports are regenerated, no numeric claim relying on
`gated_adaptive_range` or `gated_adaptive_range+front` should be treated as current. This replay
reuses previously inspected validation regimes and real streams; it is a code correction, not
independent confirmation.

## Additional comparator fidelity corrections

- The paper links a public author repository for MOPE. The inspected checkout is
  [`n17s/mope`](https://github.com/n17s/mope) at commit
  `a4b8584b622f3a8296932568c520c1bb3e1957f0` (MIT license). The benchmark still uses a paired-loss
  MOPE adapter and has not yet been numerically compared against the repository's native gated
  `K^gd` implementation. The native source is now available for that follow-up; the adapter must
  not be called an author-native gated deployment reproduction.
- The DISCERN Appendix A variance penalty matches the current Waudby-Smith–Ramdas-scaled code:
  `4 * residual^2 * ((-log(1-lambda)-lambda)/4)` equals
  `residual^2 * (-log(1-lambda)-lambda)`. The former docstring incorrectly suggested the printed
  DISCERN formula was uncovered by the cited theorem. The previous local implementation error was
  omitting `/4` while retaining the factor 4, which inflated the penalty fourfold.

## Primary sources

- Karampatziakis, Mineiro & Ramdas, [Off-Policy Confidence Sequences](https://proceedings.mlr.press/v139/karampatziakis21a/karampatziakis21a.pdf), ICML 2021. The paper requires predictable betting parameters; see §3.
- Balachandran, [Pay Only for Disagreement](https://arxiv.org/html/2609.17560v1), Appendix A.
- Waudby-Smith & Ramdas, [Variance-adaptive confidence sequences by betting](https://arxiv.org/abs/2010.09686), Theorem 2.

This is an internal code and source audit, not an external human review or a proof review.
