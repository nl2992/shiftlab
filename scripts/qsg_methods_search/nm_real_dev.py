"""Next-method development on the 14 EXPOSED real streams (counts for nothing in C4).

Reuses the C4-0 pilot driver (checksums, delays, episode/seed layout) with the next-method arm
set. Usage: python nm_real_dev.py run --out DIR --seeds 5 --seed-base 2026110961 --workers 20
"""

import c4_pilot
import next_method as nm

ARMS = (
    list(nm.WALD)
    + [f"dep_l0.9_g0.15_lr{a}_rp{b}" for a in (0.97, 0.99) for b in (5.0, 20.0)]
    + [
        "sgr_l0.9_g0.15_W150_z2.5_L20",
        "sgr_l0.9_g0.15_W150_z3.5_L0",
        "sgr_l0.9_g0.2_W150_z3.5_L20",
        "bocpd_h0.02_g0.2",
        "bocpd_h0.01_g0.1",
        "amb_l0.9_g0.15_m0.0_r1.0",
        "bpay_h0.002_g0.2",
        "EQSDp_l0.9_g0.2",
        "gongT_w100_m10",
        "qiu_delayed_movement",
        "CONTROL_never_switch",
    ]
)
c4_pilot.POLICIES[:] = ARMS
c4_pilot._extra = lambda: nm.EXTRA

if __name__ == "__main__":
    c4_pilot.main()
