"""P2 harm-attribution confirmation on datasets never used by P2 (P2_HARM_CONFIRMATION_REGISTRATION.md).

Twin construction is the unchanged scripts/sota_sprint/twin_null.build (same model, 20 splits, 30% train window, T=2000,
<=20 episodes); only the loaders, delays and output directory differ. Conditions reuse p2_controls.transform unchanged.
Usage: p2_confirm.py check | build <outdir> | run <outdir> <cond> <policies> <seeds> [workers]
"""
import hashlib, io, json, sys, zipfile
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint")); sys.path.insert(0, str(HERE))
RAW = ROOT / "data/raw/p2_confirm"
DATASETS = ["tetouan_power", "steel_energy", "seoul_bike"]
SOURCES = {"tetouan_power": (849, "Tetuan City power consumption.csv"),
           "steel_energy": (851, "Steel_industry_data.csv"), "seoul_bike": (560, "SeoulBikeData.csv")}
RAW_SHA = {"tetouan_power": "3c4bf684161180937043a9fb65701a83d44b740b0d42f0492b6e7aec57ddbbfe",
           "steel_energy": "d82d28b33780ff1582507fcf08ae764ff648af459d58234370c551e62aadeaef",
           "seoul_bike": "139e9908f0a3544bb222386855c9ce107e96467306bb8e4ce936aab59e7baac4"}
DELAYS = {"tetouan_power": 144, "steel_energy": 96, "seoul_bike": 24}   # one day of natural time (10-min, 15-min, hourly)
CATEGORICAL = {"seoul_bike": ["Seasons", "Holiday"]}
CONDS = ["ORIG", "PERM", "BSWAP", "ESWAP"]


def _csv(name):
    uid, member = SOURCES[name]
    p = RAW / f"uci_{uid}" / "raw.zip"
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    assert h == RAW_SHA[name], (name, h)
    with zipfile.ZipFile(p) as z:
        return z.read(member)


def _cal(df, ts):
    df = df.copy(); df["hour"], df["weekday"], df["month"] = ts.dt.hour, ts.dt.weekday, ts.dt.month
    return df


def _sort(df, ts):
    o = np.argsort(ts.to_numpy(), kind="stable")
    return df.iloc[o].reset_index(drop=True), ts.iloc[o].reset_index(drop=True)


def load_tetouan_power():
    df = pd.read_csv(io.BytesIO(_csv("tetouan_power")))
    ts = pd.to_datetime(df.pop("DateTime"), format="%m/%d/%Y %H:%M")
    df, ts = _sort(df, ts)
    y = df.pop("Zone 1 Power Consumption").astype(float)
    df = df.drop(columns=[c for c in df.columns if "Power Consumption" in c])   # other zones: contemporaneous city load
    return _cal(df, ts), y, ts


def load_steel_energy():
    df = pd.read_csv(io.BytesIO(_csv("steel_energy")), encoding="utf-8-sig")
    ts = pd.to_datetime(df.pop("date"), format="%d/%m/%Y %H:%M")
    df, ts = _sort(df, ts)
    y = df.pop("Usage_kWh").astype(float)
    # CO2 is a fixed multiple of usage; power factors with reactive power determine kWh algebraically; Load_Type may be
    # defined from usage; WeekStatus/Day_of_week duplicate the calendar. Keep reactive powers, NSM and calendar.
    df = df.drop(columns=["CO2(tCO2)", "Lagging_Current_Power_Factor", "Leading_Current_Power_Factor", "Load_Type",
                          "WeekStatus", "Day_of_week"])
    return _cal(df, ts), y, ts


def load_seoul_bike():
    df = pd.read_csv(io.BytesIO(_csv("seoul_bike")), encoding="latin-1")
    df = df[df["Functioning Day"] == "Yes"].drop(columns=["Functioning Day"]).reset_index(drop=True)  # closed days: no rentals
    ts = pd.to_datetime(df.pop("Date"), format="%d/%m/%Y") + pd.to_timedelta(df.pop("Hour"), unit="h")
    df, ts = _sort(df, ts)
    y = df.pop("Rented Bike Count").astype(float)
    df.columns = [f"f{i}" if c not in CATEGORICAL["seoul_bike"] else c for i, c in enumerate(df.columns)]
    return _cal(df, ts), y, ts


LOADERS = {"tetouan_power": load_tetouan_power, "steel_energy": load_steel_energy, "seoul_bike": load_seoul_bike}


def check():
    for n, f in LOADERS.items():
        x, y, ts = f()
        print(n, x.shape, list(x.columns), "monotone", bool(ts.is_monotonic_increasing), "eps", min(20, (len(x) - int(.3 * len(x))) // 2000))


def build(out):
    import twin_null
    from p2_controls import transform
    out = Path(out); src = out / "twin_src"
    twin_null.LOADERS, twin_null.CATEGORICAL, twin_null.OUT = LOADERS, CATEGORICAL, src
    twin_null.DELAYS = DELAYS
    stats = {n: twin_null.build(n) for n in DATASETS}
    (src / "stats.json").write_text(json.dumps(stats, indent=1))
    man = {}
    for ci, cond in enumerate(CONDS):
        d = out / cond; d.mkdir(parents=True, exist_ok=True)
        for di, n in enumerate(DATASETS):
            z = np.load(src / f"twin_{n}.npz")
            rng = np.random.default_rng([20261108, di, ci])
            l0, l1 = (z["l0"], z["l1"]) if cond == "ORIG" else transform(z["l0"], z["l1"], cond, rng)
            np.savez(d / f"twin_{n}.npz", l0=l0, l1=l1, split=z["split"], ep=z["ep"])
            man[f"{cond}/{n}"] = dict(array_sha256=hashlib.sha256(l0.tobytes() + l1.tobytes()).hexdigest(), episodes=int(l0.shape[0]))
    (out / "build_manifest.json").write_text(json.dumps({"stats": stats, "files": man}, indent=1))
    print(json.dumps({n: {k: v for k, v in s.items() if k != "array_content_sha256"} for n, s in stats.items()}, indent=1))


def run(out, cond, policies, seeds, workers):
    import screen
    screen.FRESH_DELAYS.update(DELAYS)            # registered delays for the new datasets; screen.py itself unchanged
    screen.TWIN_DIR = Path(out) / cond
    screen.main(["--kind", "real", "--regimes", ",".join(f"twin_{d}" for d in DATASETS), "--policies", policies,
                 "--seeds", str(seeds), "--seed-base", "2026110820", "--workers", str(workers),
                 "--out", str(Path(out) / f"run_{cond}")])


if __name__ == "__main__":
    a = sys.argv
    {"check": lambda: check(), "build": lambda: build(a[2]),
     "run": lambda: run(a[2], a[3], a[4], int(a[5]), int(a[6]) if len(a) > 6 else 4)}[a[1]]()
