# Smart Control Tower: Architecture Plan

## Purpose

Keep the existing DFOS display for near-live shift monitoring, and add a private team workspace for daily analysis. The new workspace should help three named team members understand what changed, investigate likely causes, ask questions about the same DFOS data, and track actions through completion.

The photo shows existing Press Shop OEE, quality, and downtime views by cell. The new app should add history, evidence-led daily interpretation, and follow-through rather than duplicate those live screens.

## Recommendation

Build a continuing operational history and case-tracking workflow; daily insight is one output of that workflow. Every result should trace back to imported source rows, a reason classification, a saved report version, and any follow-up action. A standalone daily prompt or static HTML file is not enough to retain that history reliably.

For a quick start, backfill the usable historical reports into an approved shared repository, then append each new DFOS export. Claude Enterprise can help classify and explain patterns, but the team’s durable record must be the shared history and case/action log. If/when an app is built, use **Method 1: human uploads a daily DFOS export** first and keep the schema ready for **Method 2: a read-only DFOS API or database connection**. Both methods should use the same data model.

## Lower-hurdle pilot before a web app

If the client already approves Claude Enterprise for these DFOS files, use it as the first analysis workspace. This avoids a new host, app, database, API key, or deployment project:

1. Create a Claude for Work Project called **DFOS Daily Performance Review**. Set it private and invite only the three named members. Enterprise/Team project sharing supports named people and separate “Can use” or “Can edit” roles. Chats inside a project are not shared by default, so the project is the shared analysis workspace, not the team history log. [Project visibility and sharing](https://support.anthropic.com/en/articles/9519189-project-visibility-and-sharing)
2. Create the approved shared repository first: a raw-file folder plus a master data table, reason taxonomy/review table, versioned report register, issue/RCA register, action history, and effectiveness checks. An existing Microsoft/Google shared workspace may be enough for a pilot; use separate tables/tabs so source facts, normalized classifications, generated reports, and human decisions do not overwrite each other.
3. Backfill the five November 2025–March 2026 downtime reports as separate batches. Keep the September 2026 dashboard workbook as a separate time series unless the missing April–August history is obtained and the grains are reconciled.
4. Add project instructions with KPI definitions, machine/cell aliases, expected data grain, reason taxonomy, validation rules, report format, and RCA confidence rules. Keep stable definitions/SOPs in project knowledge; keep changing event data and action status in the repository.
5. On each new day, append the export to the master history and upload the relevant current and comparison-period data to a project chat. Claude supports CSV; XLSX upload requires the analysis tool to be enabled. [Supported file types](https://support.anthropic.com/en/articles/8241126-what-kinds-of-documents-can-i-upload-to-claude-ai)
6. Ask Claude to validate coverage and arithmetic, classify new free-text reasons without replacing the original values, compare with the correct baseline, and produce an evidence-linked report. Save each report version and link it to an issue/case. A human confirms root cause, assigns the action, and records whether it prevented recurrence.
7. Keep the existing DFOS screens for near-live monitoring. Use the project for AI-assisted analysis and the repository for team-visible history, decisions, actions, and results.

This can establish whether the history, RCA, and action workflow is valuable before building an app. It is not a DFOS-connected application: someone still transfers each new export into the repository and analysis chat. The repository—not private chat history—provides the shared record. The project owner should confirm Enterprise retention and sharing settings before the pilot.

If all three users later need automatic uploads, a shared question history, and live action updates in one interface, build the app only after the pilot proves those needs. A centrally hosted app still needs an approved host and access controls. A temporary app served from one person's PC only works while that computer is on and the local network permits access; avoid using that shortcut for operational data unless company policy allows it.

The files reviewed so far are not a continuous feed: five downtime reports cover November 2025 through March 2026, while the dashboard workbook has 500 data rows for September 1–28, 2026. These periods do not overlap. Backfill them as separate source batches and establish the missing April–August period or explicitly flag it as a history gap before calculating long-term trends.

## History-first operating model

The system of record is an append-only history, not a chat. Its minimum chain is:

**DFOS batch → normalized machine/time/reason records → daily report version → recurring issue/RCA case → action and effectiveness check.**

Keep the original values and the reviewed/normalized values side by side. For example, preserve the raw downtime reason and remark, then add a standard reason family, AI-suggested classification, confidence, reviewer, and review time. Never replace the source text with an AI rewrite.

Each upload should create an immutable batch record with its source filename, checksum, uploader, upload time, covered dates, rows accepted/rejected, validation warnings, and import status. A correction or re-upload creates a new version and marks the earlier batch as superseded; it must not silently overwrite history.

Each daily/weekly report should be saved as a versioned record with the source batch IDs, date window, filters, metric values, comparison baseline, evidence row IDs, insight text, prompt/model version, generation time, and human review status. This lets the team reproduce what the report said from the data available then.

Create a persistent issue/case when a pattern needs investigation. Link every related downtime event and report. Track recorded symptom/reason, likely cause, confirmed cause, evidence for confirmation, assigned corrective action, owner, due date, status changes, completion evidence, and a later effectiveness result such as whether the issue returned over the next defined number of production days.

Keep the AI question/answer as an interaction aid. If the answer creates a decision, copy the decision and its evidence into the versioned report or case record. This keeps useful work from disappearing in individual chat histories.

## Architecture

~~~mermaid
flowchart LR
  U[Three signed-in team members] --> W[Private web app]
  W -->|Method 1: upload Excel| V[Import and quality checks]
  F[DFOS API or read-only database view] -->|Method 2: scheduled read| V
  V --> R[(Raw file archive)]
  V --> D[(PostgreSQL: normalized history)]
  D --> C[Deterministic metrics and comparisons]
  C --> A[AI analysis and data Q&A]
  A --> I[Evidence-linked insights]
  I --> T[Shared action tracker]
  T --> L[(Audit and action history)]
~~~

The LLM is called by the server, never directly by the browser. The AI uses a small set of approved read-only application functions to retrieve metrics and source records. It does not receive an unrestricted database login or run arbitrary SQL. Each answer should show its date range, filters, source batch, supporting measure, and whether the explanation is a confirmed cause or a hypothesis to investigate.

## Two ways to bring DFOS data into the app

### Method 1 — Daily Excel upload (recommended MVP)

1. A user exports the daily DFOS data and uploads the workbook from the app.
2. The server checks the file type, expected columns, dates, row count, missing values, duplicate candidates, machine names, and time arithmetic.
3. The app previews the period and any warnings. The user confirms the import; invalid rows are rejected or marked for review rather than silently discarded.
4. The original file is retained with uploader, upload time, checksum, and import status. Parsed rows are stored in a shared database.
5. The metrics and daily insight run against the newly imported history. The team can ask questions and create tracked actions.

**Advantages:** quickest path, no DFOS integration permission required, simple to pilot with the available Excel exports.

**Trade-offs:** depends on a person uploading each day; missed or late uploads need to be visible. Re-upload handling must prevent duplicate data.

**MVP estimate:** about **10–15 developer days**, typically **2–4 calendar weeks** for one experienced full-stack developer, assuming access to a server, a stable export format, and timely review by the business and IT. See the effort breakdown below.

### Method 2 — Direct, read-only DFOS integration

1. DFOS owner/IT provides an approved API, export endpoint, or database view and documents its fields, refresh behavior, and access method.
2. A backend worker retrieves new or changed records on a schedule, or reads from a stable source view. Use a read-only identity and a watermark such as last updated time or source sequence.
3. The same validation, history tables, analytics, AI Q&A, and action tracker used in Method 1 process the incoming data.
4. The app shows last successful sync, records received, rejected records, and source freshness. Keep manual upload as a controlled fallback if desired.

**Advantages:** fewer manual steps and better daily continuity; can preserve the source’s three-minute refresh cadence if the DFOS source and business need support it.

**Trade-offs:** requires DFOS/IT cooperation, credentials, a stable interface, and a clear policy for corrections and historical changes. A screenshot or dashboard webpage is not a reliable data API.

**Incremental estimate:** about **5–10 developer days** if the source API/view is documented and accessible; **2–4+ weeks** if the interface, permissions, or source data semantics need discovery. Security review and access approval may add calendar time.

## Hosting choices for either method

| Hosting route | Good fit | Main components | Access |
|---|---|---|---|
| **Company intranet/on-premises server** | Data should stay inside the company network, or there is already a maintained internal server | App container/service, PostgreSQL, secured file archive, backup job, internal DNS/reverse proxy | Company LAN or VPN; use existing AD/Entra SSO or a trusted internal proxy. Do not expose an unauthenticated port to the internet. |
| **Private Azure deployment** | The company already uses Azure/Microsoft Entra and approves cloud processing | Azure App Service, Entra authentication, Azure Database for PostgreSQL, private Blob Storage, Key Vault for secrets, Application Insights/logging | Restrict sign-in to the approved Entra group. Use private networking if required by company policy. |

For an existing on-premises app that needs approved remote access, Microsoft Entra Application Proxy is one option; it provides authenticated access to internal applications through Entra. For an Azure-hosted app, App Service supports Entra authentication and access restrictions. These require IT configuration. [App Service authentication](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad) · [Entra Application Proxy](https://learn.microsoft.com/en-us/entra/identity/app-proxy/overview-what-is-app-proxy)

If the organization does not use Azure, use its approved identity provider and hosting platform instead. A managed service such as Supabase is another possible database/authentication option, but it is cloud-hosted and should be approved first. Enable and test row-level security and storage policies for every exposed table/bucket. [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) · [Supabase Storage access control](https://supabase.com/docs/guides/storage/security/access-control)

### Managed hosting platforms: Render, Vercel, and PythonAnywhere

These services can host the app without the team managing its own server. A URL on one of these providers is internet-reachable unless the hosting platform or application adds an access gate. A private source-code repository alone does **not** make the deployed app private.

| Platform | How to restrict the app to the three users | Fit for this project |
|---|---|---|
| **Render** | A normal web service has a public web endpoint, so implement individual sign-in and an email/account allowlist in the app. Render's private services are for communication between Render services; they are not directly reachable by the users' browsers. | Strong fit for the recommended Python FastAPI app and a managed PostgreSQL database. Keep database credentials server-side and restrict the database to the app. [Render service types](https://render.com/docs/service-types) · [Render private services](https://render.com/docs/private-services) |
| **Vercel** | Deployment Protection's Vercel Authentication can limit access to Vercel team members or approved share links. Password protection is a paid Pro feature or included in Enterprise. If the app calls a separate database/API, protect those endpoints too; protecting a page does not replace authorization at the data layer. | Good fit if the team is comfortable using Vercel accounts and the app is built with Next.js. The Python-first stack in this plan would need to change or use a separate Python API. [Vercel deployment protection](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments) |
| **PythonAnywhere** | The web app gets a normal `pythonanywhere.com` URL. Use Django's sign-in/permissions or implement authentication in Flask, then allow only the three named accounts. Do not treat an obscure URL or shared password as access control. | Straightforward for a small, all-Python Django/Flask app; less suitable if direct database/API integration or more complex background jobs are needed. Check current plan limits for outbound API access and scheduled tasks. [PythonAnywhere web app basics](https://help.pythonanywhere.com/pages/WebAppBasics) · [PythonAnywhere plans](https://www.pythonanywhere.com/pricing/) |

**Practical hosted choice:** Render + FastAPI + PostgreSQL, with individual app accounts restricted to the three users, is the closest match to the Python stack in this plan. Vercel is attractive if built-in deployment gating is the priority and the app is moved to Next.js. PythonAnywhere is a reasonable all-Python alternative, but its hosted URL still needs application sign-in.

Any managed host means the operational data is stored outside the plant network. Confirm that the company permits that before uploading real DFOS files. If no one can approve external hosting, use the lower-hurdle shared-folder pilot above until an approved host is available.

### Data approval is separate from app access

Restricting a Render/Vercel/PythonAnywhere app to three users prevents casual access; it does not mean the provider is approved to store company data. Treat daily production, rejection, downtime, machine, and action records as confidential operational data unless the company has classified them otherwise.

Claude Enterprise and Render have different purposes and data lifecycles. Anthropic says commercial-product inputs and outputs are not used for model training by default, and Enterprise includes custom retention controls; however, chats/files may remain in the product according to the configured retention. Render would be a separate provider holding the app database, imported history, and possibly uploaded originals, backups, and action log. Approval for uploading a workbook to Claude Enterprise does not automatically approve long-term storage in Render Postgres. [Anthropic training policy](https://privacy.anthropic.com/en/articles/7996868-is-my-data-used-for-model-training) · [Claude Enterprise features](https://support.anthropic.com/en/articles/9797531-what-is-the-claude-enterprise-plan) · [Anthropic retention overview](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)

Render documents encryption at rest for Postgres and TLS for external database connections, and provides database recovery/backups on eligible plans. Those are useful platform safeguards, but they do not replace company approval, app-level access control, retention rules, or secure application code. Render describes security as a shared responsibility. [Render Postgres encryption](https://render.com/docs/postgresql-creating-connecting) · [Render database recovery and backups](https://render.com/docs/postgresql-backups) · [Render security and trust](https://render.com/security)

If Render is approved, reduce the stored copy: keep the database private to the app service, use named user accounts, retain only the columns and history needed for analysis, avoid saving full file contents in logs or AI chats, and set a retention/deletion rule for original workbooks and backups. If Render is not approved, keep source data in the company-approved store and run the pilot locally; send only approved, minimized evidence to Claude Enterprise. A no-IT pilot can reduce the amount of new infrastructure, but it cannot itself approve an external data processor.

If the app should call Claude automatically, confirm API access separately. Claude for Work seats and API/Console usage are separate products and billing paths. [Anthropic API access and billing](https://support.anthropic.com/en/articles/9876003-i-subscribe-to-a-paid-claude-ai-plan-why-do-i-have-to-pay-separately-for-api-usage-on-console)

## Suggested MVP technology stack

| Layer | Recommended technology | Why |
|---|---|---|
| Web page | **Python FastAPI with Jinja2/HTMX**; Chart.js for charts | A simple interactive single-page experience without maintaining a separate frontend build. |
| Programming language | **Python** for the app, importer, metrics, and AI orchestration; small amounts of HTML/CSS/JavaScript for the UI | The Excel parsing and data analysis can share one codebase. |
| API | FastAPI REST endpoints, e.g. `/api/uploads`, `/api/insights`, `/api/ask`, `/api/actions` | Separates the browser from database and AI credentials; supports a future DFOS connector. |
| Excel import | `openpyxl` (and `pandas` only where useful) | Reads `.xlsx` exports and supports column/type validation. |
| Database | **PostgreSQL** | Shared durable store for uploaded history, metrics, conversations, and team actions. |
| Original files | Private filesystem volume on-prem, or private Azure Blob container in Azure | Retain the original export for review and reprocessing. |
| Authentication | Microsoft Entra ID/OIDC if available; otherwise the company’s existing SSO | Individual sign-ins and a three-person access group. Avoid homemade password handling. |
| AI | An IT-approved LLM API called only by the server; OpenAI Responses API with function calling if approved | Lets the model request approved queries while the application computes and returns the actual evidence. [Function calling](https://developers.openai.com/api/docs/guides/function-calling) |
| Secrets and logging | Environment/secret store; structured server logs; upload, insight, and action audit records | Keeps API keys off the browser and makes failures and user changes traceable. |

This stack keeps the UI intentionally modest. If the team prefers React or already has a standard frontend, React + TypeScript can replace Jinja/HTMX while keeping the same Python API and PostgreSQL design.

## Data model to start with

- **upload_batch:** file name, checksum, uploader, upload time, reported date range, record count, validation results, status.
- **downtime_event:** date, interval/shift, machine ID, model/SKU, available minutes, uptime, total/planned/unplanned downtime, reason, remark, source batch and row reference.
- **production_daily:** date, machine/cell, model, planned and actual production, rejections, availability, performance, quality, OEE, source batch.
- **machine_alias:** maps spelling/case variations to one canonical machine/cell; changes should be reviewable.
- **insight_run:** time window, filters, metric results, generated narrative, evidence references, model/prompt version, review status.
- **action_item** and **action_history:** linked insight/evidence, owner, due date, status, comments, and timestamped changes.
- **question_log:** user question, filters/date window, query/function calls, answer, and evidence references. Set an explicit retention policy.

Do not assume that date + hour + machine + model is a unique event key until the source grain is confirmed. Define and test the deduplication key with the DFOS owner.

## Daily insight and Q&A behavior

### Deterministic calculations first

Calculate totals, rates, rankings, and comparisons in Python/SQL. Examples:

- Top downtime minutes and reasons by cell, machine, model, and shift.
- Change against the previous comparable production day and a rolling baseline.
- Repeated machine/reason combinations and the contribution of each to downtime.
- Planned vs unplanned share, production/rejection changes, and OEE component movement.
- Missing reason, unusual volume, incomplete date coverage, or inconsistent time arithmetic.

Do not compare a partial current shift with a full previous day without labeling the comparison. Normalize machine-name variants before grouping. Show missing or invalid data as a quality warning, not as a confident insight.

### AI narration and questions

Give the model narrowly scoped application functions such as `get_daily_kpis`, `compare_periods`, `rank_downtime_reasons`, `get_machine_history`, and `get_quality_warnings`. Return a bounded result set with source dates and row references. The model can explain the observed pattern and suggest a check or action; the app must show the calculation and evidence used. Function calling is designed to connect models with application data and functions. [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)

Example questions:

- “What drove the increase in unplanned downtime for Cell 2 yesterday?”
- “Which machines had the same downtime reason on at least three days this week?”
- “Compare this model’s rejection rate and downtime with its last 10 production days.”
- “Show open actions related to press failures and whether the same reason returned.”

If the data only contains a free-text reason, the AI should call a repeated pattern a **likely cause to investigate**, not a confirmed root cause. Record a confirmed cause only after a person validates it or an additional source, such as a maintenance/work-order log, supports it.

## Privacy and security requirements

1. Allow access only to the three named people or a company-managed group; require sign-in for every app route and uploaded file.
2. Keep the AI key and database credentials on the server. Use read-only source credentials for a DFOS connection.
3. Restrict AI database access to approved, read-only application functions. Never pass unrestricted SQL execution to the model.
4. Keep uploaded files and database backups in private storage with retention and restore rules agreed with IT.
5. Log uploads, reprocessing, insight generation, question metadata, and action changes. Avoid logging secrets or unnecessary personal data.
6. Get company approval for any cloud hosting or AI provider. OpenAI states that API data is not used to train models by default, but abuse-monitoring logs may retain content for up to 30 days by default; confirm the organization’s current settings and requirements before sending production data. [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)

## Delivery plan and effort

Estimates assume one experienced developer working full time, a small three-person user group, and prompt access to a DFOS subject-matter reviewer. They exclude vendor/license costs and may shift after source discovery.

| Work | Method 1: upload MVP | Added for Method 2: direct integration |
|---|---:|---:|
| Confirm fields, grain, KPI definitions, and comparison rules | 1–2 days | 1–3 days if the source/API is undocumented |
| App shell, sign-in, database, private deployment | 2–3 days | Reuse MVP; add connector secret/configuration as needed |
| Import/connector, idempotency, and quality checks | 2–3 days | 3–6 days for a documented API/view; more if source discovery is needed |
| Daily metrics, insight page, charts, and evidence links | 2–3 days | Reuse MVP |
| Grounded AI Q&A and daily insight generation | 2–3 days | Reuse MVP; add source-specific tests |
| Action tracker, history, and audit trail | 1–2 days | Reuse MVP |
| Access review, backup/restore plan, user walkthrough | 1–2 days | 1–2 days for connector and sync-failure walkthrough |
| **Indicative total** | **10–15 developer days** | **5–10 additional developer days** with a ready source; **2–4+ weeks** if integration details are unknown |

Method 1 is about **2–4 calendar weeks** for one developer once the environment and reviewers are available. Method 2 is an incremental phase: roughly **1–2 additional calendar weeks** for a documented source, or longer when IT/source discovery is on the critical path. These estimates are for a usable internal pilot, not a plant-wide production rollout.

## First decisions for the project owner

1. Is the first release allowed to use a daily human-uploaded Excel file, or is direct DFOS integration required from day one?
2. Can IT provide an internal server and company SSO, or should the app use an approved Azure tenant?
3. What exactly is the source of truth: a DFOS API, a database view, the dashboard export, or a daily report workbook?
4. Which KPI definitions and comparison baseline should the daily insight use (shift/day, production days, previous comparable shift, or rolling period)?
5. Which AI provider is approved for this operational data, and what retention rules apply?

## Official references

- [Microsoft: Configure Entra authentication for Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad)
- [Microsoft: Entra Application Proxy overview](https://learn.microsoft.com/en-us/entra/identity/app-proxy/overview-what-is-app-proxy)
- [Supabase: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase: Storage access control](https://supabase.com/docs/guides/storage/security/access-control)
- [OpenAI API: Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI API: Data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
- [Microsoft: Power BI licenses for business users](https://learn.microsoft.com/en-us/power-bi/fundamentals/end-user-license)
