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
    page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    page.on('requestfailed', (r) => errs.push('requestfailed: ' + r.url()));
    await page.goto(`${BASE}/ui/${kind === 'public' ? 'public' : 'professional'}/index.html`);
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
          const bodyText = await page.$eval('body', (b) => b.innerText);
          if (!bodyText.includes('DEMO MODE: Sample data for course evaluation. Not for clinical use.')) { status = 'FAIL'; notes.push('demo banner missing'); }
          if (shots && m === entries[0]) {
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
      results.push({ screen: uiScreen, state: m.state, file: m.file || 'idle', status, notes: notes.join('; ') });
    }
  }
  await browser.close();
  const fails = results.filter((r) => r.status !== 'pass');
  let md = '| Screen | State | Mock file | Result | Notes |\n|---|---|---|---|---|\n';
  for (const r of results) md += `| ${r.screen} | ${r.state} | ${r.file} | ${r.status} | ${r.notes} |\n`;
  fs.writeFileSync(process.env.OUT || path.join(root, 'ui', 'check_results.md'), md);
  console.log(`${results.length} states, ${fails.length} failed`);
  for (const f of fails) console.log('FAIL', f.screen, f.file, '::', f.notes);
})();
