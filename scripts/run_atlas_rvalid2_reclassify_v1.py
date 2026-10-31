"""Amendment 5 items 3-4: reclassify the cycle-3 Failure Atlas cells with R_valid2 and hard_budget_pacing.

Reuses cycle-3 per-seed results (archive.jsonl, discovery seeds 0..19) and reruns only
``ref_valid2`` and ``hard_budget_pacing`` on the same cells and seeds, plus ``ref_valid2`` on the
null twins (20 discovery seeds) and ``ref_valid``/``ref_valid2`` on the 100 dedicated null-fp seeds.
Resumable (append-only ``rerun.jsonl`` per family). Development-grade, descriptive only.

    .venv/Scripts/python scripts/run_atlas_rvalid2_reclassify_v1.py [--workers 6]
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import copy
import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import paired_ci, run, wilson

PREV = ROOT / "outputs" / "failure_atlas_v1_cycle3"
OUT = ROOT / "outputs" / "failure_atlas_v1_cycle4_rvalid2"
CLASSES = (
    "shared_failure",
    "cost_of_validity",
    "prior_gap",
    "headroom_not_shared",
    "no_headroom",
    "info_limited",
    "reference_unsafe",
)


def work(task: tuple) -> dict:
    kind, cell, seed_list, kappa = task
    if kind == "cell":
        res = fa.evaluate_cell(
            cell, seed_list, ["hard_budget_pacing"], ["ref_valid2"], kappa=kappa, with_null=False
        )
        return {k: res["methods"][k] for k in ("hard_budget_pacing", "ref_valid2")}
    if kind == "twin":
        res = fa.evaluate_cell(cell, seed_list, [], ["ref_valid2"], kappa=kappa, with_null=False)
        return {"ref_valid2": res["methods"]["ref_valid2"]}
    if kind == "nullfp":
        k1 = k2 = 0
        for sd in seed_list:
            st = fa.make_stream(cell, sd)
            cfg = cell.config(sd)
            k1 += int(run(st, fa.build_ref_valid(cell), cfg).promotions > 0)
            k2 += int(run(st, fa.build_ref_valid2(cell), cfg).promotions > 0)
        return {"k_valid": k1, "k_valid2": k2, "n": len(seed_list)}
    if kind == "repro":  # rerun the stored ref_valid to confirm the stored seeds reproduce
        res = fa.evaluate_cell(cell, seed_list, [], ["ref_valid"], kappa=kappa, with_null=False)
        return {"ref_valid": res["methods"]["ref_valid"]}
    raise ValueError(kind)


def load_rows(path: Path) -> dict[str, dict]:
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["key"]] = r
    return rows


def process_family(fam: int, pool, workers: int) -> dict:
    src = PREV / f"family{fam}"
    st = json.loads((src / "state.json").read_text(encoding="utf-8"))
    kappa = st["kappa"]
    disc = fa.seeds("discovery", 20)
    tag = f"{disc[0]}+{len(disc)}"
    prows = load_rows(src / "archive.jsonl")
    cells_by_id = {c.cell_id: c for c in (fa.all_cells2() if fam == 2 else fa.all_cells())}
    ids = [*st["sample"], *st["refine"]]
    cells = [cells_by_id[i] for i in ids]
    for cid in ids:
        assert list(prows[f"cell|{cid}|{tag}|k{kappa}"]["payload"]["seeds"]) == list(disc)
    twins = {c.null_twin().cell_id: c.null_twin() for c in cells}
    nf_seeds = fa.seeds("discovery", 100, offset=5000)

    odir = OUT / f"family{fam}"
    odir.mkdir(parents=True, exist_ok=True)
    rpath = odir / "rerun.jsonl"
    done = load_rows(rpath)
    tasks = []
    for c in cells:
        tasks.append((f"cell|{c.cell_id}", ("cell", c, tuple(disc), kappa)))
    for tid, tw in twins.items():
        tasks.append((f"twin|{tid}", ("twin", tw, tuple(disc), kappa)))
        tasks.append((f"nullfp|{tid}", ("nullfp", tw, tuple(nf_seeds), kappa)))
    for c in cells[:4]:
        tasks.append((f"repro|{c.cell_id}", ("repro", c, tuple(disc), kappa)))
    pending = [(k, t) for k, t in tasks if k not in done]
    print(f"[family {fam}] {len(pending)}/{len(tasks)} tasks pending", flush=True)
    step = max(1, workers * 8)
    with open(rpath, "a", encoding="utf-8") as fh:
        for i in range(0, len(pending), step):
            chunk = pending[i : i + step]
            for (k, _), out in zip(chunk, pool.map(work, [t for _, t in chunk]), strict=True):
                row = {"key": k, "payload": out}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                done[k] = row
            print(f"  [family {fam}] {min(i + step, len(pending))}/{len(pending)}", flush=True)

    # reproducibility of stored ref_valid costs
    repro_max = 0.0
    for c in cells[:4]:
        new = np.asarray(done[f"repro|{c.cell_id}"]["payload"]["ref_valid"]["cost"])
        old = np.asarray(
            prows[f"cell|{c.cell_id}|{tag}|k{kappa}"]["payload"]["methods"]["ref_valid"]["cost"]
        )
        repro_max = max(repro_max, float(np.abs(new - old).max()))

    rows = []
    for c in cells:
        res = copy.deepcopy(prows[f"cell|{c.cell_id}|{tag}|k{kappa}"]["payload"])
        twin = c.null_twin().cell_id
        res["null"] = copy.deepcopy(prows[f"null|{twin}|{tag}|k{kappa}"]["payload"])
        nf = st["null_fp"][f"{twin}|k{kappa}"]
        res["null"]["methods"]["ref_family"]["fp"] = [1] * nf["k"] + [0] * (nf["n"] - nf["k"])
        old = fa.classify_cell(res)  # cycle-3 R_valid classes (reproduced)
        res["methods"].update(done[f"cell|{c.cell_id}"]["payload"])
        res["null"]["methods"]["ref_valid2"] = done[f"twin|{twin}"]["payload"]["ref_valid2"]
        new = fa.classify_cell(res, valid_key="ref_valid2")
        pac = np.asarray(res["methods"]["hard_budget_pacing"]["cost"])
        best = np.asarray(res["methods"][new["best_safe"]]["cost"])
        pg = paired_ci(best - pac)  # >0: pacing cheaper than the best gated baseline
        rows.append(
            {
                "cell_id": c.cell_id,
                "old": old,
                "new": new,
                "pacing_vs_best_safe": {"mean": pg[0], "lo": pg[1], "hi": pg[2]},
                "pacing_cost": float(pac.mean()),
                "valid_cost": float(np.mean(res["methods"]["ref_valid"]["cost"])),
                "valid2_cost": float(np.mean(res["methods"]["ref_valid2"]["cost"])),
                "valid_promo_twin": int(sum(res["null"]["methods"]["ref_valid"]["fp"])),
                "valid2_promo_twin": int(sum(res["null"]["methods"]["ref_valid2"]["fp"])),
            }
        )
    nfk = {
        "k_valid": sum(done[f"nullfp|{t}"]["payload"]["k_valid"] for t in twins),
        "k_valid2": sum(done[f"nullfp|{t}"]["payload"]["k_valid2"] for t in twins),
        "n": sum(done[f"nullfp|{t}"]["payload"]["n"] for t in twins),
    }
    stored = {f["cell_id"]: f["label"] for f in st.get("failures", [])}
    mism = [
        r["cell_id"]
        for r in rows
        if r["cell_id"] in stored and stored[r["cell_id"]] != r["old"]["label"]
    ]
    return {
        "family": fam,
        "rows": rows,
        "nullfp100": nfk,
        "n_twins": len(twins),
        "repro_max_abs_diff": repro_max,
        "stored_label_mismatch": mism,
        "n_stored_failures": len(stored),
    }


def fmt(m, ci):
    return f"{m:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]"


def pct(k, n):
    r, lo, hi = wilson(int(k), int(n))
    return f"{r:.4f} ({int(k)}/{int(n)}, Wilson [{lo:.4f}, {hi:.4f}])"


def summarize(results: list[dict], wall: float) -> str:
    L = [
        "# Failure Atlas cycle 4: R_valid2 reclassification of the cycle-3 cells",
        "",
        (
            "Amendment 5 items 3-4. Development seeds only (discovery seeds 0..19 per cell, as in cycle 3). "
            "Descriptive; nothing here is confirmatory. Stored cycle-3 per-seed costs were reused; "
            "`ref_valid2` and `hard_budget_pacing` were rerun on the same cells and seeds; `ref_valid2` "
            "also on every null twin. `ref_valid` classes (`old`) are reproduced from the archive."
        ),
        "",
        f"Wall time of this run (rerun + reclassification): {wall:.0f} s.",
        "",
    ]
    for r in results:
        fam, rows = r["family"], r["rows"]
        L += [f"## Family {fam} ({len(rows)} cells, {r['n_twins']} null twins)", ""]
        mm = r["stored_label_mismatch"]
        L += [
            (
                f"Reproducibility check: max abs diff of rerun vs stored ref_valid per-seed cost on 4 cells = "
                f"{r['repro_max_abs_diff']:.2e}. Stored shared-failure labels reproduced: "
                f"{'yes' if not mm else 'MISMATCH ' + str(mm)} ({r['n_stored_failures']} stored)."
            ),
            "",
            "### Validity rates (null twins, any-promotion rate; alpha = 0.1)",
            "",
        ]
        k1 = sum(x["valid_promo_twin"] for x in rows)
        k2 = sum(x["valid2_promo_twin"] for x in rows)
        n = len(rows) * 20
        nf = r["nullfp100"]
        L += [
            f"- Pooled over cells, 20 discovery seeds (cell-weighted): R_valid {pct(k1, n)}; R_valid2 {pct(k2, n)}.",
            (
                f"- Distinct twins, 100 dedicated seeds (offset 5000): R_valid {pct(nf['k_valid'], nf['n'])}; "
                f"R_valid2 {pct(nf['k_valid2'], nf['n'])}."
            ),
            "",
            "### Class counts (cycle 3 with R_valid vs R_valid2)",
            "",
            "| class | R_valid (cycle 3) | R_valid2 |",
            "|---|---|---|",
        ]
        co = Counter(x["old"]["label"] for x in rows)
        cn = Counter(x["new"]["label"] for x in rows)
        for c in CLASSES:
            L.append(f"| {c} | {co.get(c, 0)} | {cn.get(c, 0)} |")
        L += ["", "### Transition table (rows: cycle-3 class, columns: R_valid2 class)", ""]
        tr = Counter((x["old"]["label"], x["new"]["label"]) for x in rows)
        cols = [c for c in CLASSES if cn.get(c, 0)]
        rws = [c for c in CLASSES if co.get(c, 0)]
        L.append("| old / new | " + " | ".join(cols) + " |")
        L.append("|" + "---|" * (len(cols) + 1))
        for a in rws:
            L.append(f"| {a} | " + " | ".join(str(tr.get((a, b), 0)) for b in cols) + " |")
        L += [
            "",
            "### Cells that become shared_failure or prior_gap (label changed vs cycle 3)",
            "",
        ]
        ch = [
            x
            for x in rows
            if x["new"]["label"] in ("shared_failure", "prior_gap")
            and x["new"]["label"] != x["old"]["label"]
        ]
        if ch:
            L.append(
                "| cell | old -> new | H vs R_family (95% CI) | H_valid2 (95% CI) | best_safe | pacing vs best_safe |"
            )
            L.append("|---|---|---|---|---|---|")
            for x in ch:
                nw, pb = x["new"], x["pacing_vs_best_safe"]
                L.append(
                    f"| {x['cell_id']} | {x['old']['label']} -> {nw['label']} | {fmt(nw['H'], nw['H_ci'])} | "
                    f"{fmt(nw['H_valid'], nw['H_valid_ci'])} | {nw['best_safe']} | "
                    f"{fmt(pb['mean'], [pb['lo'], pb['hi']])} |"
                )
        else:
            L.append("None.")
        L += ["", "### Shared failures under R_valid2 (all, including unchanged)", ""]
        sf = [x for x in rows if x["new"]["label"] == "shared_failure"]
        L.append(f"{len(sf)} cells (cycle 3: {co.get('shared_failure', 0)}).")
        for x in sf:
            nw = x["new"]
            L.append(
                f"- {x['cell_id']} (was {x['old']['label']}): H {fmt(nw['H'], nw['H_ci'])}; "
                f"H_valid2 {fmt(nw['H_valid'], nw['H_valid_ci'])}"
            )
        L += ["", "### hard_budget_pacing (ungated comparator)", ""]
        pb_win = sum(1 for x in rows if x["pacing_vs_best_safe"]["lo"] > fa.MATERIAL)
        pb_mean = float(np.mean([x["pacing_vs_best_safe"]["mean"] for x in rows]))
        L += [
            f"- Cells where pacing beats the best gated baseline by more than {fa.MATERIAL} (lower CI): {pb_win}/{len(rows)}.",
            f"- Mean (best_safe - pacing) cost over cells: {pb_mean:.4f}.",
            (
                f"- In shared_failure cells under R_valid2: pacing beats best_safe (lower CI > material) in "
                f"{sum(1 for x in sf if x['pacing_vs_best_safe']['lo'] > fa.MATERIAL)}/{len(sf)}."
            ),
            "",
        ]
        vc = np.mean([x["valid_cost"] for x in rows])
        v2c = np.mean([x["valid2_cost"] for x in rows])
        L += [f"Mean per-round cost over cells: R_valid {vc:.4f}, R_valid2 {v2c:.4f}.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    a.workers = max(1, min(a.workers, 6))
    OUT.mkdir(parents=True, exist_ok=True)
    meta = OUT / "timing.json"
    prev_wall = json.loads(meta.read_text())["wall_s"] if meta.exists() else 0.0
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for fam in (1, 2):
            results.append(process_family(fam, pool, a.workers))
    wall = prev_wall + time.time() - t0
    meta.write_text(json.dumps({"wall_s": wall}))
    (OUT / "summary.md").write_text(summarize(results, wall), encoding="utf-8")
    (OUT / "classes.json").write_text(
        json.dumps({r["family"]: r["rows"] for r in results}, default=float), encoding="utf-8"
    )
    print(f"done -> {OUT / 'summary.md'} wall {wall:.0f}s", flush=True)


if __name__ == "__main__":
    main()
