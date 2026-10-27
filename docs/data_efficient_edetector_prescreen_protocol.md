# WP3 predictable observation-control prescreen

**Status:** specification before any 590 block use, 2026-10-27. A follow-up commit
records this specification's hash. This is a small development screen, not confirmation.

## Target and proof

H=D-0.10 is paired decision harm, with pooled null E[H_t|past]<=0. Before observing
current X, choose intensity theta_t from past information and draw I_t using a fresh
uniform. When I=1, observe H (a label is needed only on disagreement); when I=0,
use factor 1. Selected agreements retain their known H=-0.10. Thus
E[I_t H_t|past]=theta_t E[H_t|past]<=0. The disagreement shortcut saves labels;
it does not remove agreement scores or condition the target on disagreement.
The deterministic cap stop occurs before current X if remaining dollars <2.5;
all subsequent factors equal 1. No DE-CuSum upward drift is added during a skip.

For every fixed start j, products of these factors are nonnegative supermartingales.
Mixing fixed stakes preserves that fact. A horizon H0=2400 has at most H0 starts;
the sum of terminal start processes has expectation at most H0. The nonnegative
submartingale-style SR recursion, or equivalently a stopped crossing argument for
the sum over starts, gives P(max SR>=H0/alpha)<=alpha. CUSUM is bounded by SR
pathwise. Threshold is 48000 at alpha=.05, not 20. A fixed convex mixture of
start-specific e-processes instead uses threshold 20. Skips advance calendar starts.
This is a standard composition, not a new e-detector validity theorem.

## Frozen experiment

Use boundary_local_harm, n=3200,d=16, fn=5,fp=1; train0–399,validation400–799,
monitor800–3199. Primary onset is 75% of the monitored horizon: absolute2600,
change_fraction=.8125. Secondary onset50%: absolute2000,change_fraction=.625.
Scheduled change is a synthetic positive control, not an inferred natural harm time.
Use all 20 seeds59000000–59000019 at each onset and budgets {.02,.05,.10,.20}.
Primary R6 is onset75%,budget.05; other seven cells are registered secondary cells.
The alternative generator is not a null calibration. No confirmation block is used.
Generate on CUDA, replay on CPU, using one common path and uniforms per seed/onset.
Source model/proxy fits and tariffs follow WP1. Dollar cap is
r*2400*mean(validation tariff); maximum tariff2.5 is reserved before each event.
All arms continue to horizon with factor-1 padding after stopping. Record hard caps,
actual dollars and labels; a shared cap does not establish equal realized resources.

## Observation policies, fixed before outcomes

Reuse the 200-event past-only DisagreementPacer from WP1. Its fixed pilot intensity
is the uniform baseline; its past-window intensity is the paced baseline. Both draw
I before current X. A temporal baseline multiplies paced intensity by .25 before
monitor index1200 and1.75 thereafter, clipping to [.01,1]. This baseline explicitly
gives a simple late-prior policy the same opportunity as adaptive control.

The candidate multiplies paced intensity by
`.25+3.75*clip((log(R_previous)-log(t+1))/log(20),0,1)`, clipping to [.01,1].
Here t is zero-based calendar index and R_previous is the candidate's fixed-stake
SR mixture on selected H/5.1; before the first event R=0 and the multiplier=.25.
This canonical controller never depends on which reported engine performs best.
All policies observe current disagreement/tariff only after selecting I, then update
their past-only pacer for the next event. No oracle field is a learner input.

## Matched and composed comparator panel

All four observation policies get identical detector/engine choices: fixed stakes
(.05,.1,.2,.4,.8,1) with equal weights, predictable plugin, Timans approximate GRAPA
and GRAPA via the verified shared replay. For fixed stakes, mix component SR/CUSUM
statistics; for adaptive engines, use their predictable one-step factors. Also report
fixed-start wealth and equal-weight starts {0,600,1200,1800}; unopened starts hold
wealth1. All skip gains are zero and every calendar start is retained.

Include WP1 uniform PPI, variance PPI/Xu, gated HT fixed/paced, gated PPI paced,
gated EB, and PPE/Xu source-factor aliases on this same late-onset path, with shared
adaptive betting replays wherever compatible. These use their proper propensity
correction and global predictable bounds; optional sampling is not substituted into
their published formulas. Fold their one-step evidence through SR/CUSUM and report
their fixed-start/started variants as well. Full-feedback is an unmatched upper reference.
Report label-free feature ADWIN separately as a feature-target sentinel; it cannot
establish decision harm. Standard subgroup composition has a different intersection
null: it is analytically tied to WP2's candidate and excluded from pooled-primary
ranking. Comparecast weak null, PPRM predictive risk and Q2 do not match this target;
record these exclusions in the report. No arm is dropped for poor outcomes.

## Gate and report

Primary candidate is the adaptive observation controller with fixed-stake SR.
At primary R6, compare with every applicable registered incumbent, including other
engine/detector choices for uniform/paced/temporal policies and the WP1 panel.
Advance only if against each incumbent it has >=10 percentage-point greater
post-onset detection OR >=1.5 ratio of incumbent/candidate mean censored delay,
and candidate uses no more mean labels or dollars. Pre-onset first alarms are failures;
nondetections get delay horizon-onset (600 primary,1200 secondary), including cap stops.
Require candidate detection no worse than -3 points against the strongest incumbent
in each other cell, again at no greater mean labels/dollars. Undefined delay ratios
cannot pass. Report Wilson95% detection intervals, paired differences/resources,
all arms/cells and criterion decisions. Twenty seeds cannot establish a confirmed win
or null validity; no confidence-bound advancement claim is made at this gate.

Prediction: no reliable primary advance against the complete composed panel;
the controller may conserve pre-onset labels but may fail to gather enough evidence
to increase intensity. A fail stops WP3 development and yields a ranked fallback
recommendation. Do not change intensity, clock, thresholds or cells after outcomes.
Every run records starting HEAD, source/output hashes, device, hardware and runtime.
PaperBanana is required for figures; tabular output is sufficient here.
