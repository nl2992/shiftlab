"""Headless plots; metadata.json is the reproducibility sidecar."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot(trace, config, directory):
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for method, frame in trace[trace.seed == config.seeds[0]].groupby("method"):
        error = (frame.target - frame.prediction) ** 2
        axes[0].plot(frame.time, error.rolling(50).mean(), label=method)
        axes[1].plot(frame.time, frame.covered.rolling(80).mean(), label=method)
        axes[2].plot(frame.time, 2 * frame.radius, label=method)
    for ax in axes:
        if config.shift != "none":
            ax.axvline(config.change_at, color="black", ls="--", label="true change")
        ax.legend()
    axes[0].set_ylabel("Squared error (50)")
    axes[1].set_ylabel("Coverage (80)")
    axes[2].set_ylabel("Interval width")
    axes[1].axhline(1 - config.alpha, color="gray", ls=":")
    axes[2].set_xlabel("Prediction time")
    fig.suptitle(f"Paper {config.paper}: {config.shift}; seed {config.seeds[0]}")
    fig.tight_layout()
    fig.savefig(directory / "summary.png", dpi=160)
    fig.savefig(directory / "summary.pdf")
    plt.close(fig)
