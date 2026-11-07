"""B3+ tables, generated only from the JSONL written by b3_plus_experiments.py.

Paired differences are per episode on shared query seeds. CI: bootstrap over episodes when K >= 5,
otherwise over seeds (flagged ``low_power: true``, ``bootstrap_level: "seed"``), mirroring
``b3_real_data.boot_diff``. Repeated query seeds are never treated as independent episodes.
Horizons are never mixed: each (stream, config, horizon) group is analysed on its own.
Headroom capture = (P0 - X) / (P0 - min(P0, P1)), reported when the denominator is positive; P1
is the non-deployable hindsight reference.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "docs/promising_directions/results/b3_plus"
BOOT = 2000
BOOT_SEED = 20261101 + 7
MIN_EPISODES = 5
ORDER = ("P0", "P1", "P2", "P3b", "P6", "PCT", "P4ref", "P7a", "P7b", "P7", "P7c")


# ----------------------------------------------------------------------------- loading
def load_groups(out: Path) -> dict:
    """{(stream, config, horizon): {episode: {variant: stats}}}; variant sets merged per episode."""
    groups: dict = defaultdict(lambda: defaultdict(dict))
    for path in sorted(out.glob("*__*__h*.jsonl")):
        for ln in path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            ep = groups[(r["stream"], r["config"], r["horizon"])][r["episode"]]
            ep.update(r["variants"])  # later rows win
            ep["_meta"] = {k: r[k] for k in ("budget", "cs", "cq", "delay", "n_seeds")}
    return groups


def split_meta(eps: dict):
    meta = next(iter(eps.values()))["_meta"]
    return {e: {k: v for k, v in d.items() if k != "_meta"} for e, d in eps.items()}, meta


# ----------------------------------------------------------------------------- statistics
def boot_diff(per_ep: np.ndarray, per_seed: np.ndarray, rng) -> dict:
    low = len(per_ep) < MIN_EPISODES
    arr = per_seed if low else per_ep
    idx = rng.integers(0, len(arr), size=(BOOT, len(arr)))
    m = arr[idx].mean(1)
    return {
        "mean": float(per_ep.mean()),
        "lo": float(np.percentile(m, 2.5)),
        "hi": float(np.percentile(m, 97.5)),
        "bootstrap_level": "seed" if low else "episode",
        "low_power": bool(low),
    }


def stream_stats(eps: dict, variants: list[str], rng) -> dict:
    """Means, diagnostics and paired differences for one (stream, config, horizon)."""
    order = sorted(eps)
    per_ep = {v: np.array([eps[e][v]["mean_cost"] for e in order]) for v in variants}
    per_seed = {v: np.mean([eps[e][v]["cost_seeds"] for e in order], axis=0) for v in variants}

    def avg(field, v):
        vals = [eps[e][v][field] for e in order]
        vals = [x for x in vals if x is not None]
        return float(np.mean(vals)) if vals else None

    mean = {v: float(per_ep[v].mean()) for v in variants}
    p0, p1 = mean.get("P0"), mean.get("P1")
    denom = (p0 - min(p0, p1)) if p0 is not None and p1 is not None else None
    out = {"episodes": len(order), "variants": {}}
    for v in variants:
        out["variants"][v] = {
            "mean_cost": mean[v],
            "pct_vs_P0": 100 * (mean[v] - p0) / p0 if p0 else None,
            "pct_vs_P3b": 100 * (mean[v] - mean["P3b"]) / mean["P3b"] if "P3b" in mean else None,
            "mean_loss": avg("mean_loss", v),
            "mean_labels": avg("mean_labels", v),
            "mean_switches": avg("mean_switches", v),
            "mean_rollbacks": avg("mean_rollbacks", v),
            "promotion_rate": avg("promotion_rate", v),
            "mean_promotion_time": avg("mean_promotion_time", v),
            "headroom_capture": (p0 - mean[v]) / denom if denom and denom > 0 else None,
        }
    for ref in ("P3b", "P0"):
        if ref not in mean:
            continue
        out[f"paired_vs_{ref}"] = {
            v: boot_diff(per_ep[v] - per_ep[ref], per_seed[v] - per_seed[ref], rng)
            for v in variants
            if v != ref
        }
    out["labels_saved_vs_P3b"] = (
        {
            v: out["variants"]["P3b"]["mean_labels"] - out["variants"][v]["mean_labels"]
            for v in variants
        }
        if "P3b" in mean
        else None
    )
    return out


# ----------------------------------------------------------------------------- formatting
def f(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(d) -> str:
    if d is None:
        return "n/a"
    tag = " (seed-boot, low power)" if d["low_power"] else ""
    return f"{d['mean']:+.2f} [{d['lo']:+.2f}, {d['hi']:+.2f}]{tag}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def suffix(h: int) -> str:
    return "" if h == 2000 else f"_h{h}"


# ----------------------------------------------------------------------------- tables
def build(out: Path, main_variant: str, main_config: str) -> dict:
    groups = load_groups(out)
    if not groups:
        raise SystemExit(f"no B3+ JSONL found under {out}")
    rng = np.random.default_rng(BOOT_SEED)
    stats: dict = {}
    for key in sorted(groups):
        eps, meta = split_meta(groups[key])
        variants = [v for v in ORDER if all(v in d for d in eps.values())]
        stats[key] = {"meta": meta, "stats": stream_stats(eps, variants, rng)}
    tables = out / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    written = []
    for h in sorted({k[2] for k in stats}):
        sfx = suffix(h)
        sel = {k[0]: v for k, v in stats.items() if k[1] == main_config and k[2] == h}
        # main results
        main_rows, main_json = [], {}
        for s, v in sel.items():
            st = v["stats"]
            vv = st["variants"]
            has = main_variant in vv and "P3b" in vv
            d = st.get("paired_vs_P3b", {}).get(main_variant) if has else None
            saved = st["labels_saved_vs_P3b"][main_variant] if has else None
            main_json[s] = {
                "config": main_config,
                "horizon": h,
                "episodes": st["episodes"],
                "main_variant": main_variant,
                "mean_cost": {
                    k: vv[k]["mean_cost"] for k in ("P0", "P3b", main_variant) if k in vv
                },
                "main_minus_P3b": d,
                "pct_change_vs_P3b": vv[main_variant]["pct_vs_P3b"] if has else None,
                "labels_saved_vs_P3b": saved,
                "headroom_capture": {
                    k: vv[k]["headroom_capture"] for k in ("P3b", main_variant) if k in vv
                },
            }
            main_rows.append(
                [
                    f"{s} (K={st['episodes']})",
                    f(vv.get("P0", {}).get("mean_cost")),
                    f(vv.get("P3b", {}).get("mean_cost")),
                    f(vv.get(main_variant, {}).get("mean_cost")),
                    ci(d),
                    f(saved, 1),
                ]
            )
        md = f"# Main results ({main_config}, horizon {h}); B3+ = {main_variant}\n\n" + md_table(
            ["Dataset", "P0", "P3b", "B3+", "B3+ vs P3b (95% CI)", "labels saved"], main_rows
        )
        (tables / f"main_results{sfx}.json").write_text(json.dumps(main_json, indent=2))
        (tables / f"main_results{sfx}.md").write_text(md)
        written += [f"main_results{sfx}.json", f"main_results{sfx}.md"]
        # baselines / ablations
        abl_json, abl_md = {}, f"# Baselines and ablations ({main_config}, horizon {h})\n\n"
        for s, v in sel.items():
            st = v["stats"]
            abl_json[s] = {"config": main_config, "horizon": h, **st}
            rows = []
            for name, d in st["variants"].items():
                pv = st.get("paired_vs_P3b", {}).get(name)
                rows.append(
                    [
                        name + (" (hindsight)" if name == "P1" else ""),
                        f(d["mean_cost"]),
                        f(d["pct_vs_P0"], 1),
                        f(d["mean_labels"], 1),
                        f(d["promotion_rate"], 3),
                        f(d["mean_promotion_time"], 0),
                        f(d["mean_switches"], 3),
                        f(d["mean_rollbacks"], 3),
                        f(d["headroom_capture"], 3),
                        ci(pv),
                    ]
                )
            abl_md += (
                f"## {s} (K={st['episodes']})\n\n"
                + md_table(
                    [
                        "Variant",
                        "cost",
                        "% vs P0",
                        "labels",
                        "promo rate",
                        "promo t",
                        "switches",
                        "rollbacks",
                        "headroom",
                        "vs P3b (95% CI)",
                    ],
                    rows,
                )
                + "\n"
            )
        (tables / f"baselines_ablations{sfx}.json").write_text(json.dumps(abl_json, indent=2))
        (tables / f"baselines_ablations{sfx}.md").write_text(abl_md)
        written += [f"baselines_ablations{sfx}.json", f"baselines_ablations{sfx}.md"]
        # sensitivity across configs (this horizon only)
        sens_json, rows = {}, []
        for (s, cfg, hh), v in stats.items():
            if hh != h:
                continue
            st, vv = v["stats"], v["stats"]["variants"]
            has = main_variant in vv and "P3b" in vv
            d = st.get("paired_vs_P3b", {}).get(main_variant) if has else None
            sens_json[f"{s}__{cfg}"] = {
                "meta": v["meta"],
                "horizon": h,
                "episodes": st["episodes"],
                **st,
            }
            rows.append(
                [
                    s,
                    cfg,
                    f"B{v['meta']['budget']} cs{v['meta']['cs']:g} cq{v['meta']['cq']:g} d{v['meta']['delay']}",
                    f(vv.get("P0", {}).get("mean_cost")),
                    f(vv.get("P3b", {}).get("mean_cost")),
                    f(vv.get(main_variant, {}).get("mean_cost")),
                    ci(d),
                    f(st["labels_saved_vs_P3b"][main_variant], 1) if has else "n/a",
                ]
            )
        rows.sort()
        (tables / f"sensitivity{sfx}.json").write_text(json.dumps(sens_json, indent=2))
        (tables / f"sensitivity{sfx}.md").write_text(
            f"# Sensitivity across configs (horizon {h}); B3+ = {main_variant}\n\n"
            + md_table(
                [
                    "Dataset",
                    "Config",
                    "Setting",
                    "P0",
                    "P3b",
                    "B3+",
                    "B3+ vs P3b (95% CI)",
                    "labels saved",
                ],
                rows,
            )
        )
        written += [f"sensitivity{sfx}.json", f"sensitivity{sfx}.md"]
    return {"tables_dir": str(tables), "written": written}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--main-variant", default="P7", help="variant shown as B3+")
    ap.add_argument("--main-config", default="S0")
    a = ap.parse_args(argv)
    print(json.dumps(build(a.out, a.main_variant, a.main_config), indent=2))


if __name__ == "__main__":
    main()
