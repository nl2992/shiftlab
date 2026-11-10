"""Paired per-stream Delta J with stream-cluster / family-cluster bootstrap."""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("outputs/paper3/transfer")
rng = np.random.default_rng(0)


def boot(vals_by_stream, fam_of, nb=2000):
    """vals: dict stream->delta; returns (stream-mean, ci_stream, family-mean, ci_family)."""
    s = np.array(list(vals_by_stream.values()))
    names = list(vals_by_stream)
    fams = np.array([fam_of[n] for n in names])
    ms = s.mean()
    bs = [s[rng.integers(0, len(s), len(s))].mean() for _ in range(nb)]
    uf = np.unique(fams)
    fm = lambda idx_fams: np.mean([s[fams == f].mean() for f in idx_fams])
    mf = fm(uf)
    bf = []
    for _ in range(nb):
        pick = rng.choice(uf, len(uf))
        # resample families, then streams within each family
        vals = []
        for f in pick:
            x = s[fams == f]
            vals.append(x[rng.integers(0, len(x), len(x))].mean())
        bf.append(np.mean(vals))
    return ms, np.percentile(bs, [2.5, 97.5]), mf, np.percentile(bf, [2.5, 97.5])


def main(kind="real", scope="all", scn="primary"):
    d = pd.read_csv(OUT / "d0d2_results.csv")
    d = d[(d.kind == kind) & (d.scope == scope) & (d.scenario == scn)]
    P = d.pivot(index="stream", columns="method", values="J")
    fam = d.drop_duplicates("stream").set_index("stream").fold.to_dict()
    ex = d.pivot(index="stream", columns="method", values="extra_labels")
    methods = [m for m in P.columns if m not in ("hindsight_oracle", "never_switch")]
    lines = []
    for base in ("per_stream_tuned", "global_fixed"):
        lines.append(
            f"\n### {kind}/{scope}/{scn}: Delta J = J(method) - J({base}); negative = method better\n"
        )
        lines.append(
            "| method | stream-mean dJ [95% stream CI] | % of base J | family-mean dJ [95% family CI] | worst-family dJ | streams worse | extra labels/stream |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for m in methods:
            if m == base:
                continue
            dl = (P[m] - P[base]).to_dict()
            ms, ci, mf, cf = boot(dl, fam)
            pc = 100 * ms / P[base].mean()
            fam_means = pd.Series(dl).groupby(pd.Series(fam)).mean()
            worse = int((np.array(list(dl.values())) > 0).sum())
            lines.append(
                f"| {m} | {ms:+.2f} [{ci[0]:+.2f}, {ci[1]:+.2f}] | {pc:+.2f}% | {mf:+.2f} [{cf[0]:+.2f}, {cf[1]:+.2f}] | {fam_means.max():+.2f} | {worse}/{len(dl)} | {ex[m].mean():.0f} |"
            )
    lines.append(f"\n### mean J per method ({kind}/{scope}/{scn}), equal-stream\n")
    lines.append("| method | mean J | hindsight gap |")
    lines.append("|---|---|---|")
    for m in list(methods) + ["hindsight_oracle", "never_switch"]:
        lines.append(
            f"| {m} | {P[m].mean():.2f} | {P[m].mean() - P['hindsight_oracle'].mean():+.2f} |"
        )
    # per family for key methods
    lines.append(
        "\n### per-family dJ vs per_stream_tuned / vs global_fixed (mean over family streams, [stream bootstrap CI])\n"
    )
    key = [
        "D1_ridge",
        "D2_gbdt",
        "D2_mlp",
        "D2_mlp+ood",
        "D1_ridge+ood",
        "D2_gbdt+ood",
        "knn_meta_cusum_analogue",
        "hier_pool",
        "hedge",
        "global_fixed",
    ]
    lines.append("| family | n | " + " | ".join(key) + " |")
    lines.append("|---|---|" + "---|" * len(key))
    for f in sorted(set(fam.values())):
        sts = [s for s in P.index if fam[s] == f]
        cells = []
        for m in key:
            row = []
            for base in ("per_stream_tuned", "global_fixed"):
                x = (P.loc[sts, m] - P.loc[sts, base]).values
                bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(1000)]
                lo, hi = np.percentile(bs, [2.5, 97.5])
                row.append(f"{x.mean():+.1f}[{lo:+.1f},{hi:+.1f}]")
            cells.append(" / ".join(row))
        lines.append(f"| {f} | {len(sts)} | " + " | ".join(cells) + " |")
    od = d.drop_duplicates("stream")
    lines.append(
        f"\nOOD fallback triggered for {int(od.ood.sum())}/{len(od)} streams: {list(od[od.ood].stream)}"
    )
    return "\n".join(lines)


if __name__ == "__main__":
    out = []
    for kind, scope, scn in [
        ("real", "all", "primary"),
        ("real", "early", "primary"),
        ("real", "all", "shifted"),
        ("synth", "all", "primary"),
    ]:
        out.append(main(kind, scope, scn))
    txt = "\n".join(out)
    (OUT / "analysis.md").write_text(txt, encoding="utf-8")
    print(txt)
