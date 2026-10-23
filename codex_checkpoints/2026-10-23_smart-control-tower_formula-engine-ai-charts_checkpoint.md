# Smart Control Tower checkpoint

**Date:** 2026-10-23  
**Workspace:** `D:\HMC\Amber All\Soma ji\Smart Control Tower`  
**Live:** Vercel, deployed from `master` (last pushed commit `e97f285`)

## OEE formula engine (per the innovation head's sheet, `assets/formula_logic.png`)

- Availability = Σ Uptime ÷ Σ Available Minutes × 100
- Performance = Σ (Production × Ideal Cycle Time) ÷ Σ Uptime × 100, calculated as each row's system Performance % weighted by its uptime (the ideal cycle time is not in the files)
- Quality = (Σ Production − Σ Rejection Qty) ÷ Σ Production × 100, from the hourly rejection log
- OEE = A × P × Q ÷ 10000; Downtime = Available − Uptime; SPM = Actual ÷ Uptime; Plan fulfilment = Actual ÷ Plan (not Performance)
- Sums first, then ratios. Row percentages are never averaged.
- On each upload, every row's A, Q, OEE and downtime are recalculated and compared with the file (badge: "Formulas verified on N rows").

## Accuracy safeguards

- Files missing a required column are rejected with the column named; missing values show "—", never 0.
- Fixed header bugs: "Uptime (Mins)", "Downtime (Mins)" and "Model Name" were not recognised and were silently read as blank or 0.
- Percent columns are scaled to percent as a whole column, never per value (a real 0.27% availability is no longer read as 27%).
- `tests/formula_check.js` (run `node tests/formula_check.js`, 46 checks): header mapping, hand-checkable formula rows, missing-uptime handling, chart engine, day lock, percent parsing, and public/index.html matching index.html.
- Final verification: the real October files were uploaded through the app's own `loadFiles()` in headless Edge and compared with an independent openpyxl recalculation. Everything matched: totals, all 14 days, charts and tile baselines.

## AI insights tab (default tab)

- The AI never writes numbers. It returns chart requests (metrics, group_by, filters); `runChartSpec` and `oeeCalc` calculate the values. The same applies to the floating Ask AI chat; any chart block carrying AI-written datasets is refused.
- Daily analysis runs automatically once per day and file set (cached): bento tiles compared with the month average of earlier days and with the previous day (On track / Watch / Off track), 2 AI-chosen charts side by side, chart notes, Why/Action on Watch and Off-track tiles, and prioritised actions. This takes 2 AI calls.
- Follow-up "Ask for a chart" is locked to the selected day; trends run from the start of the month to the selected day.
- Monthly insight runs only from the Generate button.

## UI

- Top bar with the Amber logo, "Daily AI Insight · AI Assistance in Smart Control", and large AI insights / At a glance tabs. Sidebar shows upload, report status, file check and "Datasets used".
- Single "Upload files" button (per-report tabs and template downloads removed).
- Amber navy, red and gold theme, shaded buttons, loading skeletons, and the Amber star favicon.

## Deployment

- Vercel serves `public/index.html` and `public/assets/`; `vercel.json` rewrites `/api/*` to `api/index.py`, which imports `server.py`.
- Always run `cp index.html public/index.html` before committing (the test fails otherwise).
- The user runs `git push origin master` themselves. The repo contains client Excel files in `data/`; recommend keeping it private.

## October 1–19 results

- OEE 53.44% · A 69.25% · P 77.40% · Q 99.71% · Downtime 39,879 min · SPM 5.63 · Plan fulfilment 54.02% · Rejection rate 0.29%

## Open data issues sent to the client

Client doc: https://claude.ai/artifact/2Nqy6jtvHgymt4EM6pfQxL

1. Rejections: 212 pcs in the OEE report (Sheet1, Total row 318) vs 1,483 pcs in the hourly log. The OEE report shows 0 rejections on 9 of 14 days.
2. Performance is above 100% on 119 rows (32 models), with a maximum of 346.1% (Sheet1 row 246). The ideal cycle times are likely outdated.
3. PP-15 and PP-18 show 1,217–2,628 available minutes per shift (18 rows) against a 600-minute shift (08:30–18:30).
4. Downtime: 77% of minutes have no planned/unplanned flag, 32% have a blank reason, and 5% are "Others".
