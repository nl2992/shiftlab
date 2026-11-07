import numpy as np

from shiftlab.sota.challenger import *

rng = np.random.default_rng(0)
# stylised: n=1 sample/step, T=163400 steps (paper N_te), epochs N=500,1500,3500,7500,15500,31500,63500,127500 (paper schedule)
N = np.array([500, 1500, 3500, 7500, 15500, 31500, 63500, 127500.0])
ep = list(N)
T = 163400
g_star, g0, alpha = 0.05, 0.6, 0.5
G = g_star - g0 * N**-alpha


def reg(e, out_epoch, dec):
    vo = oracle_value(e, ep, G)[0]
    v = (
        e.v_switch(ep[out_epoch], G[out_epoch]) if dec == SWITCH else e.v_discard(ep[out_epoch]) * 0
    )  # discard => 0 relative
    return vo - v


# value relative to discarding-never? use V_ORACLE=max{0,max V_switch} as in paper; discard => 0 (paper normalises V_discard(0)=0 -> here V_discard(t_ALG)=-c n t)
def run(c, rho, sd, gam_gse, reps=2000):
    e = Economics(n=1, T=T, c=c)
    res = {k: [] for k in ["GSE_g", "GSE_small", "OSE4", "LSE", "LSEc"]}
    sw = {k: 0 for k in res}
    for _ in range(reps):
        gh = G + rng.normal(0, 1, len(N)) * sd / np.sqrt(rho * N)
        outs = {
            "GSE_g": run_gse(e, ep, gh, gam_gse, rho),
            "GSE_small": run_gse(e, ep, gh, 0.1, rho),
            "OSE4": run_ose(e, ep, gh, 3),
            "LSE": run_lse(e, ep, gh, variant="LSE", rho=rho),
            "LSEc": run_lse(e, ep, gh, variant="LSEc", gamma=0.1, rho=rho),
        }
        vo = oracle_value(e, ep, G)[0]
        for k, o in outs.items():
            v = (
                e.v_switch(ep[o.epoch_idx], G[o.epoch_idx])
                if o.decision == SWITCH
                else e.v_discard(ep[o.epoch_idx])
            )
            res[k].append(vo - v)
            sw[k] += o.decision == SWITCH
    e0 = Economics(n=1, T=T, c=c)
    return {
        k: (round(float(np.mean(v)), 1), round(sw[k] / reps, 2)) for k, v in res.items()
    }, oracle_value(e0, ep, G)


for c in (0.0025, 0.01):
    for sd in (1.0, 3.0):
        print("c", c, "noise_sd_const", sd, run(c, 0.5, sd, 1.92))
