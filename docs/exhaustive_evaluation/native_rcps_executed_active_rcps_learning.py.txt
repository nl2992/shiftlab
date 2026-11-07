"""Vectorized COCOB optimizer primitive for the active-RCPS adaptation.

Port of author-vendored cocob.py (a67f85d), Copyright (c) 2023 Francesco
Orabona, MIT license; see COCOB_LICENSE.txt. This is known optimizer machinery,
not a new acquisition algorithm. Leading dimensions are independent learners.
"""

import numpy as np


class Cocob:
    def __init__(self, initial, *, alpha=100, eps=1e-8):
        self.value = np.asarray(initial, dtype=float).copy()
        if not np.isfinite(self.value).all() or alpha < 0 or eps <= 0:
            raise ValueError("finite initial values and positive epsilon required")
        self.initial = self.value.copy()
        self.alpha = alpha
        self.scale = np.full_like(self.value, eps)
        self.negative_gradients = np.zeros_like(self.value)
        self.gradient_norm = np.zeros_like(self.value)
        self.reward = np.zeros_like(self.value)

    def step(self, gradient):
        gradient = np.asarray(gradient, dtype=float)
        if gradient.shape != self.value.shape or not np.isfinite(gradient).all():
            raise ValueError("finite gradient matching parameters required")
        self.scale = np.maximum(self.scale, np.abs(gradient))
        self.negative_gradients -= gradient
        self.gradient_norm += np.abs(gradient)
        self.reward = np.maximum(0, self.reward - gradient * (self.value - self.initial))
        denominator = (
            np.maximum(self.gradient_norm + self.scale, self.alpha * self.scale) * self.scale
        )
        self.value = (
            self.initial + (self.reward + self.scale) * self.negative_gradients / denominator
        )
        return self.value
