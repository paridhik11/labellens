/**
 * Final rehearsal driver. Runs each step once, records PASS or FAIL, seconds and what the screen shows. It never retries
 * and never fixes anything. Usage:
 *   PLAYWRIGHT_DIR=<dir> BASE=http://127.0.0.1:8138 node reports/rehearsal/rehearse.cjs
 * Output: reports/rehearsal/results.json and screenshots in reports/rehearsal/shots/.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { createRequire } = require('module');

const ROOT = path.resolve(__dirname, '..', '..');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR, 'x.js'));
const { chromium } = req('playwright');
const BASE = process.env.BASE;
const PY = path.join(ROOT, '.venv312', 'Scripts', 'python.exe');
const SHOTS = path.join(__dirname, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'rehearsal_'));
const RES = path.join(__dirname, 'results.json');
const results = process.env.ONLY && fs.existsSync(RES) ? JSON.parse(fs.readFileSync(RES, 'utf8')) : [];

async function step(page, name, shot, fn) {
  const t0 = Date.now();
  let status = 'PASS'; let note = '';
  try { note = (await fn()) || ''; } catch (e) { status = 'FAIL'; note = e.message.split('\n')[0]; }
  const seconds = Number(((Date.now() - t0) / 1000).toFixed(1));
  try { await page.screenshot({ path: path.join(SHOTS, `${shot}.png`), fullPage: true }); } catch (e) { /* ignore */ }
  results.push({ step: name, status, seconds, note: String(note).replace(/\s+/g, ' ').slice(0, 600), shot: `shots/${shot}.png` });
  console.log(`${status} ${seconds}s ${name} :: ${String(note).replace(/\s+/g, ' ').slice(0, 300)}`);
  fs.writeFileSync(path.join(__dirname, 'results.json'), JSON.stringify(results, null, 2));
}

const idle = (page, t) => page.waitForFunction(() => !document.querySelector('[data-testid^="busy-"]'), null, { timeout: t || 300000 });
async function click(page, testid) {
  const sel = `[data-testid="${testid}"]`;
  await page.waitForSelector(`${sel}:not([disabled])`, { timeout: 30000 });
  await page.click(sel);
  await page.waitForTimeout(150);
  await idle(page);
}
const text = (page, sel) => page.$eval(sel, (e) => e.innerText);
async function noError(page, id) {
  const e = await page.$(`[data-testid="error-${id}"]`);
  if (e) throw new Error(`page shows error: ${(await e.innerText()).replace(/\s+/g, ' ').slice(0, 300)}`);
}
async function openStage(page, stage) { await page.click(`[data-testid="step-${stage}"]`); await page.waitForTimeout(150); await idle(page); }
async function setRole(page, role) { await page.click(`[data-testid="role-${role}"]`); await page.waitForTimeout(200); await idle(page); }

async function ensureEvidence(page) {
  if (await page.$('[data-testid="evidence-question"]')) return;
  await page.click('[data-testid="btn-toggle-evidence"]'); await page.waitForTimeout(300);
}

/** Public photo: upload, wait for a verdict, return the visible result text. */
async function publicPhoto(page, file) {
  await page.goto(`${BASE}/ui/public/index.html`);
  await page.waitForSelector('[data-testid="upload-photo"]');
  const [chooser] = await Promise.all([page.waitForEvent('filechooser'), page.click('[data-testid="upload-photo"]')]);
  await chooser.setFiles(path.join(ROOT, 'demo_photos', 'public', file));
  await page.waitForFunction(() => {
    const q = (s) => document.querySelector(`[data-testid="${s}"]`);
    return q('scan-confirm') || q('not-identified') || q('retake') || q('scan-failed') || q('scan-confirm-panel');
  }, null, { timeout: 150000 });
  return (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));
  const only = process.env.ONLY ? process.env.ONLY.split(',') : null;
  const want = (k) => !only || only.includes(k);

  if (want('pub')) {
    await step(page, 'Public: 04_barcode_aspirin photo', 'r01_aspirin', async () => {
      const t = await publicPhoto(page, '04_barcode_aspirin.jpg');
      if (!/Aspirin/i.test(t)) throw new Error('no Aspirin in result: ' + t.slice(0, 300));
      const m = /Is this [^?]*\?[^.]*\./.exec(t);
      if (page.url()) await page.click('[data-testid="scan-confirm"]');
      await page.waitForTimeout(1500);
      const t2 = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
      return `${m ? m[0] : 'matched'}; after Confirm: ${t2.slice(t2.indexOf('Aspirin') > -1 ? t2.indexOf('Aspirin') : 0).slice(0, 150)}`;
    });
    await step(page, 'Public: 08_live_zetia photo, then name, Find, Search DailyMed, Select', 'r02_zetia', async () => {
      const t = await publicPhoto(page, '08_live_zetia.jpg');
      if (!/Not identified/i.test(t)) throw new Error('expected Not identified: ' + t.slice(0, 300));
      await page.fill('[data-testid="type-name-input"]', 'Zetia');
      await page.click('[data-testid="type-name-go"]');
      await page.getByRole('button', { name: /Search DailyMed/i }).click({ timeout: 60000 });
      await page.getByRole('button', { name: /^Select/i }).first().click({ timeout: 120000 });
      await page.waitForFunction(() => /Fetched live from DailyMed/i.test(document.body.innerText), null, { timeout: 180000 });
      return 'live label shown: ' + (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ').match(/ZETIA[^.]{0,80}/i);
    });
  }

  if (want('pubtype')) {
    await step(page, 'Public page: type metoprolol, ask "how to store it"', 'r04_metoprolol', async () => {
      await page.goto(`${BASE}/ui/public/index.html`);
      await page.waitForSelector('[data-testid="upload-photo"]');
      await page.getByRole('button', { name: /3\. Ask about this label/ }).click();
      await page.waitForSelector('#p3Medicine');
      await page.fill('#p3Medicine', 'metoprolol');
      await page.fill('#p3QuestionInput', 'how to store it');
      await page.click('#btnP3AskSubmit');
      await page.waitForFunction(() => document.querySelector('[data-testid="answer"],[data-testid="abstained"],[data-testid="low-confidence-passages"],#p3Note:not(:empty)'), null, { timeout: 90000 });
      await page.waitForTimeout(1500);
      const t = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
      const i = t.search(/Medicine Q&A/);
      const first = t.slice(i, i + 260);
      if (!/No label loaded/.test(t)) return first;
      await page.getByRole('button', { name: /Search DailyMed/i }).first().click({ timeout: 20000 });
      await page.getByRole('button', { name: /^Select/i }).first().click({ timeout: 120000 });
      await page.waitForFunction(() => /Fetched live from DailyMed/i.test(document.body.innerText), null, { timeout: 180000 }).catch(() => {});
      await page.getByRole('button', { name: /3\. Ask about this label/ }).click();
      await page.waitForSelector('#p3QuestionInput');
      await page.fill('#p3QuestionInput', 'how to store it');
      await page.click('#btnP3AskSubmit');
      await page.waitForFunction(() => document.querySelector('[data-testid="answer"],[data-testid="abstained"]'), null, { timeout: 90000 });
      const t2 = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
      const j = t2.search(/Answer|Store|store/);
      return 'first ask: ' + first + ' || after Search DailyMed + Select: ' + t2.slice(j, j + 400);
    });
  }

  if (want('dev')) {
    await step(page, 'Device: 03_golden_blurry refused', 'r03_blurry', async () => {
      await page.goto(`${BASE}/ui/pro/index.html`);
      await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'LIVE API');
      await openStage(page, 'products');
      await click(page, 'btn-go-add');
      await page.setInputFiles('[data-testid="add-file"]', path.join(ROOT, 'demo_photos', 'device', '03_golden_blurry.jpg'));
      await page.waitForSelector('[data-testid="chosen-file"]');
      await page.click('[data-testid="btn-read"]');
      await page.waitForFunction(() => document.querySelector('[data-testid="error-read"],[data-testid="read-result"]'), null, { timeout: 120000 });
      const e = await page.$('[data-testid="error-read"]');
      if (!e) throw new Error('no refusal shown');
      const msg = (await e.innerText()).replace(/\s+/g, ' ');
      if (!/blur/i.test(msg)) throw new Error('refused, but not for blur: ' + msg);
      return msg;
    });
  }

  if (want('pro')) {
    const S = {};
    await step(page, 'Pro: Golden Pump saved (sample, GP-100, LOT1, EXP 2030-06-30)', 'r05_saved', async () => {
      await page.goto(`${BASE}/ui/pro/index.html`);
      await page.waitForFunction(() => document.getElementById('proLiveText').textContent === 'LIVE API');
      await openStage(page, 'products');
      await click(page, 'btn-go-add');
      await click(page, 'btn-sample');
      await page.waitForSelector('[data-testid="read-result"]', { timeout: 20000 });
      const vals = {};
      for (const f of ['name', 'model', 'lot', 'expiry']) vals[f] = await page.inputValue(`[data-testid="input-${f}"]`);
      await page.fill('[data-testid="input-model"]', 'GP-100');
      await page.fill('[data-testid="input-sterilization"]', 'EO');
      await page.fill('[data-testid="input-storage"]', 'Store dry');
      await click(page, 'btn-save');
      await noError(page, 'save');
      const flash = await text(page, '[data-testid="flash"]');
      const m = /Saved product (prd_[0-9a-z]+)/.exec(flash);
      if (!m) throw new Error('no product id: ' + flash);
      S.pid = m[1];
      if (vals.lot !== 'LOT1' || vals.expiry !== '2030-06-30') throw new Error('sample values are ' + JSON.stringify(vals));
      return `${m[1]} ${JSON.stringify(vals)}`;
    });
    await step(page, 'Pro: run check', 'r06_check', async () => {
      await openStage(page, 'check');
      await click(page, 'btn-check');
      await noError(page, 'check');
      await page.waitForSelector('[data-testid="check-result"]');
      return (await text(page, '[data-testid="check-result"]')).replace(/\s+/g, ' ').slice(0, 300);
    });
    await step(page, 'Pro: change lot to LOT2, confirm', 'r07_change', async () => {
      await openStage(page, 'change');
      await page.selectOption('[data-testid="change-field"]', 'lot');
      await page.fill('[data-testid="change-value"]', 'LOT2');
      await click(page, 'btn-assess');
      await noError(page, 'assess');
      await page.waitForSelector('[data-testid="assessment"]');
      await click(page, 'btn-dec-all');
      await click(page, 'btn-confirm');
      await noError(page, 'confirm');
      await page.waitForSelector('[data-testid="change-confirmed"]', { timeout: 10000 });
      return 'confirmed';
    });
    await step(page, 'Pro: generate artwork, barcode REGENERATE with DRAFT', 'r08_generate', async () => {
      await click(page, 'btn-go-artwork');
      await click(page, 'btn-generate');
      await noError(page, 'generate');
      await page.waitForSelector('[data-testid="artwork"]');
      const d = await page.$eval('[data-testid="artwork"] [data-testid="barcode-decision"]', (e) => e.dataset.decision);
      await page.waitForFunction(() => { const i = document.querySelector('[data-testid="artwork-preview"]'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
      const t = await text(page, '[data-testid="artwork"]');
      if (d !== 'REGENERATE') throw new Error('barcode decision ' + d);
      return `${d}; DRAFT text on page: ${/DRAFT/.test(t)}`;
    });
    await step(page, 'Pro: reviewer re-check and approve', 'r09_approve', async () => {
      await openStage(page, 'review');
      await setRole(page, 'reviewer');
      await click(page, 'btn-recheck-review');
      await noError(page, 'recheck');
      await page.waitForSelector('[data-testid="check-result"]');
      await page.fill('[data-testid="review-comment"]', 'rehearsal approval');
      await click(page, 'btn-approve');
      await noError(page, 'review');
      return await text(page, '[data-testid="review-recorded"]');
    });
    await step(page, 'Pro: export PDF', 'r10_export', async () => {
      await click(page, 'btn-go-export');
      await noError(page, 'export-load');
      const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 60000 }), page.click('[data-testid="btn-download"]')]);
      await idle(page);
      await noError(page, 'download');
      S.pdf = path.join(work, dl.suggestedFilename());
      await dl.saveAs(S.pdf);
      return `${dl.suggestedFilename()} ${fs.statSync(S.pdf).size} bytes; ${(await text(page, '[data-testid="download-result"]')).slice(0, 150)}`;
    });
    await step(page, 'Pro: print verification', 'r11_verify', async () => {
      const png = path.join(work, 'printed.png');
      execFileSync(PY, ['-c', `import pypdfium2 as p; d=p.PdfDocument(r'${S.pdf}'); d[0].render(scale=300/72).to_pil().save(r'${png}'); d.close()`], { stdio: 'pipe' });
      await page.setInputFiles('[data-testid="print-file"]', png);
      await page.selectOption('[data-testid="print-condition"]', 'clean_print_scan');
      await click(page, 'btn-verify');
      await noError(page, 'verify');
      const o = await page.$eval('[data-testid="print-result"]', (e) => e.dataset.outcome);
      return `outcome ${o} (rasterized copy of the exported PDF, not a camera photo)`;
    });
    await step(page, 'Pro: Ask the regulations (expiration date)', 'r12_ask', async () => {
      await setRole(page, 'editor');
      await openStage(page, 'check');
      await ensureEvidence(page);
      const q = 'what must a label show for the expiration date?';
      await page.waitForSelector('[data-testid="evidence-question"]', { timeout: 10000 });
      await page.fill('[data-testid="evidence-question"]', q);
      await click(page, 'btn-ask');
      await noError(page, 'ask');
      const r = await page.$$eval('[data-testid="thread"] > .turn:first-child [data-testid="passage"] .ptitle strong', (x) => x.map((e) => e.innerText));
      if (!r.length) throw new Error('no passages');
      return r.join(' | ');
    });
    await step(page, 'Pro: Retrieval lab, same query', 'r13_lab', async () => {
      await click(page, 'open-lab');
      await page.fill('[data-testid="lab-query"]', 'what must a label show for the expiration date?');
      await click(page, 'btn-lab-run');
      await noError(page, 'lab');
      await page.waitForSelector('[data-testid="lab-table"]');
      return `${await page.$$eval('[data-testid="lab-cell"]', (x) => x.length)} cells; ${(await text(page, '[data-testid="lab-summary"]')).slice(0, 200)}`;
    });
    await step(page, 'Pro: Ask with AI (after warm-up)', 'r14_ai', async () => {
      await page.click('[data-testid="step-check"]');
      await page.waitForSelector('[data-testid="btn-check"]');
      await ensureEvidence(page);
      await page.fill('[data-testid="evidence-question"]', 'what must a label show for the expiration date?');
      await click(page, 'btn-ask-ai');
      await noError(page, 'ask-ai');
      return (await text(page, '[data-testid="thread"] > .turn:first-child')).replace(/\s+/g, ' ').slice(0, 300);
    });
  }
  console.log('page errors:', pageErrors.length ? pageErrors.join(' | ') : 'none');
  fs.writeFileSync(path.join(__dirname, 'page_errors.json'), JSON.stringify(pageErrors));
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
