"""Development comparison E_rb / RMM vs the matched two-sided e-SR.

Protocol (locked before running): docs/sota_fidelity/esr_vs_erb_dev_protocol.md.

    uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel main --out DIR
    uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel null --out DIR
    uv run python scripts/sota_fidelity/esr_vs_erb_dev.py analyze --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint",
           ROOT / "scripts/promising_directions/sota/competitors", ROOT / "scripts/sota_fidelity"):
    sys.path.insert(0, str(_p))

PANELS = {
    "main": dict(seed_base=2026120601, seeds=100, regimes=[
        "F3_reversal_800", "W_reversal_700", "S_reversal_400", "V_reversal_1000",
        "V_late_600", "W_late_1000", "F1_late_800", "F0_better"]),
    "null": dict(seed_base=2026120602, seeds=1000, regimes=["F0_null", "V_null", "V_worse"]),
    # plumbing check only, separate seed base; never analysed as evidence
    "pilot": dict(seed_base=2026120609, seeds=2, regimes=["F3_reversal_800", "V_late_600"]),
}
REVERSAL = PANELS["main"]["regimes"][:4]
LATE = ["V_late_600", "W_late_1000", "F1_late_800"]
HOSTS = ["gated_deployment", "discern_style", "SMCS+retain-incumbent", "gated_adaptive_range"]
ESR = "two_sided_esr_label_clock"
POLICIES = (["CONTROL_never_switch", ESR, "esr_rmmbets_fullalpha", "esr_arl",
             "shekhar_ramdas_rcs_t3_anyexcl", "river_page_hinkley_t3", "rmm:LRMD_k1"]
            + HOSTS + [f"rmm:{h}+RMM" for h in HOSTS] + [f"E_rb:{h}" for h in HOSTS])


def _job(args):
    import screen
    from bench import CONTRACT, parse_regime
    from smoke_shin_esr import build_extra
    from suite import build_suite

    name, seed, seed_base = args
    extra = build_extra()
    R, _ = parse_regime(name)
    losses = R.sample(np.random.default_rng(np.random.SeedSequence([seed_base, screen._h(R.name), seed])))
    gain, delay = R.truth_gain(), R.delay
    rows = []
    for pol in build_suite(losses.shape[0], CONTRACT["budget"], CONTRACT["cs"], CONTRACT["cq"],
                           CONTRACT["alpha"], delay, seed, seed_base + screen._h(name) % 1000,
                           names=POLICIES, extra=extra):
        m = screen.metrics(pol, losses, gain, delay=delay, budget=CONTRACT["budget"],
                           cq=CONTRACT["cq"], cs=CONTRACT["cs"],
                           stream_rng=np.random.default_rng([seed_base, screen._h(name), seed, 7]))
        rows.append({"regime": name, "seed": seed, "policy": pol.name, **m})
    return rows


def run(panel: str, out: Path, workers: int):
    cfg = PANELS[panel]
    jobs = [(r, s, cfg["seed_base"]) for r in cfg["regimes"] for s in range(cfg["seeds"])]
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"records_{panel}.jsonl"
    with Pool(workers) as pool, path.open("w") as f:
        for i, rows in enumerate(pool.imap_unordered(_job, jobs, chunksize=4)):
            for r in rows:
                f.write(json.dumps(r, default=float) + "\n")
            if i % 100 == 0:
                print(f"{panel}: {i}/{len(jobs)}", flush=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip())
    (out / f"manifest_{panel}.json").write_text(json.dumps(
        {**cfg, "panel": panel, "policies": POLICIES, "git_head": sha, "worktree_dirty": dirty,
         "n_jobs": len(jobs)}, indent=1))


def _tci(x):
    x = np.asarray(x, float)
    n = len(x)
    from scipy import stats
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(n)
    q = stats.t.ppf(0.975, n - 1)
    p = 2 * stats.t.sf(abs(m / se), n - 1) if se > 0 else float("nan")
    return {"mean": float(m), "ci95": [float(m - q * se), float(m + q * se)], "p": float(p), "n": n}


def _wilson_hi(k, n, z=1.96):
    p = k / n
    return float((p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n))


def analyze(out: Path):
    import pandas as pd

    df = pd.read_json(out / "records_main.jsonl", lines=True)
    net = df.pivot_table(index=["regime", "seed"], columns="policy", values="net")

    def block(regs, a_fmt, b=ESR):
        sub = net.loc[regs]
        d = sum(sub[a_fmt.format(h=h)] - sub[b] for h in HOSTS) / len(HOSTS)
        return d.groupby(level="seed").mean()

    res = {"primary_E_rb_minus_esr_reversal": _tci(block(REVERSAL, "E_rb:{h}"))}
    sec = {
        "S1_rmm_minus_esr_reversal": block(REVERSAL, "rmm:{h}+RMM"),
        "S2_rmm_minus_esr_late": block(LATE, "rmm:{h}+RMM"),
        "S3_E_rb_minus_esr_late": block(LATE, "E_rb:{h}"),
        "S4_E_rb_minus_esr_F0_better": block(["F0_better"], "E_rb:{h}"),
    }
    sec = {k: _tci(v) for k, v in sec.items()}
    order = sorted(sec, key=lambda k: sec[k]["p"])  # Holm
    for i, k in enumerate(order):
        sec[k]["p_holm"] = float(min(1.0, max(sec[o]["p"] * (len(order) - j) for j, o in enumerate(order[: i + 1]))))
    res["secondary"] = sec
    expl = {}
    for reg in PANELS["main"]["regimes"]:
        for pol in POLICIES:
            if pol == ESR:
                continue
            expl[f"{reg}|{pol}-{ESR}"] = _tci(net.loc[reg][pol] - net.loc[reg][ESR])
    res["exploratory_unadjusted"] = expl
    g = df.groupby(["regime", "policy"]).agg(
        net=("net", "mean"), labels=("labels", "mean"), switches=("switches", "mean"),
        rollbacks=("n_rollbacks", "mean"), on_wrong=("frac_on_wrong", "mean"),
        promote=("ever_promote", "mean"))
    res["summary"] = {f"{r}|{p}": v for (r, p), v in g.round(3).to_dict("index").items()}
    nul = out / "records_null.jsonl"
    if nul.exists():
        dn = pd.read_json(nul, lines=True)
        res["null_first_promotion"] = {
            f"{r}|{p}": {"rate": float(g.ever_promote.mean()), "n": len(g),
                         "wilson_hi": _wilson_hi(int(g.ever_promote.sum()), len(g))}
            for (r, p), g in dn.groupby(["regime", "policy"])}
    res["manifests"] = {p: json.loads((out / f"manifest_{p}.json").read_text())
                        for p in PANELS if (out / f"manifest_{p}.json").exists()}
    dst = ROOT / "docs/sota_fidelity/esr_vs_erb_dev_results.json"
    dst.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("primary_E_rb_minus_esr_reversal", "secondary")}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze"])
    ap.add_argument("--panel", choices=list(PANELS))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.panel, a.out, a.workers)
    else:
        analyze(a.out)


if __name__ == "__main__":
    main()
