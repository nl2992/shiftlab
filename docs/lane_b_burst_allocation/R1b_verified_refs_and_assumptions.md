# R1b: verified references and declared assumptions (2026-10-28)

I closed the "needs a human" items from R1 with the built-in browser; none of the pages showed a
bot challenge. Receipts with rendered-text SHA-256 hashes are in
`<main>/data/raw/lane_b_external_refs_2026-10-28/browser_verification_receipts.json`, which is
gitignored.

## Verified against primary sources

| Item | Source | Verified statement |
|---|---|---|
| ENTSO-E load publication clocks | Reg. (EU) 543/2013 Art. 6(2), EUR-Lex | Actual total load is due no later than 1 h after the operating period. The day-ahead total-load forecast is due no later than 2 h before day-ahead gate closure in the bidding zone, and is updated when significant changes occur. |
| Binance spot fee | binance.com/en/fee/trading (rendered 2026-10-28) | Regular user: 0.100% maker and taker; 0.075% with the BNB discount. This is the current schedule. |
| OPSD German series | OPSD time_series field documentation | `DE_load_*` is the country-level "Total load in Germany … as published on ENTSO-E Transparency". `DE_LU_*` is the bidding zone. The 2018-10 zone split therefore does not change the `DE_load_*` definition. |
| OPSD attribution | OPSD data platform | Cite DOI 10.25832/time_series/2020-10-06. No explicit data licence is shown (site text is CC-BY). |

## Declared assumptions (the user asked for assumptions instead of further manual checks)

1. **A1, OPSD decision time.** The forecast is treated as available at D-1 10:00 UTC. Day-ahead
   gate closure for DE is 12:00 CET/CEST, so the regulatory deadline of 2 h before is 10:00
   local. Using 10:00 UTC is equal to or later than that deadline, so the clock is conservative.
2. **A2, OPSD vintage.** Values are the 2020-10-06 snapshot "as published". They may include later
   revisions rather than first releases.
   - **Mitigation:** candidate features use actual-load lags of at least 2 days.
   - **Disclosure:** revision look-ahead is a residual threat.
3. **A3, OPSD licence.** Research reuse with attribution is assumed permissible. The data stays out
   of Git, and only derived results are published.
4. **A4, Binance fee.** The 0.100% taker fee from the current schedule is applied to 2025–2026.
   The historical schedule is not verified, so this is an imposed cost with a documented source.
5. **A5, label costs.** Labels are free in both tasks. Query budgets and costs represent an imposed
   analyst-review capacity, and are not a measured cost.
