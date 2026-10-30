import numpy as np

from shiftlab.sota_search import generators as g
from shiftlab.sota_search.db import Registry


def test_three_dimensions_can_disagree():
    _, d_b, p_b, h_b = g.population_effects("cov_benign", 3.0)
    _, d_c, p_c, h_c = g.population_effects("concept", 2.0)
    _, d_i, _, h_i = g.population_effects("cov_inform", 2.0)
    # large discrepancy with no harm; tiny discrepancy with large harm; large discrepancy that lowers cost
    assert d_b[-1] > 0.2 and abs(h_b[-1]) < 0.02 and abs(p_b[-1]) < 0.01
    assert d_c[-1] < 0.01 and h_c[-1] > 2 * g.HARM_THRESHOLD and p_c[-1] > 0.05
    assert d_i[-1] > 0.1 and h_i[-1] < -0.1


def test_null_world_has_no_effect_and_streams_are_reproducible():
    w = g.World(kind="none")
    tr = g.truth(w)
    assert not tr["harmful"].any() and np.allclose(tr["harm"], 0, atol=0.02)
    a, b = g.simulate(w, 5, 1), g.simulate(w, 5, 1)
    assert np.array_equal(a["y"], b["y"]) and a["loss"].max() <= g.FN_COST


def test_empirical_loss_matches_population_harm():
    w = g.World(kind="concept", delta=2.0, shape="abrupt", t0=0, T=1000)
    sim = g.simulate(w, 400, 3)
    base = g.simulate(g.World(kind="none", T=1000), 400, 4)["loss"].mean()
    assert abs((sim["loss"].mean() - base) - g.truth(w)["harm"][-1]) < 0.05


def test_registry_is_append_only_and_validates(tmp_path):
    r = Registry(tmp_path / "r.sqlite")
    rid = r.record("t", candidate_algorithm="x", execution_status="negative", primary_metric=0.1)
    r.record(
        "t", candidate_algorithm="y", execution_status="implementation_defect", failure_reason="bug"
    )
    r.flush()
    assert r.count() == 2 and r.rows(f"run_id='{rid}'")[0]["candidate_algorithm"] == "x"
    for bad in ({"nonsense": 1}, {"execution_status": "great"}):
        try:
            r.record("t", **bad)
        except (KeyError, ValueError):
            continue
        raise AssertionError("schema not enforced")
