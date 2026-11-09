"""Out-of-class drift of the envelope e-process (graceful misspecification).

Under a stationary symmetric Markov null (p = 1/2, persistence rho) sampled at event gap g, the
envelope bet with relative edge c declared for rho_bar has expected log-increment
  D(c) = 1/2 [v1 log(1 + c(1-u1)/u1) + (1-v1) log(1-c)] + 1/2 [v0 log(1+c) + (1-v0) log(1-c)],
  v1 = 1/2 + rho^g/2, v0 = 1/2 - rho^g/2, u1 = 1/2 + rho_bar^g/2.
max_c D(c) <= 0 means no component has positive drift: the certificate stays asymptotically safe
even though rho > rho_bar. Prints the largest safe rho for each (rho_bar, g).
"""

import numpy as np

C = np.linspace(1e-3, 0.99, 400)


def drift(rho, rb, g):
    a, b = rho**g, rb**g
    v1, v0, u1 = 0.5 + a / 2, 0.5 - a / 2, 0.5 + b / 2
    d1 = v1 * np.log1p(C * (1 - u1) / u1) + (1 - v1) * np.log1p(-C)
    d0 = v0 * np.log1p(C) + (1 - v0) * np.log1p(-C)
    return float(np.max(0.5 * d1 + 0.5 * d0))


if __name__ == "__main__":
    for rb in (0.0, 0.8, 0.9):
        for g in (5, 10, 15):
            rhos = np.linspace(0, 0.999, 1000)
            safe = [r for r in rhos if drift(r, rb, g) <= 1e-12]
            print(f"rho_bar={rb:.2f} g={g:2d}: max drift at rho=.95: {drift(0.95, rb, g):+.4f}; "
                  f"safe for all rho <= {max(safe):.3f}" if safe else "none")  # fmt: skip
