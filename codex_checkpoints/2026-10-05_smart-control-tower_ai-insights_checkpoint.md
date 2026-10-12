# Smart Control Tower checkpoint

**Date:** 2026-10-05  
**Workspace:** `D:\HMC\Amber All\Soma ji\Smart Control Tower`

## AI insights and rejection upload update

- Added a top-level **AI insights** tab beside **At a glance** in `prototype.html`.
- Monthly insight generation starts when the AI tab is opened. Daily insight uses a selected date and an explicit generate action; Enter in the date picker is also supported.
- AI evidence is summarized in the browser before sending. Missing numeric measures remain unreported instead of being presented as zero. Prompts require evidence-led findings, practical actions, and historical-data caveats.
- Updated rejection upload feedback. If a file is already loaded under a different report type, or the selected report type does not match the tab, the notice now says what type is expected.
- The upload screenshots in `issue/2.png` show the rejection tab selected while the notice identifies `Downtime_Report_Dec'25(1 to 30).xlsx` as already loaded. That attempt did not load a rejection workbook. Choose a file from `data/Fw__REJECTION/` (October, November, or December 2025 rejection reports).
- Improved AI response rendering: wide Markdown tables become aligned cards; narrower tables stay contained within the insight panel; inline code and separators are rendered cleanly. The AI prompt asks for bullets instead of tables.
- Screenshots `issue/3.png` through `issue/5.png` show the prior wide-table overflow. The updated renderer prevents those response tables from widening the page.

## Verification status

- Parsed the inline JavaScript block successfully and checked that HTML IDs are unique.
- No live browser upload or new provider-generated response was run during this update. Confirm the rejection workbook upload and regenerate monthly/daily insights in the local dashboard when ready.

## Insight accuracy follow-up

- Compared the pasted December claims with the local workbooks: both reports contain December 1 records. December 1 rejection data show 20 rejects from 18,131 production (0.11031%); downtime data show 1,314 total minutes and 798 unplanned minutes. December 4 rejection data show 419 rejects from 82,277 production (0.50926%); downtime data show 5,240 total minutes and 321 unplanned minutes.
- The pasted daily AI answer is internally inconsistent: it says December 1 has no day-level figures, then uses December 1 values (20/18,131 and 798 unplanned minutes). It also reports 12–27 December coverage, while both workbooks contain records on 25 days from December 1–27.
- Tightened the AI prompt to keep daily metrics scoped to the selected date, distinguish source-file coverage from metric scope, avoid inventing targets/thresholds/owners/causes, and call rejection labels recorded reasons.
- Monthly totals and reason rankings should still be checked against the uploaded evidence before client use. Generated targets are proposals only unless the client has approved them.

## Scoped evidence and accuracy safeguards

- Updated `prototype.html` so monthly and daily AI requests receive calculated reason coverage, rejected-piece totals by reason, reason-by-machine/model combinations, downtime reason rankings by unplanned minutes / reported total minutes / row count, and scoped downtime reconciliation counts and sums.
- The AI evidence no longer uses the first 12 global upload warnings as if they describe the selected day or month. Blank downtime reasons retain a flag while displaying as `Unclassified`; zero remains a reported zero.
- The prompt tells the provider not to call piece counts occurrences, not to merge separate machine/reason rankings, and not to calculate an unplanned share when downtime fields do not reconcile.
- Added response safeguards: verification lines are replaced with a client-approved-baseline instruction, and downtime percentages are marked not reported when the selected evidence has reconciliation mismatches.
- Reconfirmed the supplied examples: Dec 2 rate is 35 / 39,936 = 0.08764%; 9 Hamming NG pieces occur in two rows; total / planned / unplanned downtime are 1,264 / 198 / 736 minutes, which do not reconcile. Dec 4 has 407 Damage pieces across labeled rows and 328 for Cell-1_PP-20-200Ton, not 347.
- The updated dashboard has not been run end-to-end with a live AI provider in this update. Reload the prototype, upload the December reports again, regenerate the December monthly insight, and regenerate the Dec 2 daily insight to review the new output.

## Accuracy architecture discussion

- Keep analysis for the selected day/month as fixed, deterministic app functions. The app calculates rates, reason-piece counts versus reason-row counts, reason × machine × model totals, downtime field reconciliation, and data coverage before sending a compact evidence package to AI.
- AI should explain checked facts and suggest qualitative first checks. It should not recalculate source figures, infer a cause, merge separate rankings, or invent action thresholds. Numeric findings should be validated against the calculated evidence before being shown.
- Do not add ChromaDB to solve numeric accuracy or aggregate spreadsheet rows. Consider it later as an optional search layer for longer free-text remarks, work orders, SOPs, or corrective-action notes. Current reasons are short labels with sparse coverage (December: rejection reasons 131/4,292 rows; downtime reasons 810/4,292 rows), so use exact groupings and a client-approved reason mapping first.
- Do not add an AI-generated-code step. The current monthly/daily workflow is a fixed sequence and does not need LangChain/LangGraph orchestration. For a later open-ended Ask AI experience, expose a small allowlist of static analysis tools (for example, daily summary, compare dates, reason breakdown); consider an agent/workflow framework only if branching, retries, durable state, or human approval steps become requirements.
- Current development direction: app calculates; AI explains. Team-shared persistence and an action register remain separate product steps from this local, session-only prototype.

## Monthly and daily top 10 evidence panels

- Added a shared `AI_TOP_REASON_LIMIT` of 10 for the AI evidence rankings.
- Added calculated top 10 rejection reasons, sorted by rejected pieces, with the number of source rows containing rejects and period reason coverage.
- Added calculated top 10 downtime reasons, sorted by unplanned minutes, with reported total minutes and source row count shown as separate measures. Downtime reconciliation totals/warnings appear below the rankings.
- Added responsive ranking panels below the AI narrative in both the monthly and daily sections of the AI insights tab. The panels are rendered from app calculations, so they remain useful if AI generation fails.
- Daily rankings clear when the selected date changes to avoid showing a prior day’s list under a new date. At a glance is unchanged.
- Live provider generation and visual browser review are still pending; reload the app and upload files again to see the panels because uploads are session-only.

## Follow-up check — October 5, 2026

- Parsed the page’s inline JavaScript with Node.js; syntax check passed.
- Ran focused checks against the extracted ranking and response-sanitizing helpers: rankings return the top 10 in descending order; incomplete downtime fields make unplanned-share calculations unsafe; the response guard removes downtime percentages in that case while preserving rejection-rate percentages; verification text no longer presents unsupported numeric targets.
- This check found and fixed a gap: the downtime percentage guard previously covered mismatched rows but not incomplete rows. It now covers either condition.
- Could not inspect the rendered dashboard or run a live monthly/daily AI request: no browser instance is available in this session. The end-to-end visual/provider check remains pending.

## Follow-up UI update — October 5, 2026

- Monthly and daily top 10 panels are now hidden while an AI request is running and appear only after the AI response has arrived. They are shown directly below the narrative as supporting evidence for the same review.
- Added a polished loading panel with an animated AI badge, moving progress indicator, and labeled analysis steps. It respects reduced-motion settings.
- Changing the selected month/day clears the prior result and invalidates an in-flight response, so older rankings cannot appear under a newly selected period.
- The evidence label states that rankings are calculated from the uploaded records and accompany the AI interpretation.
- No browser visual review or live AI request was available in this session; those remain the only end-to-end checks outstanding.
