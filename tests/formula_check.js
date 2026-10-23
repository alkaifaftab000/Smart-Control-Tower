// Formula regression check: runs the dashboard's own formula code on a
// known dataset and compares against hand-verified results.
// Run: node tests/formula_check.js
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
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

console.log(failed ? `\n${failed} check(s) FAILED` : '\nAll formula checks passed');
process.exit(failed ? 1 : 0);
