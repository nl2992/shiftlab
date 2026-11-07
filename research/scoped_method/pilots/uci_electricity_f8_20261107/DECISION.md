# UCI Electricity F8 profile-screen decision

**Screen gate: FAIL.** The frozen 2011-fit / 2012-development screen evaluated 158 eligible client
series and found one F8-profile match (`MT_330`): 2.399% disagreement and 87.663% challenger
accuracy on disagreements. The protocol requires 20 matching clients before any policy replay.
Therefore no deployment-cost comparison was run and the 2013–2014 period remains unopened.

This is not evidence that the Failure Atlas F8 control fails in every application. It says this
particular, independently sourced client-load series and fixed HGB-versus-persistence pair do not
provide the predeclared breadth for a generalizable F8 validation study. Do not report the single
matching client as independent confirmation or change the gate post hoc.

The archive is officially described by UCI as 370 client series at 15-minute resolution, with
Portuguese local timestamps, zero-filled pre-entry histories for some clients, and daylight-saving
artifacts. Its archive checksum and exact partition boundaries are recorded in `RUN_STATUS.md` and
`DATASET_PROFILE.json`. Any later feedback delay would have to be simulated because the archive has
no release-time log. The 2011–2012 result is development evidence only; client series share common
time shocks and are not 158 independent source domains.

**Next action:** keep this source closed for the F8 candidate. Continue only with a separately
justified Failure Atlas mechanism and data source; do not expand the same fixed-pair search across
additional clients or time windows to chase a favorable profile.
