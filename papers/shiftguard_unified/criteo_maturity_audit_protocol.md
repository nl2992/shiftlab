# Criteo Attribution label-maturity suitability audit

**Purpose:** decide whether the acquired Display Attribution dataset can
support a delayed-feedback sequential monitoring comparison during its
observed impression stream.

Use the pinned dataset release `c9a39688a4d56f404fb3` and its processed
`event_time`, `target` and `label_available_time` fields. The source README
describes 30 days of impressions and a 30-day conversion window. The local
adapter conservatively assigns every binary label availability to
`impression_time + 30 days`; that is a study assumption based on the
publisher's follow-up window, not a verified ingestion timestamp. Keep the
publisher-relative clock distinct from calendar time.

Stream only these three columns in Parquet row groups. Report observation
count, class counts, impression-clock span, the number and fraction of labels
that would mature by the last impression event, and the label-maturity curve
by event day. Never write impression-level records to the audit output.

Base the suitability decision on the observed maturity curve; do not encode a
generic minimum-feedback percentage. Report the fraction and class composition
of labels mature by the last impression event. If the observed curve leaves
too little within-stream feedback to compare monitoring methods informatively,
classify the dataset as unsuitable for that purpose under this 30-day rule. It
may remain useful for retrospective fixed-sample prediction or delayed-label
stress tests with an explicitly extended quiet follow-up period. Do not invent
model feedback or campaign counterfactual utility. The publisher's relative
timestamps do not establish actual real-time feature or label release.
