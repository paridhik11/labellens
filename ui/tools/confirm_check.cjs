/**
 * A photo never confirms itself. With a running server (API mode) this feeds the P2 screen a matched scan result
 * (the real /public/match answer for a typed name plus made-up OCR lines) and checks:
 *   1. "Is this <product>?" with the read lines as evidence, Confirm / Not this one / Type the name, and NO label
 *      information (reference label summary) before Confirm.
 *   2. Confirm shows the label information.
 *   3. Not this one shows no label information and offers typing the name.
 *
 *   PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 node ui/tools/confirm_check.cjs
 */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const URL_P1 = `${BASE}/ui/public/index.html?dev=1&devopen=1&mode=api`;
let failed = 0;
const log = (name, ok, note) => { if (!ok) failed += 1; console.log(`${ok ? 'PASS' : 'FAIL'}  ${name} ${note || ''}`); };

async function open(browser) {
  const page = await (await browser.newContext({ viewport: { width: 1100, height: 900 } })).newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(URL_P1);
  await page.waitForSelector('#devStateButtons .btn-state');
  const body = await page.evaluate(async () => {
    const r = await window.LabelLensApi.request('POST', '/public/match', { json: { product_name: 'Lisinopril' } });
    return r.body;
  });
  const scan = {
    ...body,
    matched_text: 'Lisinopril Tablets',
    read_lines: [
      { text: 'Lisinopril Tablets USP', confidence: 0.93, used: true },
      { text: 'Rx only', confidence: 0.9, used: false },
    ],
  };
  await page.evaluate((b) => window.LabelLensPublicScan.showMatch(b), scan);
  await page.waitForSelector('[data-testid="scan-confirm-panel"]');
  return { page, errors, scan };
}

(async () => {
  const browser = await chromium.launch();
  try {
    const { page, errors, scan } = await open(browser);
    const text = await page.$eval('#publicDynamicContent', (e) => e.innerText);
    const name = scan.candidates[0].product_name;
    log('asks "Is this <product>?"', text.includes(`Is this ${name}?`), `(${name})`);
    log('shows the lines read as evidence', (await page.$$('[data-testid="read-line"]')).length === 2);
    log('Confirm, Not this one and Type the name are offered',
      !!(await page.$('[data-testid="scan-confirm"]')) && !!(await page.$('[data-testid="scan-reject"]'))
      && !!(await page.$('[data-testid="scan-typename"]')));
    const summary = scan.summary || '';
    log('no label information before Confirm', !!summary && !text.includes(summary), `(summary: ${summary.slice(0, 50)})`);
    await page.click('[data-testid="scan-confirm"]');
    await page.waitForFunction(() => !document.querySelector('[data-testid="scan-confirm-panel"]'));
    const after = await page.$eval('#publicDynamicContent', (e) => e.innerText);
    log('Confirm shows the label information', after.includes(name) && after.length > text.length, `(${after.length} chars)`);
    log('no page errors', errors.length === 0, errors.join('; '));
  } catch (e) { log('confirm flow', false, e.message.split('\n')[0]); }
  try {
    const { page } = await open(browser);
    await page.click('[data-testid="scan-reject"]');
    await page.waitForSelector('[data-testid="type-name-input"]');
    const text = await page.$eval('#publicDynamicContent', (e) => e.innerText);
    log('Not this one shows no label information and offers typing the name',
      /Nothing is shown for this product/.test(text) && !!(await page.$('[data-testid="scan-confirm-panel"]')));
  } catch (e) { log('reject flow', false, e.message.split('\n')[0]); }
  await browser.close();
  console.log(failed ? `${failed} FAILED` : 'ALL PASSED');
  process.exit(failed ? 1 : 0);
})();
