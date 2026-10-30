# Development grid results (v2; development seeds only, nothing here is confirmation)

## H1: decision-gated ONS (17 configs × 2 label rates; `outputs/hg_v2/h1_dev_search.csv`, `h1_frontier_dev.csv`)
Fresh development seeds (dev worlds 40000+, G3 development stream 41000). Gate and ONS bet depend on resolved labels only, so the Objective-A (Brier) guarantee under H0-A with fixed delay is inherited; decision-awareness is empirical.

**Theory-threshold table (selected rows; harm power / benign FA / null FA / G3-dev power):**
| labels | arm | dev power | benign FA | null FA | G3-dev power |
|---|---|---|---|---|---|
| 10% | HG_unifcap | .579 | .032 | .010 | .229 |
| 10% | ONS | .681 | .090 | .025 | .338 |
| 10% | gated ONS hard w200 | .651 | .058 | .020 | .294 |
| 10% | gated ONS unc k2 | .642 | .052 | .010 | .271 |
| 10% | gated ONS soft a2 b0 | .643 | .049 | .005 | .265 |
| 20% | HG_unifcap | .849 | .097 | .005 | .510 |
| 20% | ONS | .838 | .143 | .030 | .517 |
| 20% | gated ONS hard w200 | .841 | .102 | .010 | .492 |
Gated ONS sits between HG and ONS: it recovers most of ONS's power with false alarms roughly halfway to HG's.

**Matched benign-FA frontier (thresholds swept; empirical operating points, forfeit the theory guarantee).** Best harm power with benign FA ≤ cap, null FA ≤ .07:
| labels | cap | HG_unifcap | ONS | disc_only | gONS hard200 | gONS soft2 | gONS unc2 | gONS multi |
|---|---|---|---|---|---|---|---|---|
| 10% | .02 | .464 | – | .352 | .481 | .453 | .461 | **.506** |
| 10% | .05 | .579 | .503 | .528 | .602 | **.643** | .603 | .608 |
| 10% | .08 | .688 | .641 | .642 | .651 | .685 | **.692** | .647 |
| 20% | .05 | .744 | – | – | **.777** | .735 | .738 | .762 |
| 20% | .08 | .812 | .751 | .737 | **.819** | .794 | .798 | .793 |

**Reading against the pre-registered selection rule (charter).** Rule (ii) — beat ONS at matched benign FA ≤ .05 by ≥ .03: **met** by all gated variants (10%: +.10 to +.14 at cap .05; at 20% ONS cannot reach the cap). Rule (i) — beat HG_unifcap by ≥ .03 in power at the theory threshold at both rates: met at 10% (+.05 to +.07), **not** at 20% (≤ −.01). Against HG at matched FA the gains are small and mixed (+.003 to +.064). So gated ONS is a modest, development-level improvement on ONS and approximately ties HG, not a clear advance over HG. Carried forward to the next stage: hard w200, soft a2 b0, unc k2, multi (30/200). No confirmation claim.
