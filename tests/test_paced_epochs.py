import numpy as np

from shiftlab.sota_search.paced_epochs import EpochConfig, epoch_configurations, epoch_screen


def test_configuration_alias_removed():
    configs = epoch_configurations()
    assert len(configs) == 504 and len(set(configs)) == 504
    assert all(not (c.pace == "quota" and c.epochs == 1) for c in configs)


def test_epoch_quota_and_delayed_old_labels_do_not_leak():
    s = {
        "loss": np.ones((1, 40)),
        "candidate_loss": np.zeros((1, 40)),
        "score": np.full((1, 40), 0.5),
        "disagree": np.ones((1, 40), bool),
    }
    c = EpochConfig("uniform", "quota", 1, "kelly", 0.75, 4)
    r = epoch_screen(s, [c], frac=1, delay=3, trace=True, switch_cost=100)
    tr = r["trace"]
    q = tr["query"][0, 0]
    for t in range(40):
        assert q[: t + 1].sum() <= 10 * (t // 10 + 1)
    assert np.all(tr["wealth"][0, 0, [10, 11, 12, 20, 21, 22, 30, 31, 32]] == 1)
    assert r["labels"][0, 0] <= 40


def test_no_early_actions_depend_on_hidden_outcome():
    rng = np.random.default_rng(15)
    s = {
        "loss": rng.random((2, 60)),
        "candidate_loss": rng.random((2, 60)),
        "score": rng.random((2, 60)),
        "disagree": rng.random((2, 60)) > 0.5,
    }
    other = {k: v.copy() for k, v in s.items()}
    other["loss"][:, :5] = 1 - s["loss"][:, :5]
    configs = epoch_configurations()[:20]
    a = epoch_screen(s, configs, trace=True)
    b = epoch_screen(other, configs, trace=True)
    for k in ["query", "wealth", "stake"]:
        np.testing.assert_array_equal(a["trace"][k][:, :, :5], b["trace"][k][:, :, :5])
    assert np.all(a["labels"] <= 12)
