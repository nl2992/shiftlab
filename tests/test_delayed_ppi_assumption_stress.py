import torch

from shiftlab.dive.delayed_ppi_assumption_stress import (
    BUDGET,
    HORIZON,
    _generate,
    _log_paths,
)


def test_persistent_sign_generator_preserves_exact_stream_hard_cap():
    signs, queries = _generate(8, rho=0.9, seed=42, device=torch.device("cpu"))
    assert signs.shape == (8, HORIZON)
    assert set(torch.unique(signs).tolist()) == {-1.0, 1.0}
    assert int(queries.sum(dim=1).max()) <= BUDGET
    assert int(queries.sum(dim=1).min()) > 0
    empirical_corr = float((signs[:, 1:] * signs[:, :-1]).mean())
    assert empirical_corr > 0.85


def test_informative_delay_changes_wall_clock_but_not_event_time_evidence():
    signs, queries = _generate(4, rho=0.0, seed=123, device=torch.device("cpu"))
    signs.fill_(1.0)
    fixed = _log_paths(signs, queries, delay_profile="fixed12")
    fast = _log_paths(signs, queries, delay_profile="positive_fast")
    slow = _log_paths(signs, queries, delay_profile="positive_slow")
    for left, right in zip(fixed, fast, strict=True):
        assert left[0] == right[0]
        assert torch.equal(left[1], right[1])
        assert torch.equal(left[2], right[2])
    assert any(not torch.equal(fast[i][3], slow[i][3]) for i in range(len(fast)))
