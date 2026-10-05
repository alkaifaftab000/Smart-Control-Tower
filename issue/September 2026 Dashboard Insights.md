# September 2026 DFOS dashboard insights

## Executive summary

The dashboard contains **500 machine/model-day rows** for **23 dates** from September 1–28, 2026. Across those rows, recorded actual production was **787,413** against **1,412,542 planned** (a weighted plan attainment of **55.7%**). Recorded uptime was **132,072 minutes** out of **194,712 available**, giving **67.8% availability**; the remaining **62,640 minutes** are recorded downtime.

These are production and downtime-total findings only. This workbook has **no downtime-reason field**, so it cannot explain why the stops happened. The older reason-level downtime reports cover different dates and are not used in this analysis.

## Findings and suggested checks

### 1. September 22 and 24 stand out for lost time and low output attainment

| Date | Recorded downtime | Availability | Actual vs plan |
|---|---:|---:|---:|
| Sep 22 | 5,177 min | 52.6% | 32.6% |
| Sep 24 | 3,986 min | 47.0% | 47.2% |

**Suggested check:** review machine-level rows, production plan, and shift coverage for these dates. The export does not provide reasons, so treat this as a signal to investigate—not an explanation of cause.

### 2. Downtime is spread across several machines

| Machine as named in source | Downtime in September | Share of recorded downtime | Availability | Actual vs plan |
|---|---:|---:|---:|---:|
| Cell-3_PP -11-250Ton | 3,776 min | 6.0% | 44.6% | 48.3% |
| Cell-3 PP-29 (250 TON) | 3,458 min | 5.5% | 54.9% | 65.5% |
| Cell-1_PP-09-200Ton | 3,209 min | 5.1% | 40.9% | 42.0% |
| Cell-1_PP-20-200Ton | 3,117 min | 5.0% | 43.3% | 42.9% |
| Cell-3 PP-28 (315 TON) | 2,923 min | 4.7% | 54.0% | 58.6% |

The five highest-downtime machine labels account for about **26.3%** of the total, so the loss is not concentrated in just one machine. **Suggested check:** prioritize these machines for review, and confirm the machine-name mapping before comparing them with future downtime-reason exports.

### 3. One machine has planned output but no recorded production

`Cell-2_PP-23-110 Ton` has **10 rows** in this file: **11,347 planned**, **0 actual**, **0 uptime**, and **2,203 downtime minutes**.

**Suggested check:** confirm whether this machine was intentionally out of production, whether the plan was assigned correctly, and whether its production counter/data feed was working. Do not interpret the planned quantity as an achievable target until that is checked.

### 4. Availability improved slightly in the second half, but plan attainment did not

Comparing Sep 1–14 with Sep 15–28, weighted availability moved from **66.4% to 69.0%** (+2.6 percentage points), while plan attainment stayed nearly flat (**55.9% to 55.6%**).

**Suggested check:** after confirming product mix and plan definitions, investigate performance loss or cycle-rate assumptions. Higher uptime alone did not correspond to higher attainment in this comparison.

### 5. Rejections are concentrated on a few dates

The file records **164 rejections** against **787,413 actual production** (about **0.021%**, if both fields are counts of pieces). Sep 2 has 46, Sep 11 has 35, and Sep 3 has 30; together these dates account for **111 of 164** recorded rejections.

**Suggested check:** review the available part/model and machine rows for those dates and confirm the rejection field is complete. This file has no defect-reason detail, so it cannot identify the defect cause.

## Coverage and data checks

- Rows are at **date + machine + model** grain; there are 26 machine labels and 48 model labels.
- Five calendar dates have no rows: **Sep 5, 6, 13, 20, and 27**. Four are Sundays; confirm whether Sep 5 was a non-production day or a missing upload.
- No duplicate date + machine + model keys were found.
- For all 500 rows, uptime + downtime equals available minutes, and the source availability percentage agrees with uptime / available minutes.
- The source OEE formula agrees with its availability × performance × quality factors. However, **22 rows have OEE above 100%**, with a maximum of **209.86%**. Confirm the performance/cycle-time definition before using OEE for management targets or comparisons.
- The aggregate plan-attainment and rejection rates above are weighted from row totals. They can shift with model mix; confirm that planned and actual quantities are comparable across models.

## What this workbook can support

It can support daily monitoring of plan attainment, availability, downtime totals, recorded rejections, and machine/model outliers. It cannot support reason-level downtime insights for September or link September production losses to the November 2025–March 2026 reason history.

