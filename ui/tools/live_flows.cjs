/**
 * Live checks of the api-mode actions in headless Chromium, against a running demo (scripts/run_demo.py).
 * Each flow prints PASS, FALLBACK (the API said no, the UI showed that honestly) or FAIL. Nothing is faked.
 *
 *   PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 \
 *   [BLUR_IMAGE=<png>] [GOOD_FILE=<pdf or png>] [PRODUCT=<product id>] [CHANGE=<id> LABEL=<id> VERSION=<id>] \
 *   node ui/tools/live_flows.cjs
 */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';

(async () => {
  const browser = await chromium.launch();
  const out = [];
  const log = (name, status, note) => { out.push({ name, status, note }); console.log(`${status.padEnd(8)} ${name} ${note || ''}`); };
  const open = async (kind, qs = '') => {
    const ctx = await browser.newContext({ viewport: { width: 1300, height: 900 }, acceptDownloads: true });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push(e.message));
    await page.goto(`${BASE}/ui/${kind}/index.html?mode=api${qs}`);
    await page.waitForSelector('#devStateButtons .btn-state');
    return { page, errs };
  };
  const go = async (page, screen, file) => {
    await page.evaluate((s) => window.LabelLensStateSwitcher.setScreen(s), screen);
    await page.waitForTimeout(300);
    await page.click(`#devStateButtons .btn-state[data-file="${file}"]`);
    await page.waitForTimeout(500);
  };

  // 1. Professional ask: instant extractive answer, then the optional AI answer with fallback.
  try {
    const { page, errs } = await open('professional');
    await go(page, 'D5 Evidence', 'professional/evidence/success.json');
    await page.fill('#d5Question', 'how must a date be written on a device label?');
    await page.click('#d5Ask');
    await page.waitForSelector('[data-testid="answer"], [data-testid="abstained"]', { timeout: 20000 });
    const instant = (await page.$('[data-testid="answer"]')) ? 'answered' : 'abstained';
    await page.click('#d5AskAI');
    await page.waitForSelector('[data-testid="ai-panel"]', { timeout: 10000 });
    await page.waitForSelector('[data-testid="ai-note"], [data-testid="ai-fallback"], [data-testid="ai-failed"]', { timeout: 125000 });
    const fb = await page.$('[data-testid="ai-fallback"]');
    const failed = await page.$('[data-testid="ai-failed"]');
    const badge = await page.$eval('#dataSourceBadge', (b) => b.textContent);
    log('D5 ask + Ask AI', failed ? 'FALLBACK' : 'PASS', `instant ${instant}; AI ${fb ? 'fell back to passages' : (failed ? 'job failed, passages kept' : 'model answer or abstention')}; badge ${badge}; page errors ${errs.length}`);
  } catch (e) { log('D5 ask + Ask AI', 'FAIL', e.message.split('\n')[0]); }

  // 2. Public ask with a real reference product (matcher, then ask), plus the AI button.
  try {
    const { page } = await open('public');
    await page.evaluate(() => window.LabelLensStateSwitcher.setScreen('P3 Ask about this label'));
    await page.waitForSelector('#p3Medicine');
    await page.fill('#p3Medicine', process.env.MEDICINE || 'Childrens Ibuprofen');
    await page.fill('#p3QuestionInput', 'what are the warnings');
    await page.click('#btnP3AskSubmit');
    await page.waitForSelector('[data-testid="answer"], [data-testid="abstained"]', { timeout: 30000 });
    const t = await page.$eval('#publicDynamicContent', (e) => e.innerText);
    log('P3 matcher + ask', 'PASS', `${(await page.$('[data-testid="answer"]')) ? 'answered' : 'abstained'}; banner ${/Authenticity not verified/.test(await page.$eval('body', (b) => b.innerText)) ? 'present' : 'MISSING'}; ${t.length} chars`);
  } catch (e) { log('P3 matcher + ask', 'FAIL', e.message.split('\n')[0]); }

  // 3. Upload with product_id: a blurry photo must come back as retake_photo, a good file creates a scan.
  const PRODUCT = process.env.PRODUCT;
  async function upload(label, file) {
    try {
      const { page } = await open('professional');
      await go(page, 'D3 Upload or scan', 'professional/upload/loading.json');
      await page.setInputFiles('#d3File', file);
      await page.fill('#d3Product', PRODUCT);
      await page.click('#d3Upload');
      await page.waitForFunction(() => /Scan processed|Retake the photo|Upload processing failed|Upload failed/.test(document.getElementById('professionalDynamicContent').innerText), null, { timeout: 120000 });
      const t = await page.$eval('#professionalDynamicContent', (e) => e.innerText);
      return { page, t };
    } catch (e) { return { err: e.message.split('\n')[0] }; }
  }
  if (PRODUCT && process.env.BLUR_IMAGE) {
    const r = await upload('blur', process.env.BLUR_IMAGE);
    if (r.err) log('D3 upload blurry photo', 'FAIL', r.err);
    else if (/Retake the photo/.test(r.t)) log('D3 upload blurry photo', 'PASS', 'retake_photo shown with reasons: ' + (await r.page.$eval('[data-testid="retake-reasons"]', (e) => e.innerText).catch(() => 'none')));
    else log('D3 upload blurry photo', 'FALLBACK', 'not rejected: ' + r.t.replace(/\s+/g, ' ').slice(0, 120));
  }
  if (PRODUCT && process.env.GOOD_FILE) {
    const r = await upload('good', process.env.GOOD_FILE);
    if (r.err) log('D3 upload good file', 'FAIL', r.err);
    else log('D3 upload good file', /Scan processed/.test(r.t) ? 'PASS' : 'FALLBACK', r.t.replace(/\s+/g, ' ').slice(0, 140));
  }

  // 4. Generate and download on a live package (needs CHANGE, LABEL and VERSION of a confirmed change).
  if (process.env.CHANGE && process.env.LABEL) {
    try {
      const qs = `&change=${process.env.CHANGE}&label=${process.env.LABEL}` + (process.env.VERSION ? `&version=${process.env.VERSION}` : '');
      const { page } = await open('professional', qs);
      await go(page, 'D6 Changes', 'professional/changes/confirm_success.json');
      await page.click('#btnGenerateDraftArtwork');
      await page.waitForSelector('#btnGoToReviewFromDraft, [data-testid="generate-error"]', { timeout: 120000 });
      const err = await page.$('[data-testid="generate-error"]');
      if (err) log('D6 generate', 'FALLBACK', 'API refused: ' + (await err.innerText()).replace(/\s+/g, ' '));
      else {
        log('D6 generate', 'PASS', 'draft artwork shown with DRAFT mark');
        await page.evaluate(() => window.LabelLensStateSwitcher.setScreen('D8 Export'));
        await page.waitForTimeout(400);
        await page.click('#devStateButtons .btn-state[data-file="professional/export/draft.json"]');
        await page.waitForTimeout(800);
        const badge = await page.$eval('#dataSourceBadge', (b) => b.textContent);
        const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 20000 }).catch(() => null), page.click('[data-testid="export-pdf"] .dl-btn')]);
        const note = await page.$eval('#downloadNote', (e) => e.textContent).catch(() => '');
        const banner = !!(await page.$('[data-testid="draft-banner"]'));
        log('D8 download', dl ? 'PASS' : 'FALLBACK', `${dl ? 'file ' + dl.suggestedFilename() : 'no file'}; DRAFT banner ${banner}; badge ${badge}; ${note}`);
      }
    } catch (e) { log('D6 generate and D8 download', 'FAIL', e.message.split('\n')[0]); }
  }
  // 6. D2 register (real endpoint) and P1 public scan (the server answers it with a mock: the badge must say so).
  if (process.env.GOLDEN_JSON) {
    const g = JSON.parse(require('fs').readFileSync(process.env.GOLDEN_JSON, 'utf8'));
    try {
      const { page } = await open('professional', `&product=${g.template_product_id}`);
      await go(page, 'D2 Template setup', 'professional/template_setup/success.json');
      const t = g.template;
      await page.fill('#d2JsonPlaceholder, [data-testid="d2-json"]', JSON.stringify({ size_mm: t.size_mm, background: null, slots: t.slots }));
      await page.$eval('#btnRegisterTemplate', (e) => e.click());
      await page.waitForFunction(() => /Registered|Refused|failed|not valid/.test(document.getElementById('d2Result').innerText), null, { timeout: 30000 });
      const r = await page.$eval('#d2Result', (e) => e.innerText);
      const kind = await page.$eval('#dataSourceBadge', (b) => b.dataset.kind);
      log('D2 register template', /Registered/.test(r) && kind === 'api' ? 'PASS' : 'FAIL', `${r.slice(0, 110)} | badge ${kind}`);
    } catch (e) { log('D2 register template', 'FAIL', e.message.split('\n')[0]); }
  }
  if (process.env.BLUR_IMAGE) {
    try {
      const { page } = await open('public');
      await page.waitForSelector('#devStateButtons .btn-state');
      await page.evaluate(() => window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand'));
      await page.waitForSelector('#btnP1UploadImage');
      const [fc] = await Promise.all([page.waitForEvent('filechooser'), page.$eval('#btnP1UploadImage', (e) => e.click())]);
      await fc.setFiles(process.env.BLUR_IMAGE);
      await page.waitForFunction(() => /Product information|ExampleMed|Authenticity not verified/.test(document.getElementById('publicDynamicContent').innerText) && !!document.querySelector('[data-testid="source-badge"]'), null, { timeout: 30000 });
      const kind = await page.$eval('#dataSourceBadge', (b) => b.dataset.kind);
      log('P1 upload (public scan)', kind === 'x-mock' ? 'FALLBACK' : 'PASS', `badge ${kind}: publicScan is a mock on this server, the page says so`);
    } catch (e) { log('P1 upload (public scan)', 'FAIL', e.message.split('\n')[0]); }
  }
  // 5. End to end on the golden package through the UI (GOLDEN_JSON from golden_setup.py).
  if (process.env.GOLDEN_JSON) await require('./e2e_golden.cjs')({ open, go, log, goldenJson: process.env.GOLDEN_JSON });
  await browser.close();
  const bad = out.filter((o) => o.status === 'FAIL').length;
  console.log(`${out.length} flows, ${bad} FAIL`);
})();
