// Formula regression check: runs the dashboard's own formula code on a
// known dataset and compares against hand-verified results.
// Run: node tests/formula_check.js
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'public', 'index.html'), 'utf8');
const pick = re => { const m = html.match(re); if (!m) throw Error('Code block not found: ' + re); return m[0]; };
eval(pick(/const aliases=\{[^;]*;/).replace('const ', 'var '));
eval(pick(/function averageReported[^\n]*/));
eval(pick(/function oeeCalc[^\n]*/));
eval(pick(/function validateOee[^\n]*/));
const key = s => String(s ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');

let failed = 0;
const check = (name, got, want, tol = 0.01) => {
  const ok = typeof want === 'string' ? got === want : Math.abs(got - want) <= tol;
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}: got ${typeof got === 'number' ? got.toFixed(2) : got}, expected ${want}`);
};

// 1. Every real header in the plant files must map to the right field
const headers = {
  'Uptime (Mins)': 'uptime', 'Downtime (Mins)': 'downtime', 'Available Minutes': 'available',
  'Plan Production': 'plan', 'Actual Production': 'actual', 'Rejections': 'reject',
  'Availability': 'availability', 'Performance': 'performance', 'Quality': 'quality', 'OEE': 'oee',
  'Total Downtime (mins.)': 'totaldown', 'Planned Downtime (mins.)': 'planned',
  'UnPlanned Downtime (mins.)': 'unplanned', 'Downtime Reason': 'reason',
  'Production': 'productionQty', 'Rejection Qty': 'reject', 'Machine Name': 'machine', 'Date': 'date',
  'Model Name': 'model', 'Model/SKU': 'model',
};
for (const [h, want] of Object.entries(headers))
  check(`header "${h}"`, Object.keys(aliases).find(f => aliases[f].includes(key(h))) || 'NOT MAPPED', want);

// 2. Hand-checkable rows (formula sheet: A = up/avail, P = prod*ICT/up, Q = (prod-rej)/prod, OEE = A*P*Q/10000)
//    Row 1: avail 380, up 232, plan 1900 (ICT 0.2 min), actual 1318, rej 11 -> A 61.05, P 113.62, Q 99.17, OEE 68.79
//    Row 2: avail 380, up 274, actual 1277, rej 3 -> A 72.11, P 93.21, Q 99.77, OEE 67.06
const rows = [
  { uptime: 232, available: 380, downtime: 148, plan: 1900, actual: 1318, reject: 11, availability: 61.05, performance: 113.62, quality: 99.17, oee: 68.79 },
  { uptime: 274, available: 380, downtime: 106, plan: 1900, actual: 1277, reject: 3, availability: 72.11, performance: 93.21, quality: 99.77, oee: 67.06 },
];
const k = oeeCalc(rows);
check('Availability = 506/760', k.availability, 100 * 506 / 760);
check('Performance = Σ(P×up)/Σup', k.performance, (113.62 * 232 + 93.21 * 274) / 506);
check('Quality = (2595-14)/2595', k.quality, 100 * (2595 - 14) / 2595);
check('OEE = A×P×Q/10000', k.oee, k.availability * k.performance * k.quality / 10000);
check('Downtime = 760-506', k.downtimeMin, 254);
check('SPM = 2595/506', k.spm, 2595 / 506);
check('Validation status', validateOee(rows).status, 'verified');

// 3. Missing uptime must give "no value", never 0%
const noUp = oeeCalc([{ available: 380, plan: 1900, actual: 1318, reject: 11 }]);
check('Missing uptime -> Availability not shown', String(noUp.availability), 'null');
check('Missing uptime -> OEE not shown', String(noUp.oee), 'null');

// 4. Wrong source percentages must be caught
const bad = rows.map(r => ({ ...r, availability: r.availability + 5 }));
check('Mismatched file is flagged', validateOee(bad).status, 'check');

// 4b. A real 0.27% must stay 0.27 (columns are scaled as a whole, not per value)
eval(pick(/function percentVal[^\n]*/));
check('Percent: 0.27 stays 0.27', percentVal(0.27), 0.27);
check('Percent: "61.05%" reads as 61.05', percentVal('61.05%'), 61.05);

// 5. On-demand chart engine: values must come from the same formulas
var state = {
  production: [
    { date: '2026-10-01', machine: 'PP-1', model: 'A', shift: 'Shift A', ...rows[0] },
    { date: '2026-10-01', machine: 'PP-2', model: 'B', shift: 'Shift A', ...rows[1] },
  ],
  downtime: [
    { date: '2026-10-01', machine: 'PP-1', reason: 'Dent', total: 100, planned: 0, unplanned: 100 },
    { date: '2026-10-01', machine: 'PP-1', reason: 'Dent', total: 48, planned: 0, unplanned: 48 },
    { date: '2026-10-01', machine: 'PP-2', reason: 'Punch broken', total: 106, planned: 6, unplanned: 100 },
  ],
  rejection: [
    { date: '2026-10-01', machine: 'PP-1', model: 'A', production: 1318, reject: 11, rejectionReason: 'Hamming NG' },
    { date: '2026-10-01', machine: 'PP-2', model: 'B', production: 1277, reject: 3, rejectionReason: 'Dent' },
  ],
  source: [],
};
var fmt = (n, d = 0) => Number(n || 0).toFixed(d), dateLabel = d => d;
var document = { getElementById: () => null, querySelectorAll: () => [] };
var switchMainTab = () => {}, generateMonthlyInsight = () => {}, generateDailyInsight = () => {}, refreshInsightSelectors = () => {};
eval(html.match(/<script id="aiChartsModule">([\s\S]*?)<\/script>/)[1]);

const byReason = runChartSpec({ metrics: ['downtime_min'], group_by: 'downtime_reason', filters: { date: '2026-10-01' } });
check('Chart: downtime by reason top label', byReason.chart.labels[0], 'Dent');
check('Chart: Dent minutes = 100 + 48', byReason.chart.datasets[0].data[0], 148);
const oeeByMachine = runChartSpec({ metrics: ['oee'], group_by: 'machine', filters: { date: '2026-10-01' }, sort: 'asc' });
const pp2 = oeeCalc([state.production[1]], [state.rejection[1]], []).oee;
check('Chart: lowest OEE machine first', oeeByMachine.chart.labels[0], 'PP-2');
check('Chart: machine OEE equals formula engine', oeeByMachine.chart.datasets[0].data[0], Math.round(pp2 * 100) / 100);
const top1 = runChartSpec({ metrics: ['downtime_min'], group_by: 'machine', filters: { date: '2026-10-01' }, top: 2 });
const topCut = runChartSpec({ metrics: ['downtime_min'], group_by: 'downtime_reason', filters: { date: '2026-10-01' }, top: 1 });
check('Chart: total counts all groups, not only shown ones', topCut.facts[0], 'Total: 254 min across 2 downtime reason value(s).');
check('Chart: machine total = 254 min', top1.facts[0], 'Total: 254 min across 2 machine value(s).');
const l1 = lockToDay({ metrics: ['oee'], group_by: 'machine', filters: { date: '2026-10-17' } }, '2026-10-19');
check('Day lock: other day forced to selected day', l1.spec.filters.date, '2026-10-19');
check('Day lock: user is told about the other day', String(l1.otherDay), 'true');
const l2 = lockToDay({ metrics: ['oee'], group_by: 'date', filters: { date_from: '2026-10-01', date_to: '2026-10-31' } }, '2026-10-19');
check('Day lock: trend ends on selected day', l2.spec.filters.date_to, '2026-10-19');
check('Day lock: trend starts at month start', l2.spec.filters.date_from, '2026-10-01');
check('Chart: unknown metric rejected', String(runChartSpec({ metrics: ['profit'], group_by: 'machine' }).ok), 'false');
check('Chart: reason grouping across reports rejected', String(runChartSpec({ metrics: ['oee'], group_by: 'downtime_reason' }).ok), 'false');
check('Chart: no matching rows rejected', String(runChartSpec({ metrics: ['downtime_min'], group_by: 'machine', filters: { date: '2030-01-01' } }).ok), 'false');

const l3 = lockToDay({ metrics: ['downtime_min'], group_by: 'machine', filters: { date_from: '2026-10-13', date_to: '2026-10-25' } }, '2026-10-19');
check('Range: "this week" keeps its start', l3.spec.filters.date_from, '2026-10-13');
check('Range: cut off at the selected day', l3.spec.filters.date_to, '2026-10-19');
check('Range: no other-day warning', String(l3.otherDay), 'false');
check('Hour label: "08:30:01 - 09:30:00"', hourLabel('08:30:01 - 09:30:00'), '08:30–09:30');

// 6. Frequency and weekly/monthly review engine, on a small hand-checkable week (Mon 5 Oct to Sun 11 Oct)
//    Downtime: PP-1 Dent on 5, 6, 7 Oct (30+20+10 min), PP-2 Punch on 7 Oct (40), PP-2 no reason on 8 Oct (15), PP-1 Dent 0 min on 8 Oct.
//    Rejection: part A on PP-1 rejected 2 of 100 (5 Oct) and 3 of 100 (6 Oct) for Burr; part B 0 of 200 (7 Oct). Rate = 5/400 = 1.25%.
const H = h => `${h}:30:01 - ${String(Number(h) + 1).padStart(2, '0')}:30:00`;
state.production = [];
state.downtime = [
  { date: '2026-10-05', hour: H('09'), machine: 'PP-1', reason: 'Dent', total: 30, planned: 0, unplanned: 30 },
  { date: '2026-10-06', hour: H('09'), machine: 'PP-1', reason: 'Dent', total: 20, planned: 0, unplanned: 20 },
  { date: '2026-10-07', hour: H('10'), machine: 'PP-1', reason: 'Dent', total: 10, planned: 0, unplanned: 10 },
  { date: '2026-10-07', hour: H('10'), machine: 'PP-2', reason: 'Punch broken', total: 40, planned: 0, unplanned: 40 },
  { date: '2026-10-08', hour: H('11'), machine: 'PP-2', reason: 'Unclassified', reasonWasBlank: true, total: 15, planned: 0, unplanned: 15 },
  { date: '2026-10-08', hour: H('11'), machine: 'PP-1', reason: 'Dent', total: 0, planned: 0, unplanned: 0 },
];
state.rejection = [
  { date: '2026-10-05', hour: H('09'), shift: 'Shift A', machine: 'PP-1', model: 'A', production: 100, reject: 2, rejectionReason: 'Burr' },
  { date: '2026-10-06', hour: H('10'), shift: 'Shift A', machine: 'PP-1', model: 'A', production: 100, reject: 3, rejectionReason: 'Burr' },
  { date: '2026-10-07', hour: H('11'), shift: 'Shift A', machine: 'PP-2', model: 'B', production: 200, reject: 0, rejectionReason: '' },
];
const hoursByMachine = runChartSpec({ metrics: ['downtime_hours'], group_by: 'machine', filters: { date_from: '2026-10-05', date_to: '2026-10-11' } });
check('Frequency: PP-1 has 3 hours with downtime (0-minute row not counted)', hoursByMachine.items.find(i => i.label === 'PP-1').values[0], 3);
const daysByMachine = runChartSpec({ metrics: ['downtime_days'], group_by: 'machine', filters: { date_from: '2026-10-05', date_to: '2026-10-11' } });
check('Frequency: PP-2 had downtime on 2 days', daysByMachine.items.find(i => i.label === 'PP-2').values[0], 2);
eval(pick(/function startOfWeek[^\n]*/));
eval(html.match(/<script id="reviewEngine">([\s\S]*?)<\/script>/)[1]);
const wk = rvWeeks(['2026-10-07', '2026-10-05', '2026-10-12']);
check('Week: Wednesday 7 Oct is in the week starting Monday 5 Oct', wk[0].key, '2026-10-05');
check('Week: ends on Sunday 11 Oct', wk[0].to, '2026-10-11');
check('Week: Monday 12 Oct starts a new week', String(wk.length), '2');
const rv = rvBuild('2026-10-05', '2026-10-11');
check('Review: top downtime reason is Dent', rv.downReasons[0].name, 'Dent');
check('Review: Dent = 30 + 20 + 10 min', rv.downReasons[0].value, 60);
check('Review: Dent in 3 hours', rv.downReasons[0].hours, 3);
check('Review: no-reason downtime is not ranked', String(rv.downReasons.some(x => x.name === 'Unclassified')), 'false');
check('Review: no-reason minutes = 15', rv.totals.noReasonMin, 15);
check('Review: rejection rate = 5 / 400', rv.totals.ratePercent, 1.25);
check('Review: part A rate = 5 / 200', rv.parts[0].ratePercent, 2.5);
check('Review: part B (no rejections) not listed', String(rv.parts.length), '1');
check('Recurring: PP-1 Dent on 3 of 4 days', `${rv.recurringDown[0].machine} ${rv.recurringDown[0].what[0]} ${rv.recurringDown[0].days}/${rv.recurringDown[0].workDays}`, 'PP-1 Dent 3/4');
check('Recurring: 3 of 4 days = almost every day', rv.recurringDown[0].howOften, 'Almost every day');
check('Recurring: one-day problems not listed', String(rv.recurringDown.length), '1');
check('Recurring: part A Burr on 2 of 3 days = every other day', rv.recurringRej[0].howOften, 'Every other day');
const h10 = rv.hours.find(h => h.hour === '10:30–11:30');
check('By hour: 10:30–11:30 rejection rate = 3 / 100', h10.ratePercent, 3);
check('By hour: 10:30–11:30 downtime = 10 + 40', h10.downtimeMin, 50);
check('Hidden facts found', rv.facts.map(f => f.key).join(','), 'hour_quality,hour_downtime,recurring_downtime,recurring_rejection,part_rate,no_reason');
check('Hidden fact: worst hour is 10:30–11:30', rv.facts[0].title, 'Rejections peak at 10:30–11:30');
state.rejection.push({ date: '2026-10-08', hour: H('22'), shift: 'Shift B', machine: 'PP-1', model: 'A', production: 300, reject: 0, rejectionReason: '' });
const rvB = rvBuild('2026-10-05', '2026-10-11');
check('Hidden fact: night shift with output but 0 rejections is flagged', String(rvB.facts.some(f => f.key === 'shift_no_rejections' && f.title.startsWith('Shift B'))), 'true');
check('Shift: Shift B made 300 pieces on 1 day', `${rvB.shifts[1].production}/${rvB.shifts[1].days}`, '300/1');

console.log(failed ? `\n${failed} check(s) FAILED` : '\nAll formula checks passed');
process.exit(failed ? 1 : 0);
