"""One-time initialisation of confirmation_attempts.csv with the 7 legacy (Nov-9 doc 19/20) openings.

    python init_ledger.py --records <records_all.jsonl> --ledger docs/paper1_scale25/confirmation_attempts.csv

Legacy rows reserve indices 1..7 (conservative: they were opened, so under a strict reading they consume
alpha budget even though they were registered under a different protocol). r/L are computed retroactively
with certify.py for the doc-19 H1 contrast (EQ+pair vs EQ+cut) at alpha_i, for information only.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger as lg
from certify import alpha_i, paired_series, primary_lower

WINDOWS = {  # doc 20 section 2 order = index order
    "sf_311": "2025-07-01_2026-07-01",
    "dallas_311": "2025-07-01_2026-07-01",
    "kc_311": "2025-07-01_2026-07-01",
    "austin_311": "2025-07-01_2026-07-01",
    "cincinnati_311": "2025-07-01_2026-07-01",
    "dc_311": "2025-01-01_2026-01-01",
    "sandiego_311": "2025-01-01_2026-01-01",
}
REG_UTC = "2026-11-09T17:50:54Z"  # commit 1c5f2fdd (protocol locked), 12:50:54-05:00
OPEN_UTC = "2026-11-09T18:10:43Z"  # commit e1948471 (registration); policies ran after this, exact time not logged

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--ledger", required=True)
    a = ap.parse_args()
    if Path(a.ledger).exists():
        sys.exit("ledger exists; refusing to re-initialise")
    rec = pd.read_json(a.records, lines=True, dtype={"config_id": str}).drop_duplicates(
        ["stream", "ep", "seed", "config_id"]
    )
    for i, (ds, win) in enumerate(WINDOWS.items(), 1):
        g = lg.register_attempt(
            a.ledger,
            f"{ds}@fresh_{win}",
            ds,
            "P1-EQSDP-FRESH-DOC19",
            "EQ+pair vs EQ+cut (doc19 H1)",
            utc=REG_UTC,
            legacy=1,
            note="legacy: registered under doc 19 before this ledger existed; index reserved conservatively",
        )
        assert int(g["attempt_index"]) == i
        x, y = paired_series(rec, "P2_K2__E48_F60", "s2armr_H1100", ds)
        res = primary_lower(x, y, alpha_i(i))
        lg.record_open(
            a.ledger,
            i,
            res["r_hat"],
            res["L"],
            res["n"],
            res["block_len"],
            utc=OPEN_UTC,
            note="legacy; r/L retro-computed by certify.py (not registered); open time = earliest possible (commit e1948471)",
        )
        print(i, ds, round(res["r_hat"], 3), round(res["L"], 3), res["n"], res["block_len"])
