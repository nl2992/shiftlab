"""Amendment A7 mechanism stage (PROTOCOL A7): M1 head-to-head / ablations / ctx-ONS, M2 corrected negative control,
M3 stake-matched no-transfer controls. Runs after stage 4 on the confirm partition, the stage-4 cells, T=2000 and
N = min(A1.6 N, 1000) seeds per cell. Guarded by freeze.confirm_seeds_allowed(). Order: (1) DEV-seed M3 parameter
selection, frozen to <out>/m3_params.json (+ sha256) before (2) any confirm tape is drawn. Resumable per (method, cell)
shard. Stage-4 shards are only READ (first N seeds) when complete for a chunk; nothing under stage4/ is written.
Writes <out>/mechanism.json.

  PYTHONPATH=src .venv/Scripts/python.exe scripts/hgxh2c/stage4_mechanism.py [--smoke]
"""

import argparse
import importlib.util
import json
import time
from pathlib import Path

import pandas as pd
import torch

from shiftlab.hgxh2c import freeze, stats
from shiftlab.hgxh2c import grammar as G
from shiftlab.hgxh2c import mechanism as MC
from shiftlab.hgxh2c import search as SR
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.baselines import REGISTRY
from shiftlab.hgxh2c.evaluate import score

ROOT = Path(__file__).resolve().parents[2]
rp = lambda p: Path(p) if Path(p).is_absolute() else ROOT / p
MIX = "mix_w0.5"
NCAP = 1000
DEFECTIVE = {
    "label": "DEFECTIVE_A7",
    "applies_to": [
        "stage3 equivalence_suite E7-E9 (audit_cells(500, small=True), T=500, n=8: most changes after the horizon)",
        "stage3/stage4 cyclic-shift negative control (shuffled(): moves the change earlier, scores with original tau)",
        "stage4 confirmation.json entries '<hash>|nc', negative_control, equivalence.E7/E8/E9",
    ],
    "unchanged": "stage-4 primary analysis (per-seed J, IUT, Holm) is not affected",
}


def load(name):
    sp = importlib.util.spec_from_file_location(name, ROOT / f"scripts/hgxh2c/{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def run_methods(todo, tape, alt, fin_cands, params, S4):
    """Run the methods in ``todo`` on one chunk; returns {method_id: df}. Scoring always uses the ORIGINAL tape."""
    out, S = {}, tape["B"].shape[0]
    byh = {c.hash: c for c in fin_cands}
    spec = S4.specs(fin_cands)

    def add(mid, res, k, t0, track="J"):
        df = score(res, tape, track, k, mid)
        df["runtime_s"], df["peak_mem_mb"] = (time.perf_counter() - t0) / S, 0.0
        out[mid] = df[S4.KEEP]

    std = [m for m in todo if "|m2" not in m and "|m3" not in m and "|stake" not in m]
    out.update(S4.run_chunk(tape, std, spec))
    for m in todo:
        t0 = time.perf_counter()
        if m.endswith("|m2"):  # finalist with source track(s) replaced
            c = byh[m[:-3]]
            tp = MC.replace_source(tape, alt, MC.source_channels(c))
            add(m, G.compile_batch([c]).run(tp), 0, t0)
        elif m.startswith(
            MIX + "|m2tape:"
        ):  # matched no-transfer comparator on the same replaced tape
            tp = MC.replace_source(tape, alt, m.split(":")[1])
            add(m, REGISTRY[MIX][0]().run(tp), 0, t0)
        elif m.endswith("|m3a"):
            ad = params["addon"][m[:-4]]
            add(m, MC.mix_control(add=ad).run(tape), 0, t0)
        elif m == MIX + "|m3b":
            add(m, MC.mix_control(mult=params["mult"]).run(tape), 0, t0)
    return out


def method_list(fr, fin_cands):
    bases, secondary = list(fr.union), list(fr.secondary)
    ext = [MIX] if MIX not in bases + secondary else []
    spec = []
    for c in fin_cands:
        spec += [c.hash, f"{c.hash}|ctx"]
        spec += [
            f"{c.hash}|abl:{'_'.join(G.SLOTS[s])}" for s in range(6) if c.slots[s]
        ]  # same ids as stage 4
        spec += [f"{c.hash}|m2", f"{c.hash}|m3a"]
    chans = sorted({MC.source_channels(c) for c in fin_cands} - {""})
    spec += [f"{MIX}|m2tape:{s}" for s in chans] + [f"{MIX}|m3b"]
    return bases, secondary, bases + secondary + ext + spec


def analyse(W, fin, bases, secondary, fin_cands, params, a, S4):
    """W: DataFrame (cell_id, seed, family, one J column per method). Returns the mechanism dict."""
    S4._M.clear()
    B = lambda x, y, seed: S4.boot(W, x, y, a.boot, seed)  # gain = J_y - J_x, positive: x better
    res = {}
    for c in fin_cands:
        h = c.hash
        v = {
            "source_channels": MC.source_channels(c),
            "n_shift_ops": sum(1 for i in range(6) for o, _ in c.slots[i] if o == "shift"),
        }
        v["m1"] = {
            "vs_primary": {b: B(h, b, 1) for b in bases if b in W},
            "vs_secondary": {b: B(h, b, 2) for b in secondary if b in W},
            "ablations": {
                s.split("abl:")[1]: B(h, s, 3) for s in W.columns if str(s).startswith(h + "|abl:")
            },
            "ctx_replace": B(h, h + "|ctx", 4) if h + "|ctx" in W else None,
            "note": "gain = J_other - J_finalist; for ablation/ctx_replace positive = the channel helps",
        }
        src = MC.source_channels(c)
        v["gain_vs_mix"] = B(h, MIX, 5)
        m2 = {"finalist_M2_vs_mix_w0.5": B(h + "|m2", MIX, 6)}
        mt = f"{MIX}|m2tape:{src}"
        if mt in W:
            m2["finalist_M2_vs_mix_same_replaced_tape"] = B(h + "|m2", mt, 7)
        m2["note"] = (
            "gain = J_mix - J_finalist_M2. The clean-mix comparison is confounded negatively when the source track also "
            "carries its own evidence; the matched comparison runs mix_w0.5 on the same replaced tape."
        )
        v["m2"] = m2
        v["m3"] = {
            "a": B(h, h + "|m3a", 8),
            "b": B(h, MIX + "|m3b", 9),
            "shift_addon": params["addon"][h],
            "multiplier": params["mult"],
        }
        res[h] = v
    for key, get in (("m3a", lambda v: v["m3"]["a"]), ("m3b", lambda v: v["m3"]["b"])):
        hp = stats.holm({h: get(v)["p"] for h, v in res.items()})
        for h, v in res.items():
            v["m3"][key + "_holm_p"] = hp[h]
    for v in res.values():
        v["verdict"] = verdict(v)
    return res


def verdict(v):
    """A7 verdict. TRANSFER_SUPPORTED: finalist beats M3a and M3b (Holm p<0.05, mean>0) and the M2 gain vanishes
    (CI of the M2 gain vs mix_w0.5, and vs the matched mix, not significantly positive). STAKE_SIZE_EFFECT: the finalist
    beats mix_w0.5 but not both stake-matched controls. Else INCONCLUSIVE."""
    beats = lambda r, p: r["mean"] > 0 and p < 0.05
    b3a = beats(v["m3"]["a"], v["m3"]["m3a_holm_p"])
    b3b = beats(v["m3"]["b"], v["m3"]["m3b_holm_p"])
    vanishes = all(r["lo"] <= 0 for k, r in v["m2"].items() if isinstance(r, dict))
    orig = v["gain_vs_mix"]["mean"] > 0 and v["gain_vs_mix"]["lo"] > 0
    if orig and b3a and b3b and vanishes:
        return "TRANSFER_SUPPORTED"
    if orig and not (b3a and b3b):
        return "STAKE_SIZE_EFFECT"
    return "INCONCLUSIVE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--stage3", default="outputs/hgxh2c/stage3")
    ap.add_argument("--stage4", default="outputs/hgxh2c/stage4")
    ap.add_argument("--out", default="outputs/hgxh2c/stage4_mechanism")
    ap.add_argument("--freeze-file", default=None)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument(
        "--n", type=int, default=0, help="override confirm N per cell (smoke / debugging only)"
    )
    ap.add_argument("--dev-seeds", type=int, default=64)
    ap.add_argument(
        "--dev-cells", type=int, default=0, help="limit dev cells (smoke / debugging only)"
    )
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--max-seeds", type=int, default=4096)
    a = ap.parse_args()
    ffile = Path(a.freeze_file) if a.freeze_file else freeze.FREEZE
    freeze.confirm_seeds_allowed(
        ffile
    )  # raises unless frontier and finalists are frozen and verified
    d = freeze.require_frozen(["frontier", "finalists"], ffile)
    S4 = load("stage4_confirm")
    out = ROOT / a.out
    sh = out / "shards"
    sh.mkdir(parents=True, exist_ok=True)
    fin = json.loads(rp(d["finalists"]["path"]).read_text())
    fr = SR.Frontier(rp(d["frontier"]["path"]))
    fin_cands = [G.Candidate.from_dict(f["cand"]) for f in fin["finalists"]]
    T = 2000
    cells = TP.dev_grid(T)
    if a.smoke:
        T = int(fin["plan"]["T12"])
        cells = [TP.ScenarioCell(c.family, c.magnitude, c.delay, c.label_regime, c.proxy, T)
                 for c in S4.json_cells(fin)]  # fmt: skip
    nn = lambda c: (
        a.n
        or min(
            NCAP, fin["N_per_cell_null"] if c.family in TP.NULL_FAMILIES else fin["N_per_cell_alt"]
        )
    )

    # ---- (1) DEV-seed selection of the M3 parameters, frozen before any confirm tape is drawn
    if not (out / MC.PARAMS).exists():
        dcells = cells[: a.dev_cells] if a.dev_cells else cells
        print(f"dev selection on {len(dcells)} cells x {a.dev_seeds} seeds", flush=True)
        params = MC.select_m3(fin_cands, dcells, a.dev_seeds, a.device, score, a.max_seeds)
        params["finalists_sha"] = d["finalists"]["sha256"]
        params["frontier_sha"] = d["frontier"]["sha256"]
        params["frozen_utc"] = pd.Timestamp.now("UTC").isoformat()
        print("m3_params sha256", MC.freeze_m3(out, params), flush=True)
    params = MC.verify_m3(out)  # refuses to continue unless frozen and unchanged
    if params["finalists_sha"] != d["finalists"]["sha256"]:
        raise RuntimeError("M3 params were frozen against different finalists")

    # ---- (2) confirm runs
    bases, secondary, methods = method_list(fr, fin_cands)
    s4sh = rp(a.stage4) / "shards"
    shard = lambda m, c: sh / S4.safe(m) / (S4.safe(c.cell_id) + ".parquet")
    s4shard = lambda m, c: s4sh / S4.safe(m) / (S4.safe(c.cell_id) + ".parquet")
    print(f"{len(cells)} cells, {len(methods)} methods, device {a.device}", flush=True)
    for k, chunk in enumerate(MC.chunked(cells, nn, a.max_seeds)):
        todo = [
            m
            for m in methods
            if not all(shard(m, c).exists() or s4shard(m, c).exists() for c in chunk)
        ]
        if not todo:
            continue
        t0 = time.perf_counter()
        tape = TP.cat_tapes([TP.generate(c, "confirm", nn(c), a.device) for c in chunk])
        alt = TP.cat_tapes([MC.generate_indep(c, "confirm", nn(c), a.device) for c in chunk])
        res = run_methods(todo, tape, alt, fin_cands, params, S4)
        for m, df in res.items():
            (sh / S4.safe(m)).mkdir(exist_ok=True)
            for c in chunk:
                f = shard(m, c)
                tmp = f.with_suffix(".tmp")
                df[df.cell_id == c.cell_id].to_parquet(tmp, index=False)
                tmp.replace(f)
        print(
            f"chunk {k} ({len(chunk)} cells, {len(todo)} methods) {time.perf_counter() - t0:.1f}s",
            flush=True,
        )
        del tape, alt

    # ---- (3) analysis
    cap = {c.cell_id: nn(c) for c in cells}

    def read(m):
        parts = []
        for c in cells:
            f = shard(m, c) if shard(m, c).exists() else s4shard(m, c)
            x = pd.read_parquet(f)
            parts.append(x[x.seed < cap[c.cell_id]])
        return pd.concat(parts, ignore_index=True).set_index(["cell_id", "seed"])

    D = {m: read(m) for m in methods}
    idx = D[MIX].index
    W = pd.DataFrame({m: x.J_cost.reindex(idx) for m, x in D.items()})
    W = W.join(D[MIX][["family"]]).reset_index()
    fins = analyse(W, fin, bases, secondary, fin_cands, params, a, S4)
    mech = {
        "protocol": "PROTOCOL Amendment A7",
        "config": {
            "N_cap": NCAP,
            "N_alt": min(NCAP, fin["N_per_cell_alt"]),
            "N_null": min(NCAP, fin["N_per_cell_null"]),
            "T": T,
            "cells": len(cells),
            "boot": a.boot,
            "smoke": a.smoke,
            "partition": "confirm",
            "m3_params_sha256": (out / MC.SHA).read_text().strip(),
            "frozen": {k: v["sha256"] for k, v in freeze.read_freeze(ffile).items()},
        },
        "m3_params": params,
        "defective_a7": DEFECTIVE,
        "finalists": fins,
        "interpretation_rule": (
            "A7: primary pass but verdict != TRANSFER_SUPPORTED caps the section-10 outcome at "
            "'useful combination, weak novelty' (gain explained by stake size / not shown to be information transfer)."
        ),
    }
    (out / "mechanism.json").write_text(
        json.dumps(mech, indent=1, default=lambda o: None if o is None else float(o))
    )
    print("wrote", out / "mechanism.json")


if __name__ == "__main__":
    main()
