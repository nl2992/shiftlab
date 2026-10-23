import numpy as np

from shiftlab.dive.persistence_promotion import (
    PersistencePromotionConfig,
    _persistence_rows,
    _two_phase_decisions,
)


def test_conjunctive_gate_rejects_discovery_only_burst_but_accepts_persistence():
    discovery_only = np.concatenate([np.full(200, 0.8), np.full(200, -0.8)])[None, :]
    discovery, persistence, promoted = _two_phase_decisions(
        discovery_only, discovery_length=200, bound=1.1, alpha=0.05
    )
    assert discovery[0] >= 0
    assert persistence[0] < 0
    assert not promoted[0]

    sustained = np.full((1, 400), 0.5)
    discovery, persistence, promoted = _two_phase_decisions(
        sustained, discovery_length=200, bound=1.1, alpha=0.05
    )
    assert discovery[0] >= 0
    assert persistence[0] >= 0
    assert promoted[0]


def test_persistence_grid_smoke_has_fixed_disjoint_forward_windows():
    config = PersistencePromotionConfig(
        n=1200,
        seeds=3,
        discovery_fractions=(0.5,),
        device="cpu",
    )
    rows = _persistence_rows("benefit_reversal", config=config, scenario_index=0)
    assert len(rows) == 3
    for row in rows:
        assert row["discovery_window_length"] + row["persistence_window_length"] == (
            row["shadow_end_index"] - row["shadow_start_index"]
        )
        if row["promoted"]:
            assert row["shadow_start_index"] <= row["promotion_event_index"]
            assert row["promotion_event_index"] < row["shadow_end_index"]
        assert row["promotion_null"].startswith("discovery phase nonpositive OR")
