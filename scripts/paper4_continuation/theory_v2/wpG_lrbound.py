"""wpG: check Lemma P (t = 1): along every label path at most floor(B/2) of q_2..q_B exceed 1/2, and
max_y P_A(y)/Q*(y) <= (2(1-e))^floor(B/2), Q* = RIPr null p_i = min(q_i, 1/2).  Also E_A KL bound <= B I_e/2.
usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_lrbound.py OUT.json"""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
rows = []
for e in (0.02, 0.1, 0.2, 0.35):
    for B in range(1, 17):
        # forward over paths: arrays over prefixes of joint P(theta, y)
        w = np.array([[0.5, 0.5]])  # columns theta=0,1
        cnt = np.zeros(1); lr = np.ones(1); kl = np.zeros(1)
        for i in range(1, B + 1):
            # P(Y_i=1 | theta): S_i = theta for odd i, 1-theta for even i; P(Y=1|S=1)=1-e
            p1 = np.array([e, 1 - e]) if i % 2 == 1 else np.array([1 - e, e])
            pa = w.sum(1)
            q = (w * p1).sum(1) / pa
            up = q > 0.5 + 1e-12
            Ie = np.where(up, q * np.log(2 * q) + (1 - q) * np.log(2 * (1 - q)), 0.0)
            new_w = np.empty((2 * len(w), 2)); new_w[0::2] = w * (1 - p1); new_w[1::2] = w * p1
            r0 = np.where(up, (1 - q) / 0.5, 1.0); r1 = np.where(up, q / 0.5, 1.0)
            lr = np.stack([lr * r0, lr * r1], 1).ravel()
            cnt = np.repeat(cnt + up, 2)
            kl = np.repeat(kl + Ie, 2)
            w = new_w
        pa = w.sum(1)
        Ie_full = math.log(2) + (1 - e) * math.log(1 - e) + e * math.log(e)
        rows.append(dict(e=e, B=B, max_count=int(cnt.max()), floorB2=B // 2, max_lr=float(lr.max()),
                         lr_bound=(2 * (1 - e)) ** (B // 2), EKL=float((pa * kl).sum()), KL_bound=B * Ie_full / 2))
        r = rows[-1]
        assert r["max_count"] <= B // 2 and r["max_lr"] <= r["lr_bound"] * (1 + 1e-12) and r["EKL"] <= r["KL_bound"] + 1e-12, r
print("all", len(rows), "rows satisfy Lemma P bounds")
out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), rows=rows), indent=1))
print("wrote", out)
