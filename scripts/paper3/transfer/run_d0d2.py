"""LOFO evaluation of D0 baselines, D1/D2 recommenders and D4 fallback on the J table (dev only)."""

import json
import time
from pathlib import Path

import pandas as pd

from shiftlab.paper3.transfer import data, streams, synth
from shiftlab.paper3.transfer import methods as M
from shiftlab.paper3.transfer.sim import GRID, SCENARIOS

OUT = Path("outputs/paper3/transfer")
LEDGER = Path("papers/paper3_cost_aware_adaptation/2026_programme/ledger/transfer.jsonl")
T = 2000


def ledger(rec):
    LEDGER.parent.mkdir(exist_ok=True, parents=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def main():
    recs = data.load_all()
    real = [r for r in recs.values() if r.real]
    syn = [r for r in recs.values() if not r.real]
    folds = [
        (f, [r for r in real if r.family == f], [r for r in real if r.family != f], syn, "real")
        for f in streams.DEV_FOLDS
    ]
    folds += [
        (f, [r for r in syn if r.family == f], real, [r for r in syn if r.family != f], "synth")
        for f in synth.FAMILIES
    ]
    rows = []
    for scope in ("all", "early"):
        for fold, test, trr, trs, kind in folds:
            t0 = time.time()
            ctx = M.build_ctx(trr, trs, scope)
            tf = {}
            for nm, fn in (("ridge", M.fit_ridge), ("gbdt", M.fit_gbdt), ("mlp", M.fit_mlp)):
                t1 = time.time()
                fn(ctx)
                tf[nm] = time.time() - t1
            ood = M.OOD(ctx)
            for r in test:
                for scn, costs in SCENARIOS.items():
                    x = data.embed(r, 0, r.n_early, costs)
                    ev = r.J[scn][r.n_early :].mean(0)
                    gf = M.global_fixed(ctx, scn)
                    sel = {
                        "global_fixed": gf,
                        "nearest_family_best": M.nearest_family(ctx, scn, x),
                        "per_stream_tuned": M.per_stream_tuning(r, scn),
                        "ess_heuristic": M.ess_heuristic(ctx, scn, x),
                        "hier_pool": M.hier_pool(ctx, r, scn),
                        "knn_meta_cusum_analogue": M.knn_meta(ctx, scn, x),
                        "D1_ridge": int(M.predict(ctx, "ridge", x).argmin()),
                        "D2_gbdt": int(M.predict(ctx, "gbdt", x).argmin()),
                        "D2_mlp": int(M.predict(ctx, "mlp", x).argmin()),
                    }
                    is_ood, dist = ood.is_ood(x)
                    for k in ("D1_ridge", "D2_gbdt", "D2_mlp"):
                        sel[k + "+ood"] = gf if is_ood else sel[k]
                    base = {
                        "scope": scope,
                        "fold": fold,
                        "kind": kind,
                        "stream": r.name,
                        "scenario": scn,
                        "n_eval": r.K - r.n_early,
                        "ood": bool(is_ood),
                        "ood_dist": dist,
                    }
                    n_replay = r.n_early * T
                    for m, th in sel.items():
                        replay = m in ("per_stream_tuned", "hier_pool")
                        rows.append(
                            dict(
                                base,
                                method=m,
                                theta=th,
                                J=float(ev[th]),
                                extra_labels=n_replay if replay else 0,
                                configs_tried=len(GRID) if replay else 1,
                            )
                        )
                    rows.append(
                        dict(
                            base,
                            method="hedge",
                            theta=-1,
                            J=M.hedge_expected_J(r, scn),
                            extra_labels=(r.K - 1) * T,
                            configs_tried=len(GRID),
                        )
                    )
                    rows.append(
                        dict(
                            base,
                            method="hindsight_oracle",
                            theta=int(ev.argmin()),
                            J=float(ev.min()),
                            extra_labels=0,
                            configs_tried=len(GRID),
                        )
                    )
                    rows.append(
                        dict(
                            base,
                            method="never_switch",
                            theta=-1,
                            J=float(r.never[r.n_early :].mean()),
                            extra_labels=0,
                            configs_tried=0,
                        )
                    )
            ledger(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "stage": "D0-D2-D4",
                    "scope": scope,
                    "fold": fold,
                    "kind": kind,
                    "n_test": len(test),
                    "n_train_real": len(trr),
                    "n_train_synth": len(trs),
                    "fit_seconds": tf,
                    "ridge_alpha": ctx.models["ridge_alpha"],
                    "ood_thr": ood.thr,
                    "wall_seconds": time.time() - t0,
                    "status": "dev_exploratory_only",
                }
            )
            print(scope, fold, round(time.time() - t0, 1), flush=True)
    pd.DataFrame(rows).to_csv(OUT / "d0d2_results.csv", index=False)


if __name__ == "__main__":
    main()
