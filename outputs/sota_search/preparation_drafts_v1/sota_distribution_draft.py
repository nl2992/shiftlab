"""Draft generic-shift comparators, isolated from the running source snapshot.

SOURCE_INSPIRED_BASELINE unless stated otherwise. No harmful-risk interpretation
follows from a generic two-sample alarm. IID permutation calibration is explicitly
unsupported for serially dependent inputs. No publication-wide guarantees claimed.
"""

import numpy as np
from scipy.special import betaln, logsumexp
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from shiftlab.monitoring import rbf_mmd_squared


def samples(reference, current):
    x, y = np.asarray(reference, float), np.asarray(current, float)
    if x.ndim != 2 or y.ndim != 2 or x.shape[1] != y.shape[1] or min(len(x), len(y)) < 4:
        raise ValueError("need compatible sample matrices with at least four rows each")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("samples must be finite")
    return x, y


def permutation_mmd(reference, current, *, gamma, permutations=199, seed=0, independent=True):
    if not independent:
        raise ValueError("IID permutation contract does not support dependent streams")
    x, y = samples(reference, current)
    if type(permutations) is not int or permutations < 1:
        raise ValueError("permutations must be a positive integer")
    observed = rbf_mmd_squared(x, y, gamma)
    pooled = np.concatenate((x, y))
    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(permutations):
        order = rng.permutation(len(pooled))
        statistic = rbf_mmd_squared(pooled[order[:len(x)]], pooled[order[len(x):]], gamma)
        exceedances += statistic >= observed
    return {"statistic": observed, "p_value": (1 + exceedances) / (1 + permutations)}


def random_feature_mmd(reference, current, *, gamma, components=64, permutations=199, seed=0, independent=True):
    """SOURCE_INSPIRED_BASELINE RFF approximation, not a novel sketch method.

    Frequencies/phases are independent of the domain labels; the same feature map
    is used for every permutation. Both transformation and calibration costs must
    count in an eventual S12 runtime comparison.
    """
    if not independent:
        raise ValueError("IID permutation contract does not support dependent streams")
    x, y = samples(reference, current)
    if not np.isfinite(gamma) or gamma <= 0 or type(components) is not int or components < 1:
        raise ValueError("positive bandwidth and feature count required")
    if type(permutations) is not int or permutations < 1:
        raise ValueError("positive permutation count required")
    rng = np.random.default_rng(seed)
    frequencies = rng.normal(0, np.sqrt(2 * gamma), size=(x.shape[1], components))
    phases = rng.uniform(0, 2 * np.pi, size=components)
    features = np.sqrt(2 / components) * np.cos(np.concatenate((x, y)) @ frequencies + phases)

    def statistic(left, right):
        n, m = len(left), len(right)
        a, b = left.sum(axis=0), right.sum(axis=0)
        xx = (a @ a - np.square(left).sum()) / (n * (n - 1))
        yy = (b @ b - np.square(right).sum()) / (m * (m - 1))
        return float(xx + yy - 2 * (a @ b) / (n * m))

    observed = statistic(features[:len(x)], features[len(x):])
    exceedances = 0
    for _ in range(permutations):
        order = rng.permutation(len(features))
        exceedances += statistic(features[order[:len(x)]], features[order[len(x):]]) >= observed
    return {"statistic": observed, "p_value": (1 + exceedances) / (1 + permutations), "components": components}


def c2st(reference, current, *, seed=0, regularization=1.0, nonlinear=False, independent=True):
    if not independent:
        raise ValueError("binomial held-out calibration requires independent samples")
    x, y = samples(reference, current)
    if not np.isfinite(regularization) or regularization <= 0:
        raise ValueError("regularization must be finite and positive")
    # Equal sizes ensure the held-out class probability is exactly one half.
    count = min(len(x), len(y))
    rng = np.random.default_rng(seed)
    x = x[rng.permutation(len(x))[:count]]
    y = y[rng.permutation(len(y))[:count]]
    split = count // 2
    train = np.concatenate((x[:split], y[:split]))
    labels = np.r_[np.zeros(split), np.ones(split)]
    # Preprocessing fitted on training only.
    center, scale = train.mean(axis=0), np.maximum(train.std(axis=0), 1e-8)
    if nonlinear:
        classifier = MLPClassifier(
            hidden_layer_sizes=(16,), alpha=1 / regularization, random_state=seed,
            max_iter=500, early_stopping=False,
        )
    else:
        classifier = LogisticRegression(C=regularization, random_state=seed, max_iter=500)
    classifier.fit((train - center) / scale, labels)
    test = np.concatenate((x[split:], y[split:]))
    target = np.r_[np.zeros(count - split), np.ones(count - split)]
    correct = int((classifier.predict((test - center) / scale) == target).sum())
    # Fixed balanced test counts induce dependence in the binomial correctness
    # indicators under some classifiers. Return accuracy only; permutation of
    # held-out domain labels gives the matched conditional randomization p-value.
    prediction = classifier.predict((test - center) / scale)
    permutations = 199
    exceedances = sum(
        int((prediction == rng.permutation(target)).sum()) >= correct
        for _ in range(permutations)
    )
    return {
        "accuracy": correct / len(target),
        "p_value": (1 + exceedances) / (1 + permutations),
        "train_rows": len(train), "test_rows": len(test),
        "calibration": "heldout_label_randomization_fixed_classifier",
    }


def bbsd(reference_probabilities, current_probabilities, *, independent=True):
    if not independent:
        raise ValueError("KS calibration is restricted to independent rows")
    x, y = samples(reference_probabilities, current_probabilities)
    if np.any((x < 0) | (x > 1)) or np.any((y < 0) | (y > 1)):
        raise ValueError("prediction representations must lie in [0,1]")
    pvalues = [ks_2samp(x[:, j], y[:, j], method="auto").pvalue for j in range(x.shape[1])]
    return {"p_value": min(1.0, len(pvalues) * min(pvalues)), "coordinate_p_values": pvalues}


class PageHinkley:
    """One-sided cumulative centered deviations; empirically calibrated threshold."""

    def __init__(self, *, threshold=5.0, allowance=0.01):
        if threshold <= 0 or allowance < 0 or not np.isfinite([threshold, allowance]).all():
            raise ValueError("invalid threshold or allowance")
        self.threshold, self.allowance = threshold, allowance
        self.count, self.mean, self.total, self.minimum = 0, 0.0, 0.0, 0.0

    def update(self, value):
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("bounded loss required")
        self.count += 1
        self.mean += (value - self.mean) / self.count
        self.total += value - self.mean - self.allowance
        self.minimum = min(self.minimum, self.total)
        return self.total - self.minimum >= self.threshold


class AdaptiveWindow:
    """LOCAL_HEURISTIC exhaustive split Hoeffding window; not river ADWIN.

    Scans every split in a bounded window and drops the oldest segment upon
    a detected mean increase. Delta is per update, not an anytime error budget.
    """

    def __init__(self, *, delta=0.01, minimum=8, maximum=256):
        if not 0 < delta < 1 or minimum < 2 or maximum < 2 * minimum:
            raise ValueError("invalid window settings")
        self.delta, self.minimum, self.maximum = delta, minimum, maximum
        self.values = []

    def update(self, value):
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("bounded loss required")
        self.values.append(float(value))
        self.values = self.values[-self.maximum:]
        n = len(self.values)
        if n < 2 * self.minimum:
            return False
        cumulative = np.cumsum(self.values)
        for split in range(self.minimum, n - self.minimum + 1):
            left = cumulative[split - 1] / split
            right = (cumulative[-1] - cumulative[split - 1]) / (n - split)
            threshold = np.sqrt(0.5 * (1 / split + 1 / (n - split)) * np.log(2 * n / self.delta))
            if right - left > threshold:
                self.values = self.values[split:]
                return True
        return False


class BernoulliBOCPD:
    """Beta-Bernoulli run-length posterior with constant hazard.

    Change is proposed before the current observation. The change branch uses
    the prior predictive, whereas the growth branch uses each run's posterior.
    No sequential frequentist false-alarm guarantee is asserted.
    """

    def __init__(self, *, hazard=0.01, prior_a=1.0, prior_b=1.0):
        if not 0 < hazard < 1 or min(prior_a, prior_b) <= 0:
            raise ValueError("invalid hazard or Beta prior")
        self.hazard, self.prior_a, self.prior_b = hazard, prior_a, prior_b
        self.log_posterior = np.array([0.0])
        self.a, self.b = np.array([prior_a]), np.array([prior_b])

    def update(self, value):
        if value not in (0, 1):
            raise ValueError("Bernoulli BOCPD requires binary observations")
        predictive = betaln(self.a + value, self.b + 1 - value) - betaln(self.a, self.b)
        prior = betaln(self.prior_a + value, self.prior_b + 1 - value) - betaln(self.prior_a, self.prior_b)
        change = np.log(self.hazard) + prior
        growth = self.log_posterior + np.log1p(-self.hazard) + predictive
        posterior = np.r_[change, growth]
        self.log_posterior = posterior - logsumexp(posterior)
        self.a = np.r_[self.prior_a + value, self.a + value]
        self.b = np.r_[self.prior_b + 1 - value, self.b + 1 - value]
        return float(np.exp(self.log_posterior[0]))
