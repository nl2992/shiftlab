"""WP1: chronological incumbent-challenger streams, outcome-blind episode classifier, real runner.

Protocol (registered before any build or policy run): docs/sprint2/wp1/protocol.md.

    uv run python scripts/sota_sprint/late_real.py build              # data/sprint_late_losses/*.npz
    uv run python scripts/sota_sprint/late_real.py classify --out outputs/sprint2/WP1/classes.json
    uv run python scripts/sota_sprint/late_real.py run --streams all --policies P1,P2 --seeds 5 \
        --workers 2 --out outputs/sprint2/WP1/primary [--delay-mult 0.5] [--budget 100] [--cs 2]
    uv run python scripts/sota_sprint/late_real.py analyze outputs/sprint2/WP1/primary \
        --classes outputs/sprint2/WP1/classes.json --out outputs/sprint2/WP1/primary.json

Construction (protocol section 2): for each episode start e both roles are refit with the same model
class; ``win``: incumbent on [e-D-H, e-D), challenger on [e-H, e); ``exp``: incumbent on [0, e-D),
challenger on [e-W, e). Preprocessing and the label threshold use rows before e only.

Runner: replays screen.py's real-stream seeding exactly (same stream generator, policy generators and
metrics), but takes any loss file in the stream table and accepts delay / budget / switch-cost
overrides, which screen.py cannot do for real streams. The evaluator-side gain passed to the metrics
is the classifier's piecewise segment means (m1 before tau, m2 after) instead of screen.py's
episode mean; it only affects the diagnostics (frac_on_wrong, detect_delay, excess_vs_expected_G,
regret_expected_oracle), never ``net``.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORRECTION_TAG = "_mopeinterval_20261106"
CORRECTED_REPLAY = False


def _records(directory):
    import pandas as pd
    path = Path(directory)
    old = pd.read_json(path / "records.jsonl", lines=True)
    sibling = path.with_name(path.name + CORRECTION_TAG) / "records.jsonl"
    if not CORRECTED_REPLAY or not sibling.is_file():
        if not CORRECTED_REPLAY:
            return old
        manifest_path = path / "manifest.json"
        if not manifest_path.is_file():
            return old
        manifest = json.loads(manifest_path.read_text())
        constituents = manifest.get("constituent_runs", [])
        if not constituents:
            return old
        parts = []
        for name in constituents:
            source = Path(name)
            if not source.is_absolute():
                source = ROOT / source
            base = pd.read_json(source / "records.jsonl", lines=True)
            replay = source.with_name(source.name + CORRECTION_TAG) / "records.jsonl"
            if replay.is_file():
                patch = pd.read_json(replay, lines=True)
                base = base[~base.policy.isin(set(patch.policy))]
                base = pd.concat([base, patch], ignore_index=True)
            parts.append(base)
        new = pd.concat(parts, ignore_index=True)
        policies = set(new.policy)
        previous = old[old.policy.isin(policies)]
        keys = ["kind", "regime", "ep", "seed", "policy"]
        if previous.duplicated(keys).any() or new.duplicated(keys).any():
            raise ValueError(f"duplicate aggregate WP1 correction keys for {path}")
        joined = previous[keys].merge(new[keys], on=keys, how="outer", indicator=True,
                                      validate="one_to_one")
        if not (joined["_merge"] == "both").all():
            raise ValueError(f"aggregate WP1 correction coverage differs for {path}")
        return pd.concat([old[~old.policy.isin(policies)], new], ignore_index=True)
    new = pd.read_json(sibling, lines=True)
    keys = ["kind", "regime", "ep", "seed", "policy"]
    if not set(keys).issubset(old) or not set(keys).issubset(new):
        raise ValueError(f"missing exact WP1 correction keys for {path}")
    policies = set(new.policy)
    previous = old[old.policy.isin(policies)]
    if previous.duplicated(keys).any() or new.duplicated(keys).any():
        raise ValueError(f"duplicate WP1 correction keys for {path}")
    joined = previous[keys].merge(new[keys], on=keys, how="outer", indicator=True,
                                   validate="one_to_one")
    if not (joined["_merge"] == "both").all():
        raise ValueError(f"unmatched WP1 correction rows for {path}")
    return pd.concat([old[~old.policy.isin(policies)], new], ignore_index=True)
for _p in (ROOT / "scripts/failure_atlas_v2_flq", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

OUT = ROOT / "data/sprint_late_losses"
T_EP = 2000
MAX_EPS = 20
D_LAG, H_WIN, W_RECENT = 4000, 4000, 2000
CONSTRUCTIONS = ("win", "exp")
UCI = ("metro", "beijing_pm25", "bike_hour", "appliances", "household_power")
CACHED = ("rialto", "openml_ldpa", "airlines", "criteo", "bank", "elec2", "weather", "spam",
          "uci_occupancy")
TWIN_SPLITS = (0, 1)

# classifier constants (protocol section 4)
DELTA, SEG_MIN, T_LATE, BLOCK, N_PERM, P_SIG, PERM_SEED = 0.01, 200, 400, 50, 999, 0.01, 20261104
CLASSES = ("late_improvement", "early_improvement", "reversal", "stationary_better", "null")


# ----------------------------------------------------------------------------- construction
def episode_starts(n: int) -> np.ndarray:
    e_min = max(int(0.30 * n), D_LAG + H_WIN)
    K = (n - e_min) // T_EP
    idx = np.arange(K) if K <= MAX_EPS else np.unique(np.round(np.linspace(0, K - 1, MAX_EPS)).astype(int))
    return (e_min + T_EP * idx).astype(np.int64)


def train_ranges(constr: str, e: int) -> tuple[tuple[int, int], tuple[int, int]]:
    if constr == "win":
        return (e - D_LAG - H_WIN, e - D_LAG), (e - H_WIN, e)
    if constr == "exp":
        return (0, e - D_LAG), (e - W_RECENT, e)
    raise ValueError(constr)


def _hgb():
    from sklearn.ensemble import HistGradientBoostingClassifier

    return HistGradientBoostingClassifier(max_iter=100, max_depth=4, learning_rate=0.1,
                                          random_state=0)


def build_dataset(name: str) -> list[dict]:
    import fresh_real as fr

    x, yraw, ts = fr.LOADERS[name]()
    cat = fr.CATEGORICAL.get(name, [])
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    thr = float(np.median(yraw.to_numpy()[: int(0.30 * n)]))
    y = (yraw.to_numpy() > thr).astype(int)
    starts = episode_starts(n)
    stats = []
    for constr in CONSTRUCTIONS:
        L0, L1 = [], []
        for e in starts:
            (a0, b0), (a1, b1) = train_ranges(constr, int(e))
            f = fr.prep(x.iloc[min(a0, a1):e], cat)
            m0 = _hgb().fit(f(x.iloc[a0:b0]), y[a0:b0])
            m1 = _hgb().fit(f(x.iloc[a1:b1]), y[a1:b1])
            xe, ye = f(x.iloc[e:e + T_EP]), y[e:e + T_EP]
            L0.append((m0.predict(xe) != ye).astype(np.int8))
            L1.append((m1.predict(xe) != ye).astype(np.int8))
        l0, l1 = np.stack(L0), np.stack(L1)
        OUT.mkdir(parents=True, exist_ok=True)
        p = OUT / f"late_{name}_{constr}.npz"
        np.savez(p, l0=l0, l1=l1, starts=starts)
        adv = (l0.astype(float) - l1).mean(axis=1)
        stats.append({
            "stream": p.stem, "dataset": name, "construction": constr, "n_rows": n, "K": len(starts),
            "starts": starts.tolist(),
            "episode_time_start": [str(ts.iloc[int(e)]) for e in starts],
            "label_threshold": thr, "D": D_LAG, "H": H_WIN, "W": W_RECENT,
            "raw_sha256": fr.sha256(fr.raw_zip(name)),
            "array_content_sha256": hashlib.sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).hexdigest(),
            "incumbent_err": float(l0.mean()), "challenger_err": float(l1.mean()),
            "disagreement": float((l0 != l1).mean()),
            "mean_adv_per_episode": [round(float(a), 4) for a in adv],
        })
        print(f"{p.stem:32s} K={len(starts):2d} err0={l0.mean():.3f} err1={l1.mean():.3f} "
              f"dis={(l0 != l1).mean():.3f}")
    return stats


# ----------------------------------------------------------------------------- stream table
def _delay_native(name: str) -> int:
    from screen import FRESH_DELAYS, REAL_DELAYS

    return {**REAL_DELAYS, **FRESH_DELAYS}[name]


@functools.lru_cache(maxsize=1)
def streams() -> dict[str, dict]:
    """name -> {file, rows (episode indices into the file), delay, cluster, family}."""
    out = {}
    for nm in CACHED:
        p = ROOT / f"data/atlas_v2_losses/{nm}.npz"
        out[nm] = {"file": p, "rows": list(range(np.load(p)["l0"].shape[0])), "delay": _delay_native(nm),
                   "cluster": nm, "family": "cached"}
    for nm in UCI:
        p = ROOT / f"data/sprint_fresh_losses/{nm}.npz"
        out[nm] = {"file": p, "rows": list(range(np.load(p)["l0"].shape[0])), "delay": _delay_native(nm),
                   "cluster": nm, "family": "fresh"}
        for c in CONSTRUCTIONS:
            q = OUT / f"late_{nm}_{c}.npz"
            if q.exists():
                out[q.stem] = {"file": q, "rows": list(range(np.load(q)["l0"].shape[0])),
                               "delay": _delay_native(nm), "cluster": nm, "family": f"late_{c}"}
        t = ROOT / f"data/sprint_twin_losses/twin_{nm}.npz"
        if t.exists():
            z = np.load(t)
            rows = np.flatnonzero(np.isin(z["split"], TWIN_SPLITS)).tolist()
            out[f"twin_{nm}"] = {"file": t, "rows": rows, "delay": _delay_native(nm), "cluster": nm,
                                 "family": "twin"}
    return out


def select(spec: str) -> list[str]:
    st = streams()
    groups = {"all": [k for k, v in st.items() if v["family"] != "twin"],
              "twin": [k for k, v in st.items() if v["family"] == "twin"],
              "late": [k for k, v in st.items() if v["family"].startswith("late")],
              "fixed": [k for k, v in st.items() if v["family"] in ("cached", "fresh")]}
    names = []
    for s in spec.split(","):
        names += groups.get(s, [s])
    return names


# ----------------------------------------------------------------------------- classifier
def _cusum_stat(d: np.ndarray):
    T = len(d)
    sd = d.std()
    if sd == 0:
        return 0.0, T // 2
    S = np.cumsum(d - d.mean())[:-1]  # S[k-1] = sum_{t<k}
    k = np.arange(1, T)
    ok = (k >= SEG_MIN) & (k <= T - SEG_MIN)
    a = np.abs(S) * ok
    i = int(np.argmax(a))
    return float(a[i] / (sd * np.sqrt(T))), int(k[i])


def _sgn(x: float, delta: float) -> int:
    return 1 if x >= delta else (-1 if x <= -delta else 0)


def classify(l0, l1, delta: float = DELTA) -> dict:
    d = np.asarray(l0, float) - np.asarray(l1, float)
    T = len(d)
    stat, tau = _cusum_stat(d)
    if stat == 0.0:
        p = 1.0
    else:
        rng = np.random.default_rng(PERM_SEED)
        nb = T // BLOCK
        blocks = d[: nb * BLOCK].reshape(nb, BLOCK)
        perm = np.empty(N_PERM)
        for i in range(N_PERM):
            perm[i] = _cusum_stat(blocks[rng.permutation(nb)].ravel())[0]
        p = float((1 + (perm >= stat).sum()) / (N_PERM + 1))
    change = p <= P_SIG
    m1, m2, mb = float(d[:tau].mean()), float(d[tau:].mean()), float(d.mean())
    s1, s2, sb = _sgn(m1, delta), _sgn(m2, delta), _sgn(mb, delta)
    sub = []
    if change and s1 <= 0 and s2 == 1 and m2 - m1 >= 2 * delta:
        cls = "late_improvement" if tau >= T_LATE else "early_improvement"
    elif change and s1 == 1 and s2 <= 0 and m1 - m2 >= 2 * delta:
        cls = "reversal"
    elif sb == 1:
        cls = "stationary_better"
        sub += ["changed"] if change else []
    else:
        cls = "null"
        sub += (["worse"] if sb == -1 else []) + (["changed"] if change else [])
    return {"class": cls, "sub": sub, "tau": tau, "p": p, "stat": round(stat, 4), "m1": round(m1, 5),
            "m2": round(m2, 5), "mbar": round(mb, 5), "dis": round(float((d != 0).mean()), 4)}


def _classify_stream(name):
    st = streams()[name]
    z = np.load(st["file"])
    out = []
    for r in st["rows"]:
        c = classify(z["l0"][r], z["l1"][r])
        c["sens"] = {str(dl): classify(z["l0"][r], z["l1"][r], dl)["class"] for dl in (0.005, 0.02)}
        out.append({"stream": name, "ep": int(r), "cluster": st["cluster"], "family": st["family"], **c})
    return out


def classify_all(names, workers=2) -> list[dict]:
    with mp.Pool(workers) as pool:
        return [row for rows in pool.map(_classify_stream, names) for row in rows]


# ----------------------------------------------------------------------------- runner
def _job(args):
    name, ep, seed, seed_base, names, delay_mult, budget, cs, alpha = args
    import screen
    from registry import EXTRA
    from suite import build_suite

    st = streams()[name]
    z = np.load(st["file"])
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    c = classify(losses[:, 0], losses[:, 1])
    gain = np.where(np.arange(losses.shape[0]) < c["tau"], c["m1"], c["m2"])
    delay = max(1, int(round(st["delay"] * delay_mult)))
    cq = screen.CONTRACT["cq"]
    rows = []
    run_ep = ep * 100_000 + seed
    for pol in build_suite(losses.shape[0], budget, cs, cq, alpha, delay, run_ep,
                           seed_base + screen._h(name) % 1000, names=names, extra=EXTRA):
        stream_rng = np.random.default_rng([seed_base, screen._h(name), ep, seed, 7])
        m = screen.metrics(pol, losses, gain, delay=delay, budget=budget, cq=cq, cs=cs,
                           stream_rng=stream_rng)
        rows.append({"kind": "real", "gain_is_proxy": True, "regime": name, "ep": ep, "seed": seed,
                     "policy": pol.name, "alpha": alpha, "delay": delay, "budget": budget, "cs": cs,
                     "delay_mult": delay_mult, **m})
    return rows


def run(names, policies, seeds, out, *, seed_base=2026110803, workers=2, delay_mult=1.0,
        budget=200, cs=5.0, alpha=0.05, only_classes=None, classes_path=None):
    st = streams()
    keep = None
    if only_classes:  # classifier output is outcome-blind (protocol A3)
        keep = {(r["stream"], r["ep"]) for r in json.loads(Path(classes_path).read_text())
                if r["class"] in only_classes}
    jobs = [(n, r, s, seed_base, policies, delay_mult, budget, cs, alpha)
            for n in names for r in st[n]["rows"] for s in range(seeds)
            if keep is None or (n, r) in keep]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(out / "records.jsonl", "w") as f, mp.Pool(workers) as pool:
        for rows in pool.imap_unordered(_job, jobs, chunksize=2):
            for row in rows:
                f.write(json.dumps(row) + "\n")
    import screen

    srcs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            for p in sorted(HERE.glob("*.py"))}
    srcs.update({str(st[n]["file"].relative_to(ROOT)): hashlib.sha256(st[n]["file"].read_bytes()).hexdigest()[:16]
                 for n in names})
    man = {"argv": sys.argv, "streams": names, "policies": policies, "seeds": seeds,
           "seed_base": seed_base, "delay_mult": delay_mult, "budget": budget, "cs": cs,
           "alpha": alpha, "git": screen._git_rev(), "sources": srcs, "n_jobs": len(jobs),
           "seconds": round(time.time() - t0, 1)}
    (out / "manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    print(f"done {len(jobs)} jobs in {time.time() - t0:.0f}s -> {out}")


# ----------------------------------------------------------------------------- analysis
CERTIFIED = ["xu_acquisition_only", "SMCS+retain-incumbent", "gated_adaptive_range+front",
             "choe_ramdas_eb+front", "gated_deployment", "discern_style", "gated_adaptive_range"]
from bench import CERTIFIED_PUBLISHED
RMM_HOSTS = {"rmm:gated_deployment+RMM": "gated_deployment",
             "rmm:discern_style+RMM": "discern_style",
             "rmm:SMCS+retain-incumbent+RMM": "SMCS+retain-incumbent",
             "rmm:gated_adaptive_range+RMM": "gated_adaptive_range"}


def cluster_boot(df, col, n_boot=2000, seed=20261104):
    """Mean of per-episode values with a 95% percentile CI from resampling clusters."""
    g = {k: v[col].to_numpy() for k, v in df.groupby("cluster")}
    keys = list(g)
    mean = float(df[col].mean())
    if len(keys) < 3:
        return {"mean": round(mean, 2), "lo": None, "hi": None, "n_ep": int(len(df)), "n_cl": len(keys)}
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        v = np.concatenate([g[keys[i]] for i in pick])
        bs.append(v.mean())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"mean": round(mean, 2), "lo": round(float(lo), 2), "hi": round(float(hi), 2),
            "n_ep": int(len(df)), "n_cl": len(keys)}


def episode_table(dirs, classes_path):
    import pandas as pd

    df = pd.concat([_records(d) for d in dirs],
                   ignore_index=True)
    cl = pd.DataFrame(json.loads(Path(classes_path).read_text()))
    J = df.groupby(["regime", "ep", "policy"]).net.mean().unstack("policy")
    J.index = J.index.set_names(["stream", "ep"])
    meta = cl.set_index(["stream", "ep"])[["class", "cluster", "family", "tau", "m1", "m2"]]
    return J.join(meta, how="inner"), df


def contrasts(E, pols, classes=CLASSES, extra_pairs=()):
    res = {}
    for c in (*classes, "all"):
        g = E if c == "all" else E[E["class"] == c]
        if g.empty:
            res[c] = {"n_ep": 0}
            continue
        certs = [p for p in CERTIFIED if p in g]
        best = min(certs, key=lambda p: g[p].mean()) if certs else None
        r = {"n_ep": int(len(g)), "n_cl": int(g.cluster.nunique()), "best_certified": best,
             "mean_J": {p: round(float(g[p].mean()), 2) for p in pols if p in g}, "contrasts": {}}
        pairs = []
        for rm, host in RMM_HOSTS.items():
            if rm in g:
                pairs += [(rm, best), (rm, host), (rm, "CONTROL_never_switch")]
        pairs += list(extra_pairs)
        for a, b in pairs:
            if a in g and b in g:
                h = g.assign(_d=g[a] - g[b])
                r["contrasts"][f"{a} - {b}"] = cluster_boot(h, "_d")
        res[c] = r
    return res


PAIRS = ([(f"E_rb:{h}", rm) for rm, h in RMM_HOSTS.items()]
         + [(rm, f"E_srr:{h}") for rm, h in RMM_HOSTS.items()]
         + [("rmm:gated_deployment+RMM", "rmm:gated_deployment+RMM_single"),
            ("rmm:gated_deployment+RMM", "rmm:gated_deployment+RMM_noacq"),
            ("rmm:discern_style+RMM", "rmm:discern_style+RMM_single"),
            ("rmm:discern_style+RMM", "rmm:discern_style+RMM_noacq"),
            ("rmm:SMCS+retain-incumbent+RMM", "rmm:SMCS+retain-incumbent+RMM_single"),
            ("E_srr:gated_deployment", "E_srr_noacq:gated_deployment"),
            ("rmm:gated_deployment+RMM", "E_glr:gated_deployment"),
            ("rmm:gated_deployment+RMM", "xu_acquisition_only"),
            ("E_swcert", "xu_acquisition_only")])


def report(primary, twin, sens, classes_path, supplemental=()) -> dict:
    """Everything RESULTS.md reports, from validated run outputs only."""
    import collections

    from risk_curves import wilson

    cl = json.loads(Path(classes_path).read_text())
    out = {"class_counts": {}, "class_clusters": {}}
    for r in cl:
        k = r["family"]
        out["class_counts"].setdefault(k, collections.Counter())[r["class"]] += 1
        if r["class"] in ("late_improvement", "reversal", "early_improvement") and k != "twin":
            out["class_clusters"].setdefault(r["class"], collections.Counter())[r["cluster"]] += 1
    E, df = episode_table([primary, *supplemental], classes_path)
    pols = [p for p in E.columns if p not in ("class", "cluster", "family", "tau", "m1", "m2")]
    real = E[E.family != "twin"]
    out["primary"] = contrasts(real, pols, extra_pairs=PAIRS)
    out["late_constructions_only"] = contrasts(E[E.family.str.startswith("late")], pols)
    late = out["primary"]["late_improvement"]
    ok = 0
    for rm in RMM_HOSTS:
        c = late.get("contrasts", {}).get(f"{rm} - {late.get('best_certified')}")
        ok += int(bool(c) and c["hi"] is not None and c["mean"] < 0 and c["hi"] < 0)
    enough = late.get("n_ep", 0) >= 10 and late.get("n_cl", 0) >= 3
    out["H_late"] = {"hosts_supporting": ok, "enough_episodes": enough,
                     "verdict": ("INSUFFICIENT_REAL_LATE_EPISODES" if not enough else
                                 "SUPPORTED" if ok >= 3 else "NOT_SUPPORTED")}
    d = df.merge(pd_classes(cl), left_on=["regime", "ep"], right_on=["stream", "ep"])
    d = d[d.family != "twin"]
    diag = d.groupby(["class", "policy"]).agg(promote=("ever_promote", "mean"),
                                              rollbacks=("n_rollbacks", "mean"),
                                              switches=("switches", "mean"),
                                              harm_on1=("excess_vs_expected_G", "mean"),
                                              labels=("labels", "mean"))
    out["diagnostics"] = {c: g.droplevel(0).round(3).to_dict("index") for c, g in diag.groupby(level=0)}
    if twin:
        t = pd_read(twin)
        out["twin_promotion"] = {}
        for p, g in t.groupby("policy"):
            k, n = int(g.ever_promote.sum()), len(g)
            lo, hi = wilson(k, n)
            out["twin_promotion"][p] = {"rate": round(k / n, 3), "ci": [round(lo, 3), round(hi, 3)], "n": n}
    out["sensitivity"] = {}
    for sd in sens:
        if not (Path(sd) / "records.jsonl").exists():
            continue
        Es, _ = episode_table([sd], classes_path)
        Es = Es[Es.family != "twin"]
        ps = [p for p in Es.columns if p not in ("class", "cluster", "family", "tau", "m1", "m2")]
        res = contrasts(Es, ps, classes=("late_improvement", "reversal", "stationary_better", "null"),
                        extra_pairs=[("E_rb:gated_deployment", "rmm:gated_deployment+RMM")])
        out["sensitivity"][Path(sd).name] = {
            c: {"n_ep": v.get("n_ep"), "best_certified": v.get("best_certified"),
                "contrasts": v.get("contrasts", {})}
            for c, v in res.items()}
    return out


def pd_read(d):
    return _records(d)


def pd_classes(cl):
    import pandas as pd

    return pd.DataFrame(cl)[["stream", "ep", "class", "family", "cluster"]]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    c = sub.add_parser("classify")
    c.add_argument("--streams", default="all,twin")
    c.add_argument("--workers", type=int, default=2)
    c.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--streams", default="all")
    r.add_argument("--policies", required=True)
    r.add_argument("--seeds", type=int, default=5)
    r.add_argument("--seed-base", type=int, default=2026110803)
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--delay-mult", type=float, default=1.0)
    r.add_argument("--budget", type=int, default=200)
    r.add_argument("--cs", type=float, default=5.0)
    r.add_argument("--alpha", type=float, default=0.05)
    r.add_argument("--only-classes", default="")
    r.add_argument("--classes", default="")
    r.add_argument("--out", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("dirs", nargs="+")
    a.add_argument("--classes", required=True)
    a.add_argument("--extra-pairs", default="")
    a.add_argument("--out", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("--primary", required=True)
    rp.add_argument("--twin", default="")
    rp.add_argument("--sens", nargs="*", default=[])
    rp.add_argument("--supplemental", nargs="*", default=[],
                    help="additional policy records to join to primary episodes for a scoped sensitivity")
    rp.add_argument("--classes", required=True)
    rp.add_argument("--amended-no-xu", action="store_true",
                    help="Exclude Xu acquisition adapter from published-certificate ranking; preserve historical output separately.")
    rp.add_argument("--strict-published-subset", action="store_true",
                    help="Rank only evaluated members of bench.CERTIFIED_PUBLISHED; report omitted ports.")
    rp.add_argument("--adaptive-gate-corrected", action="store_true",
                    help="Substitute affected rows from exact-key same-seed correction replays.")
    rp.add_argument("--out", required=True)
    x = ap.parse_args(argv)
    if x.cmd == "report":
        global CERTIFIED, CORRECTED_REPLAY
        if x.amended_no_xu and x.strict_published_subset:
            ap.error("choose only one of --amended-no-xu or --strict-published-subset")
        if x.amended_no_xu:
            CERTIFIED = [p for p in CERTIFIED if p != "xu_acquisition_only"]
        if x.strict_published_subset:
            CERTIFIED = list(CERTIFIED_PUBLISHED)
        CORRECTED_REPLAY = bool(x.adaptive_gate_corrected)
        res = report(x.primary, x.twin, x.sens, x.classes, x.supplemental)
        if CORRECTED_REPLAY:
            res["adaptive_gate_correction"] = ("affected policies replaced by exact stream/episode/seed/policy matches; "
                                                "same-seed sensitivity, not independent confirmation")
        if x.strict_published_subset:
            policy_set = set()
            for policy_dir in [x.primary, *x.supplemental]:
                policy_set.update(pd_read(policy_dir).policy.unique())
            available = [p for p in CERTIFIED_PUBLISHED if p in policy_set]
            missing = [p for p in CERTIFIED_PUBLISHED if p not in policy_set]
            res["comparator_panel"] = {"source": "bench.CERTIFIED_PUBLISHED", "available": available,
                                       "missing": missing,
                                       "coverage": f"{len(available)}/{len(CERTIFIED_PUBLISHED)}"}
            if missing:
                res["analysis_status"] = ("strict published-pool subset sensitivity; rankings use only evaluated members of bench.CERTIFIED_PUBLISHED; "
                                           "one or more registered ports are absent; same-episode comparator selection remains unadjusted")
            else:
                res["analysis_status"] = ("strict published-pool analysis; all six bench.CERTIFIED_PUBLISHED ports are evaluated; "
                                           "same-episode comparator selection remains unadjusted")
        elif x.amended_no_xu:
            res["analysis_status"] = ("amended adapter-panel sensitivity; Xu acquisition adapter excluded; Choe-Ramdas adapter retained; "
                                       "not a complete published-certificate ranking; same-episode comparator selection remains unadjusted")
        else:
            res["analysis_status"] = "registered historical analysis"
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(res, indent=1, default=str) + "\n")
        print(json.dumps(res["H_late"]))
        return
    if x.cmd == "build":
        stats = [s for nm in UCI for s in build_dataset(nm)]
        (OUT / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    elif x.cmd == "classify":
        rows = classify_all(select(x.streams), x.workers)
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(rows) + "\n")
        import collections

        cnt = collections.Counter((r["family"], r["class"]) for r in rows)
        for k in sorted(cnt):
            print(k, cnt[k])
    elif x.cmd == "run":
        run(select(x.streams), [p for p in x.policies.split(",") if p], x.seeds, x.out,
            seed_base=x.seed_base, workers=x.workers, delay_mult=x.delay_mult, budget=x.budget,
            cs=x.cs, alpha=x.alpha, only_classes=[c for c in x.only_classes.split(",") if c],
            classes_path=x.classes)
    else:
        E, _ = episode_table(x.dirs, x.classes)
        pols = [p for p in E.columns if p not in ("class", "cluster", "family", "tau", "m1", "m2")]
        pairs = [tuple(s.split(":", 1)[0].split("|")) for s in x.extra_pairs.split(",") if s]
        res = {"real_nontwin": contrasts(E[E.family != "twin"], pols, extra_pairs=pairs),
               "late_constructions": contrasts(E[E.family.str.startswith("late")], pols,
                                               extra_pairs=pairs),
               "fixed_pairs": contrasts(E[E.family.isin(["cached", "fresh"])], pols,
                                        extra_pairs=pairs)}
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res["real_nontwin"], indent=1)[:4000])


if __name__ == "__main__":
    main()
