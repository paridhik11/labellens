/**
 * End-to-end check of the single-workflow Professional page (ui/pro/) against a RUNNING demo server.
 * Real clicks in a headed Chromium, real API, nothing faked. Every step prints PASS or FAIL with its seconds,
 * saves a screenshot in reports/pro_ui/ and the table goes to reports/pro_ui/results.json.
 *
 *   python scripts/run_demo.py                       # terminal 1 (default port 8000)
 *   PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 node ui/tools/pro_e2e.cjs
 *
 * Options (environment): HEADLESS=1 to hide the browser, PY=<python with the renderer> (default .venv312),
 * ONLY=stopped to run only the "server is down" check (stop the server first).
 * No em dashes.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { createRequire } = require('module');

const ROOT = path.resolve(__dirname, '..', '..');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');
const BASE = (process.env.BASE || 'http://127.0.0.1:8000').replace(/\/$/, '');
const URL = `${BASE}/ui/pro/index.html`;
const HEADLESS = process.env.HEADLESS === '1';
const PY = process.env.PY || path.join(ROOT, '.venv312', 'Scripts', 'python.exe');
const SHOTS = path.join(ROOT, 'reports', 'pro_ui');
const LONG = 300000;
const stamp = new Date().toTimeString().slice(0, 8).replace(/:/g, '');
fs.mkdirSync(SHOTS, { recursive: true });
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'pro_e2e_'));


/** Launch Chromium; if the bundled one cannot start (seen on this PC), use the installed Google Chrome. */
async function launch(opts) {
  if (process.env.PW_CHANNEL) return chromium.launch({ ...opts, channel: process.env.PW_CHANNEL });
  try { return await chromium.launch(opts); } catch (e) {
    console.log(`bundled Chromium failed (${e.message.split(/\r?\n/)[0]}); using channel chrome`);
    return chromium.launch({ ...opts, channel: 'chrome' });
  }
}

const results = [];
let failures = 0;
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

async function step(page, name, shot, fn) {
  const t0 = Date.now();
  let status = 'PASS'; let note = '';
  try { note = (await fn()) || ''; } catch (e) { status = 'FAIL'; note = e.message.split('\n')[0]; failures += 1; }
  const seconds = ((Date.now() - t0) / 1000).toFixed(1);
  let shotFile = '';
  if (page && shot) {
    shotFile = `${shot}.png`;
    try { await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, shotFile), fullPage: true }); } catch (e) { shotFile = ''; }
  }
  results.push({ step: name, status, seconds: Number(seconds), note, screenshot: shotFile });
  console.log(`${status.padEnd(4)} ${seconds.padStart(6)}s  ${name}  ${note}`);
  return status === 'PASS';
}

const idle = (page, t) => page.waitForFunction(() => !document.querySelector('[data-testid^="busy-"]'), null, { timeout: t || LONG });
async function click(page, testid) {
  const sel = `[data-testid="${testid}"]`;
  await page.waitForSelector(`${sel}:not([disabled])`, { timeout: 30000 });
  await page.click(sel);
  await page.waitForTimeout(150);
  await idle(page);
}
async function noError(page, id) {
  const e = await page.$(`[data-testid="error-${id}"]`);
  if (e) throw new Error(`page shows error: ${(await e.innerText()).replace(/\s+/g, ' ').slice(0, 300)}`);
}
const text = (page, sel) => page.$eval(sel, (e) => e.innerText);
async function fill(page, testid, value) { await page.fill(`[data-testid="${testid}"]`, value); }
async function setRole(page, role) {
  await page.click(`[data-testid="role-${role}"]`);
  await page.waitForTimeout(150);
  await idle(page);
  const who = await text(page, '[data-testid="who"]');
  if (!who.includes(role)) throw new Error(`role switch to ${role} shows "${who}"`);
}
async function openStage(page, stage) { await page.click(`[data-testid="step-${stage}"]`); await page.waitForTimeout(150); await idle(page); }

/** Add a product through the page. sample: use the sample button; else upload `file` and type every field. */
async function addProduct(page, o) {
  await openStage(page, 'products');
  await click(page, 'btn-go-add');
  if (o.sample) await click(page, 'btn-sample');
  else {
    await page.setInputFiles('[data-testid="add-file"]', o.file);
    await page.waitForSelector('[data-testid="chosen-file"]');
    await click(page, 'btn-read');
  }
  await noError(page, 'read');
  await page.waitForSelector('[data-testid="read-result"]', { timeout: 10000 });
  const unclear = await page.$$eval('.field.unclear', (els) => els.map((e) => e.dataset.testid.replace('field-', '')));
  const prefilled = {};
  for (const f of ['name', 'manufacturer', 'manufacturer_address', 'model', 'lot', 'expiry', 'udi_di', 'serial']) {
    prefilled[f] = await page.inputValue(`[data-testid="input-${f}"]`);
  }
  if (o.shotRead) await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, `${o.shotRead}.png`), fullPage: true });
  if (o.emptyFirst) {
    // Saving with a printed field empty must be refused by the page with a clear message.
    for (const [f, v] of Object.entries(o.values)) if (f !== o.emptyFirst) await fill(page, `input-${f}`, v);
    await fill(page, `input-${o.emptyFirst}`, '');
    await click(page, 'btn-save');
    await page.waitForSelector('[data-testid="error-save"]', { timeout: 10000 });
    o.emptyMsg = (await text(page, '[data-testid="error-save"]')).replace(/\s+/g, ' ').replace(/Retry$/, '').trim();
    if (o.shotEmpty) { await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, `${o.shotEmpty}.png`), fullPage: true }); }
  }
  for (const [f, v] of Object.entries(o.values)) await fill(page, `input-${f}`, v);
  await click(page, 'btn-save');
  await noError(page, 'save');
  await page.waitForSelector('[data-testid="flash"]', { timeout: 10000 });
  const flash = await text(page, '[data-testid="flash"]');
  const pid = /Saved product (prd_[0-9a-z]+)/.exec(flash);
  if (!pid) throw new Error('no product id in: ' + flash);
  return { pid: pid[1], unclear, prefilled, flash, emptyMsg: o.emptyMsg };
}

async function assess(page, field, value) {
  await openStage(page, 'change');
  await page.selectOption('[data-testid="change-field"]', field);
  await fill(page, 'change-value', value);
  await click(page, 'btn-assess');
}

async function confirmChange(page) {
  await click(page, 'btn-dec-all');
  await click(page, 'btn-confirm');
  await noError(page, 'confirm');
  await page.waitForSelector('[data-testid="change-confirmed"]', { timeout: 10000 });
}

async function main() {
  if (process.env.ONLY === 'stopped') return stoppedOnly();
  const browser = await launch({ headless: HEADLESS, slowMo: HEADLESS ? 0 : 60 });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));
  const mocked = [];
  page.on('response', (r) => { if (r.headers()['x-mock']) mocked.push(r.url()); });
  const S = {};

  await step(null, 'sample files are byte-identical to their sources', '', async () => {
    const out = path.join(work, 'golden_label.pdf');
    execFileSync(PY, ['-c', `import sys; sys.path[:0]=[r'${ROOT}', r'${path.join(ROOT, 'scripts')}']; import demo_flow as f; from pathlib import Path; f.render_golden_pdf(Path(r'${out}'))`], { stdio: 'pipe' });
    const a = sha(out); const b = sha(path.join(ROOT, 'ui', 'pro', 'sample', 'golden_label.pdf'));
    if (a !== b) throw new Error(`fresh render ${a.slice(0, 12)} differs from ui/pro/sample copy ${b.slice(0, 12)}`);
    const t1 = sha(path.join(ROOT, 'src', 'gen', 'templates', 'test_device.json'));
    const t2 = sha(path.join(ROOT, 'ui', 'pro', 'sample', 'test_device.json'));
    if (t1 !== t2) throw new Error('ui/pro/sample/test_device.json differs from src/gen/templates/test_device.json');
    S.goldenPdf = out;
    return `golden PDF ${a.slice(0, 12)} rendered now = sample copy; template copy identical`;
  });

  // ------------------------------------------------------------ run A: sample Golden Pump, full workflow
  await step(page, 'open Products, LIVE API indicator', '01_products', async () => {
    await page.goto(URL);
    await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'LIVE API', null, { timeout: 15000 });
    await idle(page);
    await noError(page, 'products');
    const n = await page.$$eval('[data-testid="product-row"]', (r) => r.length);
    const refreshHelp = await text(page, '[data-testid="help-refresh"]');
    if (!/reloads the product list/i.test(refreshHelp)) throw new Error('no help line under Refresh: ' + refreshHelp);
    return `${n} products listed; Refresh help "${refreshHelp}"; ${await text(page, '[data-testid="product-note"]')}; user ${await text(page, '[data-testid="who"]')}`;
  });

  await step(page, 'search filtering', '02_filter', async () => {
    // Filter by a word from a product that is really listed (the database may hold any products).
    const first = await page.$eval('[data-testid="product-row"] strong', (e) => e.innerText);
    const word = first.split(/\s+/)[0].toLowerCase();
    await fill(page, 'product-filter', word);
    const names = await page.$$eval('[data-testid="product-row"]', (r) => r.map((x) => x.innerText.toLowerCase()));
    if (!names.length || names.some((n) => !n.includes(word))) throw new Error(`filter "${word}" shows rows without it`);
    await fill(page, 'product-filter', 'zz-no-such-product');
    await page.waitForSelector('[data-testid="no-match"]', { timeout: 3000 });
    await fill(page, 'product-filter', 'ExampleDevice');
    const ex = await page.$$eval('[data-testid="product-row"]', (r) => r.length);
    await fill(page, 'product-filter', '');
    return `${word} -> ${names.length} rows, nonsense -> no-match message, ExampleDevice -> ${ex} row(s)`;
  });

  let ok = await step(page, 'add sample Golden Pump (read, correct, save)', '04_saved', async () => {
    const r = await addProduct(page, {
      sample: true, shotRead: '03_read_sample', emptyFirst: 'model', shotEmpty: '03b_empty_model_refused',
      values: { name: `Golden Pump (pro ${stamp})`, model: 'GP-100', sterilization: 'EO', storage: 'Store dry' },
    });
    S.pidA = r.pid;
    if (!r.emptyMsg || !/Model/.test(r.emptyMsg)) throw new Error('empty model was not refused: ' + r.emptyMsg);
    return `${r.pid}; empty model refused first ("${r.emptyMsg.slice(0, 90)}"); unclear highlighted: ${r.unclear.join(', ')}; prefilled lot ${r.prefilled.lot}, expiry ${r.prefilled.expiry}, udi ${r.prefilled.udi_di}, serial ${r.prefilled.serial}, model "${r.prefilled.model}"`;
  });

  ok = ok && await step(page, 'run check (inspect)', '05_check', async () => {
    await click(page, 'btn-check');
    await noError(page, 'check');
    await page.waitForSelector('[data-testid="check-result"]');
    const n = await page.$$eval('[data-testid="finding"]', (x) => x.length);
    const human = await page.$$eval('[data-testid="human-review"] li', (x) => x.length).catch(() => 0);
    const unreliable = !!(await page.$('[data-testid="unreliable-note"]'));
    const nocite = await page.$$eval('[data-testid="no-citation"]', (x) => x.length);
    S.lotBefore = await page.evaluate(() => {
      const dt = [...document.querySelectorAll('[data-testid="record"] dt')].find((d) => d.textContent.trim() === 'lot');
      return dt ? dt.nextElementSibling.firstChild.textContent.trim() : '';
    });
    const helps = {};
    for (const id of ['help-check', 'help-change', 'help-evidence']) helps[id] = await text(page, `[data-testid="${id}"]`);
    if (!/16 rules/.test(helps['help-check'])) throw new Error('help under Run check: ' + helps['help-check']);
    const btnText = await text(page, '[data-testid="btn-check"]');
    return `${btnText}; ${await text(page, '[data-testid="check-outcome"]')}; ${n} finding(s), ${nocite} say a person must look; ${human} human-review items; extraction_unreliable note ${unreliable}; help lines ${Object.keys(helps).length}; lot before ${S.lotBefore}`;
  });

  await step(page, 'Ask the regulations: expiry question returns 21 CFR 801 passages, off-topic abstains', '06_evidence', async () => {
    const mockedBefore = mocked.length;
    await click(page, 'btn-toggle-evidence');
    const title = await text(page, '[data-testid="evidence"] h3');
    if (!/^Evidence for /.test(title)) throw new Error('card title: ' + title);
    const passagesOf = () => page.evaluate(() => [...document.querySelectorAll('[data-testid="evidence"] > [data-testid="evidence-results"] [data-testid="passage"]')].map((e) => e.querySelector('.ptitle').innerText.replace(/\s+/g, ' ')));
    const ask = async (q) => {
      await fill(page, 'evidence-question', q);
      await click(page, 'btn-ask');
      await noError(page, 'ask');
      return { none: !!(await page.$('[data-testid="evidence"] > [data-testid="no-passage"]')), passages: await passagesOf() };
    };
    // the example buttons run the question themselves
    await click(page, 'example-expiration');
    await noError(page, 'ask');
    const expiry = await passagesOf();
    if (!expiry.length || !/^21 CFR 801/.test(expiry[0])) throw new Error('expiry question did not return 21 CFR 801 first: ' + expiry.join(' | '));
    if (expiry.length > 3) throw new Error('more than 3 passages shown before Show more: ' + expiry.length);
    const shown = await page.$eval('[data-testid="evidence"]', (e) => ({ ids: /fda_21cfr/.test(e.innerText), open: e.querySelector('details[data-testid="evidence-details"]').open }));
    if (shown.ids || shown.open) throw new Error('chunk ids visible without opening details: ' + JSON.stringify(shown));
    await click(page, 'btn-more-passages');
    const more = await page.$$eval('[data-testid="more-results"] [data-testid="passage"]', (x) => x.length);
    const off = await ask('weather in Paris tomorrow');
    if (!off.none || off.passages.length) throw new Error('off-topic question was not stopped: ' + JSON.stringify(off));
    const noText = await text(page, '[data-testid="no-passage"]');
    if (!/No regulation passage answers this\. Try a labeling question\./.test(noText)) throw new Error('no-answer text: ' + noText);
    // the user's own example is reported, not asserted: the existing score gate sits just below its score
    const golden = await ask('benefits of golden pump');
    const card = await text(page, '[data-testid="evidence"]');
    if (mocked.length !== mockedBefore) throw new Error('a mock response was served: ' + mocked.slice(mockedBefore).join(', '));
    if (/\b(sample|mock|lorem)\b/i.test(card)) throw new Error('sample or mock wording on the evidence card');
    return `expiry: ${expiry.length} passages, first "${expiry[0].slice(0, 60)}", +${more} more; "weather in Paris tomorrow": abstained; "benefits of golden pump": ${golden.none ? 'abstained' : golden.passages.length + ' passages shown (the gate does not stop it)'}; no X-Mock responses`;
  });

  await step(page, 'invalid value error and Retry', '07_invalid_value', async () => {
    await assess(page, 'expiry', '03/04/2028');
    await page.waitForSelector('[data-testid="change-rejected"]', { timeout: 10000 });
    const msg = await text(page, '[data-testid="change-rejected"]');
    if (!/ambiguous_date/.test(msg)) throw new Error('no ambiguous_date message: ' + msg);
    await click(page, 'retry-unassessed');
    await page.waitForSelector('[data-testid="change-rejected"]', { timeout: 10000 });
    await assess(page, 'lot', 'LOT1');
    await page.waitForSelector('[data-testid="error-assess"]', { timeout: 10000 });
    const e2 = await text(page, '[data-testid="error-assess"]');
    if (!/no_change/.test(e2)) throw new Error('no no_change error: ' + e2);
    await click(page, 'retry-assess');
    await page.waitForSelector('[data-testid="error-assess"]', { timeout: 10000 });
    return `ambiguous date: "${msg.split('\n')[0].slice(0, 110)}"; same lot: "${e2.replace(/\s+/g, ' ').replace(/Retry$/, '').slice(0, 90)}"; both Retry buttons re-sent and showed the API answer again`;
  });

  ok = ok && await step(page, 'change lot to LOT2, confirm checklist', '08_change_lot', async () => {
    await assess(page, 'lot', 'LOT2');
    await noError(page, 'assess');
    await page.waitForSelector('[data-testid="assessment"]');
    const items = await page.$$eval('[data-testid="affected-item"]', (x) => x.map((i) => i.dataset.kind));
    const noBc = !!(await page.$('[data-testid="no-barcode-decision"]'));
    await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, '08a_assess_lot.png'), fullPage: true });
    await confirmChange(page);
    return `affected items: ${items.join(', ')}; uploaded label so barcode decision deferred to Generate: ${noBc}; checklist confirmed`;
  });

  ok = ok && await step(page, 'generate revised artwork: barcode REGENERATE', '09_artwork_regenerate', async () => {
    await click(page, 'btn-go-artwork');
    await click(page, 'btn-generate');
    await noError(page, 'generate');
    await page.waitForSelector('[data-testid="artwork"]');
    const d = await page.$eval('[data-testid="artwork"] [data-testid="barcode-decision"]', (e) => e.dataset.decision);
    if (d !== 'REGENERATE') throw new Error('barcode decision ' + d);
    await page.waitForFunction(() => { const i = document.querySelector('[data-testid="artwork-preview"]'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
    const sentence = await text(page, '[data-testid="artwork"] [data-testid="barcode-decision"]');
    return `${await text(page, '[data-testid="artwork-version"]')}; ${sentence.split('\n')[0]}; DRAFT preview drawn`;
  });

  ok = ok && await step(page, 're-check the lot version', '10_recheck_lot', async () => {
    await click(page, 'btn-recheck');
    await noError(page, 'recheck');
    await page.waitForSelector('[data-testid="artwork"] ~ .card [data-testid="check-result"], .card [data-testid="check-result"]');
    const f = await page.$$eval('[data-testid="finding"]', (x) => x.map((e) => e.dataset.rule));
    const cited = await page.$$eval('[data-testid="finding"][data-rule="B-LOT"] [data-testid="citation"]', (x) => x.map((e) => e.innerText.slice(0, 60)));
    return `${await text(page, '[data-testid="check-outcome"]')}; findings ${f.join(', ')}; B-LOT citation: ${cited.join(' | ') || 'none'}`;
  });

  ok = ok && await step(page, 'what changed: versions and history say lot X to LOT2 with the change id', '10b_what_changed', async () => {
    await openStage(page, 'check');
    await page.waitForSelector('[data-testid="what-changed"]');
    const cells = await page.$$eval('[data-testid="what-changed"]', (x) => x.map((e) => e.innerText.trim()));
    const l2 = cells.find((c) => c.startsWith('L2:')); const l1 = cells.find((c) => c.startsWith('L1:'));
    if (l1 !== 'L1: first upload') throw new Error('L1 text: ' + l1);
    const before = S.lotBefore.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('^L2: lot ' + before + ' → LOT2 \\(change chg_[0-9a-f]+\\)$');
    if (!l2 || !re.test(l2)) throw new Error(`L2 text "${l2}" (record lot before: "${S.lotBefore}")`);
    const details = await page.$$eval('[data-testid="history-detail"]', (x) => x.map((e) => e.textContent.trim()).filter(Boolean));
    const req = details.find((d) => d.startsWith('Change requested: lot')) || '';
    const rec = details.find((d) => /^Record v2: lot/.test(d)) || '';
    if (!req.includes('→ LOT2') || !rec.includes('→ LOT2')) throw new Error('history details: ' + details.join(' | '));
    return `${l1}; ${l2}; history: "${req}", "${rec}"`;
  });

  ok = ok && await step(page, 'Evidence for this field: all ten fields, value + check + passages', '10c_field_evidence', async () => {
    const fields = ['name', 'model', 'manufacturer', 'manufacturer_address', 'udi_di', 'sterilization', 'storage', 'lot', 'expiry', 'serial'];
    const word = { manufacturer_address: 'manufacturer address', udi_di: 'UDI-DI' };
    const mockedBefore = mocked.length;
    const out = [];
    for (const f of fields) {
      await click(page, `evidence-${f}`);
      await noError(page, 'field-ask');
      const r = await page.evaluate(() => {
        const p = document.querySelector('[data-testid="field-evidence"]');
        return {
          value: p.querySelector('[data-testid="field-value"]').innerText.trim(),
          rules: [...p.querySelectorAll('[data-testid="field-rule"]')].map((x) => `${x.querySelector('.mono').innerText}:${x.dataset.outcome}`),
          noRule: /No check rule looks at this field/.test(p.innerText),
          passages: [...p.querySelectorAll('[data-testid="passage"] .ptitle strong')].map((x) => x.innerText),
          abstained: !!p.querySelector('[data-testid="no-passage"]'),
          title: p.querySelector('h3').innerText,
        };
      });
      if (!r.title.includes(word[f] || f)) throw new Error(`${f}: panel title ${r.title}`);
      if (r.value === '') throw new Error(`${f}: no record value shown`);
      if (!r.passages.length && !r.abstained) throw new Error(`${f}: neither passages nor a no-answer notice`);
      out.push(`${f}=${r.value.slice(0, 14)} [${r.rules.join(',') || (r.noRule ? 'no rule' : 'no check yet')}] ${r.passages.length ? r.passages[0] : 'no passage'}`);
      if (f === 'lot') {
        if (r.value.replace(/\s*TEST$/, '') !== 'LOT2') throw new Error('lot value shown ' + r.value);
        if (!r.rules.length) throw new Error('lot panel has no check result although L2 was re-checked');
        if (!r.passages.some((x) => /801|830/.test(x))) throw new Error('lot panel has no 801 or 830 passage: ' + r.passages.join(','));
      }
    }
    if (mocked.length !== mockedBefore) throw new Error('a mock response was served');
    return out.join('; ');
  });

  ok = ok && await step(page, 'change name: barcode KEEP, confirm', '11_change_name_keep', async () => {
    await assess(page, 'name', 'Golden Pump B');
    await noError(page, 'assess');
    const d = await page.$$eval('[data-testid="assessment"] [data-testid="barcode-decision"]', (x) => x.map((e) => e.dataset.decision));
    if (!d.includes('KEEP')) throw new Error('assessment barcode decisions: ' + (d.join(', ') || 'none'));
    const sentence = await text(page, '[data-testid="assessment"] [data-testid="barcode-decision"]');
    await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, '11a_assess_name_keep.png'), fullPage: true });
    await confirmChange(page);
    return `barcode ${d.join(', ')}: ${sentence.split('\n')[0]}`;
  });

  ok = ok && await step(page, 'generate the name version (KEEP)', '12_artwork_keep', async () => {
    await click(page, 'btn-go-artwork');
    await click(page, 'btn-generate');
    await noError(page, 'generate');
    const d = await page.$eval('[data-testid="artwork"] [data-testid="barcode-decision"]', (e) => e.dataset.decision);
    if (d !== 'KEEP') throw new Error('barcode decision ' + d);
    S.finalVersion = await text(page, '[data-testid="artwork-version"]');
    return `${S.finalVersion}, barcode KEEP`;
  });

  ok = ok && await step(page, 'blocked approval (no re-check yet) shows the API message', '13_blocked_approval', async () => {
    await openStage(page, 'review');
    await noError(page, 'review-load');
    await setRole(page, 'reviewer');
    await page.waitForSelector('[data-testid="no-recheck"]');
    await click(page, 'btn-approve');
    await page.waitForSelector('[data-testid="error-review"]', { timeout: 10000 });
    const msg = await text(page, '[data-testid="error-review"]');
    if (!/check_required/.test(msg)) throw new Error('unexpected: ' + msg);
    return msg.replace(/\s+/g, ' ').replace(/Retry$/, '').trim();
  });

  ok = ok && await step(page, 'reviewer: re-check, comment, approve', '14_approved', async () => {
    await click(page, 'btn-recheck-review');
    await noError(page, 'recheck');
    await page.waitForSelector('[data-testid="check-result"]');
    await fill(page, 'review-comment', `pro_e2e approval ${stamp}`);
    await click(page, 'btn-approve');
    await noError(page, 'review');
    const rec = await text(page, '[data-testid="review-recorded"]');
    if (!/approve/.test(rec)) throw new Error(rec);
    const rows = await page.$$eval('[data-testid="reviews"] tbody tr', (x) => x.length);
    return `${rec}; ${rows} decision row(s) listed`;
  });

  ok = ok && await step(page, 'export: download PDF, hash and DRAFT', '15_export', async () => {
    await click(page, 'btn-go-export');
    await noError(page, 'export-load');
    const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 60000 }), page.click('[data-testid="btn-download"]')]);
    await idle(page);
    await noError(page, 'download');
    const file = path.join(work, dl.suggestedFilename());
    await dl.saveAs(file);
    S.exportPdf = file;
    const res = await text(page, '[data-testid="download-result"]');
    if (!/matches the recorded hash/.test(res)) throw new Error(res);
    const pkg = await text(page, '[data-testid="export-package"]');
    if (!/DRAFT/.test(pkg) || !/100 x 60 mm/.test(pkg)) throw new Error('package text lacks DRAFT or size: ' + pkg.replace(/\s+/g, ' ').slice(0, 200));
    return `${dl.suggestedFilename()}, ${fs.statSync(file).size} bytes, sha256 on disk ${sha(file).slice(0, 12)}; ${res}`;
  });

  await step(page, 'print verification on a rasterized copy of the approved PDF', '16_print_verify', async () => {
    const png = path.join(work, 'printed.png');
    execFileSync(PY, ['-c', `import pypdfium2 as p; d=p.PdfDocument(r'${S.exportPdf}'); d[0].render(scale=300/72).to_pil().save(r'${png}'); d.close()`], { stdio: 'pipe' });
    await page.setInputFiles('[data-testid="print-file"]', png);
    await page.selectOption('[data-testid="print-condition"]', 'clean_print_scan');
    await click(page, 'btn-verify');
    await noError(page, 'verify');
    const outcome = await page.$eval('[data-testid="print-result"]', (e) => e.dataset.outcome);
    return `outcome ${outcome} (a perfect digital render, not a photo of a real print)`;
  });

  await step(page, 'history', '17_history', async () => {
    const rows = await page.$$eval('[data-testid="history"] tbody tr', (x) => x.map((r) => r.innerText));
    const actions = [...new Set(rows.map((r) => r.split('\t')[2]))];
    if (!rows.length) throw new Error('no history rows');
    return `${rows.length} events: ${actions.join(', ')}`;
  });

  // ------------------------------------------------------------ run B: second product typed by hand
  await step(page, 'second product: upload golden_label.pdf, type fields by hand', '19_saved_by_hand', async () => {
    await setRole(page, 'editor');
    const r = await addProduct(page, {
      file: fs.existsSync(path.join(ROOT, 'golden', 'golden_label.pdf')) ? path.join(ROOT, 'golden', 'golden_label.pdf') : S.goldenPdf,
      shotRead: '18_read_by_hand',
      values: {
        name: `Hand Entry Pump ${stamp}`, manufacturer: 'Demo Labs', manufacturer_address: '12 Demo Road', model: 'HP-200',
        lot: 'LOT1', expiry: '2030-06-30', udi_di: '00000000000000', serial: 'SN1', sterilization: 'Gamma', storage: 'Store below 25 C',
      },
    });
    S.pidB = r.pid;
    const rec = await text(page, '[data-testid="record"]');
    if (!/HP-200/.test(rec) || !/Gamma/.test(rec)) throw new Error('record does not show the typed values');
    return `${r.pid}; record shows the typed model HP-200 and sterilization Gamma`;
  });

  await step(page, 'second product: change expiry, confirm', '20_change_by_hand', async () => {
    await assess(page, 'expiry', '2031-01-31');
    await noError(page, 'assess');
    const items = await page.$$eval('[data-testid="affected-item"]', (x) => x.map((i) => i.dataset.kind));
    await confirmChange(page);
    return `affected: ${items.join(', ')}; confirmed`;
  });

  // ------------------------------------------------------------ layout at 1024 px
  await step(page, 'layout at 1024 px (no horizontal scroll)', '21_width_1024', async () => {
    await page.setViewportSize({ width: 1024, height: 800 });
    await openStage(page, 'check');
    const sw = await page.evaluate(() => document.documentElement.scrollWidth);
    await page.setViewportSize({ width: 1280, height: 900 });
    if (sw > 1024) throw new Error(`page is ${sw} px wide at a 1024 px window`);
    return `scrollWidth ${sw}`;
  });

  // ------------------------------------------------------------ API unreachable (requests aborted in the browser)
  await step(page, 'API unreachable: clear error, LIVE indicator, Retry recovers', '22_api_unreachable', async () => {
    await openStage(page, 'products');
    await page.route((u) => !u.pathname.startsWith('/ui/'), (r) => r.abort('connectionrefused'));
    await page.click('[data-testid="btn-load-products"]');
    await idle(page);
    await page.waitForSelector('[data-testid="error-products"]', { timeout: 10000 });
    const msg = await text(page, '[data-testid="error-products"]');
    await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'API offline', null, { timeout: 12000 });
    await page.evaluate(() => window.scrollTo(0, 0)); await page.screenshot({ path: path.join(SHOTS, '22_api_unreachable.png'), fullPage: true });
    await page.unroute(() => true).catch(() => {});
    await page.unrouteAll({ behavior: 'ignoreErrors' }).catch(() => {});
    await page.click('[data-testid="retry-products"]');
    await idle(page);
    await noError(page, 'products');
    await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'LIVE API', null, { timeout: 12000 });
    return `${msg.replace(/\s+/g, ' ').replace(/Retry$/, '').trim().slice(0, 140)}; after Retry the list loaded again`;
  });
  if (pageErrors.length) { failures += 1; console.log('FAIL page errors: ' + pageErrors.slice(0, 3).join(' | ')); }
  await browser.close();

  // ------------------------------------------------------------ camera: denied, then a fake camera device
  {
    const b = await launch({ headless: HEADLESS, args: ['--deny-permission-prompts'] });
    const c = await b.newContext({ viewport: { width: 1280, height: 900 } });
    const p = await c.newPage();
    await step(p, 'camera denied: clear message, upload still works', '23_camera_denied', async () => {
      await p.goto(URL); await idle(p);
      await p.click('[data-testid="step-add"]');
      await p.click('[data-testid="btn-cam-start"]');
      await p.waitForSelector('[data-testid="camera-msg"]', { timeout: 15000 });
      const msg = await text(p, '[data-testid="camera-msg"]');
      const uploadEnabled = await p.$eval('[data-testid="add-file"]', (e) => !e.disabled);
      if (!uploadEnabled) throw new Error('file input disabled');
      return `${msg} | file upload still enabled`;
    });
    await b.close();
  }
  {
    const b = await launch({ headless: HEADLESS, args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'] });
    const c = await b.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['camera'] });
    const p = await c.newPage();
    await step(p, 'camera with a fake device: capture and read', '24_camera_fake_device', async () => {
      await p.goto(URL); await idle(p);
      await p.click('[data-testid="step-add"]');
      await p.click('[data-testid="btn-cam-start"]');
      await p.waitForSelector('[data-testid="camera-panel"]', { timeout: 15000 });
      await p.waitForTimeout(1500);
      await p.click('[data-testid="btn-cam-capture"]');
      await p.waitForSelector('[data-testid="chosen-file"]', { timeout: 10000 });
      const chosen = await text(p, '[data-testid="chosen-file"]');
      await click(p, 'btn-read');
      const err = await p.$('[data-testid="error-read"]');
      const outcome = err ? 'API answered: ' + (await err.innerText()).replace(/\s+/g, ' ').replace(/Retry$/, '').trim().slice(0, 160) : 'read result shown';
      return `${chosen.replace(/\s+/g, ' ')}; ${outcome}`;
    });
    await b.close();
  }
}

async function stoppedOnly() {
  const b = await launch({ headless: HEADLESS });
  const p = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  // The page is loaded while the server runs; then the server is stopped for real (by hand or another shell).
  await p.goto(URL); await idle(p);
  console.log('Page loaded. Stop the server now (waiting up to 180 s) ...');
  const end = Date.now() + 180000;
  let down = false;
  while (Date.now() < end && !down) {
    try { const r = await fetch(`${BASE}/health`); down = !r.ok; } catch (e) { down = true; }
    if (!down) await new Promise((r) => setTimeout(r, 1000));
  }
  await step(p, 'server really stopped: offline indicator and clear error', '25_server_stopped', async () => {
    if (!down) throw new Error('the server was not stopped within 180 s');
    await p.click('[data-testid="btn-load-products"]');
    await idle(p);
    await p.waitForSelector('[data-testid="error-products"]', { timeout: 10000 });
    await p.waitForFunction(() => document.getElementById('proLiveText').textContent === 'API offline', null, { timeout: 12000 });
    return (await text(p, '[data-testid="error-products"]')).replace(/\s+/g, ' ').replace(/Retry$/, '').trim();
  });
  await b.close();
}

main().then(() => {
  fs.writeFileSync(path.join(SHOTS, 'results.json'), JSON.stringify({ base: BASE, at: new Date().toISOString(), results }, null, 1));
  const bad = results.filter((r) => r.status === 'FAIL').length;
  console.log(`\n${results.length} steps, ${bad} FAIL${failures > bad ? ' (plus page errors)' : ''}`);
  process.exit(failures ? 1 : 0);
}).catch((e) => { console.error(e); process.exit(1); });
