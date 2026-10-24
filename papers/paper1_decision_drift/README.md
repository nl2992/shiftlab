# Paper 1: decision-harm monitoring

The implementation is a decision-loss and drift **baseline study**. The research target is
sequential monitoring of downstream decision harm relative to an explicit reference policy, under
stated feedback, predictability, and dependence assumptions. Generic feature-shift alarms are
sentinels, not proof of harm. The delayed-feedback study now includes standard bounded-cost
e-processes and fixed-start mixtures with independent synthetic calibration and a two-block
factorial confirmation; these are established constructions, not novel algorithms. Their anytime
guarantees require the declared bounded conditional-mean null and feedback filtration, which remain
unverified for real data.

See the [research charter](../../docs/research_charter.md), the protocol, hypotheses, research log,
and implementation status before extending or citing these results. The delayed-feedback protocols
and results are in [the null-calibration/confirmation protocol](../../docs/delayed_null_calibration_protocol.md)
and [the design-grid protocol](../../docs/delayed_feedback_grid_protocol.md).
