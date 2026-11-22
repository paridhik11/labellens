/**
 * Api mode never shows sample data: with no label loaded, P2 says so and P3 offers the DailyMed search.
 * Usage: PLAYWRIGHT_DIR=<dir with node_modules/playwright> BASE=http://127.0.0.1:8000 node ui/tools/nolabel_check.cjs
 */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'x.js'));
const { chromium } = req('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8000';
let fails = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'}     ${m}`); if (!c) fails += 1; };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`${BASE}/ui/public/index.html`);
  await page.waitForSelector('[data-testid="take-photo"]');
  ok(true, 'no query string: the page opens in api mode on the scan tab');
  await page.click('[data-screen="P2 Product information"]');
  await page.waitForSelector('[data-testid="no-label-loaded"]');
  ok(!/ExampleMed/.test(await page.locator('body').innerText()), 'P2 with nothing loaded shows no sample product');
  ok(await page.locator('[data-testid="live-search-go"]').count() === 1, 'P2 offers Search DailyMed');
  await page.click('[data-screen="P3 Ask about this label"]');
  await page.waitForSelector('#p3QuestionInput');
  ok(!/ExampleMed/.test(await page.locator('#publicDynamicContent').innerText()), 'P3 shows no sample answer');
  await page.fill('#p3Medicine', 'Advil');
  await page.fill('#p3QuestionInput', 'stomach bleeding');
  await page.click('#btnP3AskSubmit');
  await page.waitForSelector('[data-testid="no-label-loaded"]', { timeout: 30000 });
  ok(await page.locator('[data-testid="live-search-go"]').count() === 1, 'P3: unknown name shows "No label loaded for this name" with Search DailyMed');
  ok(await page.locator('[data-testid="citation"]').count() === 0, 'no regulation answer is shown for it');
  ok(errors.length === 0, `page errors ${errors.length}`);
  await browser.close();
  console.log(`${fails} FAIL`);
  process.exit(fails ? 1 : 0);
})();
