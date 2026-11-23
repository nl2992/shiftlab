"""Data and 3D assets for fig_overview (composed schematic).

Everything numeric is computed from the lattice solver (risk_budget_dp_fast, same cell as Fig. 4) or read from
docs/.../real_data/results/phase10c_baselines/tally.json.  Needs PYTHONPATH=src.

  landscape()  -> value surfaces W(beta, w) at t=1, n=B (adaptive and i.i.d.) from the solver tables Vup[t][n]
  rollout()    -> one simulated stream under the extracted RB-DP policy (the solver's own _Evaluator._decide,
                  same branching as _Evaluator._vertex); returns (beta_t, w_t) per round, queries and labels
  render_landscape(path) -> transparent 600-dpi PNG + projected 2-D anchor points (json) for the SVG labels
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LightSource
from mpl_toolkits.mplot3d import proj3d
from scipy.interpolate import RegularGridInterpolator
from shiftlab.paper4 import risk_budget_dp_fast as F
import lattice_data as LD
from style import RBDP

TALLY = RBDP / "real_data/results/phase10c_baselines/tally.json"
WMAX = 0.3  # show w in [0, 0.3]: the rollout lives at small w
T_SHOW, N_SHOW = 1, LD.B  # surface shown at t=1 with all B labels left


def landscape():
    res, N, C0 = LD.get()
    sc, si = res["causal"][0], res["iid"][0]
    assert np.allclose(sc.grid, si.grid)
    Wc_ = sc.Vup[T_SHOW][N_SHOW]  # (G, N+1): cost-to-go W(t, beta, n, w) from the Bellman tables
    Wi_ = si.Vup[T_SHOW][N_SHOW]
    assert Wc_.shape == (len(sc.grid), N + 1)
    assert np.all(Wi_ <= Wc_ + 1e-9)  # the i.i.d. null is the weaker constraint: lower cost-to-go
    Wc, Wi = C0 - Wc_, C0 - Wi_  # value of information (saving over never promoting), as in Fig. 4
    return dict(solver=sc, N=N, C0=C0, beta=np.asarray(sc.grid), w=np.arange(N + 1) / N, Wc=Wc, Wi=Wi, Wc_cost=Wc_)


def rollout(L, seed):
    """Execute the stored adaptive-mode policy; returns list of dict(t, beta, w, n, v, query, y, promote)."""
    s = L["solver"]
    N = s.N
    ev = F._Evaluator(s)
    rng = np.random.default_rng(seed)
    lo_idx, _ = s.root_indices()
    t, n, j, b = 1, s.cfg.B, lo_idx, float(s.beta1)
    steps = []
    while t <= s.cfg.T:
        dec = ev._decide(t, n, b)
        va, vb = int(dec["pv"][j]), int(dec["nv"][j])
        v = va if va == vb else (vb if rng.random() < (j - va) / (vb - va) else va)
        mp = dec["mp"]
        rec = dict(t=t, beta=b, w=j / N, n=n, v=v, query=False, y=None, promote=False)
        if v == N and dec["promote_n"]:
            rec["promote"] = True
            steps.append(rec)
            break
        if dec["q"] is not None and bool(dec["q"][v]):
            i0 = int(dec["w0"][v])
            i1 = min(N, 2 * v - i0)
            p1 = float(mp.p1[0])
            y = int(rng.random() < p1)
            rec.update(query=True, y=y)
            steps.append(rec)
            b = float((mp.b1 if y else mp.b0)[0])
            j = i1 if y else i0
            n -= 1
        else:
            steps.append(rec)
            b = float(mp.bn[0])
            j = v
        t += 1
    return steps


def pick_rollout(L, min_pts=4):
    """First seed (from 0) whose rollout makes B queries or promotes, visits >= min_pts distinct (beta,w) points."""
    for seed in range(500):
        st = rollout(L, seed)
        pts = {(round(r["beta"], 3), round(r["w"], 4)) for r in st}
        nq = sum(r["query"] for r in st)
        if nq >= 3 and len(pts) >= min_pts and len(st) >= 5:
            return seed, st
    raise RuntimeError("no suitable seed")


def tally():
    d = json.loads(TALLY.read_text())["new"]
    return d


def render_landscape(path, L, steps, size=(5.2, 4.4), elev=36, azim=-45, dpi=600, zoom=0.86):
    """Adaptive = opaque blue ramp (#CFE3F6 -> #3775BA); i.i.d. = sparse #B64342 wireframe over a 12% #F6CFCB fill.
    The rollout path itself is drawn in the SVG from the projected anchors (so it can carry arrowheads)."""
    beta, w, Wc, Wi = L["beta"], L["w"], L["Wc"], L["Wi"]
    cmap = LinearSegmentedColormap.from_list("blues", ["#CFE3F6", "#3775BA"])
    sub = np.unique(np.r_[np.arange(0, len(beta), 6), len(beta) - 1])
    wfull = w
    wk = w <= WMAX + 1e-12
    w = w[wk]
    Bg, Wg = np.meshgrid(beta[sub], w, indexing="ij")
    Zc, Zi = Wc[sub][:, wk], Wi[sub][:, wk]
    fig = plt.figure(figsize=size)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.set_proj_type("ortho")
    ls = LightSource(azdeg=300, altdeg=50)
    zmin, zmax = float(Zi.min()), float(Zc.max())
    zmax_i = float(Zi.max())
    ax.computed_zorder = False
    rgb_c = ls.shade(Zc, cmap=cmap, vert_exag=0.6, blend_mode="soft", vmin=float(Zc.min()), vmax=float(Zc.max()))
    ax.plot_surface(Bg, Wg, Zc, facecolors=rgb_c, rstride=1, cstride=1, linewidth=0.2, edgecolor=(1, 1, 1, 0.35),
                    antialiased=True, alpha=1.0, shade=False, zorder=1)
    ax.plot_surface(Bg, Wg, Zi, color="#F6CFCB", rstride=1, cstride=1, linewidth=0, antialiased=True, alpha=0.12,
                    shade=False, zorder=40)
    ax.plot_wireframe(Bg, Wg, Zi, rstride=max(1, Bg.shape[0] // 14), cstride=max(1, Bg.shape[1] // 5), color="#B64342",
                      linewidth=0.55, alpha=0.9, zorder=41)
    interp = RegularGridInterpolator((beta, wfull), Wc)
    pts = [(r["beta"], r["w"]) for r in steps]
    zs = [(b_, w_, float(interp([[b_, w_]])[0]) + 0.05) for b_, w_ in pts]
    path_xyz = []
    for (b0, w0), (b1, w1) in zip(pts[:-1], pts[1:]):
        for u in np.linspace(0, 1, 24):
            bb, ww = b0 + u * (b1 - b0), w0 + u * (w1 - w0)
            path_xyz.append((bb, ww, float(interp([[bb, ww]])[0]) + 0.05))
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlim(0, 1); ax.set_ylim(0, WMAX); ax.set_zlim(zmin - 0.05, zmax_i + 0.1)
    ax.set_box_aspect((1.0, 0.95, 0.52), zoom=zoom)
    ax.set_axis_off()
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    fig.canvas.draw()
    M = ax.get_proj()

    def proj(x, y, z):
        X, Y, _ = proj3d.proj_transform(x, y, z, M)
        px, py = ax.transData.transform((X, Y))
        W_, H_ = fig.canvas.get_width_height()
        return [float(px / W_), float(1 - py / H_)]

    ZI = RegularGridInterpolator((beta, wfull), Wi)
    zlo = zmin - 0.05
    anchors = dict(
        traj=[proj(*z) for z in zs],
        path=[proj(*z) for z in path_xyz],
        corner_b0w0=proj(0, 0, zlo), corner_b1w0=proj(1, 0, zlo), corner_b0w1=proj(0, WMAX, zlo),
        corner_b1w1=proj(1, WMAX, zlo),
        iid_b1=proj(1, 0.15, float(ZI([[1, 0.15]])[0])), iid_w1=proj(0.5, WMAX, float(ZI([[0.5, WMAX]])[0])),
        iid_b0=proj(0, 0.15, float(ZI([[0, 0.15]])[0])),
        ad_b1=proj(1, 0.15, float(interp([[1, 0.15]])[0])), ad_w1=proj(0.5, WMAX, float(interp([[0.5, WMAX]])[0])),
        ad_b0=proj(0, 0.15, float(interp([[0, 0.15]])[0])), ad_w0=proj(0.6, 0, float(interp([[0.6, 0]])[0])),
        iid_top=proj(*max(((b_, w_, float(ZI([[b_, w_]])[0])) for b_ in np.linspace(0, 1, 21) for w_ in np.linspace(0, WMAX, 7)), key=lambda t: t[2])),
    )
    fig.savefig(path, dpi=dpi, transparent=True)
    plt.close(fig)
    return anchors, (zmin, zmax)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp")
    L = landscape()
    seed, st = pick_rollout(L)
    print("seed", seed, [(r["t"], round(r["beta"], 3), r["w"], r["n"], r["v"], r["query"], r["y"], r["promote"]) for r in st])
    a, zr = render_landscape(out / "landscape.png", L, st, dpi=200)
    print(a, zr)
