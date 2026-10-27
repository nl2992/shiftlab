import numpy as np

from scripts.evaluate_wilds_pace_gate import (
    _candidate_table,
    fixed_n_mcnemar,
    one_row_per_article,
    pace_gate,
)


def test_pace_uses_only_discordant_pairs_and_stops_at_first_crossing():
    candidate = np.array([True] * 8 + [True, False], dtype=bool)
    incumbent = np.array([False] * 8 + [True, False], dtype=bool)

    result = pace_gate(candidate, incumbent, alpha=0.05, lam=0.5)

    assert result["promoted"] is True
    assert result["evaluated_instances"] == 8
    assert result["discordant_pairs"] == 8
    assert result["candidate_wins"] == 8
    assert result["incumbent_wins"] == 0
    assert np.isclose(result["e_at_stop"], 1.5**8)


def test_pace_does_not_update_wealth_on_concordant_instances():
    result = pace_gate(
        np.array([True, False, True, False]),
        np.array([True, False, False, True]),
    )

    assert result["discordant_pairs"] == 2
    assert result["candidate_wins"] == 1
    assert result["incumbent_wins"] == 1
    assert result["promoted"] is False
    assert np.isclose(result["e_at_stop"], 0.75)


def test_fixed_n_gate_uses_one_sided_exact_binomial_test():
    result = fixed_n_mcnemar(
        np.array([True] * 8 + [True, False]),
        np.array([False] * 8 + [True, False]),
        alpha=0.05,
    )

    assert result["promoted"] is True
    assert result["discordant_pairs"] == 8
    assert result["p_value_one_sided"] == 1 / 256


def test_one_row_per_article_is_unique_and_seed_reproducible():
    articles = np.array([10, 10, 10, 20, 20, 30, 30, 30])
    rows = np.arange(len(articles))

    selected_a = one_row_per_article(rows, articles, np.random.default_rng(7))
    selected_b = one_row_per_article(rows, articles, np.random.default_rng(7))

    np.testing.assert_array_equal(selected_a, selected_b)
    assert len(selected_a) == 3
    assert len(np.unique(articles[selected_a])) == 3


def test_candidate_table_selects_highest_scout_accuracy_with_frozen_tie_break():
    y = np.array([0, 1, 1], dtype=np.int8)
    probabilities = {
        1e-5: np.array([0.1, 0.6, 0.4]),
        1e-4: np.array([0.9, 0.1, 0.4]),
        1e-3: np.array([0.9, 0.1, 0.6]),
    }

    table, selected = _candidate_table(
        probabilities=probabilities,
        targets=y,
        scout_positions=np.array([0, 1, 2]),
    )

    assert len(table) == 15
    assert selected == (1e-5, 0.25)
