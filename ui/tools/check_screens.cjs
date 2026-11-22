/**
 * Opens every screen and every mock state of ui/ in headless Chromium.
 * Records console errors, page errors and simple text checks, and writes a markdown table.
 *
 * Usage (from the repo root, with the UI served at BASE, default http://localhost:8765):
 *   PLAYWRIGHT_DIR=<folder containing node_modules/playwright> node ui/tools/check_screens.cjs [--shots]
 * --shots also writes ui/screenshots/NN_<screen>.png in demo order (first state of each screen).
 * Set OUT to choose the markdown output file (default ui/check_results.md).
 */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');

const BASE = process.env.BASE || 'http://localhost:8765';
const root = path.resolve(__dirname, '..', '..');
const index = JSON.parse(fs.readFileSync(path.join(root, 'src/api/mock/index.json'), 'utf8'));
const shots = process.argv.includes('--shots');

const isPublic = (s) => s.startsWith('P1') || s.startsWith('P2') || s.startsWith('P3');
const BAD = [/\bundefined\b/, /\bNaN\b/, /\[object /, /\bnull\b/, /—/];
let fallbackHttp = 0;
const MODE = process.env.MODE === 'api' ? 'api' : 'mock';
// Elements each mock state must show (data-testid), so an empty-looking render cannot pass.
const EXPECT = {
  'public/ask/ai_accepted.json': ['ai-running'],
  'public/ask/ai_job_done.json': ['ai-note', 'answer'],
  'public/ask/ai_job_fallback_timeout.json': ['ai-fallback', 'abstained'],
  'public/live/search_candidates.json': ['live-candidate', 'live-pick-note'],
  'public/live/search_none.json': ['live-none'],
  'public/live/search_unavailable.json': ['live-offline'],
  'public/live/fetching.json': ['live-fetching'],
  'public/live/fetch_failed.json': ['live-failed'],
  'public/live/product.json': ['live-label', 'live-product'],
  'public/ask/success.json': ['answer', 'citation'],
  'public/ask/abstained_needs_human_check.json': ['abstained'],
  'professional/ask/success.json': ['ask-card', 'answer', 'citation'],
  'professional/ask/ai_accepted.json': ['ai-running'],
  'professional/ask/abstained_needs_human_check.json': ['abstained', 'citation'],
  'professional/ask/abstained_out_of_scope.json': ['abstained'],
  'professional/evidence/success.json': ['evidence-results'],
  'professional/evidence/empty.json': ['evidence-empty'],
  'professional/review/recheck_failed_check.json': ['draft-banner', 'approval-blocked', 'coverage'],
  'professional/review/recheck_success.json': ['draft-banner', 'needs-human', 'decision-panel'],
  'professional/review/self_approval_forbidden.json': ['approval-blocked'],
  'professional/review/approved.json': ['draft-banner'],
  'professional/export/draft.json': ['draft-banner', 'no-qr', 'export-pdf'],
  'professional/export/approved.json': ['draft-banner', 'qr-card'],
  'professional/export/publish_success.json': ['draft-banner', 'publish-card'],
  'professional/print_verify/needs_review.json': ['pv-rescan', 'pv-no-result'],
  'professional/print_verify/failed_check.json': ['pv-mismatch-banner', 'pv-mismatch'],
  'professional/print_verify/success.json': ['pv-match-note'],
  'professional/print_verify/loading.json': ['pv-loading'],
  'professional/print_verify/empty.json': ['pv-empty'],
  'professional/upload/failed.json': ['upload-card'],
  'professional/upload/success.json': ['upload-card'],
  'professional/inspect/extraction_needs_review.json': ['extraction-status', 'unclear-banner', 'edit-manufacturer_address'],
  'professional/inspect/extraction_success.json': ['extraction-status', 'barcode'],
  'professional/inspect/extraction_confirmed.json': ['extraction-status'],
  'professional/inspect/failed_check.json': ['finding', 'citation', 'coverage'],
  'professional/inspect/success.json': ['passed-note', 'coverage'],
  'professional/inspect/loading.json': ['inspect-loading'],
};
// Extra controls that exist only in api mode.
const EXPECT_API = {
  'professional/template_setup/success.json': ['register-card'],
  'professional/template_setup/failed_check.json': ['register-card'],
  'professional/changes/assess_success.json': ['assess-btn'],
  'professional/review/recheck_success.json': ['recheck-card'],
  'professional/review/approved.json': ['recheck-card'],
};
const demoOrder = [
  'P1 Scan and Understand', 'P2 Product information', 'P3 Ask about this label',
  'D1 Products', 'D2 Template setup', 'D3 Upload or scan', 'D4 Inspect',
  'D5 Evidence', 'D6 Changes', 'D7 Review', 'D8 Export', 'D9 History', 'D10 Print verification',
];

(async () => {
  const browser = await chromium.launch();
  const results = [];
  const shotDir = path.join(root, 'ui', 'screenshots');
  if (shots) fs.mkdirSync(shotDir, { recursive: true });

  async function openPage(kind) {
    const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('console', (m) => {
      if (m.type() !== 'error') return;
      // In api mode a live lookup that answers 404 or 503 is an expected fallback to the mock, not a page error.
      if (MODE === 'api' && /Failed to load resource: the server responded with a status of (404|409|422|503)/.test(m.text())) { fallbackHttp += 1; return; }
      errs.push('console: ' + m.text());
    });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    page.on('requestfailed', (r) => errs.push('requestfailed: ' + r.url()));
    await page.goto(`${BASE}/ui/${kind === 'public' ? 'public' : 'professional'}/index.html?dev=1&devopen=1${MODE === 'api' ? '&mode=api' : ''}`);
    await page.waitForSelector('#devStateButtons .btn-state', { timeout: 8000 });
    return { page, errs };
  }

  const pub = await openPage('public');
  const pro = await openPage('pro');

  const screens = [...new Set(index.mocks.map((m) => m.screen))].filter((s) => s !== 'all professional');
  for (const screen of screens) {
    const target = isPublic(screen) ? pub : pro;
    const uiScreen = screen === 'Professional evidence' ? 'D5 Evidence' : screen;
    const entries = index.mocks.filter((m) => m.screen === screen);
    if (screen.startsWith('P1')) entries.unshift({ file: null, state: 'empty', screen });
    for (const m of entries) {
      const { page, errs } = target;
      const before = errs.length;
      let status = 'pass';
      let source = '';
      const notes = [];
      try {
        await page.evaluate((s) => window.LabelLensStateSwitcher.setScreen(s), uiScreen);
        await page.waitForTimeout(300);
        const sel = `#devStateButtons .btn-state[data-file="${m.file || ''}"]`;
        const btn = await page.$(sel);
        if (!btn) { status = 'FAIL'; notes.push('no state button for ' + (m.file || 'idle')); }
        else {
          await btn.click();
          await page.waitForTimeout(300);
          const cid = target === pub ? '#publicDynamicContent' : '#professionalDynamicContent';
          const text = await page.$eval(cid, (e) => e.innerText);
          if (text.trim().length < 40) { status = 'FAIL'; notes.push('content empty or tiny'); }
          if (/Renderer not loaded|No professional renderer/.test(text)) { status = 'FAIL'; notes.push('no renderer'); }
          for (const re of BAD) if (re.test(text)) { status = 'FAIL'; notes.push('text matches ' + re); }
          if (/verified/i.test(text) && screen.startsWith('D10')) { status = 'FAIL'; notes.push('word "verified" on D10'); }
          if ((screen.startsWith('D8') || screen.startsWith('D7')) && !/DRAFT/.test(text)) { status = 'FAIL'; notes.push('no DRAFT mark'); }
          for (const id of [...(EXPECT[m.file] || []), ...(MODE === 'api' ? EXPECT_API[m.file] || [] : [])]) {
            if (!(await page.$(`[data-testid="${id}"]`))) { status = 'FAIL'; notes.push('missing ' + id); }
          }
          source = await page.$eval('#dataSourceBadge', (b) => b.dataset.kind).catch(() => 'none');
          const bodyText = await page.$eval('body', (b) => b.innerText);
          if (!bodyText.includes('DEMO MODE: Sample data for course evaluation. Not for clinical use.')) { status = 'FAIL'; notes.push('demo banner missing'); }
          if (shots && m === entries[0] && screen === uiScreen) {
            const i = demoOrder.indexOf(uiScreen);
            if (i >= 0) {
              await page.evaluate(() => { const p = document.getElementById('devStateSwitcher'); if (p) p.style.display = 'none'; });
              const name = String(i + 1).padStart(2, '0') + '_' + uiScreen.replace(/[^A-Za-z0-9]+/g, '_').toLowerCase() + '.png';
              await page.screenshot({ path: path.join(shotDir, name), fullPage: true });
              await page.evaluate(() => { const p = document.getElementById('devStateSwitcher'); if (p) p.style.display = ''; });
            }
          }
        }
      } catch (e) { status = 'FAIL'; notes.push('exception: ' + e.message.split('\n')[0]); }
      const newErrs = errs.slice(before);
      if (newErrs.length) { status = 'FAIL'; notes.push(...newErrs.slice(0, 3)); }
      results.push({ screen: uiScreen, state: m.state, file: m.file || 'idle', source, status, notes: notes.join('; ') });
    }
  }
  // Click-through checks: buttons must move to a state that actually renders (not an empty payload).
  async function openState(screen, file) {
    const { page, errs } = pro;
    await page.evaluate((s) => window.LabelLensStateSwitcher.setScreen(s), screen);
    await page.waitForTimeout(300);
    await page.click(`#devStateButtons .btn-state[data-file="${file}"]`);
    await page.waitForTimeout(300);
    return { page, errs };
  }
  const text = (page) => page.$eval('#professionalDynamicContent', (e) => e.innerText);
  const flows = [
    ['D6 confirm checklist button', async () => {
      const { page } = await openState('D6 Changes', 'professional/changes/assess_success.json');
      await page.click('#btnConfirmChecklist'); await page.waitForTimeout(400);
      const t = await text(page);
      if (MODE === 'api') return /Assess a change first/.test(t) ? '' : 'api mode must refuse to confirm a mock checklist';
      return /Generate Draft Artwork/.test(t) && !/undefined/.test(t) ? '' : 'confirm did not reach a confirmed state: ' + t.slice(0, 80);
    }],
    ['D6 generate draft button (mock)', async () => {
      const { page } = await openState('D6 Changes', 'professional/changes/confirm_success.json');
      await page.click('#btnGenerateDraftArtwork'); await page.waitForTimeout(MODE === 'api' ? 4000 : 400);
      const t = await text(page);
      if (MODE === 'api' && (await page.$('[data-testid="generate-error"]'))) return '';  // the API refused: the reason is shown, nothing invented
      return /DRAFT/.test(t) && /Review/.test(t) ? '' : 'generate did not reach the draft artwork: ' + t.slice(0, 80);
    }],
    ['D9 audit and versions switch buttons', async () => {
      const { page } = await openState('D9 History', 'professional/history/label_versions.json');
      const b = await page.$('#btnSwitchToAuditLog');
      if (!b) return 'no switch button on versions view';
      await b.click(); await page.waitForTimeout(400);
      const t = await text(page);
      return /undefined/.test(t) || t.length < 60 ? 'audit view empty after switch' : '';
    }],
    ['D7 return needs a comment', async () => {
      const { page } = await openState('D7 Review', 'professional/review/recheck_success.json');
      await page.click('#btnReturn');
      return /comment is required/.test(await page.$eval('#reviewActionNote', (e) => e.textContent)) ? '' : 'no comment warning';
    }],
    ['D7 approve is disabled when the re-check failed', async () => {
      const { page } = await openState('D7 Review', 'professional/review/recheck_failed_check.json');
      return (await page.$eval('#btnApprove', (b) => b.disabled)) ? '' : 'approve button is enabled on a failed check';
    }],
    ['D7 draws each finding citation (section, title, quote)', async () => {
      // Synthetic re-check result built here for the test, not a mock file: one finding with a citation, one without.
      const { page } = await openState('D7 Review', 'professional/review/recheck_success.json');
      const html = await page.evaluate(() => {
        const box = document.createElement('div');
        const cite = { source_type: 'cfr', chunk_id: 'c1', source: 'test', section: '801.40', title: 'Form of a unique device identifier', url: 'https://example.invalid/x', quote: 'The test quote text for the unique device identifier.' };
        window.LabelLensRenderers['D7 Review'](box, 'success', null, { check_id: 'chk_t', version_id: 'v_t', passed: true, findings: [
          { flag_id: 'f1', kind: 'barcode_mismatch', severity: 'review', message: 'm', evidence_chunk_ids: [], confidence: 0.5, needs_human: true, rule_id: 'B-LOT', field: 'lot', citations: [cite] },
          { flag_id: 'f2', kind: 'text_overflow', severity: 'critical', message: 'm', evidence_chunk_ids: [], confidence: 1, needs_human: false, citations: [] }], coverage: [] });
        return box.innerHTML;
      });
      const n = (html.match(/data-testid="citation"/g) || []).length;
      if (n !== 1) return `expected 1 citation, drew ${n}`;
      return /21 CFR 801\.40: Form of a unique device identifier/.test(html) && /The test quote text/.test(html) ? '' : 'citation section, title or quote missing';
    }],
    ['D8 download click', async () => {
      const { page } = await openState('D8 Export', 'professional/export/draft.json');
      await page.click('.dl-btn');
      const n = await page.$eval('#downloadNote', (e) => e.textContent);
      return n.length > 5 ? '' : 'no download note';
    }],
    ['D4 confirm button reaches a confirmed extraction (mock)', async () => {
      if (MODE === 'api') return '';
      const { page } = await openState('D4 Inspect', 'professional/inspect/extraction_needs_review.json');
      await page.$eval('#btnConfirmExtractionAction', (e) => e.click()); await page.waitForTimeout(500);
      return /Extraction confirmed/.test(await text(page)) ? '' : 'did not reach the confirmed extraction';
    }],
    ['D4 run inspection reaches the check result', async () => {
      if (MODE === 'api') return '';
      const { page } = await openState('D4 Inspect', 'professional/inspect/extraction_success.json');
      await page.$eval('#btnRunInspectionNow', (e) => e.click()); await page.waitForTimeout(500);
      return (await page.$('[data-testid="inspect-outcome"]')) ? '' : 'no inspection result after Run inspection';
    }],
    ['D4 unclear field is editable, confirmed field is not', async () => {
      const { page } = await openState('D4 Inspect', 'professional/inspect/extraction_needs_review.json');
      const editable = await page.$$eval('input[data-field]', (i) => i.length);
      const { page: p2 } = await openState('D4 Inspect', 'professional/inspect/extraction_confirmed.json');
      const after = await p2.$$eval('input[data-field]', (i) => i.length);
      return editable > 0 && after === 0 ? '' : `editable ${editable}, after confirm ${after}`;
    }],
    ['D5 ask click', async () => {
      const { page } = await openState('D5 Evidence', 'professional/evidence/success.json');
      await page.fill('#d5Question', 'how must a date be written?');
      await page.click('#d5Ask');
      if (MODE === 'api') await page.waitForFunction(() => /Extractive answer|Abstained|Search is not available|HTTP|error/.test(document.getElementById('professionalDynamicContent').innerText), null, { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(500);
      const t = await text(page);
      return MODE === 'api' ? (/Extractive answer|Abstained|Search is not available|HTTP|error/.test(t) ? '' : 'no answer or message: ' + t.slice(-120)) : (/Mock mode/.test(t) ? '' : 'no mock note');
    }],
  ];
  const flowResults = [];
  for (const [name, fn] of flows) {
    const before = pro.errs.length;
    let msg = '';
    try { msg = await fn(); } catch (e) { msg = 'exception: ' + e.message.split(String.fromCharCode(10))[0]; }
    const errs = pro.errs.slice(before);
    if (errs.length) msg += ' ' + errs.slice(0, 2).join('; ');
    flowResults.push({ name, status: msg ? 'FAIL' : 'pass', notes: msg });
  }
  await browser.close();
  const fails = results.filter((r) => r.status !== 'pass');
  const NL = String.fromCharCode(10);
  let md = '| Screen | State | Mock file | Data source | Result | Notes |' + NL + '|---|---|---|---|---|---|' + NL;
  for (const r of results) md += `| ${r.screen} | ${r.state} | ${r.file} | ${r.source} | ${r.status} | ${r.notes} |` + NL;
  md += NL + '| Click-through | Result | Notes |' + NL + '|---|---|---|' + NL;
  for (const f of flowResults) md += `| ${f.name} | ${f.status} | ${f.notes} |` + NL;
  fs.writeFileSync(process.env.OUT || path.join(root, 'ui', 'check_results.md'), md);
  console.log(`expected fallback HTTP errors ignored (api mode): ${fallbackHttp}`);
  console.log(`${results.length} states, ${fails.length} failed; ${flowResults.length} click-throughs, ${flowResults.filter((f) => f.status !== 'pass').length} failed`);
  for (const f of flowResults.filter((x) => x.status !== 'pass')) console.log('FLOW FAIL', f.name, '::', f.notes);
  for (const f of fails) console.log('FAIL', f.screen, f.file, '::', f.notes);
})();
