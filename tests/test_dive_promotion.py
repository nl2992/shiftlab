import pytest

from shiftlab.dive.promotion import CandidatePromotionTest, CandidateVersion
from shiftlab.dive.promotion_experiment import (
    PromotionExperimentConfig,
    run_promotion_experiment,
)


def test_candidate_promotion_requires_fresh_paired_evidence_and_spends_alpha():
    version = CandidateVersion("recal-v2", "incumbent-v1", 100, 2)
    test = CandidatePromotionTest(version, alpha_total=0.05, max_event_cost=1.0)
    assert test.alpha_i == pytest.approx(0.05 / 6)
    with pytest.raises(ValueError, match="after training"):
        test.update(event_index=100, incumbent_cost=0.8, candidate_cost=0.4)
    for index in range(101, 500):
        test.update(event_index=index, incumbent_cost=0.9, candidate_cost=0.1)
    assert test.certified


def test_candidate_promotion_rejects_invalid_costs():
    test = CandidatePromotionTest(CandidateVersion("c1", "v1", 0, 1), max_event_cost=1.0)
    with pytest.raises(ValueError, match="candidate_cost"):
        test.update(event_index=1, incumbent_cost=0.5, candidate_cost=1.1)


def test_candidate_promotion_accepts_precommitted_alpha_weight():
    test = CandidatePromotionTest(
        CandidateVersion("weighted", "v1", 0, 1),
        alpha_total=0.05,
        alpha_i=0.01,
    )
    assert test.alpha_i == 0.01

    with pytest.raises(ValueError, match="alpha_i"):
        CandidatePromotionTest(
            CandidateVersion("invalid", "v1", 0, 1),
            alpha_total=0.05,
            alpha_i=0.06,
        )


def test_candidate_certificate_is_absorbing_after_first_threshold_crossing():
    test = CandidatePromotionTest(CandidateVersion("c1", "v1", 0, 1), max_event_cost=1.0)
    crossed_at = None
    for index in range(1, 21):
        test.update(event_index=index, incumbent_cost=1.0, candidate_cost=0.0)
        if test.certified:
            crossed_at = test.certificate_event
            break
    assert crossed_at is not None

    for index in range(crossed_at + 1, crossed_at + 81):
        test.update(event_index=index, incumbent_cost=0.0, candidate_cost=1.0)

    assert not test.process.alarm
    assert test.certified
    assert test.certificate_event == crossed_at


def test_promotion_experiment_writes_reproducible_artifacts(tmp_path):
    run_promotion_experiment(
        PromotionExperimentConfig(n=1000, d=8, seeds=1, device="cpu"), tmp_path
    )
    assert (tmp_path / "metrics/promotion_comparison.parquet").is_file()
    report = (tmp_path / "reports/promotion_comparison.md").read_text()
    assert "95% Wilson" in report
    assert "pointwise expected net gain" in report
    assert (tmp_path / "figures/adaptation_promotion.png").is_file()
