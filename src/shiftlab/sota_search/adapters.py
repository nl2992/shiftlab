"""Streaming core adapters: fixed-bet PPE, block PPRM, and switching controls.

No adapter imports or accepts SyntheticWorld/EvaluatorTruth. Source calibration
contains disclosed labeled source losses, never DGP probabilities. The fixed bet
does not depend on current context, unlike query probabilities and proxy scores.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from shiftlab.dive.delayed_feedback import EventOrderBuffer
from shiftlab.dive.pprm_risk_monitor import (
    PPRMRiskMonitor,
    PredictableReliance,
    prediction_powered_batch_risk,
)
from shiftlab.dive.prediction_powered_evalues import prediction_powered_factor

from .feedback import Feedback, QueryReceipt
from .generators import PublicEvent


@dataclass(frozen=True)
class AdapterConfig:
    track: str = "Q1"
    method: str = "ppe"
    endpoint: str = "decision"
    query: str = "uniform"
    budget_fraction: float = 0.2
    stake_scale: float = 0.8
    window: int = 64
    uniform_mixture: float = 0.5
    margin: float = 0.01
    cusum_threshold: float = 3.0

    def __post_init__(self):
        if self.track not in ("Q1", "Q2", "Q3"):
            raise ValueError("unknown research track")
        if self.method not in (
            "direct",
            "ppe",
            "multiscale",
            "reliable",
            "pprm",
            "pprm_adaptive",
            "cusum",
            "frozen",
            "greedy",
            "hysteresis",
            "certified",
            "reversal",
            "cams_inspired",
        ):
            raise ValueError("unknown adapter method")
        if self.query not in ("uniform", "variance", "robust", "growth", "mixed", "paced"):
            raise ValueError("unknown query rule")
        if self.endpoint not in ("predictive", "decision"):
            raise ValueError("unknown loss endpoint")
        if self.track != "Q1" and self.endpoint != "decision":
            raise ValueError("paired tracks use decision losses")
        if self.method.startswith("pprm") and (self.track != "Q1" or self.query != "uniform"):
            raise ValueError("block PPRM requires Q1 and outcome-independent uniform querying")
        if self.track != "Q3" and self.method in (
            "frozen",
            "greedy",
            "hysteresis",
            "certified",
            "reversal",
            "cams_inspired",
        ):
            raise ValueError("switching methods require Q3")
        numeric = (
            self.budget_fraction,
            self.stake_scale,
            self.uniform_mixture,
            self.margin,
            self.cusum_threshold,
        )
        if not np.isfinite(numeric).all() or any(isinstance(v, bool) for v in numeric):
            raise ValueError("adapter parameters must be finite and non-boolean")
        if not 0 < self.budget_fraction <= 1 or not 0 < self.stake_scale < 1:
            raise ValueError("invalid budget or stake")
        if not 0 <= self.uniform_mixture <= 1 or not 0 <= self.margin < 1:
            raise ValueError("invalid mixture or margin")
        if isinstance(self.window, bool) or not isinstance(self.window, int) or self.window < 4:
            raise ValueError("window must be an integer >= 4")
        if self.cusum_threshold <= 0:
            raise ValueError("CUSUM threshold must be positive")


@dataclass(frozen=True)
class SourceCalibration:
    events: tuple[PublicEvent, ...]
    predictive_losses: np.ndarray
    decision_losses: np.ndarray


def context(event: PublicEvent) -> int:
    return 2 * int(event.features[0] > 0) + int(event.features[2] > 0.5)


class StreamingAdapter:
    """Predictable query/action decisions with event-order evidence resolution."""

    def __init__(self, config: AdapterConfig, source: SourceCalibration, *, horizon: int):
        self.config, self.horizon = config, horizon
        self.alpha = 0.025 if config.track == "Q1" else 0.05
        source_loss = (
            source.predictive_losses if config.endpoint == "predictive" else source.decision_losses
        )
        self.source_upper = min(
            1.0,
            float(source_loss[:, 0].mean() + np.sqrt(np.log(40) / (2 * len(source.events)))),
        )
        self.threshold = self.source_upper + config.margin
        if config.track == "Q1" and self.threshold > 1:
            raise ValueError("source risk upper bound plus margin exceeds bounded risk support")
        self.pairs = 1 if config.track == "Q1" else source_loss.shape[1] - 1
        self.bound = 1.0 if config.track == "Q1" else 1 + config.margin
        self.stake = config.stake_scale * config.budget_fraction / (2 - config.budget_fraction)
        self.floor = 2 * self.stake / (1 + self.stake) + 1e-10
        if self.floor > 1:
            raise ValueError("no feasible PPE query floor")
        stride = config.window
        self.starts = (
            np.arange(0, horizon, stride) if config.method == "multiscale" else np.array([0])
        )
        self.log_capital = np.zeros((self.pairs, len(self.starts)))
        self.buffers = [EventOrderBuffer() for _ in range(self.pairs)]
        self.records: dict[int, dict] = {}
        self.model_means = source.decision_losses.mean(axis=0).copy()
        self.context_means = np.tile(self.model_means, (4, 1))
        self.source_contexts = np.array([context(e) for e in source.events])
        self.context_weights = (np.bincount(self.source_contexts, minlength=4) + 1) / (
            len(source.events) + 4
        )
        self.score_samples = [deque(maxlen=128) for _ in range(4)]
        self.proxy_means = np.zeros(4)
        self.residual_mse = np.full(4, 0.1)
        for k in range(4):
            mask = self.source_contexts == k
            if not mask.any():
                self.score_samples[k].append(0.0)
                continue
            losses = source_loss[mask]
            scores = (
                losses[:, 0] - self.threshold
                if config.track == "Q1"
                else losses[:, 0] - losses[:, 1] - config.margin
            )
            proxies = np.array(
                [
                    self._raw_proxy(e)[0]
                    for e, match in zip(source.events, mask, strict=True)
                    if match
                ]
            )
            self.score_samples[k].extend((scores / self.bound).tolist())
            self.proxy_means[k] = float(proxies.mean())
            self.residual_mse[k] = float(np.mean((scores / self.bound - proxies) ** 2))
            self.context_means[k] = source.decision_losses[mask].mean(axis=0)
        self.q_table = np.full(4, config.budget_fraction)
        self.first_crossing: int | None = None
        self.certified_candidate: int | None = None
        self.current_model = 0
        self.switches = 0
        self.last_switch = -config.window
        self.cusum = 0.0
        self._wall_time = 0
        self.block_next = 0
        self.block_eta: dict[int, float] = {}
        self.pprm = None
        self.reliance = PredictableReliance(window_rounds=8, initial_reliance=1)
        if config.method.startswith("pprm"):
            self.pprm = PPRMRiskMonitor(
                source_upper_bound=self.source_upper,
                tolerance=config.margin,
                max_reliance=1,
                alpha_test=self.alpha,
                lambda_count=32,
                root_iterations=24,
            )

    def _raw_proxy(self, event: PublicEvent) -> np.ndarray:
        values = np.asarray(
            event.proxy_predictive_losses
            if self.config.endpoint == "predictive"
            else event.proxy_decision_losses
        )
        if self.config.track == "Q1":
            return np.array([values[0] - self.threshold]) / self.bound
        return (values[0] - values[1:] - self.config.margin) / self.bound

    def _true_scores(self, feedback: Feedback) -> np.ndarray:
        values = np.asarray(
            feedback.predictive_losses
            if self.config.endpoint == "predictive"
            else feedback.decision_losses
        )
        if self.config.track == "Q1":
            return np.array([values[0] - self.threshold]) / self.bound
        return (values[0] - values[1:] - self.config.margin) / self.bound

    @property
    def log_e_values(self) -> np.ndarray:
        return np.logaddexp.reduce(self.log_capital, axis=1) - np.log(len(self.starts))

    def _apply(self, pair: int, resolved) -> None:
        for item in resolved:
            factor = item.value
            if factor < 0:
                raise ArithmeticError("negative evidence factor")
            log_factor = float(np.log(factor)) if factor > 0 else -np.inf
            self.log_capital[pair, self.starts <= item.event_index] += log_factor
        crossing = self.log_e_values >= np.log(self.pairs / self.alpha)
        if crossing.any() and self.first_crossing is None:
            self.first_crossing = self._wall_time + 1
            self.certified_candidate = int(np.argmax(self.log_e_values)) + 1

    def _allocation(self, rate: float) -> np.ndarray:
        if self.config.query in ("uniform", "paced"):
            return np.full(4, rate)
        scale = np.sqrt(np.maximum(self.residual_mse, 1e-6))

        def normalize(scores):
            lo, hi = 0.0, 1e5
            for _ in range(30):
                mid = (lo + hi) / 2
                if np.dot(self.context_weights, np.clip(mid * scores, self.floor, 1)) < rate:
                    lo = mid
                else:
                    hi = mid
            return np.clip(hi * scores, self.floor, 1)

        variance = normalize(scale)
        if self.config.query == "variance":
            return variance
        if self.config.query == "robust":
            return self.config.uniform_mixture * rate + (1 - self.config.uniform_mixture) * variance
        # Plug-in exact log-factor objective on historical conditional samples.
        # The bet is fixed globally; only queries respond to current context.
        grid = np.linspace(self.floor, 1, 48)
        gains = []
        for k in range(4):
            h = self.proxy_means[k]
            scores = np.asarray(self.score_samples[k])
            corrected = 1 + self.stake * (h + (scores[:, None] - h) / grid)
            if np.any(corrected <= 0):
                raise ArithmeticError("growth model violated the global positivity floor")
            gains.append(
                (1 - grid) * np.log1p(self.stake * h) + grid * np.log(corrected).mean(axis=0)
            )
        gains = np.array(gains)

        def pick(penalty):
            return grid[np.argmax(gains - penalty * grid, axis=1)]

        lo, hi = -100.0, 100.0
        for _ in range(35):
            mid = (lo + hi) / 2
            if np.dot(self.context_weights, pick(mid)) > rate:
                lo = mid
            else:
                hi = mid
        under, over = pick(hi), pick(lo)
        gap = np.dot(self.context_weights, over - under)
        fraction = 0 if gap < 1e-12 else (rate - np.dot(self.context_weights, under)) / gap
        growth = under + np.clip(fraction, 0, 1) * (over - under)
        if self.config.query == "growth":
            return growth
        mixture = self.config.uniform_mixture
        return mixture * rate + (1 - mixture) * (growth + variance) / 2

    def propensity(self, event: PublicEvent, *, remaining: int) -> float:
        self._wall_time = event.index
        if self.config.method == "frozen" or remaining == 0:
            return 0.0
        rate = self.config.budget_fraction
        if self.config.query == "paced":
            rate = remaining / (self.horizon - event.index)
        rate = min(1.0, max(self.floor, rate))
        if event.index % 16 == 0 or self.config.query == "paced":
            self.q_table = self._allocation(rate)
        return float(self.q_table[context(event)])

    def register(self, event: PublicEvent, receipt: QueryReceipt) -> None:
        self._wall_time = event.index
        proxy = self._raw_proxy(event)
        if self.config.method == "direct":
            proxy[:] = 0
        elif self.config.method == "reliable":
            gate = 1 / (1 + 8 * self.residual_mse[context(event)])
            proxy *= gate
        self.records[event.index] = {
            "event": event,
            "receipt": receipt,
            "proxy": proxy,
            "feedback": None,
        }
        if self.pprm is not None:
            block = event.index // self.config.window
            if block not in self.block_eta:
                self.block_eta[block] = self.reliance.choose(
                    labeled_count=1, unlabeled_count=self.config.window - 1
                )
            self._process_blocks()
            return
        for pair, buffer in enumerate(self.buffers):
            factor = (
                None
                if receipt.purchased
                else (1 + self.stake * proxy[pair] if receipt.effective_propensity > 0 else 1.0)
            )
            self._apply(pair, buffer.register(event.index, event.index, factor))

    def receive(self, feedbacks: tuple[Feedback, ...], *, time: int) -> None:
        self._wall_time = time
        for feedback in feedbacks:
            record = self.records[feedback.event_index]
            if record["feedback"] is not None:
                raise ValueError("duplicate feedback")
            record["feedback"] = feedback
            if feedback.missing:
                continue  # Leave evidence unresolved rather than select it away.
            event, proxy = record["event"], record["proxy"]
            scores = self._true_scores(feedback)
            k = context(event)
            step = min(0.5, 1 / self.config.window)
            error = float((scores[0] - proxy[0]) ** 2)
            self.residual_mse[k] = (1 - step) * self.residual_mse[k] + step * error
            self.proxy_means[k] = (1 - step) * self.proxy_means[k] + step * proxy[0]
            self.score_samples[k].append(float(scores[0]))
            costs = np.asarray(feedback.decision_losses)
            self.model_means = (1 - step) * self.model_means + step * costs
            self.context_means[k] = (1 - step) * self.context_means[k] + step * costs
            if self.config.method == "cusum":
                self.cusum = max(0.0, self.cusum + scores[0] - 0.01)
                if self.cusum >= self.config.cusum_threshold and self.first_crossing is None:
                    self.first_crossing = time + 1
            if self.pprm is None:
                for pair, buffer in enumerate(self.buffers):
                    factor = prediction_powered_factor(
                        proxy_factor=1 + self.stake * proxy[pair],
                        queried=True,
                        propensity=feedback.propensity,
                        lower=1 - self.stake,
                        upper=1 + self.stake,
                        observed_factor=1 + self.stake * scores[pair],
                    )
                    # CUSUM is a separate empirically calibrated alarm, not PPE.
                    if self.config.method != "cusum":
                        self._apply(
                            pair,
                            buffer.resolve(feedback.event_index, available_time=time, value=factor),
                        )
        if self.pprm is not None:
            self._process_blocks()

    def _process_blocks(self):
        width = self.config.window
        while (self.block_next + 1) * width - 1 in self.records:
            indices = range(self.block_next * width, (self.block_next + 1) * width)
            rows = [self.records[i] for i in indices]
            queried = [r for r in rows if r["receipt"].purchased]
            if any(r["feedback"] is None or r["feedback"].missing for r in queried):
                break
            unlabeled = [
                r
                for r in rows
                if not r["receipt"].purchased and r["receipt"].effective_propensity > 0
            ]
            if queried and unlabeled:
                field = (
                    "predictive_losses"
                    if self.config.endpoint == "predictive"
                    else "decision_losses"
                )
                proxy_field = "proxy_" + field
                y = np.array([getattr(r["feedback"], field)[0] for r in queried])
                h_l = np.array([getattr(r["event"], proxy_field)[0] for r in queried])
                h_u = np.array([getattr(r["event"], proxy_field)[0] for r in unlabeled])
                eta = (
                    self.block_eta[self.block_next]
                    if self.config.method == "pprm_adaptive"
                    else 1.0
                )
                estimate = prediction_powered_batch_risk(y, h_l, h_u, reliance=eta)
                if self.pprm.update(estimate) and self.first_crossing is None:
                    self.first_crossing = self._wall_time + 1
                self.reliance.update(y, h_l, h_u)
            self.block_next += 1

    def choose_model(self, event: PublicEvent) -> int:
        if self.config.track != "Q3" or self.config.method == "frozen":
            return 0
        method = self.config.method
        desired = self.current_model
        if (
            method in ("certified", "reversal")
            and self.certified_candidate is not None
            and self.switches == 0
        ):
            desired = self.certified_candidate
        elif method in ("greedy", "hysteresis", "cams_inspired"):
            if event.index % self.config.window == 0:
                estimates = (
                    self.context_means[context(event)]
                    if method == "cams_inspired"
                    else self.model_means
                )
                best = int(np.argmin(estimates))
                gain = estimates[self.current_model] - estimates[best]
                margin = (
                    0
                    if method == "greedy"
                    else event.switch_cost / max(1, self.horizon - event.index)
                )
                if gain > margin + (0 if method == "greedy" else self.config.margin):
                    desired = best
        elif method == "reversal" and self.current_model != 0:
            gain = self.model_means[self.current_model] - self.model_means[0]
            if event.index - self.last_switch >= self.config.window and gain > self.config.margin:
                if gain * (self.horizon - event.index) > event.switch_cost:
                    desired = 0
        if desired != self.current_model:
            self.current_model = desired
            self.switches += 1
            self.last_switch = event.index
        return self.current_model
