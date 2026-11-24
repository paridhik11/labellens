// Checks guessNames in ui/js/public-scan.js on recorded OCR lines (results/ndc_scan/lines_*.jsonl), no browser.
// Usage: node ui/tools/check_name_guess.cjs [--report]
// It reports, per set, how often the first guessed word is part of the pack's own product name (a proposal for the
// right medicine) and lists the photos whose first guess is another word (a possible wrong proposal; whether DailyMed
// lists a label for that word decides if anything would be shown).
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..', '..');
global.window = { LabelLensRenderers: {}, LabelLensData: { escapeHtml: (s) => String(s), CONFIG: { mode: 'api' } } };
global.document = { querySelectorAll: () => [] };
global.navigator = { userAgent: '' };
eval(fs.readFileSync(path.join(ROOT, 'ui', 'js', 'public-scan.js'), 'utf8'));
const { guessNames } = global.window.LabelLensPublicScan;
const failures = [];
const check = (name, ok) => { if (!ok) failures.push(name); };

// unit cases
const lopressor = [{ text: 'NDC 12345-678-90', confidence: 0.93 }, { text: 'Rx only', confidence: 0.96 }, { text: 'LOPRESSOR®', confidence: 0.92 },
  { text: '(metoprolol tartrate) Tablets, USP', confidence: 0.96 }, { text: '50 mg', confidence: 0.96 }, { text: 'Synthetic test image', confidence: 0.98 }];
const g = guessNames(lopressor);
check('LOPRESSOR first', g[0] === 'LOPRESSOR');
check('metoprolol second', g[1] === 'metoprolol');
check('salt and pack words dropped', !g.some((w) => /tartrate|tablets|synthetic|image/i.test(w)));
check('low-confidence lines ignored', guessNames([{ text: 'ZETIA', confidence: 0.5 }]).length === 0);

const report = process.argv.includes('--report');
const rows = [];
for (const set of ['unused_decoy', 'positives']) {
  const file = path.join(ROOT, 'results', 'ndc_scan', `lines_${set}.jsonl`);
  if (!fs.existsSync(file)) continue;
  const seen = new Set();
  for (const line of fs.readFileSync(file, 'utf8').split('\n').filter(Boolean)) {
    const r = JSON.parse(line);
    if (seen.has(r.id)) continue;
    seen.add(r.id);
    const words = guessNames(r.lines || []);
    const product = String(r.product || '').toLowerCase();
    const first = (words[0] || '').toLowerCase();
    rows.push({ set, id: r.id, product: r.product, words, own: first !== '' && product.split(/[^a-z]+/).includes(first) });
  }
}
for (const set of ['unused_decoy', 'positives']) {
  const rs = rows.filter((r) => r.set === set);
  if (!rs.length) continue;
  const own = rs.filter((r) => r.own).length;
  const none = rs.filter((r) => !r.words.length).length;
  console.log(`${set}: ${rs.length} photos, first guess is the pack's own name ${own}, no guess ${none}, other word ${rs.length - own - none}`);
  if (report) rs.filter((r) => !r.own && r.words.length).forEach((r) => console.log(`  other: ${r.product} -> ${r.words.join(', ')}`));
}
if (failures.length) { console.log('FAIL: ' + failures.join('; ')); process.exit(1); }
console.log('name-guess checks: all passed');
