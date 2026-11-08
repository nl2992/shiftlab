"""Stage-8 arms on the 14 EXPOSED real streams (development; same seeds as nm_real_dev)."""

import c4_pilot
import next_method as nm

c4_pilot.POLICIES[:] = list(nm.STAGE8) + ["wald_l0.97_g0.2"]
c4_pilot._extra = lambda: nm.EXTRA

if __name__ == "__main__":
    c4_pilot.main()
