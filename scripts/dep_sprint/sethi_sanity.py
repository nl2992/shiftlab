import numpy as np

from shiftlab.dep import sethi

rng = np.random.default_rng(1)
S, T = 500, 2000
for pi in (0.9, 0.6, 0.45, 0.3):
    x = (rng.random((S, T + 1)) < pi).astype(int)
    n = np.zeros((S, 2, 2))
    first = np.full(S, T)
    for t in range(1, T + 1):
        np.add.at(n, (np.arange(S), x[:, t - 1], x[:, t]), 1)
        if t % 10 == 0:
            L = sethi.statistic(n[:, 0, 0], n[:, 0, 1], n[:, 1, 0], n[:, 1, 1], 0.3)
            b = sethi.threshold(n[:, 0].sum(1), n[:, 1].sum(1), 0.05)
            first = np.where((L >= b) & (first == T), t, first)
    print(
        "iid pi",
        pi,
        "reject",
        (first < T).mean(),
        "median stop",
        np.median(first[first < T]) if (first < T).any() else None,
    )
