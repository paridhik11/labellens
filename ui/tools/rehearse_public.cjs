// Rehearsal of the public demo paths on a running server: every demo photo, then metoprolol questions on P3.
// One screenshot per step and a JSON table of seconds and what the page showed, written to OUT (outside the repo).
// Usage: PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 OUT=<folder> node ui/tools/rehearse_public.cjs [photo ...]
const fs = require('fs');
const os = require('os');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');
const ROOT = path.join(__dirname, '..', '..');
const BASE = (process.env.BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');
const OUT = process.env.OUT || path.join(os.tmpdir(), 'labellens_rehearse_public');
fs.mkdirSync(OUT, { recursive: true });
const PHOTOS = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync(path.join(ROOT, 'demo_photos', 'public')).filter((f) => /\.jpe?g$/.test(f)).sort();
const ODD = /Â|â€|�|undefined|NaN|\bnull\b|\[object/;

async function launch() {
  try { return await chromium.launch(); } catch (e) { return chromium.launch({ channel: 'chrome' }); }
}

async function openPublic(page) {
  await page.goto(`${BASE}/ui/public/index.html`);
  await page.waitForSelector('[data-testid="upload-photo"]', { timeout: 30000 });
}

/** What the visible page says, checked for problems a person would notice. */
async function look(page) {
  return page.evaluate((oddSrc) => {
    const odd = new RegExp(oddSrc);
    const text = document.body.innerText;
    const banners = (text.match(/Authenticity not verified\n/g) || []).length;
    return {
      banners,
      abstained: /Abstained/.test(text),
      percent: /\b\d{1,3}%/.test(text.replace(/\d{1,3}% \|/g, '')) && /Match: \d|Confidence: \d/.test(text),
      zero: /\b0%/.test(text),
      cfrLabel: /21 CFR [a-z]+\/[0-9-]+\/\d+/.test(text),
      odd: (text.match(odd) || [''])[0],
      title: (document.querySelector('.notice-title') || { innerText: '' }).innerText,
      text: text.slice(0, 4000),
    };
  }, ODD.source);
}

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

async function scanPhoto(page, file) {
  await openPublic(page);
  const t0 = Date.now();
  const [chooser] = await Promise.all([page.waitForEvent('filechooser'), page.click('[data-testid="upload-photo"]')]);
  await chooser.setFiles(path.join(ROOT, 'demo_photos', 'public', file));
  // a result: confirm panel, a live proposal, not identified, a retake, a failure or a review list
  const sel = '[data-testid="scan-confirm-panel"], [data-testid="live-proposal"], [data-testid="not-identified"], [data-testid="scan-failed"], [data-testid="retake"], .btn-select-candidate';
  await page.waitForSelector(sel, { timeout: 150000 });
  await page.waitForFunction(() => !document.querySelector('[data-testid="live-photo-searching"]'), null, { timeout: 60000 });
  const secs = (Date.now() - t0) / 1000;
  const kind = await page.evaluate(() => (['scan-confirm-panel', 'live-proposal', 'not-identified', 'scan-failed', 'retake'].find((t) => document.querySelector(`[data-testid="${t}"]`)) || 'review'));
  const title = await page.evaluate(() => { const t = document.querySelector('[data-testid="scan-confirm-panel"] .notice-title, [data-testid="live-proposal"] .notice-title, [data-testid="not-identified"] .notice-title, .notice-title'); return t ? t.innerText : ''; });
  const seen = await look(page);
  return { secs, kind, title, seen, shot: await shot(page, `photo_${file.replace(/\.jpe?g$/, '')}`) };
}

async function confirmAndShow(page, kind) {
  const t0 = Date.now();
  if (kind === 'scan-confirm-panel') await page.click('[data-testid="scan-confirm"]');
  else await page.click('[data-testid="live-confirm"]');
  await page.waitForSelector('#btnP2AskTeaser', { timeout: 300000 });
  return (Date.now() - t0) / 1000;
}

async function ask(page, medicine, question, name) {
  await page.click('.public-nav-btn[data-screen="P3 Ask about this label"]');
  await page.waitForSelector('#p3QuestionInput');
  if (medicine !== null) await page.fill('#p3Medicine', medicine);
  await page.fill('#p3QuestionInput', question);
  const t0 = Date.now();
  await page.click('#btnP3AskSubmit');
  await page.waitForSelector('[data-testid="closest-passages"], [data-testid="abstained"], [data-testid="answer"], [data-testid="no-label-loaded"]', { timeout: 120000 });
  const secs = (Date.now() - t0) / 1000;
  const r = await page.evaluate(() => ({
    kind: ['closest-passages', 'abstained', 'answer', 'no-label-loaded'].find((t) => document.querySelector(`[data-testid="${t}"]`)),
    head: (document.querySelector('[data-testid="closest-passages"] .font-semibold, [data-testid="abstained"] .notice-title, [data-testid="no-label-loaded"] .notice-title') || { innerText: '' }).innerText,
    sections: [...document.querySelectorAll('[data-testid="citation"] .font-semibold')].map((e) => e.innerText),
    quotes: [...document.querySelectorAll('[data-testid="citation"] [style*="italic"]')].map((e) => e.innerText.slice(0, 140)),
    details: (document.querySelector('[data-testid="answer-details"]') || { innerText: '' }).innerText,
  }));
  return { secs, ...r, seen: await look(page), shot: await shot(page, name) };
}

(async () => {
  const browser = await launch();
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const rows = [];
  for (const file of PHOTOS) {
    try {
      const r = await scanPhoto(page, file);
      const row = { step: `photo ${file}`, ...r };
      if (r.kind === 'scan-confirm-panel' || r.kind === 'live-proposal') {
        row.confirm_secs = await confirmAndShow(page, r.kind);
        row.after = await look(page);
        row.shot_after = await shot(page, `photo_${file.replace(/\.jpe?g$/, '')}_confirmed`);
      }
      rows.push(row);
      console.log(`${file}: ${r.kind} "${r.title}" ${r.secs.toFixed(1)} s${row.confirm_secs ? `, confirm ${row.confirm_secs.toFixed(1)} s` : ''}`);
    } catch (e) {
      rows.push({ step: `photo ${file}`, error: e.message.split('\n')[0], shot: await shot(page, `photo_${file.replace(/\.jpe?g$/, '')}_error`) });
      console.log(`${file}: ERROR ${e.message.split('\n')[0]}`);
    }
  }
  // metoprolol on P3: an unknown name first ("Pick a medicine first", DailyMed searched), then the picked label
  try {
    await openPublic(page);
    const first = await ask(page, 'metoprolol', 'how to store it', 'p3_metoprolol_pick_first');
    rows.push({ step: 'P3 metoprolol before a pick', ...first });
    console.log(`P3 metoprolol before pick: ${first.kind} "${first.head}"`);
    await page.waitForSelector('[data-testid="live-select"]', { timeout: 60000 });
    const t0 = Date.now();
    await page.click('[data-testid="live-select"]');
    await page.waitForSelector('#btnP2AskTeaser', { timeout: 300000 });
    rows.push({ step: 'P3 metoprolol pick and fetch', secs: (Date.now() - t0) / 1000, seen: await look(page), shot: await shot(page, 'p3_metoprolol_label') });
    for (const [q, n] of [['how to store it', 'store'], ['side effects', 'side_effects'], ['what is the capital of France', 'off_topic']]) {
      const r = await ask(page, null, q, `p3_metoprolol_${n}`);
      rows.push({ step: `P3 metoprolol "${q}"`, ...r });
      console.log(`P3 "${q}": ${r.kind} "${r.head}" ${r.secs.toFixed(1)} s; ${r.sections.slice(0, 2).join(' | ')}; ${r.quotes[0] || ''}`);
    }
  } catch (e) {
    rows.push({ step: 'P3 metoprolol', error: e.message.split('\n')[0], shot: await shot(page, 'p3_error') });
    console.log('P3 ERROR ' + e.message.split('\n')[0]);
  }
  // device photos on the Professional page: Add label, choose the file, Read label
  for (const file of fs.readdirSync(path.join(ROOT, 'demo_photos', 'device')).filter((f) => /\.(jpe?g|png|pdf)$/.test(f)).sort()) {
    try {
      await page.goto(`${BASE}/ui/pro/index.html`);
      await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'LIVE API', null, { timeout: 30000 });
      await page.click('[data-testid="step-add"]');
      await page.setInputFiles('#addFile', path.join(ROOT, 'demo_photos', 'device', file));
      const t0 = Date.now();
      await page.click('[data-testid="btn-read"]');
      await page.waitForSelector('[data-testid="read-result"], [data-testid="error-read"]', { timeout: 150000 });
      const secs = (Date.now() - t0) / 1000;
      const msg = await page.evaluate(() => { const e = document.querySelector('[data-testid="error-read"] .msg'); return e ? e.innerText : 'read: ' + [...document.querySelectorAll('[data-testid^="input-"]')].map((i) => `${i.dataset.testid.slice(6)}=${i.value}`).join(', '); });
      rows.push({ step: `device ${file}`, secs, msg, seen: await look(page), shot: await shot(page, `device_${file.replace(/\.[a-z]+$/, '')}`) });
      console.log(`device ${file}: ${secs.toFixed(1)} s; ${msg.slice(0, 160)}`);
    } catch (e) {
      rows.push({ step: `device ${file}`, error: e.message.split('\n')[0], shot: await shot(page, `device_${file}_error`) });
      console.log(`device ${file}: ERROR ${e.message.split('\n')[0]}`);
    }
  }
  await browser.close();
  const problems = rows.flatMap((r) => [r.seen, r.after].filter(Boolean).map((s) => [
    s.banners > 1 && 'duplicated banner', s.abstained && '"Abstained" shown', s.zero && '0% shown', s.cfrLabel && '21 CFR label-section citation', s.odd && `odd text "${s.odd}"`,
  ].filter(Boolean).map((p) => `${r.step}: ${p}`)).flat()).concat(rows.filter((r) => r.error).map((r) => `${r.step}: ${r.error}`));
  fs.writeFileSync(path.join(OUT, 'rehearse_public.json'), JSON.stringify({ base: BASE, at: new Date().toISOString(), problems, rows }, null, 1));
  console.log(problems.length ? 'PROBLEMS:\n' + problems.join('\n') : 'no visible problems found by the checks');
})();
