# Smart Control Tower checkpoint

**Date:** 2026-10-03  
**Workspace:** `D:\HMC\Amber All\Soma ji\Smart Control Tower`

## AI assistant pilot

- Added a floating **Ask AI** button and full-screen assistant to `prototype.html`, with a generated transparent cartoon avatar.
- The page summarizes the uploaded reports for AI context: totals, period trends, top reason/machine/model groupings, selected-day values, source coverage, and data-check examples. Raw workbook rows and downtime remarks are excluded. The summary can be previewed before sending.
- Added `ai_local_server.py`, using Python standard library only. It binds to `127.0.0.1`, injects a short-lived local request token, and serves only the dashboard and its two image assets.
- Provider keys are read from `.env` or process environment variables. `.env` is excluded by `.gitignore`; `.env.example` contains blank key fields.
- Provider fallback order is OpenAI → Mistral → Groq. Missing keys and HTTP 429 responses continue down the chain; other provider errors are returned.
- OpenAI uses the Responses API; Mistral and Groq use `/v1/chat/completions`. Groq defaults to `openai/gpt-oss-120b`. OpenAI requests set `store: false`; provider data handling still applies.
- Groq requests send an explicit `SmartControlTower-AI-Pilot/1.0` User-Agent; the default Python urllib signature was blocked by Groq's edge, while the explicit app User-Agent passed the live smoke check.
- Assistant replies are instructed to use compact Markdown sections and are rendered as safe DOM headings, lists, tables, and emphasis in the chat.
- Fallback answers end with a compact attribution, e.g. `🕶️ Answered by Groq · openai/gpt-oss-120b`.
- Start with `python ai_local_server.py` from the workspace, open the printed local URL, and press Ctrl+C to stop.

## Data and privacy boundary

- Dashboard data remains in the browser until a question is submitted. A submitted question sends grouped summaries and recent chat to the first available provider; inference is not local.
- `.env` holds local keys and must not be shared or committed. Both API key entries are currently blank pending replacement keys.

## Verification and security status

- Key-like values were found in `.env.example`; the sample file was reset to blanks, the two key values in `.env` were cleared, and `.env` is ignored by `.gitignore`. Revoke/rotate the exposed OpenAI and Mistral keys before use.
- Local fallback smoke tests are available in `test_ai_pilot.py` (5 routing tests pass). Latest live checks: OpenAI reports no credits remaining; Mistral reports rate limit exceeded; Groq passes with `openai/gpt-oss-120b` after setting the explicit app User-Agent.
