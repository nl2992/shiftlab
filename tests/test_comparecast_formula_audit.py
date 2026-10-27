import numpy as np

from scripts.audit_comparecast_formula import _paper_integral
from shiftlab.dive.comparecast_gamma_mixture import gamma_exponential_log_mixture_paper


def test_gamma_exponential_mixture_is_one_at_zero_sum_and_zero_intrinsic_time():
    result = gamma_exponential_log_mixture_paper([0.0], [0.0], rho=0.7, c=1.4)

    np.testing.assert_allclose(result, [0.0], rtol=0.0, atol=1e-12)


def test_positive_z_formula_matches_independent_integral():
    sums = np.asarray([0.0, 0.3, 1.5])
    intrinsic = np.asarray([0.2, 0.4, 0.7])
    rho, c = 0.7, 1.4
    actual = np.exp(gamma_exponential_log_mixture_paper(sums, intrinsic, rho, c))
    expected = np.asarray(
        [_paper_integral(float(s), float(v), rho, c) for s, v in zip(sums, intrinsic, strict=True)]
    )

    np.testing.assert_allclose(actual, expected, rtol=1e-10, atol=1e-12)


def test_negative_z_branch_is_the_documented_upper_bound():
    sums = np.asarray([-0.9, -1.2])
    intrinsic = np.asarray([0.1, 0.0])
    rho, c = 0.7, 1.4
    actual_bound = np.exp(gamma_exponential_log_mixture_paper(sums, intrinsic, rho, c))
    exact_integral = np.asarray(
        [_paper_integral(float(s), float(v), rho, c) for s, v in zip(sums, intrinsic, strict=True)]
    )

    assert np.all(actual_bound >= exact_integral)
