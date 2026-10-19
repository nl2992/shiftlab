from collections import Counter

import pytest
import yaml

from shiftlab.data.synthetic.planning import (
    SamplingPlan,
    expand_plan,
    profiles,
    summarize_plan,
)


def test_balanced_reproducible_and_paired():
    plan = SamplingPlan(profiles=7, levels={"d": [2, 16, 64], "severity": [0, 1]}, seeds=[11, 12])
    assert profiles(plan) == profiles(plan)
    for axis in plan.levels:
        counts = Counter(p[axis] for p in profiles(plan))
        assert max(counts.values()) - min(counts.values()) <= 1
    streams = list(expand_plan(plan))
    assert len(streams) == 7 * 2 * 2
    for start in range(0, len(streams), 4):
        block = streams[start : start + 4]
        assert len({identity for identity, _ in block}) == 1
        assert [(c.scenario, c.seed) for _, c in block] == [
            (s, seed) for s in plan.scenarios for seed in plan.seeds
        ]


def test_requested_levels_without_cartesian_expansion():
    with open("configs/data/synthetic/balanced_initial.yaml") as handle:
        plan = SamplingPlan.model_validate(yaml.safe_load(handle))
    report = summarize_plan(plan)
    assert report["profile_count"] == 12
    assert report["stream_count"] == 1440
    assert all(count > 0 for axis in report["coverage"].values() for count in axis.values())
    assert len(list(expand_plan(plan))) == 1440


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seeds": []},
        {"seeds": [-1]},
        {"scenarios": ["unknown"]},
        {"profiles": 1, "levels": {"n": [5000, 20000]}},
        {"levels": {"seed": [42]}},
        {"levels": {"d": [1]}},
    ],
)
def test_reject_invalid_plans(kwargs):
    with pytest.raises(ValueError):
        SamplingPlan(**kwargs)
