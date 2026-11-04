"""Descriptive: gap-indexed Markov persistence MLE (fam_a.rho_mle) of real disagreement-outcome signs.

    uv run python scripts/sota_sprint/real_persistence.py > docs/sota_sprint/validation/real_persistence.json
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "scripts/sota_sprint")
from fam_a import rho_mle  # noqa: E402

out = {}
for d in ["data/sprint_fresh_losses", "data/atlas_v2_losses"]:
    for f in sorted(Path(d).glob("*.npz")):
        z = np.load(f)
        rs, ps = [], []
        for e in range(z["l0"].shape[0]):
            D = z["l0"][e].astype(int) - z["l1"][e]
            t = np.flatnonzero(D != 0)
            if len(t) < 20:
                continue
            zz = (D[t] > 0).astype(int)
            rs.append(rho_mle(zz, t))
            ps.append(zz.mean())
        out[f.stem] = {"median_rho_hat_all_disagreements": float(np.median(rs)),
                       "mean_p_challenger_right": float(np.mean(ps)), "K": len(rs)}
print(json.dumps(out, indent=1))
