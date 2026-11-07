"""Stage-3 search machinery (PROTOCOL section 8 + A1.5/A1.6). Scoring is vectorised over [candidates, seeds].

Delta_J(candidate) = equal-cell mixture of (best frozen-frontier J-member's cell-mean J) - (candidate's cell-mean J),
both measured on the SAME tape (common random numbers). Never reads the confirm partition.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import beta, norm

from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.baselines import REGISTRY
from shiftlab.hgxh2c.evaluate import C_FA, C_I, C_Q, C_S
from shiftlab.hgxh2c.evaluate import run as eval_run

ROOT = Path(__file__).resolve().parents[3]
ALPHA, WINDOW = 0.05, 800
EMPIRICAL = ("cusum", "ph")
REG_COLS = [
    "rung",
    "hash",
    "status",
    "reason",
    "cand",
    "structure",
    "dJ",
    "power",
    "labels",
    "far_k",
    "far_n",
    "far_lo",
    "runtime_s",
    "novelty",
    "extra",
    "scoring",
]
SCORING = "a6_min_member_cumulative"  # dJ(c) = min over fixed primary set P of mean_cells(J_b - J_c)  (PROTOCOL A6)
OLD_SCORING = "a5_percell_min"  # rows written before A6 (per-cell oracle composite); listed in _scoring_manifest.json


# ------------------------------------------------------------------ registry (append-only parts)
class Registry:
    def __init__(self, path, prefix=""):
        """prefix: part-name prefix (stage 3 uses 'a6-' so A6 parts never collide with the archived A5 parts)."""
        self.dir = Path(path)
        self.prefix = prefix
        self.dir.mkdir(parents=True, exist_ok=True)

    def append(self, name, df):
        """New part file; an existing part is never rewritten (deterministic names make resume idempotent)."""
        f = self.dir / f"part-{self.prefix}{name}.parquet"
        if f.exists() or df is None or not len(df):
            return False
        df = df.copy()
        df["scoring"] = SCORING
        for c in REG_COLS:
            if c not in df:
                df[c] = None
        df = df[REG_COLS].copy()
        df["rung"] = df["rung"].astype("int64")
        for c in ("hash", "status", "reason", "cand", "extra", "scoring"):
            df[c] = df[c].astype("string")
        for c in (
            "structure",
            "dJ",
            "power",
            "labels",
            "far_k",
            "far_n",
            "far_lo",
            "runtime_s",
            "novelty",
        ):
            df[c] = df[c].astype("float64")
        tmp = f.with_suffix(f".{uuid.uuid4().hex[:6]}.tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(f)
        return True

    def read(self):
        fs = sorted(self.dir.glob("part-*.parquet"))
        old = set()
        m = (
            self.dir / "_scoring_manifest.json"
        )  # sidecar: parts written under the A5 scoring (never rewritten)
        if m.exists():
            old = set(json.loads(m.read_text("utf-8")).get("a5_percell_min", []))
        parts = []
        for f in fs:
            d = pd.read_parquet(f)
            d["scoring"] = OLD_SCORING if f.name in old else d.get("scoring", SCORING)
            parts.append(d)
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=REG_COLS)


# ------------------------------------------------------------------ frontier
class Frontier:
    def __init__(self, fp):
        self.fp = Path(fp)
        d = json.loads(self.fp.read_text("utf-8"))
        # A5: primary family = anytime-valid J-track frontier members (strong controls included); secondary = empirical-alarm
        # CUSUM / Page-Hinkley, logged but never optimised.
        isJ = lambda m: m in REGISTRY and REGISTRY[m][1] == "J" and not m.startswith(EMPIRICAL)
        self.secondary = [m for m in REGISTRY if m.startswith(EMPIRICAL)]
        self.cells = {
            k[2:]: [m for m in v if isJ(m)] for k, v in d["frontier"].items() if k.startswith("J|")
        }
        self.union = sorted({m for v in self.cells.values() for m in v}) or [
            m for m in REGISTRY if isJ(m) and not m.startswith(("cusum", "ph"))
        ]
        self.summary = self.fp.parent / "summary.parquet"

    def ref_ids(self, cell):
        cid = cell.cell_id
        return (
            self.cells.get(cid) or self.cells.get(cid.rsplit("|T", 1)[0] + "|T2000") or self.union
        )

    def hardness(self):
        """cell key (cell_id sans T) -> best frontier J (high = hard for the frontier)."""
        if not self.summary.exists():
            return {}
        s = pd.read_parquet(self.summary)
        s = s[s.method_id.isin(self.union)]
        b = s.groupby("cell_id").J_cost.min()
        return {k.rsplit("|T", 1)[0]: v for k, v in b.items()}


# ------------------------------------------------------------------ cells
def pick_cells(n_cells, T, fr: Frontier, seed=0, n_null=6):
    """Rung-0 cells: n_null guaranteed-null cells + harm cells oversampled where the frontier's best J is worst."""
    rng = np.random.default_rng(seed)
    grid = TP.dev_grid(T)
    nulls = [c for c in grid if c.family in ("null_stationary", "null_boundary")]
    harm = [c for c in grid if c.family not in TP.NULL_FAMILIES]
    h = fr.hardness()
    w = np.array([h.get(c.cell_id.rsplit("|T", 1)[0], np.nan) for c in harm], float)
    w = np.where(np.isnan(w), np.nanmean(w) if (~np.isnan(w)).any() else 1.0, w)
    w = 0.25 + (w - w.min()) / max(np.ptp(w), 1e-9)
    ih = rng.choice(len(harm), size=min(n_cells - n_null, len(harm)), replace=False, p=w / w.sum())
    inull = rng.choice(len(nulls), size=min(n_null, len(nulls)), replace=False)
    return [nulls[i] for i in inull] + [harm[i] for i in ih]


def stress_cells(T, small=False):
    fams = [(f, 0.0) for f in TP.NULL_FAMILIES] + [(f, 0.08) for f in TP.ALT_FAMILIES]
    ds, regs, prox = (
        ((0, 20), ("b05",), ("good",)) if small else ((0, 5, 20, 50), ("b05", "b20"), TP.PROXIES)
    )
    return [
        TP.ScenarioCell(f, m, d, r, p, T) for f, m in fams for d in ds for r in regs for p in prox
    ]


def audit_cells(T, small=False):
    fams = [(f, 0.0) for f in TP.NULL_FAMILIES] + [(f, 0.08) for f in TP.ALT_FAMILIES]
    ds, regs, prox = (
        ((5,), ("b20",), ("good",)) if small else ((5, 20), ("b20", "b05"), ("good", "biased"))
    )
    return [
        TP.ScenarioCell(f, m, d, r, p, T) for f, m in fams for d in ds for r in regs for p in prox
    ]


# ------------------------------------------------------------------ batched evaluation
def _at(cs, idx):
    return cs.unsqueeze(0).expand(idx.shape[0], -1, -1).gather(2, idx.unsqueeze(2)).squeeze(2)


def ensure_cs(tape):
    if "cs" not in tape:
        tape["cs"] = {
            c: torch.cat([torch.zeros_like(tape[c][:, :1]), tape[c].cumsum(1)], 1) for c in "BC"
        }


def per_seed(res, tape, track="J"):
    """Vectorised twin of evaluate.score: J_cost, alarm, labels as [K,S] tensors."""
    T = tape["B"].shape[1]
    ev = tape["eval"]
    ensure_cs(tape)
    al, nq = res.alarm[track], res.nq_at[track].double()
    stop = torch.where(al >= T, torch.full_like(al, T - 1), al)
    tauv = torch.where(ev["tau"] >= 0, ev["tau"], torch.full_like(ev["tau"], T)).clamp(0, T)
    exc = 0.0
    for c, null in (("B", ev["null_B"]), ("C", ev["null_C"])):
        cs = tape["cs"][c]
        tot = (
            _at(cs, stop + 1)
            - cs.gather(1, tauv[:, None])[:, 0][None]
            - tape["theta"][c] * (stop + 1 - tauv[None])
        )
        exc = exc + torch.where(
            (~null & (ev["tau"] >= 0))[None] & (stop >= tauv[None]), tot, torch.zeros_like(tot)
        )
    hit = (al < T).double()
    fa = hit * (ev["null_B"] & ev["null_C"])[None]
    return exc + C_Q * nq + C_FA * fa + (C_I + C_S) * hit, al, nq


def kmax_auto(S, Dmax, device, cap=16384, ntr=4):
    """Candidates per wide batch from free GPU memory: ~5 ring doubles x (Dmax+2) per track plus ~250 state/temporary
    [K,S] doubles. An OOM during a run halves K (run_cands)."""
    if not str(device).startswith("cuda"):
        return max(1, min(cap, int(2e7 // max(S, 1)) // 8))
    free = torch.cuda.mem_get_info()[0]
    per = 8 * (250 + 5 * ntr * (Dmax + 2)) * S
    return int(max(1, min(cap, 0.6 * free // per)))


def sig(c):
    """Operator-type signature: batches are filled in this order so neighbours share active operators."""
    return tuple(tuple(o for o, _ in s) for s in c.slots)


def run_cands(cands, tape, fn, kmax=None, paths=False, graph=None):
    """Run candidates as WIDE batches: one Monitor per (base engines, combiner) with every parameter a [K,1] tensor,
    filled in operator-signature order and sized to GPU memory; CUDA-graph captured on cuda. fn(res, sub_indices) is
    called per batch; returns seconds per candidate in the order of ``cands``."""
    dev = tape["B"].device
    S, Dmax = tape["B"].shape[0], int(tape["d"].max())
    km = kmax or kmax_auto(S, Dmax, dev)
    graph = str(dev).startswith("cuda") if graph is None else graph
    pos, out = {}, np.zeros(len(cands))
    for i, c in enumerate(cands):
        pos.setdefault(c.group, []).append(i)
    for idx in pos.values():
        idx.sort(key=lambda i: sig(cands[i]))
        i = 0
        while i < len(idx):
            sub = idx[i : i + km]
            try:
                t0 = time.perf_counter()
                res = G.compile_batch([cands[j] for j in sub], graph=graph).run(
                    tape, keep_paths=paths
                )
                fn(res, sub)
                if str(dev).startswith("cuda"):
                    torch.cuda.synchronize()
                out[sub] = (time.perf_counter() - t0) / len(sub)
                i += len(sub)
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                km = max(1, km // 2)
                if km == 1 and len(sub) == 1:
                    raise
    return out


def tapes_for(cells, partition, n, device, max_seeds=4096):
    assert partition != "confirm", "stage 3 never touches the confirm partition"
    per = max(1, max_seeds // n)
    for i in range(0, len(cells), per):
        yield TP.cat_tapes([TP.generate(c, partition, n, device) for c in cells[i : i + per]])


def eval_cands(cands, cells, n, partition, device, kmax=None, transform=None):
    """-> dict of numpy arrays: per-(candidate, cell) tables [N, nc] plus runtime [N]."""
    N, tabs, rt = (
        len(cands),
        {k: [] for k in ("J", "hit", "harm", "fa", "null", "af", "lab")},
        np.zeros(len(cands)),
    )
    for tape in tapes_for(cells, partition, n, device):
        if transform:
            tape = transform(tape)
        nc, T, ev = len(tape["cells"]), tape["B"].shape[1], tape["eval"]
        acc = {k: torch.zeros(N, nc, dtype=torch.float64) for k in tabs}
        harm = ~(ev["null_B"] & ev["null_C"]) & (ev["tau"] >= 0)
        nullg = torch.tensor(
            [
                c.family in ("null_stationary", "null_boundary")
                for c in tape["cells"]
                for _ in range(n)
            ],
            device=harm.device,
        )
        nulls = ev["null_B"] & ev["null_C"] & nullg

        def fn(res, sub, tape=tape, acc=acc, nc=nc, T=T, ev=ev, harm=harm, nulls=nulls):
            J, al, nq = per_seed(res, tape)
            v = lambda x: x.view(len(sub), nc, n).mean(2).cpu()
            s = lambda x: x.view(len(sub), nc, n).sum(2).double().cpu()
            hit = harm[None] & (al >= ev["tau"][None]) & (al <= ev["tau"][None] + WINDOW)
            fa = nulls[None] & (al < T)
            for k, x in (
                ("J", v(J)),
                ("af", v(al.clamp(max=T).double() / T)),
                ("lab", v(nq)),
                ("hit", s(hit)),
                ("fa", s(fa)),
            ):
                acc[k][sub] = x
            for k, x in (("harm", harm), ("null", nulls)):
                acc[k][sub] = s(x[None].expand(len(sub), -1))

        rt += run_cands(cands, tape, fn, kmax)
        for k, v in tabs.items():
            v.append(acc[k].numpy())
        del tape
    out = {k: np.concatenate(v, 1) for k, v in tabs.items()}
    out["runtime"] = rt
    return out


def shuffled(tape, which, seed=0):
    """Negative control: random cyclic time-shift of the source channel(s) `which` (e.g. 'B', 'BC'); marginals kept,
    cross-risk alignment broken. Scoring keeps the original labels (eval and cumulative sums)."""
    ensure_cs(tape)
    t = dict(tape)
    S, T = tape["B"].shape
    sh = torch.randint(
        T // 4, 3 * T // 4 + 1, (S,), generator=torch.Generator().manual_seed(seed)
    ).to(tape["B"].device)
    idx = (torch.arange(T, device=sh.device)[None] - sh[:, None]) % T
    for ch in which:
        t[ch], t[ch + "hat"] = tape[ch].gather(1, idx), tape[ch + "hat"].gather(1, idx)
    return t


def cp_lower(k, n, conf=0.95):
    k, n = np.asarray(k, float), np.asarray(n, float)
    lo = beta.ppf((1 - conf) / 2, np.maximum(k, 1), np.maximum(n - k + 1, 1))
    return np.where((k == 0) | (n == 0), 0.0, lo)


def baseline_table(fr: Frontier, cells, n, partition, device):
    """Frontier members on the same tape. A6: JP [|P|, nc] = cell-mean J of EVERY primary member (fixed set P = fr.union)
    and JS [|S|, nc] for the empirical-alarm family; scoring takes the min over members of the cumulative mean gain."""
    P, S = list(fr.union), list(fr.secondary)
    parts = []
    for i in range(0, len(cells), 64):
        parts.append(eval_run(P + S, cells[i : i + 64], partition, n, device))
    df = pd.concat(parts, ignore_index=True)
    T = cells[0].T
    jm = df.groupby(["method_id", "cell_id"]).J_cost.mean().unstack("cell_id")
    af = (
        df.assign(a=np.where(df.alarm_J < 0, T, df.alarm_J) / T)
        .groupby(["method_id", "cell_id"])
        .a.mean()
        .unstack("cell_id")
    )
    order = [c.cell_id for c in cells]
    P = [m for m in P if m in jm.index]
    S = [m for m in S if m in jm.index]
    return {
        "JP": jm.loc[P, order].to_numpy(float),
        "JS": jm.loc[S, order].to_numpy(float) if S else None,
        "members": P,
        "secondary": S,
        "feats": af.loc[P][order].to_numpy(float),
        "jm": jm[order],
        "df": df,
    }


def min_member_gain(JP, Jc):
    """A6 score: min over members b of mean_cells(J_b - J_c). JP [|P|, nc], Jc [N, nc] -> (dJ [N], binding member [N])."""
    g = np.stack([(JP[b][None] - Jc).mean(1) for b in range(len(JP))])  # [|P|, N]
    return g.min(0), g.argmin(0)


def summarise(tabs, JP, cells, JS=None):
    """Candidate-level scores from per-cell tables (A6). dJ is the min over the primary members of the cumulative gain;
    dJ_sec is the same over the empirical-alarm family (logged, never optimised); frac_worse = share of cells where the
    candidate is worse than its binding member."""
    dJ, bind = min_member_gain(JP, tabs["J"])
    harm, hit = tabs["harm"].sum(1), tabs["hit"].sum(1)
    k, nn = tabs["fa"].sum(1), tabs["null"].sum(1)
    return pd.DataFrame(
        {
            "dJ": dJ,
            "power": np.where(harm > 0, hit / np.maximum(harm, 1), np.nan),
            "labels": tabs["lab"].mean(1),
            "far_k": k,
            "far_n": nn,
            "far_lo": cp_lower(k, nn),
            "runtime_s": tabs["runtime"],
            "dJ_sec": min_member_gain(JS, tabs["J"])[0] if JS is not None else np.nan,
            "frac_worse": (tabs["J"] > JP[bind]).mean(1),
        }
    )


# ------------------------------------------------------------------ selection
def pareto_rank(M):
    """Domination count of rows of M (all objectives maximised); 0 = non-dominated. Chunked O(N^2)."""
    N, out = len(M), np.zeros(len(M), int)
    for i in range(0, N, 512):
        a = M[i : i + 512, None, :]
        out[i : i + 512] = ((M[None] >= a).all(2) & (M[None] > a).any(2)).sum(1)
    return out


def select_rung0(df, feats, base_feats, n_ops, keep, div_frac=0.15, rng=None):
    """Top-`keep` by Delta_J among FAR survivors, 15% of the slots by Pareto(Delta_J, novelty, cheapness) in the rest."""
    ok = np.where(df.far_lo.to_numpy() <= ALPHA)[0]
    ok = ok[np.argsort(-df.dJ.to_numpy()[ok], kind="stable")]
    n_main = round(keep * (1 - div_frac))
    main, rest = ok[:n_main], ok[n_main:]
    nov = np.zeros(len(df))
    f = torch.tensor(feats, dtype=torch.float32)
    nov[:] = (
        torch.cdist(f, torch.tensor(base_feats, dtype=torch.float32), p=1).min(1).values
        / f.shape[1]
    ).numpy()
    if len(rest) and keep > n_main:
        pool = rest[: max(10 * (keep - n_main), 2000)]
        kept = f[main[:5000]] if len(main) else f[:1]
        nk = torch.cdist(f[pool], kept, p=1).min(1).values.numpy() / f.shape[1]
        M = np.column_stack([df.dJ.to_numpy()[pool], np.minimum(nov[pool], nk), -n_ops[pool]])
        pr = pareto_rank(M)
        extra = pool[np.lexsort((-M[:, 0], pr))[: keep - n_main]]
        main = np.concatenate([main, extra])
    return main, nov


def select_pareto(df, keep):
    ok = np.where(df.far_lo.to_numpy() <= ALPHA)[0]
    M = np.column_stack(
        [df.dJ.to_numpy()[ok], np.nan_to_num(df.power.to_numpy()[ok]), -df.labels.to_numpy()[ok]]
    )
    pr = pareto_rank(M)
    return ok[np.lexsort((-M[:, 0], pr))[:keep]]


def select_top(df, keep):
    ok = np.where(df.far_lo.to_numpy() <= ALPHA)[0]
    return ok[np.argsort(-df.dJ.to_numpy()[ok], kind="stable")[:keep]]


# ------------------------------------------------------------------ selector / paired tables / power N
def calib_score(tape, src=200):
    """Per-stream proxy calibration on SOURCE data (first 200 steps, before any change): 1 - mean sq. proxy error / sd^2."""
    z = [
        1 - ((tape[c + "hat"][:, :src] - tape[c][:, :src]) ** 2).mean(1) / tape["sd"][c] ** 2
        for c in "BC"
    ]
    return (0.5 * (z[0] + z[1])).cpu().numpy()


def finalist_tables(cands, fr, cells, n, partition, device):
    """Per-seed J of the finalists [F,nc,n], per-seed J of every primary member {member: [nc,n]} (A6: paired differences
    are taken against the binding member of each finalist), calibration [nc,n], plus delay and label regime per cell."""
    F, J, ref, cal = len(cands), [], {}, []
    for tape in tapes_for(cells, partition, n, device):
        nc = len(tape["cells"])
        out = torch.zeros(F, nc * n, dtype=torch.float64)

        def fn(res, sub, tape=tape, out=out):
            out[sub] = per_seed(res, tape)[0].cpu()

        run_cands(cands, tape, fn)
        J.append(out.view(F, nc, n).numpy())
        cal.append(calib_score(tape).reshape(nc, n))
        df = eval_run(list(fr.union), tape["cells"], partition, n, device)
        pv = df.pivot_table(index=["cell_id", "seed"], columns="method_id", values="J_cost")
        for m in pv.columns:
            ref.setdefault(m, []).append(
                np.stack([pv.loc[c.cell_id][m].to_numpy() for c in tape["cells"]])
            )
    return {
        "J": np.concatenate(J, 1),
        "ref": {m: np.concatenate(v, 0) for m, v in ref.items()},
        "cal": np.concatenate(cal, 0),
        "delay": np.array([c.delay for c in cells]),
        "regime": np.array([c.label_regime for c in cells]),
    }


def fit_selector(hashes, tabs):
    """Lookup rule (d, label regime, calibration tercile) -> finalist, fitted on per-stream J of dev+stress tables
    (list of finalist_tables); falls back to (d, regime) then global. Uses design-time observables only."""
    rows = []
    for t in tabs:
        nc, n = t["cal"].shape
        for c in range(nc):
            for s in range(n):
                rows.append(
                    (
                        int(t["delay"][c]),
                        str(t["regime"][c]),
                        float(t["cal"][c, s]),
                        *t["J"][:, c, s],
                    )
                )
    df = pd.DataFrame(rows, columns=["d", "reg", "cal", *range(len(hashes))])
    cut = [float(x) for x in df.cal.quantile([1 / 3, 2 / 3])]
    df["bin"] = np.digitize(df.cal, cut)
    best = lambda g: int(g[list(range(len(hashes)))].mean().idxmin())
    table = {
        f"{d}|{r}|{b}": best(g) for (d, r, b), g in df.groupby(["d", "reg", "bin"]) if len(g) >= 30
    }
    table.update({f"{d}|{r}": best(g) for (d, r), g in df.groupby(["d", "reg"]) if len(g) >= 30})
    return {
        "finalists": list(hashes),
        "cut": cut,
        "table": table,
        "global_best": best(df),
        "n_rows": len(df),
    }


def select_index(sel, d, regime, cal):
    b = int(np.digitize(cal, sel["cut"]))
    t = sel["table"]
    return t.get(f"{d}|{regime}|{b}", t.get(f"{d}|{regime}", sel["global_best"]))


def power_n(diffs, k, floor=1000, cap=10000, power=0.8, shrink=0.5):
    """A1.6: smallest per-cell N giving `power` to detect shrink*effect, one-sided 0.05/k.
    diffs [nc, n] paired J differences (best baseline - candidate) from rung 3. Variance of the equal-cell mean =
    between-cell variance / nc + mean within-cell variance / (nc N)."""
    nc = diffs.shape[0]
    delta, between, within = (
        diffs.mean(),
        diffs.mean(1).var(ddof=1) / 1.0,
        diffs.var(1, ddof=1).mean(),
    )
    z = norm.ppf(1 - 0.05 / k) + norm.ppf(power)
    room = (shrink * delta / z) ** 2 - between / nc
    if delta <= 0 or room <= 0:
        return {
            "N": cap,
            "capped": True,
            "delta": float(delta),
            "sd_within": float(within**0.5),
            "sd_between": float(between**0.5),
        }
    N = within / nc / room
    return {
        "N": int(min(cap, max(floor, np.ceil(N)))),
        "capped": bool(N > cap),
        "raw_N": float(N),
        "delta": float(delta),
        "sd_within": float(within**0.5),
        "sd_between": float(between**0.5),
    }


# ------------------------------------------------------------------ equivalence tests E1-E11 (NOVELTY_AUDIT section 4, A3.6)
def pp_identity_check(n_sets=200, seed=0):
    """E5 (candidate independent): exact enumeration over (Q, R) of E[1 + lam x] for random finite supports with
    E[R] <= theta; the PP factor must have conditional mean <= 1 and equal 1 + lam (E[R] - theta) exactly."""
    rng = np.random.default_rng(seed)
    worst, err = -1.0, 0.0
    for _ in range(n_sets):
        v = rng.uniform(0, 1, 4)
        p = rng.dirichlet(np.ones(4))
        theta = float(p @ v) + rng.uniform(0, 0.1)  # null: E[R] <= theta
        h, q = rng.uniform(0, 0.6), rng.uniform(0.05, 1)
        bd = 0.6 * (1 / q - 1) + theta
        lam = rng.uniform(0, 0.5 / bd)
        ef = sum(
            pq * pr * (1 + lam * (h + (Qv / q) * (r - h) - theta))
            for Qv, pq in ((1, q), (0, 1 - q))
            for r, pr in zip(v, p)
        )
        worst = max(worst, ef - 1)
        err = max(err, abs(ef - (1 + lam * (float(p @ v) - theta))))
    return {
        "max_E_f_minus_1": float(worst),
        "max_abs_identity_err": float(err),
        "pass_": bool(worst <= 1e-12 and err < 1e-12),
    }


def equivalence_suite(cands, fr, device, n=8, T=500):
    """E1-E10 on audit seeds (E11, the size audit, needs the confirm-size null runs: stage4_confirm). Returns
    {hash: {E1..E10}}; every entry states the criterion it was judged on."""
    from shiftlab.hgxh2c import baselines as BL

    cells = audit_cells(T, small=True)
    tape = TP.cat_tapes([TP.generate(c, "audit", n, device) for c in cells])
    Jm = lambda res, k=0: float(per_seed(res, tape)[0][k].mean())
    eq = G.audit_equivalence(cands, tape)  # E2
    jb = {}
    for m in ("ryu_wornell", "mix_w0.25", "mix_w0.5", "mix_w0.75", "indep_HG_H2c"):  # E7
        jb[m] = Jm(BL.REGISTRY[m][0]().run(tape))
    e5 = pp_identity_check()
    out = {}
    for c in cands:
        o = out[c.hash] = {}
        res = G.compile(c).run(tape, keep_paths=True)
        none = G.compile(G.Candidate(((),) * 6, c.comb, c.w, c.base)).run(tape, keep_paths=True)
        jc = Jm(res)
        # E1: the single-op special cases reproduce H2c / HG (checks the reduction, per component present in the candidate)
        e1 = {}
        if any(op == "ratio" and p == (1.0, 0) for op, p in c.slots[0]):
            r1 = G.compile(
                G.Candidate((c.slot("BC", "S"),) + ((),) * 5, "bonf", 0.0, ("kelly", "kelly"))
            ).run(tape, keep_paths=True)
            e1["h2c"] = (
                float(
                    (r1.logW["C"][0] - BL.h2c().run(tape, keep_paths=True).logW["C"][0]).abs().max()
                )
                if c.slots[0] == (("ratio", (1.0, 0)),)
                else None
            )
        if c.slots[3] == (("gate", (0.0,)),):
            r1 = G.compile(
                G.Candidate(((),) * 3 + (c.slots[3],) + ((),) * 2, "bonf", 0.0, ("kelly", "kelly"))
            ).run(tape, keep_paths=True)
            e1["hg"] = float(
                (r1.logW["B"][0] - BL.hg().run(tape, keep_paths=True).logW["B"][0]).abs().max()
            )
        o["E1"] = {"res": e1 or "not applicable", "criterion": "max abs dlogW < 1e-9"}
        o["E2"] = {
            "res": eq[c.hash] or "not equivalent",
            "criterion": "max abs dlogW < 1e-9 vs joint ctx ONS / no-transfer",
        }
        # E3: stake function class: regress the candidate's stake on [1, base stake B, base stake C] (the joint linear class)
        r2 = {}
        X = torch.stack(
            [torch.ones_like(none.lam["B"][0]), none.lam["B"][0], none.lam["C"][0]], -1
        ).reshape(-1, 3)
        for t in "BC":
            y = res.lam[t][0].reshape(-1, 1)
            beta_ = torch.linalg.lstsq(X.cpu(), y.cpu()).solution
            resid = y.cpu() - X.cpu() @ beta_
            r2[t] = {
                "R2": float(1 - resid.var() / y.cpu().var().clamp(min=1e-18)),
                "max_resid": float(resid.abs().max()),
            }
        o["E3"] = {
            "res": r2,
            "in_class": bool(min(v["R2"] for v in r2.values()) > 0.99),
            "criterion": "R2 > 0.99 => in linear joint class (J-gap refit not computed)",
        }
        # E4: pure query candidates vs Xu (ipw uses the OTHER track's variance, so the src=tgt identity does not apply)
        o["E4"] = {
            "res": "not applicable (ipw src != tgt)"
            if any(op == "ipw" for s in c.slots for op, _ in s)
            else "no ipw operator"
        }
        o["E5"] = {
            "res": e5,
            "criterion": "E[f]<=1 by exact enumeration, |E[f]-(1+lam(E R-theta))|<1e-12",
        }
        # E6: R controls (no restart; periodic predetermined restart every 250 steps) -> Delta_J = J_control - J_candidate
        if any(s for s in c.slots[2::3]):
            norest = G.Candidate(
                tuple(() if SLOTS_R else s for s, SLOTS_R in zip(c.slots, (0, 0, 1, 0, 0, 1))),
                c.comb,
                c.w,
                c.base,
            )
            mons = {"no_restart": G.compile(norest)}
            per = G.compile(norest)
            keep = lambda ctx: torch.where(
                (ctx.tt % 250 == 0) & (ctx.tt > 0),
                torch.zeros_like(ctx.logW["B"]),
                torch.ones_like(ctx.logW["B"]),
            )
            per.hooks.restart = {"B": keep, "C": keep}
            mons["periodic_250"] = per
            o["E6"] = {
                "res": {k: Jm(m.run(tape)) - jc for k, m in mons.items()},
                "criterion": "Delta_J = J_control - J_candidate; candidate counts only if > 0 vs best",
            }
        else:
            o["E6"] = {"res": "no R operator"}
        o["E7"] = {
            "res": {k: v - jc for k, v in jb.items()},
            "criterion": "Delta_J = J_baseline - J_candidate on audit seeds",
        }
        sh = G.compile(c).run(SR_shuffle(tape, c), keep_paths=False)
        o["E8"] = {
            "res": {"J_shifted_minus_J": Jm(sh) - jc},
            "criterion": "gain must vanish when the source is cyclically shifted",
        }
        abl = {
            "_".join(G.SLOTS[i]): Jm(G.compile(c.without(i)).run(tape)) - jc
            for i in range(6)
            if c.slots[i]
        }
        ctxr = Jm(G.compile_batch([c], ctx_replace=True).run(tape)) - jc
        o["E9"] = {
            "res": {"ablation_J_minus_Jfull": abl, "ctx_replace_J_minus_Jfull": ctxr},
            "criterion": "which channel carries the gain",
        }
        o["E10"] = {
            "res": "comb=" + c.comb,
            "valid": c.comb != "prod",
            "criterion": "product combiner is INVALID (A3.1)",
        }
    return out


def SR_shuffle(tape, c):
    which = ("B" if any(c.slots[:3]) else "") + ("C" if any(c.slots[3:]) else "")
    return shuffled(tape, which, seed=3) if which else tape
