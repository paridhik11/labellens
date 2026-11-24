// Live check of the photo name lookup (ui/js/public-scan.js guessNames + DailyMed search + namesWord) on recorded OCR
// lines of the scan evaluation photos that the scan itself did not identify. Needs a running server (BASE) with internet.
// Usage: BASE=http://127.0.0.1:8000 node ui/tools/check_photo_lookup_live.cjs [out.json]
// A proposal is "right" when the proposed DailyMed label shares a name word with the pack's own product name, "wrong"
// otherwise. Nothing is graded by hand; the pack names come from the evaluation records.
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..', '..');
const BASE = (process.env.BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');
global.window = { LabelLensRenderers: {}, LabelLensData: { escapeHtml: (s) => String(s), CONFIG: { mode: 'api' } } };
global.document = { querySelectorAll: () => [] };
global.navigator = { userAgent: '' };
eval(fs.readFileSync(path.join(ROOT, 'ui', 'js', 'public-scan.js'), 'utf8'));
const { guessNames, namesWord } = global.window.LabelLensPublicScan;

const words = (t) => String(t || '').toLowerCase().split(/[^a-z]+/).filter((w) => w.length >= 4);
const SALTS = new Set(['hydrochloride', 'tartrate', 'calcium', 'sodium', 'besylate', 'sulfate', 'hyclate', 'extra', 'strength', 'relief', 'childrens']);

async function search(word) {
  const r = await fetch(`${BASE}/public/live/search`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ product_name: word }) });
  return r.json();
}

(async () => {
  const final = new Map();
  for (const l of fs.readFileSync(path.join(ROOT, 'results', 'ndc_scan', 'final_rows.jsonl'), 'utf8').split('\n').filter(Boolean)) {
    const r = JSON.parse(l); if (!final.has(r.id)) final.set(r.id, r);
  }
  const rows = [];
  for (const set of ['unused_decoy', 'positives']) {
    const seen = new Set();
    for (const l of fs.readFileSync(path.join(ROOT, 'results', 'ndc_scan', `lines_${set}.jsonl`), 'utf8').split('\n').filter(Boolean)) {
      const r = JSON.parse(l);
      if (seen.has(r.id)) continue; seen.add(r.id);
      const f = final.get(r.id);
      if (!f || f.new.category === 'correct' || f.new.category === 'timeout' || !r.complete) continue; // only unidentified, fully read
      const guess = guessNames(r.lines || []);
      let proposal = null; let word = '';
      for (const w of guess) {
        const res = await search(w);
        if (res.outcome === 'unavailable') { console.log('DailyMed unavailable:', res.message); process.exit(2); }
        const list = (res.candidates || []).filter((c) => namesWord(c, w));
        if (list.length) { proposal = list[0]; word = w; break; }
      }
      const truth = new Set(words(r.product).filter((w) => !SALTS.has(w)));
      const pw = proposal ? words(`${proposal.product_name} ${proposal.generic_name || ''}`) : [];
      const verdict = !proposal ? 'none' : (pw.some((w) => truth.has(w)) ? 'right' : 'wrong');
      rows.push({ set, id: r.id, product: r.product, scan: f.new.category, guess, word, proposal: proposal ? proposal.title : '', verdict });
      console.log(set, verdict, r.product, '->', word, proposal ? proposal.title.slice(0, 70) : '');
    }
  }
  const sum = {};
  for (const r of rows) { sum[r.set] = sum[r.set] || { n: 0, right: 0, wrong: 0, none: 0 }; sum[r.set].n++; sum[r.set][r.verdict]++; }
  console.log(JSON.stringify(sum));
  if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify({ base: BASE, at: new Date().toISOString(), summary: sum, rows }, null, 1));
})();
