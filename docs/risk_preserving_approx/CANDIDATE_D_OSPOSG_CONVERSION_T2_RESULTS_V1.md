# Candidate D OS-POSG conversion T=2 results (v1)

**Protocol:** `CANDIDATE_D_OSPOSG_CONVERSION_T2_PROTOCOL_V1.md`

**Run date:** 2026-10-29

**Status:** NO-GO; the registered comparison did not reach HSVI search.

The pinned parser accepted the compiled file and reported 65 states, 28
partitions, and 118 transitions, matching the compiler metadata. The independent
scalarized sequence-form LP was optimal at value `-1.0` (21 learner sequences,
5 null sequences, 39 flow nodes). HSVI presolve then terminated with
`KeyError: (1, 6, 1)`, so there is no lower/upper bound interval and no
containment result. This is a compiler/model-conformance failure under the
frozen v1 protocol; no threshold or parameter was changed.

**Diagnosis from the pinned source:** `presolve_LB` indexes the reward map for
every legal state/action pair. The compiled file omits zero-valued rewards, so
the terminal self-loop `(state=1, player1 action=6, player2 action=1)` has a
transition but no explicit zero reward. The upstream loader does not default
missing rewards to zero. This explains the exception but does not validate any
corrected conversion. Any repair must be separately versioned and preregistered.

**Reproduction:**

```powershell
$julia='C:\Users\nigel\AppData\Local\Programs\Julia-1.13.3\bin\julia.exe'
& $julia --project=.aris/runs/hsvi-osposg-upstream -e 'using HSVIforOSPOSGs; g=OSPOSG(".aris/runs/candidate_d_osposg_conversion_t2/switching.osposg"); h=HSVI(neighborhood=1e-8,presolve_epsilon=1e-8,presolve_time_limit=10.0); r=solve(g,h,1e-4,30.0); println("lower=",LB_value(g,h)); println("upper=",UB_value(g,h)); println("width=",UB_value(g,h)-LB_value(g,h)); println("exploration_count=",r.exploration_count);'
```

Pinned upstream checkout: `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`. Process
exit code was 1. The captured log is ignored at
`.aris/runs/candidate_d_osposg_conversion_t2/hsvi_20261029.log` (SHA-256
`82ba0eeb94129a7404a94fbc4a96d97a8002e5bdfb73497258513f237043dd30`); parser
log SHA-256 is
`d9220fb574043fbba47a6bf042c8786f4601170b4c4e40c491505698edb2fd25`.
The failed model is retained unchanged at
`.aris/runs/candidate_d_osposg_conversion_t2/switching.osposg` (SHA-256
`b0fd7020307b63ff8313589f3b33ecab2314f6989d2ef810486914bf066a9b37`). Compiler
SHA-256: `9e9377c3c2e1836aa184ff1f4a11b3402ac7266b3214360ffad5cfb1210cf7cc`.

No ShiftLab efficacy, runtime advantage, risk guarantee, baseline win or
real-data result follows from this failure. The next permitted step is a
separately registered diagnostic compiler revision that writes explicit zero
rewards for every legal state/action pair, followed by independent structural
validation before invoking HSVI.
